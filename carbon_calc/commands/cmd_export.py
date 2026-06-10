from ..core.exporter import ReportExporter
from ..core import ProjectConfig


def cmd_export(args):
    if not ProjectConfig.project_exists(args.project_dir):
        print(f"✗ 错误: 项目目录不存在或未初始化: {args.project_dir}")
        return 1
    
    try:
        exporter = ReportExporter(args.project_dir)
        
        export_format = args.format if args.format in ["csv", "json"] else "csv"
        
        if args.output:
            output_file = args.output
        else:
            output_file = None
        
        if export_format == "csv":
            result_path = exporter.export_csv(output_file)
        else:
            result_path = exporter.export_json(output_file)
        
        print(f"✓ 管理层汇报表已导出: {result_path}")
        
    except FileNotFoundError as e:
        print(f"✗ 错误: {e}")
        return 1
    except Exception as e:
        print(f"✗ 导出失败: {e}")
        return 1
    
    return 0
