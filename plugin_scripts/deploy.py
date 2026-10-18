import ast
import fnmatch
import json
import logging
import os
import time
import zipfile
from pathlib import Path
from pprint import pformat
from tempfile import TemporaryFile
from typing import Any
from urllib.parse import urlparse

import google.auth
import google.auth.exceptions
import requests
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient import discovery
from requests import Response

from plugin_scripts import annotation
from plugin_scripts.pipeline_exceptions import (
    CloudFunctionDirectoryNonExistent,
    DeployFailed,
    MissingConfigError,
)

_logger = logging.getLogger("cloud-function")
_logger.setLevel(logging.INFO)
console = logging.StreamHandler()
_logger.addHandler(console)


# What the annotation reports; filled in while deploying
_report: dict[str, Any] = {}

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# Never uploaded: version control data, local secrets and build leftovers
_EXCLUDED_DIRECTORIES = {".git", "__pycache__", "node_modules"}
_EXCLUDED_FILE_PATTERNS = (".env", ".env.*", "*.pyc", ".DS_Store")


def _exclude_patterns() -> list[str]:
    """User patterns from the `exclude` option (newline separated)."""
    raw = os.environ.get("exclude_patterns", "")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _is_excluded(relative_path: Path, patterns: list[str] | None = None) -> bool:
    """
    Return True if a path (relative to the function directory) is not uploaded.

    Besides the built-in exclusions, `patterns` are shell-style globs (`fnmatch`)
    matched against the path relative to the directory, with `/` separators. A
    pattern that matches a directory excludes everything inside it. Note that `*`
    also matches `/`.
    """
    if any(part in _EXCLUDED_DIRECTORIES for part in relative_path.parts):
        return True
    if any(relative_path.match(pattern) for pattern in _EXCLUDED_FILE_PATTERNS):
        return True
    posix = relative_path.as_posix()
    candidates = [posix, *(parent.as_posix() for parent in relative_path.parents)]
    return any(
        fnmatch.fnmatchcase(candidate, pattern)
        for pattern in patterns or []
        for candidate in candidates
        if candidate != "."
    )


