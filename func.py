import pandas as pd

def replace_spaces_in_column(excel_path, column_name, save_path=None):
    try:
        
        df = pd.read_excel(excel_path, engine='openpyxl')

        
        if column_name not in df.columns:
            raise ValueError(f"列 '{column_name}' 在Excel文件中不存在。")

        
        df[column_name] = df[column_name].str.replace(' ', '_')

        
        if save_path:
            df.to_excel(save_path, index=False)
            print(f"修改后的Excel文件已保存到: {save_path}")

        return df

    except Exception as e:
        print(f"发生错误: {e}")


replace_spaces_in_column(excel_path="/path/to/example/Li+-electrolyte.xlsx", column_name="Dimer_Name", save_path="/path/to/example/Li+-electrolyte.xlsx")
replace_spaces_in_column(excel_path="/path/to/example/Dimer.xlsx", column_name="Dimer Name", save_path="/path/to/example/Dimer.xlsx")