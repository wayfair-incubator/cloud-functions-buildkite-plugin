#!/usr/bin/env bash

set -eo pipefail

RUFF_FIX=""

function usage
{
    echo "usage: run_tests.sh [--format-code]"
    echo ""
    echo " --format-code : Format the code instead of checking formatting."
    exit 1
}

while [[ $# -gt 0 ]]; do
    arg="$1"
    case $arg in
        --format-code)
        RUFF_FIX="--fix"
        ;;
        -h|--help)
        usage
        ;;
        "")
        # ignore
        ;;
        *)
        echo "Unexpected argument: ${arg}"
        usage
        ;;
    esac
    shift
done

# Run tests with coverage
echo "Running tests with pytest..."
pytest --cov plugin_scripts/ tests --cov-report html

# Run type checking
echo "Running MyPy..."
mypy plugin_scripts tests

# Run linting and formatting with Ruff
echo "Running Ruff linter..."
if [ -n "$RUFF_FIX" ]; then
    echo "Formatting code with Ruff..."
    ruff format plugin_scripts tests
    ruff check --fix plugin_scripts tests
else
    echo "Checking code formatting with Ruff..."
    ruff format --check plugin_scripts tests
    ruff check plugin_scripts tests
fi

echo "All checks passed!"
