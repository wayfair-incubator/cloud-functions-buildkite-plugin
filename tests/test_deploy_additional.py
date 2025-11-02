"""Comprehensive tests for the deploy module - additional coverage."""

from unittest.mock import Mock

import pytest
import requests

from plugin_scripts import deploy
from plugin_scripts.pipeline_exceptions import DeployFailed


def test__upload_source_code_using_archive_url_exception(mocker):
    """Test upload fails with archive URL."""
    mock_storage = mocker.patch("plugin_scripts.deploy.storage")
    mock_storage.Client.side_effect = Exception("Storage error")
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")

    mock_data = mocker.Mock()
    mock_data.read.return_value = b"test data"

    with pytest.raises(DeployFailed) as exc_info:
        deploy._upload_source_code_using_archive_url(
            "gs://test-bucket/test-blob", mock_data
        )
    assert "Failed to upload source code" in str(exc_info.value)


def test__upload_source_code_using_upload_url_with_debug(mocker):
    """Test successful upload using upload URL with debug mode."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json = {"status": "success"}
    mock_response.raise_for_status = mocker.Mock()
    mock_requests = mocker.patch("plugin_scripts.deploy.requests")
    mock_requests.put.return_value = mock_response

    mock_data = mocker.Mock()

    # Test with debug mode enabled
    deploy._upload_source_code_using_upload_url(
        "https://example.com/upload", debug_mode=True, data=mock_data
    )

    mock_requests.put.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test__upload_source_code_using_upload_url_request_exception(mocker):
    """Test upload fails with RequestException."""
    mock_requests = mocker.patch("plugin_scripts.deploy.requests")
    mock_requests.put.side_effect = requests.exceptions.RequestException(
        "Network error"
    )
    mock_requests.exceptions.RequestException = requests.exceptions.RequestException

    mock_data = mocker.Mock()

    with pytest.raises(DeployFailed) as exc_info:
        deploy._upload_source_code_using_upload_url(
            "https://example.com/upload", debug_mode=False, data=mock_data
        )
    assert "Failed to upload source code" in str(exc_info.value)


def test_main_with_debug_mode(mocker, monkeypatch):
    """Test main with debug mode enabled."""
    # Set environment variables with debug mode enabled
    monkeypatch.setenv("debug_mode", "True")
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")
    monkeypatch.setenv("credentials", '{"secret": "value"}')
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")

    # Mock dependencies
    mock_path = mocker.patch("plugin_scripts.deploy.Path")
    mock_path.return_value.is_dir.return_value = True
    mocker.patch("plugin_scripts.deploy._deploy")

    deploy.main()
    # Should complete without error


def test_main_unexpected_exception(mocker, monkeypatch):
    """Test main handles unexpected exceptions properly."""
    # Set environment variables
    monkeypatch.setenv("debug_mode", "false")
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")
    monkeypatch.setenv("credentials", '{"secret": "value"}')
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")

    # Mock Path to raise unexpected exception
    mock_path = mocker.patch("plugin_scripts.deploy.Path")
    mock_path.side_effect = RuntimeError("Unexpected error")

    with pytest.raises(DeployFailed) as exc_info:
        deploy.main()
    assert "Unexpected error" in str(exc_info.value)


def test__deploy_with_source_archive_url(mocker, monkeypatch):
    """Test _deploy function with sourceArchiveUrl."""
    # Set environment variables
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")

    # Mock the Google Cloud API
    mock_discovery = mocker.patch("plugin_scripts.deploy.discovery")
    mock_service = Mock()
    mock_cloud_functions = Mock()

    # Mock function response with sourceArchiveUrl
    mock_function = {
        "name": "test-function",
        "sourceArchiveUrl": "gs://test-bucket/test.zip",
    }
    mock_cloud_functions.get.return_value.execute.return_value = mock_function
    mock_cloud_functions.patch.return_value.execute.return_value = {
        "name": "operations/test-op"
    }

    mock_service.projects.return_value.locations.return_value.functions.return_value = (
        mock_cloud_functions
    )
    mock_discovery.build.return_value = mock_service

    # Mock other dependencies
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")
    mocker.patch("plugin_scripts.deploy._zip_directory")
    mock_upload_archive = mocker.patch(
        "plugin_scripts.deploy._upload_source_code_using_archive_url"
    )

    # Execute
    deploy._deploy(debug_mode=False)

    # Verify sourceArchiveUrl path was taken
    mock_upload_archive.assert_called_once()


def test__deploy_with_upload_url(mocker, monkeypatch):
    """Test _deploy function with generateUploadUrl."""
    # Set environment variables
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")

    # Mock the Google Cloud API
    mock_discovery = mocker.patch("plugin_scripts.deploy.discovery")
    mock_service = Mock()
    mock_cloud_functions = Mock()

    # Mock function response without sourceArchiveUrl
    mock_function = {
        "name": "test-function",
        # No sourceArchiveUrl
    }
    mock_cloud_functions.get.return_value.execute.return_value = mock_function
    mock_cloud_functions.generateUploadUrl.return_value.execute.return_value = {
        "uploadUrl": "https://upload.example.com/path"
    }
    mock_cloud_functions.patch.return_value.execute.return_value = {
        "name": "operations/test-op"
    }

    mock_service.projects.return_value.locations.return_value.functions.return_value = (
        mock_cloud_functions
    )
    mock_discovery.build.return_value = mock_service

    # Mock other dependencies
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")
    mocker.patch("plugin_scripts.deploy._zip_directory")
    mock_upload_url = mocker.patch(
        "plugin_scripts.deploy._upload_source_code_using_upload_url"
    )

    # Execute
    deploy._deploy(debug_mode=False)

    # Verify upload URL path was taken
    mock_upload_url.assert_called_once()


def test__deploy_with_debug_mode(mocker, monkeypatch):
    """Test _deploy function with debug mode enabled."""
    # Set environment variables
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")

    # Mock the Google Cloud API
    mock_discovery = mocker.patch("plugin_scripts.deploy.discovery")
    mock_service = Mock()
    mock_cloud_functions = Mock()

    mock_function = {"name": "test-function", "runtime": "python39"}
    mock_cloud_functions.get.return_value.execute.return_value = mock_function
    mock_cloud_functions.generateUploadUrl.return_value.execute.return_value = {
        "uploadUrl": "https://upload.example.com/path"
    }
    mock_cloud_functions.patch.return_value.execute.return_value = {
        "name": "operations/test-op"
    }

    mock_service.projects.return_value.locations.return_value.functions.return_value = (
        mock_cloud_functions
    )
    mock_discovery.build.return_value = mock_service

    # Mock other dependencies
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")
    mocker.patch("plugin_scripts.deploy._zip_directory")
    mocker.patch("plugin_scripts.deploy._upload_source_code_using_upload_url")

    # Execute with debug mode
    deploy._deploy(debug_mode=True)

    # Should complete without error and log debug info


def test__deploy_function_not_found(mocker, monkeypatch):
    """Test _deploy when cloud function is not found."""
    # Set environment variables
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "nonexistent-function")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")

    # Mock the Google Cloud API
    mock_discovery = mocker.patch("plugin_scripts.deploy.discovery")
    mock_service = Mock()
    mock_cloud_functions = Mock()

    # Simulate function not found
    mock_cloud_functions.get.return_value.execute.side_effect = Exception(
        "Function not found"
    )

    mock_service.projects.return_value.locations.return_value.functions.return_value = (
        mock_cloud_functions
    )
    mock_discovery.build.return_value = mock_service

    # Mock credentials
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")

    # Execute and expect DeployFailed
    with pytest.raises(DeployFailed) as exc_info:
        deploy._deploy(debug_mode=False)

    # The error gets wrapped by outer exception handler
    assert "Deployment failed due to errors" in str(exc_info.value)


def test__deploy_upload_url_generation_fails(mocker, monkeypatch):
    """Test _deploy when upload URL generation fails."""
    # Set environment variables
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")

    # Mock the Google Cloud API
    mock_discovery = mocker.patch("plugin_scripts.deploy.discovery")
    mock_service = Mock()
    mock_cloud_functions = Mock()

    # Mock function response without sourceArchiveUrl
    mock_function = {"name": "test-function"}
    mock_cloud_functions.get.return_value.execute.return_value = mock_function

    # Simulate upload URL generation failure
    mock_cloud_functions.generateUploadUrl.return_value.execute.side_effect = Exception(
        "Upload URL generation failed"
    )

    mock_service.projects.return_value.locations.return_value.functions.return_value = (
        mock_cloud_functions
    )
    mock_discovery.build.return_value = mock_service

    # Mock other dependencies
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")
    mocker.patch("plugin_scripts.deploy._zip_directory")

    # Execute and expect DeployFailed
    with pytest.raises(DeployFailed) as exc_info:
        deploy._deploy(debug_mode=False)

    # The error gets wrapped by outer exception handler
    assert "Deployment failed due to errors" in str(exc_info.value)


def test__deploy_patch_fails(mocker, monkeypatch):
    """Test _deploy when patching the function fails."""
    # Set environment variables
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")

    # Mock the Google Cloud API
    mock_discovery = mocker.patch("plugin_scripts.deploy.discovery")
    mock_service = Mock()
    mock_cloud_functions = Mock()

    mock_function = {"name": "test-function"}
    mock_cloud_functions.get.return_value.execute.return_value = mock_function
    mock_cloud_functions.generateUploadUrl.return_value.execute.return_value = {
        "uploadUrl": "https://upload.example.com/path"
    }

    # Simulate patch failure
    mock_cloud_functions.patch.return_value.execute.side_effect = Exception(
        "Patch failed"
    )

    mock_service.projects.return_value.locations.return_value.functions.return_value = (
        mock_cloud_functions
    )
    mock_discovery.build.return_value = mock_service

    # Mock other dependencies
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")
    mocker.patch("plugin_scripts.deploy._zip_directory")
    mocker.patch("plugin_scripts.deploy._upload_source_code_using_upload_url")

    # Execute and expect DeployFailed
    with pytest.raises(DeployFailed) as exc_info:
        deploy._deploy(debug_mode=False)

    assert "Deployment failed due to errors" in str(exc_info.value)


def test__deploy_general_exception(mocker, monkeypatch):
    """Test _deploy handles general exceptions."""
    # Set environment variables
    monkeypatch.setenv("gcp_project", "test-project")
    monkeypatch.setenv("gcp_region", "us-central1")
    monkeypatch.setenv("cloud_function_name", "test-function")
    monkeypatch.setenv("cloud_function_directory", "/test/dir")

    # Mock discovery to raise exception
    mock_discovery = mocker.patch("plugin_scripts.deploy.discovery")
    mock_discovery.build.side_effect = Exception("General error")

    # Mock credentials
    mocker.patch("plugin_scripts.deploy._get_bq_credentials")

    # Execute and expect DeployFailed
    with pytest.raises(DeployFailed) as exc_info:
        deploy._deploy(debug_mode=False)

    assert "Deployment failed due to errors" in str(exc_info.value)
