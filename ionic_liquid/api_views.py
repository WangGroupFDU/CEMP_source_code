
import json
from pathlib import Path
from django.conf import settings
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





def _resolve_model_paths():
    """
    功能目的：解析离子液体 SMILES 预测 API 所需的模型文件路径。
    输入参数：无，优先读取 CEMP_IL_MODEL_DIR 环境变量。
    返回值：包含 ECW、Tm 和 conductivity 三个模型路径的字典。
    关键流程：默认使用仓库内 ionic_liquid/static/model；若模型资产从
    GitHub Release/Zenodo 解压到其他目录，可通过 CEMP_IL_MODEL_DIR 指定。
    边界情况：模型文件缺失时抛出 FileNotFoundError，API 会返回明确错误信息。
    """
    default_model_dir = Path(settings.BASE_DIR) / "ionic_liquid" / "static" / "model"
    model_dir = Path(os.environ.get("CEMP_IL_MODEL_DIR", str(default_model_dir))).expanduser()
    model_paths = {
        "ecw": model_dir / "IL_ECW_xgb_model_fp.joblib",
        "tm": model_dir / "Tm_xgb_model_fp.joblib",
        "conductivity": model_dir / "conductivity_MLP_model_fp.pt",
    }
    missing_files = [str(path) for path in model_paths.values() if not path.is_file()]
    if missing_files:
        raise FileNotFoundError(
            "Missing ionic liquid model files. Download and extract the public model "
            f"assets, or set CEMP_IL_MODEL_DIR. Missing: {missing_files}"
        )
    return model_paths


@lru_cache(maxsize=1)
def _load_models_once():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_paths = _resolve_model_paths()


    mlp = MLP(input_size=2048, hidden_sizes=[256, 64], output_size=1).to(device)
    mlp.load_state_dict(torch.load(model_paths["conductivity"], map_location=device))
    mlp.eval()


    ecw_xgb = joblib.load(model_paths["ecw"])
    tm_xgb = joblib.load(model_paths["tm"])

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