def _zip_directory(handler: zipfile.ZipFile) -> list[str]:
    """
    Zip the cloud function directory for deployment.

    Args:
        handler: ZipFile handler to write files to

    Returns:
        The names of the files that were added, sorted

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

    patterns = _exclude_patterns()
    if patterns:
        _logger.info(f"Excluding: {', '.join(patterns)}")

    names: list[str] = []
    file_count = 0
    excluded_count = 0
    for file_path in sorted(cloud_function_directory.rglob("*")):
        arcname = file_path.relative_to(cloud_function_directory)
        if not file_path.is_file():
            continue
        if _is_excluded(arcname, patterns):
            excluded_count += 1
            continue
        handler.write(file_path, arcname)
        names.append(arcname.as_posix())
        file_count += 1

    if patterns and file_count == 0:
        msg = "Every file in the directory is excluded by the `exclude` patterns"
        _logger.error(msg)
        raise DeployFailed(msg)

    _report["files"] = file_count
    _report["excluded"] = excluded_count
    _logger.info(f"Successfully zipped {file_count} files ({excluded_count} excluded)")
    return names


def _get_credentials() -> Any:
    """
    Get Google Cloud credentials.

    Uses the service account key in the `credentials` environment variable when
    there is one, otherwise Application Default Credentials (the metadata server
    of the agent's cloud identity, Workload Identity, or the file named by
    GOOGLE_APPLICATION_CREDENTIALS).

    Returns:
        Google credentials

    Raises:
        DeployFailed: If there is no key and no Application Default Credentials
        ValueError: If the service account key is not valid JSON
    """
    credentials_str = os.environ.get("credentials")
    if not credentials_str:
        _logger.info(
            "No service account key given, using Application Default Credentials"
        )
        try:
            credentials, _ = google.auth.default(scopes=_SCOPES)
        except google.auth.exceptions.DefaultCredentialsError as e:
            _logger.error(f"No Application Default Credentials found: {e}")
            raise DeployFailed(
                "No credentials: set `gcp_service_account` or make Application "
                f"Default Credentials available to the agent ({e})"
            ) from e
        return credentials

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
        storage_client = storage.Client(credentials=_get_credentials())
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(data.read())
        _logger.info(f"Source code object {blob_name} uploaded to bucket {bucket_name}")
    except Exception as e:
        _logger.error(f"Failed to upload source code: {e}")
        raise DeployFailed(f"Failed to upload source code: {e}") from e


def _upload_source_code_using_upload_url(
    upload_url: str, debug_mode: bool, data: Any, content_length_range: bool = True
) -> None:
    """
    Upload source code using upload URL.

    Args:
        upload_url: Upload URL for the cloud function
        debug_mode: Whether to log debug information
        data: File-like object containing the zipped source code
        content_length_range: Send the 1st gen size limit header (a 2nd gen signed
            URL does not sign it)

    Raises:
        DeployFailed: If upload fails
    """
    # Prepare Header and data for PUT request
    # https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions/generateUploadUrl
    _logger.info("Uploading source code using upload URL")
    headers = {"content-type": "application/zip"}
    if content_length_range:
        headers["x-goog-content-length-range"] = "0,104857600"

    try:
        response: Response = requests.put(
            upload_url, headers=headers, data=data, timeout=300
        )
        _logger.info(f"HTTP Status Code for uploading data: {response.status_code}")

        if debug_mode:
            _logger.debug(f"Response body: {response.text}")

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


DEFAULT_WAIT_TIMEOUT = 600
_POLL_INTERVAL_SECONDS = 5


def _wait_for_operation(operations: Any, operation_name: str, timeout: float) -> None:
    """
    Wait until a long-running Cloud Functions operation has finished.

    `functions.patch` only starts the deployment; the build and rollout happen
    afterwards and are reported by the returned operation.

    Args:
        operations: The API's operations resource (it has a `get` method)
        operation_name: Name of the operation returned by the patch call
        timeout: Seconds to wait before giving up

    Raises:
        DeployFailed: If the operation fails or does not finish in time
    """
    deadline = time.monotonic() + timeout
    _logger.info(f"Waiting for operation {operation_name} (up to {timeout:.0f}s)...")

    while True:
        operation = operations.get(name=operation_name).execute()
        if operation.get("done"):
            error = operation.get("error")
            if error:
                message = f"Deployment operation failed: {error.get('message', error)}"
                raise DeployFailed(message)
            _logger.info("Deployment operation finished successfully")
            return

        if time.monotonic() + _POLL_INTERVAL_SECONDS > deadline:
            raise DeployFailed(
                f"Timed out after {timeout:.0f}s waiting for operation "
                f"{operation_name}; the deployment may still complete"
            )
        time.sleep(_POLL_INTERVAL_SECONDS)


def _wait_enabled() -> bool:
    """Whether to wait for the deployment operation (the `wait` option)."""
    return os.environ.get("wait", "true").lower() in ("true", "on", "yes", "1")


def _wait_timeout() -> float:
    """Seconds to wait for the deployment operation (the `wait_timeout` option)."""
    raw = os.environ.get("wait_timeout") or str(DEFAULT_WAIT_TIMEOUT)
    try:
        timeout = float(raw)
    except ValueError as e:
        raise MissingConfigError("wait_timeout (a number of seconds)") from e
    return timeout


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


def _deploy_gen1(debug_mode: bool) -> None:
    """
    Deploy a 1st generation cloud function (Cloud Functions v1 API).

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
            "cloudfunctions", "v1", credentials=_get_credentials()
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
            # Only non-sensitive fields: the full definition can hold environment
            # variables and secret references
            summary = {
                key: function.get(key)
                for key in ("name", "status", "runtime", "entryPoint", "updateTime")
            }
            _logger.debug(f"Function summary: {pformat(summary)}")

        with TemporaryFile() as data:
            file_handler = zipfile.ZipFile(data, mode="w")
            _zip_directory(file_handler)
            file_handler.close()
            _report["bytes"] = data.tell()
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
            _report["operation"] = response["name"]

            if debug_mode:
                _logger.debug(f"Response: {pformat(response)}")

            if _wait_enabled():
                _wait_for_operation(
                    service.operations(), response["name"], _wait_timeout()
                )
            else:
                _logger.info("Not waiting for the deployment to finish (wait is off)")
        except Exception as e:
            deploy_failed = True
            _handle_exception(e, debug_mode)
    except Exception as e:
        deploy_failed = True
        _handle_exception(e, debug_mode)

    if deploy_failed:
        raise DeployFailed("Deployment failed due to errors")


