import os
import sys
import threading
import webbrowser

from flask import Flask, render_template, request, send_from_directory
from barcode_generator import (
    process_barcode_request,
    peek_next_build_number,
    CABINET_SECTIONS,
    BARCODES_DIR,
    QRCODES_DIR,
)

# --- Template path resolution (works both as .py and as .exe) --------------
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller .exe — templates bundled inside
    TEMPLATE_FOLDER = os.path.join(sys._MEIPASS, 'templates')
else:
    TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)

DEFAULT_PROJECT = "Keskpinge seadmete juhtmetester"
APP_HOST = "127.0.0.1"
APP_PORT = 5000
APP_URL = f"http://{APP_HOST}:{APP_PORT}"


# --- Static file serving ----------------------------------------------------

@app.route('/generated_barcodes/<build_folder>/<filename>')
def serve_barcode(build_folder, filename):
    directory = os.path.join(BARCODES_DIR, build_folder)
    return send_from_directory(directory, filename)


@app.route('/generated_qrcodes/<build_folder>/<filename>')
def serve_qrcode(build_folder, filename):
    directory = os.path.join(QRCODES_DIR, build_folder)
    return send_from_directory(directory, filename)


# --- Main route -------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    error_msg = None
    result = None

    next_build_num = str(peek_next_build_number()).zfill(4)

    if request.method == 'POST':
        tester_name = request.form.get('tester_name', '').strip()
        cabinet_type = request.form.get('cabinet_type', '').strip()

        try:
            res_data = process_barcode_request(
                project_name=DEFAULT_PROJECT,
                tester_name=tester_name,
                cabinet_type=cabinet_type,
            )

            build_folder = res_data['build_folder']
            labels = []
            for lbl in res_data['labels']:
                labels.append({
                    "section": lbl['section'],
                    "payload": lbl['payload'],
                    "barcode_url": f"/generated_barcodes/{build_folder}/{lbl['barcode_filename']}",
                    "qr_url": f"/generated_qrcodes/{build_folder}/{lbl['qr_filename']}",
                })

            result = {
                "project": res_data['project'],
                "tester": res_data['tester'],
                "build_num": res_data['build_num'],
                "cabinet": res_data['cabinet'],
                "build_folder": build_folder,
                "labels": labels,
            }

            next_build_num = str(peek_next_build_number()).zfill(4)

        except Exception as e:
            error_msg = str(e) or f"Tundmatu viga: {type(e).__name__}"

    return render_template(
        'index.html',
        next_build_num=next_build_num,
        cabinet_options=list(CABINET_SECTIONS.keys()),
        result=result,
        error=error_msg,
    )


# --- Startup helper ---------------------------------------------------------

def _open_browser():
    """Opens the app in the default browser after a short delay."""
    webbrowser.open(APP_URL)


if __name__ == '__main__':
    # Auto-open browser 1.5 s after startup (gives Flask time to bind the port)
    threading.Timer(1.5, _open_browser).start()

    # debug=False in .exe; set to True locally for auto-reload
    is_frozen = getattr(sys, 'frozen', False)
    app.run(host=APP_HOST, port=APP_PORT, debug=not is_frozen)