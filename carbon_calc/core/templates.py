import json
import os
from pathlib import Path
import shutil


DEFAULT_BASELINE = {
    "annual_electricity_kwh": 1000000,
    "annual_gas_m3": 50000,
    "annual_water_ton": 10000,
    "operating_hours": 8760,
    "carbon_factor_electricity": 0.5839,
    "carbon_factor_gas": 2.1622,
    "description": "基准年能耗数据"
}

DEFAULT_TARIFF = {
    "electricity_price": 0.85,
    "gas_price": 3.5,
    "water_price": 5.0,
    "demand_charge": 0,
    "peak_price": 1.2,
    "valley_price": 0.4,
    "flat_price": 0.8,
    "description": "电价及能源价格信息"
}

DEFAULT_EQUIPMENT = {
    "lighting": [
        {"name": "车间照明", "type": "T8荧光灯", "count": 500, "power_w": 40, "hours_per_day": 10, "days_per_year": 300}
    ],
    "air_conditioning": [
        {"name": "中央空调", "type": "冷水机组", "capacity_kw": 500, "cop": 3.5, "hours_per_day": 12, "days_per_year": 180}
    ],
    "photovoltaic": [
        {"name": "厂房屋顶", "area_m2": 2000, "tilt_angle": 30, "orientation": "south"}
    ],
    "waste_heat_recovery": [
        {"name": "空压机余热", "heat_source": "空压机", "waste_heat_kw": 100, "operating_hours": 6000, "recovery_efficiency": 0.6}
    ]
}

DEFAULT_PLANS = {
    "plan_led": {
        "name": "LED照明改造",
        "type": "lighting",
        "description": "将传统荧光灯替换为LED灯",
        "investment": 150000,
        "efficiency_improvement": 0.6,
        "lifetime_years": 8,
        "maintenance_cost": 2000
    },
    "plan_ac_inverter": {
        "name": "空调变频改造",
        "type": "air_conditioning",
        "description": "中央空调加装变频控制系统",
        "investment": 300000,
        "efficiency_improvement": 0.25,
        "lifetime_years": 10,
        "maintenance_cost": 5000
    },
    "plan_rooftop_pv": {
        "name": "屋顶光伏项目",
        "type": "photovoltaic",
        "description": "厂房屋顶安装太阳能光伏发电系统",
        "investment": 800000,
        "capacity_kw": 200,
        "annual_generation_kwh_per_kw": 1100,
        "self_use_ratio": 0.7,
        "lifetime_years": 25,
        "maintenance_cost": 8000
    },
    "plan_waste_heat": {
        "name": "余热回收系统",
        "type": "waste_heat_recovery",
        "description": "空压机余热回收用于热水供应",
        "investment": 250000,
        "heat_recovery_rate": 0.6,
        "displaced_fuel": "gas",
        "lifetime_years": 15,
        "maintenance_cost": 6000
    }
}


def init_project(project_dir, overwrite=False):
    proj_path = Path(project_dir).resolve()
    
    if proj_path.exists() and not overwrite:
        if list(proj_path.iterdir()):
            raise FileExistsError(f"目录 {proj_path} 已存在且不为空，使用 --overwrite 覆盖")
    
    proj_path.mkdir(parents=True, exist_ok=True)
    
    from ..core import ProjectConfig
    
    ProjectConfig.save_json(proj_path / "baseline.json", DEFAULT_BASELINE)
    ProjectConfig.save_json(proj_path / "tariff.json", DEFAULT_TARIFF)
    ProjectConfig.save_json(proj_path / "equipment.json", DEFAULT_EQUIPMENT)
    ProjectConfig.save_json(proj_path / "plans.json", DEFAULT_PLANS)
    
    results_path = proj_path / "results"
    results_path.mkdir(exist_ok=True)
    
    return proj_path
