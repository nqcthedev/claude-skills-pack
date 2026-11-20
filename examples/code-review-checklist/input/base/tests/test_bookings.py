import sqlite3
from pathlib import Path

import pytest

from app import create_app

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    conn = sqlite3.connect(db_path)
    for sql in sorted(MIGRATIONS.glob("*.sql")):
        conn.executescript(sql.read_text())
    conn.close()
    app = create_app({"DATABASE": str(db_path), "TESTING": True})
    return app.test_client()


def test_create_booking(client):
    res = client.post("/bookings", json={"service": "cleaning", "patient_phone": "0900000001", "dentist_id": 3, "starts_at": "2027-01-05T09:00"})
    assert res.status_code == 201
    assert client.get(f"/bookings/{res.json['id']}").json["status"] == "booked"


def test_rejects_unbookable_service(client):
    res = client.post("/bookings", json={"service": "implant", "patient_phone": "0900000001", "dentist_id": 3, "starts_at": "2027-01-05T09:00"})
    assert res.status_code == 400
