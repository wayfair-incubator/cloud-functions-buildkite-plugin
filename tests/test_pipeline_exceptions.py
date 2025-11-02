"""Tests for custom pipeline exceptions."""

import pytest

from plugin_scripts.pipeline_exceptions import (
    CloudFunctionDirectoryNonExistent,
    DeployFailed,
    MissingConfigError,
)


def test_cloud_function_directory_nonexistent_init():
    """Test CloudFunctionDirectoryNonExistent exception initialization."""
    e = CloudFunctionDirectoryNonExistent("/path/to/dir")
    assert isinstance(e, Exception)
    assert e.directory == "/path/to/dir"
    assert "Cloud function directory does not exist: /path/to/dir" in str(e)


def test_cloud_function_directory_nonexistent_throws():
    """Test CloudFunctionDirectoryNonExistent exception can be raised."""
    e = CloudFunctionDirectoryNonExistent("/some/path")
    with pytest.raises(CloudFunctionDirectoryNonExistent):
        raise e


def test_deploy_failed_init():
    """Test DeployFailed exception initialization."""
    e = DeployFailed("Custom error message")
    assert isinstance(e, Exception)
    assert "Custom error message" in str(e)


def test_deploy_failed_default_message():
    """Test DeployFailed exception with default message."""
    e = DeployFailed()
    assert isinstance(e, Exception)
    assert "Deployment to Cloud Function failed" in str(e)


def test_deploy_failed_throws():
    """Test DeployFailed exception can be raised."""
    e = DeployFailed("Test error")
    with pytest.raises(DeployFailed):
        raise e


def test_missing_config_error_init():
    """Test MissingConfigError exception initialization."""
    e = MissingConfigError("gcp_project")
    assert isinstance(e, Exception)
    assert e.config_name == "gcp_project"
    assert "Missing `gcp_project` config" in str(e)


def test_missing_config_error_throws():
    """Test MissingConfigError exception can be raised."""
    e = MissingConfigError("test_config")
    with pytest.raises(MissingConfigError):
        raise e


@pytest.mark.parametrize(
    "exception_object",
    [
        CloudFunctionDirectoryNonExistent("/test/dir"),
        DeployFailed("test message"),
        MissingConfigError("test_param"),
    ],
)
def test_all_exceptions_are_exceptions(exception_object):
    """Test that all custom exceptions inherit from Exception."""
    assert isinstance(exception_object, Exception)
