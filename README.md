[![Actions Status](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/workflows/Lint/badge.svg?branch=main)](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/actions)
[![Actions Status](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/workflows/Unit%20Tests/badge.svg?branch=main)](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/actions)
![Version](https://img.shields.io/static/v1.svg?label=Version&message=1.0.0&color=lightgrey&?link=http://left&link=https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/tree/v1.0.0)
![Plugin Status](https://img.shields.io/static/v1.svg?label=&message=Buildkite%20Plugin&color=blue&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAMAAADVRocKAAAAk1BMVEX///+DrRik1Cb+/vyErhin1yeAqhfJ5n+dzCO50X2VwiC2zna020vg8LSo1i+q1zTN3qL7/fav2UDT4q33++yXuj3z+eLO6IqMuByJsSPM54XX5bWcvUbH5Xrg6sWiwVHB1ovk7cymxFnq8deOtC2xzG7c6L6/1YfU7JbI2pj2+e+jzzPd763K3J3j8ryRtDbY7aOqCe3pAAACTElEQVRoge3Z11KDQBSAYUpItSRqVGwxEVOwxPd/OndhCbA5BTaLM87sueb83+yMStHz3Lhx48bN/5iw+2VjImy0fDvzQiNCLKVrdjn0nq++QwNCLMy+9uOzc2Y59AZBwF4F55NefxxxyxK4aEvI/C7x/QxglrMTBNxVej6V+QNALh+AhkRY5isAsVwBxFWfM/rnLsu/qnwNQIkawBBy/abMawBCaEAQXGFElt/Evo8CIHEEIESWH9XyAAAQACCIH40A8yBwRICARiB5BNAIBKgQ8tLbCZBHgRqBAgWB5wmgQhCAIt7ekTwJ5AQHSGKC1TkgiM7WIs8A0bBvCETR8H7CA4EhIPP9fgPA7AR53u91BBR53+8EKPPdACLvq3wXQC1vH9DytoGjvF0gGo71vE0gCoC8PQDJ2wJEvgfmbQFo3g5A5HNA3K+eL0yBePdO5AtAEAOUoIB4c+ONiHwBZHddjMCB5DUV6yOqfzgBQWCAzMu9ZoAiHgACBpJdmj3SNAdQAgKSXfFQ1gZQz28PlxxQ5tsCIKED+6/qU2tbQBF3lxgwn9YfitsDR0QVmE9D7bHeBNCIEphf63lToEYUAJQ3BxSxlUQGPD3Cr5DmwIGQJ8DypwHqlXX7gec5oMcAXv5OT31OYU6weuM/9tDv/iSwWnJxfghA5s0+QzUCFi828iiwWNvJI4C9PAg8WcwDAPVLYwGwndeAufV8DZB/bm3nK0A3+RyI81tdF3l1gn1neQlM4qnpp+9ms0xP/P8AP/8778aNGzdu/mh+AQp1NCB/JInXAAAAAElFTkSuQmCC)

# Cloud Functions Buildkite Plugin

This buildkite plugin deploys code to an existing [Cloud Functions](https://cloud.google.com/functions) function.

It zips `cloud_function_directory`, uploads the archive and updates the function through the Cloud Functions **v1 API**, so by default it manages **1st generation** functions that already exist (`generation: 2` switches to the v2 API for 2nd generation / Cloud Run functions). It does not create functions and does not change their runtime, entry point, environment variables or any other settings: only the source code is replaced. The work happens in a Docker container (`python:3.15-slim` by default) that installs a hash-locked set of Google client libraries (from `uv.lock`) with uv, so agents need Docker and network access.

See the [plugin tester](https://github.com/buildkite-plugins/buildkite-plugin-tester) for testing examples and usage, and the [Buildkite docs on writing plugins](https://buildkite.com/docs/plugins/writing) to understand everything in this repo.

## Using the plugin

If the version number is not provided then the most recent version of the plugin will be used. Do not use version number as `main` or any branch name.

### Simple

```yaml
steps:
  - plugins:
      - wayfair-incubator/cloud-functions#v1.0.0:
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

### `mode` (optional, string)

- `apply` (default): deploy.
- `plan`: show what a deployment would do and change nothing. It reads the function (current state, runtime and source) with your credentials, builds the archive and logs the files that would be uploaded and its size. It does not generate an upload URL, upload or patch anything, so it is safe to run on pull requests with a read-only identity (for example `roles/cloudfunctions.viewer`).
- `validate`: check the options and the archive offline, with no credentials and no API calls: the directory exists, `exclude` leaves files, and (for 1st generation) the archive is under the 100 MiB upload limit.

```yaml
          mode: plan
```

With `annotate`, the annotation says which mode ran.

### `annotate` (optional, boolean)

Add a Buildkite annotation that summarises the deployment: function, project, region, generation, number and size of the uploaded files, operation name, whether it waited, time taken and, on failure, the error (an error annotation). It is created by the hook on the agent after the run, so the container never gets the agent or its token, and a problem creating it never changes the step's result. Default: `false`.

### `annotation_context` (optional, string)

Context of the annotation, so several deployments in one build each keep their own. Default: `cloud-functions-<cloud_function_name>`.

### `exclude` (optional, array of strings)

Shell-style globs, relative to `cloud_function_directory`, of files that are not uploaded, in addition to the [built-in exclusions](#what-is-uploaded). A pattern that matches a directory excludes everything inside it, and `*` also matches `/`. The step fails if every file ends up excluded.

```yaml
          exclude:
            - "tests"
            - "docs"
            - "*.md"
```

### `generation` (optional, integer)

`1` (default) updates a 1st generation function through the Cloud Functions v1 API. `2` updates a 2nd generation function (a Cloud Run function) through the v2 API: the archive is uploaded to a signed URL and only the function's source location (`buildConfig.source.storageSource`) is changed, so runtime, entry point, environment variables and every other setting stay as they are. Using the wrong value fails with a clear error (the plugin checks the function's generation).

```yaml
          generation: 2
```

### `wait` (optional, boolean)

Wait for the deployment to finish and fail the step if it fails. Updating a function only starts a
long-running operation (build, rollout); with `wait: false` the step succeeds as soon as the update was
accepted (the behaviour before this option existed). Default: `true`.

### `wait_timeout` (optional, integer)

Seconds to wait for the deployment to finish. The step fails when it takes longer (the deployment
may still complete). Default: `600`.

### `custom_image` (optional, string)

Docker image the deployment runs in. It needs Python 3.11 or newer and network access to PyPI. Default: `python:3.15-slim`.

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
      - wayfair-incubator/cloud-functions#v1.0.0:
          gcp_project: "gcp-us-project"
          gcp_region: "us-central1"
          cloud_function_name: "function-1"
          cloud_function_directory: "directory/function-code"
          gcp_service_account: "${GCP_SA_KEY}" # or set a gcp_service_account env var
```

**Application Default Credentials**, when no key is given: the identity of the agent's machine (GCE/GKE metadata server, Workload Identity), or the credentials file named by `GOOGLE_APPLICATION_CREDENTIALS` on the agent, which is mounted read-only into the container. No long-lived key has to be stored in Buildkite. The identity needs permission to update the function (for example `roles/cloudfunctions.developer`) and to act as its runtime service account. A federated (`external_account`) credentials file that points at other files, such as a token file, will not find them inside the container; use the metadata server in that case.

The key is handed to the container by variable name only, so it never appears on a command line. The container does not receive the rest of the job environment (only the proxy variables `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` and their lowercase forms, when set).

## What is uploaded

Everything in `cloud_function_directory` except `.git`, `node_modules`, `__pycache__`, `*.pyc`, `.env`, `.env.*` and `.DS_Store`, and anything matched by the [`exclude`](#exclude-optional-array-of-strings) option. The log lists the patterns and how many files were excluded.

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

# Add or change a dependency, then refresh uv.lock
docker compose run --rm lock-requirements          # or: uv lock
docker compose run --rm lock-requirements --upgrade # move every pin to its latest release
```

`uv.lock` is the only lock file: the deploy container exports its hashed requirements from it when it runs. CI fails when it is out of date.

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
├── hooks/command            # The plugin: starts the deploy container
├── plugin.yml               # Options (checked by the plugin linter)
├── plugin_scripts/          # Code that runs inside the container
│   ├── deploy.py            # Deployment logic
│   ├── pipeline_exceptions.py
├── tests/                   # pytest for plugin_scripts, bats for the hook and scripts
├── docker/                  # Devbox, shfmt image, test and lock scripts
├── .github/                 # Workflows and the changelog script (releases)
├── pyproject.toml           # Dependencies and the Ruff, mypy and pytest settings
├── uv.lock                  # Locked dependencies (all platforms)
└── renovate.json            # Dependency updates
```

## Contributing

See the [Contributing Guide](CONTRIBUTING.md) for additional information.

### Running Tests Locally

Requires `docker` and Docker Compose:

```bash
docker compose run --rm py-test   # pytest, mypy and Ruff
docker compose run --rm test      # bats tests of the hook and scripts
docker compose run --rm lint      # Buildkite plugin linter
docker compose run --rm shfmt     # shell formatting of hooks/ and .github/scripts
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

## Upgrading to 1.0.0

Pipelines that only set the four required options and a `gcp_service_account` keep working. Things that behave differently:

- **The deployment is waited for.** A failed build or rollout now fails the step. Set `wait: false` for the old behaviour, or `wait_timeout` to change the 600 seconds.
- **The container no longer receives the job environment**, the agent token or the `buildkite-agent` binary; only proxy variables are forwarded. If your function directory relied on a variable being present in the container, it never reached the deployed function anyway (only the zip is uploaded).
- **The archive excludes `.git`, `node_modules`, `__pycache__`, `*.pyc`, `.env`, `.env.*` and `.DS_Store`.**
- **The default image is `python:3.15-slim`** (was `python:3.13-slim`). Use `custom_image: python:3.13-slim` to keep the old one; Python 3.11 or newer is required.
- `gcp_service_account` is optional now and can be a plugin option; without it Application Default Credentials are used.

See [CHANGELOG.md](CHANGELOG.md) for every change.

## Credits

This plugin was originally written by [Jash Parekh](https://github.com/jashparekh) for Wayfair.
