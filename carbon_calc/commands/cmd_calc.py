from ..core.calculator import CarbonCalculator
from ..core import ProjectConfig


def cmd_calc(args):
    if not ProjectConfig.project_exists(args.project_dir):
        print(f"✗ 错误: 项目目录不存在或未初始化: {args.project_dir}")
        return 1
    
    try:
        calculator = CarbonCalculator(args.project_dir)
        
        if args.plan:
            plan = calculator.plans.get(args.plan)
            if not plan:
                print(f"✗ 错误: 未找到方案: {args.plan}")
                return 1
            result = calculator.calculate_plan(args.plan, plan)
            _print_single_result(result)
        else:
            results = calculator.calculate_all()
            print(f"✓ 已完成 {len(results)} 个方案的计算")
            print("")
            for plan_id, result in results.items():
                print(f"【{result['plan_name']}】")
                _print_single_result(result)
                print("")
        
        print(f"✓ 结果已保存至: {ProjectConfig.get_project_path(args.project_dir) / 'results' / 'calculation_results.json'}")
        
    except Exception as e:
        print(f"✗ 计算失败: {e}")
        return 1
    
    return 0


def _print_single_result(result):
    print(f"  方案类型: {result['plan_type']}")
    print(f"  投资额: ¥{result['investment']:,.2f}")
    print(f"  年节电量: {result.get('annual_electricity_savings_kwh', 0):,.0f} kWh")
    print(f"  年节气量: {result.get('annual_gas_savings_m3', 0):,.0f} m³")
    print(f"  年减排量: {result['annual_carbon_reduction_ton']:,.2f} 吨CO₂")
    print(f"  年节省费用: ¥{result['annual_savings_value']:,.2f}")
    print(f"  投资回收期: {result['payback_years']:.2f} 年" if result['payback_years'] != float('inf') else "  投资回收期: 无法回收")
    print(f"  投资回报率: {result['roi']:.2f}%")
    print(f"  寿命期总减排: {result['total_carbon_reduction_lifetime']:,.2f} 吨CO₂")
