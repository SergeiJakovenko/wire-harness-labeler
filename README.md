\# wire-harness-labeler



Barcode (Code128) and QR code label generator for wire harness production.



Generates a complete label set for one harness build — one 1D barcode and one QR code per cabinet section — with a crash-safe sequential build counter.



\## What it does



\- One cabinet type selection produces \*\*all section labels at once\*\*.

\- Supported cabinet types:

&#x20; - ``KKT``  → sections ``J00``, ``J01``, ``J02``, ``J03``

&#x20; - ``KKTT`` → sections ``J00``, ``J01``, ``J02``, ``J03``, ``J04``

&#x20; - ``KKKT`` → sections ``J00``, ``J01``, ``J02``, ``J03``, ``J04``

\- Each label carries a payload like ``0007KKTJ01`` (build number + cabinet + section).

\- The counter in ``counter.txt`` is committed \*\*only after every label in the batch has been written\*\*. A failure mid-batch leaves the counter untouched — no gaps, no duplicates.

\- Files are stored per build:



generated\_barcodes/0007\_KKT/barcode\_0007KKTJ00.png

generated\_qrcodes/0007\_KKT/qrcode\_0007KKTJ00.png



\## Web UI



Flask app, Estonian interface, three fields: tester name, cabinet type, submit.



\- ``app.py`` — Flask controller (routes, file serving).

\- ``barcode\_generator.py`` — core: validation, payload assembly, image generation, counter.

\- ``templates/index.html`` — UI (Estonian).

\- ``WireTester.spec`` — PyInstaller build config.



\## Run from source



Requirements: Python 3.10+.



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

pip install flask python-barcode qrcode pillow

python app.py



Then open http://127.0.0.1:5000.



\## Build a standalone .exe



```powershell

pip install pyinstaller

python -m PyInstaller WireTester.spec --clean

```



Output: dist\\WireTester.exe. Copy it to an empty folder and run — the app creates counter.txt, generated\_barcodes\\, and generated\_qrcodes\\ next to itself and opens the browser automatically.



\## Stack



· Flask — HTTP layer

· python-barcode — Code128 generation

· qrcode + Pillow — QR rendering

· PyInstaller — Windows packaging



\## License



MIT

