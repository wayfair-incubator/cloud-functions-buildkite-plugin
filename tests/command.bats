#!/usr/bin/env bats

# Tests for hooks/command. `docker` is replaced by a stub that records its
# arguments, so nothing is pulled or run. Only needs bats-core.

setup() {
  TEST_DIR="$(mktemp -d)"
  HOOK="${BATS_TEST_DIRNAME}/../hooks/command"
  STUB_BIN="${TEST_DIR}/bin"
  export DOCKER_LOG="${TEST_DIR}/docker.log"
  mkdir -p "${STUB_BIN}" "${TEST_DIR}/repo"

  cat >"${STUB_BIN}/docker" <<'STUB'
#!/bin/bash
printf '%s\n' "$*" >>"${DOCKER_LOG}"
case "$1" in
  pull)
    exit "${STUB_PULL_RC:-0}"
    ;;
  create)
    printf '%s\n' "$@" >"${DOCKER_LOG}.create"
    printf 'credentials_in_env=%s\n' "${credentials:-}" >"${DOCKER_LOG}.env"
    echo fakecontainer
    ;;
  cp)
    exit "${STUB_CP_RC:-0}"
    ;;
  start)
    exit "${STUB_START_RC:-0}"
    ;;
esac
STUB
  chmod +x "${STUB_BIN}/docker"

  cd "${TEST_DIR}/repo"
  export PATH="${STUB_BIN}:${PATH}"
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_GCP_PROJECT="my-project"
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_GCP_REGION="us-central1"
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_CLOUD_FUNCTION_NAME="my-function"
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_CLOUD_FUNCTION_DIRECTORY="src"
  export gcp_service_account='{"private_key": "TOP-SECRET-KEY"}'
}

teardown() {
  cd /
  rm -rf "${TEST_DIR}"
}

@test "service account key never appears in the docker create arguments" {
  run "${HOOK}"
  [ "$status" -eq 0 ]
  ! grep -q "TOP-SECRET-KEY" "${DOCKER_LOG}.create"
  ! grep -q "TOP-SECRET-KEY" "${DOCKER_LOG}"
  grep -qx -- "credentials" "${DOCKER_LOG}.create"
  grep -q "TOP-SECRET-KEY" "${DOCKER_LOG}.env"
}

@test "service account can come from the plugin option" {
  unset gcp_service_account
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_GCP_SERVICE_ACCOUNT='{"private_key": "OPTION-KEY"}'
  run "${HOOK}"
  [ "$status" -eq 0 ]
  grep -q "OPTION-KEY" "${DOCKER_LOG}.env"
  ! grep -q "OPTION-KEY" "${DOCKER_LOG}.create"
}

@test "the job environment, agent token and agent binary are not given to the container" {
  printf 'AWS_SECRET_ACCESS_KEY=zzz\n' >"${TEST_DIR}/env"
  export BUILDKITE_ENV_FILE="${TEST_DIR}/env"
  export BUILDKITE_AGENT_ACCESS_TOKEN="agent-token"
  export HTTPS_PROXY="http://proxy:3128"
  run "${HOOK}"
  [ "$status" -eq 0 ]
  ! grep -q "AWS_SECRET_ACCESS_KEY" "${DOCKER_LOG}.create"
  ! grep -q "BUILDKITE_AGENT_ACCESS_TOKEN" "${DOCKER_LOG}.create"
  ! grep -q "buildkite-agent" "${DOCKER_LOG}.create"
  ! grep -qx -- "--volume" "${DOCKER_LOG}.create"
  grep -qx -- "HTTPS_PROXY" "${DOCKER_LOG}.create"
}

@test "missing options give a readable error, not an unbound variable" {
  for option in GCP_PROJECT GCP_REGION CLOUD_FUNCTION_NAME CLOUD_FUNCTION_DIRECTORY; do
    (
      unset "BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_${option}"
      run "${HOOK}"
      [ "$status" -eq 1 ]
      [[ $output == *"ERROR:"* ]]
      [[ $output != *"unbound variable"* ]]
    )
  done
}

