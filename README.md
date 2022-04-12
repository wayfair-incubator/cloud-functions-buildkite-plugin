[![Actions Status](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/workflows/Lint/badge.svg?branch=main)](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/actions)
[![Actions Status](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/workflows/Unit%20Tests/badge.svg?branch=main)](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/actions)
![Version](https://img.shields.io/static/v1.svg?label=Version&message=0.1.2&color=lightgrey&?link=http://left&link=https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/tree/v0.1.2)
![Plugin Status](https://img.shields.io/static/v1.svg?label=&message=Buildkite%20Plugin&color=blue&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAMAAADVRocKAAAAk1BMVEX///+DrRik1Cb+/vyErhin1yeAqhfJ5n+dzCO50X2VwiC2zna020vg8LSo1i+q1zTN3qL7/fav2UDT4q33++yXuj3z+eLO6IqMuByJsSPM54XX5bWcvUbH5Xrg6sWiwVHB1ovk7cymxFnq8deOtC2xzG7c6L6/1YfU7JbI2pj2+e+jzzPd763K3J3j8ryRtDbY7aOqCe3pAAACTElEQVRoge3Z11KDQBSAYUpItSRqVGwxEVOwxPd/OndhCbA5BTaLM87sueb83+yMStHz3Lhx48bN/5iw+2VjImy0fDvzQiNCLKVrdjn0nq++QwNCLMy+9uOzc2Y59AZBwF4F55NefxxxyxK4aEvI/C7x/QxglrMTBNxVej6V+QNALh+AhkRY5isAsVwBxFWfM/rnLsu/qnwNQIkawBBy/abMawBCaEAQXGFElt/Evo8CIHEEIESWH9XyAAAQACCIH40A8yBwRICARiB5BNAIBKgQ8tLbCZBHgRqBAgWB5wmgQhCAIt7ekTwJ5AQHSGKC1TkgiM7WIs8A0bBvCETR8H7CA4EhIPP9fgPA7AR53u91BBR53+8EKPPdACLvq3wXQC1vH9DytoGjvF0gGo71vE0gCoC8PQDJ2wJEvgfmbQFo3g5A5HNA3K+eL0yBePdO5AtAEAOUoIB4c+ONiHwBZHddjMCB5DUV6yOqfzgBQWCAzMu9ZoAiHgACBpJdmj3SNAdQAgKSXfFQ1gZQz28PlxxQ5tsCIKED+6/qU2tbQBF3lxgwn9YfitsDR0QVmE9D7bHeBNCIEphf63lToEYUAJQ3BxSxlUQGPD3Cr5DmwIGQJ8DypwHqlXX7gec5oMcAXv5OT31OYU6weuM/9tDv/iSwWnJxfghA5s0+QzUCFi828iiwWNvJI4C9PAg8WcwDAPVLYwGwndeAufV8DZB/bm3nK0A3+RyI81tdF3l1gn1neQlM4qnpp+9ms0xP/P8AP/8778aNGzdu/mh+AQp1NCB/JInXAAAAAElFTkSuQmCC)

# Cloud Functions Buildkite Plugin

This buildkite plugin can be used to deploy code to Cloud Functions

See the [plugin tester](https://github.com/buildkite-plugins/buildkite-plugin-tester) for testing examples and usage, and the [Buildkite docs on writing plugins](https://buildkite.com/docs/plugins/writing) to understand everything in this repo.

## Using the plugin

If the version number is not provided then the most recent version of the plugin will be used. Do not use version number as `master` or any branch names.

### Simple

```yaml
steps:
  - plugins:
      - wayfair-incubator/cloud-functions#v0.1.2:
          gcp_project: "gcp-us-project"
          gcp_region: "us-central1"
          cloud_function_name: "function-1"
          cloud_function_directory: "directory/function-code"
```

## Configuration

### Required

### `gcp_project` (required, string)

The name of the GCP project you want to deploy.

Example: `gcp-us-project`

### `gcp_region` (required, string)

GCP region where the cloud function is hosted.

Example: `us-central1`

### `cloud_function_name` (required, string)

Name of the cloud function in GCP.

Example: `function-1`

### `cloud_function_directory` (required, string)

The directory in your repository where are you storing the code files for cloud function.

Example: `directory/function-code`

## Secret

This plugin expects `GCP_SERVICE_ACCOUNT` is placed as environment variable. Make sure to store it [securely](https://buildkite.com/docs/pipelines/secrets)!

```yaml
env:
  gcp_service_account: '{"email": ""}'
```

## Contributing

See the [Contributing Guide](CONTRIBUTING.md) for additional information.

To execute tests locally (requires that `docker` and `docker-compose` are installed):

```bash
docker-compose run py-test
```

## Credits

This plugin was originally written by [Jash Parekh](https://github.com/jashparekh) for Wayfair.
