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
    parser.add_argument(
        '--include-temp-power-actuals-review',
        action='store_true',
        help='Also validate Temp Power actuals-capture review route registration and readback shape without sending a POST.',
    )
    parser.add_argument(
        '--include-temp-power-customer-preview-review',
        action='store_true',
        help='Also validate Temp Power customer-preview review route registration and readback shape without sending a POST.',
    )
    parser.add_argument(
        '--include-temp-power-customer-delivery-proof-review',
        action='store_true',
        help='Also validate Temp Power customer-delivery/durable-proof review route registration and readback shape without sending a POST.',
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


def expect_openapi_methods(*, payload: Any, required_methods: dict[str, set[str]], failures: list[str]) -> None:
    paths = payload.get('paths') if isinstance(payload, dict) else None
    if not isinstance(paths, dict):
        return
    for route_path, route_methods in sorted(required_methods.items()):
        route_spec = paths.get(route_path)
        if not isinstance(route_spec, dict):
            continue
        available_methods = {method.lower() for method in route_spec}
        for route_method in sorted(route_methods):
            if route_method.lower() not in available_methods:
                failures.append(f'openapi missing {route_method.upper()} {route_path}')


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
            '/api/v1/reads/project-import-approval-status',
            '/api/v1/reads/durable-field-record-status',
            '/api/v1/reads/production-tracking-status',
            '/api/v1/reads/customer-completion-status',
            '/api/v1/reads/financial-handoff-status',
            '/api/v1/mutations/project-import-approvals',
            '/api/v1/mutations/durable-field-records',
            '/api/v1/mutations/production-tracking',
            '/api/v1/mutations/customer-completion',
            '/api/v1/mutations/financial-handoff',
        }
        required_openapi_methods = {
            '/api/v1/reads/project-import-approval-status': {'get'},
            '/api/v1/reads/durable-field-record-status': {'get'},
            '/api/v1/reads/production-tracking-status': {'get'},
            '/api/v1/reads/customer-completion-status': {'get'},
            '/api/v1/reads/financial-handoff-status': {'get'},
            '/api/v1/mutations/project-import-approvals': {'post'},
            '/api/v1/mutations/durable-field-records': {'post'},
            '/api/v1/mutations/production-tracking': {'post'},
            '/api/v1/mutations/customer-completion': {'post'},
            '/api/v1/mutations/financial-handoff': {'post'},
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
            expect_openapi_methods(payload=payload, required_methods=required_openapi_methods, failures=failures)

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
            (
                'project_import_approval_status',
                '/api/v1/reads/project-import-approval-status',
                {
                    'classification',
                    'source',
                    'route',
                    'approval_storage_available',
                    'audit_log_used_for_current_status',
                    'import_authority',
                },
            ),
            (
                'durable_field_record_status',
                '/api/v1/reads/durable-field-record-status',
                {
                    'classification',
                    'route',
                    'production_tracking_authority',
                    'customer_reporting_authority',
                    'finance_authority',
                },
            ),
            (
                'production_tracking_status',
                '/api/v1/reads/production-tracking-status',
                {
                    'classification',
                    'route',
                    'production_tracking_authority',
                    'customer_reporting_authority',
                    'finance_authority',
                },
            ),
            (
                'customer_completion_status',
                '/api/v1/reads/customer-completion-status',
                {
                    'classification',
                    'route',
                    'production_tracking_authority',
                    'customer_reporting_authority',
                    'completion_evidence_authority',
                    'customer_delivery_authority',
                    'finance_authority',
                    'billing_authority',
                    'payroll_authority',
                    'invoice_authority',
                    'accounting_authority',
                },
            ),
            (
                'financial_handoff_status',
                '/api/v1/reads/financial-handoff-status',
                {
                    'classification',
                    'route',
                    'financial_handoff_authority',
                    'labor_reconciliation_authority',
                    'finance_authority',
                    'billing_export_authority',
                    'payroll_export_authority',
                    'invoice_authority',
                    'accounting_authority',
                    'external_finance_sync_authority',
                    'customer_billing_delivery_authority',
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
                if label == 'project_import_approval_status':
                    if isinstance(payload, dict) and payload.get('import_authority') != 'not_admitted':
                        failures.append(f'{label} returned import_authority={payload.get("import_authority")}')
                    if isinstance(payload, dict) and payload.get('approval_storage_available') is not True:
                        failures.append(
                            f'{label} returned approval_storage_available={payload.get("approval_storage_available")}'
                        )
                    if isinstance(payload, dict) and payload.get('audit_log_used_for_current_status') is not False:
                        failures.append(
                            f'{label} returned audit_log_used_for_current_status={payload.get("audit_log_used_for_current_status")}'
                        )
                elif label == 'durable_field_record_status':
                    if isinstance(payload, dict) and payload.get('storage_available') is not True:
                        failures.append(f'{label} returned storage_available={payload.get("storage_available")}')
                    for authority_field in [
                        'production_tracking_authority',
                        'customer_reporting_authority',
                        'finance_authority',
                    ]:
                        if isinstance(payload, dict) and payload.get(authority_field) != 'not_admitted':
                            failures.append(f'{label} returned {authority_field}={payload.get(authority_field)}')
                elif label == 'production_tracking_status':
                    if isinstance(payload, dict) and payload.get('storage_available') is not True:
                        failures.append(f'{label} returned storage_available={payload.get("storage_available")}')
                    if (
                        isinstance(payload, dict)
                        and payload.get('production_tracking_authority')
                        != 'admitted_by_pm_lane_282_zero_actual_baseline'
                    ):
                        failures.append(
                            f'{label} returned production_tracking_authority='
                            f'{payload.get("production_tracking_authority")}'
                        )
                    for authority_field in ['customer_reporting_authority', 'finance_authority']:
                        if isinstance(payload, dict) and payload.get(authority_field) != 'not_admitted':
                            failures.append(f'{label} returned {authority_field}={payload.get(authority_field)}')
                elif label == 'customer_completion_status':
                    if isinstance(payload, dict) and payload.get('storage_available') is not True:
                        failures.append(f'{label} returned storage_available={payload.get("storage_available")}')
                    if (
                        isinstance(payload, dict)
                        and payload.get('production_tracking_authority')
                        != 'admitted_by_pm_lane_282_zero_actual_baseline'
                    ):
                        failures.append(
                            f'{label} returned production_tracking_authority='
                            f'{payload.get("production_tracking_authority")}'
                        )
                    if (
                        isinstance(payload, dict)
                        and payload.get('customer_reporting_authority')
                        != 'admitted_by_pm_lane_283_customer_completion_baseline'
                    ):
                        failures.append(
                            f'{label} returned customer_reporting_authority='
                            f'{payload.get("customer_reporting_authority")}'
                        )
                    if (
                        isinstance(payload, dict)
                        and payload.get('completion_evidence_authority')
                        != 'admitted_by_pm_lane_283_zero_evidence_baseline'
                    ):
                        failures.append(
                            f'{label} returned completion_evidence_authority='
                            f'{payload.get("completion_evidence_authority")}'
                        )
                    if (
                        isinstance(payload, dict)
                        and payload.get('customer_delivery_authority') != 'not_admitted_external_delivery'
                    ):
                        failures.append(
                            f'{label} returned customer_delivery_authority='
                            f'{payload.get("customer_delivery_authority")}'
                        )
                    for authority_field in [
                        'finance_authority',
                        'billing_authority',
                        'payroll_authority',
                        'invoice_authority',
                        'accounting_authority',
                    ]:
                        if isinstance(payload, dict) and payload.get(authority_field) != 'not_admitted':
                            failures.append(f'{label} returned {authority_field}={payload.get(authority_field)}')
                elif label == 'financial_handoff_status':
                    if isinstance(payload, dict) and payload.get('storage_available') is not True:
                        failures.append(f'{label} returned storage_available={payload.get("storage_available")}')
                    if (
                        isinstance(payload, dict)
                        and payload.get('financial_handoff_authority')
                        != 'admitted_by_pm_lane_284_zero_finance_handoff_baseline'
                    ):
                        failures.append(
                            f'{label} returned financial_handoff_authority='
                            f'{payload.get("financial_handoff_authority")}'
                        )
                    if (
                        isinstance(payload, dict)
                        and payload.get('labor_reconciliation_authority')
                        != 'admitted_by_pm_lane_284_zero_labor_reconciliation_baseline'
                    ):
                        failures.append(
                            f'{label} returned labor_reconciliation_authority='
                            f'{payload.get("labor_reconciliation_authority")}'
                        )
                    for authority_field in [
                        'finance_authority',
                        'billing_export_authority',
                        'payroll_export_authority',
                        'invoice_authority',
                        'accounting_authority',
                        'external_finance_sync_authority',
                        'customer_billing_delivery_authority',
                    ]:
                        if isinstance(payload, dict) and payload.get(authority_field) != 'not_admitted':
                            failures.append(f'{label} returned {authority_field}={payload.get(authority_field)}')
                elif isinstance(payload, dict) and payload.get('mutation_authority') != 'not_admitted':
                    failures.append(f'{label} returned mutation_authority={payload.get("mutation_authority")}')

    if args.include_temp_power_actuals_review:
        actuals_paths = {
            '/api/v1/reads/temp-power-actuals-capture-review-status',
            '/api/v1/mutations/temp-power-actuals-capture-reviews',
        }
        actuals_methods = {
            '/api/v1/reads/temp-power-actuals-capture-review-status': {'get'},
            '/api/v1/mutations/temp-power-actuals-capture-reviews': {'post'},
        }
        status, payload = request_json(f'{base_url}/openapi.json', timeout_seconds=args.timeout_seconds)
        expect_status(
            label='openapi_temp_power_actuals_review',
            status=status,
            payload=payload,
            allowed_statuses={200},
            failures=failures,
        )
        if status == 200:
            expect_openapi_paths(payload=payload, required_paths=actuals_paths, failures=failures)
            expect_openapi_methods(payload=payload, required_methods=actuals_methods, failures=failures)

        status, payload = request_json(
            f'{base_url}/api/v1/reads/temp-power-actuals-capture-review-status',
            timeout_seconds=args.timeout_seconds,
            headers=pm_auth_header(),
        )
        expect_status(
            label='temp_power_actuals_capture_review_status',
            status=status,
            payload=payload,
            allowed_statuses={200},
            failures=failures,
        )
        if status == 200:
            expect_fields(
                label='temp_power_actuals_capture_review_status',
                payload=payload,
                required_fields={
                    'project_id',
                    'candidate_id',
                    'source_fingerprint',
                    'current_candidate_match',
                    'current_source_fingerprint_match',
                    'status',
                    'record_count',
                    'storage_route_registered',
                    'storage_source',
                    'entity_type',
                    'customer_delivery_authority',
                    'finance_authority',
                    'source_writeback_authority',
                    'durable_delivery_event',
                },
                failures=failures,
            )
            if isinstance(payload, dict) and payload.get('storage_route_registered') is not True:
                failures.append(
                    'temp_power_actuals_capture_review_status returned '
                    f'storage_route_registered={payload.get("storage_route_registered")}'
                )
            for authority_field in [
                'customer_delivery_authority',
                'finance_authority',
                'source_writeback_authority',
            ]:
                if isinstance(payload, dict) and payload.get(authority_field) != 'not_admitted':
                    failures.append(
                        'temp_power_actuals_capture_review_status returned '
                        f'{authority_field}={payload.get(authority_field)}'
                    )
            if isinstance(payload, dict) and payload.get('durable_delivery_event') is not False:
                failures.append(
                    'temp_power_actuals_capture_review_status returned '
                    f'durable_delivery_event={payload.get("durable_delivery_event")}'
                )

    if args.include_temp_power_customer_preview_review:
        customer_preview_paths = {
            '/api/v1/reads/temp-power-customer-preview-status',
            '/api/v1/mutations/temp-power-customer-preview-reviews',
        }
        customer_preview_methods = {
            '/api/v1/reads/temp-power-customer-preview-status': {'get'},
            '/api/v1/mutations/temp-power-customer-preview-reviews': {'post'},
        }
        status, payload = request_json(f'{base_url}/openapi.json', timeout_seconds=args.timeout_seconds)
        expect_status(
            label='openapi_temp_power_customer_preview_review',
            status=status,
            payload=payload,
            allowed_statuses={200},
            failures=failures,
        )
        if status == 200:
            expect_openapi_paths(payload=payload, required_paths=customer_preview_paths, failures=failures)
            expect_openapi_methods(payload=payload, required_methods=customer_preview_methods, failures=failures)

        status, payload = request_json(
            f'{base_url}/api/v1/reads/temp-power-customer-preview-status',
            timeout_seconds=args.timeout_seconds,
            headers=pm_auth_header(),
        )
        expect_status(
            label='temp_power_customer_preview_status',
            status=status,
            payload=payload,
            allowed_statuses={200},
            failures=failures,
        )
        if status == 200:
            expect_fields(
                label='temp_power_customer_preview_status',
                payload=payload,
                required_fields={
                    'project_id',
                    'candidate_id',
                    'source_fingerprint',
                    'current_candidate_match',
                    'current_source_fingerprint_match',
                    'status',
                    'record_count',
                    'storage_route_registered',
                    'storage_source',
                    'entity_type',
                    'customer_delivery_authority',
                    'finance_authority',
                    'source_writeback_authority',
                    'durable_delivery_event',
                    'delivery_proof_recorded',
                },
                failures=failures,
            )
            if isinstance(payload, dict) and payload.get('storage_route_registered') is not True:
                failures.append(
                    'temp_power_customer_preview_status returned '
                    f'storage_route_registered={payload.get("storage_route_registered")}'
                )
            for authority_field in [
                'customer_delivery_authority',
                'finance_authority',
                'source_writeback_authority',
            ]:
                if isinstance(payload, dict) and payload.get(authority_field) != 'not_admitted':
                    failures.append(
                        'temp_power_customer_preview_status returned '
                        f'{authority_field}={payload.get(authority_field)}'
                    )
            if isinstance(payload, dict) and payload.get('durable_delivery_event') is not False:
                failures.append(
                    'temp_power_customer_preview_status returned '
                    f'durable_delivery_event={payload.get("durable_delivery_event")}'
                )
            if isinstance(payload, dict) and payload.get('delivery_proof_recorded') is not False:
                failures.append(
                    'temp_power_customer_preview_status returned '
                    f'delivery_proof_recorded={payload.get("delivery_proof_recorded")}'
                )

    if args.include_temp_power_customer_delivery_proof_review:
        delivery_proof_paths = {
            '/api/v1/reads/temp-power-customer-delivery-proof-status',
            '/api/v1/mutations/temp-power-customer-delivery-proof-reviews',
        }
        delivery_proof_methods = {
            '/api/v1/reads/temp-power-customer-delivery-proof-status': {'get'},
            '/api/v1/mutations/temp-power-customer-delivery-proof-reviews': {'post'},
        }
        status, payload = request_json(f'{base_url}/openapi.json', timeout_seconds=args.timeout_seconds)
        expect_status(
            label='openapi_temp_power_customer_delivery_proof_review',
            status=status,
            payload=payload,
            allowed_statuses={200},
            failures=failures,
        )
        if status == 200:
            expect_openapi_paths(payload=payload, required_paths=delivery_proof_paths, failures=failures)
            expect_openapi_methods(payload=payload, required_methods=delivery_proof_methods, failures=failures)

        status, payload = request_json(
            f'{base_url}/api/v1/reads/temp-power-customer-delivery-proof-status',
            timeout_seconds=args.timeout_seconds,
            headers=pm_auth_header(),
        )
        expect_status(
            label='temp_power_customer_delivery_proof_status',
            status=status,
            payload=payload,
            allowed_statuses={200},
            failures=failures,
        )
        if status == 200:
            expect_fields(
                label='temp_power_customer_delivery_proof_status',
                payload=payload,
                required_fields={
                    'project_id',
                    'candidate_id',
                    'source_fingerprint',
                    'preview_review_id',
                    'current_candidate_match',
                    'current_source_fingerprint_match',
                    'preview_review_lineage_match',
                    'status',
                    'record_count',
                    'storage_route_registered',
                    'storage_source',
                    'entity_type',
                    'finance_authority',
                    'source_writeback_authority',
                    'customer_billing_delivery_authority',
                },
                failures=failures,
            )
            if isinstance(payload, dict) and payload.get('storage_route_registered') is not True:
                failures.append(
                    'temp_power_customer_delivery_proof_status returned '
                    f'storage_route_registered={payload.get("storage_route_registered")}'
                )
            for authority_field in [
                'finance_authority',
                'source_writeback_authority',
                'customer_billing_delivery_authority',
            ]:
                if isinstance(payload, dict) and payload.get(authority_field) != 'not_admitted':
                    failures.append(
                        'temp_power_customer_delivery_proof_status returned '
                        f'{authority_field}={payload.get(authority_field)}'
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
