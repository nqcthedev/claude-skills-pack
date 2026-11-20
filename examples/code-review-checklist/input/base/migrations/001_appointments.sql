CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_phone TEXT NOT NULL,
    dentist_id INTEGER NOT NULL,
    service TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'booked'
);
CREATE INDEX idx_appointments_starts_at ON appointments (starts_at);
