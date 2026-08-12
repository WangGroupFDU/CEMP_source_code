




set -euo pipefail

if [ -z "${CEMP_GAUSSIAN_SCRATCH_DIR:-}" ]; then
  echo "CEMP_GAUSSIAN_SCRATCH_DIR is not configured." >&2
  exit 2
fi

TARGET_DIR="${CEMP_GAUSSIAN_SCRATCH_DIR}"


if [ -d "${TARGET_DIR}" ]; then
  rm -rf "${TARGET_DIR}"
fi


mkdir -p "${TARGET_DIR}"
