import pandas as pd
import re
from rdkit import Chem
import pubchempy as pcp
import os
from cryptography.fernet import Fernet  
import json
from django.conf import settings 

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
from django.utils import timezone
from autocompute.models import ComputeTask


def decrypt_download_url_list(encrypted_id):
    cipher_suite = Fernet(settings.FERNET_SECRET_KEY)
    
    try:
        
        decrypted = cipher_suite.decrypt(encrypted_id.encode('utf-8'))

        
        download_url_list = json.loads(decrypted.decode('utf-8'))

        return download_url_list
    except Exception as e:
        
        print(f"解密失败: {str(e)}")
        return None


def validate_HTQC_single_point_energy_df(df):
    
    result_message = []  

    
    if 'Name' not in df.columns:
        result_message.append("❌ The 'Name' column is missing.")
    if 'SMILES' not in df.columns:
        result_message.append("❌ The 'SMILES' column is missing.")
    
    
    if result_message:
        return "<br>".join(result_message)
    
    
    illegal_chars_pattern = r"[(){}\[\],，。？！、：；‘’“”《》【】（）……￥#@!~%^&*<>?/|\\]"
    illegal_names = df['Name'].apply(lambda x: bool(re.search(illegal_chars_pattern, str(x))))
    if illegal_names.any():
        result_message.append("❌ The 'Name' column contains illegal characters: " + ", ".join(df[illegal_names]['Name'].tolist()))
    else:
        result_message.append("✅ The 'Name' column passed the character validation.")
    
    
    invalid_smiles = df['SMILES'].apply(lambda x: Chem.MolFromSmiles(str(x)) is None)
    if invalid_smiles.any():
        result_message.append("❌ The 'SMILES' column contains invalid SMILES: " + ", ".join(df[invalid_smiles]['SMILES'].tolist()))
    else:
        result_message.append("✅ The 'SMILES' column contains all valid SMILES.")
    
    
    return "<br>".join(result_message)


def validate_HTQC_binding_energy_df(df):
    """
    Validate the existence of 'Dimer Name', 'Component Name A', 'Component Name B' columns, 
    check for illegal characters in these columns, and validate the SMILES in 'Dimer SMILES', 
    'Component SMILES A', and 'Component SMILES B' using RDKit.
    
    Parameters:
        df: pandas DataFrame, containing the columns to validate.
    
    Returns:
        result_message: A string containing all the validation results, formatted for frontend display.
    """
    
    result_message = []  

    
    required_columns = ['Dimer Name', 'Component Name A', 'Component Name B', 'Dimer SMILES', 'Component SMILES A', 'Component SMILES B']
    
    for column in required_columns:
        if column not in df.columns:
            result_message.append(f"❌ The '{column}' column is missing.")
    
    
    if result_message:
        return "<br>".join(result_message)

    
    illegal_chars_pattern = r"[(){}\[\],，。？！、：；‘’“”《》【】（）……￥#@!~%^&*<>?/|\\]"

    
    name_columns = ['Dimer Name', 'Component Name A', 'Component Name B']
    for column in name_columns:
        illegal_names = df[column].apply(lambda x: bool(re.search(illegal_chars_pattern, str(x))))
        if illegal_names.any():
            result_message.append(f"❌ The '{column}' column contains illegal characters: " + ", ".join(df[illegal_names][column].tolist()))
        else:
            result_message.append(f"✅ The '{column}' column passed the character validation.")

    
    smiles_columns = ['Dimer SMILES', 'Component SMILES A', 'Component SMILES B']
    for column in smiles_columns:
        invalid_smiles = df[column].apply(lambda x: Chem.MolFromSmiles(str(x)) is None)
        if invalid_smiles.any():
            result_message.append(f"❌ The '{column}' column contains invalid SMILES: " + ", ".join(df[invalid_smiles][column].tolist()))
        else:
            result_message.append(f"✅ The '{column}' column contains all valid SMILES.")
    
    
    return "<br>".join(result_message)

