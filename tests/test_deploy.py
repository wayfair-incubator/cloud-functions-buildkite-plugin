"""Tests for the deploy module."""

import pytest

from plugin_scripts import deploy
from plugin_scripts.pipeline_exceptions import (
    CloudFunctionDirectoryNonExistent,
    DeployFailed,
    MissingConfigError,
)


@pytest.fixture
def debug_mode(monkeypatch):
    """Set debug_mode environment variable."""
    return monkeypatch.setenv("debug_mode", "false")


@pytest.fixture
def cloud_function_directory(monkeypatch):
    """Set cloud_function_directory environment variable."""
    return monkeypatch.setenv("cloud_function_directory", "schemas/project")


@pytest.fixture
def cloud_function_name(monkeypatch):
    """Set cloud_function_name environment variable."""
    return monkeypatch.setenv("cloud_function_name", "cloud_function_name")


@pytest.fixture
def gcp_project(monkeypatch):
    """Set gcp_project environment variable."""
    return monkeypatch.setenv("gcp_project", "gcp_project")


@pytest.fixture
def gcp_region(monkeypatch):
    """Set gcp_region environment variable."""
    return monkeypatch.setenv("gcp_region", "gcp_region")


@pytest.fixture
def credentials(monkeypatch):
    """Set credentials environment variable."""
    return monkeypatch.setenv("credentials", '{"secret": "value"}')


def test__validate_env_variables_missing_cloud_function_directory(
    monkeypatch, gcp_project, credentials, gcp_region, cloud_function_name
):
    """Test validation fails when cloud_function_directory is missing."""
    # Explicitly remove the cloud_function_directory
    monkeypatch.delenv("cloud_function_directory", raising=False)

    with pytest.raises(MissingConfigError) as exec_info:
        deploy._validate_env_variables()
    assert exec_info.value.config_name == "cloud_function_directory"


def test__validate_env_variables_missing_cloud_function_name(
    gcp_project, credentials, gcp_region, cloud_function_directory
):
    """Test validation fails when cloud_function_name is missing."""
    with pytest.raises(MissingConfigError) as exec_info:
        deploy._validate_env_variables()
    assert exec_info.value.config_name == "cloud_function_name"


def test__validate_env_variables_missing_gcp_project(
    cloud_function_directory, credentials, gcp_region, cloud_function_name
):
    """Test validation fails when gcp_project is missing."""
    with pytest.raises(MissingConfigError) as exec_info:
        deploy._validate_env_variables()
    assert exec_info.value.config_name == "gcp_project"


def test__validate_env_variables_missing_gcp_region(
    cloud_function_directory, credentials, gcp_project, cloud_function_name
):
    """Test validation fails when gcp_region is missing."""
    with pytest.raises(MissingConfigError) as exec_info:
        deploy._validate_env_variables()
    assert exec_info.value.config_name == "gcp_region"


def test__validate_env_variables_missing_credentials(
    gcp_project, cloud_function_directory, gcp_region, cloud_function_name
):
    """Test validation fails when credentials are missing."""
    with pytest.raises(MissingConfigError) as exec_info:
        deploy._validate_env_variables()
    assert exec_info.value.config_name == "credentials"


def test__validate_env_variables_all_variables_present(
    gcp_project, cloud_function_directory, credentials, gcp_region, cloud_function_name
):
    """Test validation passes when all variables are present."""
    deploy._validate_env_variables()
    # No exception should be raised


def test__validate_if_path_exists_true(mocker, cloud_function_directory):
    """Test path validation returns True when directory exists."""
    mock_path = mocker.patch("plugin_scripts.deploy.Path")
    mock_path.return_value.is_dir.return_value = True
    assert deploy._validate_if_path_exists()


def test__validate_if_path_exists_false(mocker, cloud_function_directory):
    """Test path validation returns False when directory does not exist."""
    mock_path = mocker.patch("plugin_scripts.deploy.Path")
    mock_path.return_value.is_dir.return_value = False
    assert not deploy._validate_if_path_exists()


def test__validate_if_path_exists_no_env_var(mocker, monkeypatch):
    """Test path validation returns False when env var is not set."""
    monkeypatch.delenv("cloud_function_directory", raising=False)
    assert not deploy._validate_if_path_exists()


def test__get_bq_credentials_success(mocker, credentials):
    """Test successfully getting credentials."""
    expected = mocker.Mock()
    mocker.patch(
        "plugin_scripts.deploy.service_account.Credentials.from_service_account_info",
        return_value=expected,
    )
    response = deploy._get_bq_credentials()
    assert response == expected


def test__get_bq_credentials_missing(mocker, monkeypatch):
    """Test getting credentials fails when not set."""
    monkeypatch.delenv("credentials", raising=False)
    with pytest.raises(MissingConfigError) as exec_info:
        deploy._get_bq_credentials()
    assert exec_info.value.config_name == "credentials"


def test__get_bq_credentials_invalid_json(mocker, monkeypatch):
    """Test getting credentials fails with invalid JSON."""
    monkeypatch.setenv("credentials", "not valid json")
    with pytest.raises(ValueError) as exec_info:
        deploy._get_bq_credentials()
    assert "Invalid credentials JSON" in str(exec_info.value)


