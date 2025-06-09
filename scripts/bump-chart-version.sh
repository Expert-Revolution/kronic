#!/bin/bash

# Helm Chart Version Bumping Script
# This script automatically bumps the Helm chart version based on the type of change

set -e

CHART_DIR="chart/kronic"
CHART_YAML="$CHART_DIR/Chart.yaml"

# Function to display usage
usage() {
    echo "Usage: $0 [major|minor|patch|auto]"
    echo ""
    echo "Arguments:"
    echo "  major    - Increment major version (for breaking changes)"
    echo "  minor    - Increment minor version (for new features)"
    echo "  patch    - Increment patch version (for bug fixes)"
    echo "  auto     - Auto-detect version bump based on git commit messages"
    echo ""
    echo "Examples:"
    echo "  $0 patch"
    echo "  $0 auto"
    exit 1
}

# Function to get current version from Chart.yaml
get_current_version() {
    grep "^version:" "$CHART_YAML" | awk '{print $2}' | tr -d '"'
}

# Function to bump version
bump_version() {
    local current_version="$1"
    local bump_type="$2"
    
    # Split version into parts
    IFS='.' read -ra VERSION_PARTS <<< "$current_version"
    local major="${VERSION_PARTS[0]}"
    local minor="${VERSION_PARTS[1]}"
    local patch="${VERSION_PARTS[2]}"
    
    case "$bump_type" in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            echo "Error: Invalid bump type '$bump_type'"
            exit 1
            ;;
    esac
    
    echo "${major}.${minor}.${patch}"
}

# Function to auto-detect version bump type from recent commits
auto_detect_bump_type() {
    # Check for breaking changes (major)
    if git log --oneline --max-count=10 | grep -i -E "(BREAKING|breaking.*change)" >/dev/null 2>&1; then
        echo "major"
        return
    fi
    
    # Check for new features (minor)
    if git log --oneline --max-count=10 | grep -i -E "(feat|feature|add.*feature)" >/dev/null 2>&1; then
        echo "minor"
        return
    fi
    
    # Default to patch for any other changes
    echo "patch"
}

# Function to update Chart.yaml version
update_chart_version() {
    local new_version="$1"
    
    # Use sed to update the version in Chart.yaml
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/^version:.*/version: $new_version/" "$CHART_YAML"
    else
        # Linux
        sed -i "s/^version:.*/version: $new_version/" "$CHART_YAML"
    fi
}

# Main logic
main() {
    if [[ $# -ne 1 ]]; then
        usage
    fi
    
    local bump_type="$1"
    
    # Validate chart file exists
    if [[ ! -f "$CHART_YAML" ]]; then
        echo "Error: Chart.yaml not found at $CHART_YAML"
        exit 1
    fi
    
    # Get current version
    local current_version
    current_version=$(get_current_version)
    
    if [[ -z "$current_version" ]]; then
        echo "Error: Could not extract current version from $CHART_YAML"
        exit 1
    fi
    
    echo "Current chart version: $current_version"
    
    # Handle auto-detection
    if [[ "$bump_type" == "auto" ]]; then
        bump_type=$(auto_detect_bump_type)
        echo "Auto-detected bump type: $bump_type"
    fi
    
    # Validate bump type
    if [[ ! "$bump_type" =~ ^(major|minor|patch)$ ]]; then
        echo "Error: Invalid bump type '$bump_type'. Must be major, minor, patch, or auto."
        exit 1
    fi
    
    # Calculate new version
    local new_version
    new_version=$(bump_version "$current_version" "$bump_type")
    
    echo "Bumping version from $current_version to $new_version ($bump_type)"
    
    # Update Chart.yaml
    update_chart_version "$new_version"
    
    # Verify the change
    local updated_version
    updated_version=$(get_current_version)
    
    if [[ "$updated_version" == "$new_version" ]]; then
        echo "✅ Successfully updated chart version to $new_version"
        echo "Updated file: $CHART_YAML"
    else
        echo "❌ Error: Version update failed. Expected $new_version, got $updated_version"
        exit 1
    fi
}

# Run main function
main "$@"