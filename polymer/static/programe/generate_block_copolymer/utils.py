

import re
import pandas as pd
from typing import Iterable
from typing import List, Tuple, Set
from rdkit import Chem                           
from rdkit.Chem import AllChem                   







RULE_SMIRKS: List[Tuple[str, str]] = [
    
    
    ("diacid_like",  
     "[O&H1:1][C:2](=[O:3])[#6:4]>>[*][C:2](=[O:3])[#6:4]"),

    
    
    ("primary_amine",
     "[N;H2;!$([N]-C(=O));!$([N]-S(=O)(=O)):1][!#1:2]>>[N:1]([*:100])[!#1:2]"),

    
    ("alcohol_or_phenol_OH_to_Ostar",
    "[O;!H0;X2:1]-[$([CX4;!$(C=O):2]),$([c:2])]>>[*][O:1]-[#6:2]"),

    
    ("diacyl_chloride_like",
     "[Cl:1][C:2](=[O:3])[#6:4]>>[*][C:2](=[O:3])[#6:4]"),

    
    
    ("isocyanate_acyl_like",
    "[N:1]=[C:2]=[O:3]>>[*][C:2](=[O:3])[N:1]"),

    
    ("anhydride_to_diacylStars",
     "[*:1][#6X3;!a](=O)[O;X2H0][#6X3;!a](=O)[*:2]>>"
     "[*:1][#6X3](=O)[*]-[*][#6X3](=O)[*:2]"),

    
    ("thiol_to_Sstar",
     "[*:1][S;X2;H1]>>[*:1]-[S][*]"),

    
    ("aldehyde_to_acylStar",
     "[*:1][#6X3H1;!a](=O)>>[*:1][#6X3](=O)[*]"),

     
    ("alkene_HX_to_star_int_dir1",
    "[*:1][#6X3H1;!a:2]=[#6X3H1;!a:3][*:4]>>[*:1][#6X4H2:2]-[#6X4H1:3]([*])[*:4]"),

    
    
    ("diene_1_4_open",
    "[#6X3;!a:1]=[#6X3;!a:2]-[#6X3;!a:3]=[#6X3;!a:4]>>[*]-[#6:1]-[#6:2]=[#6:3]-[#6:4]-[*]"),

    
    ("alkene_open",
        "[#6X3;!a;!$([#6X3]-[#6X3]=[#6X3]):1]=[#6X3;!a;!$([#6X3]-[#6X3]=[#6X3]):2]>>[*][#6:1]-[#6:2][*]"), 

    
    ("alkyne_to_alkene",
        "[C:1]#[C:2]>>[*:100][C:1]=[C:2][*:101]"),

    
    ("dibromo_thiophene",
        "[!#1:5]c1c([Br:1])[s:3]c([Br:2])c1>>[!#1:5]c1c([*:100])[s:3]c([*:101])c1"),
    ]


RULES = []
for name, smirks in RULE_SMIRKS:
    rxn = AllChem.ReactionFromSmarts(smirks)   
    rxn.Initialize()                            
    RULES.append((name, rxn))                   





from rdkit import Chem
from rdkit.Chem import AllChem


def strip_dummy_isotopes(mol):
    for atom in mol.GetAtoms():                  
        if atom.GetAtomicNum() == 0:             
            atom.SetIsotope(0)                   
    return mol                                   

def open_ring_by_bond(mol, match_smarts, star_left=100, star_right=101):
    q = Chem.MolFromSmarts(match_smarts)
    hits = mol.GetSubstructMatches(q)
    if not hits:
        return None  

    
    aC = hits[0][1]  
    aX = hits[0][2]  
    bond = mol.GetBondBetweenAtoms(aC, aX)
    if bond is None:
        return None

    
    
    if bond.GetBeginAtomIdx() == aX:
        labels = [(star_left, star_right)]
    else:
        labels = [(star_right, star_left)]

    
    opened = Chem.FragmentOnBonds(mol, [bond.GetIdx()], addDummies=True, dummyLabels=labels)
    Chem.SanitizeMol(opened)  
    opened = strip_dummy_isotopes(opened) 
    return opened

def _sanitize_soft(m: Chem.Mol) -> Chem.Mol:
    try:
        Chem.SanitizeMol(m, catchErrors=True)
    except Exception:
        pass
    return m

def _canon_smiles(m: Chem.Mol) -> str:
    try:
        return Chem.MolToSmiles(m)
    except Exception:
        return ""
