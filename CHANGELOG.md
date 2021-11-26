# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.5.0] - 2021-08-13

### Changed

* Added logic to use archive_url to upload the source_code to storage bucket if present else use upload_url.
* Changed logic of preparing the payload to cloud function's patch method.
* Removed the unused plugin variables. 

## [v0.4.3] - 2021-08-03

### Changed

* Added logic to pass 'serviceAccountEmail' from the service account credentials to cloud function's patch API.

## [v0.4.2] - 2021-06-08

### Changed

* Added logic to pass 'Runtime environment variables' to cloud functions.

## [v0.4.1] - 2021-06-06

### Changed

* Changed directory archive logic to retain package structure.

## [v0.4.0] - 2021-05-17

### Changed

* Pipeline logic to deploy to non 'prod' project too.

## [v0.3.0] - 2021-04-19

### Changed

* Update Dev image version logic to use current commit hash
* Update Prod image version logic to mirror plugin version

## Added

* Added new plugin_image_version param for use in testing

## [v0.2.0] - 2021-05-07

## Changed

* Deprecate setting egress proxy explicitly
* Python version and docker image version

### Added

* Dependabot and Dozer config


## [v0.1.0] - 2021-01-29

* Initial Release