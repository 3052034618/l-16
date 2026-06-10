import copy
from ..core import ProjectConfig
from ..core.calculator import CarbonCalculator


SCENARIO_PRESETS = {
    "optimistic": {
        "label": "乐观情景",
        "description": "各项参数向好的方向波动",
        "investment_multiplier": 0.9,
        "efficiency_multiplier": 1.15,
        "electricity_price_multiplier": 1.1,
        "carbon_factor_multiplier": 1.1,
    },
    "baseline": {
        "label": "基准情景",
        "description": "按当前参数测算",
        "investment_multiplier": 1.0,
        "efficiency_multiplier": 1.0,
        "electricity_price_multiplier": 1.0,
        "carbon_factor_multiplier": 1.0,
    },
    "conservative": {
        "label": "保守情景",
        "description": "各项参数向不利方向波动",
        "investment_multiplier": 1.15,
        "efficiency_multiplier": 0.85,
        "electricity_price_multiplier": 0.9,
        "carbon_factor_multiplier": 0.9,
    },
}


class SensitivityAnalyzer:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.base_calculator = CarbonCalculator(project_dir)

    def run_sensitivity(self, plan_ids=None, custom_params=None):
        if plan_ids is None:
            plan_ids = list(self.base_calculator.plans.keys())
        
        results = {}
        
        for scenario_key, preset in SCENARIO_PRESETS.items():
            scenario_params = dict(preset)
            if custom_params and scenario_key in custom_params:
                scenario_params.update(custom_params[scenario_key])
            
            scenario_results = {}
            for plan_id in plan_ids:
                if plan_id not in self.base_calculator.plans:
                    continue
                
                adjusted_plan = self._adjust_plan(
                    self.base_calculator.plans[plan_id],
                    scenario_params
                )
                adjusted_calc = self._create_adjusted_calculator(scenario_params)
                result = adjusted_calc.calculate_plan(plan_id, adjusted_plan)
                scenario_results[plan_id] = result
            
            results[scenario_key] = {
                "label": scenario_params.get("label", preset["label"]),
                "description": scenario_params.get("description", preset["description"]),
                "params": {
                    "investment_multiplier": scenario_params.get("investment_multiplier", 1.0),
                    "efficiency_multiplier": scenario_params.get("efficiency_multiplier", 1.0),
                    "electricity_price_multiplier": scenario_params.get("electricity_price_multiplier", 1.0),
                    "carbon_factor_multiplier": scenario_params.get("carbon_factor_multiplier", 1.0),
                },
                "plans": scenario_results,
            }
        
        summary = self._summarize(results)
        
        return {"scenarios": results, "summary": summary}

    def _adjust_plan(self, plan, params):
        adjusted = copy.deepcopy(plan)
        
        inv_mult = params.get("investment_multiplier", 1.0)
        if "investment" in adjusted:
            adjusted["investment"] = adjusted["investment"] * inv_mult
        
        eff_mult = params.get("efficiency_multiplier", 1.0)
        if "efficiency_improvement" in adjusted:
            adjusted["efficiency_improvement"] = adjusted["efficiency_improvement"] * eff_mult
        if "heat_recovery_rate" in adjusted:
            adjusted["heat_recovery_rate"] = adjusted["heat_recovery_rate"] * eff_mult
        if "annual_generation_kwh_per_kw" in adjusted:
            adjusted["annual_generation_kwh_per_kw"] = adjusted["annual_generation_kwh_per_kw"] * eff_mult
        
        return adjusted

    def _create_adjusted_calculator(self, params):
        calc = CarbonCalculator(self.project_dir)
        
        elec_mult = params.get("electricity_price_multiplier", 1.0)
        calc.tariff["electricity_price"] = calc.tariff["electricity_price"] * elec_mult
        calc.tariff["peak_price"] = calc.tariff.get("peak_price", 0) * elec_mult
        calc.tariff["valley_price"] = calc.tariff.get("valley_price", 0) * elec_mult
        calc.tariff["flat_price"] = calc.tariff.get("flat_price", 0) * elec_mult
        
        carbon_mult = params.get("carbon_factor_multiplier", 1.0)
        calc.baseline["carbon_factor_electricity"] = calc.baseline["carbon_factor_electricity"] * carbon_mult
        calc.baseline["carbon_factor_gas"] = calc.baseline["carbon_factor_gas"] * carbon_mult
        
        return calc

    def _summarize(self, results):
        summary = {}
        
        baseline = results.get("baseline", {}).get("plans", {})
        optimistic = results.get("optimistic", {}).get("plans", {})
        conservative = results.get("conservative", {}).get("plans", {})
        
        all_plan_ids = set(list(baseline.keys()) + list(optimistic.keys()) + list(conservative.keys()))
        
        for plan_id in all_plan_ids:
            base = baseline.get(plan_id)
            opt = optimistic.get(plan_id)
            cons = conservative.get(plan_id)
            
            if base is None:
                continue
            
            payback_opt = opt.get("payback_years") if opt else None
            payback_cons = cons.get("payback_years") if cons else None
            
            carbon_opt = opt.get("annual_carbon_reduction_ton") if opt else 0
            carbon_cons = cons.get("annual_carbon_reduction_ton") if cons else 0
            
            roi_opt = opt.get("roi") if opt else 0
            roi_cons = cons.get("roi") if cons else 0
            
            summary[plan_id] = {
                "plan_name": base.get("plan_name", plan_id),
                "baseline_payback_years": base.get("payback_years"),
                "optimistic_payback_years": payback_opt,
                "conservative_payback_years": payback_cons,
                "payback_range": {
                    "best": payback_opt,
                    "worst": payback_cons,
                },
                "baseline_carbon_ton": base.get("annual_carbon_reduction_ton", 0),
                "optimistic_carbon_ton": carbon_opt,
                "conservative_carbon_ton": carbon_cons,
                "carbon_range": {
                    "best": carbon_opt,
                    "worst": carbon_cons,
                },
                "baseline_roi": base.get("roi", 0),
                "optimistic_roi": roi_opt,
                "conservative_roi": roi_cons,
                "roi_range": {
                    "best": roi_opt,
                    "worst": roi_cons,
                },
            }
        
        return summary

    def save_results(self, sensitivity_data, filename="sensitivity_results.json"):
        results_path = ProjectConfig.get_project_path(self.project_dir) / "results"
        results_path.mkdir(exist_ok=True)
        file_path = results_path / filename
        ProjectConfig.save_json(file_path, sensitivity_data)
        return file_path
