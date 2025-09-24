"""
批量分析进度显示组件
"""

import streamlit as st
import time
from typing import Dict, List, Any
from datetime import datetime

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('web')


def render_batch_progress_display(batch_id: str, progress_info: Dict[str, Any], completed_stocks: List[Dict[str, Any]]):
    """渲染批量分析进度显示"""
    
    if not progress_info:
        st.info("⏱️ 批量分析正在进行中，请耐心等待...")
        return
    
    # 显示进度概览
    st.subheader("📊 分析进度概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="当前股票",
            value=progress_info.get('current_stock', 'N/A'),
            help="正在分析的股票代码"
        )
    
    with col2:
        current_index = progress_info.get('current_index', 0)
        total_stocks = progress_info.get('total_stocks', 0)
        st.metric(
            label="分析进度",
            value=f"{current_index}/{total_stocks}",
            help="当前股票/总股票数"
        )
    
    with col3:
        progress_percent = progress_info.get('progress', 0)
        st.metric(
            label="完成率",
            value=f"{progress_percent:.1f}%",
            help="整体分析完成百分比"
        )
    
    with col4:
        completed_count = len(completed_stocks) if completed_stocks else 0
        st.metric(
            label="已完成",
            value=completed_count,
            help="已分析完成的股票数量"
        )
    
    # 显示进度条
    progress_bar = st.progress(progress_percent / 100)
    
    # 显示当前状态
    current_status = progress_info.get('status', '准备中...')
    if "完成" in current_status:
        st.success(f"📊 {current_status}")
    elif "失败" in current_status or "错误" in current_status:
        st.error(f"📊 {current_status}")
    elif "等待" in current_status:
        st.warning(f"📊 {current_status}")
    else:
        st.info(f"📊 {current_status}")
    
    # 显示已完成的股票结果
    if completed_stocks:
        st.markdown("---")
        st.subheader("✅ 已完成分析")
        
        # 按完成时间排序
        sorted_stocks = sorted(completed_stocks, 
                             key=lambda x: x.get('analysis_time', 0), 
                             reverse=True)
        
        for i, stock_result in enumerate(sorted_stocks):
            stock_symbol = stock_result.get('stock_symbol', '')
            success = stock_result.get('success', False)
            
            if success:
                decision = stock_result.get('decision', {})
                action = decision.get('action', 'N/A')
                confidence = decision.get('confidence', 0) * 100
                risk_score = decision.get('risk_score', 0) * 100
                
                # 根据投资建议设置颜色
                if action == '买入':
                    color = 'green'
                elif action == '卖出':
                    color = 'red'
                else:
                    color = 'orange'
                
                with st.expander(f"📈 {stock_symbol} - {action} (置信度: {confidence:.1f}%)", expanded=(i < 3)):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("投资建议", action)
                    
                    with col2:
                        st.metric("置信度", f"{confidence:.1f}%")
                    
                    with col3:
                        st.metric("风险分数", f"{risk_score:.1f}%")
                    
                    # 目标价格
                    target_price = decision.get('target_price')
                    if target_price:
                        st.info(f"🎯 目标价格: ¥{target_price:.2f}")
                    
                    # 分析推理
                    reasoning = decision.get('reasoning', '')
                    if reasoning:
                        st.write("💭 分析推理:")
                        st.write(reasoning[:300] + "..." if len(reasoning) > 300 else reasoning)
                    
                    # 分析时间
                    analysis_time = stock_result.get('analysis_time')
                    if analysis_time:
                        analysis_time_str = datetime.fromtimestamp(analysis_time).strftime('%H:%M:%S')
                        st.caption(f"⏰ 分析时间: {analysis_time_str}")
                    
                    # 分析耗时
                    duration = stock_result.get('analysis_duration', 0)
                    if duration:
                        st.caption(f"⏱️ 分析耗时: {duration:.1f}秒")
            else:
                error = stock_result.get('error', '未知错误')
                with st.expander(f"❌ {stock_symbol} - 分析失败", expanded=False):
                    st.error(f"❌ 分析失败: {error}")
                    
                    # 提供重试建议
                    st.info("""
                    **💡 重试建议**:
                    1. 检查股票代码是否正确
                    2. 确认股票是否在指定市场交易
                    3. 检查网络连接是否正常
                    4. 稍后重试分析
                    """)
    
    # 显示分析统计
    if completed_stocks:
        st.markdown("---")
        st.subheader("📈 分析统计")
        
        # 统计投资建议
        buy_count = sum(1 for stock in completed_stocks 
                        if stock.get('success', False) and 
                        stock.get('decision', {}).get('action') == '买入')
        sell_count = sum(1 for stock in completed_stocks 
                        if stock.get('success', False) and 
                        stock.get('decision', {}).get('action') == '卖出')
        hold_count = sum(1 for stock in completed_stocks 
                        if stock.get('success', False) and 
                        stock.get('decision', {}).get('action') == '持有')
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("买入", buy_count)
        
        with col2:
            st.metric("卖出", sell_count)
        
        with col3:
            st.metric("持有", hold_count)
        
        with col4:
            failed_count = sum(1 for stock in completed_stocks 
                             if not stock.get('success', False))
            st.metric("失败", failed_count)
        
        # 显示平均置信度和风险分数
        successful_stocks = [stock for stock in completed_stocks if stock.get('success', False)]
        if successful_stocks:
            avg_confidence = sum(stock.get('decision', {}).get('confidence', 0) 
                               for stock in successful_stocks) / len(successful_stocks) * 100
            avg_risk_score = sum(stock.get('decision', {}).get('risk_score', 0) 
                                for stock in successful_stocks) / len(successful_stocks) * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("平均置信度", f"{avg_confidence:.1f}%")
            
            with col2:
                st.metric("平均风险分数", f"{avg_risk_score:.1f}%")


