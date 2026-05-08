import pandas as pd
list = ['Al','Ba','Ca','K','Li','Mg','Na','Zn']
df = pd.read_excel('Al_cleaned.xlsx')
col_name = df.columns.tolist()
for item in col_name:
    print(item)