import pandas as pd
from ...models import ILgenerator_IL
from django.core.management.base import BaseCommand
import pandas as pd


class Command(BaseCommand):
    help = 'Import data from Excel file'

    def handle(self, *args, **kwargs):
        df = pd.read_csv('ILgenerator_IL_top50000.csv')
        entries = []

        
        for index, row in df.iterrows():
            entry = ILgenerator_IL(
                Name=row["Name"],
                SMILES=row["SMILES"],
                Anion_Name=row["Anion_Name"],
                Cation_Name=row["Cation_Name"],
                Cation_SMILES_type=row["Cation_SMILES_type"],
                Anion_SMILES=row["Anion_SMILES"],
                Cation_SMILES=row["Cation_SMILES"],
                conductivity=row["conductivity(S/m)"],
                Ea=row["Ea(kJ/mol)"],
                lnA=row["lnA"],
                Tm=row["Tm(K)"],
                ECW=row["ECW(V)"],
                ILScore=row["ILScore"]
            )
            entries.append(entry)

        
        ILgenerator_IL.objects.bulk_create(entries, batch_size=10000) 

        print('Excel数据已成功导入到sqlite3数据库。')
