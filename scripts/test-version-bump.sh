#!/bin/bash

# Test script for bump-chart-version.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Test directory
TEST_DIR="/tmp/chart-version-test"
ORIGINAL_DIR=$(pwd)

# Function to print test results
print_result() {
    local test_name="$1"
    local result="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
    fi
}

# Setup test environment
setup_test_env() {
    echo -e "${YELLOW}Setting up test environment...${NC}"
    
    # Clean up any existing test directory
    rm -rf "$TEST_DIR"
    mkdir -p "$TEST_DIR/chart/kronic"
    
    # Copy the script to test directory
    cp "$ORIGINAL_DIR/scripts/bump-chart-version.sh" "$TEST_DIR/"
    chmod +x "$TEST_DIR/bump-chart-version.sh"
    
    # Create a test Chart.yaml
    cat > "$TEST_DIR/chart/kronic/Chart.yaml" << EOF
apiVersion: v2
name: kronic
description: Test chart
version: 1.0.0
appVersion: "v1.0.0"
EOF

    # Initialize git repo for auto-detection tests
    cd "$TEST_DIR"
    git init --quiet
    git config user.email "test@example.com"
    git config user.name "Test User"
    git add .
    git commit --quiet -m "Initial commit"
}

# Test version extraction
test_version_extraction() {
    cd "$TEST_DIR"
    
    local current_version=$(grep "^version:" chart/kronic/Chart.yaml | awk '{print $2}')
    
    if [ "$current_version" = "1.0.0" ]; then
        print_result "Version extraction" "PASS"
    else
        print_result "Version extraction (got: $current_version)" "FAIL"
    fi
}

# Test patch version bump
test_patch_bump() {
    cd "$TEST_DIR"
    
    ./bump-chart-version.sh patch > /dev/null 2>&1
    local new_version=$(grep "^version:" chart/kronic/Chart.yaml | awk '{print $2}')
    
    if [ "$new_version" = "1.0.1" ]; then
        print_result "Patch version bump (1.0.0 -> 1.0.1)" "PASS"
    else
        print_result "Patch version bump (got: $new_version)" "FAIL"
    fi
}

# Test minor version bump
test_minor_bump() {
    cd "$TEST_DIR"
    
    # Reset to 1.0.0
    sed -i 's/^version:.*/version: 1.0.0/' chart/kronic/Chart.yaml
    
    ./bump-chart-version.sh minor > /dev/null 2>&1
    local new_version=$(grep "^version:" chart/kronic/Chart.yaml | awk '{print $2}')
    
    if [ "$new_version" = "1.1.0" ]; then
        print_result "Minor version bump (1.0.0 -> 1.1.0)" "PASS"
    else
        print_result "Minor version bump (got: $new_version)" "FAIL"
    fi
}

# Test major version bump
test_major_bump() {
    cd "$TEST_DIR"
    
    # Reset to 1.0.0
    sed -i 's/^version:.*/version: 1.0.0/' chart/kronic/Chart.yaml
    
    ./bump-chart-version.sh major > /dev/null 2>&1
    local new_version=$(grep "^version:" chart/kronic/Chart.yaml | awk '{print $2}')
    
    if [ "$new_version" = "2.0.0" ]; then
        print_result "Major version bump (1.0.0 -> 2.0.0)" "PASS"
    else
        print_result "Major version bump (got: $new_version)" "FAIL"
    fi
}

# Test invalid argument handling
test_invalid_args() {
    cd "$TEST_DIR"
    
    if ./bump-chart-version.sh invalid > /dev/null 2>&1; then
        print_result "Invalid argument handling" "FAIL"
    else
        print_result "Invalid argument handling" "PASS"
    fi
}

# Test missing Chart.yaml
test_missing_chart() {
    cd "$TEST_DIR"
    
    # Temporarily move Chart.yaml
    mv chart/kronic/Chart.yaml chart/kronic/Chart.yaml.bak
    
    if ./bump-chart-version.sh patch > /dev/null 2>&1; then
        print_result "Missing Chart.yaml handling" "FAIL"
    else
        print_result "Missing Chart.yaml handling" "PASS"
    fi
    
    # Restore Chart.yaml
    mv chart/kronic/Chart.yaml.bak chart/kronic/Chart.yaml
}

# Test auto-detection with patch commits
test_auto_detection_patch() {
    cd "$TEST_DIR"
    
    # Reset version
    sed -i 's/^version:.*/version: 1.0.0/' chart/kronic/Chart.yaml
    
    # Create a commit that should trigger patch
    echo "# Test change" >> chart/kronic/Chart.yaml
    git add chart/kronic/Chart.yaml
    git commit --quiet -m "fix: minor bug fix"
    
    # Reset chart file
    sed -i '/# Test change/d' chart/kronic/Chart.yaml
    
    ./bump-chart-version.sh auto > /dev/null 2>&1
    local new_version=$(grep "^version:" chart/kronic/Chart.yaml | awk '{print $2}')
    
    # Auto should default to patch
    if [ "$new_version" = "1.0.1" ]; then
        print_result "Auto-detection (patch default)" "PASS"
    else
        print_result "Auto-detection (got: $new_version)" "FAIL"
    fi
}

# Test complex version numbers
test_complex_versions() {
    cd "$TEST_DIR"
    
    # Test with version 10.20.30
    sed -i 's/^version:.*/version: 10.20.30/' chart/kronic/Chart.yaml
    
    ./bump-chart-version.sh patch > /dev/null 2>&1
    local new_version=$(grep "^version:" chart/kronic/Chart.yaml | awk '{print $2}')
    
    if [ "$new_version" = "10.20.31" ]; then
        print_result "Complex version numbers (10.20.30 -> 10.20.31)" "PASS"
    else
        print_result "Complex version numbers (got: $new_version)" "FAIL"
    fi
}

# Cleanup function
cleanup() {
    cd "$ORIGINAL_DIR"
    rm -rf "$TEST_DIR"
}

# Main test execution
main() {
    echo -e "${YELLOW}Running Helm Chart Version Bumping Tests${NC}"
    echo "=============================================="
    
    # Setup
    setup_test_env
    
    # Run tests
    test_version_extraction
    test_patch_bump
    test_minor_bump
    test_major_bump
    test_invalid_args
    test_missing_chart
    test_auto_detection_patch
    test_complex_versions
    
    # Cleanup
    cleanup
    
    # Results
    echo "=============================================="
    echo -e "${YELLOW}Test Results:${NC}"
    echo "Tests run: $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$((TESTS_RUN - TESTS_PASSED))${NC}"
    
    if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    fi
}

# Run tests
main "$@"