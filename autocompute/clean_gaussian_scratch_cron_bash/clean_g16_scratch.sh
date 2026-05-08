




set -euo pipefail

TARGET_DIR="/root/Gaussian16_Linux_AVX2/tar/g16/scratch"


if [ -d "${TARGET_DIR}" ]; then
  rm -rf "${TARGET_DIR}"
fi


mkdir -p "${TARGET_DIR}"

