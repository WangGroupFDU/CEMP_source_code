
import os  
from rdkit import Chem
from rdkit.Chem import AllChem, AddHs, RemoveHs, RWMol
from rdkit.Chem.rdmolfiles import MolToSmiles
from openbabel import openbabel, pybel
import os
import re
import pandas as pd
import subprocess
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from openpyxl import Workbook
import time
import shutil
import glob


from cemp_software_settings import load_and_apply_settings
result = load_and_apply_settings()


def check_and_create_gaussian_database(base_dir: str = result['gaussian_database_path']):  
    home_directory = os.path.abspath(os.path.expanduser(base_dir))  
    gaussian_database_path = os.path.join(home_directory, 'Gaussian_database')  
    optfreq_gaussian_database_path = os.path.join(gaussian_database_path, 'opt+freq')  
    RESPpolymer_database_path = os.path.join(gaussian_database_path, 'RESPpolymer')  

    if not os.path.exists(gaussian_database_path):  
        os.makedirs(gaussian_database_path)  
        os.makedirs(optfreq_gaussian_database_path)  
        os.makedirs(RESPpolymer_database_path)  
        print(f"文件夹不存在，已在{gaussian_database_path}创建Gaussian_database文件夹。")  

    elif not os.path.exists(optfreq_gaussian_database_path) and os.path.exists(RESPpolymer_database_path):  
        os.makedirs(optfreq_gaussian_database_path)  
        print(f"opt+freq文件夹不存在，已在{optfreq_gaussian_database_path}创建opt+freq文件夹。")  

    elif not os.path.exists(RESPpolymer_database_path) and os.path.exists(optfreq_gaussian_database_path):  
        os.makedirs(RESPpolymer_database_path)  
        print(f"RESPpolymer文件夹不存在，已在{RESPpolymer_database_path}创建RESPpolymer文件夹。")  

    elif not os.path.exists(RESPpolymer_database_path) and not os.path.exists(optfreq_gaussian_database_path):  
        os.makedirs(optfreq_gaussian_database_path)  
        os.makedirs(RESPpolymer_database_path)  
        print(f"RESPpolymer和opt+freq文件夹不存在，已在{RESPpolymer_database_path}和{optfreq_gaussian_database_path}创建文件夹。")  

    else:  
        print(f"Gaussian_database文件夹已存在于{gaussian_database_path}。")  

    return gaussian_database_path, optfreq_gaussian_database_path, RESPpolymer_database_path  



def compare_smiles_dicts(system_dict, database_dict):
    not_found_molecule_dict = {}
    found_molecule_dict = {}

    
    for smiles, name in system_dict.items():
        if smiles not in database_dict.keys():
            not_found_molecule_dict[smiles] = name

    
    for smiles in database_dict:
        if smiles in system_dict:
            name = system_dict[smiles]  
            found_molecule_dict[smiles] = name

    return not_found_molecule_dict, found_molecule_dict


def read_excel_to_dict(excel_path, key_col, value_col):
    try:
        
        df = pd.read_excel(excel_path)
        
        
        if key_col not in df.columns or value_col not in df.columns:
            raise ValueError(f"指定的列'{key_col}'或'{value_col}'在表格中不存在。")
        
        
        result_dict = pd.Series(df[value_col].values,index=df[key_col]).to_dict()
        
        return result_dict
    except FileNotFoundError:
        print(f"文件 {excel_path} 未找到。")
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"读取Excel文件时发生错误：{e}")


def read_system_excel_to_dict(excel_path, SMILESName="SMILES", Name="Name"):
    return read_excel_to_dict(excel_path, SMILESName, Name)


def read_database_excel_to_dict(database_path):
    return read_excel_to_dict(database_path, 'SMILES', 'FileName')


def create_or_load_molecule_xlsx(directory):
    
    xlsx_path = os.path.join(directory, 'molecule.xlsx')
    
    
    if not os.path.exists(xlsx_path):
        
        df = pd.DataFrame(columns=['FileName', 'SMILES'])
        
        df.to_excel(xlsx_path, index=False)
    else:
        
        df = pd.read_excel(xlsx_path)
    
    return df


def normalization(mol):
    smi=Chem.MolToSmiles(mol)
    n_mol=Chem.MolFromSmiles(smi)
    return n_mol


def get_filename_without_extension(xlsx_path):
    
    base_name = os.path.basename(xlsx_path)
    
    file_name_without_extension = os.path.splitext(base_name)[0]
    return file_name_without_extension


def normalization_SMILES(excel_path, SMILESName="SMILES"):
    
    df = pd.read_excel(excel_path)
    file_name_without_extension = get_filename_without_extension(excel_path)
    
    
    if SMILESName in df.columns:
        
        for index, row in df.iterrows():
            
            mol = Chem.MolFromSmiles(row[SMILESName])
            if mol is not None:  
                
                n_mol = normalization(mol)
                
                n_smi = Chem.MolToSmiles(n_mol)
                
                df.at[index, SMILESName] = n_smi

        
        df.to_excel(f'{file_name_without_extension}.xlsx', index=False)
    else:
        print(f"The {SMILESName} column does not exist in the provided Excel file.")

def copy_files_based_on_smiles(database_directory, database_excel_path, found_molecule_dict, destination_directory, SMILESName = 'SMILES'):
    
    if not os.path.exists(destination_directory):
        raise Exception(f"{destination_directory} does not exist")

    
    df = pd.read_excel(database_excel_path)

    
    for smiles, name in found_molecule_dict.items():
        
        matched_files = df[df[SMILESName] == smiles]['FileName'].tolist()
        
        
        for matched_file in matched_files:
            
            for ext in ['.gjf', '.chk', '.out']:
                file_to_copy = matched_file + ext
                source_path = os.path.join(database_directory, file_to_copy)
                
                if os.path.isfile(source_path):
                    
                    new_name = name + ext
                    destination_path = os.path.join(destination_directory, new_name)
                    
                    shutil.copy2(source_path, destination_path)
                    print(f"文件 {new_name} （即数据库中的 {file_to_copy} ）已被复制到路径： {destination_directory}")
                else:
                    print(f"文件 {new_name} 不存在，无法复制。")