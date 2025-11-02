import ast
import json
import logging
import os
import zipfile
from pathlib import Path
from pprint import pformat
from tempfile import TemporaryFile
from typing import Any
from urllib.parse import urlparse

import requests
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient import discovery
from requests import Response

from plugin_scripts.pipeline_exceptions import (
    CloudFunctionDirectoryNonExistent,
    DeployFailed,
    MissingConfigError,
)

_logger = logging.getLogger("cloud-function")
_logger.setLevel(logging.INFO)
console = logging.StreamHandler()
_logger.addHandler(console)


def _zip_directory(handler: zipfile.ZipFile) -> None:
    """
    Zip the cloud function directory for deployment.

    Args:
        handler: ZipFile handler to write files to

    Raises:
        ValueError: If cloud_function_directory is not set
    """
    cloud_function_directory_str = os.environ.get("cloud_function_directory")
    if not cloud_function_directory_str:
        msg = "cloud_function_directory environment variable is not set"
        _logger.error(msg)
        raise ValueError(msg)

    cloud_function_directory = Path(cloud_function_directory_str)
    _logger.info(f"Zipping directory: {cloud_function_directory}")

    file_count = 0
    for file_path in cloud_function_directory.rglob("*"):
        if file_path.is_file():
            arcname = file_path.relative_to(cloud_function_directory)
            handler.write(file_path, arcname)
            file_count += 1

    _logger.info(f"Successfully zipped {file_count} files")


def _get_bq_credentials() -> service_account.Credentials:
    """
    Get Google Cloud credentials from environment variable.

    Returns:
        Service account credentials

    Raises:
        MissingConfigError: If credentials are not set
        json.JSONDecodeError: If credentials JSON is invalid
    """
    credentials_str = os.environ.get("credentials")
    if not credentials_str:
        _logger.error("Missing credentials configuration")
        raise MissingConfigError("credentials")

    try:
        svc = json.loads(credentials_str)
        _logger.debug("Successfully parsed credentials JSON")
        return service_account.Credentials.from_service_account_info(svc)
    except json.JSONDecodeError as e:
        _logger.error(f"Invalid credentials JSON: {e}")
        raise ValueError(f"Invalid credentials JSON: {e}") from e


def _upload_source_code_using_archive_url(archive_url: str, data: Any) -> None:
    """
    Upload source code to GCS using archive URL.

    Args:
        archive_url: GCS URL to upload to
        data: File-like object containing the zipped source code

    Raises:
        Exception: If upload fails
    """
    _logger.info(f"Uploading source code using archive URL: {archive_url}")
    object_path = urlparse(archive_url)
    bucket_name = object_path.netloc
    blob_name = object_path.path.lstrip("/")

    try:
        storage_client = storage.Client(credentials=_get_bq_credentials())
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(data.read())
        _logger.info(f"Source code object {blob_name} uploaded to bucket {bucket_name}")
    except Exception as e:
        _logger.error(f"Failed to upload source code: {e}")
        raise DeployFailed(f"Failed to upload source code: {e}") from e


def _upload_source_code_using_upload_url(
    upload_url: str, debug_mode: bool, data: Any
) -> None:
    """
    Upload source code using upload URL.

    Args:
        upload_url: Upload URL for the cloud function
        debug_mode: Whether to log debug information
        data: File-like object containing the zipped source code

    Raises:
        DeployFailed: If upload fails
    """
    # Prepare Header and data for PUT request
    # https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions/generateUploadUrl
    _logger.info("Uploading source code using upload URL")
    headers = {
        "content-type": "application/zip",
        "x-goog-content-length-range": "0,104857600",
    }

    try:
        response: Response = requests.put(
            upload_url, headers=headers, data=data, timeout=300
        )
        _logger.info(f"HTTP Status Code for uploading data: {response.status_code}")

        if debug_mode:
            _logger.debug(f"Response body: {pformat(response.json)}")

        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        _logger.error(f"Failed to upload source code via upload URL: {e}")
        raise DeployFailed(f"Failed to upload source code: {e}") from e


def _validate_env_variables() -> None:
    """
    Validate that all required environment variables are set.

    Raises:
        MissingConfigError: If any required environment variable is missing
    """
    required_vars = {
        "gcp_project": os.environ.get("gcp_project"),
        "gcp_region": os.environ.get("gcp_region"),
        "cloud_function_name": os.environ.get("cloud_function_name"),
        "cloud_function_directory": os.environ.get("cloud_function_directory"),
        "credentials": os.environ.get("credentials"),
    }

    for var_name, var_value in required_vars.items():
        if not var_value:
            _logger.error(f"Missing required environment variable: {var_name}")
            raise MissingConfigError(var_name)

    _logger.debug("All required environment variables are present")