def _deploy_gen2(debug_mode: bool) -> None:
    """
    Deploy a 2nd generation function (Cloud Run functions, Cloud Functions v2 API).

    The archive is uploaded to a signed URL and only the function's source
    location is patched; every other setting stays as it is.

    Args:
        debug_mode: Whether to enable debug logging

    Raises:
        DeployFailed: If deployment fails
    """
    _logger.info("Starting 2nd generation cloud function deployment...")

    try:
        gcp_project = os.environ.get("gcp_project")
        gcp_region = os.environ.get("gcp_region")
        cloud_function_name = os.environ.get("cloud_function_name")

        parent = f"projects/{gcp_project}/locations/{gcp_region}"
        function_path = f"{parent}/functions/{cloud_function_name}"
        _logger.info(f"Deploying function: {function_path}")

        service = discovery.build(
            "cloudfunctions", "v2", credentials=_get_credentials()
        )
        locations = service.projects().locations()
        cloud_functions = locations.functions()

        try:
            function = cloud_functions.get(name=function_path).execute()
            _logger.info(f"Found existing cloud function: {cloud_function_name}")
        except Exception as e:
            _logger.error(f"Failed to get cloud function: {e}")
            raise DeployFailed(
                f"Cloud function not found: {cloud_function_name}"
            ) from e

        if function.get("environment") == "GEN_1":
            raise DeployFailed(
                f"{cloud_function_name} is a 1st generation function; "
                "use `generation: 1` (the default)"
            )

        if debug_mode:
            summary = {
                key: function.get(key)
                for key in ("name", "state", "environment", "updateTime")
            }
            _logger.debug(f"Function summary: {pformat(summary)}")

        with TemporaryFile() as data:
            file_handler = zipfile.ZipFile(data, mode="w")
            _zip_directory(file_handler)
            file_handler.close()
            _report["bytes"] = data.tell()
            data.seek(0)

            try:
                upload = cloud_functions.generateUploadUrl(
                    parent=parent, body={"environment": "GEN_2"}
                ).execute()
                _logger.info("Generated upload URL for source code")
            except Exception as e:
                _logger.error(f"Failed to generate upload URL: {e}")
                raise DeployFailed(f"Failed to generate upload URL: {e}") from e

            _upload_source_code_using_upload_url(
                upload["uploadUrl"], debug_mode, data, content_length_range=False
            )

        _logger.info("Patching cloud function...")
        response = cloud_functions.patch(
            name=function_path,
            updateMask="buildConfig.source.storageSource",
            body={
                "buildConfig": {"source": {"storageSource": upload["storageSource"]}}
            },
        ).execute()
        _logger.info("Successfully patched Cloud Function")
        _logger.info(f"Operation Name: {response['name']}")
        _report["operation"] = response["name"]

        if _wait_enabled():
            _wait_for_operation(
                locations.operations(), response["name"], _wait_timeout()
            )
        else:
            _logger.info("Not waiting for the deployment to finish (wait is off)")
    except Exception as e:
        _handle_exception(e, debug_mode)
        raise DeployFailed("Deployment failed due to errors") from e


def _deploy(debug_mode: bool) -> None:
    """
    Deploy the cloud function to Google Cloud Platform.

    Args:
        debug_mode: Whether to enable debug logging

    Raises:
        DeployFailed: If deployment fails
    """
    if os.environ.get("generation", "1") == "2":
        _deploy_gen2(debug_mode)
    else:
        _deploy_gen1(debug_mode)


def main() -> None:
    """
    Main entry point for cloud function deployment.

    Writes the annotation file first when `annotation_file` is set, whatever the
    outcome.
    """
    _report.clear()
    started = time.monotonic()
    _report.update(
        function=os.environ.get("cloud_function_name"),
        project=os.environ.get("gcp_project"),
        region=os.environ.get("gcp_region"),
        generation=os.environ.get("generation", "1"),
        wait=_wait_enabled(),
        mode=os.environ.get("mode", "apply"),
    )
    try:
        _main()
    except Exception as e:
        _report["error"] = str(e)
        raise
    finally:
        _report["seconds"] = time.monotonic() - started
        path = annotation.annotation_path()
        if path:
            annotation.write(path, _report)


# The upload URL of a 1st gen function only accepts archives up to this size
_MAX_ARCHIVE_BYTES_GEN1 = 104857600


