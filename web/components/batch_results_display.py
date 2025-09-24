"""
批量分析结果展示组件
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any
import datetime

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('web')


def render_batch_results(batch_results: Dict[str, Any]):
    """渲染批量分析结果"""
    
    if not batch_results:
        st.warning("暂无批量分析结果")
        return
    
    # 显示批量分析概览
    render_batch_overview(batch_results)
    
    # 显示投资建议统计
    render_investment_statistics(batch_results)
    
    # 显示风险分析
    render_risk_analysis(batch_results)
    
    # 显示详细结果
    render_detailed_results(batch_results)
    
    # 显示失败分析
    render_failed_analyses(batch_results)


def render_batch_overview(batch_results: Dict[str, Any]):
    """渲染批量分析概览"""
    
    st.header("📊 批量分析概览")
    
    # 基本统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="总股票数",
            value=batch_results.get('total_stocks', 0),
            help="本次批量分析的总股票数量"
        )
    
    with col2:
        st.metric(
            label="成功分析",
            value=batch_results.get('successful_analyses', 0),
            help="成功完成分析的股票数量"
        )
    
    with col3:
        st.metric(
            label="失败分析",
            value=batch_results.get('failed_analyses', 0),
            help="分析失败的股票数量"
        )
    
    with col4:
        success_rate = batch_results.get('successful_analyses', 0) / batch_results.get('total_stocks', 1) * 100
        st.metric(
            label="成功率",
            value=f"{success_rate:.1f}%",
            help="分析成功的比例"
        )
    
    # 分析时间和配置信息
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **⏱️ 分析时间信息**
        - 开始时间: {datetime.datetime.fromtimestamp(batch_results.get('start_time', 0)).strftime('%Y-%m-%d %H:%M:%S')}
        - 结束时间: {datetime.datetime.fromtimestamp(batch_results.get('end_time', 0)).strftime('%Y-%m-%d %H:%M:%S')}
        - 总耗时: {batch_results.get('total_duration', 0) // 60:.0f}分{batch_results.get('total_duration', 0) % 60:.0f}秒
        """)
    
    with col2:
        st.info(f"""
        **⚙️ 分析配置**
        - 市场类型: {batch_results.get('market_type', '未知')}
        - 研究深度: {batch_results.get('research_depth', 0)}级
        - 分析师: {', '.join(batch_results.get('analysts', []))}
        - 分析日期: {batch_results.get('analysis_date', '未知')}
        """)


