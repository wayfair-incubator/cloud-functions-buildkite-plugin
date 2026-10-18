[![Actions Status](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/workflows/Lint/badge.svg?branch=main)](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/actions)
[![Actions Status](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/workflows/Unit%20Tests/badge.svg?branch=main)](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/actions)
![Version](https://img.shields.io/static/v1.svg?label=Version&message=0.2.0&color=lightgrey&?link=http://left&link=https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/tree/v0.2.0)
![Plugin Status](https://img.shields.io/static/v1.svg?label=&message=Buildkite%20Plugin&color=blue&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAMAAADVRocKAAAAk1BMVEX///+DrRik1Cb+/vyErhin1yeAqhfJ5n+dzCO50X2VwiC2zna020vg8LSo1i+q1zTN3qL7/fav2UDT4q33++yXuj3z+eLO6IqMuByJsSPM54XX5bWcvUbH5Xrg6sWiwVHB1ovk7cymxFnq8deOtC2xzG7c6L6/1YfU7JbI2pj2+e+jzzPd763K3J3j8ryRtDbY7aOqCe3pAAACTElEQVRoge3Z11KDQBSAYUpItSRqVGwxEVOwxPd/OndhCbA5BTaLM87sueb83+yMStHz3Lhx48bN/5iw+2VjImy0fDvzQiNCLKVrdjn0nq++QwNCLMy+9uOzc2Y59AZBwF4F55NefxxxyxK4aEvI/C7x/QxglrMTBNxVej6V+QNALh+AhkRY5isAsVwBxFWfM/rnLsu/qnwNQIkawBBy/abMawBCaEAQXGFElt/Evo8CIHEEIESWH9XyAAAQACCIH40A8yBwRICARiB5BNAIBKgQ8tLbCZBHgRqBAgWB5wmgQhCAIt7ekTwJ5AQHSGKC1TkgiM7WIs8A0bBvCETR8H7CA4EhIPP9fgPA7AR53u91BBR53+8EKPPdACLvq3wXQC1vH9DytoGjvF0gGo71vE0gCoC8PQDJ2wJEvgfmbQFo3g5A5HNA3K+eL0yBePdO5AtAEAOUoIB4c+ONiHwBZHddjMCB5DUV6yOqfzgBQWCAzMu9ZoAiHgACBpJdmj3SNAdQAgKSXfFQ1gZQz28PlxxQ5tsCIKED+6/qU2tbQBF3lxgwn9YfitsDR0QVmE9D7bHeBNCIEphf63lToEYUAJQ3BxSxlUQGPD3Cr5DmwIGQJ8DypwHqlXX7gec5oMcAXv5OT31OYU6weuM/9tDv/iSwWnJxfghA5s0+QzUCFi828iiwWNvJI4C9PAg8WcwDAPVLYwGwndeAufV8DZB/bm3nK0A3+RyI81tdF3l1gn1neQlM4qnpp+9ms0xP/P8AP/8778aNGzdu/mh+AQp1NCB/JInXAAAAAElFTkSuQmCC)

# Cloud Functions Buildkite Plugin

This buildkite plugin can be used to deploy code to [Cloud Functions](https://cloud.google.com/functions)

See the [plugin tester](https://github.com/buildkite-plugins/buildkite-plugin-tester) for testing examples and usage, and the [Buildkite docs on writing plugins](https://buildkite.com/docs/plugins/writing) to understand everything in this repo.

## Using the plugin

If the version number is not provided then the most recent version of the plugin will be used. Do not use version number as `main` or any branch name.

### Simple

```yaml
steps:
  - plugins:
      - wayfair-incubator/cloud-functions#v0.2.0:
          gcp_project: "gcp-us-project"
          gcp_region: "us-central1"
          cloud_function_name: "function-1"
          cloud_function_directory: "directory/function-code"
```

## Configuration

### Required

### `gcp_project` (required, string)

The name of the GCP project you want to deploy to.

Example: `gcp-us-project`

### `gcp_region` (required, string)

GCP region where the cloud function is hosted.

Example: `us-central1`

### `cloud_function_name` (required, string)

Name of the cloud function in GCP.

Example: `function-1`

### `cloud_function_directory` (required, string)

The directory in your repository where you are storing the code files for the cloud function.

Example: `directory/function-code`

### Optional

### `wait` (optional, boolean)

Wait for the deployment to finish and fail the step if it fails. Updating a function only starts a
long-running operation (build, rollout); with `wait: false` the step succeeds as soon as the update was
accepted (the behaviour before this option existed). Default: `true`.

### `wait_timeout` (optional, integer)

Seconds to wait for the deployment to finish. The step fails when it takes longer (the deployment
may still complete). Default: `600`.

### `custom_image` (optional, string)

Docker image the deployment runs in. Default: `python:3.13-slim`.

### `debug_mode` (optional, boolean)

Log extra details. Default: `false`.

### `docker_pull_retries` (optional, integer)

How many times pulling the image is tried. Default: `3`.

## Credentials

Either of:

**A service account key (JSON)**, passed with the `gcp_service_account` plugin option or a `gcp_service_account` environment variable. Store it [securely](https://buildkite.com/docs/pipelines/secrets)!

```yaml
steps:
  - plugins:
      - wayfair-incubator/cloud-functions#v0.2.0:
          gcp_project: "gcp-us-project"
          gcp_region: "us-central1"
          cloud_function_name: "function-1"
          cloud_function_directory: "directory/function-code"
          gcp_service_account: "${GCP_SA_KEY}" # or set a gcp_service_account env var
```

**Application Default Credentials**, when no key is given: the identity of the agent's machine (GCE/GKE metadata server, Workload Identity), or the credentials file named by `GOOGLE_APPLICATION_CREDENTIALS` on the agent, which is mounted read-only into the container. No long-lived key has to be stored in Buildkite. The identity needs permission to update the function (for example `roles/cloudfunctions.developer`) and to act as its runtime service account. A federated (`external_account`) credentials file that points at other files, such as a token file, will not find them inside the container; use the metadata server in that case.

The key is handed to the container by variable name only, so it never appears on a command line. The container does not receive the rest of the job environment (only the proxy variables `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` and their lowercase forms, when set).

## What is uploaded

Everything in `cloud_function_directory` except `.git`, `node_modules`, `__pycache__`, `*.pyc`, `.env`, `.env.*` and `.DS_Store`.

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependencies (`pyproject.toml` and the committed `uv.lock`), Ruff for linting and formatting, and Docker for a consistent environment.

### Requirements

- Docker and Docker Compose
- Python 3.11 to 3.15 and [uv](https://github.com/astral-sh/uv) (for local development without Docker)

### Quick Start

```bash
# Build the development container (Python 3.15)
docker compose build devbox

# Run all tests and linting
docker compose run --rm py-test
```

The plugin's code is tested on Python 3.11, 3.12, 3.13, 3.14 and 3.15 in CI. The deploy container uses `python:3.15-slim` by default (`custom_image` overrides it).

### Development Commands

#### Testing

```bash
# Run all tests with coverage
docker compose run --rm py-test

# Run tests with formatting (formats code before running tests)
docker compose run --rm py-test --format-code

# Run tests locally
uv run pytest --cov plugin_scripts tests --cov-report html
```

#### Code Quality

```bash
# Format code with Ruff
docker compose run --rm ruff-format

# Check formatting (without modifying files)
docker compose run --rm ruff-format-check

# Run linter and auto-fix issues
docker compose run --rm ruff-lint

# Run linter in check mode (no fixes)
docker compose run --rm ruff-check

# Run type checking with mypy
docker compose run --rm mypy
```

#### Dependency Management

```bash
# Install the locked dependencies, including the dev tools
uv sync --locked

# Add or change a dependency, then refresh uv.lock and the hashed
# plugin_scripts/requirements.lock that the deploy container installs
docker compose run --rm lock-requirements          # or: uv lock && uv export ...
docker compose run --rm lock-requirements --upgrade # move every pin to its latest release
```

CI fails when `uv.lock` or `plugin_scripts/requirements.lock` is out of date.

#### Interactive Development

```bash
# Start an interactive shell in the container
docker compose run --rm devbox

# Inside the container, you can:
#   - Run pytest
#   - Run ruff check/format
#   - Run mypy
#   - Debug code
```

### Local Development (without Docker)

```bash
uv sync --locked

uv run pytest
uv run ruff format plugin_scripts tests
uv run ruff check --fix plugin_scripts tests
uv run mypy plugin_scripts tests
```

### Project Structure

```
cloud-functions-buildkite-plugin/
├── plugin_scripts/          # Main plugin code
│   ├── __init__.py
│   ├── deploy.py           # Deployment logic
│   └── pipeline_exceptions.py  # Custom exceptions
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_deploy.py
│   └── test_pipeline_exceptions.py
├── docker/                  # Docker configuration
│   ├── devbox.dockerfile
│   ├── run_tests.sh        # Test runner script
│   └── lock_requirements.sh # Dependency locking script
├── hooks/                   # Buildkite plugin hooks
│   └── command             # Main plugin command
├── pyproject.toml          # All tool configurations
├── uv.lock                 # Locked dependencies (all platforms)
└── docker-compose.yaml     # Docker services
```

### Configuration

All tool configurations are centralized in `pyproject.toml`:

- **Ruff**: Linting and formatting rules
- **MyPy**: Type checking configuration
- **Pytest**: Test runner configuration
- **Coverage**: Code coverage settings

See `pyproject.toml` for detailed configuration options.

## Contributing

See the [Contributing Guide](CONTRIBUTING.md) for additional information.

### Running Tests Locally

To execute tests locally (requires that `docker` and Docker Compose are installed):

```bash
docker compose run --rm py-test
# Or with legacy v1: docker compose run --rm py-test
```

### Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Ruff is configured to:

- Enforce PEP 8 style guidelines
- Sort imports (replacing isort)
- Check for common bugs and security issues (replacing bandit)
- Enforce modern Python patterns (pyupgrade)
- Use pathlib for file operations

To format your code before committing:

```bash
docker compose run --rm ruff-format
docker compose run --rm ruff-lint
```

### Type Checking

This project uses [MyPy](https://mypy-lang.org/) for static type checking. Run type checks with:

```bash
docker compose run --rm mypy
```

## What's New in v0.2.0

This release includes major modernization improvements:

- ⚡ **10-100x faster** dependency installation with uv
- ⚡ **10-100x faster** linting and formatting with Ruff
- 🐍 **Python 3.13 & 3.14** support (upgraded from 3.10)
- 🔒 **Security improvements**: Better error handling and logging
- 📦 **Latest dependencies**: All packages updated to latest versions
- 🧪 **Enhanced test coverage**: 17+ new test cases with branch coverage
- 🎯 **Better error messages**: Custom exceptions with detailed information
- 📝 **Comprehensive documentation**: Full docstrings and type hints

See [CHANGELOG.md](CHANGELOG.md) for complete details.

## Migration from v0.1.x

For users, no changes required - the plugin API is unchanged. Simply update your version reference.

For developers:

1. Rebuild Docker containers: `docker compose build`
2. All old linting tools (black, isort, flake8, bandit) have been replaced with Ruff
3. Configuration moved from multiple files to `pyproject.toml`

See the [CHANGELOG.md](CHANGELOG.md#migration-guide) for detailed migration instructions.

## Credits

This plugin was originally written by [Jash Parekh](https://github.com/jashparekh) for Wayfair.
