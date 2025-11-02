"""Custom exceptions for the cloud functions deployment pipeline."""


class CloudFunctionDirectoryNonExistent(Exception):
    """Raised when the specified cloud function directory does not exist."""

    def __init__(self, directory: str = ""):
        self.directory = directory
        super().__init__(f"Cloud function directory does not exist: {directory}")


class DeployFailed(Exception):
    """Raised when the deployment to Google Cloud Functions fails."""

    def __init__(self, message: str = "Deployment to Cloud Function failed"):
        super().__init__(message)


class MissingConfigError(Exception):
    """Raised when a required configuration parameter is missing."""

    def __init__(self, config_name: str):
        self.config_name = config_name
        super().__init__(f"Missing `{config_name}` config")
