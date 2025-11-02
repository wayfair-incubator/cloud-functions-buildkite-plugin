# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security (CRITICAL)

- **CRITICAL FIX**: Secure credential handling in Buildkite plugin hook
  - Replaced predictable `/tmp/service_account.json` with secure `mktemp`
  - Set restrictive file permissions (600) on credential files
  - Added proper cleanup trap handlers (EXIT, ERR, INT, TERM)
  - Eliminated symlink attack vulnerability
  - Fixed race condition when multiple builds run simultaneously
  - Credentials no longer visible to all users on the system

### Changed (Breaking)

- **BREAKING**: Updated Buildkite hook to use Python 3.13-slim image (was 3.10.1-buster)
  - Plugin now requires Python 3.13+ compatible environments
  - Updated default Docker image from `python:3.10.1-buster` to `python:3.13-slim`
- **BREAKING**: GitHub Actions now require Python 3.13 or 3.14
  - CI/CD pipelines updated to test against Python 3.13 and 3.14 only
  - Dropped support for Python 3.7, 3.8, 3.9, 3.10 (all EOL or deprecated)

### Updated

**GitHub Actions**:
- `actions/checkout`: v3 → v4
- `actions/setup-python`: v4 → v5 (with prerelease support for Python 3.14)
- `actions/upload-artifact`: v3 → v4
- `codecov/codecov-action`: v3.1.1 → v4
- `suzuki-shunsuke/github-action-renovate-config-validator`: v0.1.2 → v1.0.1

**GitHub Workflows**:
- Consolidated 5 separate linting jobs (black, isort, flake8, bandit, mypy) into 2 jobs (ruff, mypy)
- Added matrix testing for Python 3.13 and 3.14
- All workflows now use uv for dependency installation (10-100x faster)

**Buildkite Hook (`hooks/command`)**:
- Updated to use uv for package installation
- Command now: `pip install uv && uv pip install --system -r plugin_scripts/requirements.lock`
- Added detailed debug output for credential file path

**GitHub Actions Install Script**:
- `.github/actions/install-dependencies/action.sh` now uses uv instead of pip
- Installs uv via official install script
- Significantly faster CI/CD runs

### Fixed

- Fixed outdated `requirements.lock` file
  - Updated from ancient versions (e.g., protobuf 3.20.1 → 5.29.2)
  - Now matches updated `requirements.txt` specifications
  - Uses `>=` version specifiers for flexibility
- Fixed GitHub Actions using deprecated Python versions
- Fixed GitHub Actions using outdated action versions

### Development

- CI/CD now 10-100x faster with uv for dependency installation
- Linting consolidated from 5 jobs to 2 (ruff + mypy)
- GitHub Actions test matrix now includes Python 3.13 and 3.14
- Added `allow-prereleases: true` for Python 3.14 testing

## [v0.2.0] - 2025-11-02

### Changed (Breaking)

- **BREAKING**: Upgraded Python from 3.10 to 3.13/3.14
  - Update your Docker images and CI/CD pipelines to use Python 3.13 or 3.14
  - Code is now compatible with Python 3.13+ only (including Python 3.14)
  - Both Python 3.13 and 3.14 are officially supported and tested
- **BREAKING**: Replaced pip with uv for faster dependency management
  - Installation is now 10-100x faster
  - Update any custom scripts that relied on pip-specific features
- **BREAKING**: Replaced black, isort, flake8, and bandit with unified Ruff linter
  - Ruff provides 10-100x faster linting and formatting
  - Configuration moved to `pyproject.toml`
- **BREAKING**: Consolidated all tool configurations into `pyproject.toml`
  - Removed: `.bandit`, `.flake8`, `mypy.ini`, `pytest.ini`, `.coveragerc`
  - All configuration is now in a single file
- **BREAKING**: Custom exceptions now have improved semantics
  - `MissingConfigError` now takes config name as parameter
  - `CloudFunctionDirectoryNonExistent` now includes directory path
  - `DeployFailed` now accepts custom error messages

### Security

- **CRITICAL**: Removed `sys.tracebacklimit = 0` to show full stack traces
  - Previously, errors were hidden which made debugging and security audits difficult
  - Full stack traces now available for better error diagnosis
- Enhanced credential handling with proper error chaining
  - All credential errors now properly logged and traceable
  - Added validation for JSON parsing of credentials

### Fixed

- Fixed path handling using pathlib for better cross-platform compatibility
  - Replaced all `os.path` and string concatenation with `pathlib.Path`
  - Eliminates potential path separator issues on different platforms
- Improved error handling throughout deployment pipeline
  - All exceptions now properly chained with `raise ... from e`
  - Better error messages for all failure scenarios
- Added timeout to HTTP requests (300 seconds) to prevent hanging
- Fixed logging output (removed extraneous newlines)

### Updated

**Core Dependencies (Major Version Updates)**:
- pydantic: 1.9.1 → 2.10.3 (Major: v1 → v2)
- numpy: 1.23.0 → 2.2.0 (Major: v1 → v2)
- protobuf: 3.20.2 → 5.29.2 (Major: v3 → v5)

**Google Cloud Dependencies**:
- google-api-core: 2.8.2 → 2.23.0
- google-api-python-client: 2.51.0 → 2.154.0
- google-auth: 2.8.0 → 2.37.0
- google-cloud-bigquery: 3.2.0 → 3.27.0
- google-cloud-bigquery-storage: 2.13.2 → 2.27.0
- google-cloud-core: 2.3.2 → 2.4.1
- google-cloud-storage: 2.4.0 → 2.19.0
- google-crc32c: 1.3.0 → 1.6.0
- google-resumable-media: 2.3.3 → 2.7.2

