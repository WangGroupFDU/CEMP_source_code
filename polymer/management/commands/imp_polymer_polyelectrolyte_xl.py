import pandas as pd
from django.core.management.base import BaseCommand
from polymer.models import Polyelectrolyte

class Command(BaseCommand):
    help = '从Excel文件导入数据'

    def handle(self, *args, **kwargs):
        
        df = pd.read_excel('polymer/polyelectrolyte.xlsx')

        
        for index, row in df.iterrows():
            entry=Polyelectrolyte(
                polyelectrolyte=row['Polyelectrolytes'],
                copolymer=row['Copolymer(containing multiple types of repeat unit structures)'],
                cation=row['Cation'],
                anion=row['Anion'],
                repeat_unit=row['Repeat Unit'],
                dielectric_constant=row['Dielectric Constant'],
                chemical_structure=row['Chemical Structure'],
                hydrophilic_hydrophobic=row['Hydrophilic/Hydrophobic'],
                functional_group=row['Functional group'],
                application_function=row['Application and Function'],
                reference=row['Reference'],
                synonyms=row['Synonyms'],
                chemdraw_file=row['Chemdraw file']
            )
            
            entry.save()
        print('Excel数据已成功导入到sqlite3数据库。')
