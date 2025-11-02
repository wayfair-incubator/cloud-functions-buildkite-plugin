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

## Secret

This plugin expects `GCP_SERVICE_ACCOUNT` is placed as an environment variable. Make sure to store it [securely](https://buildkite.com/docs/pipelines/secrets)!

```yaml
env:
  gcp_service_account: '{"email": ""}'
```

## Development

This project uses modern Python tooling for fast, efficient development:

- **Python 3.13+**: Latest stable Python versions (3.13 and 3.14 supported)
- **uv**: Fast Python package installer (10-100x faster than pip)
- **Ruff**: Unified linter and formatter (10-100x faster than black/flake8/isort)
- **Docker**: Consistent development environment

### Requirements

- Docker and docker-compose
- Python 3.13 or 3.14 (for local development without Docker)
- [uv](https://github.com/astral-sh/uv) (optional, for local development)

### Quick Start

```bash
# Build the development container (Python 3.13)
docker-compose build

# Or build Python 3.14 container (when Python 3.14 is released)
docker-compose build devbox-py314

# Run all tests and linting
docker-compose run --rm py-test

# Format code automatically
docker-compose run --rm ruff-format

# Run linter with auto-fix
docker-compose run --rm ruff-lint
```

### Testing with Python 3.14

When Python 3.14 is officially released, you can test your code against it:

```bash
# Build Python 3.14 container
docker-compose build devbox-py314

# Run tests in Python 3.14
docker-compose run --rm devbox-py314 pytest

# Open interactive shell with Python 3.14
docker-compose run --rm devbox-py314
```

### Development Commands

#### Testing

```bash
# Run all tests with coverage
docker-compose run --rm py-test

# Run tests with formatting (formats code before running tests)
docker-compose run --rm py-test --format-code

# Run tests locally (requires Python 3.13 and dependencies)
pytest --cov plugin_scripts tests --cov-report html
```

#### Code Quality

```bash
# Format code with Ruff
docker-compose run --rm ruff-format

# Check formatting (without modifying files)
docker-compose run --rm ruff-format-check

# Run linter and auto-fix issues
docker-compose run --rm ruff-lint

# Run linter in check mode (no fixes)
docker-compose run --rm ruff-check

# Run type checking with mypy
docker-compose run --rm mypy
```

#### Dependency Management

```bash
# Lock requirements (creates requirements.lock file)
docker-compose run --rm lock-requirements

# Install dependencies locally with uv (fast!)
uv pip install --system -r requirements.txt -r requirements-test.txt

# Install dependencies locally with pip
pip install -r requirements.txt -r requirements-test.txt
```

#### Interactive Development

```bash
# Start an interactive shell in the container
docker-compose run --rm devbox

# Inside the container, you can:
#   - Run pytest
#   - Run ruff check/format
#   - Run mypy
#   - Debug code
```

### Local Development (without Docker)

If you prefer to develop without Docker:

```bash
# Install uv (https://github.com/astral-sh/uv)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt -r requirements-test.txt

# Run tests
pytest --cov plugin_scripts tests --cov-report html

# Format code
ruff format plugin_scripts tests

# Lint code
ruff check --fix plugin_scripts tests

# Type check
mypy plugin_scripts tests
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
├── requirements.txt        # Production dependencies
├── requirements-test.txt   # Development dependencies
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

To execute tests locally (requires that `docker` and `docker-compose` are installed):

```bash
docker-compose run --rm py-test
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
docker-compose run --rm ruff-format
docker-compose run --rm ruff-lint
```

### Type Checking

This project uses [MyPy](https://mypy-lang.org/) for static type checking. Run type checks with:

```bash
docker-compose run --rm mypy
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

1. Rebuild Docker containers: `docker-compose build`
2. All old linting tools (black, isort, flake8, bandit) have been replaced with Ruff
3. Configuration moved from multiple files to `pyproject.toml`

See the [CHANGELOG.md](CHANGELOG.md#migration-guide) for detailed migration instructions.

## Credits

This plugin was originally written by [Jash Parekh](https://github.com/jashparekh) for Wayfair.
