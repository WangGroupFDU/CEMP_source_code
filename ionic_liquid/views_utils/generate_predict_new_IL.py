import pandas as pd
from .utils import combine_ion2IL
from .utils_predict_value import predict_property


def generate_predict_new_IL(new_cation_path, new_anion_path, output_file_path, cation_limit=5000, anion_limit=300, seed=1):
    if new_cation_path.lower().endswith('.csv'):
        cation_df = pd.read_csv(new_cation_path)
    elif new_cation_path.lower().endswith(('.xls', '.xlsx')):
        cation_df = pd.read_excel(new_cation_path) 
    else:
        raise ValueError("Unsupported cation file type. Only CSV or Excel files are supported.")
    
    if new_anion_path.lower().endswith('.csv'):
        anion_df = pd.read_csv(new_anion_path) 
    elif new_anion_path.lower().endswith(('.xls', '.xlsx')):
        anion_df = pd.read_excel(new_anion_path) 
    else:
        raise ValueError("Unsupported anion file type. Only CSV or Excel files are supported.")
    
    IL_df = combine_ion2IL(cation_df, anion_df, cation_limit, anion_limit, seed)
    total_count = len(IL_df)
    predict_property(IL_df, output_file_path)

    print(f"The ionic liquid file 'IL_output.csv' has been created in the current directory! A total of {total_count} ionic liquids were generated.")


