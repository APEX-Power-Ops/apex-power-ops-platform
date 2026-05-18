import base64
import json

from openpyxl import Workbook

from app.db.memory_store import store
from app.project_import_candidate import clear_project_import_candidate_cache, load_project_import_candidate
from app.project_import_task_plan_persistence import build_project_import_task_plan_id, load_project_import_task_plan_status
from app.project_seed_sources import clear_project_seed_cache
from app.project_tracker_sources import clear_project_tracker_cache
from app.seed_workbooks import clear_seed_cache


def _token(actor_role: str = 'pm') -> dict[str, str]:
    payload = {
        'actor_id': f'{actor_role}-001',
        'actor_role': actor_role,
        'project_scope': ['proj-001'],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {'Authorization': f'Bearer {encoded}'}


def _clear_all_caches() -> None:
    clear_project_import_candidate_cache()
    clear_project_seed_cache()
    clear_project_tracker_cache()
    clear_seed_cache()


def _write_candidate_estimator(path):
    workbook = Workbook()
    try:
        sheet = workbook.active
        sheet.title = 'Updated'
        sheet.append([])
        sheet.append([None, 'Updated'])
        sheet.append([None, None, 'NETA', None, 'Miner Temp Power', 'SLD: E01-00, E01-01'])
        sheet.append([None, None, 'ATS', None, 'Santa Teresa, NM', 'Dated: 03/05/2026'])
        sheet.append([None, None, 'QTY', 'Section', 'Apparatus Type', 'Designation', 'Notes', None, 'Hrs/Unit', 'Hrs/Line'])
        sheet.append([None, None, 2, 'Temp Power', 'Switch MV - Fused Disconnect', 'PD-1', 'E01-00', None, 2.5, 5])
        sheet.append([None, None, 1, 'Temp Power', 'Panelboard LV', 'SWBD-1', 'E01-01', None, 1.5, 1.5])
        workbook.save(path)
    finally:
        workbook.close()


def _candidate(tmp_path, monkeypatch):
    workbook_path = tmp_path / 'estimator.xlsm'
    _write_candidate_estimator(workbook_path)
    monkeypatch.setenv('APEX_PROJECT_ESTIMATOR_WORKBOOK', str(workbook_path))
    monkeypatch.setenv('APEX_PROJECT_SLD_PDF', str(tmp_path / 'missing.pdf'))
    _clear_all_caches()
    return load_project_import_candidate(str(workbook_path), str(tmp_path / 'missing.pdf'))


def _domain_counts() -> dict[str, int]:
    return {
        'projects': len(store.projects),
        'workpackages': len(store.workpackages),
        'tasks': len(store.tasks),
        'apparatus': len(store.apparatus),
    }


def _manual_task_plan_payload(candidate: dict) -> dict:
    tasks = [task for workpackage in candidate['workpackages'] for task in workpackage.get('tasks', [])]
    first_task = tasks[0]
    first_apparatus = first_task['apparatus_candidates'][0]
    remaining_apparatus = []
    for task in tasks:
        for apparatus in task.get('apparatus_candidates', []):
            if apparatus['candidate_id'] != first_apparatus['candidate_id']:
                remaining_apparatus.append((task, apparatus))

    manual_group_id = 'manual-task:split-lineup'
    source_group_id = f"source-task:{first_task['task_id']}"
    apparatus_rows = [
        {
            'candidate_id': first_apparatus['candidate_id'],
            'local_task_group_id': source_group_id,
            'display_name': first_apparatus['display_name'],
            'designation': first_task.get('designation') or '',
            'source_task_id': first_task['task_id'],
            'source_task_title': first_task['title'],
        }
    ]
    for index, (task, apparatus) in enumerate(remaining_apparatus, start=1):
        apparatus_rows.append(
            {
                'candidate_id': apparatus['candidate_id'],
                'local_task_group_id': manual_group_id,
                'display_name': f"{apparatus['display_name']} regrouped" if index == 1 else apparatus['display_name'],
                'designation': 'MANUAL-PM' if index == 1 else (task.get('designation') or ''),
                'source_task_id': task['task_id'],
                'source_task_title': task['title'],
            }
        )

    return {
        'candidate_id': candidate['candidate_id'],
        'candidate_version': candidate['candidate_version'],
        'source_stat_fingerprint': candidate['source_freshness']['aggregate_fingerprint'],
        'idempotency_key': 'pm-task-plan:pm-import-candidate-miner-temp-power:test',
        'review_notes': 'Persist manual PM task grouping for durable planning only.',
        'manual_task_shaping': {
            'storage': 'local_browser_only',
            'version': 'pm_import_candidate_task_shaping_v1',
            'summary': {
                'group_count': 2,
                'regrouped_apparatus_count': len(remaining_apparatus),
                'designation_override_count': 1,
            },
            'groups': [
                {
                    'group_id': source_group_id,
                    'title': first_task['title'],
                    'designation': first_task.get('designation') or '',
                    'seeded_from_source': True,
                    'source_task_id': first_task['task_id'],
                    'apparatus_count': 1,
                    'planned_hours': 2.5,
                    'apparatus_candidate_ids': [first_apparatus['candidate_id']],
                },
                {
                    'group_id': manual_group_id,
                    'title': 'Breaker lineup split',
                    'designation': 'MANUAL-PM',
                    'seeded_from_source': False,
                    'source_task_id': None,
                    'apparatus_count': len(remaining_apparatus),
                    'planned_hours': sum(float(task.get('planned_hours') or 0) / max(len(task.get('apparatus_candidates') or []), 1) for task, _ in remaining_apparatus),
                    'apparatus_candidate_ids': [apparatus['candidate_id'] for _, apparatus in remaining_apparatus],
                },
            ],
            'apparatus': apparatus_rows,
        },
    }


def _task_plan_request(candidate: dict, payload: dict, **overrides) -> dict:
    request = {
        'idempotency_key': payload['idempotency_key'],
        'mutation_class': 'C',
        'action_type': 'persist_project_import_task_plan',
        'entity_id': build_project_import_task_plan_id(candidate),
        'payload': payload,
        'reason': 'Persist manual PM task grouping as planning-only durable rows.',
        'source': 'online',
        'client_timestamp': '2026-05-18T22:15:00Z',
    }
    request.update(overrides)
    return request


def test_project_import_task_plan_route_persists_planning_rows_and_replays(client, monkeypatch, tmp_path):
    candidate = _candidate(tmp_path, monkeypatch)
    payload = _manual_task_plan_payload(candidate)
    before_counts = _domain_counts()

    first = client.post(
        '/api/v1/mutations/project-import-task-plans',
        json=_task_plan_request(candidate, payload),
        headers=_token(),
    )
    second = client.post(
        '/api/v1/mutations/project-import-task-plans',
        json=_task_plan_request(candidate, payload),
        headers=_token(),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.json()
    second_data = second.json()
    assert first_data['status'] == 'accepted'
    assert second_data['status'] == 'idempotent_hit'
    assert first_data['entity_type'] == 'pm_import_task_plan'
    assert first_data['action_type'] == 'persist_project_import_task_plan'
    assert first_data['new_state']['task_plan_authority'] == 'admitted_by_pm_lane_361_task_plan_persistence'
    assert first_data['new_state']['row_counts']['projects'] == 1
    assert first_data['new_state']['row_counts']['workpackages'] == 1
    assert first_data['new_state']['row_counts']['tasks'] == 2
    assert first_data['new_state']['row_counts']['apparatus'] == candidate['summary']['apparatus_candidate_count']

    after_counts = _domain_counts()
    assert after_counts['projects'] == before_counts['projects'] + 1
    assert after_counts['workpackages'] == before_counts['workpackages'] + 1
    assert after_counts['tasks'] == before_counts['tasks'] + 2
    assert after_counts['apparatus'] == before_counts['apparatus'] + candidate['summary']['apparatus_candidate_count']

    status = load_project_import_task_plan_status()
    assert status['classification'] == 'task_plan_persisted'
    assert status['current_candidate_match'] is True
    assert status['persisted_row_counts']['tasks'] == 2
    assert status['persisted_row_counts']['apparatus'] == candidate['summary']['apparatus_candidate_count']
    assert status['planning_context_only'] is True

    status_route = client.get('/api/v1/reads/project-import-task-plan-status', headers=_token())
    assert status_route.status_code == 200
    assert status_route.json()['classification'] == 'task_plan_persisted'


def test_project_import_task_plan_route_rejects_candidate_identity_mismatch(client, monkeypatch, tmp_path):
    candidate = _candidate(tmp_path, monkeypatch)
    payload = _manual_task_plan_payload(candidate)
    payload['candidate_version'] = 'stale-version'

    response = client.post(
        '/api/v1/mutations/project-import-task-plans',
        json=_task_plan_request(candidate, payload),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'rejected'
    assert data['error']['code'] == 'INVALID_PAYLOAD'


def test_project_import_task_plan_route_requires_pm_online_class_c(client, monkeypatch, tmp_path):
    candidate = _candidate(tmp_path, monkeypatch)
    payload = _manual_task_plan_payload(candidate)

    non_pm = client.post(
        '/api/v1/mutations/project-import-task-plans',
        json=_task_plan_request(candidate, payload, idempotency_key='pm-task-plan:pm-import-candidate-miner-temp-power:test-non-pm'),
        headers=_token('field_tech'),
    )
    offline = client.post(
        '/api/v1/mutations/project-import-task-plans',
        json=_task_plan_request(
            candidate,
            payload,
            idempotency_key='pm-task-plan:pm-import-candidate-miner-temp-power:test-offline',
            source='offline_queue',
        ),
        headers=_token(),
    )
    wrong_class = client.post(
        '/api/v1/mutations/project-import-task-plans',
        json=_task_plan_request(
            candidate,
            payload,
            idempotency_key='pm-task-plan:pm-import-candidate-miner-temp-power:test-wrong-class',
            mutation_class='B',
        ),
        headers=_token(),
    )

    assert non_pm.json()['status'] == 'rejected'
    assert non_pm.json()['error']['code'] == 'UNAUTHORIZED_ROLE'
    assert offline.json()['status'] == 'rejected'
    assert offline.json()['error']['code'] == 'OFFLINE_CLASS_C_REJECTED'
    assert wrong_class.json()['status'] == 'rejected'
    assert wrong_class.json()['error']['code'] == 'INVALID_MUTATION_CLASS'
