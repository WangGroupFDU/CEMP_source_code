import os 
from django.conf import settings
import pandas as pd

from autocompute.utils import extract_xyz_coordinate_block

def create_result_excel(name, unique_folder):

    
    folder_path = os.path.join(settings.MEDIA_ROOT, 'AutoCompute', 'QcCompute', 'Downloads', unique_folder)
    
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    
    file_path = os.path.join(folder_path, 'Result.xlsx')
    
    
    
    if isinstance(name, str):
        data = [name]
    elif isinstance(name, list):
        data = name
    else:
        data = [str(name)]
    
    
    df = pd.DataFrame({'Name': data})
    
    
    df.to_excel(file_path, index=False)
    
    
    download_url = os.path.join(settings.MEDIA_URL, 'AutoCompute', 'QcCompute', 'Downloads', unique_folder, 'Result.xlsx')
    
    return download_url
def extract_coordinates(file_obj):
    return extract_xyz_coordinate_block(file_obj)

def create_ORCA_opt_inputfile(coordinate_str, charge, multiplicity, output_inp_file_path, mem=20, nproc=8000):
    
    with open(output_inp_file_path, 'w') as f:
        
        f.write(f"! B3LYP D3 def2-TZVP def2/J RIJCOSX opt freq tightSCF noautostart miniprint\n")
        f.write(f"%maxcore     {mem}\n")
        f.write(f"%pal nprocs  {nproc} end\n")
        f.write(f"* xyz   {charge} {multiplicity}\n")
        f.write(coordinate_str)
        f.write(f"*")