def render_investment_statistics(batch_results: Dict[str, Any]):
    """渲染投资建议统计"""
    
    st.header("📈 投资建议统计")
    
    summary_report = batch_results.get('summary_report', {})
    investment_recs = summary_report.get('investment_recommendations', {})
    
    if not investment_recs:
        st.warning("暂无投资建议数据")
        return
    
    # 投资建议分布
    col1, col2 = st.columns(2)
    
    with col1:
        # 投资建议饼图
        labels = ['买入', '卖出', '持有']
        values = [
            investment_recs.get('buy_count', 0),
            investment_recs.get('sell_count', 0),
            investment_recs.get('hold_count', 0)
        ]
        
        if sum(values) > 0:
            fig = px.pie(
                values=values,
                names=labels,
                title="投资建议分布",
                color_discrete_map={
                    '买入': '#28a745',
                    '卖出': '#dc3545',
                    '持有': '#ffc107'
                }
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 投资建议统计表
        st.subheader("📊 投资建议统计")
        
        data = {
            '建议类型': ['买入', '卖出', '持有'],
            '数量': [
                investment_recs.get('buy_count', 0),
                investment_recs.get('sell_count', 0),
                investment_recs.get('hold_count', 0)
            ],
            '占比': [
                f"{investment_recs.get('buy_percentage', 0) * 100:.1f}%",
                f"{investment_recs.get('sell_percentage', 0) * 100:.1f}%",
                f"{investment_recs.get('hold_percentage', 0) * 100:.1f}%"
            ]
        }
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    
    # 推荐度最高的股票
    top_recommendations = summary_report.get('top_recommendations', [])
    if top_recommendations:
        st.subheader("🏆 推荐度最高的股票")
        
        # 创建推荐度表格
        rec_data = []
        for rec in top_recommendations:
            rec_data.append({
                '股票代码': rec.get('stock_symbol', ''),
                '投资建议': rec.get('action', ''),
                '置信度': f"{rec.get('confidence', 0) * 100:.1f}%",
                '风险分数': f"{rec.get('risk_score', 0) * 100:.1f}%",
                '目标价格': f"¥{rec.get('target_price', 0):.2f}" if rec.get('target_price') else 'N/A',
                '分析要点': rec.get('reasoning', '')[:100] + '...' if len(rec.get('reasoning', '')) > 100 else rec.get('reasoning', '')
            })
        
        if rec_data:
            df_rec = pd.DataFrame(rec_data)
            st.dataframe(df_rec, use_container_width=True)


def render_risk_analysis(batch_results: Dict[str, Any]):
    """渲染风险分析"""
    
    st.header("⚠️ 风险分析")
    
    summary_report = batch_results.get('summary_report', {})
    risk_metrics = summary_report.get('risk_metrics', {})
    risk_alerts = summary_report.get('risk_alerts', [])
    
    if not risk_metrics:
        st.warning("暂无风险分析数据")
        return
    
    # 风险指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="平均置信度",
            value=f"{risk_metrics.get('average_confidence', 0) * 100:.1f}%",
            help="所有分析的平均置信度"
        )
    
    with col2:
        st.metric(
            label="平均风险分数",
            value=f"{risk_metrics.get('average_risk_score', 0) * 100:.1f}%",
            help="所有分析的平均风险分数"
        )
    
    with col3:
        st.metric(
            label="高置信度股票",
            value=risk_metrics.get('high_confidence_stocks', 0),
            help="置信度超过80%的股票数量"
        )
    
    with col4:
        st.metric(
            label="低风险股票",
            value=risk_metrics.get('low_risk_stocks', 0),
            help="风险分数低于30%的股票数量"
        )
    
    # 风险警报
    if risk_alerts:
        st.subheader("🚨 风险警报")
        
        for alert in risk_alerts:
            alert_type = alert.get('type', '')
            if alert_type == 'high_risk':
                st.error(f"⚠️ {alert.get('stock_symbol', '')}: {alert.get('message', '')}")
            elif alert_type == 'low_confidence':
                st.warning(f"⚠️ {alert.get('stock_symbol', '')}: {alert.get('message', '')}")
    
    # 风险分布图
    if batch_results.get('results'):
        st.subheader("📊 风险分布分析")
        
        # 提取风险数据
        risk_data = []
        for stock, result in batch_results.get('results', {}).items():
            if result.get('success', False):
                decision = result.get('decision', {})
                risk_data.append({
                    '股票代码': stock,
                    '置信度': decision.get('confidence', 0) * 100,
                    '风险分数': decision.get('risk_score', 0) * 100,
                    '投资建议': decision.get('action', '持有')
                })
        
        if risk_data:
            df_risk = pd.DataFrame(risk_data)
            
            # 置信度vs风险分数散点图
            fig = px.scatter(
                df_risk,
                x='风险分数',
                y='置信度',
                color='投资建议',
                size='置信度',
                hover_data=['股票代码'],
                title="置信度 vs 风险分数分布",
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
            
            st.plotly_chart(fig, use_container_width=True)


def render_detailed_results(batch_results: Dict[str, Any]):
    """渲染详细分析结果"""
    
    st.header("📋 详细分析结果")
    
    results = batch_results.get('results', {})
    if not results:
        st.warning("暂无详细分析结果")
        return
    
    # 创建标签页
    tab_names = []
    for stock in results.keys():
        if results[stock].get('success', False):
            tab_names.append(f"✅ {stock}")
        else:
            tab_names.append(f"❌ {stock}")
    
    if tab_names:
        tabs = st.tabs(tab_names)
        
        for i, (stock, result) in enumerate(results.items()):
            with tabs[i]:
                if result.get('success', False):
                    render_single_stock_result(stock, result)
                else:
                    render_failed_stock_result(stock, result)


def render_single_stock_result(stock_symbol: str, result: Dict[str, Any]):
    """渲染单个股票的分析结果"""
    
    st.subheader(f"📈 {stock_symbol} 分析结果")
    
    # 投资决策
    decision = result.get('decision', {})
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        action = decision.get('action', '持有')
        color = '#28a745' if action == '买入' else '#dc3545' if action == '卖出' else '#ffc107'
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: {color}20; border-radius: 8px;">
            <h3 style="color: {color}; margin: 0;">{action}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        confidence = decision.get('confidence', 0) * 100
        st.metric("置信度", f"{confidence:.1f}%")
    
    with col3:
        risk_score = decision.get('risk_score', 0) * 100
        st.metric("风险分数", f"{risk_score:.1f}%")
    
    with col4:
        target_price = decision.get('target_price')
        if target_price:
            st.metric("目标价格", f"¥{target_price:.2f}")
        else:
            st.metric("目标价格", "N/A")
    
    # 分析推理
    reasoning = decision.get('reasoning', '')
    if reasoning:
        st.subheader("💭 分析推理")
        st.write(reasoning)
    
    # 详细分析报告
    state = result.get('state', {})
    if state:
        st.subheader("📊 详细分析报告")
        
        # 技术面分析
        if 'market_report' in state:
            with st.expander("📈 技术面分析", expanded=False):
                st.markdown(state['market_report'])
        
        # 基本面分析
        if 'fundamentals_report' in state:
            with st.expander("💰 基本面分析", expanded=False):
                st.markdown(state['fundamentals_report'])
        
        # 情绪分析
        if 'sentiment_report' in state:
            with st.expander("💭 情绪分析", expanded=False):
                st.markdown(state['sentiment_report'])
        
        # 新闻分析
        if 'news_report' in state:
            with st.expander("📰 新闻分析", expanded=False):
                st.markdown(state['news_report'])
        
        # 风险评估
        if 'risk_assessment' in state:
            with st.expander("⚠️ 风险评估", expanded=False):
                st.markdown(state['risk_assessment'])
        
        # 投资计划
        if 'investment_plan' in state:
            with st.expander("📋 投资计划", expanded=False):
                st.markdown(state['investment_plan'])


def render_failed_stock_result(stock_symbol: str, result: Dict[str, Any]):
    """渲染失败股票的分析结果"""
    
    st.error(f"❌ {stock_symbol} 分析失败")
    
    error = result.get('error', '未知错误')
    st.write(f"**错误信息**: {error}")
    
    # 提供重试建议
    st.info("""
    **💡 重试建议**:
    1. 检查股票代码是否正确
    2. 确认股票是否在指定市场交易
    3. 检查网络连接是否正常
    4. 稍后重试分析
    """)


def render_failed_analyses(batch_results: Dict[str, Any]):
    """渲染失败分析列表"""
    
    failed_analyses = batch_results.get('summary_report', {}).get('failed_analyses', [])
    
    if failed_analyses:
        st.header("❌ 失败分析列表")
        
        failed_data = []
        for failed in failed_analyses:
            failed_data.append({
                '股票代码': failed.get('stock', ''),
                '错误信息': failed.get('error', ''),
                '状态': '分析失败'
            })
        
        if failed_data:
            df_failed = pd.DataFrame(failed_data)
            st.dataframe(df_failed, use_container_width=True)
            
            # 提供批量重试选项
            if st.button("🔄 重试失败分析", help="重新分析失败的股票"):
                st.info("重试功能开发中...")
    else:
        st.success("🎉 所有股票分析都成功完成！")
