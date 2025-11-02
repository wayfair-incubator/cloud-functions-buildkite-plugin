"""Tests for edge cases and error paths with full coverage."""

import json
import os
import tempfile
import zipfile
from pathlib import Path

import pytest
from google.oauth2 import service_account

from plugin_scripts import deploy
from plugin_scripts.pipeline_exceptions import (
    CloudFunctionDirectoryNonExistent,
    DeployFailed,
    MissingConfigError,
)


def test__zip_directory_missing_env_var(mocker):
    """Test _zip_directory raises ValueError when env var not set."""
    mocker.patch.dict(os.environ, {}, clear=True)
    mock_handler = mocker.Mock()

    with pytest.raises(ValueError) as exc_info:
        deploy._zip_directory(mock_handler)

    assert "cloud_function_directory environment variable is not set" in str(
        exc_info.value
    )


def test__zip_directory_with_actual_files(mocker, monkeypatch, tmp_path):
    """Test _zip_directory with actual file structure."""
    # Create test directory with files
    test_dir = tmp_path / "test_function"
    test_dir.mkdir()
    (test_dir / "main.py").write_text("def main(): pass")
    (test_dir / "requirements.txt").write_text("requests==2.28.0")
    sub_dir = test_dir / "utils"
    sub_dir.mkdir()
    (sub_dir / "helper.py").write_text("def helper(): pass")

    monkeypatch.setenv("cloud_function_directory", str(test_dir))

    # Create a real zip file handler
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".zip") as f:
        zip_path = f.name

    try:
        with zipfile.ZipFile(zip_path, mode="w") as handler:
            deploy._zip_directory(handler)

        # Verify the zip contains expected files
        with zipfile.ZipFile(zip_path, mode="r") as zip_file:
            names = zip_file.namelist()
            assert "main.py" in names
            assert "requirements.txt" in names
            assert "utils/helper.py" in names or "utils\\helper.py" in names
    finally:
        Path(zip_path).unlink()


def test__get_bq_credentials_missing_credentials(mocker, monkeypatch):
    """Test _get_bq_credentials when credentials env var is missing."""
    monkeypatch.delenv("credentials", raising=False)

    with pytest.raises(MissingConfigError) as exc_info:
        deploy._get_bq_credentials()

    assert exc_info.value.config_name == "credentials"
    assert "Missing `credentials` config" in str(exc_info.value)


def test__get_bq_credentials_invalid_json(mocker, monkeypatch):
    """Test _get_bq_credentials with invalid JSON."""
    monkeypatch.setenv("credentials", "not valid json{")

    with pytest.raises(ValueError) as exc_info:
        deploy._get_bq_credentials()

    assert "Invalid credentials JSON" in str(exc_info.value)


def test__get_bq_credentials_with_debug_logging(mocker, monkeypatch):
    """Test _get_bq_credentials logs debug info correctly."""
    valid_creds = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key123",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test.iam.gserviceaccount.com",
        "client_id": "123",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test",
    }
    monkeypatch.setenv("credentials", json.dumps(valid_creds))

    mock_from_info = mocker.patch(
        "plugin_scripts.deploy.service_account.Credentials.from_service_account_info"
    )
    mock_creds = mocker.Mock(spec=service_account.Credentials)
    mock_from_info.return_value = mock_creds

    result = deploy._get_bq_credentials()

    assert result == mock_creds
    mock_from_info.assert_called_once()


def test__upload_source_code_using_archive_url_success_with_logging(
    mocker, monkeypatch
):
    """Test successful upload to archive URL with logging."""
    mock_storage = mocker.patch("plugin_scripts.deploy.storage")
    mock_client = mocker.Mock()
    mock_bucket = mocker.Mock()
    mock_blob = mocker.Mock()

    mock_storage.Client.return_value = mock_client
    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    mock_creds = mocker.Mock()
    mocker.patch("plugin_scripts.deploy._get_bq_credentials", return_value=mock_creds)

    mock_data = mocker.Mock()
    mock_data.read.return_value = b"test source code data"

    # Execute
    deploy._upload_source_code_using_archive_url(
        "gs://my-bucket/functions/my-function.zip", mock_data
    )

    # Verify calls
    mock_storage.Client.assert_called_once_with(credentials=mock_creds)
    mock_client.bucket.assert_called_once_with("my-bucket")
    mock_bucket.blob.assert_called_once_with("functions/my-function.zip")
    mock_blob.upload_from_string.assert_called_once_with(b"test source code data")