def validate_HTQC_pka_pkb_df(df):
    
    result_message = []  

    
    required_columns = ['Acid_Name', 'Acid_SMILES', 'Conjugate_Alkali_Name', 'Conjugate_Alkali_SMILES']
    
    for column in required_columns:
        if column not in df.columns:
            result_message.append(f"❌ The '{column}' column is missing.")
    
    
    if result_message:
        return "<br>".join(result_message)

    
    illegal_chars_pattern = r"[(){}\[\],，。？！、：；‘’“”《》【】（）……￥#@!~%^&*<>?/|\\]"

    
    name_columns = ['Acid_Name', 'Conjugate_Alkali_Name']
    for column in name_columns:
        illegal_names = df[column].apply(lambda x: bool(re.search(illegal_chars_pattern, str(x))))
        if illegal_names.any():
            result_message.append(f"❌ The '{column}' column contains illegal characters: " + ", ".join(df[illegal_names][column].tolist()))
        else:
            result_message.append(f"✅ The '{column}' column passed the character validation.")

    
    smiles_columns = ['Acid_SMILES', 'Conjugate_Alkali_SMILES']
    for column in smiles_columns:
        invalid_smiles = df[column].apply(lambda x: Chem.MolFromSmiles(str(x)) is None)
        if invalid_smiles.any():
            result_message.append(f"❌ The '{column}' column contains invalid SMILES: " + ", ".join(df[invalid_smiles][column].tolist()))
        else:
            result_message.append(f"✅ The '{column}' column contains all valid SMILES.")
    
    
    return "<br>".join(result_message)