@test "without a key and without a credentials file, Application Default Credentials are used" {
  unset gcp_service_account
  run "${HOOK}"
  [ "$status" -eq 0 ]
  [[ $output == *"Application Default Credentials"* ]]
  ! grep -qx -- "credentials" "${DOCKER_LOG}.create"
  ! grep -qx -- "--volume" "${DOCKER_LOG}.create"
}

@test "GOOGLE_APPLICATION_CREDENTIALS is mounted read-only when there is no key" {
  unset gcp_service_account
  echo '{}' >"${TEST_DIR}/adc.json"
  export GOOGLE_APPLICATION_CREDENTIALS="${TEST_DIR}/adc.json"
  run "${HOOK}"
  [ "$status" -eq 0 ]
  grep -qx -- "${TEST_DIR}/adc.json:/run/secrets/google-adc.json:ro" "${DOCKER_LOG}.create"
  grep -qx -- "GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/google-adc.json" "${DOCKER_LOG}.create"
}

@test "a GOOGLE_APPLICATION_CREDENTIALS file that does not exist is an error" {
  unset gcp_service_account
  export GOOGLE_APPLICATION_CREDENTIALS="${TEST_DIR}/missing.json"
  run "${HOOK}"
  [ "$status" -eq 1 ]
  [[ $output == *"does not exist"* ]]
}

@test "the key wins over GOOGLE_APPLICATION_CREDENTIALS and nothing is mounted" {
  echo '{}' >"${TEST_DIR}/adc.json"
  export GOOGLE_APPLICATION_CREDENTIALS="${TEST_DIR}/adc.json"
  run "${HOOK}"
  [ "$status" -eq 0 ]
  grep -qx -- "credentials" "${DOCKER_LOG}.create"
  ! grep -qx -- "--volume" "${DOCKER_LOG}.create"
}

@test "a failed docker pull fails the step" {
  export STUB_PULL_RC=7
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_DOCKER_PULL_RETRIES=1
  run "${HOOK}"
  [ "$status" -eq 7 ]
  ! grep -q "^create" "${DOCKER_LOG}"
}

@test "the container is removed when docker cp fails" {
  export STUB_CP_RC=1
  run "${HOOK}"
  [ "$status" -eq 1 ]
  grep -q "^rm -f fakecontainer" "${DOCKER_LOG}"
}

@test "the container is removed and its exit code is kept after a failed deploy" {
  export STUB_START_RC=3
  run "${HOOK}"
  [ "$status" -eq 3 ]
  grep -q "^rm -f fakecontainer" "${DOCKER_LOG}"
}

@test "custom image is used and uv is pinned" {
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_CUSTOM_IMAGE="python:3.12-slim"
  run "${HOOK}"
  [ "$status" -eq 0 ]
  grep -qx -- "python:3.12-slim" "${DOCKER_LOG}.create"
  grep -q "uv==[0-9]" "${DOCKER_LOG}.create"
  grep -q -- "--require-hashes" "${DOCKER_LOG}.create"
}

@test "the default image is python 3.15" {
  run "${HOOK}"
  [ "$status" -eq 0 ]
  grep -qx -- "python:3.15-slim" "${DOCKER_LOG}.create"
}

@test "waiting for the deployment is on by default with a 600s timeout" {
  run "${HOOK}"
  [ "$status" -eq 0 ]
  grep -qx -- "wait=true" "${DOCKER_LOG}.create"
  grep -qx -- "wait_timeout=600" "${DOCKER_LOG}.create"
}

@test "wait and wait_timeout are passed to the container" {
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_WAIT=false
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_WAIT_TIMEOUT=90
  run "${HOOK}"
  [ "$status" -eq 0 ]
  grep -qx -- "wait=false" "${DOCKER_LOG}.create"
  grep -qx -- "wait_timeout=90" "${DOCKER_LOG}.create"
}

@test "a wait_timeout that is not a number is rejected" {
  export BUILDKITE_PLUGIN_CLOUD_FUNCTIONS_WAIT_TIMEOUT=soon
  run "${HOOK}"
  [ "$status" -eq 1 ]
  [[ $output == *"wait_timeout must be a number"* ]]
}
