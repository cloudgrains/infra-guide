# PyPI Publishing Guide for infra-guide

This document provides step-by-step instructions to publish `infra-guide` to PyPI and make it installable via `pipx`.

## Prerequisites

Before you can publish to PyPI, you need:

1. **A PyPI account**: Register at [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. **A Test PyPI account** (optional but recommended): Register at [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/) for testing before publishing to the real PyPI
3. **Build tools installed**:
   ```bash
   pip install build twine
   ```

## PyPI Configuration

### 1. Create `~/.pypirc` (Optional but Recommended)

Store your PyPI credentials for easier publishing:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your Test PyPI token

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your PyPI token
```

**Note**: Generate tokens at:
- PyPI: https://pypi.org/manage/account/
- Test PyPI: https://test.pypi.org/manage/account/

## Publishing Steps

### Step 1: Verify Package Structure

```bash
cd infra-guide-doctor

# Verify all necessary files exist
ls -la | grep -E "(pyproject.toml|README.md|LICENSE|MANIFEST.in|setup.py)"

# Check that the package structure is correct
ls -la infra_guide/
ls -la infra_guide/guides/
```

✅ **Expected**: All files present, CLI entry point configured in `pyproject.toml`

### Step 2: Clean Build Artifacts (if rebuilding)

```bash
rm -rf build/
rm -rf dist/
rm -rf infra_guide.egg-info/
rm -rf *.egg-info/
```

### Step 3: Build the Distribution

```bash
python3 -m build
```

✅ **Expected Output**:
```
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=61.0
  - wheel
* Getting build dependencies for sdist...
Successfully built infra_guide-0.2.0.tar.gz and infra_guide-0.2.0-py3-none-any.whl
```

Check the generated files:
```bash
ls -lh dist/
```

### Step 4: Verify Distribution Contents

```bash
# Check wheel contents
unzip -l dist/infra_guide-0.2.0-py3-none-any.whl | head -30

# Check source distribution contents
tar -tzf dist/infra_guide-0.2.0.tar.gz | head -30

# Verify entry point
unzip -q -p dist/infra_guide-0.2.0-py3-none-any.whl infra_guide-0.2.0.dist-info/entry_points.txt
```

✅ **Expected**: Should include `[console_scripts]` with `infra-guide = infra_guide.cli:main`

### Step 5: Test on Test PyPI (Recommended)

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Create a fresh test environment
python3 -m venv test_venv
source test_venv/bin/activate

# Install from Test PyPI to verify
pip install -i https://test.pypi.org/simple/ infra-guide

# Verify the command works
infra-guide

# Deactivate test environment
deactivate
rm -rf test_venv
```

### Step 6: Publish to PyPI

Once you've verified everything works on Test PyPI:

```bash
# Upload to production PyPI
twine upload dist/*

# Verify upload was successful
python3 -m venv prod_test
source prod_test/bin/activate
pip install infra-guide
infra-guide
deactivate
rm -rf prod_test
```

### Step 7: Test pipx Installation

Now that it's on PyPI, test the recommended installation method:

```bash
# If you have pipx installed
pipx install infra-guide

# Verify it works
infra-guide

# List installed packages
pipx list
```

## Verification Checklist

After publishing, verify everything works:

- ✅ Package appears on PyPI: https://pypi.org/project/infra-guide/
- ✅ `pip install infra-guide` works
- ✅ `pipx install infra-guide` works
- ✅ `infra-guide` command is available
- ✅ README displays correctly
- ✅ All classifiers are correct
- ✅ Dependencies are resolved automatically

## Updating Version and Re-publishing

When releasing a new version:

1. **Update version in `pyproject.toml`**:
   ```toml
   [project]
   version = "0.2.1"
   ```

2. **Update `infra_guide/__init__.py`**:
   ```python
   __version__ = "0.2.1"
   ```

3. **Create a git tag**:
   ```bash
   git tag v0.2.1
   git push origin v0.2.1
   ```

4. **Rebuild and republish**:
   ```bash
   rm -rf dist/ build/ *.egg-info/
   python3 -m build
   twine upload dist/*
   ```

## PyPI Package Page

Once published, your package will be available at:
- **Main**: https://pypi.org/project/infra-guide/
- **Test (during development)**: https://test.pypi.org/project/infra-guide/

## Troubleshooting

### Build Errors

**Error**: `ValueError: invalid pyproject.toml config`
- **Solution**: Ensure `pyproject.toml` follows the PEP 621 standard. Remove invalid properties like `readme-content-type`.

**Error**: `ModuleNotFoundError` during build
- **Solution**: Ensure all imports in `__init__.py` reference modules that exist.

### Upload Errors

**Error**: `401 Unauthorized`
- **Solution**: Check your token in `~/.pypirc` or re-authenticate with `twine login`

**Error**: `400 Bad Request - Invalid value for description`
- **Solution**: Verify README.md is valid Markdown and renders correctly

### Installation Issues

**Error**: `infra-guide: command not found`
- **Solution**: Ensure the entry point is correctly defined in `pyproject.toml`:
  ```toml
  [project.scripts]
  infra-guide = "infra_guide.cli:main"
  ```

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [PEP 427 - Wheel Binary Package Format](https://peps.python.org/pep-0427/)