def validate_MD_system_df(df):

    result_message = []  

    
    required_columns = ['Serial Number', 'Name', 'is polymer', 'repeating unit', 'SMILES', 'Number', 'temperature (K)', 
                        'center atom', 'scale_charge', 'is polymer melt']
    
    for column in required_columns:
        if column not in df.columns:
            result_message.append(f"❌ The '{column}' column is missing.")
    
    
    if result_message:
        return "<br>".join(result_message)

    
    if not pd.api.types.is_integer_dtype(df['Serial Number']):
        result_message.append("❌ The 'Serial Number' column should contain only integers.")
    elif df['Serial Number'].duplicated().any():
        result_message.append("❌ The 'Serial Number' column contains duplicate values.")
    else:
        result_message.append("✅ The 'Serial Number' column passed the validation.")

    
    illegal_chars_pattern = r"[(){}\[\],，。？！、：；‘’“”《》【】（）……￥#@!~%^&*<>?/|\\]"
    
    illegal_names = df['Name'].apply(lambda x: bool(re.search(illegal_chars_pattern, str(x))))
    if illegal_names.any():
        result_message.append(f"❌ The 'Name' column contains illegal characters: " + ", ".join(df[illegal_names]['Name'].tolist()))
    else:
        result_message.append("✅ The 'Name' column passed the character validation.")

    invalid_smiles = df['SMILES'].apply(lambda x: Chem.MolFromSmiles(str(x)) is None)
    if invalid_smiles.any():
        result_message.append(f"❌ The 'SMILES' column contains invalid SMILES: " + ", ".join(df[invalid_smiles]['SMILES'].tolist()))
    else:
        result_message.append("✅ The 'SMILES' column contains all valid SMILES.")
    
    
    if not pd.api.types.is_bool_dtype(df['is polymer']):
        result_message.append("❌ The 'is polymer' column should contain only True or False values.")
    else:
        polymer_issues = df[df['is polymer'] == True]['SMILES'].apply(lambda x: '*' not in str(x))
        if polymer_issues.any():
            result_message.append("❌ Some SMILES in 'is polymer' rows do not contain '*', indicating a possible issue with the polymer repeating unit.")
        else:
            result_message.append("✅ The 'is polymer' column passed validation.")
    
    
    if not pd.api.types.is_integer_dtype(df['repeating unit']):
        result_message.append("❌ The 'repeating unit' column should contain only integers.")
    else:
        result_message.append("✅ The 'repeating unit' column passed validation.")
    
    
    if not pd.api.types.is_integer_dtype(df['Number']):
        result_message.append("❌ The 'Number' column should contain only integers.")
    elif (df['Number'] > 2000).any():
        result_message.append("⚠️ Some values in the 'Number' column exceed 2000, which may lead to computational inefficiencies.")
    else:
        result_message.append("✅ The 'Number' column passed validation.")
    
    
    if not pd.api.types.is_float_dtype(df['temperature (K)']):
        result_message.append("❌ The 'temperature (K)' column should contain only floating point numbers.")
    elif (df['temperature (K)'] > 500).any():
        result_message.append("⚠️ Some values in the 'temperature (K)' column exceed 500K, which might cause simulation instability.")
    else:
        result_message.append("✅ The 'temperature (K)' column passed validation.")
    
    
    if not df['center atom'].isin(df['Name']).all():
        result_message.append("❌ Some values in the 'center atom' column do not match any entries in the 'Name' column.")
    elif len(df['center atom'].unique()) > 1:
        result_message.append("❌ The 'center atom' column contains more than one unique value. All entries should be identical.")
    else:
        result_message.append("✅ The 'center atom' column passed validation.")
    
    
    if not pd.api.types.is_float_dtype(df['scale_charge']):
        result_message.append("❌ The 'scale_charge' column should contain only floating point numbers.")
    else:
        result_message.append("✅ The 'scale_charge' column passed validation.")
    
    
    if not pd.api.types.is_bool_dtype(df['is polymer melt']):
        result_message.append("❌ The 'is polymer melt' column should contain only True or False values.")
    elif len(df['is polymer melt'].unique()) > 1:
        result_message.append("❌ The 'is polymer melt' column contains both True and False values. All entries should be identical.")
    else:
        result_message.append("✅ The 'is polymer melt' column passed validation.")
    
    
    def calculate_formal_charge(smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 0
        return sum([atom.GetFormalCharge() for atom in mol.GetAtoms()])
    
    total_charge = 0
    for index, row in df.iterrows():
        formal_charge = calculate_formal_charge(row['SMILES'])
        if row['is polymer']:
            total_charge += row['Number'] * formal_charge * row['repeating unit']
        else:
            total_charge += row['Number'] * formal_charge

    if abs(total_charge) > 0.001:
        result_message.append(f"⚠️ Charge imbalance detected. Total charge of the system is {total_charge:.4f}, which might cause issues in the simulation.")
    else:
        result_message.append("✅ The system's charge is balanced.")

    
    return "<br>".join(result_message)


def extract_energy_from_out(file_path):
    energy = None
    with open(file_path, 'r') as file:
        lines = file.readlines()
        energy_line = ''
        for i, line in enumerate(lines):
            
            line = line.strip().replace('\n', '')
            
            if line.strip().endswith('H') and i+1 < len(lines):
                next_line = lines[i+1]
                if next_line.strip().startswith('F='):
                    
                    line = line.strip() + next_line.strip()
            
            if line.strip().endswith('HF') and i+1 < len(lines):
                next_line = lines[i+1]
                if next_line.strip().startswith('='):
                    
                    line = line.strip() + next_line.strip()
            
            if 'HF=' in line:
                
                start = line.find('HF=') + 3  
                energy_line = line[start:]
                
                if '\\' in energy_line:
                    energy = energy_line.split('\\')[0].strip()
                    return energy
                else:
                    
                    for j in range(i+1, len(lines)):
                        energy_line += lines[j].strip()
                        if '\\' in lines[j]:
                            energy = energy_line.split('\\')[0].strip()
                            return energy
    return energy  


def extract_dipole_moment(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()  

        
        dipole_moment_lines = [
            i for i, line in enumerate(lines)
            if re.search(r"Dipole moment \(field-independent basis, Debye\):", line)
        ]

        
        if not dipole_moment_lines:
            print("没有找到含有'Dipole moment (field-independent basis, Debye):'的行。")
            return None

        
        last_line_number = dipole_moment_lines[-1]

        
        next_line = lines[last_line_number + 1]
        match = re.search(r"Tot=\s*(-?\d+\.\d+)", next_line)

        
        if match:
            return float(match.group(1))
        else:
            print("下一行的格式不符合预期，无法提取数值。")
            return None

    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
        return None
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return None


def extract_homo_lumo(file_path):
    try:
        
        with open(file_path, 'r') as file:
            content = file.readlines()
        
        
        pop_analysis_lines = [i for i, line in enumerate(content) if re.match(r'\s*Population analysis', line)]
        
        
        if len(pop_analysis_lines) == 0:
            return None

        
        last_population_analysis = pop_analysis_lines[-1]

        
        homo, lumo = None, None
        for line_number in range(last_population_analysis, len(content)):
            occ_match = re.match(r'\s*Alpha\s+occ.\s+eigenvalues\s+--(.*)', content[line_number])
            virt_match = re.match(r'\s*Alpha\s+virt.\s+eigenvalues\s+--(.*)', content[line_number + 1]) if line_number + 1 < len(content) else None
            
            if occ_match and virt_match:
                
                homo = float(occ_match.group(1).strip().split()[-1])  
                lumo = float(virt_match.group(1).strip().split()[0])  
                break
        
        
        if homo is None or lumo is None:
            return None
        
        
        return homo, lumo
    
    except Exception as e:
        
        return None
    

def extract_entropy(file_path):
    
    entropy_pattern = re.compile(r'\s*Total\s+[0-9.-]+\s+[0-9.-]+\s+([0-9.-]+)')
    try:
        with open(file_path, 'r') as file:
            file_content = file.read()  
            match = entropy_pattern.search(file_content)
            if match:
                
                entropy_value_cal = float(match.group(1))
                
                entropy_value_joules = entropy_value_cal * 4.184 
                return entropy_value_joules
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return None  


def extract_enthalpy_correction(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if "Thermal correction to Enthalpy" in line:
                
                match = re.search(r"=\s*([-\d.]+)", line)
                if match:
                    return float(match.group(1))
    return None


def extract_gibbs_correction(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if "Thermal correction to Gibbs Free Energy" in line:
                
                match = re.search(r"=\s*([-\d.]+)", line)
                if match:
                    return float(match.group(1))
    return None



def get_conjugate_acid_base(smiles):
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("无效的SMILES字符串。")

    
    mol = Chem.AddHs(mol)
    
    
    mol_base = Chem.RWMol(mol)  
    
    mol_acid = Chem.RWMol(mol)
    
    
    
    deprotonated = False  
    for atom in mol_base.GetAtoms():
        
        if atom.GetSymbol() in ['O', 'N', 'S', 'P']:
            
            for neighbor in atom.GetNeighbors():
                
                if neighbor.GetSymbol() == 'H':
                    
                    hydrogen_idx = neighbor.GetIdx()
                    
                    mol_base.RemoveAtom(hydrogen_idx)
                    
                    atom.SetFormalCharge(atom.GetFormalCharge() - 1)
                    deprotonated = True  
                    break  
            if deprotonated:
                break  
    
    
    mol_base = Chem.RemoveHs(mol_base)
    
    conjugate_base_smiles = Chem.MolToSmiles(mol_base)
    
    
    
    protonated = False  
    for atom in mol_acid.GetAtoms():
        
        if atom.GetSymbol() in ['O', 'N', 'S', 'P']:
            
            if atom.GetFormalCharge() == 0:
                
                idx = atom.GetIdx()
                new_h = Chem.Atom('H')  
                mol_acid.AddAtom(new_h)  
                h_idx = mol_acid.GetNumAtoms() - 1  
                mol_acid.AddBond(idx, h_idx, order=Chem.BondType.SINGLE)  
                
                atom.SetFormalCharge(atom.GetFormalCharge() + 1)
                protonated = True  
                break  
    
    
    mol_acid = Chem.RemoveHs(mol_acid)
    
    conjugate_acid_smiles = Chem.MolToSmiles(mol_acid)
    
    
    return conjugate_base_smiles, conjugate_acid_smiles


def from_smiles_get_iupac_name(smiles):
    
    try:
        compounds = pcp.get_compounds(smiles, namespace='smiles')
        if compounds:
            
            iupac_name = compounds[0].iupac_name
            
            if iupac_name:
                return iupac_name
        else:
            
            return ''
    except Exception as e:
        
        print(f"在处理SMILES '{smiles}' 时发生错误：{e}")
        return ''


def get_safe_name(name):
    
    invalid_chars_pattern = r'[,\(\)\[\]\;\.\s]'

    
    replacement_char = '_'
    
    
    safe_name = re.sub(invalid_chars_pattern, replacement_char, name)
    
    
    return safe_name 


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


XYZ_COORDINATE_LINE_PATTERN = re.compile(
    r"^\s*([A-Za-z]{1,2})\s+"
    r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s+"
    r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s+"
    r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*$"
)


def _read_text_from_file_like(file_obj):

    if hasattr(file_obj, "seek"):
        try:
            file_obj.seek(0)
        except Exception:
            pass

    content = file_obj.read() if hasattr(file_obj, "read") else file_obj

    if isinstance(content, bytes):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("XYZ file must be UTF-8 encoded text.") from exc
    elif isinstance(content, str):
        text = content
    else:
        raise TypeError("Unsupported xyz input type.")

    if hasattr(file_obj, "seek"):
        try:
            file_obj.seek(0)
        except Exception:
            pass

    return text


def parse_xyz_content(file_obj):

    text = _read_text_from_file_like(file_obj)
    lines = text.splitlines()

    if len(lines) < 2:
        raise ValueError("XYZ file must contain at least two header lines.")

    atom_count_line = lines[0].strip()
    if not atom_count_line:
        raise ValueError("The first line of XYZ must be the atom count.")

    try:
        atom_count = int(atom_count_line)
    except ValueError as exc:
        raise ValueError("The first line of XYZ must be a positive integer atom count.") from exc

    if atom_count <= 0:
        raise ValueError("The atom count in XYZ must be greater than zero.")

    coordinate_lines = lines[2 : 2 + atom_count]
    if len(coordinate_lines) != atom_count:
        raise ValueError(
            f"XYZ contains {len(coordinate_lines)} coordinate lines, but atom count is {atom_count}."
        )

    validated_lines = []
    for index, line in enumerate(coordinate_lines, start=3):
        if not XYZ_COORDINATE_LINE_PATTERN.match(line):
            invalid_line = line.strip() if line.strip() else "<blank>"
            raise ValueError(f"Invalid XYZ coordinate line at line {index}: {invalid_line}")
        validated_lines.append(line.strip())

    trailing_lines = lines[2 + atom_count :]
    if any(line.strip() for line in trailing_lines):
        raise ValueError("XYZ file contains unexpected non-empty lines after the coordinate block.")

    return {
        "atom_count": atom_count,
        "comment_line": lines[1],
        "coordinate_lines": validated_lines,
        "coordinate_block": "\n".join(validated_lines),
    }


def extract_xyz_coordinate_block(file_obj):

    return parse_xyz_content(file_obj)["coordinate_block"]


def extract_coordinates(file_obj):

    return extract_xyz_coordinate_block(file_obj)

def create_ORCA_opt_inputfile(coordinate_str, charge, multiplicity, output_inp_file_path, mem=4000, nproc=20):
    
    with open(output_inp_file_path, 'w') as f:
        
        f.write(f"! B3LYP D3 def2-TZVP def2/J RIJCOSX opt freq tightSCF noautostart miniprint\n")
        f.write(f"%maxcore     {mem}\n")
        f.write(f"%pal nprocs  {nproc} end\n")
        f.write(f"* xyz   {charge} {multiplicity}\n")
        f.write(f"{coordinate_str}\n")
        f.write(f"*")

def create_ORCA_energy_inputfile(coordinate_str, charge, multiplicity, output_inp_file_path, mem=4000, nproc=20):
    
    with open(output_inp_file_path, 'w') as f:
        
        f.write(f"! wB97M-V def2-TZVP def2/J RIJCOSX strongSCF noautostart miniprint\n")
        f.write(f"%maxcore     {mem}\n")
        f.write(f"%pal nprocs  {nproc} end\n")
        f.write(f"%elprop Polar true end\n") 
        f.write(f"* xyz   {charge} {multiplicity}\n")
        f.write(f"{coordinate_str}\n")
        f.write(f"*")


def convert_chk_to_fchk(chk_path):
    
    for filename in os.listdir(chk_path):
        
        if filename.endswith('.chk'):
            
            base_filename = os.path.splitext(filename)[0]
            
            input_file = os.path.join(chk_path, filename)
            
            output_file = os.path.join(chk_path, base_filename + '.fchk')
            
            command = ['/root/Gaussian16_Linux_AVX2/tar/g16/formchk', input_file, output_file]
            
            try:
                
                subprocess.run(command, check=True)
                print(f"Converted {input_file} to {output_file}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to convert {input_file}: {e}")
def convert_gbw_to_molden(path):
    
    
    
    
    os.environ['PATH'] = '/home/fwtop/apps/openmpi/bin:' + os.environ.get('PATH', '')
    
    os.environ['LD_LIBRARY_PATH'] = '/home/fwtop/apps/openmpi/lib:' + os.environ.get('LD_LIBRARY_PATH', '')
    
    os.environ['OMPI_ALLOW_RUN_AS_ROOT'] = '1'
    os.environ['OMPI_ALLOW_RUN_AS_ROOT_CONFIRM'] = '1'

    import resource
    resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY)) 

    
    for filename in os.listdir(path):
        
        if filename.endswith('.gbw'):
            
            base_filename = os.path.splitext(filename)[0]
            
            input_file = os.path.join(path, base_filename)
            
            command = [
                '/home/public/orca_6_0_1_linux_x86-64_shared_openmpi416_avx2/orca_2mkl',
                input_file,
                "-molden"
            ]

            try:
                
                subprocess.run(command, check=True)
                print(f"Converted {input_file} to {input_file}.molden.input")
                
                
                generated_file = os.path.join(path, base_filename + ".molden.input")
                
                dest_path = os.path.join(path, base_filename + ".molden")
                
                shutil.copy(generated_file, dest_path)
                print(f"Copied {generated_file} to {dest_path}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to convert {input_file}: {e}")


def can_submit_today(request):
    
    user = request.user

    
    if not user.is_authenticated:
        from rest_framework.authtoken.models import Token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
            try:
                token = Token.objects.get(key=token_key)
                user = token.user
            except Token.DoesNotExist:
                
                return False, 0

    
    profile = getattr(user, 'userprofile', None)
    daily_limit = profile.daily_task_limit if profile else 3

    
    now = timezone.localtime()  
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day   = start_of_day + timezone.timedelta(days=1)

    today_count = ComputeTask.objects.filter(
        user=user,
        created_at__gte=start_of_day,
        created_at__lt =end_of_day
    ).count()

    signal = today_count < daily_limit
    

    
    return signal, daily_limit


def get_authenticated_user(request):
    
    user = request.user
    if user.is_authenticated:
        return user

    
    from rest_framework.authtoken.models import Token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Token '):
        token_key = auth_header.split(' ')[1]
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

    
    return None



import os                       
import subprocess               
import signal                   
from pathlib import Path        
from typing import List         
import tempfile          
import textwrap          
from shutil import which 

def batch_generate_esp_cub(fchk_folder_path: str) -> List[Path]:
    
    input_dir = Path(fchk_folder_path).expanduser().resolve()

    
    if not input_dir.is_dir():
        raise NotADirectoryError(f"路径 {input_dir} 不是有效文件夹")

    
    cmd_sequence = "\n".join(["5", "1", "3", "2", "0", "5", "12", "1", "2", "0", "q"])

    
    filename_list: List[Path] = []

    
    for fchk_path in input_dir.glob("*.fchk"):
        
        filename = fchk_path.stem
        print(filename)

        
        density_tmp = input_dir / "density.cub"
        esp_tmp = input_dir / "totesp.cub"

        
        if density_tmp.exists():
            density_tmp.unlink()
        if esp_tmp.exists():
            esp_tmp.unlink()

        
        cmd = ["Multiwfn", str(fchk_path), "-ESPrhoiso", "0.001"]

        
        with subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,      
            stdout=subprocess.PIPE,     
            stderr=subprocess.PIPE,
            text=True,                  
            cwd=input_dir               
        ) as proc:
            
            proc.communicate(input=cmd_sequence)

        
        density_new = input_dir / f"{filename}_density.cub"
        esp_new = input_dir / f"{filename}_ESP.cub"

        
        if density_tmp.exists():
            density_tmp.rename(density_new)
        else:
            print(f"警告: 未找到 {density_tmp.name}，请手动检查 {fchk_path.name}")

        if esp_tmp.exists():
            esp_tmp.rename(esp_new)
        else:
            print(f"警告: 未找到 {esp_tmp.name}，请手动检查 {fchk_path.name}")
        
        
        filename_list.append(filename)
    
    return filename_list

def generate_esp_vmd(fchk_folder_path, filename: str) -> None:
    
    
    
    basename = os.path.splitext(os.path.basename(filename))[0]  

    
    
    vmd_script = f"""#This script is used to draw ESP colored molecular vdW surface (rho=0.001)

color scale method BWR
color Display Background white
axes location Off
display depthcue off
display rendermode GLSL
light 2 on
light 3 on
material change transmode EdgyGlass 1.0
material change specular EdgyGlass 0.15
material change shininess EdgyGlass 0.95
material change opacity EdgyGlass 0.7
material change outlinewidth EdgyGlass 0.9
material change outline EdgyGlass 0.5

#The maximum number of systems to be loaded
set nsystem 1
#Lower and upper limit of color scale of ESP (a.u.)
set colorlow -0.03
set colorhigh 0.03
#eV as unit
#set colorlow -0.8
#set colorhigh 0.8

for {{set i 1}} {{${{i}}<=$nsystem}} {{incr i}} {{
set id [expr $i-1]
mol new {fchk_folder_path}/{basename}_density.cub
mol addfile {fchk_folder_path}/{basename}_ESP.cub
mol modstyle 0 $id CPK 1.000000 0.300000 22.000000 22.000000
mol addrep $id
mol modstyle 1 $id Isosurface 0.001000 0 0 0 1 1
mol modmaterial 1 $id EdgyGlass
mol modcolor 1 $id Volume 1
mol scaleminmax $id 1 $colorlow $colorhigh
}}
"""

    
    output_name = f"{fchk_folder_path}/{basename}_ESPiso.vmd"  

    
    with open(output_name, "w", encoding="utf-8") as f:  
        f.write(vmd_script)  
    
    print(f"VMD script saved to: {os.path.abspath(output_name)}")  



def render_esp_with_vmd(fchk_folder_path, filename: str) -> None:
    
    vmd_cmd = which('vmd')                         
    if vmd_cmd is None:                           
        raise FileNotFoundError(
            '未检测到 VMD，可执行文件 "vmd" 未加入系统 PATH。请先安装或配置 VMD。'
        )
    
    
    
    vmd_script = f"{fchk_folder_path}/{filename}_ESPiso.vmd"         
    output_img  = f"{fchk_folder_path}/{filename}_ESP.tga"           
    
    if not os.path.isfile(vmd_script):             
        raise FileNotFoundError(
            f"未找到 VMD 脚本文件：{vmd_script}"
        )
    
    
    
    tcl_commands = textwrap.dedent(f"""
        source "{vmd_script}"
        render TachyonInternal "{output_img}"
        quit
    """).strip()                                  
    
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.tcl', delete=False
    ) as tcl_file:                                
        tcl_file.write(tcl_commands)              
        temp_tcl_path = tcl_file.name             
    
    
    
    try:
        result = subprocess.run(
            [vmd_cmd, '-dispdev', 'text', '-e', temp_tcl_path],
            check=False,                          
            stdout=subprocess.PIPE,               
            stderr=subprocess.PIPE,               
            text=True                             
        )
    finally:
        os.remove(temp_tcl_path)                  
    
    
    if result.returncode != 0:                    
        
        err_msg = (
            f"VMD 渲染失败，退出码 {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )
        raise RuntimeError(err_msg)
    else:
        print(f"[✓] 渲染完成：{output_img}")       
