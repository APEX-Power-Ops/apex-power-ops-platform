from __future__ import annotations

import argparse
import base64
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
    parser.add_argument(
        '--include-pm-intake',
        action='store_true',
        help='Also validate Project Miner PM intake read routes and OpenAPI registration.',
    )
    return parser


def pm_auth_header() -> dict[str, str]:
    payload = {
        'actor_id': 'pm-001',
        'actor_role': 'pm',
        'project_scope': ['proj-001'],
    }
    token = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('ascii')
    return {'Authorization': f'Bearer {token}'}


def request_json(url: str, *, timeout_seconds: int, headers: dict[str, str] | None = None) -> tuple[int, Any]:
    request_headers = {'Accept': 'application/json'}
    request_headers.update(headers or {})
    req = request.Request(url, headers=request_headers)
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


def expect_openapi_paths(*, payload: Any, required_paths: set[str], failures: list[str]) -> None:
    paths = payload.get('paths') if isinstance(payload, dict) else None
    if not isinstance(paths, dict):
        failures.append('openapi returned payload without paths object')
        return
    for route_path in sorted(required_paths):
        if route_path not in paths:
            failures.append(f'openapi missing {route_path}')


def expect_fields(*, label: str, payload: Any, required_fields: set[str], failures: list[str]) -> None:
    if not isinstance(payload, dict):
        failures.append(f'{label} returned non-object payload')
        return
    for field in sorted(required_fields):
        if field not in payload:
            failures.append(f'{label} missing field {field}')


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

    if args.include_pm_intake:
        intake_paths = {
            '/api/v1/reads/project-import-candidate',
            '/api/v1/reads/project-import-admission-plan',
            '/api/v1/reads/project-import-approval-contract',
            '/api/v1/reads/project-import-approval-storage-plan',
        }
        status, payload = request_json(f'{base_url}/openapi.json', timeout_seconds=args.timeout_seconds)
        expect_status(
            label='openapi',
            status=status,
            payload=payload,
            allowed_statuses={200},
            failures=failures,
        )
        if status == 200:
            expect_openapi_paths(payload=payload, required_paths=intake_paths, failures=failures)

        intake_checks = [
            (
                'project_import_candidate',
                '/api/v1/reads/project-import-candidate',
                {'candidate_id', 'mutation_authority', 'source_freshness'},
            ),
            (
                'project_import_admission_plan',
                '/api/v1/reads/project-import-admission-plan',
                {'admission_plan_id', 'approval_record_contract', 'mutation_authority', 'no_go_checks'},
            ),
            (
                'project_import_approval_contract',
                '/api/v1/reads/project-import-approval-contract',
                {
                    'approval_contract_id',
                    'decision_payload_template',
                    'mutation_authority',
                    'persistence_authority',
                },
            ),
            (
                'project_import_approval_storage_plan',
                '/api/v1/reads/project-import-approval-storage-plan',
                {
                    'recommended_table',
                    'selected_storage_decision',
                    'mutation_authority',
                    'persistence_authority',
                },
            ),
        ]
        for label, path, required_fields in intake_checks:
            status, payload = request_json(
                f'{base_url}{path}',
                timeout_seconds=args.timeout_seconds,
                headers=pm_auth_header(),
            )
            expect_status(
                label=label,
                status=status,
                payload=payload,
                allowed_statuses={200},
                failures=failures,
            )
            if status == 200:
                expect_fields(label=label, payload=payload, required_fields=required_fields, failures=failures)
                if isinstance(payload, dict) and payload.get('mutation_authority') != 'not_admitted':
                    failures.append(f'{label} returned mutation_authority={payload.get("mutation_authority")}')

    if failures:
        print('RESULT FAIL')
        for failure in failures:
            print(f'FAILURE {failure}')
        return 1

    print('RESULT PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
