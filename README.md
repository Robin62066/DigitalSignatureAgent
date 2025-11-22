# 🧾 DigitalSignatureAgent

**DigitalSignatureAgent** is a lightweight client-side signing utility designed to digitally sign PDF documents using a **USB dongle (token)** that contains a valid **digital certificate (PKCS#11)**.  
It runs locally on the user’s computer and exposes a secure REST API that your **Django web application** (or any other web client) can interact with — ensuring that **the private key never leaves the token or client machine**.

---

## 🚀 Features

- 🔐 **Client-side digital signing** – private key remains securely in the USB token.
- 🧾 **PDF signing** – digitally sign PDF files in PKCS#7/PAdES-compliant format.
- 🧠 **Plug-and-play architecture** – easily integrate with any Django or web application.
- ⚙️ **Local REST API** – simple HTTP interface (`http://localhost:5001`) for PDF signing and status checking.
- 🪪 **PKCS#11 compatible** – supports tokens from Watchdata, ePass, SafeNet, and other vendors.
- 💡 **Cross-platform** – works on both **Windows** and **Ubuntu Linux** servers or desktops.
- 🧰 **Installer-ready** – packaged via **PyInstaller** for one-click installation and background startup.

---

## Project Structure

- **DigitalSignatureAgent**

  - common\images
    -logo-icon.ico
    -logo.png
    -seal.png
  - agent

    - main.py
    - config.py
    - pkcs11_utils.py
    - tray_gui.py
    - signer.py
    - version.py

  -installer
  -icons
  -logo_icon.ico
  -output
  -build_installer.bat
  -DigitalSignatureAgent_setup.exe
  -setup.nsi
  -uninstall.bat
  -dist
  -DigitalSignatureAgent.exe # for testing

  -build
  DigitalSignatureAgent
  -localpycs
  -pyimod01_achive.pyc
  -pyimod02_importers.pyc
  -pyimod03_dtypes.pyc
  -pyimod04_pywin32.pyc
  -struct.pyc
  -Analysis-00.toc
  -base_libarary.zip
  -DigitalSignatyreAgent.pkg
  -EXE-00.toc
  -PKG-00.toc
  -PYZ-00.toc
  -PYZ-00.pyz
  -warn-DititalSignatureAgent.txt
  -xref-DigitalSignatureAgent.html
  -signed_docs
  -unsigned_docs

  - .env
  - README.md
  - requirements.txt
  - setup.py
    -build_exe.bat
    -build_linux.sh
    -build_windows.bat
    -DigitalSignatureAgent-setup.exe
    -DigitalSignatureAgent.spec
    -installer.nsi
    -License.txt
    -main.py
    -main.spec

---

## ⚙️ Installation

### Part1

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/DigitalSignatureAgent.git
```

### 2. Environment Setup

```bash
Using requirements.txt install all dependencies
```

### 3. Activate IT

```bash
Commands
	pyinstaller --onefile --noconsole --name "DigitalSignatureAgent"    --icon=common/images/logo_icon.ico --add-data "common/images/logo.png;common/images" --add-data "common/images/logo_icon.ico;common/images" --add-data "common/images/seal.png;common/images" --hidden-import="agent.config" --hidden-import="agent.signer" --hidden-import="agent.version" --hidden-import="pkcs11" --hidden-import="pkcs11.attributes" --hidden-import="pkcs11.constants" --hidden-import="pkcs11.util" --hidden-import="cryptography" --hidden-import="flask" --hidden-import="flask_cors" --hidden-import="pystray" --hidden-import="PIL" --hidden-import="reportlab" --hidden-import="PyPDF2" --hidden-import="requests" main.py

Second(for testing use)
dist\DigitalSignatureAgent.exe

(venv-eSign) D:\DigitalSignatureAgent>cd installer

(venv-eSign) D:\DigitalSignatureAgent\installer>build_installer.bat

Installation Steps (End-User)
  --> Download Installer: Obtain DigitalSignatureAgent_Setup.exe.
  -->Run Installation: Execute the installer and follow the Setup Wizard prompts.
  -->Verify Installation: Check for the System Tray Icon and verify that the API is running by navigating to http://127.0.0.1:5001 in a web browser.
```

### Part 2

### 1. Connect the dongle

### 2. Install the Agent (WD PROXkey) // Its Mendatory to install

    if not in dongle then download it
      when you install path will
      ```
      C:\Windows\System32\Watchdata\PROXKey CSP India V3.0\wdpkcs.dll
      ```
      if this PROXKey CSP India V3.0  verson looks diffrent then change it in you code rebuild the agent

### Part 3

### The Django implementation code (inside it single and bulk signing option also)

```bash
{% include "header.html" %}
{% load custom_tags %}

    <script type="text/javascript">
        $(document).ready(function() {
        getFirmType();
        getinspection();
        });

        function getFirmType(){
        $.ajax({
                url: '{% url "firmtype_list" %}',
                dataType: 'json',
                success: function(response) {
                    var dropdown = $('#firm-type-dropdown');
                    dropdown.empty();
                    dropdown.append('<option value="">Select</option>');
                    response.forEach(function(item) {
                        let selected = item.id == '{{ where.firm_type }}' ? 'selected' : '';
                        dropdown.append(`<option value="${item.id}" ${selected}>${item.name}</option>`);
                    });
                },
                error: function() {
                    alert("Error fetching firm types.");
                }
            });
        }

        function getinspection(){
        $.ajax({
                url: '{% url "get_sublocations" %}',
                dataType: 'json',
                success: function(response) {
                    var dropdown = $('#sub_location');
                    dropdown.empty();
                    dropdown.append('<option value="">Select</option>');
                    // response.forEach(function(t){
                    //   alert(t.id );
                    // });
                    response.forEach(function(item) {
                        let selected = item.id == '{{ where.sub_location }}' ? 'selected' : '';
                        dropdown.append(`<option value="${item.id}" ${selected}>${item.name}</option>`);
                    });
                },
                error: function() {
                    alert("Error fetching firm types.");
                }
            });
        }
    </script>

    <style type="text/css">
    .card-header {
            background-color: hsla(111, 93%, 11%, 0.913);
            color: white;
        }
    /* Modern ring loader */
        .lds-ring { display:inline-block; position:relative; width:70px; height:70px; }
        .lds-ring div{
        box-sizing:border-box; display:block; position:absolute; width:54px; height:54px; margin:8px;
        border:6px solid #007bff; border-radius:50%; animation:lds-ring 1.2s linear infinite;
        border-color:#007bff transparent transparent transparent;
        }
        .lds-ring div:nth-child(1){ animation-delay:-0.45s }
        .lds-ring div:nth-child(2){ animation-delay:-0.3s }
        .lds-ring div:nth-child(3){ animation-delay:-0.15s }
        @keyframes lds-ring{ 0%{ transform:rotate(0) } 100%{ transform:rotate(360deg) } }

        /* Progress bar polish */
        #digitalSignatureModal .progress { background-color:#e9ecef; height:10px; }
        #digitalSignatureModal .progress-bar { transition:width .25s ease; }

        /* Message spacing tidy */
        #signMessage h5 { margin-bottom:.25rem; }
        #signMessage p  { margin-bottom:0; }


    </style>
    <style>
        #digitalSignatureModal .modal-content {
            border-radius: 10px;
            border: none;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        #digitalSignatureModal .modal-header {
            border-radius: 10px 10px 0 0;
            border-bottom: none;
        }

        #digitalSignatureModal .btn-success {
            border-radius: 8px;
            font-weight: 600;
            padding: 12px;
            transition: all 0.3s ease;
        }

        #digitalSignatureModal .btn-success:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        #digitalSignatureModal .alert {
            border-radius: 8px;
            border: none;
        }

        .btn:disabled {
            cursor: not-allowed;
            opacity: 0.6;
        }
    </style>
    <div class="col-md-10" id="resize02">
        <div class="col-12">
            <div class="card m-b-30">
                <div class="card-header" style="margin-bottom:10px;">
                    {% comment %} <span class="pull-left font-weight-bold">{{action|title}} Search</span> {% endcomment %}
                    <span class="pull-left font-weight-bold">Search</span>
                </div>

                <div class="card-body px-1">
                    <!-- Search Form -->
                    <div class="border border-info rounded p-2">
                        <form id="inbox_form" name="inbox_form" action="/admin/digital_signedbox_list/{{action}}/" method="post" class="mb-0">
                        {% csrf_token %}
                            <table class="table table-borderless table-head mb-0">
                                <tbody>
                                <tr>
                                    <td><b>From Date</b></td>
                                    <td>:</td>
                                    <td>
                                    <input type="text" value="{{ where.from_date }}" id="from_date" class="form-control tcal" name="from_date" placeholder="From Begin">
                                    </td>
                                    <td><b>To Date</b></td>
                                    <td>:</td>
                                    <td>
                                    <input type="text" value="{{ where.upto_date }}" id="upto_date" class="form-control tcal" name="upto_date" placeholder="To End">
                                    </td>
                                </tr>
                                <tr>
                                    <td><b>Inspection Area</b></td>
                                    <td>:</td>
                                    <td>
                                    <select class="form-control" name="sub_location" id="sub_location">
                                        <option value="select">Select</option>
                                        <!-- Options will be dynamically populated here via AJAX -->
                                    </select>
                                    </td>
                                    <td><b>Firm Type</b></td>
                                    <td>:</td>
                                    <td>
                                    <select class="form-control" name="firm_type" id="firm-type-dropdown">
                                        <option value="select">Select</option>
                                        <!-- Options will be dynamically populated here via AJAX -->
                                    </select>
                                    </td>
                                </tr>
                                <tr>
                                    <td><b>Search By</b></td>
                                    <td>:</td>
                                    <td>
                                    <input type="text" value="{{ where.txt_Search }}" name="txt_Search" class="form-control" placeholder="Enter keywords">
                                    </td>
                                    <td><b>Document Type</b></td>
                                    <td>:</td>
                                    <td>
                                        <select name="doc_type" id="doc_type" class="form-control">
                                            <option value="signed" {% if action == "signed" %}selected{% endif %}>
                                                Signed Documents
                                            </option>

                                            <option value="unsigned" {% if action == "unsigned" %}selected{% endif %}>
                                                Unsigned Documents
                                            </option>
                                        </select>
                                    </td>

                                </tr>
                                <tr>
                                    <td colspan="6" style="text-align: center;">
                                    <button type="submit" name="btn_search" class="btn btn-success mt-2">Search</button>
                                    </td>
                                </tr>
                                </tbody>
                            </table>
                        </form>
                    </div>
                </div>
                {% if messages %}
                {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                    {% if message.level == DEFAULT_MESSAGE_LEVELS.ERROR %}<strong>Important: </strong>{% endif %}
                    {{ message }}
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                {% endfor %}
                {% endif %}

                <!-- Total data -->
                <div class="card shadow-none mt-0 mx-1">
                    <div class="card-header " style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                        <span class="pull-left font-weight-bold">Total {{ total_records }} data(s) found.</span>
                        </div>
                        {% if action == 'unsigned' %}
                            <button type="button" class="btn btn-warning" id="signAllBtn"
                                    data-toggle="modal" data-target="#digitalSignatureModal">
                                <i class="fas fa-file-signature"></i> Sign All Documents
                            </button>
                        {% endif %}
                    </div>
                    <div class="card-body px-2">
                        <!-- datas Table -->
                        <div class="table-responsive">
                            <table class="table table-sm table-bordered">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Subject</th>
                                        <th>Inspection Area</th>
                                        <th>Firm Type</th>
                                        <th>Recieved Date</th>
                                        {% if action == 'unsigned'%}
                                            <th>Action</th>
                                        {% endif %}
                                        <th>View</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for data in FirmMailList %}
                                        <tr>
                                            <td>{{ pagination_key.start_index|add:forloop.counter0 }}</td>
                                            <td>{{ data.subjects }}</td> <!-- Subject from FirmMail -->
                                            <td>{{ data.app_id.inspenction_area.name }}</td> <!-- Inspection Area -->
                                            <td>{{ data.app_id.firm_type }}</td> <!-- Firm Type -->
                                            <td>{{ data.created_at|date:"d-M-Y" }}</td>
                                            <td class="application_no" style="display:none;">{{ data.app_id.wmd_app_module}}</td>
                                            {% if action == 'unsigned'%}
                                                <td>
                                                <!-- Button to trigger modal -->
                                                <button type="button" class="btn btn-primary digitalSignBtn" data-toggle="modal" data-target="#digitalSignatureModal">
                                                    <i class="fas fa-signature"></i> Digital Signature
                                                </button>
                                                </td>
                                            {% endif %}

                                            <td>
                                                <a href="javascript:PopupCenter('{% url 'approved_license' action data.app_id.id|get_encrypt  %}', '600', '600')" class="btn btn-success">View</a>
                                            </td>

                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                            {% include "pagination_list.html" %}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </div>

    <!-- Digital Signature Modal -->
    <div class="modal" id="digitalSignatureModal" tabindex="-1" role="dialog" aria-labelledby="digitalSignatureModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-md" role="document">
            <div class="modal-content">

            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title" id="digitalSignatureModalLabel">
                <i class="fas fa-signature"></i> Sign Document
                </h5>
                <button type="button" class="close text-white" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
                </button>
            </div>

            <div class="modal-body">

                <!-- Header (shown before signing) -->
                <div id="signHeader" class="text-center mb-4">
                <i class="fas fa-file-signature fa-3x text-primary mb-3"></i>
                <h5>Digital Signature</h5>
                <p class="text-muted">Enter PIN to sign document</p>
                </div>

                <!-- Loader (replaces header during signing) -->
                <div id="signLoader" style="display:none; text-align:center; padding:20px;">
                <div class="lds-ring"><div></div><div></div><div></div><div></div></div>
                <p class="mt-3 font-weight-bold text-primary">Processing...</p>
                </div>

                <!-- Message area (success/error after signing) -->
                <div id="signMessage" style="display:none; text-align:center; padding:20px;"></div>

                <!-- Bulk progress -->
                <div id="bulkProgressWrap" style="display:none;">
                <div class="d-flex justify-content-between mt-2 mb-1">
                    <small id="bulkProgressText">0 / 0</small>
                    <small id="bulkProgressPct">0%</small>
                </div>
                <div class="progress">
                    <div id="bulkProgressBar" class="progress-bar bg-primary" role="progressbar" style="width:0%;"></div>
                </div>
                </div>

                <!-- PIN -->
                <div class="form-group mt-3">
                <label for="pin" class="font-weight-bold">PIN Code:</label>
                <div class="input-group">
                    <div class="input-group-prepend"><span class="input-group-text"><i class="fas fa-key"></i></span></div>
                    <input type="password" class="form-control" name="pin" id="pin" placeholder="Enter your token PIN" autocomplete="off" value="12345678">
                </div>
                <small class="form-text text-muted">Default PIN: 12345678</small>
                </div>

                <!-- Verify -->
                <button id="verifyAndSignBtn" class="btn btn-success btn-block btn-lg">
                <i class="fas fa-play-circle"></i> Verify PIN & Sign Document
                </button>

                <!-- Download (single only) -->
                <a id="downloadLink" class="btn btn-primary btn-block mt-3" style="display:none">
                <i class="fas a-download"></i> Download Signed PDF
                </a>

            </div>
            </div>
        </div>
    </div>

    <script>

        /* ==========================
        UI HELPERS
        ========================== */
        function uiShowLoader() {
        document.getElementById('signHeader').style.display = 'none';
        document.getElementById('signMessage').style.display = 'none';
        document.getElementById('signLoader').style.display = 'block';
        const btn = document.getElementById('verifyAndSignBtn');
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        btn.disabled = true;
        }
        function uiHideLoader() {
        document.getElementById('signLoader').style.display = 'none';
        }
        function uiShowSuccess(msg) {
        uiHideLoader();
        const box = document.getElementById('signMessage');
        box.style.display = 'block';
        box.innerHTML = `
            <i class="fas fa-check-circle fa-3x text-success"></i>
            <h5 class="mt-3">${msg}</h5>
        `;
        }
        function uiShowError(msg) {
        uiHideLoader();
        bulkProgressHide();
        const box = document.getElementById('signMessage');
        box.style.display = 'block';
        box.innerHTML = `
            <i class="fas fa-times-circle fa-3x text-danger"></i>
            <h5 class="mt-3 text-danger">Error</h5>
            <p>${msg}</p>
        `;
        const btn = document.getElementById('verifyAndSignBtn');
        btn.innerHTML = '<i class="fas fa-play-circle"></i> Verify PIN & Sign Document';
        btn.disabled = false;
        }
        function uiResetModal() {
        document.getElementById('pin').value = '12345678';
        document.getElementById('signHeader').style.display = 'block';
        document.getElementById('signLoader').style.display = 'none';
        document.getElementById('signMessage').style.display = 'none';
        document.getElementById('signMessage').innerHTML = '';
        document.getElementById('downloadLink').style.display = 'none';
        bulkProgressHide();
        const btn = document.getElementById('verifyAndSignBtn');
        btn.innerHTML = '<i class="fas fa-play-circle"></i> Verify PIN & Sign Document';
        btn.className = 'btn btn-success btn-block btn-lg';
        btn.disabled = false;
        }

        /* ==========================
        BULK PROGRESS
        ========================== */
        function bulkProgressShow(total) {
        document.getElementById('bulkProgressWrap').style.display = 'block';
        bulkProgressUpdate(0, total);
        }
        function bulkProgressHide() {
        document.getElementById('bulkProgressWrap').style.display = 'none';
        document.getElementById('bulkProgressBar').style.width = '0%';
        document.getElementById('bulkProgressText').innerText = '0 / 0';
        document.getElementById('bulkProgressPct').innerText = '0%';
        }
        function bulkProgressUpdate(done, total) {
        const pct = total > 0 ? Math.round((done / total) * 100) : 0;
        document.getElementById('bulkProgressText').innerText = `${done} / ${total}`;
        document.getElementById('bulkProgressPct').innerText = `${pct}%`;
        document.getElementById('bulkProgressBar').style.width = `${pct}%`;
        }

        /* ==========================
        STATE
        ========================== */
        let isBulkSigning = false;
        let bulkQueue = [];              // array of raw appNos (with slashes)
        let bulkTotal = 0;
        let selectedApplicationNo = null; // single
        let signedPdfBlob = null;
        let signedFilename = '';
        let bulkSavedFiles = [];          // filenames saved on server (for merge)

        /* ==========================
        SELECT A ROW (single)
        ========================== */
        document.addEventListener('click', (e) => {
        if (e.target.closest('.digitalSignBtn')) {
            isBulkSigning = false;
            const row = e.target.closest('tr');
            selectedApplicationNo = (row.querySelector('.application_no')?.innerText || '').trim();
        }
        });

        /* ==========================
        PREPARE BULK (Sign All btn)
        ========================== */
        document.getElementById('signAllBtn')?.addEventListener('click', () => {
        isBulkSigning = true;
        const items = [];
        document.querySelectorAll('td.application_no').forEach(td => {
            const raw = td.innerText.trim();
            if (raw) items.push(raw);
        });
        bulkQueue = items;
        bulkTotal = items.length;
        bulkSavedFiles = [];
        document.getElementById('signMessage').style.display = 'none';
        document.getElementById('signMessage').innerHTML = '';
        });

        /* ==========================
         VERIFY & SIGN (with PERFECT error handling)
        ========================== */
        async function verifyAndSignAllInOne(appNoOverride = null) {

            const appNoRaw = appNoOverride || selectedApplicationNo;
            if (!appNoRaw) {
                uiShowError("❌ Application Number Not Found.");
                return false;
            }

            const cleanedAppNo = appNoRaw.replace(/\//g, '');
            const pdfFilename = `unsingedDoc_${cleanedAppNo}.pdf`;
            const pin = document.getElementById('pin').value.trim();


            if (!pin) {
                uiShowError("🔐 Please enter your PIN before signing.");
                return false;
            }

            try {
                /* ------------------------------------
                 STEP 1: VERIFY CERTIFICATE / PIN
                ------------------------------------- */
                let certRes;
                try {
                    certRes = await fetch("http://127.0.0.1:5001/cert-info", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ pin })
                    });
                } catch (networkErr) {
                    console.error("Agent network error:", networkErr);

                    uiShowError(`
                        <div style="font-size:16px; line-height:1.5;">
                            <strong style="font-size:18px;">Digital Signature Agent Not Reachable</strong>
                            <div style="margin-top:10px; color:#555;">
                                Please check the following:
                                <li>Agent Not running</li>
                                <li style="margin-right:10px;">USB Not Inserted</li>
                                <li style="margin-right:38px;">Incorrect Pin </li>
                            </div>
                        </div>
                    `);

                    //  STOP EVERYTHING HERE
                    return false;
                }


                /*  Agent reached but error occurred */
                const certData = await certRes.json();
                console.log("CERT ERROR RAW:", certData);

                //  Stop immediately if certificate check returned ANY error
                if (certData.error_type) {

                    const map = {
                        wrong_pin: "❌ Incorrect PIN. Please try again.",
                        dongle_missing: "🔌 USB Token not detected.",
                        token_locked: "🔒 Token locked. Too many wrong attempts.",
                        pkcs11_load_error: "⚠️ Token driver error. Reinstall drivers."
                    };

                    uiShowError(map[certData.error_type] || certData.error || "Unknown certificate error.");
                    return false;
                }

                //  Support older agent versions
                if (certData.error) {
                    uiShowError(certData.error);
                    return false;
                }


                /* ------------------------------------
                     STEP 2: SIGN PDF
                ------------------------------------- */
                let signRes;
                try {
                    signRes = await fetch("http://127.0.0.1:5001/sign-pdf", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ pin, pdf_filename: pdfFilename })
                    });
                } catch (signNetErr) {
                    uiShowError(`❌ Cannot contact signing service.<br><b>${signNetErr.message}</b>`);
                    return false;
                }

                const signData = await signRes.json();

                /*  PDF NOT FOUND */
                if (signData.error && /file not found|no such file/i.test(signData.error)) {
                    uiShowError(`❌ PDF Not Found:<br>${pdfFilename}<br> Please regenerate unsigned PDF.`);
                    return false;
                }

                /*  Signing failed for another reason */
                if (signData.error) {
                    uiShowError(`❌ Signing failed:<br>${signData.error}`);
                    return false;
                }

                if (!signData.signed_pdf) {
                    uiShowError("❌ No signed PDF returned.");
                    return false;
                }

                /* ------------------------------------
                     STEP 3: SAVE SIGNED PDF IN DJANGO
                ------------------------------------- */
                const bytes = Uint8Array.from(atob(signData.signed_pdf), c => c.charCodeAt(0));
                signedPdfBlob = new Blob([bytes], { type: "application/pdf" });

                signedFilename = `signedDoc_${cleanedAppNo}.pdf`;

                const saveRes = await fetch("/save-signed-pdf/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-CSRFToken": "{{ csrf_token }}"
                    },
                    body: new URLSearchParams({
                        pdf_base64: signData.signed_pdf,
                        filename: signedFilename,
                        original_app_no: appNoRaw
                    })
                });

                if (!saveRes.ok) {
                    uiShowError(`❌ Failed to save file:<br>${signedFilename}`);
                    return false;
                }

                if (isBulkSigning) bulkSavedFiles.push(signedFilename);

                return true;

            } catch (err) {
                uiShowError(`❌ Unexpected Error:<br>${err.message}`);
                return false;
            }
        }



        /* ==========================
        SINGLE FLOW
        ========================== */
        async function handleSingle() {
        if (!selectedApplicationNo) return uiShowError('No application number found!');
        uiShowLoader();

        const ok = await verifyAndSignAllInOne(selectedApplicationNo);
        if (!ok) return;

        uiShowSuccess('Document Signed Successfully!');
        const dl = document.getElementById('downloadLink');
        dl.style.display = 'block';
        dl.setAttribute('download', signedFilename);

        const btn = document.getElementById('verifyAndSignBtn');
        btn.innerHTML = '<i class="fas fa-check-circle"></i> Signed Successfully';
        btn.className = 'btn btn-outline-success btn-block btn-lg';
        btn.disabled = true;
        }

        /* ==========================
        BULK FLOW
        ========================== */
        async function handleBulk() {
            if (!bulkQueue.length) return uiShowError('No documents found to sign.');

            uiShowLoader();
            bulkProgressShow(bulkTotal);

            let done = 0;

            //  BULK LOOP (paste this)
            for (const app of bulkQueue) {

                const ok = await verifyAndSignAllInOne(app);

                if (!ok) {
                    //  STOP BULK IMMEDIATELY ON ANY ERROR
                    bulkProgressHide();
                    isBulkSigning = false;
                    return;
                }

                done++;
                bulkProgressUpdate(done, bulkTotal);
            }

            //  All documents done
            bulkProgressHide();
            uiHideLoader();
            uiShowSuccess(`All ${bulkTotal} documents signed successfully!`);

            const btn = document.getElementById('verifyAndSignBtn');
            btn.innerHTML = '<i class="fas fa-check-circle"></i> Bulk Signing Completed';
            btn.className = 'btn btn-outline-success btn-block btn-lg';
            btn.disabled = true;

            isBulkSigning = false;
        }



        /* ==========================
        WIRING
        ========================== */
        document.getElementById('verifyAndSignBtn').addEventListener('click', () => {
        if (isBulkSigning) handleBulk();
        else handleSingle();
        });

        // Download (single)
        document.getElementById('downloadLink').addEventListener('click', () => {
        if (!signedPdfBlob) return;
        const url = URL.createObjectURL(signedPdfBlob);
        const a = document.createElement('a');
        a.href = url; a.download = signedFilename; a.click();
        URL.revokeObjectURL(url);
        });

        // Modal lifecycle
        $('#digitalSignatureModal').on('shown.bs.modal', () => { $('#pin').focus().select(); });
        $('#digitalSignatureModal').on('hidden.bs.modal', uiResetModal);
    </script>

    <script>
        const CSRF_TOKEN = "{{ csrf_token }}";
        document.getElementById('doc_type').addEventListener('change', function() {
            let selectedAction = this.value;  // signed OR unsigned
            let form = document.getElementById('inbox_form');

            // Update form action dynamically
            form.action = "/admin/digital_signedbox_list/" + selectedAction + "/";
        });

    </script>



```
