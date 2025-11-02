set -euo pipefail

echo "Installing uv package manager"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

if [[ "${INSTALL_REQUIREMENTS}" == "true"  ]]; then
  echo "Installing code requirements with uv"
  uv pip install --system -r requirements.txt
fi

if [[ "${INSTALL_TEST_REQUIREMENTS}" == "true"  ]]; then
  echo "Installing test requirements with uv"
  uv pip install --system -r requirements-test.txt
fi
