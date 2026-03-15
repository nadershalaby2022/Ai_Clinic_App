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


def build_prescription_html(
    profile: dict[str, Any],
    visit_info: dict[str, Any],
    patient_info: dict[str, Any],
    drugs: list[dict[str, Any]],
    lang: str = "en",
) -> str:
    rtl = lang == "ar"
    direction = "rtl" if rtl else "ltr"
    now = datetime.now().strftime("%Y-%m-%d  %H:%M")

    def _t(en: str, ar: str) -> str:
        return ar if rtl else en

    def _safe(x: Any) -> str:
        return "" if x is None else str(x)

    drug_rows = ""
    for idx, row in enumerate(drugs, start=1):
        drug = _safe(row.get("Drug_Name", ""))
        dose = f"{_safe(row.get('Dose_Value', ''))} {_safe(row.get('Dose_Unit', ''))}".strip()
        freq = f"{_safe(row.get('Freq_Value', ''))} {_safe(row.get('Freq_Unit', ''))}".strip()
        dur = f"{_safe(row.get('Duration_Days', ''))}".strip()
        route = _safe(row.get("Route", ""))
        instructions = _safe(row.get("Instructions", ""))

        drug_rows += f"""
<tr>
  <td>{idx}</td>
  <td>{drug}</td>
  <td>{dose}</td>
  <td>{freq}</td>
  <td>{dur}</td>
  <td>{route}</td>
  <td>{instructions}</td>
</tr>
"""

    diagnosis = _safe(visit_info.get("diagnosis", ""))
    doctor_pill = _safe(profile.get("doctor_name", ""))
    diag_pill = diagnosis

    html = f"""
<!doctype html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_t("Prescription Report", "تقرير الروشتة")}</title>
<style>
  body {{
    font-family: "Tahoma","Arial",sans-serif;
    direction: {direction};
    margin: 24px;
    color: #111827;
  }}
  .card {{
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 18px;
    background: #ffffff;
  }}
  .header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px dashed #e5e7eb;
    padding-bottom: 12px;
    margin-bottom: 14px;
  }}
  .title {{
    font-size: 20px;
    font-weight: 900;
    margin: 0;
  }}
  .sub {{
    font-size: 12.5px;
    color: #374151;
    margin-top: 6px;
    line-height: 1.8;
  }}
  .pill {{
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: #f3f4f6;
    font-size: 12.5px;
    font-weight: 800;
    margin-left: 8px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    margin: 12px 0 16px;
  }}
  .box {{
    background: #f9fafb;
    border: 1px solid #eef2f7;
    border-radius: 12px;
    padding: 10px 12px;
  }}
  .box .k {{
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 6px;
  }}
  .box .v {{
    font-size: 16px;
    font-weight: 900;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    font-size: 13px;
  }}
  thead th {{
    background: #111827;
    color: #fff;
    padding: 10px;
    text-align: center;
    font-weight: 900;
  }}
  tbody td {{
    border-bottom: 1px solid #e5e7eb;
    padding: 10px;
    text-align: center;
  }}
  .section-title {{
    margin-top: 16px;
    font-size: 14.5px;
    font-weight: 900;
  }}
  .footer-note {{
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px dashed #e5e7eb;
    font-size: 12.5px;
    color: #374151;
    line-height: 1.8;
  }}
  @media print {{
    body {{ margin: 0; }}
    .no-print {{ display: none !important; }}
  }}
  .print-btn {{
    background: #111827;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 900;
    cursor: pointer;
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div>
        <p class="title">{_t("Prescription Report", "تقرير الروشتة")}</p>
        <div class="sub">
          {f'<span class="pill">{doctor_pill}</span>' if doctor_pill else ''}
          {f'<span class="pill">{diag_pill}</span>' if diag_pill else ''}
          <span>{_t("Report Date", "تاريخ التقرير")}: <b>{now}</b></span>
        </div>
      </div>
      <div style="text-align:{'left' if rtl else 'right'}">
        <div style="font-weight:900">{_safe(profile.get('clinic_name', ''))}</div>
        <div class="sub">
          <div><b>{_safe(profile.get('doctor_name', ''))}</b></div>
          <div>{_safe(profile.get('doctor_title_1', ''))}</div>
          <div>{_safe(profile.get('doctor_title_2', ''))}</div>
          <div>{_safe(profile.get('clinic_address', ''))}</div>
          <div>{_safe(profile.get('clinic_phones', ''))}</div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="box">
        <div class="k">{_t("Patient ID", "رقم المريض")}</div>
        <div class="v">{_safe(patient_info.get("patient_id", ""))}</div>
      </div>
      <div class="box">
        <div class="k">{_t("Patient Name", "اسم المريض")}</div>
        <div class="v">{_safe(patient_info.get("patient_name", ""))}</div>
      </div>
      <div class="box">
        <div class="k">{_t("Visit ID", "رقم الزيارة")}</div>
        <div class="v">{_safe(visit_info.get("visit_id", ""))}</div>
      </div>
      <div class="box">
        <div class="k">{_t("Visit Date", "تاريخ الزيارة")}</div>
        <div class="v">{_safe(visit_info.get("visit_date", ""))}</div>
      </div>
    </div>

    <div class="section-title">{_t("Medications", "الأدوية")}</div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>{_t("Drug", "الدواء")}</th>
          <th>{_t("Dose", "الجرعة")}</th>
          <th>{_t("Frequency", "التكرار")}</th>
          <th>{_t("Days", "الأيام")}</th>
          <th>{_t("Route", "الطريقة")}</th>
          <th>{_t("Notes", "ملاحظات")}</th>
        </tr>
      </thead>
      <tbody>
        {drug_rows}
      </tbody>
    </table>

    <div class="footer-note">
      {_safe(profile.get("footer_note", ""))}
    </div>

    <div class="no-print" style="margin-top:12px; text-align:left;">
      <button class="print-btn" onclick="window.print()">{_t("Print", "طباعة")}</button>
    </div>
  </div>
</body>
</html>
"""
    return html
