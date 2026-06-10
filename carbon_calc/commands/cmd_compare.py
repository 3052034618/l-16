from ..core.comparator import PlanComparator
from ..core import ProjectConfig


SORT_OPTIONS = [
    "payback_years",
    "annual_carbon_reduction_ton",
    "annual_savings_value",
    "investment",
    "roi",
]

SORT_LABELS = {
    "payback_years": "投资回收期",
    "annual_carbon_reduction_ton": "年减排量",
    "annual_savings_value": "年节省费用",
    "investment": "投资额",
    "roi": "投资回报率",
}


def cmd_compare(args):
    if not ProjectConfig.project_exists(args.project_dir):
        print(f"✗ 错误: 项目目录不存在或未初始化: {args.project_dir}")
        return 1
    
    try:
        comparator = PlanComparator(args.project_dir)
        
        sort_by = args.sort_by if args.sort_by in SORT_OPTIONS else "payback_years"
        ascending = not args.desc
        
        ranked_plans = comparator.compare(sort_by=sort_by, ascending=ascending)
        stats = comparator.get_summary_stats()
        
        sort_label = SORT_LABELS.get(sort_by, sort_by)
        title = f"方案比较 - 按「{sort_label}」排序"
        
        print(f"╔{'═' * 70}╗")
        print(f"║{title:^70}║")
        print(f"╚{'═' * 70}╝")
        print("")
        
        if not ranked_plans:
            print("  暂无方案数据，请先运行 calc 命令计算方案")
            return 0
        
        print(f"{'排名':<4} {'方案名称':<18} {'类型':<12} {'投资(万)':<10} {'年减排(吨)':<12} {'回收期(年)':<10} {'ROI(%)':<8}")
        print("-" * 70)
        
        for plan in ranked_plans:
            rank = plan.get("rank", "-")
            payback = f"{plan['payback_years']:.2f}" if plan['payback_years'] != float('inf') else "N/A"
            print(
                f"{str(rank):<4} "
                f"{plan['plan_name']:<18} "
                f"{plan['plan_type']:<12} "
                f"{plan['investment']/10000:<10.2f} "
                f"{plan['annual_carbon_reduction_ton']:<12.2f} "
                f"{payback:<10} "
                f"{plan['roi']:<8.2f}"
            )
        
        print("")
        print(f"总计 {stats['total_plans']} 个方案")
        print(f"  可盈利方案: {stats['viable_plans_count']} 个")
        if stats['unviable_plans_count'] > 0:
            print(f"  暂无法回本方案: {stats['unviable_plans_count']} 个")
        print(f"总投资额: ¥{stats['total_investment']:,.2f}")
        print(f"年总减排量: {stats['total_annual_carbon_reduction_ton']:,.2f} 吨CO₂")
        if stats['viable_plans_count'] > 0:
            print(f"平均回收期: {stats['average_payback_years']:.2f} 年")
        else:
            print(f"平均回收期: 无可盈利方案")
        
    except FileNotFoundError as e:
        print(f"✗ 提示: {e}")
        return 1
    except ValueError as e:
        print(f"✗ 提示: {e}")
        return 1
    except Exception as e:
        print(f"✗ 比较失败: {e}")
        return 1
    
    return 0
