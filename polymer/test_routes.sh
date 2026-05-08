




echo "=========================================="
echo "Testing Polymer Analysis Routes"
echo "=========================================="
echo ""

BASE_URL="https://example.com/polymer"


GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_url() {
    local url=$1
    local description=$2

    echo -n "Testing: $description ... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
    fi
}

echo "1. Test Routes (Token Caching)"
echo "-----------------------------------"
test_url "$BASE_URL/test/polymer-prediction" "Test route - polymer prediction"
test_url "$BASE_URL/test/batch-prediction" "Test route - batch prediction"
test_url "$BASE_URL/test/polymer-generator" "Test route - polymer generator"
echo ""

echo "2. RDKit Files (Critical)"
echo "-----------------------------------"
test_url "$BASE_URL/RDKit_minimal.js" "RDKit JavaScript"
test_url "$BASE_URL/RDKit_minimal.wasm" "RDKit WebAssembly"
echo ""

echo "3. Template Files"
echo "-----------------------------------"
test_url "$BASE_URL/monomer_template.csv" "Monomer template CSV"
test_url "$BASE_URL/polymer_prediction_template.xlsx" "Polymer prediction template XLSX"
echo ""

echo "4. Assets (Sample Check)"
echo "-----------------------------------"

echo -e "${YELLOW}Note: Asset filenames contain hashes, checking pattern...${NC}"
echo "Run 'ls /home/jju/remote_project/polymer/dist/assets/' to get actual filenames"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. If all tests PASS, restart Django: sudo systemctl restart gunicorn"
echo "2. Open browser and check Console for RDKit initialization"
echo "3. Visit: $BASE_URL/test/polymer-prediction"
echo ""
