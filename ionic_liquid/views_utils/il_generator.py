





import numpy as np
from rdkit import Chem
from rdkit.Chem import Draw
from more_itertools import chunked
import matplotlib.pyplot as plt
from rdkit.Chem.Draw import rdMolDraw2D
from IPython.display import SVG
import networkx as nx
import pandas as pd
from rdkit.Chem.rdchem import RWMol
from rdkit.Chem import rdmolops
from rdkit.Chem.Draw import IPythonConsole
import seaborn as sns
import re
from rdkit.Chem import AddHs
from rdkit.Chem import AllChem
import os
from openbabel import openbabel, pybel
from rdkit.Chem.rdmolfiles import MolToSmiles
from rdkit.Chem import RemoveHs
import subprocess
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from openbabel import openbabel
from openpyxl import Workbook
import time
from openbabel import pybel
import shutil
import glob
from IPython.display import display
from rdkit.Chem import Draw
from openbabel import openbabel as ob
from matplotlib.ticker import MaxNLocator
import json
from itertools import combinations
from rdkit import DataStructs
import matplotlib.pyplot as plt
import itertools
from itertools import product
from rdkit.Contrib.SA_Score import sascorer
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.DataStructs.cDataStructs import TanimotoSimilarity
from rdkit.Chem import Draw
from IPython.display import display
import random
from rdkit.Chem import RWMol, Atom
from rdkit.Chem.rdchem import AtomValenceException, KekulizeException
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from matplotlib.ticker import MaxNLocator
from sklearn.random_projection import GaussianRandomProjection
from joblib import Parallel, delayed
from openpyxl import load_workbook
from sklearn.decomposition import PCA
from rdkit import RDLogger
import warnings
import operator
from pathlib import Path                    




from .generate_core_fragment import preprocess_core_fragment 
from .generate_new_cation_anion import generate_new_cation_anion 
from .generate_predict_new_IL import generate_predict_new_IL 






def out(name, output_dir) -> str:
    return str(Path(output_dir) / name)  




from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def generate_il_by_fragments(request):
  from django.conf import settings
  from django.http import JsonResponse
  import io

  
  if request.method != 'POST':
    return JsonResponse({'success': False, 'message': 'Only POST method is supported'}, status=405)

  
  OUTPUT_DIR = settings.MEDIA_ROOT

  try:
    
    if 'cation_file' not in request.FILES or 'anion_file' not in request.FILES:
      return JsonResponse({
        'success': False,
        'message': 'Please upload both cation and anion files',
        'required_format': {
          'cation_file': 'Cation_core_backbone.xlsx (must contain columns: Core_SMILES, Backbone_SMILES)',
          'anion_file': 'Anion_core_backbone.xlsx (must contain columns: Core_SMILES, Backbone_SMILES)'
        }
      }, status=400)

    cation_file = request.FILES['cation_file']
    anion_file = request.FILES['anion_file']

    
    cation_file_path = os.path.join(OUTPUT_DIR, 'Cation_core_backbone.xlsx')
    anion_file_path = os.path.join(OUTPUT_DIR, 'Anion_core_backbone.xlsx')

    
    with open(cation_file_path, 'wb+') as destination:
      for chunk in cation_file.chunks():
        destination.write(chunk)

    with open(anion_file_path, 'wb+') as destination:
      for chunk in anion_file.chunks():
        destination.write(chunk)

    
    df_cation_core_backbone = pd.read_excel(cation_file_path)
    df_anion_core_backbone = pd.read_excel(anion_file_path)

    
    required_cols = ['Core_SMILES', 'Backbone_SMILES']
    cation_missing = [col for col in required_cols if col not in df_cation_core_backbone.columns]
    anion_missing = [col for col in required_cols if col not in df_anion_core_backbone.columns]

    if cation_missing or anion_missing:
      error_msg = []
      if cation_missing:
        error_msg.append(f"Cation file missing columns: {', '.join(cation_missing)}")
      if anion_missing:
        error_msg.append(f"Anion file missing columns: {', '.join(anion_missing)}")

      return JsonResponse({
        'success': False,
        'message': '; '.join(error_msg),
        'required_format': {
          'columns': required_cols,
          'example': {
            'Core_SMILES': '[*]n1cc[n+](C)c1',
            'Backbone_SMILES': '[*]CCCC'
          }
        }
      }, status=400)

  except Exception as e:
    return JsonResponse({
      'success': False,
      'message': f'File processing failed: {str(e)}'
    }, status=500)
  try:
    
    preprocess_core_fragment(df_cation_core_backbone, df_anion_core_backbone, output_dir=OUTPUT_DIR) 

    generate_new_cation_anion(out("Cation_core.xlsx", OUTPUT_DIR),
                              out("Anion_core.xlsx", OUTPUT_DIR),
                              out("Cation_backbone.xlsx", OUTPUT_DIR),
                              out("Anion_backbone.xlsx", OUTPUT_DIR),
                              out('New_Cation.csv', OUTPUT_DIR),
                              out('New_Anion.csv', OUTPUT_DIR)
                            )




    
    generate_predict_new_IL(out("New_Cation.csv", OUTPUT_DIR),
                            out("New_Anion.csv", OUTPUT_DIR),
                            out("IL_output.csv", OUTPUT_DIR),
                            cation_limit=500, anion_limit=300, seed=1)

    
    
    download_url = "/ionic_liquid/download/IL_output.csv"
    return JsonResponse({
        'success': True,
        'download_url': download_url,
        'message': 'Ionic liquids generated successfully'
    })
  except Exception as e:
    import traceback
    return JsonResponse({
      'success': False,
      'message': f'Ionic liquid generation failed: {str(e)}',
      'traceback': traceback.format_exc()
    }, status=500)





