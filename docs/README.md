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