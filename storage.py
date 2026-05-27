# storage.py
import json
import os
from database import get_connection, init_db

init_db()

# ── Lookup maps ───────────────────────────────────────────────────────────────
GENDER_MAP = {
    "Male": 1, "Female": 2, "Other": 3, "Prefer not to say": 0
}
STATUS_MAP = {
    "Booked": 1, "Pending": 2, "Cancelled": 3, "Completed": 4
}
PRIORITY_MAP = {
    "Routine": 1, "Urgent": 2, "Emergency": 3
}
DEPARTMENT_MAP = {
    "Cardiology": 1, "Neurology": 2, "Orthopedics": 3,
    "Pediatrics": 4, "General Practice": 5, "Dermatology": 6,
    "Oncology": 7, "Radiology": 8, "— Select Department —": None
}
APPT_TYPE_MAP = {
    "Consultation": 1, "Follow-up": 2, "Emergency": 3,
    "Routine Check": 4, "— Select —": None
}
DURATION_MAP = {
    "15 min": 15, "30 min": 30, "45 min": 45, "60 min": 60,
    "— Select —": None
}


# ── ID generators ─────────────────────────────────────────────────────────────

def _generate_patient_id(dob: str, gender: str) -> int:
    """
    Format: DDMMYYYY + gender_code + ascending 3-digit suffix
    Gender code: 1 = Male, 2 = Female, 0 = Other/Unknown
    Example: 15/04/1990, Female, 3rd patient → 150419902003
    """
    # Parse DD/MM/YYYY
    try:
        d, m, y = dob.split("/")
        date_part = f"{d}{m}{y}"          # e.g. "15041990"
    except Exception:
        date_part = "00000000"

    gender_code = 1 if gender == "Male" else (2 if gender == "Female" else 0)

    # Find the next ascending suffix by checking existing IDs with same prefix
    prefix = int(f"{date_part}{gender_code}")  # e.g. 150419901

    conn   = get_connection()
    cursor = conn.cursor()

    # Get all Patient_ids that start with this prefix
    cursor.execute("SELECT Patient_id FROM Patient")
    existing = [row["Patient_id"] for row in cursor.fetchall()]
    conn.close()

    # Filter IDs that share the same date+gender prefix
    prefix_str = f"{date_part}{gender_code}"
    matching = [
        str(pid) for pid in existing
        if str(pid).startswith(prefix_str)
    ]

    # Next suffix = count of matches + 1, zero-padded to 3 digits
    suffix = len(matching) + 1
    suffix_str = str(suffix).zfill(3)           # e.g. "001", "002"

    patient_id = int(f"{date_part}{gender_code}{suffix_str}")
    return patient_id


def _generate_appointment_id() -> int:
    """
    8-digit ID starting from 10000000, incrementing by 1.
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(Appointment_id) as max_id FROM Appointment")
    row = cursor.fetchone()
    conn.close()

    last = row["max_id"]
    if last is None or last < 10000000:
        return 10000000
    return last + 1


# ── Public functions ──────────────────────────────────────────────────────────

def save_patient(data: dict) -> int:
    patient_id = _generate_patient_id(
        data.get("dob", ""),
        data.get("gender", "")
    )

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Patient (
            Patient_id,
            First_Name, Last_Name, Date_Of_Birth, Gender, Blood_Type,
            Phone, Email, Address, City, Postcode,
            Doctor, Insurance, Allergies, Notes,
            Em_name, Em_relation, Em_phone
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        data.get("first_name", ""),
        data.get("last_name", ""),
        _convert_date(data.get("dob", "")),
        GENDER_MAP.get(data.get("gender", ""), 0),
        data.get("blood_type", ""),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("address", ""),
        data.get("city", ""),
        data.get("postcode", ""),
        data.get("doctor", ""),
        data.get("insurance", ""),
        data.get("allergies", ""),
        data.get("notes", ""),
        data.get("em_name", ""),
        data.get("em_relation", ""),
        data.get("em_phone", ""),
    ))

    conn.commit()
    conn.close()

    _save_fhir_patient(patient_id, data)
    print(f"[storage] Patient saved — ID: {patient_id}")
    return patient_id


def save_appointment(data: dict) -> int:
    appt_id = _generate_appointment_id()

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Appointment (
            Appointment_id,
            Patient_id, Status, Priority, Doctor,
            Department, Appointment_type, Duration,
            Date, Time, Time_end, Reason, Notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        appt_id,
        data.get("patient_id", ""),
        STATUS_MAP.get(data.get("status", ""), 1),
        PRIORITY_MAP.get(data.get("priority", ""), 1),
        data.get("doctor", ""),
        DEPARTMENT_MAP.get(data.get("department", ""), None),
        APPT_TYPE_MAP.get(data.get("appt_type", ""), None),
        DURATION_MAP.get(data.get("duration", ""), None),
        _convert_date(data.get("date", "")),
        data.get("time", ""),
        data.get("time_end", ""),
        data.get("reason", ""),
        data.get("notes", ""),
    ))

    conn.commit()
    conn.close()

    _save_fhir_appointment(appt_id, data)
    print(f"[storage] Appointment saved — ID: {appt_id}")
    return appt_id


# ── Internal helpers ──────────────────────────────────────────────────────────

def _convert_date(dob: str) -> str:
    """DD/MM/YYYY → YYYY-MM-DD. Returns empty string on failure."""
    try:
        d, m, y = dob.split("/")
        return f"{y}-{m}-{d}"
    except Exception:
        return ""


def _save_fhir_patient(patient_id: int, data: dict):
    folder = os.path.join("data", "patients")
    os.makedirs(folder, exist_ok=True)
    resource = {
        "resourceType": "Patient",
        "id": str(patient_id),
        "name": [{"use": "official",
                  "text": f"{data['first_name']} {data['last_name']}"}],
        "gender":    data.get("gender", "").lower(),
        "birthDate": _convert_date(data.get("dob", "")),
        "telecom": [
            {"system": "phone", "value": data.get("phone", "")},
            {"system": "email", "value": data.get("email", "")},
        ],
        "address": [{"text":       data.get("address", ""),
                     "city":       data.get("city", ""),
                     "postalCode": data.get("postcode", "")}],
        "contact": [{
            "relationship": [{"text": data.get("em_relation", "")}],
            "name":    {"text": data.get("em_name", "")},
            "telecom": [{"system": "phone",
                         "value": data.get("em_phone", "")}],
        }],
    }
    path = os.path.join(folder, f"patient_{patient_id}.json")
    with open(path, "w") as f:
        json.dump(resource, f, indent=2)


def _save_fhir_appointment(appt_id: int, data: dict):
    folder = os.path.join("data", "appointments")
    os.makedirs(folder, exist_ok=True)
    resource = {
        "resourceType": "Appointment",
        "id": str(appt_id),
        "status":      data.get("status", "booked").lower(),
        "description": data.get("reason", ""),
        "start": f"{_convert_date(data.get('date', ''))}T{data.get('time', '')}:00",
        "end":   f"{_convert_date(data.get('date', ''))}T{data.get('time_end', '')}:00",
        "participant": [
            {"actor": {"reference": f"Patient/{data.get('patient_id', '')}"},
             "status": "accepted"},
            {"actor": {"display": data.get("doctor", "")},
             "status": "accepted"},
        ],
        "comment": data.get("notes", ""),
    }
    path = os.path.join(folder, f"appt_{appt_id}.json")
    with open(path, "w") as f:
        json.dump(resource, f, indent=2)