def generate_starred_bfs(smiles: str, max_steps: int = 2,
                         return_intermediate: bool = False) -> str:

    
    
    
    
    
    ROP_PATTERNS = [
        ("lactone",           "[O:1]=[C;R:2]-;@[O;R:3]"),                         
        ("lactam",            "[O:1]=[C;R:2]-;@[N;R:3]"),                         
        ("cyclic_carbonate",  "[O:1]=[C;R:2](@[O;R:3])@[O;R:5]"),                 
        ("epoxide",           "[C;R:1]-;@[C;R:2]-;@[O;R:3]"),                     
        ("episulfide",        "[C;R:1]-;@[C;R:2]-;@[S;R:3]"),                     
    ]

    m0 = Chem.MolFromSmiles(smiles)               
    if m0 is None:
        raise ValueError("无法解析输入SMILES。")
    s0 = _canon_smiles(_sanitize_soft(m0))        
    m0 = Chem.MolFromSmiles(s0)                   
    _sanitize_soft(m0)

    
    rop_outs: Set[str] = set()
    for _, patt in ROP_PATTERNS:
        opened = open_ring_by_bond(m0, patt, star_left=100, star_right=101)
        if opened is None:
            continue
        _sanitize_soft(opened)
        s_open = _canon_smiles(opened)
        if s_open and "*" in s_open:
            rop_outs.add(s_open)

    if rop_outs:
        
        return next(iter(sorted(rop_outs)))

    
    
    CHAIN_RULE_NAMES = {"alkene_open", "alkyne_to_alkene", "diene_1_4_open"}

    
    EXCLUDE_ROP_RULES = {"lactone_open", "lactam_open", "epoxide_open",
                         "cyclic_carbonate_open", "episulfide_open"}

    layers: List[Set[str]] = [set([s0])]          
    frontier: Set[str] = set([s0])                

    for _ in range(max_steps):                    
        layer_prods: Set[str] = set()             
        next_frontier: Set[str] = set()           

        for s in frontier:
            m = Chem.MolFromSmiles(s)
            if m is None:
                continue
            _sanitize_soft(m)

            for name, rxn in RULES:
                
                if name in EXCLUDE_ROP_RULES:
                    continue

                try:
                    prods = rxn.RunReactants((m,))
                except Exception:
                    prods = ()

                for tup in prods:
                    if not tup:
                        continue
                    pm = _sanitize_soft(tup[0])
                    ps = _canon_smiles(pm)
                    if not ps or ps == s:
                        continue

                    layer_prods.add(ps)           
                    
                    if name not in CHAIN_RULE_NAMES:
                        next_frontier.add(ps)

        if not layer_prods:
            break

        layers.append(layer_prods)
        frontier = next_frontier
        if not frontier:                          
            break

    
    start_idx = 1 if return_intermediate else len(layers) - 1
    outs: Set[str] = set()
    for i in range(start_idx, len(layers)):
        for s in layers[i]:
            if "*" in s:
                outs.add(s)

    return next(iter(sorted(outs))) if outs else ""

def clean_polymer_df(df: pd.DataFrame) -> pd.DataFrame:
    
    required = {'Name', 'SMILES', 'repeating unit'}
    missing = required.difference(df.columns)
    if missing:
        raise KeyError(f"缺少必需列：{sorted(missing)}")
    out = df.copy()

    
    
    def _is_nonempty_str(x) -> bool:
        return isinstance(x, str) and (x.strip() != "")

    mask_valid_smiles = out['SMILES'].map(_is_nonempty_str)
    
    out = out[mask_valid_smiles].copy()

    
    if out.empty:
        return out

    
    
    name_empty_mask = ~out['Name'].map(lambda x: isinstance(x, str) and (x.strip() != ""))
    if name_empty_mask.any():
        empty_idx: Iterable = out.index[name_empty_mask]
        for i, idx in enumerate(empty_idx):
            out.at[idx, 'Name'] = f"test_{i}"

    
    def _whitespace_to_underscore(x):
        
        if isinstance(x, str):
            return re.sub(r"\s+", "_", x.strip())
        return x

    out['Name'] = out['Name'].map(_whitespace_to_underscore)
    if 'copolymer_name' in out.columns:
        out['copolymer_name'] = out['copolymer_name'].map(_whitespace_to_underscore)

    
    if 'Number of blocks' in out.columns:
        
        nob = pd.to_numeric(out['Number of blocks'], errors='coerce')
        nob = nob.fillna(1)
        
        out['Number of blocks'] = nob.astype('Int64')

    
    ru = pd.to_numeric(out['repeating unit'], errors='coerce')
    ru = ru.fillna(1)
    ru = ru.where(ru != 0, 1)
    out['repeating unit'] = ru.astype('Int64')

    
    def _ensure_two_anchors(smiles: str) -> str:
        
        try:
            star_cnt = smiles.count('*') if isinstance(smiles, str) else 0
            if star_cnt == 2:
                return smiles
            
            new_smiles = generate_starred_bfs(smiles)  
            return new_smiles if isinstance(new_smiles, str) and new_smiles.strip() else smiles
        except Exception:
            return smiles

    out['SMILES'] = out['SMILES'].map(_ensure_two_anchors)

    
    return out