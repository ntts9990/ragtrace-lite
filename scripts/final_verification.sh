#!/bin/bash
# Final verification script for RAGTrace Lite

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== RAGTrace Lite Final Verification ===${NC}"
echo "Starting comprehensive verification process..."

# Track results
PASSED=0
FAILED=0

# Function to check a test
check_test() {
    local test_name=$1
    local command=$2
    
    echo -n "Checking $test_name... "
    if eval $command > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAILED${NC}"
        ((FAILED++))
    fi
}

# 1. Check Python version
echo -e "\n${YELLOW}1. Environment Checks${NC}"
check_test "Python version" "python --version | grep -E '3\.(8|9|10|11|12)'"

# 2. Check required files
echo -e "\n${YELLOW}2. Required Files${NC}"
check_test "pyproject.toml" "[ -f pyproject.toml ]"
check_test "README.md" "[ -f README.md ]"
check_test "LICENSE" "[ -f LICENSE ]"
check_test ".env.example" "[ -f .env.example ]"
check_test "config.yaml" "[ -f config.yaml ]"

# 3. Check package structure
echo -e "\n${YELLOW}3. Package Structure${NC}"
check_test "Package directory" "[ -d src/ragtrace_lite ]"
check_test "__init__.py" "[ -f src/ragtrace_lite/__init__.py ]"
check_test "CLI module" "[ -f src/ragtrace_lite/cli.py ]"
check_test "Tests directory" "[ -d tests ]"

# 4. Check dependencies
echo -e "\n${YELLOW}4. Dependencies${NC}"
check_test "pip install" "pip install -e . > /dev/null 2>&1"

# 5. Import test
echo -e "\n${YELLOW}5. Import Tests${NC}"
check_test "Import package" "python -c 'import ragtrace_lite'"
check_test "Import version" "python -c 'from ragtrace_lite import __version__'"

# 6. CLI tests
echo -e "\n${YELLOW}6. CLI Tests${NC}"
check_test "CLI help" "python -m ragtrace_lite.cli --help"
check_test "CLI version" "python -m ragtrace_lite.cli version"

# 7. Test suite
echo -e "\n${YELLOW}7. Test Suite${NC}"
if command -v pytest &> /dev/null; then
    check_test "Unit tests" "pytest tests/unit -v"
else
    echo -e "${YELLOW}pytest not installed, skipping tests${NC}"
fi

# 8. Code quality
echo -e "\n${YELLOW}8. Code Quality${NC}"
if command -v black &> /dev/null; then
    check_test "Black formatting" "black --check src tests"
else
    echo -e "${YELLOW}black not installed, skipping${NC}"
fi

if command -v flake8 &> /dev/null; then
    check_test "Flake8 linting" "flake8 src tests --max-line-length=100"
else
    echo -e "${YELLOW}flake8 not installed, skipping${NC}"
fi

# 9. Documentation
echo -e "\n${YELLOW}9. Documentation${NC}"
check_test "Installation guide" "[ -f INSTALLATION.md ]"
check_test "Migration guide" "[ -f MIGRATION_GUIDE.md ]"
check_test "Contributing guide" "[ -f CONTRIBUTING.md ]"
check_test "Security policy" "[ -f SECURITY.md ]"

# 10. Docker
echo -e "\n${YELLOW}10. Docker${NC}"
check_test "Dockerfile" "[ -f Dockerfile ]"
check_test "docker-compose.yml" "[ -f docker-compose.yml ]"

if command -v docker &> /dev/null; then
    check_test "Docker build" "docker build -t ragtrace-lite:test ."
else
    echo -e "${YELLOW}Docker not installed, skipping build test${NC}"
fi

# Summary
echo -e "\n${GREEN}=== Verification Summary ===${NC}"
echo -e "Total tests: $((PASSED + FAILED))"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All verification checks passed!${NC}"
    echo "RAGTrace Lite is ready for deployment."
    exit 0
else
    echo -e "\n${RED}❌ Some verification checks failed.${NC}"
    echo "Please fix the issues before deployment."
    exit 1
fi