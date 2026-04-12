from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.incident import Incident
from app.models.playbook_execution import PlaybookExecution
from scripts import cleanup_db_payloads


def _seed_records(session):
    now = datetime.now(timezone.utc)

    old_incident = Incident(
        title='Old Closed Incident',
        description='old',
        source='option2_simulation',
        severity='high',
        status='closed',
        playbook_status='success',
        playbook_result={'report': {'ioc': '10.0.0.1'}},
        playbook_last_run_at=now - timedelta(days=45),
    )
    fresh_incident = Incident(
        title='Fresh Closed Incident',
        description='fresh',
        source='option2_simulation',
        severity='medium',
        status='closed',
        playbook_status='success',
        playbook_result={'report': {'ioc': '10.0.0.2'}},
        playbook_last_run_at=now - timedelta(days=3),
    )
    open_incident = Incident(
        title='Old Open Incident',
        description='open',
        source='option2_simulation',
        severity='low',
        status='open',
        playbook_status='running',
        playbook_result={'report': {'ioc': '10.0.0.3'}},
        playbook_last_run_at=now - timedelta(days=60),
    )

    session.add_all([old_incident, fresh_incident, open_incident])
    session.flush()

    old_execution = PlaybookExecution(
        incident_id=old_incident.id,
        task_id='task-old',
        playbook_name='default_triage',
        status='failed',
        result={'stack': 'sensitive'},
        finished_at=now - timedelta(days=40),
    )
    fresh_execution = PlaybookExecution(
        incident_id=fresh_incident.id,
        task_id='task-fresh',
        playbook_name='default_triage',
        status='success',
        result={'summary': 'keep for now'},
        finished_at=now - timedelta(days=2),
    )

    session.add_all([old_execution, fresh_execution])
    session.commit()

    return old_incident.id, fresh_incident.id, old_execution.id, fresh_execution.id


@pytest.fixture()
def isolated_db(monkeypatch, tmp_path: Path):
    db_file = tmp_path / 'cleanup_db_payloads.sqlite'
    engine = create_engine(f'sqlite:///{db_file}', connect_args={'check_same_thread': False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(cleanup_db_payloads, 'SessionLocal', SessionLocal)

    try:
        yield SessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_run_db_payload_cleanup_dry_run(isolated_db):
    session = isolated_db()
    old_incident_id, fresh_incident_id, old_execution_id, fresh_execution_id = _seed_records(session)
    session.close()

    payload = cleanup_db_payloads.run_db_payload_cleanup(retention_days=30, apply=False)

    assert payload['mode'] == 'dry-run'
    assert old_incident_id in payload['incident_candidates']
    assert fresh_incident_id not in payload['incident_candidates']
    assert old_execution_id in payload['execution_candidates']
    assert fresh_execution_id not in payload['execution_candidates']
    assert payload['incident_pruned_count'] == 0
    assert payload['execution_pruned_count'] == 0


def test_run_db_payload_cleanup_apply_prunes_old_payloads(isolated_db):
    session = isolated_db()
    old_incident_id, fresh_incident_id, old_execution_id, fresh_execution_id = _seed_records(session)
    session.close()

    payload = cleanup_db_payloads.run_db_payload_cleanup(retention_days=30, apply=True)

    assert payload['incident_pruned_count'] == 1
    assert payload['execution_pruned_count'] == 1
    assert old_incident_id in payload['incident_pruned_ids']
    assert old_execution_id in payload['execution_pruned_ids']

    verify = isolated_db()
    old_incident = verify.get(Incident, old_incident_id)
    fresh_incident = verify.get(Incident, fresh_incident_id)
    old_execution = verify.get(PlaybookExecution, old_execution_id)
    fresh_execution = verify.get(PlaybookExecution, fresh_execution_id)

    assert old_incident.playbook_result['retention_pruned'] is True
    assert fresh_incident.playbook_result == {'report': {'ioc': '10.0.0.2'}}
    assert old_execution.result['retention_pruned'] is True
    assert fresh_execution.result == {'summary': 'keep for now'}
    verify.close()


def test_main_writes_db_cleanup_audit_file(isolated_db, tmp_path: Path, capsys):
    session = isolated_db()
    _seed_records(session)
    session.close()

    audit_path = tmp_path / 'logs' / 'db_cleanup_audit.json'
    exit_code = cleanup_db_payloads.main(
        [
            '--retention-days',
            '30',
            '--dry-run',
            '--json-audit-log',
            str(audit_path),
        ]
    )

    captured = capsys.readouterr()
    stdout_payload = json.loads(captured.out.strip())
    audit_payload = json.loads(audit_path.read_text(encoding='utf-8'))

    assert exit_code == 0
    assert stdout_payload['mode'] == 'dry-run'
    assert audit_payload['mode'] == 'dry-run'
    assert audit_payload['incident_candidates']
