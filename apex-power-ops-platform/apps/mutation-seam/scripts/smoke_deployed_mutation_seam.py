from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib import error, parse, request


DEFAULT_TIMEOUT_SECONDS = 20


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            'Validate that a deployed mutation-seam host exposes the PM runtime routes '
            'needed by operations-web.'
        )
    )
    parser.add_argument('--base-url', required=True, help='Base URL for the target mutation-seam host.')
    parser.add_argument(
        '--timeout-seconds',
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help='HTTP timeout for each request.',
    )
    return parser


def request_json(url: str, *, timeout_seconds: int) -> tuple[int, Any]:
    req = request.Request(url, headers={'Accept': 'application/json'})
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode('utf-8')
            payload = json.loads(raw) if raw.strip() else {}
            return response.status, payload
    except error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='replace')
        try:
            payload = json.loads(detail) if detail.strip() else {'detail': exc.reason}
        except json.JSONDecodeError:
            payload = {'detail': detail or exc.reason}
        return exc.code, payload
    except error.URLError as exc:
        raise RuntimeError(f'Failed to reach {url}: {exc.reason}') from exc


def response_detail(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ''
    detail = payload.get('detail')
    return str(detail).strip() if detail is not None else ''


def expect_status(
    *,
    label: str,
    status: int,
    payload: Any,
    allowed_statuses: set[int],
    failures: list[str],
) -> None:
    detail = response_detail(payload)
    print(f'{label} status={status} detail={detail or "ok"}')
    if status == 404 and detail == 'Not Found':
        failures.append(f'{label} returned framework 404 Not Found')
        return
    if status not in allowed_statuses:
        failures.append(f'{label} returned unexpected status {status}')


def main() -> int:
    args = build_parser().parse_args()
    base_url = args.base_url.rstrip('/')
    failures: list[str] = []

    checks = [
        ('health', '/health', {200}),
        ('root', '/', {200}),
        ('reads_approval_queue', '/api/v1/reads/approval-queue', {200}),
        ('schedule_projects', '/api/v1/schedule/projects', {200, 503}),
        ('schedule_drivers', '/api/v1/schedule/drivers', {200, 503}),
        (
            'schedule_tracer',
            '/api/v1/schedule/tracer?' + parse.urlencode({'task_id': 'probe-task'}),
            {200, 503},
        ),
        ('schedule_variance', '/api/v1/schedule/variance', {200, 503}),
    ]

    for label, path, allowed_statuses in checks:
        status, payload = request_json(f'{base_url}{path}', timeout_seconds=args.timeout_seconds)
        expect_status(
            label=label,
            status=status,
            payload=payload,
            allowed_statuses=allowed_statuses,
            failures=failures,
        )

    if failures:
        print('RESULT FAIL')
        for failure in failures:
            print(f'FAILURE {failure}')
        return 1

    print('RESULT PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())