"""Tests for the plan and validate modes."""

import pytest
from googleapiclient import discovery

from plugin_scripts import annotation, deploy
from plugin_scripts.pipeline_exceptions import DeployFailed
from tests.fakes import FakeHttp

GEN1 = "projects/p/locations/r/functions/f"


@pytest.fixture
def env(monkeypatch, tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.py").write_text("print('hi')")
    (source / "lib.py").write_text("")
    monkeypatch.setenv("gcp_project", "p")
    monkeypatch.setenv("gcp_region", "r")
    monkeypatch.setenv("cloud_function_name", "f")
    monkeypatch.setenv("cloud_function_directory", str(source))
    monkeypatch.setenv("annotation_file", str(tmp_path / "out.html"))
    monkeypatch.delenv("credentials", raising=False)
    monkeypatch.delenv("generation", raising=False)
    return tmp_path


def _read_only_api(mocker, function):
    """An API where only GET works: any write would raise KeyError."""
    http = FakeHttp({("GET", GEN1): function})
    real_build = discovery.build
    mocker.patch(
        "plugin_scripts.deploy.discovery.build",
        side_effect=lambda name, version, credentials: real_build(
            name, version, http=http, static_discovery=True
        ),
    )
    mocker.patch("plugin_scripts.deploy._get_credentials")
    return http


def test_validate_needs_no_credentials_and_makes_no_api_call(mocker, env, monkeypatch):
    monkeypatch.setenv("mode", "validate")
    build = mocker.patch("plugin_scripts.deploy.discovery.build")
    get_credentials = mocker.patch("plugin_scripts.deploy._get_credentials")

    deploy.main()

    build.assert_not_called()
    get_credentials.assert_not_called()
    text = (env / "out.html").read_text()
    assert "valid" in text
    assert "validate (nothing was changed)" in text
    assert "Files that would be uploaded" in text


def test_validate_fails_without_files(mocker, env, monkeypatch):
    monkeypatch.setenv("mode", "validate")
    monkeypatch.setenv("exclude_patterns", "*.py")
    with pytest.raises(DeployFailed):
        deploy.main()


def test_validate_fails_for_an_empty_directory(env, monkeypatch):
    monkeypatch.setenv("mode", "validate")
    empty = env / "empty"
    empty.mkdir()
    monkeypatch.setenv("cloud_function_directory", str(empty))
    with pytest.raises(DeployFailed, match="no files"):
        deploy.main()


def test_validate_rejects_a_missing_directory(env, monkeypatch):
    monkeypatch.setenv("mode", "validate")
    monkeypatch.setenv("cloud_function_directory", str(env / "nope"))
    with pytest.raises(deploy.CloudFunctionDirectoryNonExistent):
        deploy.main()


def test_validate_rejects_a_too_big_first_generation_archive(mocker, env, monkeypatch):
    monkeypatch.setenv("mode", "validate")
    monkeypatch.setattr(deploy, "_MAX_ARCHIVE_BYTES_GEN1", 1)
    with pytest.raises(DeployFailed, match="at most"):
        deploy.main()


def test_validate_does_not_apply_the_first_generation_limit_to_gen2(env, monkeypatch):
    monkeypatch.setenv("mode", "validate")
    monkeypatch.setenv("generation", "2")
    monkeypatch.setattr(deploy, "_MAX_ARCHIVE_BYTES_GEN1", 1)
    deploy.main()


def test_plan_gen1_only_reads(mocker, env, monkeypatch, caplog):
    monkeypatch.setenv("mode", "plan")
    http = _read_only_api(
        mocker,
        {
            "name": GEN1,
            "status": "ACTIVE",
            "runtime": "python311",
            "sourceUploadUrl": "https://storage/old",
        },
    )
    put = mocker.patch("plugin_scripts.deploy.requests.put")

    with caplog.at_level("INFO", logger="cloud-function"):
        deploy.main()

    assert [c[0] for c in http.calls] == ["GET"]
    put.assert_not_called()
    assert "would upload 2 files" in caplog.text
    assert "python311" in caplog.text
    assert "main.py" in caplog.text
    text = (env / "out.html").read_text()
    assert "planned" in text
    assert "python311" in text


def test_plan_gen2_only_reads(mocker, env, monkeypatch):
    monkeypatch.setenv("mode", "plan")
    monkeypatch.setenv("generation", "2")
    http = _read_only_api(
        mocker,
        {
            "name": GEN1,
            "state": "ACTIVE",
            "buildConfig": {"runtime": "nodejs22", "source": {"storageSource": {}}},
        },
    )

    deploy.main()

    assert [c[0] for c in http.calls] == ["GET"]


def test_plan_gen2_rejects_a_gen1_function(mocker, env, monkeypatch):
    monkeypatch.setenv("mode", "plan")
    monkeypatch.setenv("generation", "2")
    _read_only_api(mocker, {"name": GEN1, "environment": "GEN_1"})
    with pytest.raises(DeployFailed, match="1st generation"):
        deploy.main()


def test_plan_function_not_found(mocker, env, monkeypatch):
    monkeypatch.setenv("mode", "plan")
    mocker.patch("plugin_scripts.deploy._get_credentials", side_effect=ValueError("x"))
    with pytest.raises(DeployFailed, match="not found"):
        deploy.main()


def test_plan_lists_at_most_200_files(mocker, env, monkeypatch, caplog):
    monkeypatch.setenv("mode", "plan")
    _read_only_api(mocker, {"name": GEN1})
    src = env / "src"
    for i in range(205):
        (src / f"f{i:03}.py").write_text("")

    with caplog.at_level("INFO", logger="cloud-function"):
        deploy.main()

    assert "... and 7 more" in caplog.text


def test_unknown_mode_fails(env, monkeypatch):
    monkeypatch.setenv("mode", "destroy")
    with pytest.raises(DeployFailed, match="Unknown mode"):
        deploy.main()


def test_annotation_wording_for_modes():
    base = {"function": "f", "project": "p", "region": "r", "generation": "1"}
    assert "planned" in annotation.render({**base, "mode": "plan"})
    assert "deployed" in annotation.render({**base, "mode": "apply"})
    assert "Waited" not in annotation.render({**base, "mode": "plan"})
    assert "failed" in annotation.render({**base, "mode": "plan", "error": "x"})
