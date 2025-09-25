#!/usr/bin/env python3
"""
TradingAgents-CN Streamlit Web界面
基于Streamlit的股票分析Web应用程序
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path
import datetime
import time
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入日志模块
try:
    from tradingagents.utils.logging_manager import get_logger
    logger = get_logger('web')
except ImportError:
    # 如果无法导入，使用标准logging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('web')

# 加载环境变量
load_dotenv(project_root / ".env", override=True)

# 导入自定义组件
from components.sidebar import render_sidebar
from components.header import render_header
from components.analysis_form import render_analysis_form
from components.results_display import render_results
from components.login import render_login_form, check_authentication, render_user_info, render_sidebar_user_info, render_sidebar_logout, require_permission
from components.user_activity_dashboard import render_user_activity_dashboard, render_activity_summary_widget
from utils.api_checker import check_api_keys
from utils.analysis_runner import run_stock_analysis, validate_analysis_params, format_analysis_results
from utils.progress_tracker import SmartStreamlitProgressDisplay, create_smart_progress_callback
from utils.async_progress_tracker import AsyncProgressTracker
from components.async_progress_display import display_unified_progress
from utils.smart_session_manager import get_persistent_analysis_id, set_persistent_analysis_id
from utils.auth_manager import auth_manager
from utils.user_activity_logger import user_activity_logger

# 设置页面配置
st.set_page_config(
    page_title="TradingAgents-CN 股票分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# 自定义CSS样式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* 隐藏Streamlit顶部工具栏和Deploy按钮 - 多种选择器确保兼容性 */
    .stAppToolbar {
        display: none !important;
    }
    
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    .stDeployButton {
        display: none !important;
    }
    
    /* 新版本Streamlit的Deploy按钮选择器 */
    [data-testid="stToolbar"] {
        display: none !important;
    }
    
    [data-testid="stDecoration"] {
        display: none !important;
    }
    
    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    
    /* 隐藏整个顶部区域 */
    .stApp > header {
        display: none !important;
    }
    
    .stApp > div[data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* 隐藏主菜单按钮 */
    #MainMenu {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* 隐藏页脚 */
    footer {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* 隐藏"Made with Streamlit"标识 */
    .viewerBadge_container__1QSob {
        display: none !important;
    }
    
    /* 隐藏所有可能的工具栏元素 */
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* 隐藏右上角的所有按钮 */
    .stApp > div > div > div > div > section > div {
        padding-top: 0 !important;
    }
    
    /* 全局样式 */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* 主容器样式 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* 主标题样式 */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    /* 卡片样式 */
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        margin: 0.5rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(20px);
        transition: all 0.3s ease;
        text-align: center;
    }
    
    .metric-card h4 {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    
    .metric-card p {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin: 0;
        font-size: 0.9rem;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
    }
    
    .analysis-section {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(20px);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        background: white;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
    }
    
    /* 状态框样式 */
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #9ae6b4;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(154, 230, 180, 0.3);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #f6d55c;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(255, 234, 167, 0.3);
    }
    
    .error-box {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #f1556c;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(245, 198, 203, 0.3);
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 12px;
        padding: 0.5rem 1rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* 数据框样式 */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* 图表容器样式 */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """初始化会话状态"""
    # 初始化认证相关状态
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    
    # 初始化分析相关状态
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'analysis_running' not in st.session_state:
        st.session_state.analysis_running = False
    if 'last_analysis_time' not in st.session_state:
        st.session_state.last_analysis_time = None
    if 'current_analysis_id' not in st.session_state:
        st.session_state.current_analysis_id = None
    if 'form_config' not in st.session_state:
        st.session_state.form_config = None

    # 尝试从最新完成的分析中恢复结果
    if not st.session_state.analysis_results:
        try:
            from utils.async_progress_tracker import get_latest_analysis_id, get_progress_by_id
            from utils.analysis_runner import format_analysis_results

            latest_id = get_latest_analysis_id()
            if latest_id:
                progress_data = get_progress_by_id(latest_id)
                if (progress_data and
                    progress_data.get('status') == 'completed' and
                    'raw_results' in progress_data):

                    # 恢复分析结果
                    raw_results = progress_data['raw_results']
                    formatted_results = format_analysis_results(raw_results)

                    if formatted_results:
                        st.session_state.analysis_results = formatted_results
                        st.session_state.current_analysis_id = latest_id
                        # 检查分析状态
                        analysis_status = progress_data.get('status', 'completed')
                        st.session_state.analysis_running = (analysis_status == 'running')
                        # 恢复股票信息
                        if 'stock_symbol' in raw_results:
                            st.session_state.last_stock_symbol = raw_results.get('stock_symbol', '')
                        if 'market_type' in raw_results:
                            st.session_state.last_market_type = raw_results.get('market_type', '')
                        logger.info(f"📊 [结果恢复] 从分析 {latest_id} 恢复结果，状态: {analysis_status}")

        except Exception as e:
            logger.warning(f"⚠️ [结果恢复] 恢复失败: {e}")

    # 使用cookie管理器恢复分析ID（优先级：session state > cookie > Redis/文件）
    try:
        persistent_analysis_id = get_persistent_analysis_id()
        if persistent_analysis_id:
            # 使用线程检测来检查分析状态
            from utils.thread_tracker import check_analysis_status
            actual_status = check_analysis_status(persistent_analysis_id)

            # 只在状态变化时记录日志，避免重复
            current_session_status = st.session_state.get('last_logged_status')
            if current_session_status != actual_status:
                logger.info(f"📊 [状态检查] 分析 {persistent_analysis_id} 实际状态: {actual_status}")
                st.session_state.last_logged_status = actual_status

            if actual_status == 'running':
                st.session_state.analysis_running = True
                st.session_state.current_analysis_id = persistent_analysis_id
            elif actual_status in ['completed', 'failed']:
                st.session_state.analysis_running = False
                st.session_state.current_analysis_id = persistent_analysis_id
            else:  # not_found
                logger.warning(f"📊 [状态检查] 分析 {persistent_analysis_id} 未找到，清理状态")
                st.session_state.analysis_running = False
                st.session_state.current_analysis_id = None
    except Exception as e:
        # 如果恢复失败，保持默认值
        logger.warning(f"⚠️ [状态恢复] 恢复分析状态失败: {e}")
        st.session_state.analysis_running = False
        st.session_state.current_analysis_id = None

    # 恢复表单配置
    try:
        from utils.smart_session_manager import smart_session_manager
        session_data = smart_session_manager.load_analysis_state()

        if session_data and 'form_config' in session_data:
            st.session_state.form_config = session_data['form_config']
            # 只在没有分析运行时记录日志，避免重复
            if not st.session_state.get('analysis_running', False):
                logger.info("📊 [配置恢复] 表单配置已恢复")
    except Exception as e:
        logger.warning(f"⚠️ [配置恢复] 表单配置恢复失败: {e}")

def check_frontend_auth_cache():
    """检查前端缓存并尝试恢复登录状态"""
    from utils.auth_manager import auth_manager
    
    logger.info("🔍 开始检查前端缓存恢复")
    logger.info(f"📊 当前认证状态: {st.session_state.get('authenticated', False)}")
    logger.info(f"🔗 URL参数: {dict(st.query_params)}")
    
    # 如果已经认证，确保状态同步
    if st.session_state.get('authenticated', False):
        # 确保auth_manager也知道用户已认证
        if not auth_manager.is_authenticated() and st.session_state.get('user_info'):
            logger.info("🔄 同步认证状态到auth_manager")
            try:
                auth_manager.login_user(
                    st.session_state.user_info, 
                    st.session_state.get('login_time', time.time())
                )
                logger.info("✅ 认证状态同步成功")
            except Exception as e:
                logger.warning(f"⚠️ 认证状态同步失败: {e}")
        else:
            logger.info("✅ 用户已认证，跳过缓存检查")
        return
    
    # 检查URL参数中是否有恢复信息
    try:
        import base64
        restore_data = st.query_params.get('restore_auth')
        
        if restore_data:
            logger.info("📥 发现URL中的恢复参数，开始恢复登录状态")
            # 解码认证数据
            auth_data = json.loads(base64.b64decode(restore_data).decode())
            
            # 兼容旧格式（直接是用户信息）和新格式（包含loginTime）
            if 'userInfo' in auth_data:
                user_info = auth_data['userInfo']
                # 使用当前时间作为新的登录时间，避免超时问题
                # 因为前端已经验证了lastActivity没有超时
                login_time = time.time()
            else:
                # 旧格式兼容
                user_info = auth_data
                login_time = time.time()
                
            logger.info(f"✅ 成功解码用户信息: {user_info.get('username', 'Unknown')}")
            logger.info(f"🕐 使用当前时间作为登录时间: {login_time}")
            
            # 恢复登录状态
            if auth_manager.restore_from_cache(user_info, login_time):
                # 清除URL参数
                del st.query_params['restore_auth']
                logger.info(f"✅ 从前端缓存成功恢复用户 {user_info['username']} 的登录状态")
                logger.info("🧹 已清除URL恢复参数")
                # 立即重新运行以应用恢复的状态
                logger.info("🔄 触发页面重新运行")
                st.rerun()
            else:
                logger.error("❌ 恢复登录状态失败")
                # 恢复失败，清除URL参数
                del st.query_params['restore_auth']
        else:
            # 如果没有URL参数，注入前端检查脚本
            logger.info("📝 没有URL恢复参数，注入前端检查脚本")
            inject_frontend_cache_check()
    except Exception as e:
        logger.warning(f"⚠️ 处理前端缓存恢复失败: {e}")
        # 如果恢复失败，清除可能损坏的URL参数
        if 'restore_auth' in st.query_params:
            del st.query_params['restore_auth']

def inject_frontend_cache_check():
    """注入前端缓存检查脚本"""
    logger.info("📝 准备注入前端缓存检查脚本")
    
    # 如果已经注入过，不重复注入
    if st.session_state.get('cache_script_injected', False):
        logger.info("⚠️ 前端脚本已注入，跳过重复注入")
        return
    
    # 标记已注入
    st.session_state.cache_script_injected = True
    logger.info("✅ 标记前端脚本已注入")
    
    cache_check_js = """
    <script>
    // 前端缓存检查和恢复
    function checkAndRestoreAuth() {
        console.log('🚀 开始执行前端缓存检查');
        console.log('📍 当前URL:', window.location.href);
        
        try {
            // 检查URL中是否已经有restore_auth参数
            const currentUrl = new URL(window.location);
            if (currentUrl.searchParams.has('restore_auth')) {
                console.log('🔄 URL中已有restore_auth参数，跳过前端检查');
                return;
            }
            
            const authData = localStorage.getItem('tradingagents_auth');
            console.log('🔍 检查localStorage中的认证数据:', authData ? '存在' : '不存在');
            
            if (!authData) {
                console.log('🔍 前端缓存中没有登录状态');
                return;
            }
            
            const data = JSON.parse(authData);
            console.log('📊 解析的认证数据:', data);
            
            // 验证数据结构
            if (!data.userInfo || !data.userInfo.username) {
                console.log('❌ 认证数据结构无效，清除缓存');
                localStorage.removeItem('tradingagents_auth');
                return;
            }
            
            const now = Date.now();
            const timeout = 10 * 60 * 1000; // 10分钟
            const timeSinceLastActivity = now - data.lastActivity;
            
            console.log('⏰ 时间检查:', {
                now: new Date(now).toLocaleString(),
                lastActivity: new Date(data.lastActivity).toLocaleString(),
                timeSinceLastActivity: Math.round(timeSinceLastActivity / 1000) + '秒',
                timeout: Math.round(timeout / 1000) + '秒'
            });
            
            // 检查是否超时
            if (timeSinceLastActivity > timeout) {
                localStorage.removeItem('tradingagents_auth');
                console.log('⏰ 登录状态已过期，自动清除');
                return;
            }
            
            // 更新最后活动时间
            data.lastActivity = now;
            localStorage.setItem('tradingagents_auth', JSON.stringify(data));
            console.log('🔄 更新最后活动时间');
            
            console.log('✅ 从前端缓存恢复登录状态:', data.userInfo.username);
            
            // 保留现有的URL参数，只添加restore_auth参数
            // 传递完整的认证数据，包括原始登录时间
            const restoreData = {
                userInfo: data.userInfo,
                loginTime: data.loginTime
            };
            const restoreParam = btoa(JSON.stringify(restoreData));
            console.log('📦 生成恢复参数:', restoreParam);
            
            // 保留所有现有参数
            const existingParams = new URLSearchParams(currentUrl.search);
            existingParams.set('restore_auth', restoreParam);
            
            // 构建新URL，保留现有参数
            const newUrl = currentUrl.origin + currentUrl.pathname + '?' + existingParams.toString();
            console.log('🔗 准备跳转到:', newUrl);
            console.log('📋 保留的URL参数:', Object.fromEntries(existingParams));
            
            window.location.href = newUrl;
            
        } catch (e) {
            console.error('❌ 前端缓存恢复失败:', e);
            localStorage.removeItem('tradingagents_auth');
        }
    }
    
    // 延迟执行，确保页面完全加载
    console.log('⏱️ 设置1000ms延迟执行前端缓存检查');
    setTimeout(checkAndRestoreAuth, 1000);
    </script>
    """
    
    st.components.v1.html(cache_check_js, height=0)

def main():
    """主应用程序"""

    # 初始化会话状态
    initialize_session_state()

    # 检查前端缓存恢复
    check_frontend_auth_cache()

    # 检查用户认证状态
    if not auth_manager.is_authenticated():
        # 最后一次尝试从session state恢复认证状态
        if (st.session_state.get('authenticated', False) and 
            st.session_state.get('user_info') and 
            st.session_state.get('login_time')):
            logger.info("🔄 从session state恢复认证状态")
            try:
                auth_manager.login_user(
                    st.session_state.user_info, 
                    st.session_state.login_time
                )
                logger.info(f"✅ 成功从session state恢复用户 {st.session_state.user_info.get('username', 'Unknown')} 的认证状态")
            except Exception as e:
                logger.warning(f"⚠️ 从session state恢复认证状态失败: {e}")
        
        # 如果仍然未认证，显示登录页面
        if not auth_manager.is_authenticated():
            render_login_form()
            return

    # 全局侧边栏CSS样式 - 确保所有页面一致
    st.markdown("""
    <style>
    /* 统一侧边栏宽度为320px */
    section[data-testid="stSidebar"] {
        width: 320px !important;
        min-width: 320px !important;
        max-width: 320px !important;
    }

    /* 侧边栏内容容器 */
    section[data-testid="stSidebar"] > div {
        width: 320px !important;
        min-width: 320px !important;
        max-width: 320px !important;
    }

    /* 主内容区域适配320px侧边栏 */
    .main .block-container {
        width: calc(100vw - 336px) !important;
        max-width: calc(100vw - 336px) !important;
    }

    /* 选择框宽度适配320px侧边栏 */
    section[data-testid="stSidebar"] .stSelectbox > div > div,
    section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
        width: 100% !important;
        min-width: 260px !important;
        max-width: 280px !important;
    }

    /* 侧边栏标题样式 */
    section[data-testid="stSidebar"] h1 {
        font-size: 1.2rem !important;
        line-height: 1.3 !important;
        margin-bottom: 1rem !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }

    /* 隐藏侧边栏的隐藏按钮 - 更全面的选择器 */
    button[kind="header"],
    button[data-testid="collapsedControl"],
    .css-1d391kg,
    .css-1rs6os,
    .css-17eq0hr,
    .css-1lcbmhc,
    .css-1y4p8pa,
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"],
    [data-testid="collapsedControl"],
    .stSidebar button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* 隐藏侧边栏顶部区域的特定按钮（更精确的选择器，避免影响表单按钮） */
    section[data-testid="stSidebar"] > div:first-child > button[kind="header"],
    section[data-testid="stSidebar"] > div:first-child > div > button[kind="header"],
    section[data-testid="stSidebar"] .css-1lcbmhc > button[kind="header"],
    section[data-testid="stSidebar"] .css-1y4p8pa > button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* 调整侧边栏内容的padding */
    section[data-testid="stSidebar"] > div {
        padding-top: 0.5rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* 调整主内容区域，设置8px边距 - 使用更强的选择器 */
    .main .block-container,
    section.main .block-container,
    div.main .block-container,
    .stApp .main .block-container {
        padding-left: 8px !important;
        padding-right: 8px !important;
        margin-left: 0px !important;
        margin-right: 0px !important;
        max-width: none !important;
        width: calc(100% - 16px) !important;
    }

    /* 确保内容不被滚动条遮挡 */
    .stApp > div {
        overflow-x: auto !important;
    }

    /* 调整详细分析报告的右边距 */
    .element-container {
        margin-right: 8px !important;
    }

    /* 优化侧边栏标题和元素间距 */
    .sidebar .sidebar-content {
        padding: 0.5rem 0.3rem !important;
    }

    /* 调整侧边栏内所有元素的间距 */
    section[data-testid="stSidebar"] .element-container {
        margin-bottom: 0.5rem !important;
    }

    /* 调整侧边栏分隔线的间距 */
    section[data-testid="stSidebar"] hr {
        margin: 0.8rem 0 !important;
    }

    /* 简化功能选择区域样式 */
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }

    /* 这些样式已在global_sidebar.css中定义 */

    /* 防止水平滚动条出现 */
    .main .block-container {
        overflow-x: visible !important;
    }

    /* 强制设置8px边距给所有可能的容器 */
    .stApp,
    .stApp > div,
    .stApp > div > div,
    .main,
    .main > div,
    .main > div > div,
    div[data-testid="stAppViewContainer"],
    div[data-testid="stAppViewContainer"] > div,
    section[data-testid="stMain"],
    section[data-testid="stMain"] > div {
        padding-left: 8px !important;
        padding-right: 8px !important;
        margin-left: 0px !important;
        margin-right: 0px !important;
    }

    /* 特别处理列容器 */
    div[data-testid="column"],
    .css-1d391kg,
    .css-1r6slb0,
    .css-12oz5g7,
    .css-1lcbmhc {
        padding-left: 8px !important;
        padding-right: 8px !important;
        margin-left: 0px !important;
        margin-right: 0px !important;
    }

    /* 容器宽度已在global_sidebar.css中定义 */

    /* 优化使用指南区域的样式 */
    div[data-testid="column"]:last-child {
        background-color: #f8f9fa !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-left: 8px !important;
        border: 1px solid #e9ecef !important;
    }

    /* 使用指南内的展开器样式 */
    div[data-testid="column"]:last-child .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border-radius: 6px !important;
        border: 1px solid #dee2e6 !important;
        font-weight: 500 !important;
    }

    /* 使用指南内的文本样式 */
    div[data-testid="column"]:last-child .stMarkdown {
        font-size: 0.9rem !important;
        line-height: 1.5 !important;
    }

    /* 使用指南标题样式 */
    div[data-testid="column"]:last-child h1 {
        font-size: 1.3rem !important;
        color: #495057 !important;
        margin-bottom: 1rem !important;
    }
    </style>

    <script>
    // JavaScript来强制隐藏侧边栏按钮
    function hideSidebarButtons() {
        // 隐藏所有可能的侧边栏控制按钮
        const selectors = [
            'button[kind="header"]',
            'button[data-testid="collapsedControl"]',
            'button[aria-label="Close sidebar"]',
            'button[aria-label="Open sidebar"]',
            '[data-testid="collapsedControl"]',
            '.css-1d391kg',
            '.css-1rs6os',
            '.css-17eq0hr',
            '.css-1lcbmhc button',
            '.css-1y4p8pa button'
        ];

        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.style.opacity = '0';
                el.style.pointerEvents = 'none';
            });
        });
    }

    // 页面加载后执行
    document.addEventListener('DOMContentLoaded', hideSidebarButtons);

    // 定期检查并隐藏按钮（防止动态生成）
    setInterval(hideSidebarButtons, 1000);

    // 强制修改页面边距为8px
    function forceOptimalPadding() {
        const selectors = [
            '.main .block-container',
            '.stApp',
            '.stApp > div',
            '.main',
            '.main > div',
            'div[data-testid="stAppViewContainer"]',
            'section[data-testid="stMain"]',
            'div[data-testid="column"]'
        ];

        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.style.paddingLeft = '8px';
                el.style.paddingRight = '8px';
                el.style.marginLeft = '0px';
                el.style.marginRight = '0px';
            });
        });

        // 特别处理主容器宽度
        const mainContainer = document.querySelector('.main .block-container');
        if (mainContainer) {
            mainContainer.style.width = 'calc(100vw - 336px)';
            mainContainer.style.maxWidth = 'calc(100vw - 336px)';
        }
    }

    // 页面加载后执行
    document.addEventListener('DOMContentLoaded', forceOptimalPadding);

    // 定期强制应用样式
    setInterval(forceOptimalPadding, 500);
    </script>
    """, unsafe_allow_html=True)

    # 添加调试按钮（仅在调试模式下显示）
    if os.getenv('DEBUG_MODE') == 'true':
        if st.button("🔄 清除会话状态"):
            st.session_state.clear()
            st.experimental_rerun()

    # 渲染页面头部
    render_header()

    # 侧边栏布局 - 标题在最顶部
    st.sidebar.title("🤖 TradingAgents-CN")
    st.sidebar.markdown("---")
    
    # 页面导航 - 在标题下方显示用户信息
    render_sidebar_user_info()

    # 在用户信息和功能导航之间添加分隔线
    st.sidebar.markdown("---")

    # 添加功能切换标题
    st.sidebar.markdown("**🎯 功能导航**")

    page = st.sidebar.selectbox(
        "切换功能模块",
        ["📊 股票分析", "📈 批量分析", "⚙️ 配置管理", "💾 缓存管理", "💰 Token统计", "📋 操作日志", "📈 分析结果", "🔧 系统状态"],
        label_visibility="collapsed"
    )
    
    # 记录页面访问活动
    try:
        user_activity_logger.log_page_visit(
            page_name=page,
            page_params={
                "page_url": f"/app?page={page.split(' ')[1] if ' ' in page else page}",
                "page_type": "main_navigation",
                "access_method": "sidebar_selectbox"
            }
        )
    except Exception as e:
        logger.warning(f"记录页面访问活动失败: {e}")

    # 在功能选择和AI模型配置之间添加分隔线
    st.sidebar.markdown("---")

    # 根据选择的页面渲染不同内容
    if page == "📈 批量分析":
        # 检查分析权限
        if not require_permission("analysis"):
            return
        try:
            from components.batch_analysis_form import render_batch_analysis_form
            from components.batch_results_display import render_batch_results
            from utils.batch_analysis_runner import run_batch_stock_analysis
            from utils.batch_report_exporter import export_batch_report
            
            # 渲染批量分析页面
            render_batch_analysis_page()
        except ImportError as e:
            st.error(f"批量分析模块加载失败: {e}")
            st.info("请确保已安装所有依赖包")
        return
    elif page == "⚙️ 配置管理":
        # 检查配置权限
        if not require_permission("config"):
            return
        try:
            from modules.config_management import render_config_management
            render_config_management()
        except ImportError as e:
            st.error(f"配置管理模块加载失败: {e}")
            st.info("请确保已安装所有依赖包")
        return
    elif page == "💾 缓存管理":
        # 检查管理员权限
        if not require_permission("admin"):
            return
        try:
            from modules.cache_management import main as cache_main
            cache_main()
        except ImportError as e:
            st.error(f"缓存管理页面加载失败: {e}")
        return
    elif page == "💰 Token统计":
        # 检查配置权限
        if not require_permission("config"):
            return
        try:
            from modules.token_statistics import render_token_statistics
            render_token_statistics()
        except ImportError as e:
            st.error(f"Token统计页面加载失败: {e}")
            st.info("请确保已安装所有依赖包")
        return
    elif page == "📋 操作日志":
        # 检查管理员权限
        if not require_permission("admin"):
            return
        try:
            from components.operation_logs import render_operation_logs
            render_operation_logs()
        except ImportError as e:
            st.error(f"操作日志模块加载失败: {e}")
            st.info("请确保已安装所有依赖包")
        return
    elif page == "📈 分析结果":
        # 检查分析权限
        if not require_permission("analysis"):
            return
        try:
            from components.analysis_results import render_analysis_results
            render_analysis_results()
        except ImportError as e:
            st.error(f"分析结果模块加载失败: {e}")
            st.info("请确保已安装所有依赖包")
        return
    elif page == "🔧 系统状态":
        # 检查管理员权限
        if not require_permission("admin"):
            return
        st.header("🔧 系统状态")
        st.info("系统状态功能开发中...")
        return

    # 默认显示股票分析页面
    # 检查分析权限
    if not require_permission("analysis"):
        return
        
    # 检查API密钥
    api_status = check_api_keys()
    
    if not api_status['all_configured']:
        st.error("⚠️ API密钥配置不完整，请先配置必要的API密钥")
        
        with st.expander("📋 API密钥配置指南", expanded=True):
            st.markdown("""
            ### 🔑 必需的API密钥
            
            1. **阿里百炼API密钥** (DASHSCOPE_API_KEY)
               - 获取地址: https://dashscope.aliyun.com/
               - 用途: AI模型推理
            
            2. **金融数据API密钥** (FINNHUB_API_KEY)  
               - 获取地址: https://finnhub.io/
               - 用途: 获取股票数据
            
            ### ⚙️ 配置方法
            
            1. 复制项目根目录的 `.env.example` 为 `.env`
            2. 编辑 `.env` 文件，填入您的真实API密钥
            3. 重启Web应用
            
            ```bash
            # .env 文件示例
            DASHSCOPE_API_KEY=sk-your-dashscope-key
            FINNHUB_API_KEY=your-finnhub-key
            ```
            """)
        
        # 显示当前API密钥状态
        st.subheader("🔍 当前API密钥状态")
        for key, status in api_status['details'].items():
            if status['configured']:
                st.success(f"✅ {key}: {status['display']}")
            else:
                st.error(f"❌ {key}: 未配置")
        
        return
    
    # 渲染侧边栏
    config = render_sidebar()
    
    # 添加使用指南显示切换
    # 如果正在分析或有分析结果，默认隐藏使用指南
    default_show_guide = not (st.session_state.get('analysis_running', False) or st.session_state.get('analysis_results') is not None)
    
    # 如果用户没有手动设置过，使用默认值
    if 'user_set_guide_preference' not in st.session_state:
        st.session_state.user_set_guide_preference = False
        st.session_state.show_guide_preference = default_show_guide
    
    show_guide = st.sidebar.checkbox(
        "📖 显示使用指南", 
        value=st.session_state.get('show_guide_preference', default_show_guide), 
        help="显示/隐藏右侧使用指南",
        key="guide_checkbox"
    )
    
    # 记录用户的选择
    if show_guide != st.session_state.get('show_guide_preference', default_show_guide):
        st.session_state.user_set_guide_preference = True
        st.session_state.show_guide_preference = show_guide

    # 添加状态清理按钮
    st.sidebar.markdown("---")
    if st.sidebar.button("🧹 清理分析状态", help="清理僵尸分析状态，解决页面持续刷新问题"):
        # 清理session state
        st.session_state.analysis_running = False
        st.session_state.current_analysis_id = None
        st.session_state.analysis_results = None

        # 清理所有自动刷新状态
        keys_to_remove = []
        for key in st.session_state.keys():
            if 'auto_refresh' in key:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del st.session_state[key]

        # 清理死亡线程
        from utils.thread_tracker import cleanup_dead_analysis_threads
        cleanup_dead_analysis_threads()

        st.sidebar.success("✅ 分析状态已清理")
        st.rerun()

    # 在侧边栏底部添加退出按钮
    render_sidebar_logout()

    # 主内容区域 - 根据是否显示指南调整布局
    if show_guide:
        col1, col2 = st.columns([2, 1])  # 2:1比例，使用指南占三分之一
    else:
        col1 = st.container()
        col2 = None
    
    with col1:
        # 1. 分析配置区域

        st.header("⚙️ 分析配置")

        # 渲染分析表单
        try:
            form_data = render_analysis_form()

            # 验证表单数据格式
            if not isinstance(form_data, dict):
                st.error(f"⚠️ 表单数据格式异常: {type(form_data)}")
                form_data = {'submitted': False}

        except Exception as e:
            st.error(f"❌ 表单渲染失败: {e}")
            form_data = {'submitted': False}

        # 避免显示调试信息
        if form_data and form_data != {'submitted': False}:
            # 只在调试模式下显示表单数据
            if os.getenv('DEBUG_MODE') == 'true':
                st.write("Debug - Form data:", form_data)

        # 添加接收日志
        if form_data.get('submitted', False):
            logger.debug(f"🔍 [APP DEBUG] ===== 主应用接收表单数据 =====")
            logger.debug(f"🔍 [APP DEBUG] 接收到的form_data: {form_data}")
            logger.debug(f"🔍 [APP DEBUG] 股票代码: '{form_data['stock_symbol']}'")
            logger.debug(f"🔍 [APP DEBUG] 市场类型: '{form_data['market_type']}'")

        # 检查是否提交了表单
        if form_data.get('submitted', False) and not st.session_state.get('analysis_running', False):
            # 只有在没有分析运行时才处理新的提交
            # 验证分析参数
            is_valid, validation_errors = validate_analysis_params(
                stock_symbol=form_data['stock_symbol'],
                analysis_date=form_data['analysis_date'],
                analysts=form_data['analysts'],
                research_depth=form_data['research_depth'],
                market_type=form_data.get('market_type', '美股')
            )

            if not is_valid:
                # 显示验证错误
                for error in validation_errors:
                    st.error(error)
            else:
                # 执行分析
                st.session_state.analysis_running = True

                # 清空旧的分析结果
                st.session_state.analysis_results = None
                logger.info("🧹 [新分析] 清空旧的分析结果")
                
                # 自动隐藏使用指南（除非用户明确设置要显示）
                if not st.session_state.get('user_set_guide_preference', False):
                    st.session_state.show_guide_preference = False
                    logger.info("📖 [界面] 开始分析，自动隐藏使用指南")

                # 生成分析ID
                import uuid
                analysis_id = f"analysis_{uuid.uuid4().hex[:8]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # 保存分析ID和表单配置到session state和cookie
                form_config = st.session_state.get('form_config', {})
                set_persistent_analysis_id(
                    analysis_id=analysis_id,
                    status="running",
                    stock_symbol=form_data['stock_symbol'],
                    market_type=form_data.get('market_type', '美股'),
                    form_config=form_config
                )

                # 创建异步进度跟踪器
                async_tracker = AsyncProgressTracker(
                    analysis_id=analysis_id,
                    analysts=form_data['analysts'],
                    research_depth=form_data['research_depth'],
                    llm_provider=config['llm_provider']
                )

                # 创建进度回调函数
                def progress_callback(message: str, step: int = None, total_steps: int = None):
                    async_tracker.update_progress(message, step)

                # 显示启动成功消息和加载动效
                st.success(f"🚀 分析已启动！分析ID: {analysis_id}")

                # 添加加载动效
                with st.spinner("🔄 正在初始化分析..."):
                    time.sleep(1.5)  # 让用户看到反馈

                st.info(f"📊 正在分析: {form_data.get('market_type', '美股')} {form_data['stock_symbol']}")
                st.info("""
                ⏱️ 页面将在6秒后自动刷新...

                📋 **查看分析进度：**
                刷新后请向下滚动到 "📊 股票分析" 部分查看实时进度
                """)

                # 确保AsyncProgressTracker已经保存初始状态
                time.sleep(0.1)  # 等待100毫秒确保数据已写入

                # 设置分析状态
                st.session_state.analysis_running = True
                st.session_state.current_analysis_id = analysis_id
                st.session_state.last_stock_symbol = form_data['stock_symbol']
                st.session_state.last_market_type = form_data.get('market_type', '美股')

                # 自动启用自动刷新选项（设置所有可能的key）
                auto_refresh_keys = [
                    f"auto_refresh_unified_{analysis_id}",
                    f"auto_refresh_unified_default_{analysis_id}",
                    f"auto_refresh_static_{analysis_id}",
                    f"auto_refresh_streamlit_{analysis_id}"
                ]
                for key in auto_refresh_keys:
                    st.session_state[key] = True

                # 在后台线程中运行分析（立即启动，不等待倒计时）
                import threading

                def run_analysis_in_background():
                    try:
                        results = run_stock_analysis(
                            stock_symbol=form_data['stock_symbol'],
                            analysis_date=form_data['analysis_date'],
                            analysts=form_data['analysts'],
                            research_depth=form_data['research_depth'],
                            llm_provider=config['llm_provider'],
                            market_type=form_data.get('market_type', '美股'),
                            llm_model=config['llm_model'],
                            progress_callback=progress_callback
                        )

                        # 标记分析完成并保存结果（不访问session state）
                        async_tracker.mark_completed("✅ 分析成功完成！", results=results)

                        # 自动保存分析结果到历史记录
                        try:
                            from components.analysis_results import save_analysis_result
                            
                            save_success = save_analysis_result(
                                analysis_id=analysis_id,
                                stock_symbol=form_data['stock_symbol'],
                                analysts=form_data['analysts'],
                                research_depth=form_data['research_depth'],
                                result_data=results,
                                status="completed"
                            )
                            
                            if save_success:
                                logger.info(f"💾 [后台保存] 分析结果已保存到历史记录: {analysis_id}")
                            else:
                                logger.warning(f"⚠️ [后台保存] 保存失败: {analysis_id}")
                                
                        except Exception as save_error:
                            logger.error(f"❌ [后台保存] 保存异常: {save_error}")

                        logger.info(f"✅ [分析完成] 股票分析成功完成: {analysis_id}")

                    except Exception as e:
                        # 标记分析失败（不访问session state）
                        async_tracker.mark_failed(str(e))
                        
                        # 保存失败的分析记录
                        try:
                            from components.analysis_results import save_analysis_result
                            
                            save_analysis_result(
                                analysis_id=analysis_id,
                                stock_symbol=form_data['stock_symbol'],
                                analysts=form_data['analysts'],
                                research_depth=form_data['research_depth'],
                                result_data={"error": str(e)},
                                status="failed"
                            )
                            logger.info(f"💾 [失败记录] 分析失败记录已保存: {analysis_id}")
                            
                        except Exception as save_error:
                            logger.error(f"❌ [失败记录] 保存异常: {save_error}")
                        
                        logger.error(f"❌ [分析失败] {analysis_id}: {e}")

                    finally:
                        # 分析结束后注销线程
                        from utils.thread_tracker import unregister_analysis_thread
                        unregister_analysis_thread(analysis_id)
                        logger.info(f"🧵 [线程清理] 分析线程已注销: {analysis_id}")

                # 启动后台分析线程
                analysis_thread = threading.Thread(target=run_analysis_in_background)
                analysis_thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
                analysis_thread.start()

                # 注册线程到跟踪器
                from utils.thread_tracker import register_analysis_thread
                register_analysis_thread(analysis_id, analysis_thread)

                logger.info(f"🧵 [后台分析] 分析线程已启动: {analysis_id}")

                # 分析已在后台线程中启动，显示启动信息并刷新页面
                st.success("🚀 分析已启动！正在后台运行...")

                # 显示启动信息
                st.info("⏱️ 页面将自动刷新显示分析进度...")

                # 等待2秒让用户看到启动信息，然后刷新页面
                time.sleep(2)
                st.rerun()

        # 2. 股票分析区域（只有在有分析ID时才显示）
        current_analysis_id = st.session_state.get('current_analysis_id')
        if current_analysis_id:
            st.markdown("---")

            st.header("📊 股票分析")

            # 使用线程检测来获取真实状态
            from utils.thread_tracker import check_analysis_status
            actual_status = check_analysis_status(current_analysis_id)
            is_running = (actual_status == 'running')

            # 同步session state状态
            if st.session_state.get('analysis_running', False) != is_running:
                st.session_state.analysis_running = is_running
                logger.info(f"🔄 [状态同步] 更新分析状态: {is_running} (基于线程检测: {actual_status})")

            # 获取进度数据用于显示
            from utils.async_progress_tracker import get_progress_by_id
            progress_data = get_progress_by_id(current_analysis_id)

            # 显示分析信息
            if is_running:
                st.info(f"🔄 正在分析: {current_analysis_id}")
            else:
                if actual_status == 'completed':
                    st.success(f"✅ 分析完成: {current_analysis_id}")

                elif actual_status == 'failed':
                    st.error(f"❌ 分析失败: {current_analysis_id}")
                else:
                    st.warning(f"⚠️ 分析状态未知: {current_analysis_id}")

            # 显示进度（根据状态决定是否显示刷新控件）
            progress_col1, progress_col2 = st.columns([4, 1])
            with progress_col1:
                st.markdown("### 📊 分析进度")

            is_completed = display_unified_progress(current_analysis_id, show_refresh_controls=is_running)

            # 如果分析正在进行，显示提示信息（不添加额外的自动刷新）
            if is_running:
                st.info("⏱️ 分析正在进行中，可以使用下方的自动刷新功能查看进度更新...")

            # 如果分析刚完成，尝试恢复结果
            if is_completed and not st.session_state.get('analysis_results') and progress_data:
                if 'raw_results' in progress_data:
                    try:
                        from utils.analysis_runner import format_analysis_results
                        raw_results = progress_data['raw_results']
                        formatted_results = format_analysis_results(raw_results)
                        if formatted_results:
                            st.session_state.analysis_results = formatted_results
                            st.session_state.analysis_running = False
                            logger.info(f"📊 [结果同步] 恢复分析结果: {current_analysis_id}")

                            # 自动保存分析结果到历史记录
                            try:
                                from components.analysis_results import save_analysis_result
                                
                                # 从进度数据中获取分析参数
                                stock_symbol = progress_data.get('stock_symbol', st.session_state.get('last_stock_symbol', 'unknown'))
                                analysts = progress_data.get('analysts', [])
                                research_depth = progress_data.get('research_depth', 3)
                                
                                # 保存分析结果
                                save_success = save_analysis_result(
                                    analysis_id=current_analysis_id,
                                    stock_symbol=stock_symbol,
                                    analysts=analysts,
                                    research_depth=research_depth,
                                    result_data=raw_results,
                                    status="completed"
                                )
                                
                                if save_success:
                                    logger.info(f"💾 [结果保存] 分析结果已保存到历史记录: {current_analysis_id}")
                                else:
                                    logger.warning(f"⚠️ [结果保存] 保存失败: {current_analysis_id}")
                                    
                            except Exception as save_error:
                                logger.error(f"❌ [结果保存] 保存异常: {save_error}")

                            # 检查是否已经刷新过，避免重复刷新
                            refresh_key = f"results_refreshed_{current_analysis_id}"
                            if not st.session_state.get(refresh_key, False):
                                st.session_state[refresh_key] = True
                                st.success("📊 分析结果已恢复并保存，正在刷新页面...")
                                # 使用st.rerun()代替meta refresh，保持侧边栏状态
                                time.sleep(1)
                                st.rerun()
                            else:
                                # 已经刷新过，不再刷新
                                st.success("📊 分析结果已恢复并保存！")
                    except Exception as e:
                        logger.warning(f"⚠️ [结果同步] 恢复失败: {e}")

            if is_completed and st.session_state.get('analysis_running', False):
                # 分析刚完成，更新状态
                st.session_state.analysis_running = False
                st.success("🎉 分析完成！正在刷新页面显示报告...")

                # 使用st.rerun()代替meta refresh，保持侧边栏状态
                time.sleep(1)
                st.rerun()



        # 3. 分析报告区域（只有在有结果且分析完成时才显示）

        current_analysis_id = st.session_state.get('current_analysis_id')
        analysis_results = st.session_state.get('analysis_results')
        analysis_running = st.session_state.get('analysis_running', False)

        # 检查是否应该显示分析报告
        # 1. 有分析结果且不在运行中
        # 2. 或者用户点击了"查看报告"按钮
        show_results_button_clicked = st.session_state.get('show_analysis_results', False)

        should_show_results = (
            (analysis_results and not analysis_running and current_analysis_id) or
            (show_results_button_clicked and analysis_results)
        )

        # 调试日志
        logger.info(f"🔍 [布局调试] 分析报告显示检查:")
        logger.info(f"  - analysis_results存在: {bool(analysis_results)}")
        logger.info(f"  - analysis_running: {analysis_running}")
        logger.info(f"  - current_analysis_id: {current_analysis_id}")
        logger.info(f"  - show_results_button_clicked: {show_results_button_clicked}")
        logger.info(f"  - should_show_results: {should_show_results}")

        if should_show_results:
            st.markdown("---")
            st.header("📋 分析报告")
            render_results(analysis_results)
            logger.info(f"✅ [布局] 分析报告已显示")

            # 清除查看报告按钮状态，避免重复触发
            if show_results_button_clicked:
                st.session_state.show_analysis_results = False
    
    # 只有在显示指南时才渲染右侧内容
    if show_guide and col2 is not None:
        with col2:
            st.markdown("### ℹ️ 使用指南")
        
            # 快速开始指南
            with st.expander("🎯 快速开始", expanded=True):
                st.markdown("""
                ### 📋 操作步骤

                1. **输入股票代码**
                   - A股示例: `000001` (平安银行), `600519` (贵州茅台), `000858` (五粮液)
                   - 美股示例: `AAPL` (苹果), `TSLA` (特斯拉), `MSFT` (微软)
                   - 港股示例: `00700` (腾讯), `09988` (阿里巴巴)

                   ⚠️ **重要提示**: 输入股票代码后，请按 **回车键** 确认输入！

                2. **选择分析日期**
                   - 默认为今天
                   - 可选择历史日期进行回测分析

                3. **选择分析师团队**
                   - 至少选择一个分析师
                   - 建议选择多个分析师获得全面分析

                4. **设置研究深度**
                   - 1-2级: 快速概览
                   - 3级: 标准分析 (推荐)
                   - 4-5级: 深度研究

                5. **点击开始分析**
                   - 等待AI分析完成
                   - 查看详细分析报告

                ### 💡 使用技巧

                - **A股默认**: 系统默认分析A股，无需特殊设置
                - **代码格式**: A股使用6位数字代码 (如 `000001`)
                - **实时数据**: 获取最新的市场数据和新闻
                - **多维分析**: 结合技术面、基本面、情绪面分析
                """)

            # 分析师说明
            with st.expander("👥 分析师团队说明"):
                st.markdown("""
                ### 🎯 专业分析师团队

                - **📈 市场分析师**:
                  - 技术指标分析 (K线、均线、MACD等)
                  - 价格趋势预测
                  - 支撑阻力位分析

                - **💭 社交媒体分析师**:
                  - 投资者情绪监测
                  - 社交媒体热度分析
                  - 市场情绪指标

                - **📰 新闻分析师**:
                  - 重大新闻事件影响
                  - 政策解读分析
                  - 行业动态跟踪

                - **💰 基本面分析师**:
                  - 财务报表分析
                  - 估值模型计算
                  - 行业对比分析
                  - 盈利能力评估

                💡 **建议**: 选择多个分析师可获得更全面的投资建议
                """)

            # 模型选择说明
            with st.expander("🧠 AI模型说明"):
                st.markdown("""
                ### 🤖 智能模型选择

                - **qwen-turbo**:
                  - 快速响应，适合快速查询
                  - 成本较低，适合频繁使用
                  - 响应时间: 2-5秒

                - **qwen-plus**:
                  - 平衡性能，推荐日常使用 ⭐
                  - 准确性与速度兼顾
                  - 响应时间: 5-10秒

                - **qwen-max**:
                  - 最强性能，适合深度分析
                  - 最高准确性和分析深度
                  - 响应时间: 10-20秒

                💡 **推荐**: 日常分析使用 `qwen-plus`，重要决策使用 `qwen-max`
                """)

            # 常见问题
            with st.expander("❓ 常见问题"):
                st.markdown("""
                ### 🔍 常见问题解答

                **Q: 为什么输入股票代码没有反应？**
                A: 请确保输入代码后按 **回车键** 确认，这是Streamlit的默认行为。

                **Q: A股代码格式是什么？**
                A: A股使用6位数字代码，如 `000001`、`600519`、`000858` 等。

                **Q: 分析需要多长时间？**
                A: 根据研究深度和模型选择，通常需要30秒到2分钟不等。

                **Q: 可以分析港股吗？**
                A: 可以，输入5位港股代码，如 `00700`、`09988` 等。

                **Q: 历史数据可以追溯多久？**
                A: 通常可以获取近5年的历史数据进行分析。
                """)

            # 风险提示
            st.warning("""
            ⚠️ **投资风险提示**

            - 本系统提供的分析结果仅供参考，不构成投资建议
            - 投资有风险，入市需谨慎，请理性投资
            - 请结合多方信息和专业建议进行投资决策
            - 重大投资决策建议咨询专业的投资顾问
            - AI分析存在局限性，市场变化难以完全预测
            """)
        
        # 显示系统状态
        if st.session_state.last_analysis_time:
            st.info(f"🕒 上次分析时间: {st.session_state.last_analysis_time.strftime('%Y-%m-%d %H:%M:%S')}")


def render_batch_analysis_page():
    """渲染批量分析页面"""
    
    # 页面标题
    st.header("📈 批量股票分析")
    st.markdown("---")
    
    # 检查API密钥
    from utils.api_checker import check_api_keys
    api_status = check_api_keys()
    
    if not api_status['all_configured']:
        st.error("⚠️ API密钥配置不完整，请先配置必要的API密钥")
        
        with st.expander("📋 API密钥配置指南", expanded=True):
            st.markdown("""
            ### 🔑 必需的API密钥
            
            1. **阿里百炼API密钥** (DASHSCOPE_API_KEY)
               - 获取地址: https://dashscope.aliyun.com/
               - 用途: AI模型推理
            
            2. **金融数据API密钥** (FINNHUB_API_KEY)  
               - 获取地址: https://finnhub.io/
               - 用途: 获取股票数据
            
            ### ⚙️ 配置方法
            
            1. 复制项目根目录的 `.env.example` 为 `.env`
            2. 编辑 `.env` 文件，填入您的真实API密钥
            3. 重启Web应用
            
            ```bash
            # .env 文件示例
            DASHSCOPE_API_KEY=sk-your-dashscope-key
            FINNHUB_API_KEY=your-finnhub-key
            ```
            """)
        
        # 显示当前API密钥状态
        st.subheader("🔍 当前API密钥状态")
        for key, status in api_status['details'].items():
            if status['configured']:
                st.success(f"✅ {key}: {status['display']}")
            else:
                st.error(f"❌ {key}: 未配置")
        
        return
    
    # 获取配置
    from components.sidebar import render_sidebar
    config = render_sidebar()
    
    # 初始化批量分析状态
    if 'batch_analysis_results' not in st.session_state:
        st.session_state.batch_analysis_results = None
    if 'batch_analysis_running' not in st.session_state:
        st.session_state.batch_analysis_running = False
    if 'current_batch_id' not in st.session_state:
        st.session_state.current_batch_id = None
    
    # 0. 认证校验（仅批量分析板块）
    try:
        from utils.license_manager import get_or_create_machine_code, is_activated, verify_and_activate, expected_password
        if not is_activated():
            st.warning("🔒 批量分析功能需激活后使用")
            mc = get_or_create_machine_code()
            st.info(f"🖥️ 机器码: {mc}")
            pwd = st.text_input("请输入激活码", type="password", help="联系管理员获取计算规则或按提示计算")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ 激活"):
                    ok, msg = verify_and_activate(pwd)
                    if ok:
                        st.success(msg)
                        st.experimental_rerun()
                    else:
                        st.error(msg)
            with col_b:
                if st.button("🧮 查看当前计算样例"):
                    now = datetime.datetime.now()
                    st.caption(f"当前时间: {now.strftime('%Y-%m-%d %H:%M')}  计算结果示例: {(expected_password(now, mc))}")
            return
    except Exception as e:
        st.error(f"授权模块异常: {e}")
        return

    # 1. 批量分析配置区域
    st.subheader("⚙️ 批量分析配置")
    
    # 渲染批量分析表单
    try:
        from components.batch_analysis_form import render_batch_analysis_form
        form_data = render_batch_analysis_form()
        
        # 验证表单数据格式
        if not isinstance(form_data, dict):
            st.error(f"⚠️ 表单数据格式异常: {type(form_data)}")
            form_data = {'submitted': False}
            
    except Exception as e:
        st.error(f"❌ 表单渲染失败: {e}")
        form_data = {'submitted': False}
    
    # 检查是否提交了批量分析表单
    if form_data.get('submitted', False) and not st.session_state.get('batch_analysis_running', False):
        # 验证分析参数
        from utils.analysis_runner import validate_analysis_params
        
        # 验证每个股票代码
        validation_errors = []
        for stock_symbol in form_data['stock_symbols']:
            is_valid, errors = validate_analysis_params(
                stock_symbol=stock_symbol,
                analysis_date=form_data['analysis_date'],
                analysts=form_data['analysts'],
                research_depth=form_data['research_depth'],
                market_type=form_data.get('market_type', '美股')
            )
            if not is_valid:
                validation_errors.extend([f"{stock_symbol}: {error}" for error in errors])
        
        if validation_errors:
            # 显示验证错误
            for error in validation_errors:
                st.error(error)
        else:
            # 执行批量分析
            st.session_state.batch_analysis_running = True
            
            # 清空旧的批量分析结果
            st.session_state.batch_analysis_results = None
            logger.info("🧹 [批量分析] 清空旧的批量分析结果")
            
            # 生成批量分析ID
            import uuid
            batch_id = f"batch_{uuid.uuid4().hex[:8]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 保存批量分析ID
            st.session_state.current_batch_id = batch_id
            
            # 显示启动信息
            st.success(f"🚀 批量分析已启动！分析ID: {batch_id}")
            st.info(f"📊 正在分析 {len(form_data['stock_symbols'])} 个股票: {', '.join(form_data['stock_symbols'])}")
            
            # 初始化进度状态
            st.session_state.batch_progress_info = {
                'current_stock': '',
                'current_index': 0,
                'total_stocks': len(form_data['stock_symbols']),
                'progress': 0,
                'status': '准备中...'
            }
            st.session_state.completed_stocks = []
            
            # 创建进度回调函数
            def progress_callback(progress_data):
                """实时更新进度信息"""
                if not isinstance(progress_data, dict):
                    return
                
                ptype = progress_data.get('type')
                
                if ptype == 'stock_start':
                    # 开始分析某只股票
                    st.session_state.batch_progress_info.update({
                        'current_stock': progress_data.get('stock_symbol', ''),
                        'current_index': progress_data.get('current_index', 0),
                        'total_stocks': progress_data.get('total_stocks', st.session_state.batch_progress_info.get('total_stocks', 0)),
                        'progress': progress_data.get('progress', st.session_state.batch_progress_info.get('progress', 0)),
                        'status': progress_data.get('message', '开始分析...'),
                        'start_time': st.session_state.batch_progress_info.get('start_time', time.time())
                    })
                
                elif ptype == 'stock_progress':
                    # 更新当前分析状态
                    st.session_state.batch_progress_info.update({
                        'current_stock': progress_data.get('stock_symbol', ''),
                        'current_index': progress_data.get('current_index', 0),
                        'total_stocks': progress_data.get('total_stocks', 0),
                        'progress': progress_data.get('progress', 0),
                        'status': progress_data.get('message', '分析中...')
                    })
                    
                elif ptype == 'stock_completed':
                    # 股票分析完成，添加到已完成列表
                    stock_symbol = progress_data.get('stock_symbol', '')
                    success = progress_data.get('success', False)
                    
                    if success:
                        result = progress_data.get('result', {})
                        # 添加投资建议到结果中
                        decision = result.get('decision', {})
                        result['action'] = decision.get('action', 'N/A')
                        result['stock_symbol'] = stock_symbol
                        result['success'] = True
                        result['analysis_time'] = result.get('analysis_time', time.time())
                    else:
                        result = {
                            'stock_symbol': stock_symbol,
                            'success': False,
                            'error': progress_data.get('error', '未知错误'),
                            'analysis_time': progress_data.get('analysis_time', time.time())
                        }
                    
                    # 添加到已完成列表
                    if 'completed_stocks' not in st.session_state:
                        st.session_state.completed_stocks = []
                    st.session_state.completed_stocks.append(result)
                    
                    # 更新进度
                    st.session_state.batch_progress_info.update({
                        'current_stock': stock_symbol,
                        'current_index': progress_data.get('current_index', 0),
                        'total_stocks': progress_data.get('total_stocks', 0),
                        'progress': progress_data.get('progress', 0),
                        'status': f"✅ {stock_symbol} 分析完成"
                    })
                    
                elif ptype == 'waiting':
                    # 等待状态
                    st.session_state.batch_progress_info.update({
                        'status': progress_data.get('message', '等待中...')
                    })
                elif ptype == 'batch_completed':
                    st.session_state.batch_progress_info.update({
                        'status': progress_data.get('message', '批量完成'),
                        'progress': 100
                    })
            
            # 改为同步顺序执行（不使用后台线程）
            st.info("🔄 正在顺序分析每只股票（每只股票需时10-20分钟，请耐心等待），结果会即时显示")
            progress_placeholder = st.empty()
            list_container = st.container()
            total = len(form_data['stock_symbols'])
            completed_items = []

            def update_ui_progress(index: int, fine: float, status_text: str):
                overall = ((index - 1) + fine) / max(1, total)
                st.session_state.batch_progress_info.update({
                    'current_index': index,
                    'total_stocks': total,
                    'progress': overall * 100,
                    'status': status_text
                })
                progress_placeholder.progress(overall)

            for idx, stock_symbol in enumerate(form_data['stock_symbols'], start=1):
                # 开始提示
                progress_callback({
                    'type': 'stock_start',
                    'stock_symbol': stock_symbol,
                    'current_index': idx,
                    'total_stocks': total,
                    'progress': (idx - 1) / max(1, total) * 100,
                    'message': f"开始分析第 {idx}/{total} 个股票: {stock_symbol}"
                })
                update_ui_progress(idx, 0.0, f"正在分析 {stock_symbol} ...")

                # 执行单只股票分析
                from utils.analysis_runner import run_stock_analysis, format_analysis_results
                start_ts = time.time()

                def single_cb(msg, s=None, t=None):
                    fine = 0.0
                    if s is not None and t:
                        try:
                            fine = max(0.0, min(1.0, float(s)/float(t)))
                        except Exception:
                            fine = 0.0
                    update_ui_progress(idx, fine, msg or '分析中...')
                    progress_callback({
                        'type': 'stock_progress',
                        'stock_symbol': stock_symbol,
                        'message': msg,
                        'step': s,
                        'total_steps': t,
                        'current_index': idx,
                        'total_stocks': total,
                        'progress': ((idx - 1) + fine) / max(1, total) * 100
                    })

                try:
                    single = run_stock_analysis(
                        stock_symbol=stock_symbol,
                        analysis_date=form_data['analysis_date'],
                        analysts=form_data['analysts'],
                        research_depth=form_data['research_depth'],
                        llm_provider=config['llm_provider'],
                        llm_model=config['llm_model'],
                        market_type=form_data.get('market_type', '美股'),
                        progress_callback=single_cb
                    )
                    duration = time.time() - start_ts
                    if single.get('success'):
                        formatted = format_analysis_results(single)
                        formatted['stock_symbol'] = stock_symbol
                        formatted['analysis_time'] = time.time()
                        formatted['analysis_duration'] = duration
                        formatted['success'] = True
                        completed_items.append(formatted)
                        st.session_state.completed_stocks.append(formatted)
                        st.session_state.batch_progress_info.update({'status': f"✅ {stock_symbol} 分析完成"})
                        progress_callback({
                            'type': 'stock_completed',
                            'stock_symbol': stock_symbol,
                            'success': True,
                            'result': formatted,
                            'current_index': idx,
                            'total_stocks': total,
                            'progress': idx / max(1, total) * 100
                        })
                    else:
                        err = {
                            'stock_symbol': stock_symbol,
                            'success': False,
                            'error': single.get('error', '未知错误'),
                            'analysis_time': time.time()
                        }
                        completed_items.append(err)
                        st.session_state.completed_stocks.append(err)
                        st.session_state.batch_progress_info.update({'status': f"❌ {stock_symbol} 分析失败"})
                        progress_callback({
                            'type': 'stock_completed',
                            'stock_symbol': stock_symbol,
                            'success': False,
                            'error': err['error'],
                            'current_index': idx,
                            'total_stocks': total,
                            'progress': idx / max(1, total) * 100
                        })
                except Exception as e:
                    err = {
                        'stock_symbol': stock_symbol,
                        'success': False,
                        'error': str(e),
                        'analysis_time': time.time()
                    }
                    completed_items.append(err)
                    st.session_state.completed_stocks.append(err)
                    st.session_state.batch_progress_info.update({'status': f"❌ {stock_symbol} 分析异常"})
                    progress_callback({
                        'type': 'stock_completed',
                        'stock_symbol': stock_symbol,
                        'success': False,
                        'error': str(e),
                        'current_index': idx,
                        'total_stocks': total,
                        'progress': idx / max(1, total) * 100
                    })

                # 分段渲染
                from components.batch_progress_display import render_batch_progress_display
                render_batch_progress_display(batch_id, st.session_state.batch_progress_info, st.session_state.completed_stocks)

                # 可选间隔
                wait_s = int(form_data.get('analysis_interval', 0) or 0)
                if idx < total and wait_s > 0:
                    st.session_state.batch_progress_info.update({'status': f"⏱️ 等待 {wait_s} 秒后继续"})
                    time.sleep(min(wait_s, 5))

            # 完成汇总
            st.session_state.batch_analysis_results = {
                'batch_id': batch_id,
                'total_stocks': total,
                'results': {item.get('stock_symbol', f'stock_{i}'): item for i, item in enumerate(completed_items)},
                'successful_count': sum(1 for x in completed_items if x.get('success')),
                'failed_count': sum(1 for x in completed_items if not x.get('success')),
                'success_rate': (sum(1 for x in completed_items if x.get('success')) / max(1, total)) * 100,
                'errors': [f"{x.get('stock_symbol')}: {x.get('error')}" for x in completed_items if not x.get('success')],
            }
            st.session_state.batch_analysis_running = False
            st.session_state.batch_progress_info.update({'status': '✅ 批量分析完成', 'progress': 100})
            st.success('🎉 批量分析完成！')
    
    # 2. 批量分析进度区域
    current_batch_id = st.session_state.get('current_batch_id')
    if current_batch_id:
        st.markdown("---")
        st.subheader("📊 批量分析进度")
        
        if st.session_state.get('batch_analysis_running', False):
            # 显示当前分析状态
            st.info(f"🔄 正在批量分析: {current_batch_id}")
            
            # 使用新的进度显示组件
            try:
                from components.batch_progress_display import render_batch_progress_display, render_progress_summary, create_progress_chart
                
                # 优先从线程安全存储读取快照，避免session_state线程冲突
                try:
                    from utils.batch_progress_store import get_snapshot as get_batch_snapshot
                    snapshot = get_batch_snapshot(current_batch_id)
                    progress_info = snapshot.get('progress_info', st.session_state.get('batch_progress_info', {}))
                    completed_stocks = snapshot.get('completed_stocks', st.session_state.get('completed_stocks', []))
                except Exception:
                    progress_info = st.session_state.get('batch_progress_info', {})
                    completed_stocks = st.session_state.get('completed_stocks', [])
                
                # 渲染进度显示（保证completed_stocks含有必要字段）
                safe_completed = []
                for item in completed_stocks:
                    if not isinstance(item, dict):
                        continue
                    # 兼容：如果result已是格式化对象，则直接使用
                    if item.get('success', False) and 'decision' in item:
                        safe_completed.append(item)
                        continue
                    # 如果是回调原始对象，提升result为一级字段
                    if 'result' in item and isinstance(item['result'], dict):
                        merged = {**item['result']}
                        merged['stock_symbol'] = merged.get('stock_symbol', item.get('stock_symbol'))
                        merged['success'] = True
                        merged['analysis_time'] = merged.get('analysis_time', item.get('analysis_time', time.time()))
                        safe_completed.append(merged)
                        continue
                    # 失败项直接透传
                    safe_completed.append(item)

                render_batch_progress_display(current_batch_id, progress_info, safe_completed)
                
                # 显示进度摘要
                summary_data = render_progress_summary(progress_info, completed_stocks)
                if summary_data:
                    st.markdown("---")
                    st.subheader("📋 进度摘要")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("当前股票", summary_data.get('当前股票', 'N/A'))
                        st.metric("分析进度", summary_data.get('分析进度', 'N/A'))
                    
                    with col2:
                        st.metric("完成率", summary_data.get('完成率', '0%'))
                        st.metric("已完成数量", summary_data.get('已完成数量', 0))
                    
                    with col3:
                        st.metric("当前状态", summary_data.get('当前状态', '准备中...'))
                        st.caption(summary_data.get('时间估算', ''))
                
                # 显示进度图表
                if completed_stocks:
                    chart = create_progress_chart(completed_stocks)
                    if chart:
                        st.markdown("---")
                        st.subheader("📊 分析结果可视化")
                        st.plotly_chart(chart, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ 进度显示失败: {e}")
                # 回退到简单显示
                st.info("⏱️ 批量分析正在进行中，请耐心等待...")
            
            # 仅提供手动刷新按钮，避免频繁自动rerun导致登录状态丢失
            if st.session_state.get('batch_analysis_running', False):
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 刷新进度", help="手动刷新分析进度"):
                        st.rerun()
        else:
            st.success(f"✅ 批量分析完成: {current_batch_id}")
    
    # 3. 批量分析结果区域
    batch_results = st.session_state.get('batch_analysis_results')
    if batch_results and not st.session_state.get('batch_analysis_running', False):
        st.markdown("---")
        st.subheader("📋 批量分析结果")
        
        # 渲染批量分析结果
        try:
            from components.batch_results_display import render_batch_results
            render_batch_results(batch_results)
            
            # 导出报告功能（新增 Word/PDF 下载按钮，与单股一致的交互）
            st.markdown("---")
            st.subheader("📄 报告导出")

            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

            def _download_button(label, file_path, mime=None):
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    st.download_button(
                        label=label,
                        data=data,
                        file_name=os.path.basename(file_path),
                        mime=mime
                    )
                except Exception as _:
                    st.error("❌ 找不到已生成的文件，请先点击对应导出按钮生成")

            with col1:
                if st.button("📄 生成Markdown", help="生成Markdown报告"):
                    try:
                        from utils.batch_report_exporter import export_batch_report
                        export_result = export_batch_report(batch_results, "Markdown", True)
                        if export_result['success']:
                            st.success(f"✅ 已生成: {export_result['filename']}")
                            _download_button("⬇️ 下载Markdown", export_result['file_path'], "text/markdown")
                        else:
                            st.error(f"❌ 导出失败: {export_result['error']}")
                    except Exception as e:
                        st.error(f"❌ 导出失败: {e}")

            with col2:
                if st.button("📊 生成Excel", help="生成Excel报告"):
                    try:
                        from utils.batch_report_exporter import export_batch_report
                        export_result = export_batch_report(batch_results, "Excel", True)
                        if export_result['success']:
                            st.success(f"✅ 已生成: {export_result['filename']}")
                            _download_button("⬇️ 下载Excel", export_result['file_path'], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                        else:
                            st.error(f"❌ 导出失败: {export_result['error']}")
                    except Exception as e:
                        st.error(f"❌ 导出失败: {e}")

            with col3:
                if st.button("🧾 生成JSON", help="生成JSON报告"):
                    try:
                        from utils.batch_report_exporter import export_batch_report
                        export_result = export_batch_report(batch_results, "JSON", True)
                        if export_result['success']:
                            st.success(f"✅ 已生成: {export_result['filename']}")
                            _download_button("⬇️ 下载JSON", export_result['file_path'], "application/json")
                        else:
                            st.error(f"❌ 导出失败: {export_result['error']}")
                    except Exception as e:
                        st.error(f"❌ 导出失败: {e}")

            with col4:
                if st.button("📄 生成汇总Word", help="生成批量汇总的docx报告（与单股导出一致）"):
                    try:
                        from utils.batch_report_exporter import export_batch_report
                        res = export_batch_report(batch_results, "DOCX", True)
                        if res['success']:
                            st.success(f"✅ 已生成: {res['filename']}")
                            _download_button("⬇️ 下载汇总Word", res['file_path'], "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                        else:
                            st.error(f"❌ 导出失败: {res['error']}")
                    except Exception as e:
                        st.error(f"❌ 导出失败: {e}")

            with col5:
                if st.button("🖨️ 生成汇总PDF(HTML)", help="生成HTML，可在本地浏览器打印为PDF"):
                    try:
                        from utils.batch_report_exporter import export_batch_report
                        pdf_res = export_batch_report(batch_results, "PDF", True)
                        if pdf_res['success']:
                            st.success(f"✅ 已生成HTML: {pdf_res['filename']}，用浏览器打开并打印为PDF")
                            _download_button("⬇️ 下载HTML(用于PDF)", pdf_res['file_path'], "text/html")
                        else:
                            st.error(f"❌ 导出失败: {pdf_res['error']}")
                    except Exception as e:
                        st.error(f"❌ 导出失败: {e}")

            with col6:
                if st.button("📦 每股Word打包", help="为每只股票生成docx并打包zip"):
                    try:
                        from utils.batch_report_exporter import export_batch_report
                        res = export_batch_report(batch_results, "ZIP_DOCX", True)
                        if res['success']:
                            st.success(f"✅ 已生成: {res['filename']}")
                            _download_button("⬇️ 下载ZIP(DOCX)", res['file_path'], "application/zip")
                        else:
                            st.error(f"❌ 导出失败: {res['error']}")
                    except Exception as e:
                        st.error(f"❌ 导出失败: {e}")

            with col7:
                if st.button("📦 每股PDF打包", help="为每只股票生成pdf并打包zip"):
                    try:
                        from utils.batch_report_exporter import export_batch_report
                        res = export_batch_report(batch_results, "ZIP_PDF", True)
                        if res['success']:
                            st.success(f"✅ 已生成: {res['filename']}")
                            _download_button("⬇️ 下载ZIP(PDF)", res['file_path'], "application/zip")
                        else:
                            st.error(f"❌ 导出失败: {res['error']}")
                    except Exception as e:
                        st.error(f"❌ 导出失败: {e}")
            
        except Exception as e:
            st.error(f"❌ 结果渲染失败: {e}")
    
    # 4. 使用指南
    with st.expander("📖 批量分析使用指南", expanded=False):
        st.markdown("""
        ### 🎯 批量分析功能说明
        
        **功能特点**:
        - 支持同时分析多个股票
        - 自动生成汇总报告
        - 支持多种导出格式
        - 智能风险分析
        
        **使用步骤**:
        1. **输入股票代码**: 支持逗号或换行分隔
        2. **选择市场类型**: A股、美股、港股
        3. **设置分析参数**: 研究深度、分析师团队
        4. **开始批量分析**: 系统将逐个分析股票
        5. **查看分析结果**: 包含汇总报告和详细分析
        6. **导出分析报告**: 支持Markdown、Excel、JSON格式
        
        **注意事项**:
        - 批量分析需要较长时间，请耐心等待
        - 建议设置合理的分析间隔，避免API限制
        - 分析结果会自动保存，可随时查看
        - 支持导出报告，便于离线查看
        
        **投资风险提示**:
        - 本系统提供的分析结果仅供参考
        - 投资有风险，入市需谨慎
        - 请结合多方信息做出投资决策
        """)

if __name__ == "__main__":
    main()
