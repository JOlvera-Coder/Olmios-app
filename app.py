import os
from flask import Flask, render_template_string, request, redirect, url_for, jsonify

app = Flask(__name__)

# --- EMBEDDED GOLD PHOENIX SVG LOGO ---
PHOENIX_SVG = """<svg class="phoenix-logo" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fbbf24" />
            <stop offset="50%" stop-color="#d97706" />
            <stop offset="100%" stop-color="#92400e" />
        </linearGradient>
    </defs>
    <path d="M50 5 L60 30 L85 35 L65 52 L72 78 L50 63 L28 78 L35 52 L15 35 L40 30 Z" fill="url(#goldGrad)" stroke="#fef08a" stroke-width="1.5"/>
    <circle cx="50" cy="45" r="12" fill="#f59e0b"/>
    <path d="M50 15 L53 25 L60 25 L55 30 L57 38 L50 33 L43 38 L45 30 L40 25 L47 25 Z" fill="#ffffff"/>
</svg>"""

# --- 1. SIGN IN / REGISTER GATEWAY ('/') ---
@app.route('/')
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - On-Demand HVAC</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&display=swap" rel="stylesheet">
    <style>
        body { background-color: #0b1329; color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 20px; }
        .auth-card { background: #162038; border: 1px solid #2a3756; border-radius: 24px; padding: 32px 28px; width: 100%; max-width: 420px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); text-align: center; }
        .phoenix-logo { width: 110px; height: 110px; margin-bottom: 12px; filter: drop-shadow(0 0 22px rgba(217, 119, 6, 0.75)); animation: float 3s ease-in-out infinite; }
        .brand-title { font-size: 2.6rem; font-weight: 900; letter-spacing: 6px; background: linear-gradient(135deg, #ffffff 30%, #fbbf24 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase; margin-bottom: 6px; }
        .hero-badge { display: inline-block; background: rgba(217, 119, 6, 0.18); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); padding: 6px 16px; border-radius: 50px; font-weight: 700; font-size: 0.82rem; letter-spacing: 0.5px; margin-bottom: 24px; }
        .nav-pills { background: #0b1329; padding: 5px; border-radius: 14px; border: 1px solid #2a3756; }
        .nav-pills .nav-link { color: #94a3b8; border-radius: 10px; font-weight: 800; font-size: 0.95rem; transition: all 0.2s ease; }
        .nav-pills .nav-link.active { background: #3b82f6; color: white; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }
        .form-label { color: #ffffff !important; font-weight: 800; font-size: 0.8rem; letter-spacing: 1px; display: block; text-align: left; margin-bottom: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
        .form-control { height: 48px; border-radius: 12px; font-weight: 600; border: 1px solid #334155; font-size: 0.95rem; background: #ffffff; color: #0f172a; }
        .form-control:focus { border-color: #f59e0b; box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.25); }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 800; font-size: 1.05rem; height: 50px; border-radius: 12px; box-shadow: 0 10px 20px -5px rgba(217, 119, 6, 0.5); transition: transform 0.15s ease; }
        .btn-amber:hover { transform: translateY(-1px); color: white; background: linear-gradient(135deg, #ea580c, #b45309); }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
    </style>
</head>
<body>
    <div class="auth-card">
        """ + PHOENIX_SVG + """
        
        <div class="brand-title">OLMIOS</div>
        <div class="hero-badge">⚡ On-Demand HVAC Techs at Your Door</div>

        <ul class="nav nav-pills nav-justified mb-4">
            <li class="nav-item"><button class="nav-link active py-2.5" id="tab-login" onclick="toggleAuth('login')">Sign In</button></li>
            <li class="nav-item"><button class="nav-link py-2.5" id="tab-register" onclick="toggleAuth('register')">Register</button></li>
        </ul>

        <div id="form-login">
            <div class="mb-3">
                <label class="form-label">USERNAME / EMAIL</label>
                <input type="text" class="form-control" placeholder="Enter username or email">
            </div>
            <div class="mb-4">
                <label class="form-label">PASSWORD</label>
                <input type="password" class="form-control" placeholder="Enter password">
            </div>
            <a href="/customer_home" class="btn btn-amber w-100 d-flex align-items-center justify-content-center">Access Dashboard</a>
        </div>

        <div id="form-register" style="display: none;">
            <div class="mb-2">
                <label class="form-label">FULL NAME</label>
                <input type="text" class="form-control" placeholder="Enter full name">
            </div>
            <div class="mb-2">
                <label class="form-label">CREATE USERNAME</label>
                <input type="text" class="form-control" placeholder="Enter desired username">
            </div>
            <div class="mb-2">
                <label class="form-label">PASSWORD</label>
                <input type="password" class="form-control" placeholder="Create strong password">
            </div>
            <div class="mb-4">
                <label class="form-label">SERVICE ADDRESS</label>
                <input type="text" class="form-control" placeholder="Enter street address, city, state">
            </div>
            <a href="/customer_home" class="btn btn-amber w-100 d-flex align-items-center justify-content-center">Create Account & Continue</a>
        </div>
    </div>

    <script>
    function toggleAuth(mode) {
        if(mode === 'login') {
            document.getElementById('form-login').style.display = 'block';
            document.getElementById('form-register').style.display = 'none';
            document.getElementById('tab-login').className = 'nav-link active py-2.5';
            document.getElementById('tab-register').className = 'nav-link py-2.5';
        } else {
            document.getElementById('form-login').style.display = 'none';
            document.getElementById('form-register').style.display = 'block';
            document.getElementById('tab-login').className = 'nav-link py-2.5';
            document.getElementById('tab-register').className = 'nav-link active py-2.5';
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
        body { background-color: #0b1329; color: white; font-family: system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        #map { height: 260px; border-radius: 12px; margin-bottom: 15px; }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 700; }
        .btn-amber:hover { background: #b45309; color: white; }
        .phoenix-logo { width: 36px; height: 36px; }
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <div class="d-flex align-items-center gap-2">
                <img id="home_avatar" src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80" style="width: 45px; height: 45px; border-radius: 50%; object-fit: cover;">
                <div>
                    <h6 class="fw-bold mb-0 text-dark">WELCOME BACK</h6>
                    <span class="fw-bold text-primary">Customer Account</span>
                </div>
            </div>
            """ + PHOENIX_SVG + """
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
        body { background-color: #0b1329; color: white; font-family: system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 700; }
        .form-label { font-weight: 800; color: #334155 !important; font-size: 0.8rem; letter-spacing: 0.5px; }
    </style>
</head>
<body>
    <div class="main-card">
        <div class="text-center mb-3">
            <h4 class="fw-bold text-dark mb-1">Instant HVAC Dispatch Request</h4>
            <div class="bg-success-subtle text-success border border-success rounded-3 p-1 small fw-bold">
                ✓ Account Verified & Ready for Service
            </div>
        </div>

        <div class="mb-3">
            <label class="form-label">PURCHASE ORDER (PO) # (OPTIONAL)</label>
            <input type="text" class="form-control rounded-3" placeholder="e.g. PO-88204">
        </div>

        <div class="mb-3">
            <label class="form-label">EQUIPMENT TYPE</label>
            <select class="form-select rounded-3">
                <option value="">Select HVAC Equipment...</option>
                <option>A/C Condenser</option>
                <option>Furnace / Air Handler</option>
                <option>Complete Split System</option>
                <option>Commercial RTU</option>
            </select>
        </div>

        <div class="p-3 mb-3 rounded-4" style="background: #f0f7ff; border: 2px solid #3b82f6;">
            <div class="d-flex align-items-center gap-2 mb-2">
                <span style="font-size: 1.2rem;">🦅</span>
                <h6 class="fw-bold mb-0 text-primary">OLMIOS Diagnostic Chat Assistant</h6>
            </div>
            <p class="small text-muted mb-2">Describe symptoms, defect notes, or drag & drop equipment images:</p>
            
            <div id="drop_zone" style="border: 2px dashed #93c5fd; background: #ffffff; border-radius: 12px; padding: 10px;">
                <textarea id="chat_assistant_input" class="form-control border-0 bg-transparent" rows="3" placeholder="Describe symptoms or drag & drop photos here..."></textarea>
                
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
            <label class="form-label">ISSUE DESCRIPTION (FINAL DISPATCH SUMMARY)</label>
            <textarea id="issue_description" class="form-control rounded-3" rows="3" placeholder="Describe requested HVAC issue or click Auto-Fill above..."></textarea>
        </div>

        <div class="mb-3">
            <label class="form-label">SELECT PAYMENT METHOD</label>
            <select class="form-select rounded-3">
                <option value="">Select Saved Payment Card...</option>
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
        body { background-color: #0b1329; color: white; font-family: system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .form-label { font-weight: 800; color: #334155 !important; font-size: 0.8rem; letter-spacing: 0.5px; }
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
            <label class="form-label">FIRST NAME</label>
            <input type="text" class="form-control rounded-3" placeholder="Enter first name">
        </div>
        <div class="mb-3">
            <label class="form-label">LAST NAME</label>
            <input type="text" class="form-control rounded-3" placeholder="Enter last name">
        </div>
        <div class="mb-3">
            <label class="form-label">PHONE NUMBER</label>
            <input type="text" class="form-control rounded-3" placeholder="(832) 000-0000">
        </div>

        <div class="p-3 mb-3 border rounded-3 bg-light">
            <h6 class="fw-bold text-dark mb-2">📍 Manage Equipment by Property Location</h6>
            <select class="form-select rounded-3 mb-2">
                <option value="">Select Property Address...</option>
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
        body { background-color: #0b1329; color: white; font-family: system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
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
