from ..core.sensitivity import SensitivityAnalyzer, SCENARIO_PRESETS
from ..core import ProjectConfig


def cmd_scenario(args):
    if not ProjectConfig.project_exists(args.project_dir):
        print(f"✗ 错误: 项目目录不存在或未初始化: {args.project_dir}")
        return 1
    
    try:
        analyzer = SensitivityAnalyzer(args.project_dir)
        
        custom_params = None
        if args.investment_change or args.efficiency_change or args.price_change or args.carbon_change:
            custom_params = _build_custom_params(args)
        
        plan_ids = None
        if args.plan:
            plan_ids = [args.plan]
        
        results = analyzer.run_sensitivity(plan_ids=plan_ids, custom_params=custom_params)
        
        _print_results(results)
        
        if args.save:
            file_path = analyzer.save_results(results)
            print(f"✓ 敏感性分析结果已保存至: {file_path}")
        
    except FileNotFoundError as e:
        print(f"✗ 提示: {e}")
        return 1
    except ValueError as e:
        print(f"✗ 错误: {e}")
        return 1
    except Exception as e:
        print(f"✗ 敏感性分析失败: {e}")
        return 1
    
    return 0


def _build_custom_params(args):
    params = {}
    
    inv_change = float(args.investment_change) if args.investment_change else 0
    eff_change = float(args.efficiency_change) if args.efficiency_change else 0
    price_change = float(args.price_change) if args.price_change else 0
    carbon_change = float(args.carbon_change) if args.carbon_change else 0
    
    if inv_change != 0 or eff_change != 0 or price_change != 0 or carbon_change != 0:
        params["optimistic"] = {
            "investment_multiplier": 1 - inv_change / 100 if inv_change > 0 else 1 + abs(inv_change) / 100,
            "efficiency_multiplier": 1 + eff_change / 100,
            "electricity_price_multiplier": 1 + price_change / 100,
            "carbon_factor_multiplier": 1 + carbon_change / 100,
        }
        params["conservative"] = {
            "investment_multiplier": 1 + inv_change / 100 if inv_change > 0 else 1 - abs(inv_change) / 100,
            "efficiency_multiplier": 1 - eff_change / 100,
            "electricity_price_multiplier": 1 - price_change / 100,
            "carbon_factor_multiplier": 1 - carbon_change / 100,
        }
    
    return params if params else None


def _print_results(results):
    scenarios = results["scenarios"]
    summary = results["summary"]
    
    print(f"╔{'═' * 72}╗")
    print(f"║{'敏感性分析 - 三情景对比':^72}║")
    print(f"╚{'═' * 72}╝")
    print("")
    
    for scenario_key in ["optimistic", "baseline", "conservative"]:
        if scenario_key not in scenarios:
            continue
        sc = scenarios[scenario_key]
        print(f"【{sc['label']}】")
        print(f"  {sc['description']}")
        params = sc["params"]
        print(f"  投资系数: {params['investment_multiplier']:.2f}x  |  "
              f"效率系数: {params['efficiency_multiplier']:.2f}x  |  "
              f"电价系数: {params['electricity_price_multiplier']:.2f}x  |  "
              f"碳因子系数: {params['carbon_factor_multiplier']:.2f}x")
        print("")
    
    print(f"{'方案名称':<16} {'指标':<12} {'乐观':>10} {'基准':>10} {'保守':>10} {'波动范围':>12}")
    print("-" * 72)
    
    for plan_id, data in summary.items():
        plan_name = data["plan_name"]
        
        payback_opt = data["optimistic_payback_years"]
        payback_base = data["baseline_payback_years"]
        payback_cons = data["conservative_payback_years"]
        
        opt_str = f"{payback_opt:.2f}年" if payback_opt != float('inf') and payback_opt is not None else "N/A"
        base_str = f"{payback_base:.2f}年" if payback_base != float('inf') and payback_base is not None else "N/A"
        cons_str = f"{payback_cons:.2f}年" if payback_cons != float('inf') and payback_cons is not None else "N/A"
        
        range_str = _calc_range_str(payback_opt, payback_cons, "年")
        
        print(f"{plan_name:<16} {'投资回收期':<12} {opt_str:>10} {base_str:>10} {cons_str:>10} {range_str:>12}")
        
        carbon_opt = data["optimistic_carbon_ton"]
        carbon_base = data["baseline_carbon_ton"]
        carbon_cons = data["conservative_carbon_ton"]
        
        c_range = _calc_range_str(carbon_opt, carbon_cons, "吨")
        
        print(f"{'':<16} {'年减排量':<12} {carbon_opt:>9.2f}吨 {carbon_base:>9.2f}吨 {carbon_cons:>9.2f}吨 {c_range:>12}")
        
        roi_opt = data["optimistic_roi"]
        roi_base = data["baseline_roi"]
        roi_cons = data["conservative_roi"]
        
        r_range = _calc_range_str(roi_opt, roi_cons, "%")
        
        print(f"{'':<16} {'投资回报率':<12} {roi_opt:>9.2f}% {roi_base:>9.2f}% {roi_cons:>9.2f}% {r_range:>12}")
        
        print("")
    
    print("说明:")
    print("  乐观情景: 投资降低、效率提升、电价上涨、碳因子上升 (最有利)")
    print("  保守情景: 投资上升、效率下降、电价下跌、碳因子下降 (最不利)")
    print("  基准情景: 按当前参数测算")


def _calc_range_str(best, worst, unit):
    if best is None or worst is None:
        return "N/A"
    if best == float('inf') or worst == float('inf'):
        return "N/A"
    if unit == "年":
        if best < worst:
            return f"{best:.1f}-{worst:.1f}{unit}"
        else:
            return f"{worst:.1f}-{best:.1f}{unit}"
    else:
        low = min(best, worst)
        high = max(best, worst)
        return f"{low:.1f}-{high:.1f}{unit}"
