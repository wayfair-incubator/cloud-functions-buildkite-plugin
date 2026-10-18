"""Tests for deploying 2nd generation functions (Cloud Functions v2 API).

The Google API client is real (built from its bundled discovery document) and only
the HTTP transport is faked, so the requests that would be sent are checked.
"""

import pytest
from googleapiclient import discovery

from plugin_scripts import deploy
from plugin_scripts.pipeline_exceptions import DeployFailed
from tests.fakes import FakeHttp

FUNCTION = "projects/p/locations/r/functions/f"
STORAGE_SOURCE = {"bucket": "upload-bucket", "object": "src.zip", "generation": "0"}


def _fail(message):
    def raiser():
        raise RuntimeError(message)

    return raiser


@pytest.fixture
def gen2_env(monkeypatch, tmp_path):
    (tmp_path / "main.py").write_text("")
    monkeypatch.setenv("gcp_project", "p")
    monkeypatch.setenv("gcp_region", "r")
    monkeypatch.setenv("cloud_function_name", "f")
    monkeypatch.setenv("cloud_function_directory", str(tmp_path))
    monkeypatch.setenv("generation", "2")
    monkeypatch.setenv("wait_timeout", "60")
    monkeypatch.delenv("wait", raising=False)


def _wire(mocker, responses):
    http = FakeHttp(responses)
    real_build = discovery.build
    mocker.patch(
        "plugin_scripts.deploy.discovery.build",
        side_effect=lambda name, version, credentials: real_build(
            name, version, http=http, static_discovery=True
        ),
    )
    mocker.patch("plugin_scripts.deploy._get_credentials")
    mocker.patch("plugin_scripts.deploy.time.sleep")
    return http


def _responses(function=None, operation=None):
    return {
        ("GET", f"{FUNCTION}"): function or {"name": FUNCTION, "state": "ACTIVE"},
        ("POST", "projects/p/locations/r/functions:generateUploadUrl"): {
            "uploadUrl": "https://storage.example/upload?sig=1",
            "storageSource": STORAGE_SOURCE,
        },
        ("PATCH", FUNCTION): {"name": "projects/p/locations/r/operations/op1"},
        ("GET", "projects/p/locations/r/operations/op1"): operation or {"done": True},
    }


def test_gen2_uploads_the_zip_and_patches_only_the_source(mocker, gen2_env):
    http = _wire(mocker, _responses())
    put = mocker.patch("plugin_scripts.deploy.requests.put")

    deploy._deploy(debug_mode=False)

    # signed URL upload: zip content type, no 1st gen size header
    assert put.call_args.args[0] == "https://storage.example/upload?sig=1"
    assert put.call_args.kwargs["headers"] == {"content-type": "application/zip"}

    patch = next(c for c in http.calls if c[0] == "PATCH")
    assert patch[2]["updateMask"] == ["buildConfig.source.storageSource"]
    assert patch[3] == {"buildConfig": {"source": {"storageSource": STORAGE_SOURCE}}}

    upload_call = next(c for c in http.calls if c[1].endswith(":generateUploadUrl"))
    assert upload_call[3] == {"environment": "GEN_2"}
    # waited for the operation
    assert http.calls[-1][1].endswith("/operations/op1")


def test_gen2_fails_when_the_operation_fails(mocker, gen2_env):
    _wire(
        mocker,
        _responses(operation={"done": True, "error": {"message": "Build failed"}}),
    )
    mocker.patch("plugin_scripts.deploy.requests.put")

    with pytest.raises(DeployFailed, match="Deployment failed"):
        deploy._deploy(debug_mode=False)


def test_gen2_does_not_wait_when_turned_off(mocker, gen2_env, monkeypatch):
    monkeypatch.setenv("wait", "false")
    http = _wire(mocker, _responses())
    mocker.patch("plugin_scripts.deploy.requests.put")

    deploy._deploy(debug_mode=False)

    assert not any("/operations/" in c[1] for c in http.calls)


def test_gen2_rejects_a_first_generation_function(mocker, gen2_env):
    _wire(mocker, _responses(function={"name": FUNCTION, "environment": "GEN_1"}))
    put = mocker.patch("plugin_scripts.deploy.requests.put")

    with pytest.raises(DeployFailed):
        deploy._deploy(debug_mode=False)
    put.assert_not_called()


def test_gen2_function_not_found(mocker, gen2_env):
    http = _wire(mocker, {})
    http.responses[("GET", FUNCTION)] = _fail("404")

    with pytest.raises(DeployFailed):
        deploy._deploy(debug_mode=False)


def test_gen2_upload_url_generation_fails(mocker, gen2_env):
    responses = _responses()
    responses[("POST", "projects/p/locations/r/functions:generateUploadUrl")] = _fail(
        "denied"
    )
    _wire(mocker, responses)

    with pytest.raises(DeployFailed):
        deploy._deploy(debug_mode=False)


def test_gen2_debug_mode_logs_a_summary_only(mocker, gen2_env):
    _wire(
        mocker,
        _responses(
            function={
                "name": FUNCTION,
                "state": "ACTIVE",
                "serviceConfig": {"environmentVariables": {"SECRET": "hunter2"}},
            }
        ),
    )
    mocker.patch("plugin_scripts.deploy.requests.put")
    debug = mocker.patch.object(deploy._logger, "debug")

    deploy._deploy(debug_mode=True)

    logged = " ".join(str(c) for c in debug.call_args_list)
    assert "ACTIVE" in logged
    assert "hunter2" not in logged


def test_generation_one_is_the_default(mocker, monkeypatch):
    monkeypatch.delenv("generation", raising=False)
    gen1 = mocker.patch("plugin_scripts.deploy._deploy_gen1")
    gen2 = mocker.patch("plugin_scripts.deploy._deploy_gen2")

    deploy._deploy(debug_mode=False)

    gen1.assert_called_once()
    gen2.assert_not_called()
