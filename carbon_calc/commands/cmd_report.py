from ..core.report import ReportGenerator
from ..core import ProjectConfig


def cmd_report(args):
    if not ProjectConfig.project_exists(args.project_dir):
        print(f"✗ 错误: 项目目录不存在或未初始化: {args.project_dir}")
        return 1
    
    try:
        generator = ReportGenerator(args.project_dir)
        
        output_format = args.format if args.format in ["text", "json"] else "text"
        report = generator.generate_report(output_format=output_format)
        
        if args.output:
            if output_format == "json":
                filename = args.output if args.output.endswith(".json") else args.output + ".json"
            else:
                filename = args.output if args.output.endswith(".txt") else args.output + ".txt"
            report_path = generator.save_report(report, filename=filename)
            print(f"✓ 报告已保存至: {report_path}")
        else:
            print(report)
        
    except FileNotFoundError as e:
        print(f"✗ 错误: {e}")
        return 1
    except Exception as e:
        print(f"✗ 生成报告失败: {e}")
        return 1
    
    return 0