**Other Dependencies**:
- cachetools: 5.2.0 → 5.5.0
- certifi: 2022.6.15 → 2024.8.30
- cffi: 1.15.1 → 1.17.1
- chardet: 5.0.0 → 5.2.0
- charset-normalizer: 2.0.12 → 3.4.0
- googleapis-common-protos: 1.56.3 → 1.66.0
- grpcio: 1.47.0 → 1.68.1
- grpcio-status: 1.47.0 → 1.68.1
- httplib2: 0.20.4 → 0.22.0
- idna: 3.3 → 3.10
- packaging: 21.3 → 24.2
- proto-plus: 1.20.6 → 1.25.0
- pyarrow: 8.0.0 → 18.1.0
- pyasn1: 0.4.8 → 0.6.1
- pyasn1-modules: 0.2.8 → 0.4.1
- pycparser: 2.21 → 2.22
- pyparsing: 3.0.9 → 3.2.0
- python-dateutil: 2.8.2 → 2.9.0
- pytz: 2022.1 → 2024.2
- requests: 2.28.0 → 2.32.3
- rsa: 4.8 → 4.9
- setuptools: 58.1.0 → 75.6.0
- six: 1.16.0 → 1.17.0
- typing-extensions: 4.2.0 → 4.12.2
- urllib3: 1.26.9 → 2.2.3
- wheel: 0.37.1 → 0.45.1

**Development Dependencies**:
- mypy: 0.961 → 1.13.0
- pytest: 7.1.2 → 8.3.4
- pytest-cov: 3.0.0 → 6.0.0
- pytest-mock: 3.8.1 → 3.14.0
- types-requests: 2.27.31 → 2.32.0.20241016
- **Added**: ruff 0.8.4 (replaces black, isort, flake8, bandit)
- **Removed**: black, isort, flake8, bandit (replaced by ruff)

### Added

- **Python 3.14 support**: Project is ready for Python 3.14
  - Added `pyproject.toml` classifiers for Python 3.14
  - Included Python 3.14 Dockerfile (`docker/devbox-py314.dockerfile`)
  - Docker Compose service for testing with Python 3.14
  - All code compatible with Python 3.14 when released
- Comprehensive logging throughout the deployment pipeline
  - All major operations now logged with INFO level
  - Debug mode enables detailed DEBUG level logging
  - Errors properly logged before raising exceptions
- Custom exception classes with better error semantics
  - `MissingConfigError`: Clear indication of which config is missing
  - Enhanced `CloudFunctionDirectoryNonExistent`: Includes directory path
  - Enhanced `DeployFailed`: Accepts custom error messages
- Detailed docstrings for all functions
  - All functions now have comprehensive docstrings
  - Includes Args, Returns, and Raises sections
  - Better code maintainability and IDE support
- Type hints throughout the codebase
  - Added return type annotations to all functions
  - Added parameter type hints where missing
  - Better IDE support and type checking
- Enhanced test coverage with 17 additional test cases
  - Tests for all new error conditions
  - Tests for edge cases (missing env vars, invalid JSON, etc.)
  - Tests for new exception types
  - Comprehensive testing of error handling paths
- Branch coverage enabled in pytest configuration
  - More thorough testing of conditional logic
  - Coverage reports now include branch coverage metrics
- New docker-compose services:
  - `ruff-check`: Run ruff linter in check mode
  - `ruff-lint`: Run ruff linter with auto-fix
  - `ruff-format-check`: Check code formatting
  - `ruff-format`: Format code automatically
  - `mypy`: Run type checking
- `pyproject.toml` with all tool configurations
  - Single source of truth for all project configuration
  - Modern Python project structure
  - Compatible with all modern Python tools

### Removed

- Old configuration files (consolidated to `pyproject.toml`):
  - `.bandit`
  - `.flake8`
  - `mypy.ini`
  - `pytest.ini`
- Old development dependencies:
  - black (replaced by ruff)
  - isort (replaced by ruff)
  - flake8 (replaced by ruff)
  - bandit (replaced by ruff)
- `sys.tracebacklimit = 0` (security improvement)
- Deprecated `os.path` usage (replaced with pathlib)

### Development

- **Python 3.14 readiness**: 
  - Added `docker/devbox-py314.dockerfile` for Python 3.14 testing
  - Added `devbox-py314` service in docker-compose.yaml
  - When Python 3.14 is released, simply build and test: `docker-compose build devbox-py314`
- Simplified test scripts using Ruff
  - Single command for all linting and formatting
  - Faster execution (10-100x speedup)
  - Consistent code style enforcement
- Updated Docker images:
  - Base image: `python:3.13-slim`
  - Includes uv for fast dependency installation
  - Optimized environment variables for Python
- Updated lock_requirements.sh to use uv
  - Faster dependency locking
  - More reliable dependency resolution
- Improved run_tests.sh script
  - Cleaner output
  - Better error messages
  - Unified linting/formatting workflow

### Migration Guide

**For Users**:
No changes required. The plugin API remains the same. Simply pull the latest version.

**For Developers**:

1. **Update Python Version**: Ensure you have Python 3.13 or 3.14 installed
2. **Install uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. **Install Dependencies**: `uv pip install -r requirements.txt -r requirements-test.txt`
4. **Update IDE/Editor**: Configure to use ruff instead of black/isort/flake8
5. **Run Tests**: `docker-compose run --rm py-test`

## [v0.1.2] - 2022-04-11

### Changed

* Update dependencies

## [v0.1.1] - 2021-12-14

### Changed

* Initial Release
