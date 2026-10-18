# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `gcp_service_account` is now optional. Without it the deployment uses Application Default
  Credentials: the agent's cloud identity (metadata server, Workload Identity) or the file named by
  `GOOGLE_APPLICATION_CREDENTIALS`, which is mounted read-only into the container. Setting a key
  works exactly as before and takes precedence.
- `wait` (default `true`) and `wait_timeout` (seconds, default `600`) options. After updating the
  function the plugin now polls the Cloud Functions operation until it is done and fails the step
  with the error of the operation (for example a failed build). **BREAKING (behaviour):** steps whose
  deployment was accepted but then failed used to pass; set `wait: false` for the old behaviour.
- Release workflow: when a pull request that turns `## [Unreleased]` into `## [X.Y.Z]` is merged,
  the commit is tagged `vX.Y.Z` and a GitHub release is created with that section as its notes. It
  uses only `GITHUB_TOKEN`, does nothing if the release exists and fails if the README does not
  mention the version. See CONTRIBUTING.md. `.github/scripts/changelog.sh` has bats tests.
- README: what the plugin does and does not do (updates the source of an existing 1st generation
  function through the v1 API), an "Upgrading to 1.0.0" section, the current options, credentials and
  project layout.
- `generation` option (`1`, the default, or `2`). `generation: 2` deploys 2nd generation functions
  (Cloud Run functions) through the Cloud Functions v2 API: it uploads the archive to a signed
  URL and patches only `buildConfig.source.storageSource`, then waits for the operation like
  generation 1 does. Without the option nothing changes.
- `exclude` option: an array of shell-style globs, relative to `cloud_function_directory`, of files that
  are not uploaded (for example `tests` or `*.md`), in addition to the built-in exclusions. The patterns
  reach the container as a newline-separated environment variable, never inside a shell command. The step
  fails when every file is excluded; the log reports how many files were excluded.
- `annotate` option: adds a Buildkite annotation with a summary of the deployment (function, project,
  region, generation, files and size, operation, time and, on failure, the error as an error
  annotation), created from the agent after the run so the container never gets the agent or its
  token. `annotation_context` (default `cloud-functions-<cloud_function_name>`) separates the
  annotations of several functions. All values are HTML-escaped and a failure to annotate never changes
  the step's result.
- `mode` option. `plan` shows what a deployment would do and changes nothing: it only reads the
  function (state, runtime, current source), builds the archive and logs the files that would be
  uploaded and the archive size; no upload URL is generated and nothing is uploaded or patched.
  `validate` checks the options and the archive offline with no credentials (directory exists,
  files remain after `exclude`, 1st generation archive within the 100 MiB upload limit). `apply`
  (the default) is unchanged. The annotation reports the mode.

### Changed

- Renovate is the only dependency updater (there is no Dependabot config). `renovate.json` now
  extends `helpers:pinGitHubActionDigests`, keeps `uv.lock` fresh with a weekly lock file
  maintenance, and also tracks the Python dependencies in `pyproject.toml`, Dockerfiles and the
  `python` image and `uv` version pinned in `hooks/command` (they were invisible before). The uv
  versions are grouped into one PR, as are Go and shfmt; the `requires-python` support range is
  not bumped. The exported `plugin_scripts/requirements.lock` is refreshed together with `uv.lock`
  (`docker compose run --rm lock-requirements`), and CI fails if it is stale.

### Security

- Updated the locked dependencies; `pip-audit` reported 33 advisories in 9 packages
  (urllib3, requests, protobuf, pyasn1, setuptools, wheel, idna, httplib2, pyarrow) and now
  reports none.
- The service account key is no longer written to a temporary file or put on the `docker create`
  command line (visible in `ps` and `docker inspect`); it is passed to Docker by variable name only.
- **BREAKING (behaviour):** the container no longer receives the whole job environment
  (`BUILDKITE_ENV_FILE`), the agent access token or the `buildkite-agent` binary; none of them was
  used. Only proxy variables are forwarded. `buildkite-agent` no longer has to be on the agent's `PATH`.
- **BREAKING (behaviour):** the uploaded archive no longer contains `.git`, `node_modules`,
  `__pycache__`, `*.pyc`, `.env`, `.env.*` or `.DS_Store`, so local secrets are not uploaded. Files
  are added in sorted order.
- Debug mode no longer logs the full function definition (it can contain environment variables);
  only name, status, runtime, entry point and update time.
- `uv` is pinned (`uv==0.13.1`) instead of installing whatever is latest.
- Workflows run with `permissions: contents: read`, checkouts no longer persist the token, and
  every action is pinned by full commit SHA. The `curl | sh` installers of `uv` are replaced by
  `astral-sh/setup-uv` with `uv` pinned to 0.13.1; the unused composite action that used one is removed.

### Changed

- **BREAKING: the default deploy image is now `python:3.15-slim`** (was `python:3.13-slim`).
  Set `custom_image: python:3.13-slim` to keep the old one.
- **Python 3.11 to 3.15 are supported and tested** (was 3.13 and 3.14); 3.10 is end of life.
- Dependencies are managed with uv: `[dependency-groups]` in `pyproject.toml` and a committed,
  universal `uv.lock`. `requirements.txt`, `requirements-test.txt` and the 3.14 devbox are removed;
  CI uses `uv sync --locked`, and a CI job fails when `uv.lock` or the container lock is stale.
- The deploy container installs only what the plugin imports: 26 packages instead of 45. The unused
  `gbq`, `google-cloud-bigquery(-storage)`, `pyarrow`, `numpy`, `pydantic`, `grpcio`, `setuptools`,
  `wheel` and others (left over from the BigQuery plugin) are gone, so every run is faster.
- `plugin_scripts/requirements.lock` is exported from `uv.lock` with hashes and installed with
  `uv pip install --require-hashes`. The devbox copies uv from a digest-pinned image.
- GitHub Actions updated: `actions/checkout` v7.0.1, `actions/setup-python` v7.0.0,
  `actions/upload-artifact` v7.0.2, `codecov/codecov-action` v7.1.1 and
  `github-action-renovate-config-validator` v2.4.1 (supersedes the open Renovate PRs).

### Fixed

- A failed `docker pull` now fails the step (it exited 0 silently).
- The deploy container is removed on every exit path, also when `docker cp` fails.
- Missing options now give the intended `ERROR: ... not set` message instead of
  `unbound variable`.
- `gcp_service_account` can be given as the plugin option (declared in `plugin.yml` but ignored
  until now) as well as the environment variable.
- `custom_image`, `debug_mode` and `docker_pull_retries` are now declared in `plugin.yml` and
  documented.
- Debug mode logged the method `Response.json` instead of the upload response body.
- The container is no longer started with `-it`/`--rm` (no TTY exists on agents).
- The `Bash shfmt` check failed on every pull request (`shfmt@latest` needs a newer Go than the
  builder image): shfmt is pinned to v3.14.1 and built with Go 1.27, and it now fails when a file
  is not formatted (`-s -d`; it used to rewrite the files and always pass).
- `codecov/codecov-action` was given an `file` input that does not exist; it is `files`.
- `buildkite/plugin-tester` and `plugin-linter` are pinned in `docker-compose.yaml`.

### Added

- `tests/command.bats`: tests of the hook with a stub `docker` (it had none), run in CI as
  `Bats (hooks/command)`.

## [0.2.0] - 2025-11-02

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

## [0.1.2] - 2022-04-11

### Changed

* Update dependencies

## [0.1.1] - 2021-12-14

### Changed

* Initial Release
