import pytest

from plugin_scripts import deploy


@pytest.fixture
def cloud_function_directory(monkeypatch):
    return monkeypatch.setenv("cloud_function_directory", "schemas/project")


@pytest.fixture
def cloud_function_name(monkeypatch):
    return monkeypatch.setenv("cloud_function_name", "cloud_function_name")


@pytest.fixture
def gcp_project(monkeypatch):
    return monkeypatch.setenv("gcp_project", "gcp_project")


@pytest.fixture
def gcp_region(monkeypatch):
    return monkeypatch.setenv("gcp_region", "gcp_region")


@pytest.fixture
def credentials(monkeypatch):
    return monkeypatch.setenv("credentials", "{'secret': 'value'}")


def test__validate_env_variables_missing_cloud_function_directory(
    gcp_project, credentials, gcp_region, cloud_function_name
):
    with pytest.raises(Exception) as exec_info:
        deploy._validate_env_variables()
    assert exec_info.value.args[0] == "Missing `cloud_function_directory` config"


def test__validate_env_variables_missing_gcp_project(
    cloud_function_directory, credentials, gcp_region, cloud_function_name
):
    with pytest.raises(Exception) as exec_info:
        deploy._validate_env_variables()
    assert exec_info.value.args[0] == "Missing `gcp_project` config"


def test__validate_env_variables_missing_credentials(
    gcp_project, cloud_function_directory, gcp_region, cloud_function_name
):
    with pytest.raises(Exception) as exec_info:
        deploy._validate_env_variables()
    assert exec_info.value.args[0] == "Missing `credentials` config"


def test__validate_env_variables_all_variables_present(
    gcp_project, cloud_function_directory, credentials, gcp_region, cloud_function_name
):
    deploy._validate_env_variables()
    assert True