def _check_archive(generation: str) -> list[str]:
    """
    Build the archive in memory-backed storage and check it, without uploading.

    Returns:
        The names of the files that would be uploaded

    Raises:
        DeployFailed: If there is nothing to upload or the archive is too big
    """
    with TemporaryFile() as data:
        with zipfile.ZipFile(data, mode="w") as file_handler:
            names = _zip_directory(file_handler)
        size = data.tell()

    _report["bytes"] = size
    if not names:
        raise DeployFailed("There are no files to upload in the function directory")
    if generation != "2" and size > _MAX_ARCHIVE_BYTES_GEN1:
        raise DeployFailed(
            f"The archive is {size / 1024 / 1024:.1f} MiB; a 1st generation upload "
            f"accepts at most {_MAX_ARCHIVE_BYTES_GEN1 // 1024 // 1024} MiB"
        )
    return names


def _log_files(names: list[str], limit: int = 200) -> None:
    for name in names[:limit]:
        _logger.info(f"  {name}")
    if len(names) > limit:
        _logger.info(f"  ... and {len(names) - limit} more")


def _validate() -> None:
    """Check the options and the archive offline; no credentials, no API calls."""
    generation = os.environ.get("generation", "1")
    names = _check_archive(generation)
    _log_files(names)
    _logger.info(
        f"Valid: {len(names)} files ({_report['bytes'] / 1024:.1f} KiB) would be "
        "uploaded"
    )


def _plan(debug_mode: bool) -> None:
    """
    Show what a deployment would do. Only reads: it fetches the function and builds
    the archive, but generates no upload URL, uploads nothing and patches nothing.

    Raises:
        DeployFailed: If the function cannot be read or the archive is not valid
    """
    generation = os.environ.get("generation", "1")
    gcp_project = os.environ.get("gcp_project")
    gcp_region = os.environ.get("gcp_region")
    cloud_function_name = os.environ.get("cloud_function_name")
    function_path = (
        f"projects/{gcp_project}/locations/{gcp_region}/functions/{cloud_function_name}"
    )

    try:
        service = discovery.build(
            "cloudfunctions",
            "v2" if generation == "2" else "v1",
            credentials=_get_credentials(),
        )
        function = (
            service.projects().locations().functions().get(name=function_path).execute()
        )
    except Exception as e:
        _logger.error(f"Failed to get cloud function: {e}")
        raise DeployFailed(f"Cloud function not found: {cloud_function_name}") from e

    if generation == "2" and function.get("environment") == "GEN_1":
        raise DeployFailed(
            f"{cloud_function_name} is a 1st generation function; "
            "use `generation: 1` (the default)"
        )

    if generation == "2":
        source = function.get("buildConfig", {}).get("source", {})
        runtime = function.get("buildConfig", {}).get("runtime")
        state = function.get("state")
    else:
        source = {
            key: function[key]
            for key in ("sourceArchiveUrl", "sourceUploadUrl", "sourceRepository")
            if key in function
        }
        runtime = function.get("runtime")
        state = function.get("status")
    _report["runtime"] = runtime
    _report["state"] = state

    names = _check_archive(generation)
    _logger.info(f"Plan for {function_path} (generation {generation}):")
    _logger.info(f"  current state: {state}, runtime: {runtime}")
    _logger.info(f"  current source: {source or 'none'}")
    _logger.info(
        f"  would upload {len(names)} files ({_report['bytes'] / 1024:.1f} KiB) and "
        "replace the function's source with them; nothing else changes"
    )
    _log_files(names)
    _logger.info("Nothing was changed (mode is plan)")


def _main() -> None:
    """
    Run the deployment.

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
            mode = os.environ.get("mode", "apply")
            if mode == "validate":
                _validate()
            elif mode == "plan":
                _plan(debug_mode)
            elif mode == "apply":
                _deploy(debug_mode)
                _logger.info("Cloud function deployment completed successfully")
            else:
                raise DeployFailed(f"Unknown mode '{mode}'")
        else:
            cloud_function_directory = os.environ.get("cloud_function_directory", "")
            raise CloudFunctionDirectoryNonExistent(cloud_function_directory)
    except (CloudFunctionDirectoryNonExistent, DeployFailed, MissingConfigError):
        # Re-raise these custom exceptions as-is
        raise
    except Exception as e:
        _logger.error(f"Unexpected error during deployment: {e}")
        raise DeployFailed(f"Unexpected error: {e}") from e