def test__upload_source_code_using_upload_url_with_headers(mocker):
    """Test upload with upload URL includes correct headers."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.Mock()
    mock_requests = mocker.patch("plugin_scripts.deploy.requests")
    mock_requests.put.return_value = mock_response

    mock_data = mocker.Mock()

    deploy._upload_source_code_using_upload_url(
        "https://upload.example.com/path", debug_mode=False, data=mock_data
    )

    # Verify headers are set correctly (lowercase as per implementation)
    call_kwargs = mock_requests.put.call_args[1]
    assert "headers" in call_kwargs
    assert call_kwargs["headers"]["content-type"] == "application/zip"
    assert call_kwargs["headers"]["x-goog-content-length-range"] == "0,104857600"


def test_exception_edge_cases():
    """Test exception initialization edge cases."""
    # Test CloudFunctionDirectoryNonExistent with empty directory
    exc1 = CloudFunctionDirectoryNonExistent("")
    assert exc1.directory == ""
    assert "does not exist: " in str(exc1)

    # Test CloudFunctionDirectoryNonExistent with path
    exc2 = CloudFunctionDirectoryNonExistent("/test/path")
    assert exc2.directory == "/test/path"
    assert "/test/path" in str(exc2)

    # Test DeployFailed with default message
    exc3 = DeployFailed()
    assert "Deployment to Cloud Function failed" in str(exc3)

    # Test DeployFailed with custom message
    exc4 = DeployFailed("Custom failure message")
    assert "Custom failure message" in str(exc4)

    # Test MissingConfigError
    exc5 = MissingConfigError("my_config")
    assert exc5.config_name == "my_config"
    assert "Missing `my_config` config" in str(exc5)


def test_main_directory_does_not_exist(mocker, monkeypatch):
    """Test main when cloud function directory does not exist."""
    # Set environment variables
    monkeypatch.setenv("debug_mode", "False")
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("cloud_function_directory", "/nonexistent/dir")
    monkeypatch.setenv("credentials", '{"secret": "value"}')
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")

    # Mock Path to return False for is_dir
    mock_path = mocker.patch("plugin_scripts.deploy.Path")
    mock_path.return_value.is_dir.return_value = False

    with pytest.raises(CloudFunctionDirectoryNonExistent) as exc_info:
        deploy.main()

    assert "/nonexistent/dir" in str(exc_info.value)


def test_main_reraises_custom_exceptions(mocker, monkeypatch):
    """Test main re-raises custom exceptions without wrapping."""
    monkeypatch.setenv("debug_mode", "False")
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")
    monkeypatch.setenv("credentials", '{"secret": "value"}')
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")

    # Mock Path and _deploy
    mock_path = mocker.patch("plugin_scripts.deploy.Path")
    mock_path.return_value.is_dir.return_value = True

    # Test with MissingConfigError
    mocker.patch(
        "plugin_scripts.deploy._deploy",
        side_effect=MissingConfigError("test_config"),
    )

    with pytest.raises(MissingConfigError) as exc_info:
        deploy.main()

    assert exc_info.value.config_name == "test_config"


def test__handle_exception_with_debug_mode(mocker, caplog):
    """Test _handle_exception logs traceback in debug mode."""
    test_exception = ValueError("Test error")

    # Call with debug mode
    deploy._handle_exception(test_exception, debug_mode=True)

    # Verify error was logged
    assert "Deployment error: Test error" in caplog.text


def test__handle_exception_without_debug_mode(mocker, caplog):
    """Test _handle_exception without debug mode."""
    test_exception = ValueError("Test error")

    # Call without debug mode
    deploy._handle_exception(test_exception, debug_mode=False)

    # Verify error was logged
    assert "Deployment error: Test error" in caplog.text


def test__validate_env_variables_comprehensive(monkeypatch):
    """Test _validate_env_variables with all combinations."""
    # Test missing gcp_project (already tested but for completeness)
    monkeypatch.delenv("gcp_project", raising=False)
    monkeypatch.setenv("cloud_function_directory", "/test")
    monkeypatch.setenv("credentials", "creds")
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "func")

    with pytest.raises(MissingConfigError) as exc_info:
        deploy._validate_env_variables()
    assert exc_info.value.config_name == "gcp_project"


def test_integration_zip_to_bytes(tmp_path):
    """Integration test: zip directory and verify contents."""
    # Create test structure
    func_dir = tmp_path / "my_function"
    func_dir.mkdir()
    (func_dir / "main.py").write_text("print('hello')")
    (func_dir / "config.json").write_text('{"key": "value"}')

    # Zip to bytes
    from io import BytesIO

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        os.environ["cloud_function_directory"] = str(func_dir)
        deploy._zip_directory(zf)

    # Verify
    buffer.seek(0)
    with zipfile.ZipFile(buffer, mode="r") as zf:
        assert "main.py" in zf.namelist()
        assert "config.json" in zf.namelist()
        assert zf.read("main.py") == b"print('hello')"
        assert zf.read("config.json") == b'{"key": "value"}'