def render_progress_summary(progress_info: Dict[str, Any], completed_stocks: List[Dict[str, Any]]):
    """渲染进度摘要"""
    
    if not progress_info:
        return
    
    # 创建进度摘要
    current_stock = progress_info.get('current_stock', 'N/A')
    current_index = progress_info.get('current_index', 0)
    total_stocks = progress_info.get('total_stocks', 0)
    progress_percent = progress_info.get('progress', 0)
    status = progress_info.get('status', '准备中...')
    
    # 计算预计剩余时间
    if current_index > 0 and progress_percent > 0:
        remaining_percent = 100 - progress_percent
        if progress_percent > 0:
            estimated_remaining_time = (remaining_percent / progress_percent) * (time.time() - progress_info.get('start_time', time.time()))
            estimated_minutes = int(estimated_remaining_time // 60)
            estimated_seconds = int(estimated_remaining_time % 60)
            time_estimate = f"预计剩余时间: {estimated_minutes}分{estimated_seconds}秒"
        else:
            time_estimate = "预计剩余时间: 计算中..."
    else:
        time_estimate = "预计剩余时间: 计算中..."
    
    # 显示摘要信息
    summary_data = {
        '当前股票': current_stock,
        '分析进度': f"{current_index}/{total_stocks}",
        '完成率': f"{progress_percent:.1f}%",
        '当前状态': status,
        '已完成数量': len(completed_stocks) if completed_stocks else 0,
        '时间估算': time_estimate
    }
    
    return summary_data


def create_progress_chart(completed_stocks: List[Dict[str, Any]]):
    """创建进度图表"""
    
    if not completed_stocks:
        return None
    
    try:
        import plotly.express as px
        import pandas as pd
        
        # 准备数据
        chart_data = []
        for i, stock in enumerate(completed_stocks):
            if stock.get('success', False):
                decision = stock.get('decision', {})
                chart_data.append({
                    '股票代码': stock.get('stock_symbol', ''),
                    '投资建议': decision.get('action', 'N/A'),
                    '置信度': decision.get('confidence', 0) * 100,
                    '风险分数': decision.get('risk_score', 0) * 100,
                    '分析顺序': i + 1
                })
        
        if not chart_data:
            return None
        
        df = pd.DataFrame(chart_data)
        
        # 创建置信度vs风险分数散点图
        fig = px.scatter(
            df,
            x='风险分数',
            y='置信度',
            color='投资建议',
            size='置信度',
            hover_data=['股票代码', '分析顺序'],
            title="投资建议分布图",
            color_discrete_map={
                '买入': '#28a745',
                '卖出': '#dc3545',
                '持有': '#ffc107'
            }
        )
        
        # 添加风险区域划分线
        fig.add_hline(y=80, line_dash="dash", line_color="green", 
                     annotation_text="高置信度线", annotation_position="top right")
        fig.add_vline(x=30, line_dash="dash", line_color="red", 
                     annotation_text="低风险线", annotation_position="top left")
        
        return fig
        
    except Exception as e:
        logger.warning(f"创建进度图表失败: {e}")
        return None
