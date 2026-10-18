"""Render the Buildkite annotation that summarises a deployment."""

import html
import os
from pathlib import Path
from typing import Any


def _row(label: str, value: Any) -> str:
    return f"<tr><td>{html.escape(label)}</td><td>{html.escape(str(value))}</td></tr>"


def render(report: dict[str, Any]) -> str:
    """
    Build the annotation body (HTML, which Buildkite annotations accept).

    Every value comes from the environment or an API error message, so it is
    escaped.
    """
    failed = bool(report.get("error"))
    icon = ":x:" if failed else ":white_check_mark:"
    mode = report.get("mode", "apply")
    result = (
        "failed"
        if failed
        else {"plan": "planned", "validate": "valid"}.get(mode, "deployed")
    )
    name = html.escape(str(report.get("function", "?")))

    rows = [
        _row("Result", result),
        _row("Project", report.get("project", "?")),
        _row("Region", report.get("region", "?")),
        _row("Generation", report.get("generation", "?")),
    ]
    if mode != "apply":
        rows.insert(0, _row("Mode", f"{mode} (nothing was changed)"))
    if report.get("runtime"):
        rows.append(_row("Runtime", report["runtime"]))
    if report.get("state"):
        rows.append(_row("Current state", report["state"]))
    if "files" in report:
        rows.append(
            _row(
                "Files uploaded" if mode == "apply" else "Files that would be uploaded",
                f"{report['files']} ({report['excluded']} excluded)",
            )
        )
    if "bytes" in report:
        rows.append(_row("Archive size", f"{report['bytes'] / 1024:.1f} KiB"))
    if report.get("operation"):
        rows.append(_row("Operation", report["operation"]))
    if mode == "apply":
        rows.append(
            _row("Waited for the operation", "yes" if report.get("wait") else "no")
        )
    if "seconds" in report:
        rows.append(_row("Time", f"{report['seconds']:.0f}s"))

    body = f"<h4>{icon} Cloud Function <code>{name}</code> {result}</h4>\n"
    body += f"<table>\n{chr(10).join(rows)}\n</table>\n"
    if failed:
        body += f"<pre>{html.escape(str(report['error']))}</pre>\n"
    return body


def write(path: str, report: dict[str, Any]) -> None:
    """Write the annotation to `path`; a problem here must never fail the deploy."""
    try:
        Path(path).write_text(render(report), encoding="utf-8")
    except OSError:
        pass


def annotation_path() -> str | None:
    """Where to write the annotation (the `annotation_file` variable), if at all."""
    return os.environ.get("annotation_file") or None
