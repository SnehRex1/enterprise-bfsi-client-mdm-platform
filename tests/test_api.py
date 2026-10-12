
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from apps.api import main


client = TestClient(main.app)


def _mock_decision_engine(
    existing_decision=None,
    update_rowcount=1,
):
    """Mock SQL operations used by the decision endpoint."""
    connection = MagicMock()

    existing_result = MagicMock()
    existing_result.scalar.return_value = existing_decision

    update_result = MagicMock()
    update_result.rowcount = update_rowcount

    connection.execute.side_effect = [
        existing_result,
        update_result,
        MagicMock(),
    ]

    engine = MagicMock()
    engine.begin.return_value.__enter__.return_value = connection

    return engine, connection


def _mapping_result(row):
    """Mock the result of a SQL query using .mappings().first()."""
    result = MagicMock()
    result.mappings.return_value.first.return_value = row
    return result


@pytest.mark.parametrize(
    "params",
    [
        {"q": "", "limit": 20},
        {"q": "MC000550", "limit": 0},
        {"q": "MC000550", "limit": 51},
    ],
)
def test_client_search_rejects_invalid_parameters(params):
    response = client.get("/clients/search", params=params)

    assert response.status_code == 422


def test_decision_requires_non_empty_fields():
    response = client.post(
        "/matches/CASE-TEST/approve",
        json={
            "steward_id": "",
            "decision_reason": "",
        },
    )

    assert response.status_code == 422


def test_approval_updates_status_and_writes_audit(monkeypatch):
    engine, connection = _mock_decision_engine()
    monkeypatch.setattr(main, "engine", engine)

    response = client.post(
        "/matches/CASE-TEST/approve",
        json={
            "steward_id": "test_steward",
            "decision_reason": "Mocked regression test",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "case_id": "CASE-TEST",
        "decision": "APPROVE_MATCH",
        "status": "persisted",
    }

    statements = [
        str(call.args[0])
        for call in connection.execute.call_args_list
    ]

    assert any(
        "status = 'RESOLVED'" in sql
        for sql in statements
    )
    assert any(
        "INSERT INTO mdm.stewardship_decision" in sql
        for sql in statements
    )


def test_duplicate_decision_returns_conflict(monkeypatch):
    engine, connection = _mock_decision_engine(
        existing_decision="APPROVE_MATCH"
    )
    monkeypatch.setattr(main, "engine", engine)

    response = client.post(
        "/matches/CASE-TEST/reject",
        json={
            "steward_id": "test_steward",
            "decision_reason": "Duplicate-decision regression test",
        },
    )

    assert response.status_code == 409
    assert "already resolved" in response.json()["detail"]
    assert connection.execute.call_count == 1


def test_missing_stewardship_case_returns_not_found(monkeypatch):
    engine, connection = _mock_decision_engine(update_rowcount=0)
    monkeypatch.setattr(main, "engine", engine)

    response = client.post(
        "/matches/CASE-MISSING/approve",
        json={
            "steward_id": "test_steward",
            "decision_reason": "Missing-case regression test",
        },
    )

    assert response.status_code == 404


def test_match_get_returns_current_resolved_status(monkeypatch):
    review = {
        "case_id": "CASE-TEST",
        "record_key_a": "RECORD-A",
        "record_key_b": "RECORD-B",
        "match_score": 0.95,
        "matching_rule": "TEST_RULE",
        "match_reason": "Mocked test evidence",
    }
    stewardship_case = {
        "case_id": "CASE-TEST",
        "status": "RESOLVED",
        "decision": "APPROVE_MATCH",
    }

    connection = MagicMock()
    connection.execute.side_effect = [
        _mapping_result(review),
        _mapping_result(stewardship_case),
        _mapping_result(None),
        _mapping_result(None),
    ]

    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    monkeypatch.setattr(main, "engine", engine)

    response = client.get("/matches/CASE-TEST")

    assert response.status_code == 200

    body = response.json()
    assert {
        "review",
        "stewardship_case",
        "record_a",
        "record_b",
    }.issubset(body.keys())
    assert body["stewardship_case"]["status"] == "RESOLVED"
