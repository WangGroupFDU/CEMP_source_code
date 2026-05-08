from django.contrib import admin


from django.contrib import admin

from .models import IL_properties, IL_smiles_rdkit, IL_smiles_psi4

admin.site.register(IL_properties)
admin.site.register(IL_smiles_rdkit)
admin.site.register(IL_smiles_psi4)