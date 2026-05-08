import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

from django.conf import settings
from PIL import Image


logger = logging.getLogger("django")


MD_TASK_TYPES = {"MDCoumpute", "MDCoumpute_ORCA", "MDCompute", "MDCompute_ORCA"}
MD_PREVIEW_MANIFEST_VERSION = 1

MD_PREVIEW_SPECS = [
    {
        "key": "rdf_atom",
        "label": "RDF and CN for atom",
        "group": "Coordination",
        "pattern": r".+_atomcharge_rdf\+cn\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "rdf_molecule",
        "label": "RDF and CN for molecule",
        "group": "Coordination",
        "pattern": r"^(?!.*_atomcharge_rdf\+cn\.).+_rdf\+cn\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "coordination_environment",
        "label": "Coordination environment",
        "group": "Coordination",
        "pattern": r"animation_.+\.(?:gif|png)$",
    },
    {
        "key": "coordination_number_variation",
        "label": "Coordination number variation",
        "group": "Coordination",
        "pattern": r".+_selection_size\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "snapshot",
        "label": "Snapshot",
        "group": "Structure",
        "pattern": r"snapshot\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "msd",
        "label": "MSD",
        "group": "Transport",
        "pattern": r"MSD\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "pmf",
        "label": "PMF",
        "group": "Transport",
        "pattern": r"PMF\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "structure_factor",
        "label": "Structure factor",
        "group": "Structure",
        "pattern": r"structure_factor\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "lifetime",
        "label": "Lifetime",
        "group": "Transport",
        "pattern": r".+_lifetime\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "dielectric_spectrum",
        "label": "Dielectric spectrum",
        "group": "Transport",
        "pattern": r"dielectric_constant_spectrum\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "strain_stress_plot",
        "label": "Strain-stress plot",
        "group": "Mechanical",
        "pattern": r"System_strain_stress_plot\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "polymer_gyration_plot",
        "label": "Polymer gyration plot",
        "group": "Mechanical",
        "pattern": r"after_stretch_polymer_gyrate_plot\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "end_to_end_distance_plot",
        "label": "End-to-end distance plot",
        "group": "Mechanical",
        "pattern": r"after_stretch_polymer_endtoend_distance_plot\.(?:tif|tiff|png|gif)$",
    },
    {
        "key": "coordination_polar_map",
        "label": "Coordination polar map",
        "group": "Coordination",
        "pattern": r"coordination_polar\.(?:png|gif|tif|tiff)$",
    },
]


def is_md_task_type(task_type: Optional[str]) -> bool:

    if not task_type:
        return False
    return task_type in MD_TASK_TYPES


def build_md_preview_manifest(download_dir: str, table_data_url: Optional[str] = None, force_rebuild: bool = False) -> List[Dict[str, str]]:

    download_path = Path(download_dir)
    if not download_path.exists() or not download_path.is_dir():
        return []

    preview_dir = download_path / "query_previews"
    manifest_path = preview_dir / "manifest.json"

    if not force_rebuild:
        cached = _load_manifest_if_usable(manifest_path)
        if cached is not None:
            return cached

    preview_dir.mkdir(parents=True, exist_ok=True)
    files = [path for path in download_path.iterdir() if path.is_file()]
    preview_items: List[Dict[str, str]] = []

    for spec in MD_PREVIEW_SPECS:
        matched = _find_best_match(files, spec["pattern"])
        if matched is None:
            continue

        preview_url = _resolve_preview_url(
            source_path=matched,
            preview_dir=preview_dir,
        )
        if not preview_url:
            continue

        preview_items.append(
            {
                "key": spec["key"],
                "label": spec["label"],
                "url": preview_url,
                "source_filename": matched.name,
                "group": spec["group"],
            }
        )

    manifest_payload = {
        "version": MD_PREVIEW_MANIFEST_VERSION,
        "items": preview_items,
    }
    manifest_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return preview_items


def build_legacy_figure_dict(preview_items: List[Dict[str, str]]) -> Dict[str, str]:

    return {item["label"]: item["url"] for item in preview_items}


def _load_manifest_if_usable(manifest_path: Path) -> Optional[List[Dict[str, str]]]:

    if not manifest_path.exists():
        return None

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if payload.get("version") != MD_PREVIEW_MANIFEST_VERSION:
        return None

    items = payload.get("items", [])
    if not isinstance(items, list):
        return None

    for item in items:
        if not isinstance(item, dict):
            return None
        preview_url = item.get("url")
        preview_path = _url_to_media_path(preview_url)
        if preview_path is None or not preview_path.exists():
            return None

    return items


def _find_best_match(files: List[Path], pattern: str) -> Optional[Path]:

    regex = re.compile(pattern, re.IGNORECASE)
    matched = [path for path in files if regex.match(path.name)]
    if not matched:
        return None

    ext_priority = {
        ".gif": 0,
        ".png": 1,
        ".jpg": 2,
        ".jpeg": 3,
        ".webp": 4,
        ".tif": 5,
        ".tiff": 5,
    }
    matched.sort(key=lambda path: (ext_priority.get(path.suffix.lower(), 9), path.name.lower()))
    return matched[0]


def _resolve_preview_url(source_path: Path, preview_dir: Path) -> Optional[str]:

    suffix = source_path.suffix.lower()
    try:
        if suffix in {".tif", ".tiff"}:
            preview_path = preview_dir / f"{source_path.stem}.png"
            if (not preview_path.exists()) or (preview_path.stat().st_mtime < source_path.stat().st_mtime):
                with Image.open(source_path) as image:
                    if getattr(image, "n_frames", 1) > 1:
                        image.seek(0)
                    if image.mode not in {"RGB", "RGBA"}:
                        image = image.convert("RGB")
                    image.save(preview_path, format="PNG")
            return _media_path_to_url(preview_path)

        if suffix in {".png", ".gif", ".jpg", ".jpeg", ".webp"}:
            return _media_path_to_url(source_path)
    except Exception as exc:
        logger.warning("Failed to prepare MD preview for %s: %s", source_path, exc)
        return None

    return None


def _media_path_to_url(path: Path) -> str:

    media_root = Path(settings.MEDIA_ROOT).resolve()
    relative_path = path.resolve().relative_to(media_root)
    return f"{settings.MEDIA_URL.rstrip('/')}/{relative_path.as_posix()}"


def _url_to_media_path(url: Optional[str]) -> Optional[Path]:

    if not url or not isinstance(url, str):
        return None

    media_prefix = settings.MEDIA_URL.rstrip("/") + "/"
    if not url.startswith(media_prefix):
        return None

    relative_path = url[len(media_prefix):]
    return Path(settings.MEDIA_ROOT) / relative_path
