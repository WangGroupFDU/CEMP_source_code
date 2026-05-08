
from pymatgen.io.cif import CifParser
import os
import math
import random
from copy import deepcopy
import numpy as np
import pickle
import torch
from torch_geometric.data import Data, Dataset, DataLoader
from crystals.DefaultElement import DEFAULT_ELEMENTS      
from pymatgen.optimization.neighbors import find_points_in_spheres
from pymatgen.core import Structure
from pymatgen.core.operations import SymmOp

def cif_to_structure(cif_file):
    try:
        parser = CifParser(cif_file)
        
        
        structures = parser.parse_structures(primitive=True)
        
        
        if len(structures) > 0:
            return structures[0]
        else:
            print("未能解析出任何结构信息。")
            return None
    except Exception as e:
        
        print(f"解析CIF文件时发生错误: {e}")
        return None
    
def gaussian_expansion(distances, initial=0.0, final=5.0, num_centers=100, width=0.5):
    centers = torch.linspace(initial, final, num_centers).to(distances.device)
    if width is None:
        width = 1.0 / torch.diff(centers).mean()  
    
    diff = distances[:, None] - centers[None, :]
    
    expanded_distances = torch.exp(-width * (diff ** 2))
    return expanded_distances

def structure_to_graph(structure, cutoff=5.0):
    
    element_types = DEFAULT_ELEMENTS
    
    
    numerical_tol = 1.0e-8
    
    
    pbc = np.array([1, 1, 1], dtype=int)
    
    
    lattice_matrix = structure.lattice.matrix
    cart_coords = structure.cart_coords
    
    
    
    
    
    
    src_id, dst_id, images, bond_dist = find_points_in_spheres(
        cart_coords, cart_coords, r=cutoff, pbc=pbc, lattice=lattice_matrix, tol=numerical_tol
    ) 
    
    
    exclude_self = (src_id != dst_id) | (bond_dist > numerical_tol)
    src_id = src_id[exclude_self]
    dst_id = dst_id[exclude_self]
    images = images[exclude_self]
    bond_dist = bond_dist[exclude_self]
    
    
    edge_index = torch.tensor([src_id, dst_id], dtype=torch.long)
    
    
    
    pbc_offset = torch.tensor(images, dtype=torch.float)
    
    
    
    
    
    
    node_type = np.array([
        element_types.index(list(site.species.keys())[0].symbol)
        for site in structure
    ])
    node_type = torch.tensor(node_type, dtype=torch.long)
    
    
    frac_coords = torch.tensor(structure.frac_coords, dtype=torch.float)
    
    
    pos = torch.tensor(structure.cart_coords, dtype=torch.float)
    
    
    
    
    
    
    
    data = Data(edge_index=edge_index, pos=pos, x=node_type, frac_coords=frac_coords, pbc_offset=pbc_offset)
    
    
    
    node_pos = data.pos
    edge_index = data.edge_index
    src, dst = edge_index[0], edge_index[1]
    
    
    vector = node_pos[dst] - node_pos[src] + data.pbc_offset
    
    
    distances = vector.norm(dim=1)
    
    
    within_cutoff_after_pbc = distances <= cutoff
    
    
    edge_index = edge_index[:, within_cutoff_after_pbc]
    pbc_offset = pbc_offset[within_cutoff_after_pbc]
    distances = distances[within_cutoff_after_pbc]
    
    
    data.edge_index = edge_index
    data.pbc_offset = pbc_offset
    
    data.edge_attr = distances
    
    
    edge_attr = gaussian_expansion(distances) 
    data.edge_attr = edge_attr
    
    
    return data
