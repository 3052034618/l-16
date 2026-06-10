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
        if not self.results:
            raise ValueError("计算结果为空，请先运行 calc 命令计算至少一个方案")

    def compare(self, sort_by="payback_years", ascending=True):
        plan_list = list(self.results.values())
        
        if not plan_list:
            return []
        
        def sort_key(plan):
            val = plan.get(sort_by)
            if val is None:
                return float("-inf") if ascending else float("inf")
            if isinstance(val, float) and val == float("inf"):
                return float("inf") if ascending else float("-inf")
            return val
        
        sorted_plans = sorted(plan_list, key=sort_key, reverse=not ascending)
        
        ranked = []
        current_rank = 0
        last_val = None
        for plan in sorted_plans:
            val = plan.get(sort_by)
            if val != last_val:
                current_rank += 1
                last_val = val
            plan_copy = dict(plan)
            plan_copy["rank"] = current_rank
            ranked.append(plan_copy)
        
        return ranked

    def get_summary_stats(self):
        plans = list(self.results.values())
        if not plans:
            return {
                "total_plans": 0,
                "total_investment": 0,
                "total_annual_carbon_reduction_ton": 0,
                "average_payback_years": 0,
                "viable_plans_count": 0,
                "unviable_plans_count": 0,
            }
        
        total_investment = sum(p.get("investment", 0) for p in plans)
        total_carbon = sum(p.get("annual_carbon_reduction_ton", 0) for p in plans)
        
        viable_plans = [p for p in plans if p.get("payback_years") is not None and p.get("payback_years") != float("inf")]
        unviable_count = len(plans) - len(viable_plans)
        
        avg_payback = sum(p.get("payback_years", 0) for p in viable_plans) / len(viable_plans) if viable_plans else 0
        
        return {
            "total_plans": len(plans),
            "total_investment": total_investment,
            "total_annual_carbon_reduction_ton": total_carbon,
            "average_payback_years": avg_payback,
            "viable_plans_count": len(viable_plans),
            "unviable_plans_count": unviable_count,
        }

    def get_recommended_portfolio(self, max_budget=None, max_payback=None):
        ranked = self.compare(sort_by="roi", ascending=False)
        
        portfolio = []
        total_investment = 0
        total_carbon = 0
        total_savings = 0
        
        for plan in ranked:
            investment = plan.get("investment", 0)
            payback = plan.get("payback_years", float("inf"))
            
            if max_payback is not None and payback > max_payback:
                continue
            
            if max_budget is not None and total_investment + investment > max_budget:
                continue
            
            portfolio.append(plan)
            total_investment += investment
            total_carbon += plan.get("annual_carbon_reduction_ton", 0)
            total_savings += plan.get("annual_savings_value", 0)
        
        portfolio_payback = total_investment / total_savings if total_savings > 0 else float("inf")
        
        return {
            "plans": portfolio,
            "plan_ids": [p["plan_id"] for p in portfolio],
            "total_investment": total_investment,
            "total_annual_carbon_reduction_ton": total_carbon,
            "total_annual_savings_value": total_savings,
            "portfolio_payback_years": portfolio_payback,
        }
