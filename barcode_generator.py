import os
import sys
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter

# --- Path handling for .exe and normal script execution ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COUNTER_FILE = os.path.join(BASE_DIR, "counter.txt")
BARCODES_DIR = os.path.join(BASE_DIR, "generated_barcodes")
QRCODES_DIR = os.path.join(BASE_DIR, "generated_qrcodes")
# ---------------------------------------------------------------------------

CABINET_SECTIONS = {
    "KKT":  ["J00", "J01", "J02", "J03"],
    "KKTT": ["J00", "J01", "J02", "J03", "J04"],
    "KKKT": ["J00", "J01", "J02", "J03", "J04"],
}

MAX_SECTION_LEN = 3
MAX_BUILD_NUM_LEN = 4


# --- Counter helpers --------------------------------------------------------

def peek_next_build_number() -> int:
    """Loeb counter.txt failist järgmise numbri, ilma seda suurendamata."""
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
        except Exception:
            pass
    return 1


def commit_build_number(number: int) -> None:
    """Kirjutab järgmise vaba numbri counter.txt faili (atomaarselt)."""
    tmp_path = COUNTER_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(str(number))
        os.replace(tmp_path, COUNTER_FILE)
    except Exception as err:
        print(f"Hoiatus: counter.txt uuendamine ebaõnnestus: {err}")


# --- Validation helpers -----------------------------------------------------

def validate_tester_name(text: str) -> str:
    """Testija nimi: ei tohi olla tühi, ainult A-Z, 0-9, - ja _, kuni 32 märki."""
    cleaned = str(text).strip().upper()
    if not cleaned:
        raise ValueError("Väli 'Testija' ei tohi olla tühi.")
    if len(cleaned) > 32:
        raise ValueError("Testija nimi ei tohi ületada 32 märki.")
    for char in cleaned:
        if not (char.isascii() and (char.isalnum() or char in "-_")):
            raise ValueError(
                f"Väljal 'Testija' on lubamatu märk: '{char}'. "
                "Kasutage ainult inglise tähti, numbreid, sidekriipsu või alakriipsu."
            )
    return cleaned


def validate_cabinet_type(cabinet: str) -> str:
    """Kapi tüüp peab olema üks CABINET_SECTIONS võtmetest."""
    cleaned = str(cabinet).strip().upper()
    if cleaned not in CABINET_SECTIONS:
        allowed = ", ".join(CABINET_SECTIONS.keys())
        raise ValueError(f"Tundmatu kapi tüüp: '{cabinet}'. Lubatud: {allowed}.")
    return cleaned


def validate_section_code(section: str) -> str:
    """Sektsiooni kood: kuni 3 märki, ainult A-Z ja 0-9."""
    cleaned = str(section).strip().upper()
    if not cleaned:
        raise ValueError("Sektsiooni kood ei tohi olla tühi.")
    if len(cleaned) > MAX_SECTION_LEN:
        raise ValueError(f"Sektsiooni kood ei tohi ületada {MAX_SECTION_LEN} märki.")
    for char in cleaned:
        if not (char.isascii() and char.isalnum()):
            raise ValueError(f"Lubamatu märk sektsiooni koodis: '{char}'.")
    return cleaned


def format_barcode_payload(build_num: str, cabinet: str, section: str) -> str:
    """Ühendab komponendid üheks triipkoodi payload-stringiks."""
    build_str = str(build_num).strip().zfill(MAX_BUILD_NUM_LEN)
    if not build_str.isdigit() or len(build_str) != MAX_BUILD_NUM_LEN:
        raise ValueError(f"Komplekti number peab koosnema {MAX_BUILD_NUM_LEN} numbrist.")

    cabinet_clean = validate_cabinet_type(cabinet)
    section_clean = validate_section_code(section)

    return f"{build_str}{cabinet_clean}{section_clean}"


# --- Image generators -------------------------------------------------------

