import json
import os
import zipfile
from tempfile import TemporaryFile
from urllib.parse import urlparse

import requests
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient import discovery

project = os.environ.get("project")
region = os.environ.get("region")
function_name = os.environ.get("cloud_functions_name")
functions_directory = os.environ.get("cloud_functions_directory")
credentials = os.environ.get("GCP_SERVICE_ACCOUNT")

if not project:
    raise Exception("Missing `project` config")

if not region:
    raise Exception("Missing `region` config")

if not function_name:
    raise Exception("Missing `cloud_functions_name` config")

if not functions_directory:
    raise Exception("Missing `cloud_functions_directory` config")

if not credentials:
    raise Exception("Missing `GCP_SERVICE_ACCOUNT` config")


def zip_directory(handler: zipfile.ZipFile):
    for root, dirs, files in os.walk(functions_directory):  # type: ignore # noqa: B007
        for file in files:
            handler.write(
                os.path.join(root, file),
                os.path.relpath(
                    os.path.join(root, file), os.path.join(functions_directory, ".")
                ),
            )


def get_bq_credentials():
    svc = json.loads(credentials)
    return service_account.Credentials.from_service_account_info(svc)


def upload_source_code_using_archive_url(archive_url):
    object_path = urlparse(archive_url)
    bucket_name = object_path.netloc
    blob_name = object_path.path.lstrip("/")

    storage_client = storage.Client(credentials=get_bq_credentials())
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(data.read())
    print(f"Source code object {blob_name} uploaded to bucket {bucket_name}.")


def upload_source_code_using_upload_url(upload_url):
    # Prepare Header and data for PUT request
    # https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions/generateUploadUrl
    headers = {
        "content-type": "application/zip",
        "x-goog-content-length-range": "0,104857600",
    }
    response = requests.put(upload_url, headers=headers, data=data)
    print(f"Response from source code upload using upload_url: {response}")


parent = f"projects/{project}/locations/{region}"
function_path = f"projects/{project}/locations/{region}/functions/{function_name}"

service = discovery.build("cloudfunctions", "v1", credentials=get_bq_credentials())
cloud_functions = service.projects().locations().functions()

# check if cloud function exists, if it exists execution continues as is otherwise it will raise an exception
function = cloud_functions.get(name=function_path).execute()
print(f"function details: {function}")

with TemporaryFile() as data:
    file_handler = zipfile.ZipFile(data, mode="w")
    zip_directory(file_handler)
    file_handler.close()
    data.seek(0)

    if "sourceArchiveUrl" in function:
        archive_url = function["sourceArchiveUrl"]
        upload_source_code_using_archive_url(archive_url)
    else:
        # https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions/generateUploadUrl
        upload_url = cloud_functions.generateUploadUrl(
            parent=parent, body={}
        ).execute()["uploadUrl"]
        upload_source_code_using_upload_url(upload_url)
        function["sourceUploadUrl"] = upload_url

patch_response = cloud_functions.patch(name=function_path, body=function).execute()
print(f"Response from cloud function patch: {patch_response}")
