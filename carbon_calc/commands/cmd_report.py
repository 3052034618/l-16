from ..core.report import ReportGenerator
from ..core import ProjectConfig


def cmd_report(args):
    if not ProjectConfig.project_exists(args.project_dir):
        print(f"✗ 错误: 项目目录不存在或未初始化: {args.project_dir}")
        return 1
    
    try:
        generator = ReportGenerator(args.project_dir)
        
        output_format = args.format if args.format in ["text", "json"] else "text"
        budget = None
        if args.budget:
            try:
                budget = float(args.budget)
            except ValueError:
                print(f"✗ 错误: 预算金额格式不正确: {args.budget}")
                return 1
        
        report = generator.generate_report(output_format=output_format, budget=budget)
        
        if args.output:
            filename = args.output
            if output_format == "json" and not filename.endswith(".json"):
                filename += ".json"
            elif output_format == "text" and not filename.endswith(".txt"):
                filename += ".txt"
            report_path = generator.save_report(report, filename=filename)
            print(f"✓ 报告已保存至: {report_path}")
        else:
            print(report)
        
    except FileNotFoundError as e:
        print(f"✗ 提示: {e}")
        return 1
    except ValueError as e:
        print(f"✗ 提示: {e}")
        return 1
    except Exception as e:
        print(f"✗ 生成报告失败: {e}")
        return 1
    
    return 0