def generate_barcode_image(payload: str, output_base_path: str) -> str:
    """Genereerib 1D Code128 triipkoodi PNG kujul. Tagastab tegeliku faili tee."""
    writer_options = {
        'module_width': 0.3,
        'module_height': 15.0,
        'quiet_zone': 3.0,
        'font_size': 10,
        'text_distance': 4.0,
    }
    barcode_obj = Code128(payload, writer=ImageWriter())
    saved_path = barcode_obj.save(output_base_path, options=writer_options)

    if not saved_path.lower().endswith(".png"):
        saved_path += ".png"
    return saved_path


def generate_qr_code_image(
    project_name: str,
    tester_name: str,
    build_num: str,
    cabinet: str,
    section: str,
    payload: str,
    output_path: str
) -> str:
    """Genereerib 2D QR-koodi kõigi detailidega (eesti keeles)."""
    qr_content = (
        f"Projekt: {project_name}\n"
        f"Testija: {tester_name}\n"
        f"Komplekt: {build_num}\n"
        f"Kapp: {cabinet}\n"
        f"Sektsioon: {section}\n"
        f"Kood: {payload}"
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=8,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    return output_path


# --- Core entry point -------------------------------------------------------

def process_barcode_request(
    project_name: str,
    tester_name: str,
    cabinet_type: str,
    build_num: str = None
) -> dict:
    """
    Genereerib terve komplekti silte ühe komplekti jaoks:
      - üks kapi tüüp -> N sektsiooni -> N triipkoodi + N QR-koodi
      - failid asuvad komplektipõhistes alamkaustades

    Loendur uuendatakse AINULT siis, kui kõik sildid on edukalt loodud.
    """
    project_clean = str(project_name).strip()
    if not project_clean:
        raise ValueError("Projekti nimi on kohustuslik väli.")

    tester_clean = validate_tester_name(tester_name)
    cabinet_clean = validate_cabinet_type(cabinet_type)
    sections = CABINET_SECTIONS[cabinet_clean]

    if build_num is None or str(build_num).strip() == "":
        current_num = peek_next_build_number()
        build_num_clean = str(current_num).zfill(MAX_BUILD_NUM_LEN)
        next_num_to_save = current_num + 1
    else:
        build_num_clean = str(build_num).strip().zfill(MAX_BUILD_NUM_LEN)
        if not build_num_clean.isdigit() or len(build_num_clean) != MAX_BUILD_NUM_LEN:
            raise ValueError(f"Komplekti number peab koosnema {MAX_BUILD_NUM_LEN} numbrist.")
        next_num_to_save = None

    build_folder_name = f"{build_num_clean}_{cabinet_clean}"
    barcode_dir = os.path.join(BARCODES_DIR, build_folder_name)
    qr_dir = os.path.join(QRCODES_DIR, build_folder_name)
    os.makedirs(barcode_dir, exist_ok=True)
    os.makedirs(qr_dir, exist_ok=True)

    labels = []
    for section in sections:
        payload = format_barcode_payload(build_num_clean, cabinet_clean, section)

        barcode_base = os.path.join(barcode_dir, f"barcode_{payload}")
        qr_full_path = os.path.join(qr_dir, f"qrcode_{payload}.png")

        barcode_path = generate_barcode_image(payload, barcode_base)
        qr_path = generate_qr_code_image(
            project_clean, tester_clean, build_num_clean,
            cabinet_clean, section, payload, qr_full_path
        )

        labels.append({
            "section": section,
            "payload": payload,
            "barcode_path": barcode_path,
            "qr_path": qr_path,
            "barcode_filename": os.path.basename(barcode_path),
            "qr_filename": os.path.basename(qr_path),
        })

    if next_num_to_save is not None:
        commit_build_number(next_num_to_save)

    return {
        "project": project_clean,
        "tester": tester_clean,
        "build_num": build_num_clean,
        "cabinet": cabinet_clean,
        "build_folder": build_folder_name,
        "labels": labels,
    }