
import json  
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes  
from rest_framework.authentication import TokenAuthentication  
from rest_framework.permissions import IsAuthenticated  
from rest_framework.response import Response  
from rest_framework import status  
import numpy as np  
import joblib  
from functools import lru_cache  
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser  

from polymer.views import process_polymer_predict_view
from .api_service import *



def make_api_excel_upload_return_ID(legacy_view):

    
    @api_view(["POST"])
    @authentication_classes([TokenAuthentication])
    @permission_classes([IsAuthenticated])
    @parser_classes([MultiPartParser, FormParser])
    def api_view_func(request):
        
        if "excel_file" not in request.FILES:
            return Response(
                {"error": "Missing file field: excel_file"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        legacy_response = legacy_view(request)

        
        
        try:
            data = json.loads(legacy_response.content.decode("utf-8"))
            return Response(data, status=legacy_response.status_code)
        except Exception:
            return Response(
                {"error": "Legacy view did not return valid JSON"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return api_view_func


process_polymer_predict_view_api = make_api_excel_upload_return_ID(process_polymer_predict_view)







MODEL_BASE_DIR = "/path/to/example/polymer/static/model"  

MODEL_TO_PREDICT_PROPERTY_LIST = [  
    "Tg",
    "Dielectric_Constant_Total",
    "Youngs_Modulus",
    "Tm",
    "Tensile_Strength",
]

PROPERTY_UNIT_MAP = {  
    "Tg": "K",
    "Dielectric_Constant_Total": "",  
    "Youngs_Modulus": "MPa",
    "Tm": "K",
    "Tensile_Strength": "MPa",
}


def _limit_model_threads(model, prop_name: str) -> None:
    try:
        
        if hasattr(model, "set_params"):
            try:
                model.set_params(n_jobs=1)  
            except Exception:
                pass  

        
        booster = getattr(model, "get_booster", lambda: None)()  
        if booster is not None and hasattr(booster, "set_param"):
            try:
                booster.set_param({"nthread": 1})  
            except Exception:
                pass  
    except Exception:
        
        return


@lru_cache(maxsize=1)
def _load_models_once():
    model_dict = {}  
    for prop in MODEL_TO_PREDICT_PROPERTY_LIST:  
        model_path = f"{MODEL_BASE_DIR}/{prop}_xgb_model.joblib"  
        model = joblib.load(model_path)  
        _limit_model_threads(model, prop_name=prop)  
        model_dict[prop] = model  
    return model_dict  


@api_view(["POST"])  
@authentication_classes([TokenAuthentication])  
@permission_classes([IsAuthenticated])  
@parser_classes([JSONParser, FormParser, MultiPartParser])  
def polymer_predict_properties_from_psmiles(request):

    
    psmiles = request.data.get("psmiles", "")  
    if not isinstance(psmiles, str):  
        return Response(
            {"error": "Invalid field type: psmiles must be a string"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    psmiles = psmiles.strip()  
    if not psmiles:  
        return Response(
            {"error": "Missing field: psmiles"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    
    try:
        psmiles_with_h = add_hydrogens_to_smiles(psmiles)  
        caped_smiles = cap_smiles(psmiles_with_h)  
    except Exception as e:
        return Response(
            {"error": f"PSMILES preprocessing failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    
    try:
        morgan_fp_tensor = smiles_to_morgan_fingerprint(  
            caped_smiles,
            radius=2,
            n_bits=2048,
        )
        
        if hasattr(morgan_fp_tensor, "detach"):
            X = morgan_fp_tensor.detach().cpu().numpy().reshape(1, -1)  
        else:
            X = np.asarray(morgan_fp_tensor).reshape(1, -1)  
    except Exception as e:
        return Response(
            {"error": f"Fingerprint generation failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    
    try:
        model_dict = _load_models_once()  
    except Exception as e:
        return Response(
            {"error": f"Model loading failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    
    predictions = {}  
    try:
        for prop, model in model_dict.items():  
            y_pred = model.predict(X)  
            value = float(np.asarray(y_pred).reshape(-1)[0])  
            predictions[prop] = {  
                "value": value,
                "unit": PROPERTY_UNIT_MAP.get(prop, ""),
            }
    except Exception as e:
        return Response(
            {"error": f"Prediction failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    
    return Response(
        {
            "psmiles": psmiles,  
            "processed_smiles": caped_smiles,  
            "predictions": predictions,  
        },
        status=status.HTTP_200_OK,
    )