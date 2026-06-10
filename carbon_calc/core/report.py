import json
from pathlib import Path
from datetime import datetime
from ..core import ProjectConfig
from .comparator import PlanComparator


RISK_RULES = {
    "high_investment": {"threshold": 500000, "message": "投资额较高，建议分阶段实施", "level": "warning"},
    "long_payback": {"threshold": 8, "message": "投资回收期较长，财务风险较高", "level": "warning"},
    "low_roi": {"threshold": 10, "message": "投资回报率偏低，需评估政策补贴", "level": "warning"},
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
        self.baseline = ProjectConfig.load_json(ProjectConfig.get_file_path(project_dir, "baseline"))

    def generate_report(self, output_format="text"):
        ranked_plans = self.comparator.compare(sort_by="payback_years", ascending=True)
        stats = self.comparator.get_summary_stats()
        
        if output_format == "text":
            return self._generate_text_report(ranked_plans, stats)
        elif output_format == "json":
            return self._generate_json_report(ranked_plans, stats)
        else:
            raise ValueError(f"不支持的报告格式: {output_format}")

    def _generate_text_report(self, ranked_plans, stats):
        lines = []
        lines.append("=" * 60)
        lines.append("       碳减排项目评估报告")
        lines.append("=" * 60)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("一、基准情况")
        lines.append("-" * 40)
        lines.append(f"年用电量: {self.baseline['annual_electricity_kwh']:,.0f} kWh")
        lines.append(f"年用气量: {self.baseline['annual_gas_m3']:,.0f} m³")
        lines.append(f"电力碳排放因子: {self.baseline['carbon_factor_electricity']} kgCO₂/kWh")
        lines.append(f"燃气碳排放因子: {self.baseline['carbon_factor_gas']} kgCO₂/m³")
        lines.append("")
        
        lines.append("二、方案概览")
        lines.append("-" * 40)
        lines.append(f"方案总数: {stats['total_plans']}")
        lines.append(f"总投资额: ¥{stats['total_investment']:,.2f}")
        lines.append(f"年总减排量: {stats['total_annual_carbon_reduction_ton']:,.2f} 吨CO₂")
        lines.append(f"平均回收期: {stats['average_payback_years']:.2f} 年")
        lines.append("")
        
        lines.append("三、方案排名 (按投资回收期)")
        lines.append("-" * 40)
        for plan in ranked_plans:
            rank = plan.get("rank", "-")
            lines.append(f"  第{rank}名: {plan['plan_name']}")
            lines.append(f"    类型: {plan['plan_type']}")
            lines.append(f"    投资: ¥{plan['investment']:,.2f}")
            lines.append(f"    年节电: {plan.get('annual_electricity_savings_kwh', 0):,.0f} kWh")
            lines.append(f"    年节气: {plan.get('annual_gas_savings_m3', 0):,.0f} m³")
            lines.append(f"    年减排: {plan.get('annual_carbon_reduction_ton', 0):,.2f} 吨CO₂")
            lines.append(f"    年节省费用: ¥{plan['annual_savings_value']:,.2f}")
            lines.append(f"    投资回收期: {plan['payback_years']:.2f} 年" if plan['payback_years'] != float('inf') else "    投资回收期: 无法回收")
            lines.append(f"    ROI: {plan['roi']:.2f}%")
            lines.append("")
        
        lines.append("四、风险与提示")
        lines.append("-" * 40)
        for plan in ranked_plans:
            risks, tech_note = self._assess_risks(plan)
            lines.append(f"  {plan['plan_name']}:")
            if risks:
                for risk in risks:
                    lines.append(f"    ⚠ 风险: {risk}")
            else:
                lines.append(f"    ✓ 财务风险较低")
            if tech_note:
                lines.append(f"    ℹ 技术提示: {tech_note}")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("        报告结束")
        lines.append("=" * 60)
        
        return "\n".join(lines)

    def _generate_json_report(self, ranked_plans, stats):
        risks_dict = {}
        for plan in ranked_plans:
            risks, tech_note = self._assess_risks(plan)
            risks_dict[plan["plan_id"]] = {
                "risks": risks,
                "tech_note": tech_note,
            }
        return {
            "generated_at": datetime.now().isoformat(),
            "baseline": self.baseline,
            "summary": stats,
            "ranked_plans": ranked_plans,
            "risk_assessment": risks_dict,
        }

    def _assess_risks(self, plan):
        risks = []
        
        if plan["investment"] > RISK_RULES["high_investment"]["threshold"]:
            risks.append(RISK_RULES["high_investment"]["message"])
        
        if plan["payback_years"] > RISK_RULES["long_payback"]["threshold"]:
            risks.append(RISK_RULES["long_payback"]["message"])
        
        if plan["roi"] < RISK_RULES["low_roi"]["threshold"]:
            risks.append(RISK_RULES["low_roi"]["message"])
        
        plan_type = plan["plan_type"]
        tech_note = TECH_NOTES.get(plan_type, "")
        
        return risks, tech_note

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
