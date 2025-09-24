#!/usr/bin/env python3
"""
批量分析功能演示脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_batch_analysis_form():
    """演示批量分析表单功能"""
    
    print("📋 批量分析表单功能演示")
    print("=" * 40)
    
    try:
        from web.components.batch_analysis_form import parse_stock_symbols, validate_and_format_symbol
        
        # 演示股票代码解析
        print("🔍 股票代码解析演示:")
        
        # 美股示例
        us_stocks = "AAPL,TSLA,MSFT\nGOOGL,AMZN"
        print(f"输入: {us_stocks}")
        parsed_us = parse_stock_symbols(us_stocks, "美股")
        print(f"解析结果: {parsed_us}")
        
        # A股示例
        cn_stocks = "000001,600519,000858"
        print(f"\n输入: {cn_stocks}")
        parsed_cn = parse_stock_symbols(cn_stocks, "A股")
        print(f"解析结果: {parsed_cn}")
        
        # 港股示例
        hk_stocks = "0700.HK,9988.HK\n3690"
        print(f"\n输入: {hk_stocks}")
        parsed_hk = parse_stock_symbols(hk_stocks, "港股")
        print(f"解析结果: {parsed_hk}")
        
        # 演示股票代码验证
        print("\n✅ 股票代码验证演示:")
        test_cases = [
            ("AAPL", "美股"),
            ("000001", "A股"),
            ("0700.HK", "港股"),
            ("0700", "港股"),
            ("INVALID", "美股")
        ]
        
        for symbol, market in test_cases:
            try:
                validated = validate_and_format_symbol(symbol, market)
                print(f"✅ {symbol} ({market}) -> {validated}")
            except Exception as e:
                print(f"❌ {symbol} ({market}) -> 验证失败: {e}")
        
        print("\n🎉 批量分析表单功能演示完成！")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

def demo_batch_analysis_runner():
    """演示批量分析执行器功能"""
    
    print("\n🚀 批量分析执行器功能演示")
    print("=" * 40)
    
    try:
        from web.utils.batch_analysis_runner import BatchAnalysisRunner
        
        # 创建批量分析执行器
        batch_id = "demo_batch_123"
        runner = BatchAnalysisRunner(batch_id)
        print(f"✅ 批量分析执行器创建成功: {batch_id}")
        
        # 模拟批量分析结果
        mock_results = {
            'AAPL': {
                'success': True,
                'decision': {
                    'action': '买入',
                    'confidence': 0.85,
                    'risk_score': 0.3,
                    'target_price': 180.0,
                    'reasoning': '技术面突破，基本面强劲'
                }
            },
            'TSLA': {
                'success': True,
                'decision': {
                    'action': '持有',
                    'confidence': 0.65,
                    'risk_score': 0.5,
                    'target_price': 250.0,
                    'reasoning': '波动较大，需要观察'
                }
            },
            'INVALID': {
                'success': False,
                'error': '股票代码无效'
            }
        }
        
        # 设置模拟结果
        runner.results = mock_results
        runner.status = "completed"
        
        # 生成汇总报告
        summary_report = runner._generate_summary_report()
        print("📊 汇总报告生成:")
        print(f"  - 总股票数: {summary_report['overview']['total_stocks']}")
        print(f"  - 成功分析: {summary_report['overview']['successful_analyses']}")
        print(f"  - 失败分析: {summary_report['overview']['failed_analyses']}")
        print(f"  - 成功率: {summary_report['overview']['success_rate'] * 100:.1f}%")
        
        print(f"  - 买入: {summary_report['investment_recommendations']['buy_count']} 个")
        print(f"  - 卖出: {summary_report['investment_recommendations']['sell_count']} 个")
        print(f"  - 持有: {summary_report['investment_recommendations']['hold_count']} 个")
        
        print(f"  - 平均置信度: {summary_report['risk_metrics']['average_confidence'] * 100:.1f}%")
        print(f"  - 平均风险分数: {summary_report['risk_metrics']['average_risk_score'] * 100:.1f}%")
        
        print("\n🎉 批量分析执行器功能演示完成！")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

def demo_batch_report_exporter():
    """演示批量分析报告导出功能"""
    
    print("\n📄 批量分析报告导出功能演示")
    print("=" * 40)
    
    try:
        from web.utils.batch_report_exporter import BatchReportExporter
        
        # 模拟批量分析结果
        mock_batch_results = {
            'batch_id': 'demo_batch_123',
            'total_stocks': 3,
            'successful_analyses': 2,
            'failed_analyses': 1,
            'analysis_date': '2024-01-15',
            'market_type': '美股',
            'research_depth': 3,
            'analysts': ['market', 'fundamentals'],
            'summary_report': {
                'overview': {
                    'total_stocks': 3,
                    'successful_analyses': 2,
                    'failed_analyses': 1,
                    'success_rate': 0.67
                },
                'investment_recommendations': {
                    'buy_count': 1,
                    'sell_count': 0,
                    'hold_count': 1,
                    'buy_percentage': 0.5,
                    'sell_percentage': 0.0,
                    'hold_percentage': 0.5
                },
                'risk_metrics': {
                    'average_confidence': 0.75,
                    'average_risk_score': 0.4,
                    'high_confidence_stocks': 1,
                    'low_risk_stocks': 1
                }
            },
            'results': {
                'AAPL': {
                    'success': True,
                    'decision': {
                        'action': '买入',
                        'confidence': 0.85,
                        'risk_score': 0.3,
                        'target_price': 180.0,
                        'reasoning': '技术面突破，基本面强劲'
                    }
                },
                'TSLA': {
                    'success': True,
                    'decision': {
                        'action': '持有',
                        'confidence': 0.65,
                        'risk_score': 0.5,
                        'target_price': 250.0,
                        'reasoning': '波动较大，需要观察'
                    }
                },
                'INVALID': {
                    'success': False,
                    'error': '股票代码无效'
                }
            }
        }
        
        # 创建报告导出器
        exporter = BatchReportExporter(mock_batch_results)
        print("✅ 批量分析报告导出器创建成功")
        
        # 演示Markdown报告生成
        print("📝 生成Markdown报告内容:")
        markdown_content = exporter._generate_markdown_content(include_summary=True)
        print("报告预览（前500字符）:")
        print(markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content)
        
        print("\n🎉 批量分析报告导出功能演示完成！")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

def main():
    """主演示函数"""
    
    print("🚀 批量股票分析功能演示")
    print("=" * 50)
    
    # 演示各个组件
    form_demo = demo_batch_analysis_form()
    runner_demo = demo_batch_analysis_runner()
    exporter_demo = demo_batch_report_exporter()
    
    print("\n" + "=" * 50)
    if form_demo and runner_demo and exporter_demo:
        print("🎉 所有演示完成！批量分析功能运行正常")
        
        print("\n📋 功能总结:")
        print("✅ 股票代码解析和验证")
        print("✅ 批量分析执行器")
        print("✅ 汇总报告生成")
        print("✅ 多格式报告导出")
        print("✅ 错误处理机制")
        
        print("\n🚀 下一步:")
        print("1. 启动Web应用: python -m streamlit run web/app.py")
        print("2. 在浏览器中访问应用")
        print("3. 选择 '📈 批量分析' 功能")
        print("4. 输入股票代码开始批量分析")
        
        return True
    else:
        print("❌ 演示过程中出现错误")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
