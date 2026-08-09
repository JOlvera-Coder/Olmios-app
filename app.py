import os
from flask import Flask, render_template_string, request, redirect, url_for, jsonify

app = Flask(__name__)

# --- 1. SIGN IN / REGISTER GATEWAY ('/') ---
@app.route('/')
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Customer Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: system-ui, -apple-system, sans-serif; }
        .auth-card { background: #1e293b; border-radius: 20px; padding: 30px; width: 100%; max-width: 420px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); }
        .phoenix-svg { width: 90px; height: 90px; filter: drop-shadow(0 0 15px rgba(217, 119, 6, 0.5)); }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 700; }
        .btn-amber:hover { background: #b45309; color: white; }
    </style>
</head>
<body>
    <div class="auth-card text-center">
        <svg class="phoenix-svg mb-2" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M50 5 L60 30 L85 35 L65 52 L72 78 L50 63 L28 78 L35 52 L15 35 L40 30 Z" fill="#d97706" stroke="#fbbf24" stroke-width="2"/>
            <circle cx="50" cy="45" r="12" fill="#f59e0b"/>
            <path d="M50 15 L53 25 L60 25 L55 30 L57 38 L50 33 L43 38 L45 30 L40 25 L47 25 Z" fill="#ffffff"/>
        </svg>
        <h2 class="fw-bold tracking-wide text-white mb-1">OLMIOS</h2>
        <p class="small text-muted mb-4">Dedicated HVAC Customer Portal</p>
        
        <ul class="nav nav-pills nav-justified mb-3 bg-dark rounded-3 p-1">
            <li class="nav-item"><button class="nav-link active py-2 fw-bold" id="tab-login" onclick="toggleAuth('login')">Sign In</button></li>
            <li class="nav-item"><button class="nav-link text-white py-2 fw-bold" id="tab-register" onclick="toggleAuth('register')">Register</button></li>
        </ul>

        <div id="form-login">
            <div class="mb-3 text-start"><label class="small text-muted fw-bold">USERNAME / EMAIL</label><input type="text" class="form-control rounded-3" placeholder="john.doe@example.com"></div>
            <div class="mb-3 text-start"><label class="small text-muted fw-bold">PASSWORD</label><input type="password" class="form-control rounded-3" placeholder="••••••••"></div>
            <a href="/customer_home" class="btn btn-amber w-100 py-2 rounded-3 mb-2">Access Dashboard</a>
        </div>

        <div id="form-register" style="display: none;">
            <div class="mb-2 text-start"><label class="small text-muted fw-bold">FULL NAME</label><input type="text" class="form-control rounded-3" placeholder="John Doe"></div>
            <div class="mb-2 text-start"><label class="small text-muted fw-bold">CREATE USERNAME</label><input type="text" class="form-control rounded-3" placeholder="johndoe_hvac"></div>
            <div class="mb-2 text-start"><label class="small text-muted fw-bold">PASSWORD</label><input type="password" class="form-control rounded-3" placeholder="Create strong password"></div>
            <div class="mb-3 text-start"><label class="small text-muted fw-bold">SERVICE ADDRESS</label><input type="text" class="form-control rounded-3" placeholder="1234 Main St, Houston, TX"></div>
            <a href="/customer_home" class="btn btn-amber w-100 py-2 rounded-3">Create Account & Continue</a>
        </div>
    </div>

    <script>
    function toggleAuth(mode) {
        if(mode === 'login') {
            document.getElementById('form-login').style.display = 'block';
            document.getElementById('form-register').style.display = 'none';
            document.getElementById('tab-login').className = 'nav-link active py-2 fw-bold';
            document.getElementById('tab-register').className = 'nav-link text-white py-2 fw-bold';
        } else {
            document.getElementById('form-login').style.display = 'none';
            document.getElementById('form-register').style.display = 'block';
            document.getElementById('tab-login').className = 'nav-link text-white py-2 fw-bold';
            document.getElementById('tab-register').className = 'nav-link active py-2 fw-bold';
        }
    }
    </script>
</body>
</html>"""

# --- 2. MAIN CUSTOMER DASHBOARD ('/customer_home') ---
@app.route('/customer_home')
def customer_home():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Customer Home</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background-color: #0f172a; color: white; font-family: system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        #map { height: 260px; border-radius: 12px; margin-bottom: 15px; }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 700; }
        .btn-amber:hover { background: #b45309; color: white; }
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <div class="d-flex align-items-center gap-2">
                <img id="home_avatar" src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80" style="width: 45px; height: 45px; border-radius: 50%; object-fit: cover;">
                <div>
                    <h6 class="fw-bold mb-0 text-dark">WELCOME BACK</h6>
                    <span class="fw-bold text-primary">John Doe</span>
                </div>
            </div>
            <svg style="width:36px; height:36px;" viewBox="0 0 100 100" fill="none">
                <path d="M50 5 L60 30 L85 35 L65 52 L72 78 L50 63 L28 78 L35 52 L15 35 L40 30 Z" fill="#d97706"/>
            </svg>
        </div>

        <div class="bg-light p-2 rounded-3 text-center mb-3 border">
            <span class="fw-bold text-dark" style="font-size: 0.9rem;">⭐⭐⭐⭐⭐ 4.9 (Customer Rating from Field Techs)</span>
        </div>

        <h6 class="fw-bold text-muted small text-center mb-2">LIVE ACTIVE FIELD TECHNICIAN COVERAGE BY ZIP CODE</h6>
        <div id="map"></div>

        <a href="/dispatch_request" class="btn btn-amber w-100 py-3 rounded-3 fw-bold fs-6 mb-2">⚡ REQUEST INSTANT HVAC SERVICE</a>
        
        <div class="row g-2 mb-2">
            <div class="col-6"><a href="/profile" class="btn btn-outline-secondary w-100 py-2 fw-bold small">👤 Profile & Wallet</a></div>
            <div class="col-6"><a href="/invoices" class="btn btn-outline-secondary w-100 py-2 fw-bold small">📜 View Invoices</a></div>
        </div>

        <div class="text-center bg-success text-white py-2 rounded-3 small fw-bold">
            🛡️ VERIFIED OLMIOS GUARANTEE - 100% Licensed & Background-Checked
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([29.7604, -95.3698], 10);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
        L.marker([29.7604, -95.3698]).addTo(map).bindPopup('Active Field Technician Unit #402').openPopup();
    </script>
</body>
</html>"""

# --- 3. INSTANT DISPATCH REQUEST ('/dispatch_request') ---
@app.route('/dispatch_request')
def dispatch_request():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Request Service</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: white; font-family: system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 700; }
    </style>
