# Helm Chart Versioning Strategy

## Overview

This document outlines the versioning strategy for the Kronic Helm chart. We follow [Semantic Versioning](https://semver.org/) principles to ensure predictable and meaningful version increments.

## Version Format

The chart version follows the format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incremented for breaking changes that require user intervention
- **MINOR**: Incremented for new features or significant non-breaking changes
- **PATCH**: Incremented for bug fixes and small improvements

## Versioning Rules

### MAJOR Version Increments (X.0.0)

Increment the major version when making **breaking changes** that affect:

- **Values Schema Changes**: Removing or renaming required values
- **Template Breaking Changes**: Changes that break existing deployments
- **API Version Updates**: Kubernetes API version changes that drop support
- **Resource Name Changes**: Changes that affect resource naming
- **Default Behavior Changes**: Changes that significantly alter default behavior

**Examples:**
- Removing a required value from `values.yaml`
- Changing the structure of ingress configuration
- Updating to a Kubernetes API version that removes deprecated fields
- Changing default resource names or labels

### MINOR Version Increments (x.Y.0)

Increment the minor version when adding **new features** or making **non-breaking changes**:

- **New Features**: Adding new optional configuration options
- **New Templates**: Adding new Kubernetes resources
- **Enhancement**: Improving existing functionality without breaking changes
- **Dependencies**: Adding new optional dependencies

**Examples:**
- Adding new optional values for monitoring configuration
- Adding support for additional Kubernetes resources (NetworkPolicy, PDB)
- Adding new deployment strategies
- Enhancing documentation or adding examples

### PATCH Version Increments (x.y.Z)

Increment the patch version for **bug fixes** and **minor improvements**:

- **Bug Fixes**: Fixing template errors or logic issues
- **Documentation**: Updating documentation, comments, or README
- **Metadata Updates**: Updating chart metadata (description, keywords)
- **Minor Improvements**: Small optimizations that don't change behavior

**Examples:**
- Fixing template syntax errors
- Correcting default values
- Updating chart description or maintainer information
- Fixing typos or improving documentation

## Automation

### Automatic Version Detection

The versioning system can automatically detect the appropriate version bump based on:

1. **Commit Messages**: Analyzing recent commit messages for keywords
2. **File Changes**: Examining what files were modified
3. **Manual Override**: Allowing manual specification when needed

### Commit Message Keywords

The automation looks for these keywords to determine version bumps:

**MAJOR (Breaking Changes):**
- `BREAKING`, `breaking change`, `breaking:`
- Removal of existing features
- API changes that break compatibility

**MINOR (New Features):**
- `feat:`, `feature:`, `add:`
- New functionality or capabilities
- Non-breaking enhancements

**PATCH (Bug Fixes):**
- `fix:`, `bug:`, `patch:`
- Documentation updates
- Minor improvements
- Everything else (default)

### Workflow Triggers

Version bumping is triggered by:

1. **Automatic**: On push to main branch with chart changes
2. **Manual**: Via GitHub Actions workflow dispatch
3. **Pull Request**: Can be triggered for testing (creates draft release)

## Release Process

### Automated Steps

When a version bump occurs, the following happens automatically:

1. **Version Update**: Chart.yaml version is updated
2. **Git Tag**: A new git tag is created (`kronic-chart-X.Y.Z`)
3. **GitHub Release**: A release is created with packaged chart
4. **Changelog**: CHANGELOG.md is updated with new version entry
5. **Chart Package**: Helm chart is packaged and attached to release

### Manual Steps

Some steps may require manual intervention:

1. **Release Notes**: Detailed release notes should be added manually
2. **Migration Guides**: For major versions, create migration documentation
3. **Testing**: Verify the release in staging environments
4. **Communication**: Announce significant releases to users

## Best Practices

### For Developers

1. **Clear Commit Messages**: Use descriptive commit messages with appropriate prefixes
2. **Test Changes**: Ensure chart changes are tested before merging
3. **Document Changes**: Update documentation for user-facing changes
4. **Review Impact**: Consider the impact of changes on existing deployments

### For Users

1. **Read Release Notes**: Always check release notes before upgrading
2. **Test Upgrades**: Test chart upgrades in non-production environments first
3. **Backup**: Backup important data before major version upgrades
4. **Monitor**: Monitor applications after chart upgrades

## Examples

### Version Bump Examples

```bash
# Manual version bumps
./scripts/bump-chart-version.sh patch   # 0.1.7 -> 0.1.8
./scripts/bump-chart-version.sh minor   # 0.1.7 -> 0.2.0
./scripts/bump-chart-version.sh major   # 0.1.7 -> 1.0.0

# Automatic detection
./scripts/bump-chart-version.sh auto    # Analyzes commits to decide
```

### Workflow Dispatch

```yaml
# Trigger manual version bump via GitHub Actions
on:
  workflow_dispatch:
    inputs:
      version_type:
        type: choice
        options: ['auto', 'patch', 'minor', 'major']
```

## Troubleshooting

### Common Issues

1. **Version Not Bumping**: Check if commit messages contain version bump indicators
2. **Failed Releases**: Verify GitHub token permissions and branch protection rules
3. **Duplicate Tags**: Ensure no manual tags conflict with automated ones

### Manual Intervention

If automation fails, you can manually:

```bash
# Bump version
./scripts/bump-chart-version.sh patch

# Create tag
git tag -a kronic-chart-0.1.8 -m "Release version 0.1.8"
git push origin kronic-chart-0.1.8

# Create release via GitHub CLI
gh release create kronic-chart-0.1.8 --title "Helm Chart v0.1.8"
```

## Support

For questions or issues with the versioning system:

1. Check this documentation
2. Review GitHub Actions logs
3. Open an issue in the repository
4. Contact the maintainers

## Changelog

- **2024-12-27**: Initial versioning strategy documentation
- **2024-12-27**: Automated version bumping implementation
- **2024-12-27**: GitHub Actions integration for releases