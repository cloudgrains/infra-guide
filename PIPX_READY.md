# infra-guide: Ready for PyPI 🚀

This repository is now fully configured as a professional Python package ready for distribution via PyPI and installation via `pipx`.

## Quick Summary

✅ **Package Structure**: Proper Python package with `infra_guide/` as main module  
✅ **Entry Point**: `infra-guide` command configured in `pyproject.toml`  
✅ **Metadata**: Complete and professional PyPI metadata  
✅ **Dependencies**: Properly declared with `rich>=13.0.0`  
✅ **License**: MIT license included  
✅ **Documentation**: Comprehensive README with installation instructions  
✅ **Build System**: Modern PEP 517/518 compliant with `pyproject.toml`  
✅ **Distribution**: Successfully builds both wheel and source distributions

## Installation Methods

### For End Users

```bash
# Using pipx (recommended for CLI tools)
pipx install infra-guide

# Using pip in a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install infra-guide

# Development installation from source
git clone https://github.com/iamtejas23/infra-guide.git
cd infra-guide
pip install -e ".[dev]"
```

### After Installation

```bash
# Run the tool
infra-guide
```

## Project Files Overview

### Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Main configuration (build system, metadata, dependencies, entry points) |
| `MANIFEST.in` | Specifies additional files to include in source distributions |
| `.gitignore` | Excludes build artifacts and Python cache files |

### Package Structure

```
infra_guide/
├── __init__.py              # Package metadata and version
├── cli.py                   # ✅ Main entry point (infra-guide command)
├── detector.py              # Tool detection (Terraform/OpenTofu)
├── runner.py                # Command execution
├── ui.py                    # TUI interface using rich
├── drift_detector.py        # Infrastructure drift detection
├── state_explorer.py        # State file exploration
├── workspace_manager.py     # Workspace management
├── validators.py            # Pre-flight validation
├── cicd.py                  # CI/CD pipeline support
├── policy_checker.py        # Policy validation
└── guides/
    ├── __init__.py
    ├── init.py
    ├── plan.py
    ├── apply.py
    └── destroy.py
```

## Building and Testing Locally

### Build the Package

```bash
# Install build tools
pip install build twine

# Build distributions (wheel + source)
python3 -m build

# Output files in dist/
ls -lh dist/
```

### Test Installation Locally

```bash
# Create test environment
python3 -m venv test_env
source test_env/bin/activate

# Install from local wheel
pip install dist/infra_guide-0.2.0-py3-none-any.whl

# Verify command is available
which infra-guide
infra-guide

# Deactivate
deactivate
rm -rf test_env
```

## Publishing to PyPI

See `PUBLISH_GUIDE.md` for detailed step-by-step instructions.

### Quick Start for Publishing

```bash
# 1. Register at https://pypi.org/account/register/
# 2. Generate API token at https://pypi.org/manage/account/
# 3. Create ~/.pypirc with your credentials (optional)

# 4. Build the package
python3 -m build

# 5. Upload to PyPI
twine upload dist/*

# 6. After publishing, users can install with:
pipx install infra-guide
```

## Features Verification

The built package includes:

- ✅ Console script entry point: `infra-guide = infra_guide.cli:main`
- ✅ All Python modules and guides included
- ✅ LICENSE file included in distributions
- ✅ README.md with setup instructions
- ✅ Proper dependency resolution (rich>=13.0.0)
- ✅ Python 3.8+ support
- ✅ Cross-platform (Linux, macOS, Windows)

## Key Metadata

| Field | Value |
|-------|-------|
| Name | `infra-guide` |
| Version | `0.2.0` |
| Python | `>=3.8` |
| License | `MIT` |
| Status | `Beta` |
| Repository | `https://github.com/iamtejas23/infra-guide` |

## Next Steps

1. **Register on PyPI**: Create account at https://pypi.org/account/register/
2. **Generate Token**: Create API token at https://pypi.org/manage/account/token/
3. **Follow Publishing Guide**: See `PUBLISH_GUIDE.md` for detailed instructions
4. **Test on Test PyPI**: Verify package before publishing to production
5. **Publish to PyPI**: Make package available for `pipx install`

## Package Verification Commands

```bash
# Check if all required files are present
find infra_guide -type f -name "*.py" | wc -l

# Verify entry point configuration
grep -A 1 "\[project.scripts\]" pyproject.toml

# Check dependencies
grep -A 5 "dependencies = " pyproject.toml

# List all classifiers
grep "Classifier:" dist/infra_guide-0.2.0-py3-none-any.whl 2>/dev/null || \
  python3 -c "import tomllib; import pprint; config = tomllib.load(open('pyproject.toml', 'rb')); pprint.pprint(config['project']['classifiers'])"
```

## Support

For more information:
- 📖 [Python Packaging Guide](https://packaging.python.org/)
- 📚 [PyPI Help](https://pypi.org/help/)
- 🔧 [Twine Documentation](https://twine.readthedocs.io/)
- 📋 [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
