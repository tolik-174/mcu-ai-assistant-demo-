from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter(prefix="/svd", tags=["svd"])

BASE_DIR = Path(__file__).resolve().parent.parent
PARSED_DIR = BASE_DIR / "data" / "parsed"

def load_svd_data():
    svd_files = list(PARSED_DIR.glob("*_svd.json"))
    if not svd_files:
        raise HTTPException(status_code=404, detail="No parsed SVD data found")

    # беремо перший файл; пізніше можна додати вибір device
    with open(svd_files[0], "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/device")
def get_device():
    data = load_svd_data()
    return {
        "device": data.get("device"),
        "description": data.get("description", "")
    }

@router.get("/peripherals")
def get_peripherals():
    data = load_svd_data()
    peripherals = [
        {
            "name": p["name"],
            "description": p.get("description", ""),
            "base_address": p.get("base_address")
        }
        for p in data.get("peripherals", [])
    ]
    return {"status": "ok", "peripherals": peripherals}

@router.get("/registers")
def get_registers(peripheral: str):
    data = load_svd_data()
    for p in data.get("peripherals", []):
        if p["name"].lower() == peripheral.lower():
            return {
                "status": "ok",
                "peripheral": p["name"],
                "registers": [
                    {
                        "name": r["name"],
                        "description": r.get("description", ""),
                        "address_offset": r.get("address_offset"),
                        "reset_value": r.get("reset_value"),
                        "access": r.get("access")
                    }
                    for r in p.get("registers", [])
                ]
            }

    raise HTTPException(status_code=404, detail=f"Peripheral '{peripheral}' not found")

@router.get("/register")
def get_register(peripheral: str, register: str):
    data = load_svd_data()
    for p in data.get("peripherals", []):
        if p["name"].lower() == peripheral.lower():
            for r in p.get("registers", []):
                if r["name"].lower() == register.lower():
                    return {
                        "status": "ok",
                        "peripheral": p["name"],
                        "register": r
                    }

    raise HTTPException(status_code=404, detail=f"Register '{register}' not found in '{peripheral}'")