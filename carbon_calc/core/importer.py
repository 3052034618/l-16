import json
import csv
from pathlib import Path
from ..core import ProjectConfig


class DataImporter:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.proj_path = ProjectConfig.get_project_path(project_dir)

    def import_baseline(self, input_file):
        data = self._load_file(input_file)
        self._validate_baseline(data)
        ProjectConfig.save_json(self.proj_path / "baseline.json", data)
        return data

    def import_equipment(self, input_file):
        data = self._load_file(input_file)
        self._validate_equipment(data)
        ProjectConfig.save_json(self.proj_path / "equipment.json", data)
        return data

    def import_tariff(self, input_file):
        data = self._load_file(input_file)
        self._validate_tariff(data)
        ProjectConfig.save_json(self.proj_path / "tariff.json", data)
        return data

    def import_plans(self, input_file):
        data = self._load_file(input_file)
        self._validate_plans(data)
        ProjectConfig.save_json(self.proj_path / "plans.json", data)
        return data

    def _load_file(self, input_file):
        file_path = Path(input_file)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {input_file}")
        
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            return ProjectConfig.load_json(file_path)
        elif suffix == ".csv":
            return self._csv_to_json(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")

    def _csv_to_json(self, csv_path):
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return {}
        
        if len(rows) == 1 and "key" in rows[0] and "value" in rows[0]:
            result = {}
            for row in rows:
                key = row["key"]
                value = row["value"]
                try:
                    value = float(value) if "." in value else int(value)
                except (ValueError, TypeError):
                    pass
                result[key] = value
            return result
        else:
            return rows

    def _validate_baseline(self, data):
        required = ["annual_electricity_kwh", "carbon_factor_electricity"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"基准能耗数据缺少必要字段: {', '.join(missing)}")

    def _validate_equipment(self, data):
        if not isinstance(data, dict):
            raise ValueError("设备清单必须是字典格式")

    def _validate_tariff(self, data):
        required = ["electricity_price"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"电价数据缺少必要字段: {', '.join(missing)}")

    def _validate_plans(self, data):
        if not isinstance(data, dict):
            raise ValueError("方案数据必须是字典格式")
        for plan_id, plan in data.items():
            if "type" not in plan:
                raise ValueError(f"方案 {plan_id} 缺少 type 字段")
            if "investment" not in plan:
                raise ValueError(f"方案 {plan_id} 缺少 investment 字段")
