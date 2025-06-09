#!/bin/bash

# Script to update GitHub Pages with current Helm chart version information
# This script updates the index.html file with the latest chart version

set -e

CHART_DIR="chart/kronic"
CHART_YAML="$CHART_DIR/Chart.yaml"
INDEX_HTML="docs/index.html"

# Function to display usage
usage() {
    echo "Usage: $0"
    echo ""
    echo "This script updates the GitHub Pages index.html file with current chart version information."
    echo "It reads the version from $CHART_YAML and updates the display in $INDEX_HTML"
    exit 1
}

# Function to get current version from Chart.yaml
get_current_version() {
    if [[ ! -f "$CHART_YAML" ]]; then
        echo "Error: Chart.yaml not found at $CHART_YAML"
        exit 1
    fi
    grep "^version:" "$CHART_YAML" | awk '{print $2}' | tr -d '"'
}

# Function to get app version from Chart.yaml
get_app_version() {
    if [[ ! -f "$CHART_YAML" ]]; then
        echo "Error: Chart.yaml not found at $CHART_YAML"
        exit 1
    fi
    grep "^appVersion:" "$CHART_YAML" | awk '{print $2}' | tr -d '"'
}

# Function to update index.html with version information
update_index_html() {
    local chart_version="$1"
    local app_version="$2"
    
    if [[ ! -f "$INDEX_HTML" ]]; then
        echo "Error: index.html not found at $INDEX_HTML"
        exit 1
    fi
    
    # Get current date for last updated
    local current_date=$(date +"%Y-%m-%d")
    
    # Create a temporary file for the updated content
    local temp_file="/tmp/index_updated.html"
    
    # Check if version info section already exists
    if grep -q "<!-- VERSION_INFO_START -->" "$INDEX_HTML"; then
        # Update existing version info section
        sed '/<!-- VERSION_INFO_START -->/,/<!-- VERSION_INFO_END -->/c\
        <!-- VERSION_INFO_START -->\
        <div class="version-info" style="background: #e8f4fd; border: 1px solid #b8daf6; border-radius: 8px; padding: 15px; margin: 20px 0; color: #2c3e50;">\
            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">📦 Current Release Information</h4>\
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">\
                <div><strong>Chart Version:</strong> <span class="badge" style="background: #28a745;">v'"$chart_version"'</span></div>\
                <div><strong>App Version:</strong> <span class="badge" style="background: #17a2b8;">'"$app_version"'</span></div>\
                <div><strong>Last Updated:</strong> '"$current_date"'</div>\
            </div>\
        </div>\
        <!-- VERSION_INFO_END -->' "$INDEX_HTML" > "$temp_file"
    else
        # Add version info section after the header
        sed '/class="header">/,/<\/div>/{
            /<\/div>/{
                a\
\
    <!-- VERSION_INFO_START -->\
    <div class="version-info" style="background: #e8f4fd; border: 1px solid #b8daf6; border-radius: 8px; padding: 15px; margin: 20px 0; color: #2c3e50;">\
        <h4 style="margin: 0 0 10px 0; color: #2c3e50;">📦 Current Release Information</h4>\
        <div style="display: flex; gap: 20px; flex-wrap: wrap;">\
            <div><strong>Chart Version:</strong> <span class="badge" style="background: #28a745;">v'"$chart_version"'</span></div>\
            <div><strong>App Version:</strong> <span class="badge" style="background: #17a2b8;">'"$app_version"'</span></div>\
            <div><strong>Last Updated:</strong> '"$current_date"'</div>\
        </div>\
    </div>\
    <!-- VERSION_INFO_END -->
            }
        }' "$INDEX_HTML" > "$temp_file"
    fi
    
    # Also update Chart Details section version references
    local temp_file2="/tmp/index_updated2.html"
    
    # Update Chart Version in Chart Details section
    sed "s/<li><strong>Chart Version:<\/strong> [^<]*<\/li>/<li><strong>Chart Version:<\/strong> $chart_version<\/li>/" "$temp_file" > "$temp_file2"
    
    # Update App Version in Chart Details section
    sed "s/<li><strong>App Version:<\/strong> [^<]*<\/li>/<li><strong>App Version:<\/strong> $app_version<\/li>/" "$temp_file2" > "$temp_file"
    
    # Replace the original file with the updated one
    mv "$temp_file" "$INDEX_HTML"
    
    # Clean up temporary file
    rm -f "$temp_file2"
    
    echo "✅ Updated $INDEX_HTML with chart version $chart_version and app version $app_version"
}

# Main execution
main() {
    echo "🔄 Updating GitHub Pages with current chart version information..."
    
    # Get current versions
    CHART_VERSION=$(get_current_version)
    APP_VERSION=$(get_app_version)
    
    if [[ -z "$CHART_VERSION" ]]; then
        echo "Error: Could not read chart version from $CHART_YAML"
        exit 1
    fi
    
    if [[ -z "$APP_VERSION" ]]; then
        echo "Error: Could not read app version from $CHART_YAML"
        exit 1
    fi
    
    echo "📋 Current chart version: $CHART_VERSION"
    echo "📋 Current app version: $APP_VERSION"
    
    # Update the index.html file
    update_index_html "$CHART_VERSION" "$APP_VERSION"
    
    echo "✅ GitHub Pages version information updated successfully!"
}

# Check if help is requested
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    usage
fi

# Run main function
main "$@"