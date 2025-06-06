# Kronic Documentation Site

This directory contains the GitHub Pages documentation website for the Kronic Helm chart.

## Contents

- `index.html` - Main documentation page with comprehensive chart information, installation instructions, and configuration examples

## Deployment

The documentation is automatically deployed to GitHub Pages via the `.github/workflows/pages.yaml` workflow when changes are pushed to the `main` branch.

The site will be available at: https://davides93.github.io/kronic/

## Local Development

To preview the documentation locally, you can simply open `index.html` in a web browser or serve it with a simple HTTP server:

```bash
# Using Python
python3 -m http.server 8080 -d docs

# Using Node.js (if you have npx)
npx http-server docs -p 8080
```

Then visit http://localhost:8080

## Features

The documentation site includes:

- Comprehensive chart overview and features
- Installation instructions and examples
- Configuration options with code examples
- Security considerations
- Screenshots of the application
- Links to repository and releases
- **Automated version information display** showing current chart and app versions

## Automated Version Updates

The documentation site is automatically updated when new Helm chart versions are released:

1. **Version Display**: The main page shows current chart version, app version, and last updated date
2. **Helm Repository**: The `index.yaml` file is automatically updated with new chart releases
3. **Synchronized Deployment**: Changes trigger automatic GitHub Pages deployment

This automation is handled by the chart versioning workflows in `.github/workflows/`.

## Version Information

The version information section is automatically maintained by the `scripts/update-pages-version.sh` script and displays:

- **Chart Version**: Current Helm chart version from `chart/kronic/Chart.yaml`
- **App Version**: Current application version
- **Last Updated**: Date when the version information was last updated

The version section is marked with HTML comments (`<!-- VERSION_INFO_START -->` and `<!-- VERSION_INFO_END -->`) to allow automated updates while preserving other page content.