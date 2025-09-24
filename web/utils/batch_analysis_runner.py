"""
批量股票分析执行工具 - 完全复用单个股票分析逻辑
"""

import sys
import os
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from dotenv import load_dotenv

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('web')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 确保环境变量正确加载
load_dotenv(project_root / ".env", override=True)

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_web_logging
logger = setup_web_logging()

# 引入线程安全的进度存储器
try:
    from .batch_progress_store import (
        init_batch as store_init_batch,
        update_progress as store_update_progress,
        add_completed_stock as store_add_completed_stock,
        set_status as store_set_status,
        complete_batch as store_complete_batch,
        fail_batch as store_fail_batch,
        get_snapshot as store_get_snapshot,
    )
except Exception:
    # 运行在不同导入路径时
    from web.utils.batch_progress_store import (
        init_batch as store_init_batch,
        update_progress as store_update_progress,
        add_completed_stock as store_add_completed_stock,
        set_status as store_set_status,
        complete_batch as store_complete_batch,
        fail_batch as store_fail_batch,
        get_snapshot as store_get_snapshot,
    )

# 导入单个股票分析函数和格式化函数
try:
    from utils.analysis_runner import run_stock_analysis, format_analysis_results, validate_analysis_params
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from web.utils.analysis_runner import run_stock_analysis, format_analysis_results, validate_analysis_params

