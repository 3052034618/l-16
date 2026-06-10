from ..core.importer import DataImporter
from ..core import ProjectConfig


def cmd_import(args):
    if not ProjectConfig.project_exists(args.project_dir):
        print(f"✗ 错误: 项目目录不存在或未初始化: {args.project_dir}")
        return 1
    
    importer = DataImporter(args.project_dir)
    
    try:
        if args.baseline:
            data = importer.import_baseline(args.baseline)
            print(f"✓ 已导入基准能耗数据: {args.baseline}")
        
        if args.equipment:
            data = importer.import_equipment(args.equipment)
            print(f"✓ 已导入设备清单: {args.equipment}")
        
        if args.tariff:
            data = importer.import_tariff(args.tariff)
            print(f"✓ 已导入电价信息: {args.tariff}")
        
        if args.plans:
            data = importer.import_plans(args.plans)
            print(f"✓ 已导入方案配置: {args.plans}")
        
        if not any([args.baseline, args.equipment, args.tariff, args.plans]):
            print("✗ 错误: 请指定至少一种要导入的数据类型 (--baseline, --equipment, --tariff, --plans)")
            return 1
            
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return 1
    
    return 0
