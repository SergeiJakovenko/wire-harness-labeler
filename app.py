import os
from datetime import datetime
from flask import Flask, render_template, request, send_from_directory
from barcode_generator import process_batch_request, QRCODES_DIR
from database import get_next_build_number, init_db

app = Flask(__name__)

# Инициализация базы данных при старте
init_db()

@app.route('/generated_qrcodes/<filename>')
def serve_qrcode(filename):
    return send_from_directory(QRCODES_DIR, filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    error_msg = None
    result = None

    next_build_num = get_next_build_number()
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == 'POST':
        tester_name = request.form.get('tester_name', '').strip()
        cabinet_type = request.form.get('cabinet_type', 'KKT').strip()

        try:
            result = process_batch_request(
                tester_name=tester_name,
                cabinet_type=cabinet_type
            )
            next_build_num = get_next_build_number()
        except Exception as e:
            error_msg = str(e)

    return render_template(
        'index.html',
        next_build_num=next_build_num,
        current_datetime=current_datetime,
        result=result,
        error=error_msg
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)