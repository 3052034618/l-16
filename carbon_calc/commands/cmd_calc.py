from ..core.calculator import CarbonCalculator
from ..core import ProjectConfig


def cmd_calc(args):
    if not ProjectConfig.project_exists(args.project_dir):
        print(f"✗ 错误: 项目目录不存在或未初始化: {args.project_dir}")
        return 1
    
    try:
        calculator = CarbonCalculator(args.project_dir)
        
        for warning in calculator.warnings:
            print(warning)
        
        if calculator.warnings:
            print("")
        
        if args.plan:
            result = calculator.calculate_single(args.plan)
            print(f"✓ 已计算方案: {result['plan_name']}")
            print("")
            _print_single_result(result)
        else:
            if not calculator.plans:
                print("✗ 错误: 未找到任何方案配置，请先运行 import 或编辑 plans.json")
                return 1
            results = calculator.calculate_all()
            print(f"✓ 已完成 {len(results)} 个方案的计算")
            print("")
            for plan_id, result in results.items():
                print(f"【{result['plan_name']}】")
                _print_single_result(result)
                print("")
        
        print(f"✓ 结果已保存至: {ProjectConfig.get_project_path(args.project_dir) / 'results' / 'calculation_results.json'}")
        
    except ValueError as e:
        print(f"✗ 错误: {e}")
        return 1
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
    payback_str = f"{result['payback_years']:.2f} 年" if result['payback_years'] != float('inf') else "无法回收"
    print(f"  投资回收期: {payback_str}")
    print(f"  投资回报率: {result['roi']:.2f}%")
    print(f"  寿命期总减排: {result['total_carbon_reduction_lifetime']:,.2f} 吨CO₂")
