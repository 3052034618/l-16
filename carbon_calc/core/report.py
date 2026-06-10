import json
from pathlib import Path
from datetime import datetime
from ..core import ProjectConfig
from .comparator import PlanComparator


RISK_RULES = {
    "high_investment": {"threshold": 500000, "message": "投资额较高，建议分阶段实施", "level": "high"},
    "long_payback": {"threshold": 8, "message": "投资回收期较长，财务风险较高", "level": "medium"},
    "low_roi": {"threshold": 10, "message": "投资回报率偏低，需评估政策补贴", "level": "medium"},
    "very_low_roi": {"threshold": 5, "message": "投资回报率很低，项目经济性存疑", "level": "high"},
}

TECH_NOTES = {
    "lighting": "LED照明技术成熟，实施风险低",
    "air_conditioning": "空调变频改造技术成熟，实施难度中等",
    "photovoltaic": "光伏项目依赖政策和光照条件，需评估并网风险",
    "waste_heat_recovery": "余热回收效果依赖设备运行工况，需现场勘测",
}


class ReportGenerator:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.comparator = PlanComparator(project_dir)
        self.results = self.comparator.results
        
        try:
            self.baseline = ProjectConfig.load_json(ProjectConfig.get_file_path(project_dir, "baseline"))
        except (FileNotFoundError, Exception):
            self.baseline = {
                "annual_electricity_kwh": 0,
                "annual_gas_m3": 0,
                "carbon_factor_electricity": 0.5839,
                "carbon_factor_gas": 2.1622,
            }

    def generate_report(self, output_format="text", budget=None):
        ranked_plans = self.comparator.compare(sort_by="payback_years", ascending=True)
        stats = self.comparator.get_summary_stats()
        portfolio = self.comparator.get_recommended_portfolio(max_budget=budget)
        
        if output_format == "text":
            return self._generate_text_report(ranked_plans, stats, portfolio, budget)
        elif output_format == "json":
            return self._generate_json_report(ranked_plans, stats, portfolio, budget)
        else:
            raise ValueError(f"不支持的报告格式: {output_format}")

    def _generate_text_report(self, ranked_plans, stats, portfolio, budget):
        lines = []
        lines.append("=" * 70)
        lines.append("                  碳减排项目评估报告 (管理层摘要)")
        lines.append("=" * 70)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("一、执行摘要")
        lines.append("-" * 55)
        lines.append(f"  评估方案总数: {stats['total_plans']} 个")
        lines.append(f"  可实施方案数: {stats['viable_plans_count']} 个")
        lines.append(f"  总投资预算需求: ¥{stats['total_investment']:,.2f}")
        lines.append(f"  预计年减排总量: {stats['total_annual_carbon_reduction_ton']:,.2f} 吨CO₂")
        
        best_plan = ranked_plans[0] if ranked_plans else None
        if best_plan:
            payback_str = f"{best_plan['payback_years']:.2f} 年" if best_plan['payback_years'] != float('inf') else "无法回收"
            lines.append(f"  最佳方案: {best_plan['plan_name']} (回收期 {payback_str})")
        lines.append("")
        
        lines.append("二、推荐组合方案")
        lines.append("-" * 55)
        if budget:
            lines.append(f"  预算约束: ¥{budget:,.2f}")
        else:
            lines.append(f"  预算约束: 无 (推荐所有可盈利方案)")
        
        if portfolio["plans"]:
            portfolio_payback = portfolio["portfolio_payback_years"]
            payback_str = f"{portfolio_payback:.2f} 年" if portfolio_payback != float('inf') else "无法回收"
            lines.append(f"  组合方案数: {len(portfolio['plans'])} 个")
            lines.append(f"  组合总投资: ¥{portfolio['total_investment']:,.2f}")
            lines.append(f"  组合年节省: ¥{portfolio['total_annual_savings_value']:,.2f}")
            lines.append(f"  组合年减排: {portfolio['total_annual_carbon_reduction_ton']:,.2f} 吨CO₂")
            lines.append(f"  组合回收期: {payback_str}")
            lines.append("")
            lines.append("  包含方案:")
            for i, plan in enumerate(portfolio["plans"], 1):
                lines.append(f"    {i}. {plan['plan_name']} (投资: ¥{plan['investment']:,.0f}, 减排: {plan['annual_carbon_reduction_ton']:.1f}吨)")
        else:
            lines.append("  ⚠ 无符合条件的推荐方案")
        lines.append("")
        
        lines.append("三、方案排名 (按投资回收期)")
        lines.append("-" * 55)
        for plan in ranked_plans:
            rank = plan.get("rank", "-")
            payback_str = f"{plan['payback_years']:.2f} 年" if plan['payback_years'] != float('inf') else "无法回收"
            lines.append(f"  第{rank}名: {plan['plan_name']}")
            lines.append(f"    类型: {plan['plan_type']} | 投资: ¥{plan['investment']:,.2f}")
            lines.append(f"    年节电: {plan.get('annual_electricity_savings_kwh', 0):,.0f} kWh | 年节气: {plan.get('annual_gas_savings_m3', 0):,.0f} m³")
            lines.append(f"    年减排: {plan.get('annual_carbon_reduction_ton', 0):,.2f} 吨CO₂ | 年节省: ¥{plan['annual_savings_value']:,.2f}")
            lines.append(f"    回收期: {payback_str} | ROI: {plan['roi']:.2f}% | 寿命: {plan['lifetime_years']} 年")
            lines.append("")
        
        lines.append("四、累计减排曲线 (前5年)")
        lines.append("-" * 55)
        lines.append(f"  {'年份':<6} {'年减排(吨)':<14} {'累计减排(吨)':<14} {'累计节省(万元)':<14}")
        lines.append("  " + "-" * 50)
        
        total_annual_carbon = stats["total_annual_carbon_reduction_ton"]
        total_annual_savings = sum(p.get("annual_savings_value", 0) for p in self.results.values())
        
        cum_carbon = 0
        cum_savings = 0
        for year in range(1, 6):
            cum_carbon += total_annual_carbon
            cum_savings += total_annual_savings
            lines.append(f"  第{year}年   {total_annual_carbon:>10.2f}    {cum_carbon:>10.2f}    {cum_savings/10000:>10.2f}")
        lines.append("")
        
        lines.append("五、风险与提示")
        lines.append("-" * 55)
        
        all_risks = self._assess_all_risks(ranked_plans)
        if all_risks["key_risks"]:
            lines.append("  ⚠ 关键风险:")
            for risk in all_risks["key_risks"]:
                lines.append(f"    • {risk}")
            lines.append("")
        
        if all_risks["medium_risks"]:
            lines.append("  ◆ 中等风险:")
            for risk in all_risks["medium_risks"]:
                lines.append(f"    • {risk}")
            lines.append("")
        
        lines.append("  ℹ 技术提示:")
        tech_notes_set = set()
        for plan in ranked_plans:
            note = TECH_NOTES.get(plan["plan_type"])
            if note and note not in tech_notes_set:
                tech_notes_set.add(note)
                lines.append(f"    • {plan['plan_type']}: {note}")
        lines.append("")
        
        lines.append("六、建议下一步行动")
        lines.append("-" * 55)
        if portfolio["plans"]:
            lines.append("  1. 优先推进推荐组合方案，确保资金到位")
            lines.append("  2. 针对高风险方案开展进一步技术经济性论证")
            lines.append("  3. 申请相关碳减排政策补贴，提升项目回报率")
            lines.append("  4. 建立能耗监测系统，验证实际减排效果")
        else:
            lines.append("  1. 当前方案经济性不足，建议优化方案设计")
            lines.append("  2. 调研政策补贴可能性，改善项目收益")
            lines.append("  3. 考虑分阶段实施，降低一次性投资压力")
        lines.append("")
        
        lines.append("=" * 70)
        lines.append("                      报告结束")
        lines.append("=" * 70)
        
        return "\n".join(lines)

    def _generate_json_report(self, ranked_plans, stats, portfolio, budget):
        all_risks = self._assess_all_risks(ranked_plans)
        
        total_annual_carbon = stats["total_annual_carbon_reduction_ton"]
        total_annual_savings = sum(p.get("annual_savings_value", 0) for p in self.results.values())
        
        carbon_curve = []
        cashflow_curve = []
        cum_carbon = 0
        cum_savings = 0
        max_years = 25
        for year in range(1, max_years + 1):
            cum_carbon += total_annual_carbon
            cum_savings += total_annual_savings
            carbon_curve.append({
                "year": year,
                "annual_carbon_reduction_ton": total_annual_carbon,
                "cumulative_carbon_reduction_ton": cum_carbon,
            })
            cashflow_curve.append({
                "year": year,
                "annual_savings": total_annual_savings,
                "cumulative_savings": cum_savings,
                "net_cumulative_cashflow": cum_savings - stats["total_investment"],
            })
        
        risk_assessment = {}
        for plan in ranked_plans:
            risks, tech_note = self._assess_plan_risks(plan)
            risk_assessment[plan["plan_id"]] = {
                "risks": risks,
                "tech_note": tech_note,
            }
        
        return {
            "generated_at": datetime.now().isoformat(),
            "report_type": "management_summary",
            "baseline": self.baseline,
            "executive_summary": {
                "total_plans": stats["total_plans"],
                "viable_plans": stats["viable_plans_count"],
                "total_investment": stats["total_investment"],
                "total_annual_carbon_reduction_ton": stats["total_annual_carbon_reduction_ton"],
                "best_plan": ranked_plans[0]["plan_name"] if ranked_plans else None,
            },
            "recommended_portfolio": {
                "budget_constraint": budget,
                "plan_count": len(portfolio["plans"]),
                "plan_ids": portfolio["plan_ids"],
                "total_investment": portfolio["total_investment"],
                "total_annual_savings_value": portfolio["total_annual_savings_value"],
                "total_annual_carbon_reduction_ton": portfolio["total_annual_carbon_reduction_ton"],
                "portfolio_payback_years": portfolio["portfolio_payback_years"],
            },
            "ranked_plans": ranked_plans,
            "cumulative_carbon_curve": carbon_curve,
            "cumulative_cashflow_curve": cashflow_curve,
            "risk_assessment": risk_assessment,
            "key_risks": all_risks["key_risks"],
            "medium_risks": all_risks["medium_risks"],
            "recommendations": all_risks["recommendations"],
        }

    def _assess_plan_risks(self, plan):
        risks = []
        
        if plan["investment"] > RISK_RULES["high_investment"]["threshold"]:
            risks.append(RISK_RULES["high_investment"]["message"])
        
        if plan["payback_years"] > RISK_RULES["long_payback"]["threshold"]:
            risks.append(RISK_RULES["long_payback"]["message"])
        
        if plan["roi"] < RISK_RULES["very_low_roi"]["threshold"]:
            risks.append(RISK_RULES["very_low_roi"]["message"])
        elif plan["roi"] < RISK_RULES["low_roi"]["threshold"]:
            risks.append(RISK_RULES["low_roi"]["message"])
        
        plan_type = plan["plan_type"]
        tech_note = TECH_NOTES.get(plan_type, "")
        
        return risks, tech_note

    def _assess_all_risks(self, ranked_plans):
        key_risks = []
        medium_risks = []
        recommendations = []
        
        stats = self.comparator.get_summary_stats()
        
        if stats["unviable_plans_count"] > 0:
            medium_risks.append(f"有 {stats['unviable_plans_count']} 个方案暂无法回本，需优化或谨慎实施")
        
        high_investment_plans = [p for p in ranked_plans if p["investment"] > RISK_RULES["high_investment"]["threshold"]]
        if high_investment_plans:
            key_risks.append(f"大额投资方案共 {len(high_investment_plans)} 个，总投资 ¥{sum(p['investment'] for p in high_investment_plans):,.0f}，资金压力较大")
        
        long_payback_plans = [p for p in ranked_plans if p["payback_years"] > RISK_RULES["long_payback"]["threshold"] and p["payback_years"] != float("inf")]
        if long_payback_plans:
            medium_risks.append(f"{len(long_payback_plans)} 个方案回收期超过 8 年，财务风险偏高")
        
        total_investment = stats["total_investment"]
        if total_investment > 1000000:
            key_risks.append(f"总投资规模 (¥{total_investment/10000:,.0f}万) 较大，建议分阶段实施")
        
        recommendations = [
            "优先推进回收期短、ROI高的方案",
            "申请碳减排政策补贴和绿色金融支持",
            "建立能耗监测系统验证实际效果",
        ]
        
        return {
            "key_risks": key_risks,
            "medium_risks": medium_risks,
            "recommendations": recommendations,
        }

    def save_report(self, content, filename="report.txt"):
        report_dir = Path(self.project_dir) / "results"
        report_dir.mkdir(exist_ok=True)
        report_path = report_dir / filename
        
        if isinstance(content, dict):
            ProjectConfig.save_json(report_path, content)
        else:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        return report_path
