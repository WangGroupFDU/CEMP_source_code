import pandas as pd
from ...models import Example
from django.core.management.base import BaseCommand
import pandas as pd


class Command(BaseCommand):
    help = 'Import data from Excel file'

    def handle(self, *args, **kwargs):
        df = pd.read_excel('Example.xlsx', engine='openpyxl')
        
        for index, row in df.iterrows():
            
            entry = Example(
                X1=row["X1"],
                X2=row["X2"],
                X3=row["X3"],
                X4=row["X4"],
            )
            
            entry.save()

        print('Excel数据已成功导入到sqlite3数据库。')