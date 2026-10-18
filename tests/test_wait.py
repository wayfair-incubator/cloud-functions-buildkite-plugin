"""Tests for waiting on the deployment operation."""

import pytest

from plugin_scripts import deploy
from plugin_scripts.pipeline_exceptions import DeployFailed, MissingConfigError


def _service(mocker, *operations):
    service = mocker.Mock()
    service.operations.return_value.get.return_value.execute.side_effect = list(
        operations
    )
    return service


@pytest.fixture(autouse=True)
def no_sleep(mocker):
    return mocker.patch("plugin_scripts.deploy.time.sleep")


def test_wait_returns_when_the_operation_is_done(mocker, no_sleep):
    service = _service(mocker, {"done": False}, {"done": False}, {"done": True})

    deploy._wait_for_operation(service, "operations/op", timeout=600)

    assert no_sleep.call_count == 2
    service.operations.return_value.get.assert_called_with(name="operations/op")


def test_wait_raises_with_the_error_of_a_failed_operation(mocker):
    service = _service(
        mocker, {"done": True, "error": {"code": 3, "message": "Build failed"}}
    )

    with pytest.raises(DeployFailed, match="Build failed"):
        deploy._wait_for_operation(service, "operations/op", timeout=600)


def test_wait_times_out(mocker):
    service = mocker.Mock()
    service.operations.return_value.get.return_value.execute.return_value = {
        "done": False
    }
    clock = iter([0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    mocker.patch(
        "plugin_scripts.deploy.time.monotonic", side_effect=lambda: next(clock)
    )

    with pytest.raises(DeployFailed, match="Timed out after 10s"):
        deploy._wait_for_operation(service, "operations/op", timeout=10)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, True), ("true", True), ("on", True), ("false", False), ("0", False)],
)
def test_wait_option(monkeypatch, value, expected):
    if value is None:
        monkeypatch.delenv("wait", raising=False)
    else:
        monkeypatch.setenv("wait", value)
    assert deploy._wait_enabled() is expected


def test_wait_timeout_option(monkeypatch):
    monkeypatch.delenv("wait_timeout", raising=False)
    assert deploy._wait_timeout() == deploy.DEFAULT_WAIT_TIMEOUT
    monkeypatch.setenv("wait_timeout", "90")
    assert deploy._wait_timeout() == 90
    monkeypatch.setenv("wait_timeout", "soon")
    with pytest.raises(MissingConfigError):
        deploy._wait_timeout()


def _deploy_with_patch_response(mocker, monkeypatch, wait):
    monkeypatch.setenv("gcp_project", "p")
    monkeypatch.setenv("gcp_region", "r")
    monkeypatch.setenv("cloud_function_name", "f")
    monkeypatch.setenv("wait", wait)
    mock_discovery = mocker.patch("plugin_scripts.deploy.discovery")
    functions = (
        mock_discovery.build.return_value.projects.return_value.locations.return_value
    ).functions.return_value
    functions.get.return_value.execute.return_value = {"sourceArchiveUrl": "gs://b/o"}
    functions.patch.return_value.execute.return_value = {"name": "operations/op"}
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")
    mocker.patch("plugin_scripts.deploy._zip_directory")
    mocker.patch("plugin_scripts.deploy._upload_source_code_using_archive_url")
    return mocker.patch("plugin_scripts.deploy._wait_for_operation")


def test_deploy_waits_by_default(mocker, monkeypatch):
    wait = _deploy_with_patch_response(mocker, monkeypatch, "true")
    deploy._deploy(debug_mode=False)
    assert wait.call_args.args[1] == "operations/op"


def test_deploy_does_not_wait_when_turned_off(mocker, monkeypatch):
    wait = _deploy_with_patch_response(mocker, monkeypatch, "false")
    deploy._deploy(debug_mode=False)
    wait.assert_not_called()


def test_deploy_fails_when_the_operation_fails(mocker, monkeypatch):
    wait = _deploy_with_patch_response(mocker, monkeypatch, "true")
    wait.side_effect = DeployFailed("Build failed")
    with pytest.raises(DeployFailed):
        deploy._deploy(debug_mode=False)