def run_batch_stock_analysis(stock_symbols: List[str], 
                           analysis_date: str,
                           analysts: List[str],
                           research_depth: int,
                           llm_provider: str,
                           llm_model: str,
                           market_type: str = "美股",
                           analysis_interval: int = 30,
                           include_sentiment: bool = True,
                           include_risk_assessment: bool = True,
                           custom_prompt: str = "",
                           progress_callback=None,
                           batch_id: Optional[str] = None) -> Dict[str, Any]:
    """执行批量股票分析 - 完全复用单个股票分析逻辑
    
    Args:
        stock_symbols: 股票代码列表
        analysis_date: 分析日期
        analysts: 分析师列表
        research_depth: 研究深度
        llm_provider: LLM提供商
        llm_model: 大模型名称
        market_type: 市场类型
        analysis_interval: 分析间隔（秒）
        include_sentiment: 是否包含情绪分析
        include_risk_assessment: 是否包含风险评估
        custom_prompt: 自定义提示
        progress_callback: 进度回调函数
        
    Returns:
        批量分析结果字典
    """
    
    # 使用传入的批量分析ID，若无则生成
    if not batch_id:
        batch_id = f"batch_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 初始化结果
    results = {}
    errors = []
    start_time = time.time()
    
    logger.info(f"🚀 [批量分析开始] 开始批量分析 {len(stock_symbols)} 个股票")
    logger.info(f"📊 [批量分析] 股票列表: {stock_symbols}")
    logger.info(f"📊 [批量分析] 分析参数: 深度={research_depth}, 分析师={analysts}, 市场={market_type}")
    
    # 初始化进度存储
    try:
        store_init_batch(batch_id, len(stock_symbols))
    except Exception as _e:
        logger.warning(f"批量进度存储初始化失败: {_e}")
    
    # 逐个分析股票 - 严格按顺序执行
    for i, stock_symbol in enumerate(stock_symbols):
        current_index = i + 1
        total_stocks = len(stock_symbols)
        
        try:
            # 计算当前进度
            progress_percent = (current_index / total_stocks) * 100
            
            # 通知开始分析当前股票
            # 写入统一进度存储
            try:
                store_update_progress(batch_id, {
                    'current_stock': stock_symbol,
                    'current_index': current_index,
                    'total_stocks': total_stocks,
                    'progress': progress_percent,
                    'status': f"开始分析第 {current_index}/{total_stocks} 个股票: {stock_symbol}"
                })
            except Exception:
                pass

            if progress_callback:
                progress_callback({
                    'type': 'stock_start',
                    'stock_symbol': stock_symbol,
                    'current_index': current_index,
                    'total_stocks': total_stocks,
                    'progress': progress_percent,
                    'message': f"开始分析第 {current_index}/{total_stocks} 个股票: {stock_symbol}"
                })
            
            logger.info(f"📈 [批量分析] 开始分析第 {current_index}/{total_stocks} 个股票: {stock_symbol}")
            
            # 创建单个股票的进度回调函数
            def create_stock_progress_callback(stock, index, total):
                def stock_progress_callback(message, step=None, total_steps=None):
                    # 计算细粒度进度
                    fine_progress = 0.0
                    if step is not None and total_steps and total_steps > 0:
                        fine_progress = max(0.0, min(1.0, float(step) / float(total_steps)))
                    
                    # 总体进度 = 已完成股票 + 当前股票内部进度
                    overall_progress = ((index - 1) + fine_progress) / max(1, total) * 100.0
                    
                    # 写入统一进度存储
                    try:
                        store_update_progress(batch_id, {
                            'current_stock': stock,
                            'current_index': index,
                            'total_stocks': total,
                            'progress': overall_progress,
                            'status': message or '分析中...'
                        })
                    except Exception:
                        pass
                    # 通知进度更新
                    if progress_callback:
                        progress_callback({
                            'type': 'stock_progress',
                            'stock_symbol': stock,
                            'message': message,
                            'step': step,
                            'total_steps': total_steps,
                            'progress': overall_progress,
                            'current_index': index,
                            'total_stocks': total
                        })
                    
                    logger.info(f"📈 [批量分析] {stock}: {message}")
                
                return stock_progress_callback
            
            # 执行单个股票分析 - 完全复用原有逻辑
            stock_start_time = time.time()
            stock_result = run_stock_analysis(
                stock_symbol=stock_symbol,
                analysis_date=analysis_date,
                analysts=analysts,
                research_depth=research_depth,
                llm_provider=llm_provider,
                llm_model=llm_model,
                market_type=market_type,
                progress_callback=create_stock_progress_callback(stock_symbol, current_index, total_stocks)
            )
            stock_duration = time.time() - stock_start_time
            
            # 处理分析结果
            if stock_result.get('success', False):
                # 分析成功，格式化为与单股一致的数据结构
                formatted = format_analysis_results(stock_result)
                formatted['stock_symbol'] = stock_symbol
                formatted['analysis_time'] = time.time()
                formatted['analysis_duration'] = stock_duration
                formatted['success'] = True
                success_msg = f"✅ {stock_symbol} 分析完成 (耗时: {stock_duration:.1f}秒)"
                logger.info(f"[批量分析] {success_msg}")
                
                # 保存结果
                results[stock_symbol] = formatted
                try:
                    store_add_completed_stock(batch_id, formatted)
                except Exception:
                    pass
                
                # 通知股票分析完成
                if progress_callback:
                    progress_callback({
                        'type': 'stock_completed',
                        'stock_symbol': stock_symbol,
                        'success': True,
                        'result': formatted,
                        'duration': stock_duration,
                        'current_index': current_index,
                        'total_stocks': total_stocks,
                        'progress': progress_percent,
                        'message': success_msg
                    })
            else:
                # 分析失败
                error_msg = stock_result.get('error', '未知错误')
                failure_msg = f"❌ {stock_symbol} 分析失败: {error_msg}"
                logger.error(f"[批量分析] {failure_msg}")
                
                # 保存错误信息
                errors.append(f"{stock_symbol}: {error_msg}")
                
                # 通知股票分析失败
                try:
                    store_add_completed_stock(batch_id, {
                        'stock_symbol': stock_symbol,
                        'success': False,
                        'error': error_msg,
                        'analysis_time': time.time(),
                        'analysis_duration': stock_duration,
                    })
                except Exception:
                    pass
                if progress_callback:
                    progress_callback({
                        'type': 'stock_completed',
                        'stock_symbol': stock_symbol,
                        'success': False,
                        'error': error_msg,
                        'analysis_time': time.time(),
                        'duration': stock_duration,
                        'current_index': current_index,
                        'total_stocks': total_stocks,
                        'progress': progress_percent,
                        'message': failure_msg
                    })
            
            # 如果不是最后一个股票，等待间隔时间
            if i < len(stock_symbols) - 1:
                wait_msg = f"⏱️ 等待 {analysis_interval} 秒后分析下一个股票..."
                logger.info(f"[批量分析] {wait_msg}")
                
                try:
                    store_update_progress(batch_id, {
                        'status': wait_msg,
                        'progress': progress_percent
                    })
                except Exception:
                    pass
                if progress_callback:
                    progress_callback({
                        'type': 'waiting',
                        'message': wait_msg,
                        'wait_time': analysis_interval,
                        'progress': progress_percent,
                        'current_index': current_index,
                        'total_stocks': total_stocks
                    })
                
                time.sleep(analysis_interval)
                
        except Exception as e:
            # 处理异常
            error_msg = f"❌ {stock_symbol} 分析过程中发生异常: {str(e)}"
            logger.error(f"[批量分析] {error_msg}")
            
            # 保存错误信息
            errors.append(f"{stock_symbol}: {str(e)}")
            
            # 通知股票分析异常
            try:
                store_add_completed_stock(batch_id, {
                    'stock_symbol': stock_symbol,
                    'success': False,
                    'error': str(e),
                    'analysis_time': time.time(),
                })
            except Exception:
                pass
            if progress_callback:
                progress_callback({
                    'type': 'stock_completed',
                    'stock_symbol': stock_symbol,
                    'success': False,
                    'error': str(e),
                    'current_index': current_index,
                    'total_stocks': total_stocks,
                    'progress': progress_percent,
                    'message': error_msg
                })
    
    # 分析完成
    end_time = time.time()
    total_duration = end_time - start_time
    
    # 计算统计信息
    successful_count = len(results)
    failed_count = len(errors)
    success_rate = (successful_count / len(stock_symbols) * 100) if stock_symbols else 0
    
    # 生成汇总报告
    summary = {
        'batch_id': batch_id,
        'success': True,
        'total_stocks': len(stock_symbols),
        'successful_count': successful_count,
        'failed_count': failed_count,
        'success_rate': success_rate,
        'total_duration': total_duration,
        'start_time': datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S'),
        'results': results,
        'errors': errors,
        'stock_symbols': stock_symbols,
        'analysis_date': analysis_date,
        'analysts': analysts,
        'research_depth': research_depth,
        'market_type': market_type
    }
    
    # 最终进度更新
    final_msg = f"🎉 批量分析完成! 成功: {successful_count}/{len(stock_symbols)}, 失败: {failed_count}, 耗时: {total_duration:.1f}秒"
    logger.info(f"[批量分析完成] {final_msg}")
    
    try:
        store_complete_batch(batch_id)
    except Exception:
        pass
    if progress_callback:
        progress_callback({
            'type': 'batch_completed',
            'message': final_msg,
            'progress': 100,
            'summary': summary
        })
    
    return summary