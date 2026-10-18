"""Tests for the Buildkite annotation."""

import pytest

from plugin_scripts import annotation, deploy
from plugin_scripts.pipeline_exceptions import DeployFailed


def test_render_success():
    html = annotation.render(
        {
            "function": "f",
            "project": "p",
            "region": "r",
            "generation": "2",
            "files": 3,
            "excluded": 1,
            "bytes": 2048,
            "operation": "operations/op",
            "wait": True,
            "seconds": 12.4,
        }
    )
    assert ":white_check_mark:" in html
    assert "deployed" in html
    assert "3 (1 excluded)" in html
    assert "2.0 KiB" in html
    assert "operations/op" in html
    assert "12s" in html
    assert "<pre>" not in html


def test_render_failure_escapes_everything():
    html = annotation.render(
        {
            "function": "<script>f</script>",
            "project": "p",
            "region": "r",
            "generation": "1",
            "wait": False,
            "error": "boom <img src=x onerror=alert(1)>",
        }
    )
    assert ":x:" in html
    assert "failed" in html
    assert "<script>" not in html
    assert "<img" not in html
    assert "&lt;img" in html
    assert "<pre>" in html


def test_write_ignores_unwritable_path(tmp_path):
    annotation.write(str(tmp_path / "missing" / "a.html"), {})


def test_annotation_path(monkeypatch):
    monkeypatch.delenv("annotation_file", raising=False)
    assert annotation.annotation_path() is None
    monkeypatch.setenv("annotation_file", "a.html")
    assert annotation.annotation_path() == "a.html"


@pytest.fixture
def env(monkeypatch, tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.py").write_text("")
    monkeypatch.setenv("gcp_project", "p")
    monkeypatch.setenv("gcp_region", "r")
    monkeypatch.setenv("cloud_function_name", "f")
    monkeypatch.setenv("cloud_function_directory", str(source))
    monkeypatch.setenv("annotation_file", str(tmp_path / "out.html"))
    return tmp_path / "out.html"


def test_main_writes_the_annotation_on_success(mocker, env):
    def fake_deploy(debug_mode):
        deploy._report["operation"] = "operations/op"

    mocker.patch("plugin_scripts.deploy._deploy", side_effect=fake_deploy)

    deploy.main()

    text = env.read_text()
    assert "deployed" in text
    assert "operations/op" in text


def test_main_writes_the_annotation_on_failure(mocker, env):
    mocker.patch(
        "plugin_scripts.deploy._deploy", side_effect=DeployFailed("Build failed")
    )

    with pytest.raises(DeployFailed):
        deploy.main()

    text = env.read_text()
    assert "failed" in text
    assert "Build failed" in text


def test_main_without_annotation_file_writes_nothing(mocker, env, monkeypatch):
    monkeypatch.delenv("annotation_file")
    mocker.patch("plugin_scripts.deploy._deploy")
    deploy.main()
    assert not env.exists()
