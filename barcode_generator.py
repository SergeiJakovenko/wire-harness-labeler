import os
import sys
from datetime import datetime
import qrcode
from database import get_next_build_number, add_harness_batch

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

QRCODES_DIR = os.path.join(BASE_DIR, "generated_qrcodes")

def process_batch_request(tester_name: str, cabinet_type: str) -> dict:
    tester_clean = str(tester_name).strip()
    if not tester_clean:
        raise ValueError("Имя тестировщика (Testija) обязательно для заполнения.")

    if cabinet_type not in ["KKT", "KKKT", "KKTT"]:
        raise ValueError("Некорректный тип шкафа.")

    project_name = "Keskpinge seadmete juhtmetester"

    # Определяем ячейки в зависимости от типа шкафа
    if cabinet_type == "KKT":
        cells = ["J00", "J01", "J02", "J03"]
    else:  # KKKT, KKTT
        cells = ["J00", "J01", "J02", "J03", "J04"]

    build_num, db_records = add_harness_batch(
        project_name=project_name,
        tester_name=tester_clean,
        section_code="GENERAL",
        cabinet_type=cabinet_type,
        cells=cells
    )

    os.makedirs(QRCODES_DIR, exist_ok=True)
    results = []

    for rec in db_records:
        payload = rec["payload"]
        cell = rec["cell"]
        qr_filename = f"qrcode_{payload}.png"
        qr_full_path = os.path.join(QRCODES_DIR, qr_filename)

        qr_content = (
            f"Project: {project_name}\n"
            f"Tester: {tester_clean}\n"
            f"Build No: {build_num}\n"
            f"Cabinet Type: {cabinet_type}\n"
            f"Cell: {cell}\n"
            f"Payload: {payload}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=3,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_full_path)

        results.append({
            "cell": cell,
            "payload": payload,
            "qr_url": f"/generated_qrcodes/{qr_filename}"
        })

    return {
        "build_num": build_num,
        "cabinet_type": cabinet_type,
        "qr_items": results
    }