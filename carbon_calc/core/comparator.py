import json
from pathlib import Path
from ..core import ProjectConfig


class PlanComparator:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        results_path = Path(project_dir) / "results" / "calculation_results.json"
        if not results_path.exists():
            raise FileNotFoundError("未找到计算结果，请先运行 calc 命令")
        self.results = ProjectConfig.load_json(results_path)

    def compare(self, sort_by="payback_years", ascending=True):
        plan_list = list(self.results.values())
        
        valid_plans = [p for p in plan_list if p.get(sort_by) is not None and p.get(sort_by) != float("inf")]
        invalid_plans = [p for p in plan_list if p.get(sort_by) is None or p.get(sort_by) == float("inf")]
        
        valid_plans.sort(key=lambda x: x.get(sort_by, 0), reverse=not ascending)
        
        ranked = []
        for idx, plan in enumerate(valid_plans, 1):
            plan_copy = dict(plan)
            plan_copy["rank"] = idx
            ranked.append(plan_copy)
        
        ranked.extend(invalid_plans)
        
        return ranked

    def get_summary_stats(self):
        plans = list(self.results.values())
        if not plans:
            return {}
        
        total_investment = sum(p.get("investment", 0) for p in plans)
        total_carbon = sum(p.get("annual_carbon_reduction_ton", 0) for p in plans)
        avg_payback = sum(p.get("payback_years", 0) for p in plans if p.get("payback_years") != float("inf")) / len([p for p in plans if p.get("payback_years") != float("inf")]) if plans else 0
        
        return {
            "total_plans": len(plans),
            "total_investment": total_investment,
            "total_annual_carbon_reduction_ton": total_carbon,
            "average_payback_years": avg_payback,
        }
