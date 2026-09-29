"""End-to-end walk through the API: create a document, submit two agreeing
annotations, confirm a GoldenExample gets finalized; submit two disagreeing
annotations on a separate document, confirm it's routed to adjudication
instead. Uses an isolated in-memory SQLite DB per test run (see conftest.py)
so tests never touch the dev .db file or leak state between runs.
"""

from __future__ import annotations


def test_document_and_agreement_finalizes_golden(client):
    doc_resp = client.post("/documents", json={"text": "I'm not sure this fits our budget."})
    assert doc_resp.status_code == 200
    doc = doc_resp.json()

    tasks = client.get("/tasks").json()
    task = next(t for t in tasks if t["document_id"] == doc["id"])

    r1 = client.post(
        f"/tasks/{task['id']}/annotations",
        json={"annotator_id": "alice", "labels": ["OBJECTION"]},
    )
    assert r1.status_code == 200

    r2 = client.post(
        f"/tasks/{task['id']}/annotations",
        json={"annotator_id": "bob", "labels": ["OBJECTION"]},
    )
    assert r2.status_code == 200

    golden = client.get("/golden").json()
    matching = [g for g in golden if g["document_id"] == doc["id"]]
    assert len(matching) == 1
    assert matching[0]["labels"] == ["OBJECTION"]
    assert matching[0]["agreement_score"] == 1.0


def test_disagreement_routes_to_adjudication(client):
    doc = client.post("/documents", json={"text": "When can we start the trial?"}).json()
    task = next(t for t in client.get("/tasks").json() if t["document_id"] == doc["id"])

    client.post(
        f"/tasks/{task['id']}/annotations",
        json={"annotator_id": "alice", "labels": ["QUESTION"]},
    )
    client.post(
        f"/tasks/{task['id']}/annotations",
        json={"annotator_id": "bob", "labels": ["BUYING_SIGNAL"]},
    )

    updated_task = next(t for t in client.get("/tasks").json() if t["id"] == task["id"])
    assert updated_task["status"] == "adjudication"

    golden = client.get("/golden").json()
    assert not any(g["document_id"] == doc["id"] for g in golden)


def test_unknown_label_rejected(client):
    doc = client.post("/documents", json={"text": "..."}).json()
    task = next(t for t in client.get("/tasks").json() if t["document_id"] == doc["id"])
    resp = client.post(
        f"/tasks/{task['id']}/annotations",
        json={"annotator_id": "alice", "labels": ["NOT_A_REAL_LABEL"]},
    )
    assert resp.status_code == 422


def test_health():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        assert c.get("/health").json() == {"status": "ok"}
