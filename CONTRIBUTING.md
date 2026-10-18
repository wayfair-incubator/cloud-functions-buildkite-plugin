# How to Contribute

Thanks for your interest in contributing to `cloud-functions-buildkite-plugin`! Here are a few general guidelines on contributing and
reporting bugs that we ask you to review. Following these guidelines helps to communicate that you respect the time of
the contributors managing and developing this open source project. In return, they should reciprocate that respect in
addressing your issue, assessing changes, and helping you finalize your pull requests. In that spirit of mutual respect,
we endeavour to review incoming issues and pull requests within 10 days, and will close any lingering issues or pull
requests after 60 days of inactivity.

Please note that all of your interactions in the project are subject to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting Issues

Before reporting a new issue, please ensure that the issue was not already reported or fixed by searching through our
[issues list](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/issues).

When creating a new issue, please be sure to include a **title and clear description**, as much relevant information as
possible, and, if possible, a test case.

**If you discover a security bug, please do not report it through GitHub. Instead, please see security procedures in
[SECURITY.md](SECURITY.md).**

## Sending Pull Requests

Before sending a new pull request, take a look at existing pull requests and issues to see if the proposed change or fix
has been discussed in the past, or if the change was already implemented but not yet released.

We expect new pull requests to include tests for any affected behavior, and, as we follow semantic versioning, we may
reserve breaking changes until the next major version release.

## Releasing

Users pin a release tag, for example `wayfair-incubator/cloud-functions#v1.0.0`. A release is cut by a pull request:

1. In `CHANGELOG.md`, rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD` (follow
   [Semantic Versioning](https://semver.org/): breaking changes bump the major version) and add a fresh empty
   `## [Unreleased]` above it.
2. In `README.md`, update the plugin version in the usage examples and the version badge to `vX.Y.Z`.
3. Get the pull request approved and merge it.

The [Release workflow](.github/workflows/release.yml) then tags the merge commit `vX.Y.Z` and creates a GitHub
release whose notes are that changelog section. It does nothing if the release already exists, and fails if the
README does not mention the new version. It uses only the built-in `GITHUB_TOKEN`; no tokens or secrets are
needed. Do not create tags by hand. (A release created this way does not trigger other workflows that listen for
the `release` event.)

## Dependency updates

Dependencies are updated by [Renovate](https://docs.renovatebot.com/) (`renovate.json`); there is no
Dependabot. After changing a dependency, refresh `uv.lock` with `docker compose run --rm lock-requirements`
(or `uv lock`): CI fails when it is stale. It is the only lock file; the deploy container exports its
hashed requirements from it, so Renovate's lock file maintenance PRs need no manual follow-up.

## Other Ways to Contribute

We welcome anyone that wants to contribute to `cloud-functions-buildkite-plugin` to triage and reply to open issues to help troubleshoot
and fix existing bugs. Here is what you can do:

* Help ensure that existing issues follows the recommendations from the _[Reporting Issues](#reporting-issues)_ section,
  providing feedback to the issue's author on what might be missing.
* Review and update the existing content of our [Wiki](https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin/wiki) with up-to-date
  instructions and code samples.
* Review existing pull requests, and testing patches against real existing applications that use `cloud-functions-buildkite-plugin`.
* Write a test, or add a missing test case to an existing test.

Thanks again for your interest on contributing to `cloud-functions-buildkite-plugin`!

:heart:
