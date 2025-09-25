import json
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Tuple


def _get_storage_path() -> Path:
    # 授权信息存放在项目 web 目录下隐藏文件
    base = Path(__file__).parent.parent
    return base / '.batch_license.json'


def _load_license() -> dict:
    p = _get_storage_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def _save_license(data: dict) -> None:
    p = _get_storage_path()
    try:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        # 目录不可写等情况忽略，保持无激活
        pass


def _generate_machine_code() -> str:
    # 使用 MAC 地址 与 主机名 生成稳定可读的机器码（仅数字）
    try:
        mac_int = uuid.getnode()
        host = os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or 'HOST'
        base_num = abs(hash(str(mac_int) + host))
        code = str(base_num)
        # 取最后 10 位作为机器码，全部是数字
        return code[-10:]
    except Exception:
        return '0000000000'


def get_or_create_machine_code() -> str:
    data = _load_license()
    code = data.get('machine_code')
    if not code:
        code = _generate_machine_code()
        data['machine_code'] = code
        data.setdefault('activated', False)
        _save_license(data)
    return code


def is_activated() -> bool:
    data = _load_license()
    return bool(data.get('activated'))


def expected_password(now: datetime, machine_code: str) -> int:
    y, m, d, h = now.year, now.month, now.day, now.hour
    last3 = int(machine_code[-3:]) if machine_code[-3:].isdigit() else 0
    return (y + m + d + h) * 7 + last3


def verify_and_activate(input_password: str) -> Tuple[bool, str]:
    """校验密码并激活。
    返回：(是否成功, 提示信息)
    """
    data = _load_license()
    code = data.get('machine_code') or get_or_create_machine_code()
    try:
        exp = expected_password(datetime.now(), code)
        if str(input_password).strip() == str(exp):
            data['activated'] = True
            _save_license(data)
            return True, '激活成功'
        else:
            return False, '激活码错误'
    except Exception as e:
        return False, f'激活异常: {e}'