def test_main_cloud_function_directory_false(mocker, monkeypatch):
    """Test main raises exception when directory does not exist."""
    # Set environment variables
    monkeypatch.setenv("debug_mode", "false")
    monkeypatch.setenv("gcp_project", "gcp_project")
    monkeypatch.setenv("cloud_function_directory", "cloud_function_directory")
    monkeypatch.setenv("credentials", "credentials")
    monkeypatch.setenv("gcp_region", "gcp_region")
    monkeypatch.setenv("cloud_function_name", "cloud_function_name")

    # Mock Path to return False for is_dir
    mock_path = mocker.patch("plugin_scripts.deploy.Path")
    mock_path.return_value.is_dir.return_value = False

    with pytest.raises(CloudFunctionDirectoryNonExistent):
        deploy.main()


def test_main_deploy_fails(mocker, monkeypatch):
    """Test main raises exception when deployment fails."""
    # Set environment variables
    monkeypatch.setenv("debug_mode", "false")
    monkeypatch.setenv("gcp_project", "gcp_project")
    monkeypatch.setenv("cloud_function_directory", "cloud_function_directory")
    monkeypatch.setenv("credentials", '{"secret": "value"}')
    monkeypatch.setenv("gcp_region", "gcp_region")
    monkeypatch.setenv("cloud_function_name", "cloud_function_name")

    # Mock Path to return True for is_dir
    mock_path = mocker.patch("plugin_scripts.deploy.Path")
    mock_path.return_value.is_dir.return_value = True

    # Mock _deploy to raise DeployFailed
    mocker.patch(
        "plugin_scripts.deploy._deploy", side_effect=DeployFailed("Test error")
    )

    with pytest.raises(DeployFailed):
        deploy.main()


def test_main_success(mocker, monkeypatch):
    """Test main executes successfully."""
    # Set environment variables
    monkeypatch.setenv("debug_mode", "false")
    monkeypatch.setenv("gcp_project", "gcp_project")
    monkeypatch.setenv("cloud_function_directory", "cloud_function_directory")
    monkeypatch.setenv("credentials", '{"secret": "value"}')
    monkeypatch.setenv("gcp_region", "gcp_region")
    monkeypatch.setenv("cloud_function_name", "cloud_function_name")

    # Mock Path to return True for is_dir
    mock_path = mocker.patch("plugin_scripts.deploy.Path")
    mock_path.return_value.is_dir.return_value = True

    # Mock _deploy to succeed
    mocker.patch("plugin_scripts.deploy._deploy")

    deploy.main()
    # No exception should be raised


def test__zip_directory_success(mocker, cloud_function_directory, tmp_path):
    """Test successfully zipping a directory."""
    # Create test directory structure
    test_dir = tmp_path / "test_function"
    test_dir.mkdir()
    (test_dir / "main.py").write_text("def hello(): pass")
    (test_dir / "requirements.txt").write_text("requests>=2.28.0")

    mocker.patch("plugin_scripts.deploy.os.environ.get", return_value=str(test_dir))

    mock_handler = mocker.Mock()
    deploy._zip_directory(mock_handler)

    # Verify write was called
    assert mock_handler.write.call_count == 2


def test__zip_directory_no_env_var(mocker):
    """Test zipping fails when environment variable is not set."""
    mocker.patch("plugin_scripts.deploy.os.environ.get", return_value=None)

    mock_handler = mocker.Mock()
    with pytest.raises(ValueError) as exec_info:
        deploy._zip_directory(mock_handler)
    assert "cloud_function_directory environment variable is not set" in str(
        exec_info.value
    )


def test__handle_exception(mocker):
    """Test exception handling logs error."""
    logger_mock = mocker.patch("plugin_scripts.deploy._logger")
    test_exception = Exception("Test error")

    deploy._handle_exception(test_exception, debug_mode=False)
    logger_mock.error.assert_called_once()


def test__handle_exception_debug_mode(mocker):
    """Test exception handling with debug mode logs additional info."""
    logger_mock = mocker.patch("plugin_scripts.deploy._logger")
    test_exception = Exception("Test error")

    deploy._handle_exception(test_exception, debug_mode=True)
    logger_mock.error.assert_called_once()
    logger_mock.debug.assert_called_once()


def test__upload_source_code_using_archive_url_success(mocker, credentials):
    """Test successful upload using archive URL."""
    mock_storage_client = mocker.patch("plugin_scripts.deploy.storage.Client")
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")

    mock_bucket = mocker.Mock()
    mock_blob = mocker.Mock()
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    mock_data = mocker.Mock()
    mock_data.read.return_value = b"test data"

    deploy._upload_source_code_using_archive_url(
        "gs://test-bucket/test-blob", mock_data
    )

    mock_blob.upload_from_string.assert_called_once_with(b"test data")


def test__upload_source_code_using_upload_url_success(mocker, credentials):
    """Test successful upload using upload URL."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.Mock()
    mock_requests = mocker.patch("plugin_scripts.deploy.requests")
    mock_requests.put.return_value = mock_response

    mock_data = mocker.Mock()

    deploy._upload_source_code_using_upload_url(
        "https://example.com/upload", debug_mode=False, data=mock_data
    )

    mock_requests.put.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test__upload_source_code_using_upload_url_failure(mocker, credentials):
    """Test upload fails with request exception."""
    mock_requests = mocker.patch("plugin_scripts.deploy.requests")
    mock_requests.put.side_effect = Exception("Network error")
    mock_requests.exceptions.RequestException = Exception

    mock_data = mocker.Mock()

    with pytest.raises(DeployFailed) as exec_info:
        deploy._upload_source_code_using_upload_url(
            "https://example.com/upload", debug_mode=False, data=mock_data
        )
    assert "Failed to upload source code" in str(exec_info.value)