def _validate_if_path_exists() -> bool:
    """
    Check if the cloud function directory exists.

    Returns:
        True if the directory exists, False otherwise
    """
    cloud_function_directory_str = os.environ.get("cloud_function_directory")
    if not cloud_function_directory_str:
        _logger.error("cloud_function_directory environment variable is not set")
        return False

    cloud_function_directory = Path(cloud_function_directory_str)
    exists = cloud_function_directory.is_dir()

    if exists:
        _logger.info(f"Cloud function directory exists: {cloud_function_directory}")
    else:
        _logger.error(
            f"Cloud function directory does not exist: {cloud_function_directory}"
        )

    return exists


def _handle_exception(e: Exception, debug_mode: bool) -> None:
    """
    Handle exceptions during deployment.

    Args:
        e: The exception to handle
        debug_mode: Whether to log additional debug information
    """
    error_message = str(e)
    _logger.error(f"Deployment error: {error_message}")

    if debug_mode:
        _logger.debug(f"Exception details: {pformat(e)}")


def _deploy(debug_mode: bool) -> None:
    """
    Deploy the cloud function to Google Cloud Platform.

    Args:
        debug_mode: Whether to enable debug logging

    Raises:
        DeployFailed: If deployment fails
    """
    _logger.info("Starting cloud function deployment...")
    deploy_failed = False

    try:
        gcp_project = os.environ.get("gcp_project")
        gcp_region = os.environ.get("gcp_region")
        cloud_function_name = os.environ.get("cloud_function_name")

        parent = f"projects/{gcp_project}/locations/{gcp_region}"
        function_path = (
            f"projects/{gcp_project}/locations/{gcp_region}/"
            f"functions/{cloud_function_name}"
        )

        _logger.info(f"Deploying function: {function_path}")

        service = discovery.build(
            "cloudfunctions", "v1", credentials=_get_bq_credentials()
        )
        cloud_functions = service.projects().locations().functions()

        # check if cloud function exists, if it exists execution continues
        # as is otherwise it will raise an exception
        try:
            function = cloud_functions.get(name=function_path).execute()
            _logger.info(f"Found existing cloud function: {cloud_function_name}")
        except Exception as e:
            _logger.error(f"Failed to get cloud function: {e}")
            raise DeployFailed(
                f"Cloud function not found: {cloud_function_name}"
            ) from e

        if debug_mode:
            _logger.debug(f"Function Definition: {pformat(function)}")

        with TemporaryFile() as data:
            file_handler = zipfile.ZipFile(data, mode="w")
            _zip_directory(file_handler)
            file_handler.close()
            data.seek(0)

            if "sourceArchiveUrl" in function:
                archive_url = function["sourceArchiveUrl"]
                _upload_source_code_using_archive_url(archive_url, data)
            else:
                # https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions/generateUploadUrl
                try:
                    upload_url = cloud_functions.generateUploadUrl(
                        parent=parent, body={}
                    ).execute()["uploadUrl"]
                    _logger.info("Generated upload URL for source code")
                except Exception as e:
                    _logger.error(f"Failed to generate upload URL: {e}")
                    raise DeployFailed(f"Failed to generate upload URL: {e}") from e

                _upload_source_code_using_upload_url(upload_url, debug_mode, data)
                function["sourceUploadUrl"] = upload_url

        try:
            _logger.info("Patching cloud function...")
            response = cloud_functions.patch(
                name=function_path, body=function
            ).execute()
            _logger.info("Successfully patched Cloud Function")
            _logger.info(f"Operation Name: {response['name']}")

            if debug_mode:
                _logger.debug(f"Response: {pformat(response)}")
        except Exception as e:
            deploy_failed = True
            _handle_exception(e, debug_mode)
    except Exception as e:
        deploy_failed = True
        _handle_exception(e, debug_mode)

    if deploy_failed:
        raise DeployFailed("Deployment failed due to errors")


def main() -> None:
    """
    Main entry point for cloud function deployment.

    Raises:
        CloudFunctionDirectoryNonExistent: If the cloud function directory
            does not exist
        DeployFailed: If deployment fails
    """
    try:
        env_debug_mode: str = os.environ.get("debug_mode", "False").title()
        debug_mode = ast.literal_eval(env_debug_mode)

        if debug_mode:
            _logger.setLevel(logging.DEBUG)
            _logger.debug("Debug mode enabled")

        _logger.info("Starting cloud function deployment process")

        _validate_env_variables()
        if _validate_if_path_exists():
            _deploy(debug_mode)
            _logger.info("Cloud function deployment completed successfully")
        else:
            cloud_function_directory = os.environ.get("cloud_function_directory", "")
            raise CloudFunctionDirectoryNonExistent(cloud_function_directory)
    except (CloudFunctionDirectoryNonExistent, DeployFailed, MissingConfigError):
        # Re-raise these custom exceptions as-is
        raise
    except Exception as e:
        _logger.error(f"Unexpected error during deployment: {e}")
        raise DeployFailed(f"Unexpected error: {e}") from e