</head>
<body>
    <div class="main-card">
        <div class="text-center mb-3">
            <h4 class="fw-bold text-dark mb-1">Instant HVAC Dispatch Request</h4>
            <div class="bg-success-subtle text-success border border-success rounded-3 p-1 small fw-bold">
                ✓ Profile Verified: John Doe (832) 388-4957
            </div>
        </div>

        <div class="mb-3">
            <label class="form-label fw-bold small text-muted">SELECT JOB SITE PROPERTY ADDRESS</label>
            <select class="form-select rounded-3">
                <option>📍 Primary Residential: 3217 Montrose Blvd, Suite 100, Houston, TX</option>
            </select>
        </div>

        <div class="mb-3">
            <label class="form-label fw-bold small text-muted">EQUIPMENT TYPE</label>
            <select class="form-select rounded-3">
                <option>A/C Condenser</option>
                <option>Furnace / Air Handler</option>
                <option>Complete Split System</option>
                <option>Commercial RTU</option>
            </select>
        </div>

        <!-- DIAGNOSTIC CHAT + FILE DRAG & DROP -->
        <div class="p-3 mb-3 rounded-4" style="background: #f0f7ff; border: 2px solid #3b82f6;">
            <div class="d-flex align-items-center gap-2 mb-2">
                <span style="font-size: 1.2rem;">🦅</span>
                <h6 class="fw-bold mb-0 text-primary">OLMIOS Diagnostic Chat Assistant</h6>
            </div>
            <p class="small text-muted mb-2">Describe symptoms, defect notes, or drag & drop equipment images:</p>
            
            <div id="drop_zone" style="border: 2px dashed #93c5fd; background: #ffffff; border-radius: 12px; padding: 10px;">
                <textarea id="chat_assistant_input" class="form-control border-0 bg-transparent" rows="3" placeholder="e.g., Blower motor is making noise..."></textarea>
                
                <div class="d-flex justify-content-between align-items-center mt-2 pt-2 border-top">
                    <label class="btn btn-sm btn-light border text-primary fw-semibold mb-0" style="cursor: pointer;">
                        📷 Attach Photo <input type="file" id="image_upload_input" accept="image/*" multiple style="display: none;" onchange="handleFileSelect(event)">
                    </label>
                    <span class="small text-muted" id="file_count_badge">Drop images here</span>
                </div>
                <div id="image_preview_container" class="d-flex gap-2 flex-wrap mt-2"></div>
            </div>

            <button type="button" class="btn btn-primary w-100 mt-3 py-2 fw-bold rounded-3 shadow-sm" onclick="autoFillDescription()">
                ✨ AUTO-FILL ISSUE DESCRIPTION
            </button>
        </div>

        <div class="mb-3">
            <label class="form-label fw-bold small text-muted">ISSUE DESCRIPTION (FINAL DISPATCH SUMMARY)</label>
            <textarea id="issue_description" class="form-control rounded-3" rows="3" placeholder="Describe requested HVAC issue or click Auto-Fill above..."></textarea>
        </div>

        <div class="mb-3">
            <label class="form-label fw-bold small text-muted">SELECT SAVED PAYMENT CARD</label>
            <select class="form-select rounded-3">
                <option>💳 Visa ending in 1004</option>
            </select>
        </div>

        <button type="button" class="btn btn-amber w-100 py-3 rounded-3 fw-bold mb-2" onclick="alert('Service Request Dispatched! A technician is being assigned.')">
            💳 Request Service & Dispatch Tech
        </button>
        
        <a href="/customer_home" class="btn btn-outline-secondary w-100 py-2 rounded-3 fw-bold small">Home Page</a>
    </div>

    <script>
    function autoFillDescription() {
        let chatInput = document.getElementById('chat_assistant_input').value.trim();
        let issueBox = document.getElementById('issue_description');
        let lowerChat = chatInput.toLowerCase();
        
        let isOutdoor = lowerChat.includes('condenser') || lowerChat.includes('outdoor') || lowerChat.includes('outside') || lowerChat.includes('compressor');
        let isIndoorBlower = lowerChat.includes('blower') || lowerChat.includes('furnace') || lowerChat.includes('air handler');
        let isCommercial = lowerChat.includes('rtu') || lowerChat.includes('rooftop');
        
        let specText = "";
        if (isCommercial) {
            specText = " | RTU M/N: Commercial Packaged Unit";
        } else if (isIndoorBlower) {
            specText = " | Furnace M/N: S8X1B040M (S/N: 24001MN091)";
        } else if (isOutdoor) {
            specText = " | Condenser M/N: 4TTR6036N (S/N: 21045XY892)";
        } else {
            specText = " | Condenser M/N: 4TTR6036N, Furnace M/N: S8X1B040M";
        }

        if (chatInput !== "") {
            issueBox.value = chatInput + specText;
        }
    }

    let dropZone = document.getElementById('drop_zone');
    let previewContainer = document.getElementById('image_preview_container');
    let fileBadge = document.getElementById('file_count_badge');

    ['dragenter', 'dragover'].forEach(e => dropZone.addEventListener(e, (evt) => { evt.preventDefault(); dropZone.style.background = '#e0f2fe'; }));
    ['dragleave', 'drop'].forEach(e => dropZone.addEventListener(e, (evt) => { evt.preventDefault(); dropZone.style.background = '#ffffff'; }));

    dropZone.addEventListener('drop', (e) => { handleFiles(e.dataTransfer.files); });
    function handleFileSelect(e) { handleFiles(e.target.files); }

    function handleFiles(files) {
        if (files.length > 0) {
            fileBadge.innerText = files.length + " photo(s) attached";
            fileBadge.className = "small text-success fw-bold";
        }
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                let reader = new FileReader();
                reader.onload = function(e) {
                    let img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.cssText = "width: 45px; height: 45px; object-fit: cover; border-radius: 6px; border: 1px solid #cbd5e1;";
                    previewContainer.appendChild(img);
                };
                reader.readAsDataURL(file);
            }
        });
    }
    </script>
