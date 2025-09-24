"""
批量分析报告导出工具
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import markdown
from io import BytesIO
import base64

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('web')


class BatchReportExporter:
    """批量分析报告导出器"""
    
    def __init__(self, batch_results: Dict[str, Any]):
        self.batch_results = batch_results
        self.batch_id = batch_results.get('batch_id', 'unknown')
        self.export_time = datetime.now()
        
    def export_report(self, format_type: str = "Markdown", include_summary: bool = True) -> Dict[str, Any]:
        """导出批量分析报告"""
        
        try:
            if format_type == "Markdown":
                return self._export_markdown(include_summary)
            elif format_type == "PDF":
                return self._export_pdf(include_summary)
            elif format_type == "DOCX":
                return self._export_docx(include_summary)
            elif format_type == "ZIP_DOCX":
                return self._export_zip_per_stock('docx')
            elif format_type == "ZIP_PDF":
                return self._export_zip_per_stock('pdf')
            elif format_type == "Excel":
                return self._export_excel(include_summary)
            elif format_type == "JSON":
                return self._export_json(include_summary)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
                
        except Exception as e:
            logger.error(f"❌ [报告导出] 导出失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': None
            }
    
    def _export_markdown(self, include_summary: bool = True) -> Dict[str, Any]:
        """导出Markdown格式报告"""
        
        try:
            # 生成报告内容
            report_content = self._generate_markdown_content(include_summary)
            
            # 保存到文件
            filename = f"batch_analysis_report_{self.batch_id}_{self.export_time.strftime('%Y%m%d_%H%M%S')}.md"
            file_path = Path("reports") / filename
            file_path.parent.mkdir(exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"✅ [Markdown导出] 报告已保存: {file_path}")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'filename': filename,
                'content': report_content,
                'format': 'Markdown'
            }
            
        except Exception as e:
            logger.error(f"❌ [Markdown导出] 导出失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': None
            }
    
    def _export_pdf(self, include_summary: bool = True) -> Dict[str, Any]:
        """导出PDF格式报告"""
        
        try:
            # 生成Markdown内容
            markdown_content = self._generate_markdown_content(include_summary)
            
            # 转换为HTML
            html_content = markdown.markdown(markdown_content, extensions=['tables', 'codehilite'])
            
            # 添加CSS样式
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>批量股票分析报告</title>
                <style>
                    body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; margin: 40px; }}
                    h1, h2, h3 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .metric {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                    .success {{ color: #28a745; }}
                    .warning {{ color: #ffc107; }}
                    .danger {{ color: #dc3545; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # 保存HTML文件
            html_filename = f"batch_analysis_report_{self.batch_id}_{self.export_time.strftime('%Y%m%d_%H%M%S')}.html"
            html_path = Path("reports") / html_filename
            html_path.parent.mkdir(exist_ok=True)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(styled_html)
            
            logger.info(f"✅ [PDF导出] HTML报告已保存: {html_path}")
            
            return {
                'success': True,
                'file_path': str(html_path),
                'filename': html_filename,
                'content': styled_html,
                'format': 'PDF',
                'note': '已生成HTML格式，可使用浏览器打印为PDF'
            }
            
        except Exception as e:
            logger.error(f"❌ [PDF导出] 导出失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': None
            }

    def _export_docx(self, include_summary: bool = True) -> Dict[str, Any]:
        """导出Word(docx)汇总报告（复用单股导出器）"""
        try:
            from .report_exporter import ReportExporter
            exporter = ReportExporter()
            if not exporter.export_available or not exporter.pandoc_available:
                raise Exception("Word导出依赖未就绪（pypandoc/pandoc）")

            # 拼接批量Markdown：逐股调用单股的markdown生成器
            md_parts = ["# 批量股票分析报告 (汇总)\n\n"]
            md_parts.append(f"**批量ID**: {self.batch_id}  ")
            md_parts.append(f"**导出时间**: {self.export_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            results_map = self.batch_results.get('results', {})
            if isinstance(results_map, dict):
                for stock, res in results_map.items():
                    try:
                        md_parts.append(exporter.generate_markdown_report(res))
                        md_parts.append("\n\n---\n\n")
                    except Exception:
                        md_parts.append(f"## {stock}\n\n生成内容失败，仅保留摘要。\n\n")
            else:
                raise Exception("批量结果结构异常：results 不是字典")

            full_md = "\n".join(md_parts)

            # 转 docx
            import pypandoc, tempfile, os
            cleaned = exporter._clean_markdown_for_pandoc(full_md)
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
                out_path = tmp.name
            pypandoc.convert_text(cleaned, 'docx', format='markdown', outputfile=out_path, extra_args=['--from=markdown-yaml_metadata_block'])

            filename = f"batch_analysis_summary_{self.batch_id}_{self.export_time.strftime('%Y%m%d_%H%M%S')}.docx"
            final_path = Path('reports') / filename
            final_path.parent.mkdir(exist_ok=True)
            os.replace(out_path, final_path)

            return {
                'success': True,
                'file_path': str(final_path),
                'filename': filename,
                'format': 'DOCX'
            }
        except Exception as e:
            logger.error(f"❌ [DOCX导出] 导出失败: {e}")
            return {'success': False, 'error': str(e), 'file_path': None}

    def _export_zip_per_stock(self, target: str = 'docx') -> Dict[str, Any]:
        """为每只股票生成单独的docx/pdf并打包zip"""
        try:
            from .report_exporter import ReportExporter
            exporter = ReportExporter()
            if not exporter.export_available or not exporter.pandoc_available:
                raise Exception("导出依赖未就绪（pypandoc/pandoc）")

            import tempfile, zipfile
            tmpdir = Path(tempfile.mkdtemp(prefix='batch_export_'))

            results_map = self.batch_results.get('results', {})
            if not isinstance(results_map, dict) or not results_map:
                raise Exception("没有可导出的结果")

            generated_files = []
            for stock, res in results_map.items():
                md = exporter.generate_markdown_report(res)
                cleaned = exporter._clean_markdown_for_pandoc(md)

                suffix = '.docx' if target == 'docx' else '.pdf'
                out_file = tmpdir / f"{stock}{suffix}"

                import pypandoc
                extra = ['--from=markdown-yaml_metadata_block']
                if target == 'pdf':
                    extra = ['--from=markdown-yaml_metadata_block', '--pdf-engine=wkhtmltopdf']
                pypandoc.convert_text(cleaned, target.replace('docx','docx').replace('pdf','pdf'), format='markdown', outputfile=str(out_file), extra_args=extra)
                if out_file.exists() and out_file.stat().st_size > 0:
                    generated_files.append(out_file)

            if not generated_files:
                raise Exception("未生成任何文件")

            zip_name = f"batch_{self.batch_id}_{self.export_time.strftime('%Y%m%d_%H%M%S')}_{target}.zip"
            zip_path = Path('reports') / zip_name
            zip_path.parent.mkdir(exist_ok=True)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in generated_files:
                    zf.write(f, arcname=f.name)

            return {
                'success': True,
                'file_path': str(zip_path),
                'filename': zip_name,
                'format': f'ZIP_{target.upper()}'
            }
        except Exception as e:
            logger.error(f"❌ [ZIP导出] 导出失败: {e}")
            return {'success': False, 'error': str(e), 'file_path': None}
    
    def _export_excel(self, include_summary: bool = True) -> Dict[str, Any]:
        """导出Excel格式报告"""
        
        try:
            filename = f"batch_analysis_report_{self.batch_id}_{self.export_time.strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path = Path("reports") / filename
            file_path.parent.mkdir(exist_ok=True)
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 汇总报告
                if include_summary:
                    self._write_summary_sheet(writer)
                
                # 详细结果
                self._write_detailed_sheet(writer)
                
                # 投资建议统计
                self._write_recommendations_sheet(writer)
                
                # 风险分析
                self._write_risk_sheet(writer)
            
            logger.info(f"✅ [Excel导出] 报告已保存: {file_path}")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'filename': filename,
                'format': 'Excel'
            }
            
        except Exception as e:
            logger.error(f"❌ [Excel导出] 导出失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': None
            }
    
    def _export_json(self, include_summary: bool = True) -> Dict[str, Any]:
        """导出JSON格式报告"""
        
        try:
            # 准备导出数据
            export_data = {
                'batch_info': {
                    'batch_id': self.batch_id,
                    'export_time': self.export_time.isoformat(),
                    'total_stocks': self.batch_results.get('total_stocks', 0),
                    'successful_analyses': self.batch_results.get('successful_analyses', 0),
                    'failed_analyses': self.batch_results.get('failed_analyses', 0),
                    'analysis_date': self.batch_results.get('analysis_date', ''),
                    'market_type': self.batch_results.get('market_type', ''),
                    'research_depth': self.batch_results.get('research_depth', 0),
                    'analysts': self.batch_results.get('analysts', [])
                },
                'summary_report': self.batch_results.get('summary_report', {}) if include_summary else None,
                'detailed_results': self.batch_results.get('results', {}),
                'error_messages': self.batch_results.get('error_messages', [])
            }
            
            # 保存JSON文件
            filename = f"batch_analysis_report_{self.batch_id}_{self.export_time.strftime('%Y%m%d_%H%M%S')}.json"
            file_path = Path("reports") / filename
            file_path.parent.mkdir(exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ [JSON导出] 报告已保存: {file_path}")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'filename': filename,
                'content': json.dumps(export_data, ensure_ascii=False, indent=2),
                'format': 'JSON'
            }
            
        except Exception as e:
            logger.error(f"❌ [JSON导出] 导出失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': None
            }
    
    def _generate_markdown_content(self, include_summary: bool = True) -> str:
        """生成Markdown格式的报告内容"""
        
        content = []
        
        # 报告标题
        content.append(f"# 批量股票分析报告")
        content.append(f"**生成时间**: {self.export_time.strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**批量分析ID**: {self.batch_id}")
        content.append("")
        
        # 分析概览
        content.append("## 📊 分析概览")
        content.append(f"- **总股票数**: {self.batch_results.get('total_stocks', 0)}")
        content.append(f"- **成功分析**: {self.batch_results.get('successful_analyses', 0)}")
        content.append(f"- **失败分析**: {self.batch_results.get('failed_analyses', 0)}")
        content.append(f"- **成功率**: {self.batch_results.get('successful_analyses', 0) / self.batch_results.get('total_stocks', 1) * 100:.1f}%")
        content.append(f"- **分析日期**: {self.batch_results.get('analysis_date', '')}")
        content.append(f"- **市场类型**: {self.batch_results.get('market_type', '')}")
        content.append(f"- **研究深度**: {self.batch_results.get('research_depth', 0)}级")
        content.append("")
        
        # 汇总报告
        if include_summary:
            summary_report = self.batch_results.get('summary_report', {})
            if summary_report:
                content.append("## 📈 投资建议汇总")
                
                investment_recs = summary_report.get('investment_recommendations', {})
                if investment_recs:
                    content.append(f"- **买入**: {investment_recs.get('buy_count', 0)} 个 ({investment_recs.get('buy_percentage', 0) * 100:.1f}%)")
                    content.append(f"- **卖出**: {investment_recs.get('sell_count', 0)} 个 ({investment_recs.get('sell_percentage', 0) * 100:.1f}%)")
                    content.append(f"- **持有**: {investment_recs.get('hold_count', 0)} 个 ({investment_recs.get('hold_percentage', 0) * 100:.1f}%)")
                    content.append("")
                
                # 推荐度最高的股票
                top_recommendations = summary_report.get('top_recommendations', [])
                if top_recommendations:
                    content.append("### 🏆 推荐度最高的股票")
                    content.append("")
                    content.append("| 股票代码 | 投资建议 | 置信度 | 风险分数 | 目标价格 | 分析要点 |")
                    content.append("|---------|---------|--------|----------|----------|----------|")
                    
                    for rec in top_recommendations:
                        target_price = f"¥{rec.get('target_price', 0):.2f}" if rec.get('target_price') else 'N/A'
                        reasoning = rec.get('reasoning', '')[:50] + '...' if len(rec.get('reasoning', '')) > 50 else rec.get('reasoning', '')
                        content.append(f"| {rec.get('stock_symbol', '')} | {rec.get('action', '')} | {rec.get('confidence', 0) * 100:.1f}% | {rec.get('risk_score', 0) * 100:.1f}% | {target_price} | {reasoning} |")
                    
                    content.append("")
        
        # 详细分析结果
        content.append("## 📋 详细分析结果")
        content.append("")
        
        results = self.batch_results.get('results', {})
        for stock, result in results.items():
            if result.get('success', False):
                content.append(f"### 📈 {stock}")
                
                decision = result.get('decision', {})
                content.append(f"**投资建议**: {decision.get('action', '持有')}")
                content.append(f"**置信度**: {decision.get('confidence', 0) * 100:.1f}%")
                content.append(f"**风险分数**: {decision.get('risk_score', 0) * 100:.1f}%")
                
                target_price = decision.get('target_price')
                if target_price:
                    content.append(f"**目标价格**: ¥{target_price:.2f}")
                
                reasoning = decision.get('reasoning', '')
                if reasoning:
                    content.append(f"**分析推理**: {reasoning}")
                
                content.append("")
            else:
                content.append(f"### ❌ {stock}")
                content.append(f"**状态**: 分析失败")
                content.append(f"**错误信息**: {result.get('error', '未知错误')}")
                content.append("")
        
        # 失败分析列表
        failed_analyses = self.batch_results.get('summary_report', {}).get('failed_analyses', [])
        if failed_analyses:
            content.append("## ❌ 失败分析列表")
            content.append("")
            content.append("| 股票代码 | 错误信息 |")
            content.append("|---------|----------|")
            
            for failed in failed_analyses:
                content.append(f"| {failed.get('stock', '')} | {failed.get('error', '')} |")
            
            content.append("")
        
        # 免责声明
        content.append("## ⚠️ 免责声明")
        content.append("")
        content.append("本分析报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。")
        content.append("请根据个人风险承受能力和投资目标做出投资决策。")
        content.append("")
        
        return "\n".join(content)
    
    def _write_summary_sheet(self, writer):
        """写入汇总报告工作表"""
        
        summary_data = []
        summary_report = self.batch_results.get('summary_report', {})
        
        # 基本统计
        overview = summary_report.get('overview', {})
        summary_data.append(['总股票数', overview.get('total_stocks', 0)])
        summary_data.append(['成功分析', overview.get('successful_analyses', 0)])
        summary_data.append(['失败分析', overview.get('failed_analyses', 0)])
        summary_data.append(['成功率', f"{overview.get('success_rate', 0) * 100:.1f}%"])
        
        # 投资建议统计
        investment_recs = summary_report.get('investment_recommendations', {})
        summary_data.append(['', ''])
        summary_data.append(['投资建议统计', ''])
        summary_data.append(['买入数量', investment_recs.get('buy_count', 0)])
        summary_data.append(['卖出数量', investment_recs.get('sell_count', 0)])
        summary_data.append(['持有数量', investment_recs.get('hold_count', 0)])
        
        # 风险指标
        risk_metrics = summary_report.get('risk_metrics', {})
        summary_data.append(['', ''])
        summary_data.append(['风险指标', ''])
        summary_data.append(['平均置信度', f"{risk_metrics.get('average_confidence', 0) * 100:.1f}%"])
        summary_data.append(['平均风险分数', f"{risk_metrics.get('average_risk_score', 0) * 100:.1f}%"])
        summary_data.append(['高置信度股票', risk_metrics.get('high_confidence_stocks', 0)])
        summary_data.append(['低风险股票', risk_metrics.get('low_risk_stocks', 0)])
        
        df_summary = pd.DataFrame(summary_data, columns=['指标', '数值'])
        df_summary.to_excel(writer, sheet_name='汇总报告', index=False)
    
    def _write_detailed_sheet(self, writer):
        """写入详细结果工作表"""
        
        detailed_data = []
        results = self.batch_results.get('results', {})
        
        for stock, result in results.items():
            if result.get('success', False):
                decision = result.get('decision', {})
                detailed_data.append({
                    '股票代码': stock,
                    '投资建议': decision.get('action', '持有'),
                    '置信度': f"{decision.get('confidence', 0) * 100:.1f}%",
                    '风险分数': f"{decision.get('risk_score', 0) * 100:.1f}%",
                    '目标价格': decision.get('target_price', 'N/A'),
                    '分析状态': '成功'
                })
            else:
                detailed_data.append({
                    '股票代码': stock,
                    '投资建议': 'N/A',
                    '置信度': 'N/A',
                    '风险分数': 'N/A',
                    '目标价格': 'N/A',
                    '分析状态': '失败'
                })
        
        if detailed_data:
            df_detailed = pd.DataFrame(detailed_data)
            df_detailed.to_excel(writer, sheet_name='详细结果', index=False)
    
    def _write_recommendations_sheet(self, writer):
        """写入投资建议工作表"""
        
        recommendations_data = []
        summary_report = self.batch_results.get('summary_report', {})
        top_recommendations = summary_report.get('top_recommendations', [])
        
        for rec in top_recommendations:
            recommendations_data.append({
                '股票代码': rec.get('stock_symbol', ''),
                '投资建议': rec.get('action', ''),
                '置信度': f"{rec.get('confidence', 0) * 100:.1f}%",
                '风险分数': f"{rec.get('risk_score', 0) * 100:.1f}%",
                '目标价格': rec.get('target_price', 'N/A'),
                '分析要点': rec.get('reasoning', '')
            })
        
        if recommendations_data:
            df_recommendations = pd.DataFrame(recommendations_data)
            df_recommendations.to_excel(writer, sheet_name='投资建议', index=False)
    
    def _write_risk_sheet(self, writer):
        """写入风险分析工作表"""
        
        risk_data = []
        results = self.batch_results.get('results', {})
        
        for stock, result in results.items():
            if result.get('success', False):
                decision = result.get('decision', {})
                risk_data.append({
                    '股票代码': stock,
                    '置信度': decision.get('confidence', 0) * 100,
                    '风险分数': decision.get('risk_score', 0) * 100,
                    '投资建议': decision.get('action', '持有'),
                    '风险等级': '高风险' if decision.get('risk_score', 0) > 0.7 else '中等风险' if decision.get('risk_score', 0) > 0.4 else '低风险'
                })
        
        if risk_data:
            df_risk = pd.DataFrame(risk_data)
            df_risk.to_excel(writer, sheet_name='风险分析', index=False)


def export_batch_report(batch_results: Dict[str, Any], format_type: str = "Markdown", include_summary: bool = True) -> Dict[str, Any]:
    """导出批量分析报告（对外接口）"""
    
    exporter = BatchReportExporter(batch_results)
    return exporter.export_report(format_type, include_summary)
