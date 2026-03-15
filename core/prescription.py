from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROFILE_FILE = Path("storage/prescription_profile.json")


def default_profile() -> dict[str, Any]:
    return {
        "clinic_name": "Clinic Name",
        "doctor_name": "Dr. ________",
        "doctor_title_1": "Consultant ________",
        "doctor_title_2": "Fellow of ________",
        "clinic_address": "Clinic Address",
        "clinic_phones": "Phone 1 | Phone 2",
        "footer_note": "Thank you. Follow-up as advised.",
    }


def load_profile() -> dict[str, Any]:
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not PROFILE_FILE.exists():
        data = default_profile()
        PROFILE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
    try:
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = default_profile()
        PROFILE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data


def save_profile(data: dict[str, Any]) -> None:
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def generate_prescription_pdf(
    profile: dict[str, Any],
    visit_info: dict[str, Any],
    patient_info: dict[str, Any],
    drugs: list[dict[str, Any]],
) -> Path:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("reportlab is required for PDF export.") from exc

    out_dir = Path("storage/prescriptions")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = out_dir / f"prescription_{stamp}.pdf"

    c = canvas.Canvas(str(file_path), pagesize=A4)
    width, height = A4
    y = height - 50

    def line(text: str, step: int = 16, size: int = 11) -> None:
        nonlocal y
        c.setFont("Helvetica", size)
        c.drawString(40, y, text[:120])
        y -= step

    # Header
    line(profile.get("clinic_name", ""), step=20, size=16)
    line(profile.get("doctor_name", ""), step=16, size=12)
    if profile.get("doctor_title_1"):
        line(profile.get("doctor_title_1", ""), step=14, size=10)
    if profile.get("doctor_title_2"):
        line(profile.get("doctor_title_2", ""), step=14, size=10)
    line(profile.get("clinic_address", ""), step=14, size=10)
    line(profile.get("clinic_phones", ""), step=18, size=10)

    line("-" * 90, step=12, size=9)

    # Patient / visit
    line(f"Patient ID: {patient_info.get('patient_id', '')}")
    if patient_info.get("patient_name"):
        line(f"Patient Name: {patient_info.get('patient_name')}")
    line(f"Visit ID: {visit_info.get('visit_id', '')}")
    line(f"Visit Date: {visit_info.get('visit_date', '')}")
    line(f"Diagnosis: {visit_info.get('diagnosis', '')}")

    line("-" * 90, step=12, size=9)
    line("Prescription:")

    for idx, row in enumerate(drugs, start=1):
        if y < 80:
            c.showPage()
            y = height - 50
        drug = row.get("Drug_Name", "")
        dose = f"{row.get('Dose_Value', '')} {row.get('Dose_Unit', '')}".strip()
        freq = f"{row.get('Freq_Value', '')} {row.get('Freq_Unit', '')}".strip()
        dur = f"{row.get('Duration_Days', '')} days".strip()
        route = row.get("Route", "")
        instructions = row.get("Instructions", "")
        line(f"{idx}. {drug}")
        line(f"   Dose: {dose} | Freq: {freq} | Duration: {dur} | Route: {route}", step=14, size=10)
        if instructions:
            line(f"   Notes: {instructions}", step=14, size=10)

    if profile.get("footer_note"):
        if y < 80:
            c.showPage()
            y = height - 50
        line("-" * 90, step=12, size=9)
        line(profile.get("footer_note", ""), step=16, size=10)

    c.showPage()
    c.save()
    return file_path
