import json
from pathlib import Path
from typing import Any


BRANDING_FILE = Path("storage/branding.json")


def _default_branding() -> dict[str, Any]:
    return {
        "sponsors": [
            {"title": "Pharma Sponsor 1", "image": "assets/sponsors/sponsor_1.png", "url": "https://example.com/pharma-1"},
            {"title": "Medical Supplies Sponsor", "image": "assets/sponsors/sponsor_2.png", "url": "https://example.com/supplies"},
            {"title": "Lab Sponsor", "image": "assets/sponsors/sponsor_3.png", "url": "https://example.com/lab"},
            {"title": "Cardio Sponsor", "image": "assets/sponsors/sponsor_4.png", "url": "https://example.com/cardio"},
        ],
        "vip_sponsors": [
            {"title": "VIP Sponsor 1", "image": "assets/vip_sponsors/vip_1.png", "url": "https://example.com/vip-1"},
            {"title": "VIP Sponsor 2", "image": "assets/vip_sponsors/vip_2.png", "url": "https://example.com/vip-2"},
            {"title": "VIP Sponsor 3", "image": "assets/vip_sponsors/vip_3.png", "url": "https://example.com/vip-3"},
        ],
    }


def load_branding() -> dict[str, Any]:
    BRANDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not BRANDING_FILE.exists():
        data = _default_branding()
        BRANDING_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
    try:
        return json.loads(BRANDING_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = _default_branding()
        BRANDING_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data


def save_branding(data: dict[str, Any]) -> None:
    BRANDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    BRANDING_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
