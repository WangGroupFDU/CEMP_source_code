

import os
import sys
import django
from datetime import datetime


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cemp.settings')
django.setup()

import pandas as pd
from django.conf import settings


DATABASES = {
    'IL': {
        'model': 'ionic_liquid.models.IL',
        'filename': 'IL.xlsx',
        'description': '离子液体IL数据库（最重要）'
    },
    'Cation': {
        'model': 'ionic_liquid.models.Cation',
        'filename': 'Cation.xlsx',
        'description': '阳离子数据库'
    },
    'Anion': {
        'model': 'ionic_liquid.models.Anion',
        'filename': 'Anion.xlsx',
        'description': '阴离子数据库'
    },
    'ILgenerator_IL': {
        'model': 'ionic_liquid.models.ILgenerator_IL',
        'filename': 'ILgenerator_IL.xlsx',
        'description': '离子液体生成器数据库（含预测性质）'
    },
    'Li_electrolyte': {
        'model': 'ionic_liquid.models.Li_electrolyte',
        'filename': 'Li_electrolyte.xlsx',
        'description': '锂电解质数据库'
    },
    'metal_anion_energy': {
        'model': 'ionic_liquid.models.metal_anion_energy',
        'filename': 'metal_anion_energy.xlsx',
        'description': '金属-阴离子结合能数据库'
    },
}


def export_model_to_excel(model_path, output_path):
    module_path, model_name = model_path.rsplit('.', 1)
    module = __import__(module_path, fromlist=[model_name])
    model = getattr(module, model_name)

    print(f"正在导出 {model_name}...")

    queryset = model.objects.all()

    data = []
    for obj in queryset.iterator(chunk_size=1000):
        row = {}
        for field in model._meta.get_fields():
            row[field.name] = getattr(obj, field.name, None)
        data.append(row)

    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False, engine='openpyxl')

    print(f"✓ {model_name}: {len(df)} 条记录 → {output_path}")
    return len(df)


def main():
    print("=" * 60)
    print("Ionic Liquid数据库Excel导出工具")
    print("=" * 60)

    output_dir = os.path.join(settings.MEDIA_ROOT, 'ionic_liquid', 'Database_full')
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n输出目录: {output_dir}\n")

    total_records = 0
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for db_name, config in DATABASES.items():
        output_path = os.path.join(output_dir, config['filename'])
        try:
            count = export_model_to_excel(config['model'], output_path)
            total_records += count
        except Exception as exc:
            print(f"✗ {db_name} 导出失败: {exc}")

    print("\n" + "=" * 60)
    print(f"导出完成！时间: {timestamp}")
    print(f"总计: {total_records} 条记录")
    print(f"输出目录: {output_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
