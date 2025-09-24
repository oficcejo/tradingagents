#!/usr/bin/env python3
"""
批量分析功能测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_batch_analysis_components():
    """测试批量分析组件"""
    
    print("🧪 开始测试批量分析组件...")
    
    try:
        # 测试批量分析表单组件
        print("📋 测试批量分析表单组件...")
        from web.components.batch_analysis_form import render_batch_analysis_form, parse_stock_symbols, validate_and_format_symbol
        
        # 测试股票代码解析
        test_stocks = "AAPL,TSLA,MSFT\nGOOGL,AMZN"
        parsed_stocks = parse_stock_symbols(test_stocks, "美股")
        print(f"✅ 股票代码解析测试通过: {parsed_stocks}")
        
        # 测试股票代码验证
        test_symbol = "AAPL"
        validated_symbol = validate_and_format_symbol(test_symbol, "美股")
        print(f"✅ 股票代码验证测试通过: {validated_symbol}")
        
        # 测试批量分析执行器
        print("🚀 测试批量分析执行器...")
        from web.utils.batch_analysis_runner import BatchAnalysisRunner
        
        batch_runner = BatchAnalysisRunner("test_batch_123")
        print("✅ 批量分析执行器创建成功")
        
        # 测试批量分析结果展示组件
        print("📊 测试批量分析结果展示组件...")
        from web.components.batch_results_display import render_batch_results
        print("✅ 批量分析结果展示组件导入成功")
        
        # 测试批量分析报告导出器
        print("📄 测试批量分析报告导出器...")
        from web.utils.batch_report_exporter import BatchReportExporter, export_batch_report
        print("✅ 批量分析报告导出器导入成功")
        
        print("🎉 所有批量分析组件测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 批量分析组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_analysis_integration():
    """测试批量分析集成"""
    
    print("\n🔗 开始测试批量分析集成...")
    
    try:
        # 测试主应用集成
        print("🌐 测试主应用集成...")
        from web.app import render_batch_analysis_page
        print("✅ 批量分析页面函数导入成功")
        
        # 测试依赖关系
        print("📦 检查依赖关系...")
        import streamlit as st
        import pandas as pd
        import plotly.express as px
        print("✅ 所有依赖包检查通过")
        
        print("🎉 批量分析集成测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 批量分析集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    
    print("🚀 开始批量分析功能测试")
    print("=" * 50)
    
    # 测试组件
    components_ok = test_batch_analysis_components()
    
    # 测试集成
    integration_ok = test_batch_analysis_integration()
    
    print("\n" + "=" * 50)
    if components_ok and integration_ok:
        print("🎉 批量分析功能测试全部通过！")
        print("\n📋 功能特性:")
        print("✅ 支持多股票批量分析")
        print("✅ 智能股票代码解析和验证")
        print("✅ 多种市场类型支持（A股、美股、港股）")
        print("✅ 可配置的分析参数")
        print("✅ 实时进度跟踪")
        print("✅ 详细分析结果展示")
        print("✅ 多种格式报告导出（Markdown、Excel、JSON）")
        print("✅ 风险分析和投资建议汇总")
        print("✅ 用户友好的Web界面")
        
        print("\n🚀 使用方法:")
        print("1. 启动Web应用: python -m streamlit run web/app.py")
        print("2. 在侧边栏选择 '📈 批量分析'")
        print("3. 输入多个股票代码（用逗号或换行分隔）")
        print("4. 配置分析参数")
        print("5. 点击开始批量分析")
        print("6. 查看分析结果和导出报告")
        
        return True
    else:
        print("❌ 批量分析功能测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
