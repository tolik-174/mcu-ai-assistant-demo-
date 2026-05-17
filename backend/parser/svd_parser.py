from pathlib import Path
import json
from cmsis_svd.parser import SVDParser

BASE_DIR = Path(__file__).resolve().parent.parent
SVD_DIR = BASE_DIR / "data" / "svd"
OUT_DIR = BASE_DIR / "data" / "parsed"

def parse_svd_file(svd_path: Path) -> dict:
    parser = SVDParser.for_xml_file(str(svd_path))
    device = parser.get_device()

    result = {
        "device": device.name,
        "description": getattr(device, "description", ""),
        "peripherals": []
    }

    for peripheral in device.peripherals:
        p = {
            "name": peripheral.name,
            "description": getattr(peripheral, "description", ""),
            "base_address": hex(peripheral.base_address) if peripheral.base_address is not None else None,
            "registers": []
        }

        registers = getattr(peripheral, "registers", []) or []
        for reg in registers:
            r = {
                "name": reg.name,
                "description": getattr(reg, "description", ""),
                "address_offset": hex(reg.address_offset) if reg.address_offset is not None else None,
                "size": getattr(reg, "size", None),
                "access": str(getattr(reg, "access", "")) if getattr(reg, "access", None) else None,
                "reset_value": hex(reg.reset_value) if getattr(reg, "reset_value", None) is not None else None,
                "fields": []
            }

            fields = getattr(reg, "fields", []) or []
            for field in fields:
                r["fields"].append({
                    "name": field.name,
                    "description": getattr(field, "description", ""),
                    "bit_offset": getattr(field, "bit_offset", None),
                    "bit_width": getattr(field, "bit_width", None),
                    "access": str(getattr(field, "access", "")) if getattr(field, "access", None) else None
                })

            p["registers"].append(r)

        result["peripherals"].append(p)

    return result


def build_svd_json():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for svd_file in SVD_DIR.glob("*.svd"):
        parsed = parse_svd_file(svd_file)
        out_file = OUT_DIR / f"{svd_file.stem}_svd.json"
        out_file.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[DONE] Parsed {svd_file.name} -> {out_file.name}")


if __name__ == "__main__":
    build_svd_json()