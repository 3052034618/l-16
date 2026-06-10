from ..core.templates import init_project


def cmd_init(args):
    try:
        proj_path = init_project(args.project_dir, overwrite=args.overwrite)
        print(f"✓ 项目已成功初始化: {proj_path}")
        print(f"  - baseline.json     基准能耗数据")
        print(f"  - equipment.json    设备清单")
        print(f"  - tariff.json       电价信息")
        print(f"  - plans.json        改造方案配置")
        print(f"  - results/          结果输出目录")
    except FileExistsError as e:
        print(f"✗ 错误: {e}")
        return 1
    return 0
