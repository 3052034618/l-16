import argparse
import sys
import os

from . import __version__
from .commands.cmd_init import cmd_init
from .commands.cmd_import import cmd_import
from .commands.cmd_calc import cmd_calc
from .commands.cmd_compare import cmd_compare
from .commands.cmd_report import cmd_report
from .commands.cmd_export import cmd_export
from .commands.cmd_scenario import cmd_scenario


def main():
    parser = argparse.ArgumentParser(
        prog="carbon-calc",
        description="碳减排项目评估工具 - 帮助企业能源管理员快速测算不同改造方案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  carbon-calc init my_project          创建新项目
  carbon-calc import --baseline data.json  导入数据
  carbon-calc calc                     计算所有方案
  carbon-calc compare --sort-by roi    按ROI排序比较
  carbon-calc report                   生成评估报告
  carbon-calc export                   导出管理层汇报表
  carbon-calc scenario                 敏感性分析 (三情景对比)
        """
    )
    
    parser.add_argument("--version", action="version", version=f"carbon-calc {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    _add_init_parser(subparsers)
    _add_import_parser(subparsers)
    _add_calc_parser(subparsers)
    _add_compare_parser(subparsers)
    _add_report_parser(subparsers)
    _add_export_parser(subparsers)
    _add_scenario_parser(subparsers)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    cmd_map = {
        "init": cmd_init,
        "import": cmd_import,
        "calc": cmd_calc,
        "compare": cmd_compare,
        "report": cmd_report,
        "export": cmd_export,
        "scenario": cmd_scenario,
    }
    
    handler = cmd_map.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


def _add_init_parser(subparsers):
    parser = subparsers.add_parser("init", help="创建新项目目录和参数模板")
    parser.add_argument("project_dir", help="项目目录路径")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的项目")


def _add_import_parser(subparsers):
    parser = subparsers.add_parser("import", help="导入基准能耗、设备清单和电价信息")
    parser.add_argument("--project-dir", "-d", default=".", help="项目目录路径 (默认: 当前目录)")
    parser.add_argument("--baseline", help="基准能耗数据文件 (JSON/CSV)")
    parser.add_argument("--equipment", help="设备清单文件 (JSON/CSV)")
    parser.add_argument("--tariff", help="电价信息文件 (JSON/CSV)")
    parser.add_argument("--plans", help="改造方案配置文件 (JSON/CSV)")


def _add_calc_parser(subparsers):
    parser = subparsers.add_parser("calc", help="计算各改造方案的投资、节能量、减排量和回收期")
    parser.add_argument("--project-dir", "-d", default=".", help="项目目录路径 (默认: 当前目录)")
    parser.add_argument("--plan", "-p", help="指定单个方案进行计算")


def _add_compare_parser(subparsers):
    parser = subparsers.add_parser("compare", help="多方案排序比较")
    parser.add_argument("--project-dir", "-d", default=".", help="项目目录路径 (默认: 当前目录)")
    parser.add_argument("--sort-by", default="payback_years", 
                        choices=["payback_years", "annual_carbon_reduction_ton", 
                                 "annual_savings_value", "investment", "roi"],
                        help="排序依据 (默认: payback_years)")
    parser.add_argument("--desc", action="store_true", help="降序排列")


def _add_report_parser(subparsers):
    parser = subparsers.add_parser("report", help="生成管理层摘要报告和风险提示")
    parser.add_argument("--project-dir", "-d", default=".", help="项目目录路径 (默认: 当前目录)")
    parser.add_argument("--format", "-f", default="text", choices=["text", "json"],
                        help="报告格式 (默认: text)")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--budget", "-b", help="投资预算约束 (元)，用于推荐组合方案")


def _add_export_parser(subparsers):
    parser = subparsers.add_parser("export", help="导出管理层汇报表")
    parser.add_argument("--project-dir", "-d", default=".", help="项目目录路径 (默认: 当前目录)")
    parser.add_argument("--format", "-f", default="csv", choices=["csv", "json"],
                        help="导出格式 (默认: csv)")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--budget", "-b", help="投资预算约束 (元)，用于推荐组合方案")


def _add_scenario_parser(subparsers):
    parser = subparsers.add_parser("scenario", help="敏感性分析 - 乐观/基准/保守三情景对比")
    parser.add_argument("--project-dir", "-d", default=".", help="项目目录路径 (默认: 当前目录)")
    parser.add_argument("--plan", "-p", help="指定单个方案进行分析")
    parser.add_argument("--investment-change", type=float, 
                        help="投资波动幅度百分比 (如: 10 表示±10%%)")
    parser.add_argument("--efficiency-change", type=float,
                        help="节能效率波动幅度百分比 (如: 15 表示±15%%)")
    parser.add_argument("--price-change", type=float,
                        help="电价波动幅度百分比 (如: 10 表示±10%%)")
    parser.add_argument("--carbon-change", type=float,
                        help="碳排放因子波动幅度百分比 (如: 10 表示±10%%)")
    parser.add_argument("--save", action="store_true", help="保存分析结果到文件")


if __name__ == "__main__":
    sys.exit(main())
