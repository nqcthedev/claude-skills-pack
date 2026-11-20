from flask import Blueprint, abort, jsonify, request

from ..db import get_db

bp = Blueprint("bookings", __name__, url_prefix="/bookings")

BOOKABLE = {"checkup": 45, "cleaning": 45, "filling": 60, "whitening": 90}


@bp.post("")
def create_booking():
    payload = request.get_json(silent=True) or {}
    service = payload.get("service")
    if service not in BOOKABLE:
        abort(400, description="service must be one of: " + ", ".join(sorted(BOOKABLE)))
    for field in ("patient_phone", "dentist_id", "starts_at"):
        if not payload.get(field):
            abort(400, description=f"{field} is required")
    db = get_db()
    cur = db.execute(
        "INSERT INTO appointments (patient_phone, dentist_id, service, starts_at, status) VALUES (?, ?, ?, ?, 'booked')",
        (payload["patient_phone"], payload["dentist_id"], service, payload["starts_at"]),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "status": "booked"}), 201


@bp.get("/<int:appointment_id>")
def get_booking(appointment_id: int):
    row = get_db().execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))
