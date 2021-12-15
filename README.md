# Cloud Functions Buildkite Plugin

This buildkite plugin can be used to deploy code to Cloud Functions

See the [plugin tester](https://github.com/buildkite-plugins/buildkite-plugin-tester) for testing examples and usage, and the (Buildkite docs on writing plugins)[https://buildkite.com/docs/plugins/writing] to understand everything in this repo.

[![Build status](https://badge.buildkite.com/d386e7f164ca1a3164302c7b17dca216c8ddcc8806d20c45db.svg?branch=master)](https://buildkite.com/wayfair/deploy-cloud-functions-buildkite-plugin)

## Configuration

### Required

### `gcp_project` (required, string)

The name of the GCP project you want to deploy.

Example: `wf-gcp-us-ae-buyfair-dev`

### `gcp_region` (required, string)

GCP region where the cloud function is hosted.

Example: `us-central1`

### `cloud_function_name` (required, string)

Name of the cloud function in GCP.

Example: `function-1`

### `cloud_function_directory` (required, string)

The directory in your repository where are you storing the code files for cloud function.

Example: `wf-gcp-project/function-1`

## Secret

This plugin expects `GCP_SERVICE_ACCOUNT` is placed as environment variable. Make sure to store it [securely](https://buildkite.com/docs/pipelines/secrets)!

```yaml
env:
  gcp_service_account: '{"email": ""}'
```


## Using the plugin

If the version number is not provided then the most recent version of the plugin will be used. Do not use version number as `master` or any branch names.

### Simple

```yaml
steps:
  - plugins:
      - wayfair-incubator/cloud-functions#v0.1.0:
          gcp_project: "gcp-us-project"
          gcp_region: "us-central1"
          cloud_function_name: "function-1"
          cloud_function_directory: "directory/project"
```

## Developing

You can use the [bk cli](https://github.com/buildkite/cli) to run the test pipeline locally, or just the tests using Docker Compose directly:

```bash
docker-compose run --rm py-test
```

You can also run linting using Docker Compose directly:

```bash
docker-compose run --rm lint
```

# Authors
`Jash Parekh <jash389@gmail.com>`