</body>
</html>"""

# --- 4. CUSTOMER PROFILE & WALLET ('/profile') ---
@app.route('/profile')
def profile():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Profile</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: white; font-family: system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
    </style>
</head>
<body>
    <div class="main-card">
        <div class="text-center mb-4">
            <h4 class="fw-bold text-dark mb-0">👤 Customer Profile & Wallet</h4>
        </div>

        <div class="mb-4 text-center">
            <img id="profile_avatar_preview" src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" style="width: 90px; height: 90px; object-fit: cover; border-radius: 50%; border: 3px solid #3b82f6;" class="mb-2">
            <div>
                <label class="btn btn-sm btn-outline-primary fw-bold rounded-3">
                    📷 Upload Profile Picture
                    <input type="file" accept="image/*" style="display: none;" onchange="previewProfilePic(event)">
                </label>
            </div>
        </div>

        <div class="mb-3">
            <label class="form-label fw-bold small text-muted">FIRST NAME</label>
            <input type="text" class="form-control rounded-3" value="John">
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold small text-muted">LAST NAME</label>
            <input type="text" class="form-control rounded-3" value="Doe">
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold small text-muted">PHONE NUMBER</label>
            <input type="text" class="form-control rounded-3" value="(832) 388-4957">
        </div>

        <div class="p-3 mb-3 border rounded-3 bg-light">
            <h6 class="fw-bold text-dark mb-2">📍 Manage Equipment by Property Location</h6>
            <select class="form-select rounded-3 mb-2">
                <option>🏡 Main Residence - 3217 Montrose Blvd, Houston, TX</option>
                <option>🏢 Commercial Property - 5678 Aldine Rd, Houston, TX</option>
            </select>
            <button class="btn btn-sm btn-outline-primary fw-bold rounded-3 w-100" onclick="alert('Form opened to register new equipment.')">➕ Add Additional Equipment</button>
        </div>

        <a href="/customer_home" class="btn btn-secondary w-100 py-2 rounded-3 fw-bold">Home Page</a>
    </div>

    <script>
    function previewProfilePic(e) {
        if(e.target.files && e.target.files[0]) {
            let reader = new FileReader();
            reader.onload = function(evt) { document.getElementById('profile_avatar_preview').src = evt.target.result; }
            reader.readAsDataURL(e.target.files[0]);
        }
    }
    </script>
</body>
</html>"""

# --- 5. INVOICES & REFUND REQUESTS ('/invoices') ---
@app.route('/invoices')
def invoices():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Invoices</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: white; font-family: system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
    </style>
</head>
<body>
    <div class="main-card">
        <h4 class="fw-bold text-dark mb-3 text-center">📜 Service Invoices</h4>
        
        <div class="border rounded-3 p-3 mb-3 bg-light">
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-bold">INV-1002 (Capacitor Replacement)</span>
                <span class="badge bg-success">Paid</span>
            </div>
            <div class="small text-muted mb-2">Service Date: 08/01/2026 | Amount: $185.00</div>
            <button class="btn btn-outline-danger btn-sm w-100 fw-bold rounded-3" onclick="alert('Refund Request Submitted. Billing department will follow up within 24 hours.')">
                ↩️ Request Refund
            </button>
        </div>

        <a href="/customer_home" class="btn btn-secondary w-100 py-2 rounded-3 fw-bold">Home Page</a>
    </div>
</body>
</html>"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
