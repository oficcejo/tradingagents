"""
批量股票分析表单组件
"""

import streamlit as st
import datetime
import json
import re
from typing import List, Dict, Any

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger

# 导入用户活动记录器
try:
    from ..utils.user_activity_logger import user_activity_logger
except ImportError:
    user_activity_logger = None

logger = get_logger('web')


def render_batch_analysis_form():
    """渲染批量股票分析表单"""
    
    st.subheader("📋 批量分析配置")
    
    # 获取缓存的表单配置
    cached_config = st.session_state.get('batch_form_config') or {}
    
    # 创建表单
    with st.form("batch_analysis_form", clear_on_submit=False):
        
        # 在表单开始时保存当前配置
        initial_config = cached_config.copy() if cached_config else {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 市场选择
            market_options = ["美股", "A股", "港股"]
            cached_market = cached_config.get('market_type', 'A股') if cached_config else 'A股'
            try:
                market_index = market_options.index(cached_market)
            except (ValueError, TypeError):
                market_index = 1  # 默认A股

            market_type = st.selectbox(
                "选择市场 🌍",
                options=market_options,
                index=market_index,
                help="选择要分析的股票市场"
            )

            # 根据市场类型显示不同的输入提示
            cached_stocks = cached_config.get('stock_symbols', []) if cached_config else []

            if market_type == "美股":
                stock_input_help = "输入美股代码，用逗号或换行分隔，如：AAPL,TSLA,MSFT"
                stock_placeholder = "AAPL, TSLA, MSFT, GOOGL, AMZN"
            elif market_type == "港股":
                stock_input_help = "输入港股代码，用逗号或换行分隔，如：0700.HK,9988.HK"
                stock_placeholder = "0700.HK, 9988.HK, 3690.HK"
            else:  # A股
                stock_input_help = "输入A股代码，用逗号或换行分隔，如：000001,600519"
                stock_placeholder = "000001, 600519, 000858, 002415"

            # 股票代码输入
            stock_symbols_text = st.text_area(
                "股票代码列表 📈",
                value="\n".join(cached_stocks) if cached_stocks else "",
                placeholder=stock_placeholder,
                help=stock_input_help,
                height=120,
                key="batch_stock_input"
            )
            
            # 分析日期
            analysis_date = st.date_input(
                "分析日期 📅",
                value=datetime.date.today(),
                help="选择分析的基准日期"
            )
        
        with col2:
            # 研究深度
            cached_depth = cached_config.get('research_depth', 3) if cached_config else 3
            research_depth = st.select_slider(
                "研究深度 🔍",
                options=[1, 2, 3, 4, 5],
                value=cached_depth,
                format_func=lambda x: {
                    1: "1级 - 快速分析",
                    2: "2级 - 基础分析", 
                    3: "3级 - 标准分析",
                    4: "4级 - 深度分析",
                    5: "5级 - 全面分析"
                }[x],
                help="选择分析的深度级别，级别越高分析越详细但耗时更长"
            )
            
            # 分析间隔设置
            analysis_interval = st.number_input(
                "分析间隔（秒）⏱️",
                min_value=5,
                max_value=300,
                value=30,
                step=5,
                help="设置股票之间的分析间隔，避免API限制"
            )
        
        # 分析师团队选择
        st.markdown("### 👥 选择分析师团队")

        col1, col2 = st.columns(2)

        # 获取缓存的分析师选择
        cached_analysts = cached_config.get('selected_analysts', ['market', 'fundamentals']) if cached_config else ['market', 'fundamentals']

        # 检测市场类型是否发生变化
        market_type_changed = cached_config.get('market_type', 'A股') != market_type

        # 如果市场类型发生变化，需要调整分析师选择
        if market_type_changed:
            if market_type == "A股":
                # 切换到A股：移除社交媒体分析师
                cached_analysts = [analyst for analyst in cached_analysts if analyst != 'social']
                if len(cached_analysts) == 0:
                    cached_analysts = ['market', 'fundamentals']  # 确保至少有默认选择
            else:
                # 切换到非A股：如果只有基础分析师，添加社交媒体分析师
                if 'social' not in cached_analysts and len(cached_analysts) <= 2:
                    cached_analysts.append('social')

        with col1:
            market_analyst = st.checkbox(
                "📈 市场分析师",
                value='market' in cached_analysts,
                help="专注于技术面分析、价格趋势、技术指标"
            )

            # 根据市场类型显示社交媒体分析师
            if market_type == "A股":
                social_analyst = st.checkbox(
                    "💭 社交媒体分析师",
                    value=False,
                    disabled=True,
                    help="A股市场暂不支持社交媒体分析（国内数据源限制）"
                )
                st.info("💡 A股市场暂不支持社交媒体分析，因为国内数据源限制")
            else:
                social_analyst = st.checkbox(
                    "💭 社交媒体分析师",
                    value='social' in cached_analysts,
                    help="分析社交媒体情绪、投资者情绪指标"
                )

        with col2:
            news_analyst = st.checkbox(
                "📰 新闻分析师",
                value='news' in cached_analysts,
                help="分析相关新闻事件、市场动态影响"
            )

            fundamentals_analyst = st.checkbox(
                "💰 基本面分析师",
                value='fundamentals' in cached_analysts,
                help="分析财务数据、公司基本面、估值水平"
            )

        # 收集选中的分析师
        selected_analysts = []
        if market_analyst:
            selected_analysts.append(("market", "市场分析师"))
        if social_analyst:
            selected_analysts.append(("social", "社交媒体分析师"))
        if news_analyst:
            selected_analysts.append(("news", "新闻分析师"))
        if fundamentals_analyst:
            selected_analysts.append(("fundamentals", "基本面分析师"))
        
        # 显示选择摘要
        if selected_analysts:
            st.success(f"已选择 {len(selected_analysts)} 个分析师: {', '.join([a[1] for a in selected_analysts])}")
        else:
            st.warning("请至少选择一个分析师")
        
        # 高级选项
        with st.expander("🔧 高级选项"):
            include_sentiment = st.checkbox(
                "包含情绪分析",
                value=True,
                help="是否包含市场情绪和投资者情绪分析"
            )
            
            include_risk_assessment = st.checkbox(
                "包含风险评估",
                value=True,
                help="是否包含详细的风险因素评估"
            )
            
            custom_prompt = st.text_area(
                "自定义分析要求",
                placeholder="输入特定的分析要求或关注点...",
                help="可以输入特定的分析要求，AI会在分析中重点关注"
            )
            
            # 导出选项
            st.markdown("#### 📄 报告导出选项")
            export_format = st.selectbox(
                "导出格式",
                options=["Markdown", "PDF", "Excel", "JSON"],
                help="选择批量分析报告的导出格式"
            )
            
            include_summary = st.checkbox(
                "包含汇总报告",
                value=True,
                help="是否生成所有股票的汇总分析报告"
            )

        # 解析股票代码
        stock_symbols = parse_stock_symbols(stock_symbols_text, market_type)
        
        # 显示解析结果
        if stock_symbols:
            st.success(f"✅ 已解析 {len(stock_symbols)} 个股票代码: {', '.join(stock_symbols)}")
            
            # 显示预估分析时间
            estimated_time = len(stock_symbols) * (research_depth * 30 + 60) + (len(stock_symbols) - 1) * analysis_interval
            st.info(f"⏱️ 预估分析时间: {estimated_time // 60}分{estimated_time % 60}秒")
        else:
            st.info("💡 请在上方输入股票代码，支持逗号或换行分隔")

        # 在提交按钮前检测配置变化并保存
        current_config = {
            'stock_symbols': stock_symbols,
            'market_type': market_type,
            'research_depth': research_depth,
            'selected_analysts': [a[0] for a in selected_analysts],
            'analysis_interval': analysis_interval,
            'include_sentiment': include_sentiment,
            'include_risk_assessment': include_risk_assessment,
            'custom_prompt': custom_prompt,
            'export_format': export_format,
            'include_summary': include_summary
        }

        # 如果配置发生变化，立即保存
        if current_config != initial_config:
            st.session_state.batch_form_config = current_config
            logger.debug(f"📊 [批量配置自动保存] 表单配置已更新")

        # 提交按钮
        submitted = st.form_submit_button(
            "🚀 开始批量分析",
            type="primary",
            use_container_width=True
        )

    # 只有在提交时才返回数据
    if submitted and stock_symbols:
        # 添加详细日志
        logger.debug(f"🔍 [批量表单提交] ===== 批量分析表单提交 =====")
        logger.debug(f"🔍 [批量表单提交] 股票代码: {stock_symbols}")
        logger.debug(f"🔍 [批量表单提交] 市场类型: {market_type}")
        logger.debug(f"🔍 [批量表单提交] 分析日期: {analysis_date}")
        logger.debug(f"🔍 [批量表单提交] 选择的分析师: {[a[0] for a in selected_analysts]}")
        logger.debug(f"🔍 [批量表单提交] 研究深度: {research_depth}")

        form_data = {
            'submitted': True,
            'stock_symbols': stock_symbols,
            'market_type': market_type,
            'analysis_date': str(analysis_date),
            'analysts': [a[0] for a in selected_analysts],
            'research_depth': research_depth,
            'analysis_interval': analysis_interval,
            'include_sentiment': include_sentiment,
            'include_risk_assessment': include_risk_assessment,
            'custom_prompt': custom_prompt,
            'export_format': export_format,
            'include_summary': include_summary
        }

        # 保存表单配置到缓存
        form_config = {
            'stock_symbols': stock_symbols,
            'market_type': market_type,
            'research_depth': research_depth,
            'selected_analysts': [a[0] for a in selected_analysts],
            'analysis_interval': analysis_interval,
            'include_sentiment': include_sentiment,
            'include_risk_assessment': include_risk_assessment,
            'custom_prompt': custom_prompt,
            'export_format': export_format,
            'include_summary': include_summary
        }
        st.session_state.batch_form_config = form_config

        # 记录用户批量分析请求活动
        if user_activity_logger:
            try:
                user_activity_logger.log_analysis_request(
                    symbol=",".join(stock_symbols),
                    market=market_type,
                    analysis_date=str(analysis_date),
                    research_depth=research_depth,
                    analyst_team=[a[0] for a in selected_analysts],
                    details={
                        'include_sentiment': include_sentiment,
                        'include_risk_assessment': include_risk_assessment,
                        'has_custom_prompt': bool(custom_prompt),
                        'form_source': 'batch_analysis_form',
                        'stock_count': len(stock_symbols),
                        'analysis_interval': analysis_interval
                    }
                )
                logger.debug(f"📊 [用户活动] 已记录批量分析请求: {len(stock_symbols)}个股票")
            except Exception as e:
                logger.warning(f"⚠️ [用户活动] 记录失败: {e}")

        logger.info(f"📊 [批量配置缓存] 表单配置已保存: {form_config}")

        logger.debug(f"🔍 [批量表单提交] 返回的表单数据: {form_data}")
        logger.debug(f"🔍 [批量表单提交] ===== 批量表单提交结束 =====")

        return form_data
    elif submitted and not stock_symbols:
        # 用户点击了提交但没有输入股票代码
        logger.error(f"🔍 [批量表单提交] 提交失败：股票代码为空")
        st.error("❌ 请输入股票代码后再提交")
        return {'submitted': False}
    else:
        return {'submitted': False}


def parse_stock_symbols(stock_text: str, market_type: str) -> List[str]:
    """解析股票代码文本，支持逗号和换行分隔"""
    
    if not stock_text or not stock_text.strip():
        return []
    
    # 按逗号和换行分割
    symbols = []
    for line in stock_text.split('\n'):
        for symbol in line.split(','):
            symbol = symbol.strip()
            if symbol:
                symbols.append(symbol)
    
    # 根据市场类型验证和格式化
    validated_symbols = []
    for symbol in symbols:
        try:
            validated_symbol = validate_and_format_symbol(symbol, market_type)
            if validated_symbol:
                validated_symbols.append(validated_symbol)
        except Exception as e:
            logger.warning(f"⚠️ 股票代码验证失败: {symbol} - {e}")
            st.warning(f"⚠️ 股票代码格式错误: {symbol}")
    
    return validated_symbols


def validate_and_format_symbol(symbol: str, market_type: str) -> str:
    """验证并格式化股票代码"""
    
    symbol = symbol.strip()
    
    if market_type == "A股":
        # A股：6位数字
        if re.match(r'^\d{6}$', symbol):
            return symbol
        else:
            raise ValueError("A股代码格式错误，应为6位数字（如：000001）")
    
    elif market_type == "港股":
        # 港股：4-5位数字.HK 或 纯4-5位数字
        symbol_upper = symbol.upper()
        # 检查是否为 XXXX.HK 或 XXXXX.HK 格式
        hk_format = re.match(r'^\d{4,5}\.HK$', symbol_upper)
        # 检查是否为纯4-5位数字格式
        digit_format = re.match(r'^\d{4,5}$', symbol)
        
        if hk_format:
            return symbol_upper
        elif digit_format:
            # 纯数字格式，添加.HK后缀
            return f"{symbol.zfill(4)}.HK"
        else:
            raise ValueError("港股代码格式错误，应为4位数字.HK（如：0700.HK）或4位数字（如：0700）")
    
    elif market_type == "美股":
        # 美股：1-5位字母
        if re.match(r'^[A-Z]{1,5}$', symbol.upper()):
            return symbol.upper()
        else:
            raise ValueError("美股代码格式错误，应为1-5位字母（如：AAPL）")
    
    return symbol
