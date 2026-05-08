

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
    'experiment_polymer_data': {
        'model': 'polymer.models.experiment_polymer_data',
        'filename': 'experiment_polymer_data.xlsx',
        'description': '实验聚合物数据库'
    },
    'calculated_monomer_data': {
        'model': 'polymer.models.calculated_monomer_data',
        'filename': 'calculated_monomer_data.xlsx',
        'description': '计算单体数据库'
    },
    'calculated_polymer_data': {
        'model': 'polymer.models.calculated_polymer_data',
        'filename': 'calculated_polymer_data.xlsx',
        'description': '计算聚合物数据库'
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
    print("Polymer数据库Excel导出工具")
    print("=" * 60)

    
    output_dir = os.path.join(settings.MEDIA_ROOT, 'Polymer', 'Database_full')
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n输出目录: {output_dir}\n")

    total_records = 0
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    
    for db_name, config in DATABASES.items():
        output_path = os.path.join(output_dir, config['filename'])

        try:
            count = export_model_to_excel(config['model'], output_path)
            total_records += count
        except Exception as e:
            print(f"✗ {db_name} 导出失败: {str(e)}")

    
    print("\n" + "=" * 60)
    print(f"导出完成！时间: {timestamp}")
    print(f"总计: {total_records} 条记录")
    print(f"输出目录: {output_dir}")
    print("=" * 60)

if __name__ == '__main__':
    main()
