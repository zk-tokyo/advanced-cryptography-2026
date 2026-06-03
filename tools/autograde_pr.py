#!/usr/bin/env python3
"""Run the assignment autograder for GitHub pull requests.

This script is intended to run from a pull_request_target workflow. It treats
pull-request contents as untrusted data: it never checks out or executes the
PR head, and only runs grader code from the trusted base branch checkout.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


COMMENT_MARKER = "<!-- auto-grade -->"
STATUS_CONTEXT = "auto-grade"
SUBMISSION_RE = re.compile(
    r"^week(?P<week>[1-9][0-9]*)/exercises/submissions/(?P<submitter>[^/]+)/(?P<file>.+)$"
)


class AutogradeError(Exception):
    """Raised for expected autograding failures."""


@dataclass(frozen=True)
class PullRequestContext:
    owner: str
    repo: str
    number: int
    head_sha: str
    token: str
    run_url: str | None


@dataclass(frozen=True)
class Classification:
    should_grade: bool
    valid: bool
    week: str | None
    submitter: str | None
    reason: str


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    event = load_json(Path(args.event_path))
    context = build_context(event)

    try:
        files = list_pull_request_files(context)
        classification = classify_changed_files(files)

        if not classification.should_grade:
            create_commit_status(
                context,
                "success",
                "Not an assignment submission PR; skipped.",
            )
            print(classification.reason)
            return 0

        if not classification.valid:
            body = format_failure_comment("Invalid assignment submission", classification.reason)
            upsert_grade_comment(context, body)
            create_commit_status(context, "failure", "Invalid assignment submission PR.")
            print(classification.reason, file=sys.stderr)
            return 1

        config = prepare_runtime_config(Path(args.config), classification)
        with tempfile.TemporaryDirectory(prefix="autograde-") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            submission_dir = temp_dir / "submission"
            submission_dir.mkdir()

            download_submission_files(
                context=context,
                files=files,
                classification=classification,
                destination=submission_dir,
                max_bytes=int(config.get("max_submission_bytes", 200000)),
            )

            grade = run_week_grader(
                week=classification.week or "",
                submission_dir=submission_dir,
                config=config,
                temp_dir=temp_dir,
            )

        evaluated = evaluate_grade(grade, float(config["pass_score"]))
        upsert_grade_comment(context, format_grade_comment(evaluated, config))
        create_commit_status(
            context,
            "success" if evaluated["pass"] else "failure",
            f"Score {evaluated['score']:.2f}/{100}; pass score {float(config['pass_score']):.2f}.",
        )
        return 0 if evaluated["pass"] else 1
    except Exception as exc:
        body = format_failure_comment("Autograding failed", str(exc))
        upsert_grade_comment(context, body)
        create_commit_status(context, "failure", "Autograding failed.")
        print(str(exc), file=sys.stderr)
        return 1


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise AutogradeError(f"Expected JSON object in {path}")
    return data


def build_context(event: dict[str, Any]) -> PullRequestContext:
    pr = event.get("pull_request")
    repository = event.get("repository")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    if not isinstance(pr, dict) or not isinstance(repository, dict):
        raise AutogradeError("This workflow must run for a pull request event.")
    if not token:
        raise AutogradeError("GITHUB_TOKEN is required.")

    full_name = repository.get("full_name")
    if not isinstance(full_name, str) or "/" not in full_name:
        raise AutogradeError("repository.full_name is missing from the event payload.")
    owner, repo = full_name.split("/", 1)

    number = pr.get("number")
    head = pr.get("head")
    if not isinstance(number, int) or not isinstance(head, dict):
        raise AutogradeError("pull_request.number or pull_request.head is missing.")
    head_sha = head.get("sha")
    if not isinstance(head_sha, str) or not head_sha:
        raise AutogradeError("pull_request.head.sha is missing.")

    return PullRequestContext(
        owner=owner,
        repo=repo,
        number=number,
        head_sha=head_sha,
        token=token,
        run_url=os.environ.get("GITHUB_RUN_URL"),
    )


def github_request(
    context: PullRequestContext,
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {context.token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AutogradeError(f"GitHub API {method} {url} failed: {exc.code} {detail}") from exc

    if not payload:
        return None
    return json.loads(payload.decode("utf-8"))


def list_pull_request_files(context: PullRequestContext) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    page = 1
    while True:
        query = urllib.parse.urlencode({"per_page": "100", "page": str(page)})
        url = (
            f"https://api.github.com/repos/{context.owner}/{context.repo}"
            f"/pulls/{context.number}/files?{query}"
        )
        payload = github_request(context, "GET", url)
        if not isinstance(payload, list):
            raise AutogradeError("Unexpected response from GitHub pull request files API.")
        files.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < 100:
            return files
        page += 1


def classify_changed_files(files: list[dict[str, Any]]) -> Classification:
    if not files:
        return Classification(False, False, None, None, "No changed files; skipped.")

    touched_submission = False
    weeks: set[str] = set()
    submitters: set[str] = set()
    invalid_paths: list[str] = []

    for file_info in files:
        filename = str(file_info.get("filename", ""))
        paths_to_check = [filename]
        previous_filename = file_info.get("previous_filename")
        if isinstance(previous_filename, str) and previous_filename:
            paths_to_check.append(previous_filename)

        for path in paths_to_check:
            match = SUBMISSION_RE.match(path)
            if match:
                touched_submission = True
                weeks.add(f"week{match.group('week')}")
                submitters.add(match.group("submitter"))
            elif "/exercises/submissions/" in path:
                touched_submission = True
                invalid_paths.append(path)
            elif touched_any_submission_path(paths_to_check):
                invalid_paths.append(path)

    if not touched_submission:
        return Classification(False, True, None, None, "No assignment submission files changed.")

    external_paths = [
        str(file_info.get("filename", ""))
        for file_info in files
        if not SUBMISSION_RE.match(str(file_info.get("filename", "")))
    ]
    invalid_paths.extend(path for path in external_paths if path)

    if invalid_paths:
        unique_paths = ", ".join(sorted(set(invalid_paths))[:10])
        return Classification(
            True,
            False,
            None,
            None,
            f"Submission PRs may only change files under one week submission directory. Invalid path(s): {unique_paths}",
        )

    if len(weeks) != 1 or len(submitters) != 1:
        return Classification(
            True,
            False,
            None,
            None,
            "Submission PRs must target exactly one week and one submitter.",
        )

    week = next(iter(weeks))
    submitter = next(iter(submitters))
    return Classification(
        True,
        True,
        week,
        submitter,
        f"Detected submission for {week} by {submitter}.",
    )


def touched_any_submission_path(paths: list[str]) -> bool:
    return any("/exercises/submissions/" in path for path in paths)


def prepare_runtime_config(config_path: Path, classification: Classification) -> dict[str, Any]:
    config = load_simple_yaml(config_path)
    week = classification.week or ""

    env_provider = os.environ.get("AUTOGRADE_PROVIDER")
    env_model = os.environ.get("AUTOGRADE_MODEL")
    if env_provider:
        config["provider"] = env_provider
    if env_model:
        config["model"] = env_model

    config.setdefault("provider", "openrouter")
    config.setdefault("pass_score", 70)
    config["week"] = week
    config["submitter"] = classification.submitter or ""

    if config["provider"] != "openrouter":
        raise AutogradeError("Only provider=openrouter is supported in v1.")
    if "model" not in config or not str(config["model"]).strip():
        raise AutogradeError("Autograde model is not configured.")

    return config


def load_simple_yaml(path: Path) -> dict[str, Any]:
    """Load the small YAML subset used by .github/autograde/config.yml."""
    result: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, result)]

    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()
            if ":" not in stripped:
                raise AutogradeError(f"Invalid config line {line_number}: {raw_line.rstrip()}")
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()

            while stack and indent <= stack[-1][0]:
                stack.pop()
            if not stack:
                raise AutogradeError(f"Invalid indentation at config line {line_number}")
            parent = stack[-1][1]

            if value == "":
                child: dict[str, Any] = {}
                parent[key] = child
                stack.append((indent, child))
            else:
                parent[key] = parse_scalar(value)

    return result


def parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("\"'")


def download_submission_files(
    context: PullRequestContext,
    files: list[dict[str, Any]],
    classification: Classification,
    destination: Path,
    max_bytes: int,
) -> None:
    prefix = f"{classification.week}/exercises/submissions/{classification.submitter}/"
    total_bytes = 0

    for file_info in files:
        filename = str(file_info.get("filename", ""))
        status = str(file_info.get("status", ""))
        if not filename.startswith(prefix) or status == "removed":
            continue

        relative_path = safe_relative_submission_path(filename[len(prefix) :])
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)

        content = download_changed_file(context, file_info)
        total_bytes += len(content)
        if total_bytes > max_bytes:
            raise AutogradeError(f"Submission exceeds max_submission_bytes={max_bytes}.")
        target.write_bytes(content)


def safe_relative_submission_path(path: str) -> Path:
    pure_path = PurePosixPath(path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise AutogradeError(f"Unsafe submission path: {path}")
    return Path(*pure_path.parts)


def download_changed_file(context: PullRequestContext, file_info: dict[str, Any]) -> bytes:
    raw_url = file_info.get("raw_url")
    if isinstance(raw_url, str) and raw_url:
        try:
            request = urllib.request.Request(raw_url)
            request.add_header("Authorization", f"Bearer {context.token}")
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError:
            pass

    contents_url = file_info.get("contents_url")
    if not isinstance(contents_url, str) or not contents_url:
        raise AutogradeError(f"Cannot download changed file: {file_info.get('filename')}")

    separator = "&" if "?" in contents_url else "?"
    payload = github_request(context, "GET", f"{contents_url}{separator}ref={context.head_sha}")
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        raise AutogradeError(f"Unexpected contents response for {file_info.get('filename')}")
    content = payload.get("content")
    if not isinstance(content, str):
        raise AutogradeError(f"Missing contents for {file_info.get('filename')}")
    return base64.b64decode(content)


def run_week_grader(
    week: str,
    submission_dir: Path,
    config: dict[str, Any],
    temp_dir: Path,
) -> dict[str, Any]:
    grader_path = Path(week) / "exercises" / "grader.py"
    if not grader_path.exists():
        raise AutogradeError(
            f"{grader_path} does not exist. Copy .github/autograde/examples/grader.py and customize it."
        )

    config_path = temp_dir / "config.json"
    output_path = temp_dir / "grade.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH")
    repo_root = str(Path.cwd())
    env["PYTHONPATH"] = (
        repo_root if not existing_pythonpath else f"{repo_root}{os.pathsep}{existing_pythonpath}"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(grader_path),
            "--submission-dir",
            str(submission_dir),
            "--config",
            str(config_path),
            "--output",
            str(output_path),
        ],
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise AutogradeError(f"{grader_path} failed: {details}")
    if not output_path.exists():
        raise AutogradeError(f"{grader_path} did not write {output_path}.")

    return load_json(output_path)


def evaluate_grade(grade: dict[str, Any], pass_score: float) -> dict[str, Any]:
    score = grade.get("score")
    if not isinstance(score, (int, float)):
        raise AutogradeError("grader output must include numeric score.")
    if score < 0 or score > 100:
        raise AutogradeError("grader score must be between 0 and 100.")

    summary = grade.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise AutogradeError("grader output must include non-empty summary.")

    items = grade.get("items")
    if not isinstance(items, list):
        raise AutogradeError("grader output must include items list.")

    needs_human_review = grade.get("needs_human_review", False)
    if not isinstance(needs_human_review, bool):
        raise AutogradeError("needs_human_review must be a boolean.")

    evaluated = dict(grade)
    evaluated["score"] = float(score)
    evaluated["pass"] = float(score) >= pass_score
    evaluated["needs_human_review"] = needs_human_review
    return evaluated


def format_grade_comment(grade: dict[str, Any], config: dict[str, Any]) -> str:
    status = "PASS" if grade["pass"] else "FAIL"
    pass_score = float(config["pass_score"])
    lines = [
        COMMENT_MARKER,
        "## Auto Grade",
        "",
        f"- Result: **{status}**",
        f"- Score: **{grade['score']:.2f} / 100**",
        f"- Pass score: **{pass_score:.2f}**",
        f"- Model: `{config.get('model')}`",
        f"- Human review suggested: **{str(grade.get('needs_human_review', False)).lower()}**",
        "",
        "### Summary",
        "",
        str(grade["summary"]).strip(),
    ]

    items = grade.get("items", [])
    if items:
        lines.extend(["", "### Rubric Items", ""])
        for item in items:
            if isinstance(item, dict):
                name = item.get("name", "item")
                points = item.get("points", "?")
                max_points = item.get("max_points", "?")
                comment = item.get("comment", "")
                lines.append(f"- **{name}**: {points}/{max_points} - {comment}")
    return "\n".join(lines) + "\n"


def format_failure_comment(title: str, message: str) -> str:
    return "\n".join(
        [
            COMMENT_MARKER,
            "## Auto Grade",
            "",
            f"**{title}**",
            "",
            message,
            "",
        ]
    )


def upsert_grade_comment(context: PullRequestContext, body: str) -> None:
    comments_url = (
        f"https://api.github.com/repos/{context.owner}/{context.repo}"
        f"/issues/{context.number}/comments"
    )
    comments = github_request(context, "GET", f"{comments_url}?per_page=100")
    if not isinstance(comments, list):
        raise AutogradeError("Unexpected response from GitHub comments API.")

    existing_id: int | None = None
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        comment_body = comment.get("body")
        comment_id = comment.get("id")
        if isinstance(comment_body, str) and COMMENT_MARKER in comment_body and isinstance(comment_id, int):
            existing_id = comment_id
            break

    if existing_id is None:
        github_request(context, "POST", comments_url, {"body": body})
    else:
        update_url = (
            f"https://api.github.com/repos/{context.owner}/{context.repo}"
            f"/issues/comments/{existing_id}"
        )
        github_request(context, "PATCH", update_url, {"body": body})


def create_commit_status(context: PullRequestContext, state: str, description: str) -> None:
    url = f"https://api.github.com/repos/{context.owner}/{context.repo}/statuses/{context.head_sha}"
    body: dict[str, Any] = {
        "state": state,
        "context": STATUS_CONTEXT,
        "description": description[:140],
    }
    if context.run_url:
        body["target_url"] = context.run_url
    github_request(context, "POST", url, body)


if __name__ == "__main__":
    raise SystemExit(main())
