"""
线程安全的批量进度存储器

避免在后台线程直接写入Streamlit的session_state，
通过此模块在后台线程更新进度，前台UI轮询读取并渲染。
"""

import threading
import time
from typing import Dict, Any, List, Optional


_lock = threading.RLock()
_batches: Dict[str, Dict[str, Any]] = {}


def init_batch(batch_id: str, total_stocks: int) -> None:
    with _lock:
        _batches[batch_id] = {
            'progress_info': {
                'current_stock': '',
                'current_index': 0,
                'total_stocks': total_stocks,
                'progress': 0.0,
                'status': '准备中...',
                'start_time': time.time(),
            },
            'completed_stocks': [],
            'status': 'running',
            'last_update': time.time(),
        }


def update_progress(batch_id: str, progress_info: Dict[str, Any]) -> None:
    with _lock:
        if batch_id not in _batches:
            return
        _batches[batch_id]['progress_info'].update(progress_info)
        _batches[batch_id]['last_update'] = time.time()


def add_completed_stock(batch_id: str, result: Dict[str, Any]) -> None:
    with _lock:
        if batch_id not in _batches:
            return
        _batches[batch_id]['completed_stocks'].append(result)
        _batches[batch_id]['last_update'] = time.time()


def set_status(batch_id: str, status: str, progress: Optional[float] = None) -> None:
    with _lock:
        if batch_id not in _batches:
            return
        _batches[batch_id]['progress_info']['status'] = status
        if progress is not None:
            _batches[batch_id]['progress_info']['progress'] = progress
        _batches[batch_id]['status'] = 'completed' if progress == 100 else _batches[batch_id]['status']
        _batches[batch_id]['last_update'] = time.time()


def complete_batch(batch_id: str) -> None:
    with _lock:
        if batch_id not in _batches:
            return
        _batches[batch_id]['status'] = 'completed'
        _batches[batch_id]['progress_info']['status'] = '✅ 批量分析完成'
        _batches[batch_id]['progress_info']['progress'] = 100.0
        _batches[batch_id]['last_update'] = time.time()


def fail_batch(batch_id: str, error: str) -> None:
    with _lock:
        if batch_id not in _batches:
            return
        _batches[batch_id]['status'] = 'failed'
        _batches[batch_id]['progress_info']['status'] = f'❌ 批量分析失败: {error}'
        _batches[batch_id]['last_update'] = time.time()


def get_snapshot(batch_id: str) -> Dict[str, Any]:
    with _lock:
        return dict(_batches.get(batch_id, {}))


def clear_batch(batch_id: str) -> None:
    with _lock:
        _batches.pop(batch_id, None)


