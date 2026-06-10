import csv
import json
from pathlib import Path
from datetime import datetime
from ..core import ProjectConfig
from .comparator import PlanComparator
from .report import ReportGenerator


class ReportExporter:
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
        
        try:
            self.tariff = ProjectConfig.load_json(ProjectConfig.get_file_path(project_dir, "tariff"))
        except (FileNotFoundError, Exception):
            self.tariff = {
                "electricity_price": 0.85,
                "gas_price": 3.5,
            }

    def export_csv(self, output_file=None, budget=None):
        ranked_plans = self.comparator.compare(sort_by="payback_years", ascending=True)
        stats = self.comparator.get_summary_stats()
        portfolio = self.comparator.get_recommended_portfolio(max_budget=budget)
        report_gen = ReportGenerator(self.project_dir)
        all_risks = report_gen._assess_all_risks(ranked_plans)
        
        if output_file is None:
            output_file = Path(self.project_dir) / "results" / "management_report.csv"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        total_annual_carbon = stats["total_annual_carbon_reduction_ton"]
        total_annual_savings = sum(p.get("annual_savings_value", 0) for p in self.results.values())
        total_investment = stats["total_investment"]
        
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            
            writer.writerow(["碳减排项目评估 - 管理层汇报表"])
            writer.writerow([f"生成日期: {datetime.now().strftime('%Y-%m-%d')}"])
            writer.writerow([])
            
            writer.writerow(["一、执行摘要"])
            writer.writerow(["指标", "数值", "单位", "备注"])
            writer.writerow(["评估方案总数", stats["total_plans"], "个", ""])
            writer.writerow(["可盈利方案数", stats["viable_plans_count"], "个", ""])
            writer.writerow(["总投资需求", f"{total_investment:.2f}", "元", ""])
            writer.writerow(["年总减排量", f"{stats['total_annual_carbon_reduction_ton']:.4f}", "吨CO₂", ""])
            writer.writerow(["年总节省费用", f"{total_annual_savings:.2f}", "元", ""])
            if stats["viable_plans_count"] > 0:
                writer.writerow(["平均回收期", f"{stats['average_payback_years']:.2f}", "年", "可盈利方案平均"])
            writer.writerow([])
            
            writer.writerow(["二、基准能耗与能源价格"])
            writer.writerow(["指标", "数值", "单位", "备注"])
            writer.writerow(["年用电量", self.baseline.get("annual_electricity_kwh", 0), "kWh", "基准年"])
            writer.writerow(["年用气量", self.baseline.get("annual_gas_m3", 0), "m³", "基准年"])
            writer.writerow(["电价", self.tariff.get("electricity_price", 0), "元/kWh", ""])
            writer.writerow(["气价", self.tariff.get("gas_price", 0), "元/m³", ""])
            writer.writerow(["电力碳排放因子", self.baseline.get("carbon_factor_electricity", 0), "kgCO₂/kWh", ""])
            writer.writerow(["燃气碳排放因子", self.baseline.get("carbon_factor_gas", 0), "kgCO₂/m³", ""])
            writer.writerow([])
            
            writer.writerow(["三、推荐组合方案"])
            if budget:
                writer.writerow(["预算约束", f"{budget:.2f}", "元", ""])
            writer.writerow(["组合方案数", len(portfolio["plans"]), "个", ""])
            writer.writerow(["组合总投资", f"{portfolio['total_investment']:.2f}", "元", ""])
            writer.writerow(["组合年节省", f"{portfolio['total_annual_savings_value']:.2f}", "元", ""])
            writer.writerow(["组合年减排", f"{portfolio['total_annual_carbon_reduction_ton']:.4f}", "吨CO₂", ""])
            portfolio_payback = portfolio["portfolio_payback_years"]
            payback_str = f"{portfolio_payback:.2f}" if portfolio_payback != float('inf') else "无法回收"
            writer.writerow(["组合回收期", payback_str, "年", ""])
            if portfolio["plans"]:
                writer.writerow(["包含方案", "; ".join(p["plan_name"] for p in portfolio["plans"]), "", "按ROI优先级组合"])
            writer.writerow([])
            
            writer.writerow(["四、方案汇总比较 (按投资回收期排序)"])
            writer.writerow([
                "排名", "方案名称", "方案类型", "投资额(元)", "年节电量(kWh)", 
                "年节气量(m³)", "年减排量(吨CO₂)", "年节省费用(元)", 
                "投资回收期(年)", "投资回报率(%)", "寿命期(年)", "描述"
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
                    plan.get("description", ""),
                ])
            
            writer.writerow([])
            
            writer.writerow(["五、累计减排与现金流预测 (前10年)"])
            writer.writerow(["年份", "年减排量(吨CO₂)", "累计减排量(吨CO₂)", "年节省费用(元)", "累计节省费用(元)", "累计净现金流(元)"])
            
            cum_carbon = 0
            cum_savings = 0
            for year in range(1, 11):
                cum_carbon += total_annual_carbon
                cum_savings += total_annual_savings
                net_cash = cum_savings - total_investment
                writer.writerow([
                    f"第{year}年",
                    f"{total_annual_carbon:.4f}",
                    f"{cum_carbon:.4f}",
                    f"{total_annual_savings:.2f}",
                    f"{cum_savings:.2f}",
                    f"{net_cash:.2f}",
                ])
            
            writer.writerow([])
            
            writer.writerow(["六、关键风险与提示"])
            if all_risks["key_risks"]:
                for i, risk in enumerate(all_risks["key_risks"], 1):
                    writer.writerow([f"关键风险{i}", risk])
            if all_risks["medium_risks"]:
                for i, risk in enumerate(all_risks["medium_risks"], 1):
                    writer.writerow([f"中等风险{i}", risk])
            writer.writerow([])
            
            writer.writerow(["七、建议下一步行动"])
            for i, rec in enumerate(all_risks["recommendations"], 1):
                writer.writerow([f"建议{i}", rec])
        
        return output_file

    def export_json(self, output_file=None, budget=None):
        report_gen = ReportGenerator(self.project_dir)
        report_data = report_gen.generate_report(output_format="json", budget=budget)
        
        report_data["report_title"] = "碳减排项目评估 - 管理层汇报表"
        report_data["tariff"] = self.tariff
        
        if output_file is None:
            output_file = Path(self.project_dir) / "results" / "management_report.json"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        ProjectConfig.save_json(output_file, report_data)
        return output_file
