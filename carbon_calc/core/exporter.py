import csv
import json
from pathlib import Path
from datetime import datetime
from ..core import ProjectConfig
from .comparator import PlanComparator


class ReportExporter:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.comparator = PlanComparator(project_dir)
        self.results = self.comparator.results
        self.baseline = ProjectConfig.load_json(ProjectConfig.get_file_path(project_dir, "baseline"))
        self.tariff = ProjectConfig.load_json(ProjectConfig.get_file_path(project_dir, "tariff"))

    def export_csv(self, output_file=None):
        ranked_plans = self.comparator.compare(sort_by="payback_years", ascending=True)
        stats = self.comparator.get_summary_stats()
        
        if output_file is None:
            output_file = Path(self.project_dir) / "results" / "management_report.csv"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            
            writer.writerow(["碳减排项目评估 - 管理层汇报表"])
            writer.writerow([f"生成日期: {datetime.now().strftime('%Y-%m-%d')}"])
            writer.writerow([])
            
            writer.writerow(["一、基准能耗情况"])
            writer.writerow(["指标", "数值", "单位", "备注"])
            writer.writerow(["年用电量", self.baseline["annual_electricity_kwh"], "kWh", "基准年"])
            writer.writerow(["年用气量", self.baseline["annual_gas_m3"], "m³", "基准年"])
            writer.writerow(["电价", self.tariff["electricity_price"], "元/kWh", ""])
            writer.writerow(["气价", self.tariff["gas_price"], "元/m³", ""])
            writer.writerow([])
            
            writer.writerow(["二、方案汇总比较"])
            writer.writerow([
                "排名", "方案名称", "方案类型", "投资额(元)", "年节电量(kWh)", 
                "年节气量(m³)", "年减排量(吨CO₂)", "年节省费用(元)", 
                "投资回收期(年)", "投资回报率(%)", "寿命期(年)"
            ])
            
            for plan in ranked_plans:
                rank = plan.get("rank", "-")
                payback = f"{plan['payback_years']:.2f}" if plan['payback_years'] != float('inf') else "无法回收"
                writer.writerow([
                    rank,
                    plan["plan_name"],
                    plan["plan_type"],
                    f"{plan['investment']:.2f}",
                    f"{plan.get('annual_electricity_savings_kwh', 0):.2f}",
                    f"{plan.get('annual_gas_savings_m3', 0):.2f}",
                    f"{plan.get('annual_carbon_reduction_ton', 0):.4f}",
                    f"{plan['annual_savings_value']:.2f}",
                    payback,
                    f"{plan['roi']:.2f}",
                    plan["lifetime_years"],
                ])
            
            writer.writerow([])
            writer.writerow(["三、合计"])
            writer.writerow(["总方案数", stats["total_plans"]])
            writer.writerow(["总投资额(元)", f"{stats['total_investment']:.2f}"])
            writer.writerow(["年总减排量(吨CO₂)", f"{stats['total_annual_carbon_reduction_ton']:.4f}"])
            writer.writerow(["平均回收期(年)", f"{stats['average_payback_years']:.2f}"])
            writer.writerow([])
            
            writer.writerow(["四、推荐方案"])
            best_plan = ranked_plans[0] if ranked_plans else None
            if best_plan:
                writer.writerow(["最佳方案(按回收期)", best_plan["plan_name"]])
                writer.writerow(["推荐理由", f"投资回收期最短({best_plan['payback_years']:.2f}年)，减排效益显著"])
        
        return output_file

    def export_json(self, output_file=None):
        ranked_plans = self.comparator.compare(sort_by="payback_years", ascending=True)
        stats = self.comparator.get_summary_stats()
        
        if output_file is None:
            output_file = Path(self.project_dir) / "results" / "management_report.json"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report_data = {
            "report_title": "碳减排项目评估 - 管理层汇报表",
            "generated_at": datetime.now().isoformat(),
            "baseline": self.baseline,
            "tariff": self.tariff,
            "summary": stats,
            "ranked_plans": ranked_plans,
            "recommendation": {
                "best_plan": ranked_plans[0]["plan_name"] if ranked_plans else None,
                "reason": "按投资回收期排序最佳方案"
            }
        }
        
        ProjectConfig.save_json(output_file, report_data)
        return output_file
