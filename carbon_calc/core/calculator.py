from ..core import ProjectConfig


DEFAULTS = {
    "baseline": {
        "annual_electricity_kwh": 1000000,
        "annual_gas_m3": 0,
        "annual_water_ton": 0,
        "operating_hours": 8760,
        "carbon_factor_electricity": 0.5839,
        "carbon_factor_gas": 2.1622,
        "description": "基准年能耗数据",
    },
    "tariff": {
        "electricity_price": 0.85,
        "gas_price": 3.5,
        "water_price": 5.0,
        "demand_charge": 0,
        "peak_price": 1.2,
        "valley_price": 0.4,
        "flat_price": 0.8,
        "description": "电价及能源价格信息",
    },
}


class CarbonCalculator:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self._warnings = []
        
        self.baseline = self._safe_load("baseline", DEFAULTS["baseline"])
        self.tariff = self._safe_load("tariff", DEFAULTS["tariff"])
        self.equipment = self._safe_load("equipment", {})
        self.plans = self._safe_load("plans", {})

    def _safe_load(self, key, default_dict):
        try:
            data = ProjectConfig.load_json(ProjectConfig.get_file_path(self.project_dir, key))
            filled_data = dict(default_dict)
            filled_data.update(data)
            return filled_data
        except FileNotFoundError:
            self._warnings.append(f"⚠ 未找到 {key}.json，使用默认值")
            return dict(default_dict)
        except Exception as e:
            self._warnings.append(f"⚠ 加载 {key}.json 失败: {e}，使用默认值")
            return dict(default_dict)

    @property
    def warnings(self):
        return list(self._warnings)

    def _results_path(self):
        return ProjectConfig.get_project_path(self.project_dir) / "results" / "calculation_results.json"

    def _load_existing_results(self):
        try:
            return ProjectConfig.load_json(self._results_path())
        except (FileNotFoundError, Exception):
            return {}

    def _save_results(self, results):
        results_dir = ProjectConfig.get_project_path(self.project_dir) / "results"
        results_dir.mkdir(exist_ok=True)
        ProjectConfig.save_json(self._results_path(), results)

    def calculate_all(self):
        results = {}
        for plan_id, plan in self.plans.items():
            results[plan_id] = self.calculate_plan(plan_id, plan)
        
        self._save_results(results)
        return results

    def calculate_single(self, plan_id):
        plan = self.plans.get(plan_id)
        if plan is None:
            raise ValueError(f"未找到方案: {plan_id}")
        
        result = self.calculate_plan(plan_id, plan)
        
        existing = self._load_existing_results()
        existing[plan_id] = result
        self._save_results(existing)
        
        return result

    def calculate_plan(self, plan_id, plan):
        plan_type = plan.get("type")
        calc_method = getattr(self, f"_calc_{plan_type}", None)
        
        if calc_method is None:
            raise ValueError(f"不支持的方案类型: {plan_type}")
        
        result = calc_method(plan)
        result["plan_id"] = plan_id
        result["plan_name"] = plan.get("name", plan_id)
        result["plan_type"] = plan_type
        result["description"] = plan.get("description", "")
        result["investment"] = plan.get("investment", 0)
        result["lifetime_years"] = plan.get("lifetime_years", 10)
        result["maintenance_cost"] = plan.get("maintenance_cost", 0)
        
        result["annual_savings_value"] = self._calc_savings_value(result)
        result["payback_years"] = self._calc_payback(result)
        result["roi"] = self._calc_roi(result)
        result["annual_carbon_reduction_ton"] = result.get("annual_carbon_reduction_ton", 0)
        result["total_carbon_reduction_lifetime"] = result["annual_carbon_reduction_ton"] * result["lifetime_years"]
        
        cashflow, cumulative = self._calc_cashflow(result)
        result["annual_cashflow"] = cashflow
        result["cumulative_carbon_reduction"] = cumulative
        
        return result

    def _calc_lighting(self, plan):
        total_savings_kwh = 0
        improvement = plan.get("efficiency_improvement", 0.5)
        
        for item in self.equipment.get("lighting", []):
            power_w = item.get("power_w", 0)
            count = item.get("count", 0)
            hours_per_day = item.get("hours_per_day", 0)
            days_per_year = item.get("days_per_year", 0)
            power_kw = power_w * count / 1000
            annual_hours = hours_per_day * days_per_year
            annual_kwh = power_kw * annual_hours
            total_savings_kwh += annual_kwh * improvement
        
        carbon_reduction = total_savings_kwh * self.baseline["carbon_factor_electricity"] / 1000
        
        return {
            "annual_electricity_savings_kwh": total_savings_kwh,
            "annual_gas_savings_m3": 0,
            "annual_carbon_reduction_ton": carbon_reduction,
            "unit": "kWh",
        }

    def _calc_air_conditioning(self, plan):
        total_savings_kwh = 0
        improvement = plan.get("efficiency_improvement", 0.2)
        
        for item in self.equipment.get("air_conditioning", []):
            capacity_kw = item.get("capacity_kw", 0)
            cop = item.get("cop", 3.0)
            hours_per_day = item.get("hours_per_day", 0)
            days_per_year = item.get("days_per_year", 0)
            power_input_kw = capacity_kw / cop if cop > 0 else 0
            annual_hours = hours_per_day * days_per_year
            annual_kwh = power_input_kw * annual_hours
            total_savings_kwh += annual_kwh * improvement
        
        carbon_reduction = total_savings_kwh * self.baseline["carbon_factor_electricity"] / 1000
        
        return {
            "annual_electricity_savings_kwh": total_savings_kwh,
            "annual_gas_savings_m3": 0,
            "annual_carbon_reduction_ton": carbon_reduction,
            "unit": "kWh",
        }

    def _calc_photovoltaic(self, plan):
        capacity_kw = plan.get("capacity_kw", 0)
        gen_per_kw = plan.get("annual_generation_kwh_per_kw", 1000)
        self_use_ratio = plan.get("self_use_ratio", 0.7)
        
        total_generation = capacity_kw * gen_per_kw
        self_use_kwh = total_generation * self_use_ratio
        grid_export_kwh = total_generation * (1 - self_use_ratio)
        
        carbon_reduction = total_generation * self.baseline["carbon_factor_electricity"] / 1000
        
        feed_in_tariff = self.tariff.get("valley_price", 0.4) * 0.5
        feed_in_income = grid_export_kwh * feed_in_tariff
        
        return {
            "annual_generation_kwh": total_generation,
            "annual_self_use_kwh": self_use_kwh,
            "annual_grid_export_kwh": grid_export_kwh,
            "annual_electricity_savings_kwh": self_use_kwh,
            "annual_gas_savings_m3": 0,
            "annual_carbon_reduction_ton": carbon_reduction,
            "unit": "kWh",
            "feed_in_tariff_income": feed_in_income,
        }

    def _calc_waste_heat_recovery(self, plan):
        heat_recovery_rate = plan.get("heat_recovery_rate", 0.6)
        displaced_fuel = plan.get("displaced_fuel", "gas")
        
        total_recovered_heat_kwh = 0
        
        for item in self.equipment.get("waste_heat_recovery", []):
            waste_heat_kw = item.get("waste_heat_kw", 0)
            operating_hours = item.get("operating_hours", 0)
            recovery_efficiency = item.get("recovery_efficiency", 0.6)
            total_recovered_heat_kwh += waste_heat_kw * operating_hours * recovery_efficiency * heat_recovery_rate
        
        gas_savings_m3 = 0
        elec_savings_kwh = 0
        carbon_reduction = 0
        
        if displaced_fuel == "gas":
            gas_calorific_value = 8600
            gas_savings_m3 = total_recovered_heat_kwh * 860 / gas_calorific_value if gas_calorific_value > 0 else 0
            carbon_reduction = gas_savings_m3 * self.baseline["carbon_factor_gas"] / 1000
        elif displaced_fuel == "electricity":
            elec_savings_kwh = total_recovered_heat_kwh
            carbon_reduction = elec_savings_kwh * self.baseline["carbon_factor_electricity"] / 1000
        
        return {
            "annual_recovered_heat_kwh": total_recovered_heat_kwh,
            "annual_electricity_savings_kwh": elec_savings_kwh,
            "annual_gas_savings_m3": gas_savings_m3,
            "annual_carbon_reduction_ton": carbon_reduction,
            "unit": "kWh(热)",
        }

    def _calc_savings_value(self, result):
        elec_savings = result.get("annual_electricity_savings_kwh", 0)
        gas_savings = result.get("annual_gas_savings_m3", 0)
        extra_income = result.get("feed_in_tariff_income", 0)
        
        value = (elec_savings * self.tariff["electricity_price"]
                + gas_savings * self.tariff["gas_price"]
                + extra_income)
        
        return value

    def _calc_payback(self, result):
        net_annual_savings = result["annual_savings_value"] - result["maintenance_cost"]
        if net_annual_savings <= 0:
            return float("inf")
        return result["investment"] / net_annual_savings

    def _calc_roi(self, result):
        net_annual_savings = result["annual_savings_value"] - result["maintenance_cost"]
        if result["investment"] <= 0:
            return 0
        return (net_annual_savings / result["investment"]) * 100

    def _calc_cashflow(self, result):
        lifetime = result["lifetime_years"]
        annual_savings = result["annual_savings_value"]
        annual_maintenance = result["maintenance_cost"]
        investment = result["investment"]
        annual_carbon = result["annual_carbon_reduction_ton"]
        
        cashflow = []
        cumulative_carbon = []
        
        cum_carbon = 0
        for year in range(1, lifetime + 1):
            net_cash = annual_savings - annual_maintenance
            cashflow.append({
                "year": year,
                "net_cashflow": net_cash,
                "cumulative_cashflow": -investment + net_cash * year,
            })
            cum_carbon += annual_carbon
            cumulative_carbon.append({
                "year": year,
                "annual_carbon_reduction_ton": annual_carbon,
                "cumulative_carbon_reduction_ton": cum_carbon,
            })
        
        return cashflow, cumulative_carbon
