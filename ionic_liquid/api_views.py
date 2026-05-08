
import json  
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes  
from rest_framework.authentication import TokenAuthentication  
from rest_framework.permissions import IsAuthenticated  
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  
from rest_framework.response import Response  
from rest_framework import status  
from functools import lru_cache  

from ionic_liquid.views import process_excel_ILpredict_XGBoost_view
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


process_excel_ILpredict_XGBoost_view_api = make_api_excel_upload_return_ID(process_excel_ILpredict_XGBoost_view)





IL_ECW_XGB_MODEL_PATH = "/path/to/example/ionic_liquid/static/model/IL_ECW_xgb_model_fp.joblib"
TM_XGB_MODEL_PATH = "/path/to/example/ionic_liquid/static/model/Tm_xgb_model_fp.joblib"
COND_MLP_MODEL_PATH = "/path/to/example/ionic_liquid/static/model/conductivity_MLP_model_fp.pt"
@lru_cache(maxsize=1)
def _load_models_once():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  

    
    mlp = MLP(input_size=2048, hidden_sizes=[256, 64], output_size=1).to(device)  
    mlp.load_state_dict(torch.load(COND_MLP_MODEL_PATH, map_location=device))  
    mlp.eval()  

    
    ecw_xgb = joblib.load(IL_ECW_XGB_MODEL_PATH)  
    tm_xgb = joblib.load(TM_XGB_MODEL_PATH)  

    return device, ecw_xgb, tm_xgb, mlp  


@api_view(["POST"])  
@authentication_classes([TokenAuthentication])  
@permission_classes([IsAuthenticated])  
@parser_classes([JSONParser, FormParser, MultiPartParser])  
def ionic_liquid_predict_from_smiles_api(request):
    
    smiles = request.data.get("smiles", "")  
    smiles = smiles.strip() if isinstance(smiles, str) else ""  
    if not smiles:  
        return Response({"error": "Missing field: smiles"}, status=status.HTTP_400_BAD_REQUEST)

    
    try:
        fp = create_morgan_fp_tensor(smiles)  
    except Exception as e:
        return Response({"error": f"Fingerprint generation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    
    try:
        device, ecw_xgb, tm_xgb, cond_mlp = _load_models_once()  
    except Exception as e:
        return Response({"error": f"Model loading failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    try:
        
        if isinstance(fp, torch.Tensor):  
            fp_np = fp.detach().cpu().numpy()  
        else:
            fp_np = np.asarray(fp)  

        if fp_np.ndim == 1:  
            fp_np = fp_np.reshape(1, -1)

        y_ecw = float(np.asarray(ecw_xgb.predict(fp_np)).reshape(-1)[0])  
        y_tm = float(np.asarray(tm_xgb.predict(fp_np)).reshape(-1)[0])  
    except Exception as e:
        return Response({"error": f"XGB prediction failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    try:
        
        fp_t = torch.tensor(fp_np, dtype=torch.float32, device=device)  

        
        data = Data(smiles=smiles, morgan_fp=fp_t)  
        data = data.to(device)  

        with torch.no_grad():  
            out = cond_mlp(data)  

        y_cond = float(out.detach().cpu().numpy().reshape(-1)[0])  
    except Exception as e:
        return Response({"error": f"MLP prediction failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    return Response(
        {"smiles": smiles, "ECW": y_ecw, "Tm": y_tm, "conductivity": y_cond},
        status=status.HTTP_200_OK,
    )