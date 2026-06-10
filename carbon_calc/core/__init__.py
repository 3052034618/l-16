import json
import os
from pathlib import Path


class ProjectConfig:
    PROJECT_FILES = {
        "baseline": "baseline.json",
        "equipment": "equipment.json",
        "tariff": "tariff.json",
        "plans": "plans.json",
        "results": "results.json",
    }

    @staticmethod
    def get_project_path(project_dir):
        return Path(project_dir).resolve()

    @classmethod
    def get_file_path(cls, project_dir, key):
        return cls.get_project_path(project_dir) / cls.PROJECT_FILES[key]

    @staticmethod
    def load_json(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_json(file_path, data):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def project_exists(project_dir):
        proj_path = ProjectConfig.get_project_path(project_dir)
        return proj_path.is_dir() and (proj_path / "plans.json").exists()
