import os
from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session

app = Flask(__name__)
app.secret_key = 'olmios_secure_customer_session_key'

PHOENIX_SVG = """<svg width="120" height="120" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="goldFeathers" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fbbf24" />
            <stop offset="50%" stop-color="#d97706" />
            <stop offset="100%" stop-color="#92400e" />
        </linearGradient>
    </defs>
    <path d="M50 8 C72 8 88 18 88 42 C88 68 50 92 50 92 C50 92 12 68 12 42 C12 18 28 8 50 8 Z" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5"/>
    <path d="M50 22 C52 22 55 24 55 27 C55 30 52 32 50 34 C49 36 49 42 50 50 C51 58 53 68 50 78 C47 68 49 58 50 50 C51 42 51 36 50 34 C48 32 45 30 45 27 C45 24 48 22 50 22 Z" fill="url(#goldFeathers)" />
    <path d="M50 18 L53 23 L50 21 L47 23 Z" fill="#d97706"/>
    <path d="M53 26 L58 28 L54 30 Z" fill="#b45309"/>
    <path d="M48 36 C38 30 26 28 16 34 C24 38 32 40 40 46 C28 46 18 50 14 58 C22 58 32 56 42 58 C32 62 24 68 22 74 C30 72 38 68 46 64 Z" fill="url(#goldFeathers)" />
    <path d="M52 36 C62 30 74 28 84 34 C76 38 68 40 60 46 C72 46 82 50 86 58 C68 62 76 68 78 74 C70 72 62 68 54 64 Z" fill="url(#goldFeathers)"/>
    <path d="M50 70 L44 86 L50 82 L56 86 Z" fill="url(#goldFeathers)"/>
</svg>"""

def get_phoenix_svg(w=120, h=120):
    return PHOENIX_SVG.replace('width="120"', f'width="{w}"').replace('height="120"', f'height="{h}"')

COMMON_HEADER = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800;900&display=swap" rel="stylesheet">
"""

# --- 1. SIGN IN / REGISTER GATEWAY ('/') ---
@app.route('/')
def index():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Customer Portal</title>
    {{HEADER}}
    <style>
        body { background-color: #0b1329; color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 20px; }
        .auth-card { background: #162038; border: 1px solid #2a3756; border-radius: 24px; padding: 32px 28px; width: 100%; max-width: 420px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); text-align: center; }
        .brand-title { font-size: 2.6rem; font-weight: 900; letter-spacing: 6px; background: linear-gradient(135deg, #ffffff 30%, #fbbf24 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase; margin-top: 10px; margin-bottom: 6px; }
        .hero-badge { display: inline-block; background: rgba(217, 119, 6, 0.18); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); padding: 6px 16px; border-radius: 50px; font-weight: 700; font-size: 0.82rem; letter-spacing: 0.5px; margin-bottom: 24px; }
        .nav-pills { background: #0b1329; padding: 5px; border-radius: 14px; border: 1px solid #2a3756; }
        .nav-pills .nav-link { color: #94a3b8; border-radius: 10px; font-weight: 800; font-size: 0.95rem; transition: all 0.2s ease; }
        .nav-pills .nav-link.active { background: #3b82f6; color: white; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }
        .form-label { color: #ffffff !important; font-weight: 800; font-size: 0.8rem; letter-spacing: 1px; display: block; text-align: left; margin-bottom: 6px; }
        .form-control { height: 48px; border-radius: 12px; font-weight: 600; border: 1px solid #334155; font-size: 0.95rem; background: #ffffff; color: #0f172a; }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 800; font-size: 1.05rem; height: 50px; border-radius: 12px; box-shadow: 0 10px 20px -5px rgba(217, 119, 6, 0.5); }
    </style>
</head>
<body>
    <div class="auth-card">
        <a href="/customer_home" style="display:inline-block; text-decoration:none;">{{PHOENIX}}</a>
        <div class="brand-title">OLMIOS</div>
        <div class="hero-badge"><i class="fa-solid fa-bolt me-1"></i> On-Demand HVAC Techs at Your Door</div>

        <ul class="nav nav-pills nav-justified mb-4">
            <li class="nav-item"><button class="nav-link active py-2.5" id="tab-login" onclick="toggleAuth('login')">Sign In</button></li>
            <li class="nav-item"><button class="nav-link py-2.5" id="tab-register" onclick="toggleAuth('register')">Register</button></li>
        </ul>

        <div id="form-login">
            <div class="mb-3">
                <label class="form-label"><i class="fa-solid fa-envelope me-1"></i> USERNAME / EMAIL</label>
                <input type="text" id="login_user" class="form-control" placeholder="Enter username or email">
            </div>
            <div class="mb-4">
                <label class="form-label"><i class="fa-solid fa-lock me-1"></i> PASSWORD</label>
                <input type="password" class="form-control" placeholder="Enter password">
            </div>
            <button type="button" class="btn btn-amber w-100 d-flex align-items-center justify-content-center" onclick="handleLogin()">Access Dashboard</button>
        </div>

        <div id="form-register" style="display: none;">
            <div class="mb-2">
                <label class="form-label"><i class="fa-solid fa-user me-1"></i> FULL NAME</label>
                <input type="text" id="reg_fullname" class="form-control" placeholder="Enter full name">
            </div>
            <div class="mb-2">
                <label class="form-label"><i class="fa-solid fa-at me-1"></i> CREATE USERNAME</label>
                <input type="text" class="form-control" placeholder="Enter desired username">
            </div>
            <div class="mb-2">
                <label class="form-label"><i class="fa-solid fa-key me-1"></i> PASSWORD</label>
                <input type="password" class="form-control" placeholder="Create strong password">
            </div>
            <div class="mb-4">
                <label class="form-label"><i class="fa-solid fa-location-dot me-1"></i> SERVICE ADDRESS</label>
                <input type="text" id="reg_address" class="form-control" placeholder="Enter street address, city, state">
            </div>
            <button type="button" class="btn btn-amber w-100 d-flex align-items-center justify-content-center" onclick="handleRegister()">Create Account & Continue</button>
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

    function handleLogin() {
        localStorage.setItem('olmios_is_first_login', 'false');
        let userVal = document.getElementById('login_user').value.trim();
        if(userVal && !localStorage.getItem('olmios_fullname')) {
            localStorage.setItem('olmios_fullname', userVal);
        }
        window.location.href = '/customer_home';
    }

    function handleRegister() {
        let name = document.getElementById('reg_fullname').value.trim() || 'John Doe';
        let addr = document.getElementById('reg_address').value.trim();
        localStorage.setItem('olmios_fullname', name);
        if(addr) localStorage.setItem('olmios_saved_address', addr);
        localStorage.setItem('olmios_is_first_login', 'true');
        window.location.href = '/customer_home';
    }
    </script>
</body>
</html>"""
    return html.replace('{{HEADER}}', COMMON_HEADER).replace('{{PHOENIX}}', get_phoenix_svg(130, 130))

# --- LOGOFF ROUTE ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- 2. MAIN CUSTOMER DASHBOARD ('/customer_home') ---
@app.route('/customer_home')
def customer_home():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Customer Home</title>
    {{HEADER}}
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background-color: #0b1329; color: white; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        #map { height: 260px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #e2e8f0; }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 800; }
        .btn-amber:hover { background: #b45309; color: white; }
        .btn-nav-thin { border: 1px solid #cbd5e1; background: #ffffff; color: #1e293b; font-weight: 700; border-radius: 10px; transition: all 0.2s; }
        .btn-nav-thin:hover { background: #f8fafc; color: #0284c7; border-color: #38bdf8; }
        .guarantee-box { background: #059669; color: white; padding: 10px; border-radius: 12px; font-weight: 700; font-size: 0.85rem; text-align: center; }
        .btn-logoff { border: 1px solid #fca5a5; background: #fef2f2; color: #dc2626; font-weight: 800; border-radius: 12px; padding: 10px; width: 100%; transition: all 0.2s; text-decoration: none; display: block; text-align: center; }
        .btn-logoff:hover { background: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <div class="d-flex align-items-center gap-2">
                <img id="home_avatar" src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80" style="width: 45px; height: 45px; border-radius: 50%; object-fit: cover;">
                <div>
                    <h6 class="fw-bold mb-0 text-muted small" id="greeting_title">WELCOME BACK</h6>
                    <span class="fw-bold text-dark fs-6" id="display_fullname">Customer Account</span>
                </div>
            </div>
            <a href="/customer_home" title="Home">{{PHOENIX}}</a>
        </div>

        <div class="bg-light p-2 rounded-3 text-center mb-3 border border-1">
            <span class="fw-bold text-dark fs-6"><i class="fa-solid fa-star text-warning"></i> <i class="fa-solid fa-star text-warning"></i> <i class="fa-solid fa-star text-warning"></i> <i class="fa-solid fa-star text-warning"></i> <i class="fa-solid fa-star text-warning"></i> 4.9</span>
        </div>

        <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="fw-bold text-muted small mb-0"><i class="fa-solid fa-map-location-dot me-1 text-primary"></i> LIVE ACTIVE FIELD TECHNICIAN COVERAGE</h6>
            <button type="button" class="btn btn-sm btn-outline-primary py-0 px-2 fw-bold" style="font-size:0.75rem;" onclick="focusSavedLocation()"><i class="fa-solid fa-location-crosshairs me-1"></i> Saved Location</button>
        </div>
        <div id="map"></div>

        <a href="/dispatch_request" class="btn btn-amber w-100 py-3 rounded-3 fw-bold fs-6 mb-3 shadow-sm">
            <i class="fa-solid fa-bolt me-1"></i> REQUEST INSTANT HVAC SERVICE
        </a>
        
        <div class="row g-2 mb-3">
            <div class="col-6"><a href="/profile" class="btn btn-nav-thin w-100 py-2.5 small"><i class="fa-solid fa-user-gear me-1 text-primary"></i> Profile & Wallet</a></div>
            <div class="col-6"><a href="/invoices" class="btn btn-nav-thin w-100 py-2.5 small"><i class="fa-solid fa-receipt me-1 text-primary"></i> View Invoices</a></div>
        </div>

        <div class="guarantee-box shadow-sm mb-3">
            <i class="fa-solid fa-shield-halved me-1"></i> VERIFIED OLMIOS GUARANTEE - 100% Licensed & Background-Checked
        </div>

        <a href="/logout" class="btn-logoff shadow-sm" onclick="localStorage.removeItem('olmios_is_first_login');">
            <i class="fa-solid fa-right-from-bracket me-1"></i> Log Off
        </a>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([29.7604, -95.3698], 10);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

        var activeZip = L.polygon([
            [29.85, -95.45], [29.90, -95.35], [29.82, -95.30], [29.78, -95.40]
        ], { color: '#22c55e', strokeWidth: 1, fillColor: '#22c55e', fillOpacity: 0.35 }).addTo(map).bindPopup("<b>Active Tech Zip Code: 77037</b><br>Immediate Dispatch Available");

        var emergencyZip = L.polygon([
            [29.75, -95.38], [29.72, -95.32], [29.68, -95.36], [29.70, -95.42]
        ], { color: '#ef4444', strokeWidth: 1, fillColor: '#ef4444', fillOpacity: 0.35 }).addTo(map).bindPopup("<b>Emergency Zip Code: 77021</b>");

        var customerMarker = null;

        function loadCustomerSession() {
            let isFirst = localStorage.getItem('olmios_is_first_login');
            let name = localStorage.getItem('olmios_fullname') || 'John Doe';
            let addr = localStorage.getItem('olmios_saved_address') || '18510 Ranch View Trail Cir, Houston, TX';

            if(isFirst === 'true') {
                document.getElementById('greeting_title').innerText = "WELCOME";
            } else {
                document.getElementById('greeting_title').innerText = "WELCOME BACK";
            }
            document.getElementById('display_fullname').innerText = name;

            let savedPic = localStorage.getItem('olmios_profile_pic');
            if(savedPic) {
                document.getElementById('home_avatar').src = savedPic;
            }

            if(addr) {
                plotCustomerAddress(addr);
            }
        }

        function plotCustomerAddress(addressStr) {
            if(customerMarker) map.removeLayer(customerMarker);
            customerMarker = L.marker([29.7604, -95.3698]).addTo(map)
                .bindPopup("<b>🏠 Saved Residence Location</b><br>" + addressStr + "<br><span class='text-success fw-bold'>Tech in Route upon Service Request</span>")
                .openPopup();
        }

        function focusSavedLocation() {
            if(customerMarker) {
                map.setView(customerMarker.getLatLng(), 13);
                customerMarker.openPopup();
            }
        }

        window.onload = loadCustomerSession;
    </script>
</body>
</html>"""
    return html.replace('{{HEADER}}', COMMON_HEADER).replace('{{PHOENIX}}', get_phoenix_svg(45, 45))

# --- 3. INSTANT DISPATCH REQUEST ('/dispatch_request') ---
@app.route('/dispatch_request')
def dispatch_request():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Request Service</title>
    {{HEADER}}
    <style>
        body { background-color: #0b1329; color: white; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 800; }
        .form-label { font-weight: 800; color: #475569 !important; font-size: 0.78rem; letter-spacing: 0.5px; text-transform: uppercase; }
        .btn-category { border: 1.5px solid #cbd5e1; background: #f8fafc; color: #475569; font-weight: 700; border-radius: 12px; padding: 12px 6px; font-size: 0.85rem; width: 100%; transition: all 0.2s; cursor: pointer; }
        .btn-category.active { background: #f0f9ff; border-color: #0284c7; color: #0284c7; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2); }
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <div>
                <h5 class="fw-bold text-dark mb-0"><i class="fa-solid fa-truck-fast me-1 text-primary"></i> Instant HVAC Dispatch Request</h5>
            </div>
            <a href="/customer_home" title="Home">{{PHOENIX}}</a>
        </div>

        <div class="p-2 mb-3 rounded-3 bg-success-subtle border border-success-subtle text-success small fw-bold d-flex align-items-center gap-2">
            <i class="fa-solid fa-circle-check fs-6"></i>
            <span id="verified_status_line">Profile Verified & Ready</span>
        </div>

        <div class="row g-2 mb-3">
            <div class="col-4">
                <button type="button" class="btn-category active" id="cat_cooling" onclick="selectCat('cooling')">
                    <i class="fa-solid fa-snowflake text-info mb-1 d-block fs-5"></i> Cooling & AC
                </button>
            </div>
            <div class="col-4">
                <button type="button" class="btn-category" id="cat_heating" onclick="selectCat('heating')">
                    <i class="fa-solid fa-fire text-danger mb-1 d-block fs-5"></i> Heating
                </button>
            </div>
            <div class="col-4">
                <button type="button" class="btn-category" id="cat_maintenance" onclick="selectCat('maintenance')">
                    <i class="fa-solid fa-screwdriver-wrench text-warning mb-1 d-block fs-5"></i> Maintenance
                </button>
            </div>
        </div>

        <div class="mb-3">
            <label class="form-label">SELECT JOB SITE PROPERTY ADDRESS</label>
            <select class="form-select rounded-3" id="dispatch_address_select">
                <option value="primary">📍 Primary Residential Address</option>
            </select>
        </div>

        <div class="mb-3">
            <label class="form-label">PURCHASE ORDER (PO) # <span class="text-muted fw-normal">(OPTIONAL)</span></label>
            <input type="text" class="form-control rounded-3" placeholder="e.g. PO-88204">
        </div>

        <div class="mb-3">
            <label class="form-label">SERVICE URGENCY</label>
            <select class="form-select rounded-3">
                <option value="">Select Urgency Level...</option>
                <option value="standard">Standard Dispatch (Within 24 Hours)</option>
                <option value="emergency">🚨 Emergency Same-Day Dispatch</option>
            </select>
        </div>

        <div class="mb-3">
            <label class="form-label">EQUIPMENT TYPE (INCLUDES RESIDENTIAL & COMMERCIAL)</label>
            <select class="form-select rounded-3">
                <option value="">Select HVAC Equipment...</option>
                <option>A/C Condenser</option>
                <option>Furnace / Air Handler</option>
                <option>Complete Split System</option>
                <option>Commercial RTU</option>
            </select>
        </div>

        <div class="p-3 mb-3 rounded-4" style="background: #f0f7ff; border: 1.5px solid #3b82f6;">
            <div class="d-flex align-items-center gap-2 mb-2">
                {{PHOENIX_SMALL}}
                <h6 class="fw-bold mb-0 text-primary">OLMIOS Diagnostic Chat Assistant</h6>
            </div>
            <p class="small text-muted mb-2">Tell us what's going on! Mention symptoms, specific defective part notes, or paste image URLs:</p>
            
            <textarea id="chat_assistant_input" class="form-control mb-2" rows="3" placeholder="e.g., Fan motor is humming and unit is blowing warm air. Defective capacitor photo: https://example.com/cap.jpg"></textarea>
            
            <button type="button" class="btn btn-primary w-100 py-2 fw-bold rounded-3 shadow-sm" onclick="autoFillDescription()">
                <i class="fa-solid fa-wand-magic-sparkles me-1"></i> AUTO-FILL ISSUE DESCRIPTION
            </button>
        </div>

        <div class="mb-3">
            <label class="form-label">ISSUE DESCRIPTION (FINAL DISPATCH SUMMARY)</label>
            <textarea id="issue_description" class="form-control rounded-3" rows="3" placeholder="Describe requested HVAC issue or click Auto-Fill above..."></textarea>
        </div>

        <div class="mb-3">
            <label class="form-label">SELECT SAVED PAYMENT CARD</label>
            <select class="form-select rounded-3">
                <option value="">Select Payment Method...</option>
                <option selected>💳 Visa ending in 1004</option>
            </select>
        </div>

        <button type="button" class="btn btn-amber w-100 py-3 rounded-3 fw-bold mb-2 shadow-sm" onclick="alert('Service Request Dispatched! Technician assigned.')">
            💳 Request Service & Dispatch Tech
        </button>
        
        <a href="/customer_home" class="btn btn-outline-secondary w-100 py-2 rounded-3 fw-bold small"><i class="fa-solid fa-house me-1"></i> Home Page</a>
    </div>

    <script>
    function selectCat(catName) {
        document.querySelectorAll('.btn-category').forEach(b => b.classList.remove('active'));
        document.getElementById('cat_' + catName).classList.add('active');
    }

    function autoFillDescription() {
        let chatInput = document.getElementById('chat_assistant_input').value.trim();
        let issueBox = document.getElementById('issue_description');
        
        let prioritizedSpecs = " | [TECH SPECS SUMMARY]: " +
            "1. Manufacturer: Trane " +
            "| 2. System Energy: Gas Heat Pump " +
            "| 3. Tonnage: 3.0 Tons " +
            "| 4. SEER Rating: 16 SEER2 " +
            "| 5. Refrigerant Type: R-410A " +
            "| 6. Line Size: 3/8' Liquid x 7/8' Suction " +
            "| 7. Model/Serial: Condenser 4TTR6036N (S/N: 21045XY892), Furnace S8X1B040M";

        if (chatInput !== "") {
            issueBox.value = chatInput + prioritizedSpecs;
        } else {
            issueBox.value = "Customer requested diagnostic service." + prioritizedSpecs;
        }
    }

    window.onload = function() {
        let name = localStorage.getItem('olmios_fullname') || 'John Doe';
        let addr = localStorage.getItem('olmios_saved_address') || '18510 Ranch View Trail Cir, Houston, TX';
        document.getElementById('verified_status_line').innerText = "Profile Verified: " + name;
        document.getElementById('dispatch_address_select').options[0].text = "📍 " + addr;
    }
    </script>
</body>
</html>"""
    return html.replace('{{HEADER}}', COMMON_HEADER).replace('{{PHOENIX}}', get_phoenix_svg(42, 42)).replace('{{PHOENIX_SMALL}}', get_phoenix_svg(28, 28))

# --- 4. CUSTOMER PROFILE & WALLET ('/profile') ---
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    saved_msg = ""
    if request.method == 'POST':
        saved_msg = '<div class="alert alert-success py-2 text-center small fw-bold mb-3"><i class="fa-solid fa-circle-check me-1"></i> Profile and Wallet specs updated successfully!</div>'

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Profile & Wallet</title>
    {{HEADER}}
    <style>
        body { background-color: #0b1329; color: white; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .form-label { font-weight: 800; color: #334155 !important; font-size: 0.78rem; letter-spacing: 0.5px; text-transform: uppercase; }
        .section-header { font-weight: 800; color: #0284c7; font-size: 0.92rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 12px; margin-top: 18px; display: flex; justify-content: space-between; align-items: center; }
        .btn-amber { background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 800; }
        .add-tab-btn { font-size: 0.75rem; padding: 2px 10px; border-radius: 20px; font-weight: 700; }
        .add-on-box { display: none; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px; margin-bottom: 12px; }
        .card-box { border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; background: #f8fafc; margin-bottom: 10px; }
        .uppercase-input { text-transform: uppercase !important; }
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <h5 class="fw-bold text-dark mb-0"><i class="fa-solid fa-id-card me-1 text-primary"></i> Customer Profile & Wallet</h5>
            <a href="/customer_home" title="Home">{{PHOENIX}}</a>
        </div>

        {{SAVED_MSG}}

        <form method="POST" id="profile_main_form" onsubmit="saveProfileToLocal(event)">
            <div class="mb-3 text-center">
                <img id="profile_avatar_preview" src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" style="width: 85px; height: 85px; object-fit: cover; border-radius: 50%; border: 3px solid #3b82f6;" class="mb-2">
                <div>
                    <label class="btn btn-sm btn-outline-primary fw-bold rounded-3">
                        <i class="fa-solid fa-camera me-1"></i> Upload Profile Picture
                        <input type="file" accept="image/*" capture="user" style="display: none;" onchange="previewProfilePic(event)">
                    </label>
                </div>
            </div>

            <!-- SECTION 1: Personal Info -->
            <div class="section-header">
                <span><i class="fa-solid fa-user me-1"></i> 1. Basic Personal Information & Residence</span>
            </div>
            
            <div class="row g-2 mb-2">
                <div class="col-6">
                    <label class="form-label">FIRST NAME</label>
                    <input type="text" id="prof_fname" class="form-control rounded-3" placeholder="Enter first name">
                </div>
                <div class="col-6">
                    <label class="form-label">LAST NAME</label>
                    <input type="text" id="prof_lname" class="form-control rounded-3" placeholder="Enter last name">
                </div>
            </div>
            
            <div class="mb-2">
                <label class="form-label">PHONE NUMBER</label>
                <input type="text" id="prof_phone" class="form-control rounded-3" placeholder="Enter phone number">
            </div>

            <div class="mb-2">
                <label class="form-label">EMAIL ADDRESS</label>
                <input type="email" id="prof_email" class="form-control rounded-3" placeholder="Enter email address">
            </div>

            <div class="mb-3">
                <label class="form-label">PRIMARY RESIDENCE STREET ADDRESS</label>
                <input type="text" id="primary_street_addr" class="form-control rounded-3" placeholder="Enter street address">
            </div>

            <!-- SECTION 2: Business & Commercial Information -->
            <div class="section-header">
                <span><i class="fa-solid fa-briefcase me-1"></i> 2. Business & Commercial Information</span>
                <button type="button" class="btn btn-outline-primary add-tab-btn" onclick="toggleAddBox('add_biz_box')"><i class="fa-solid fa-plus me-1"></i> Add-On</button>
            </div>

            <div class="mb-2">
                <label class="form-label">DRIVER'S LICENSE / STATE ID # <span class="text-muted fw-normal">(OPTIONAL)</span></label>
                <input type="text" id="prof_dl" class="form-control rounded-3 uppercase-input" placeholder="Enter Driver's License #" oninput="this.value = this.value.toUpperCase()">
            </div>
            
            <div class="mb-2">
                <label class="form-label">BUSINESS / COMPANY NAME</label>
                <input type="text" id="prof_company" class="form-control rounded-3" placeholder="Enter company name">
            </div>
            <div class="row g-2 mb-3">
                <div class="col-6">
                    <label class="form-label">TAX ID / EIN #</label>
                    <input type="text" id="prof_taxid" class="form-control rounded-3 uppercase-input" placeholder="XX-XXXXXXX" oninput="this.value = this.value.toUpperCase()">
                </div>
                <div class="col-6">
                    <label class="form-label">ACCOUNTS PAYABLE EMAIL</label>
                    <input type="email" id="prof_ap_email" class="form-control rounded-3" placeholder="ap@company.com">
                </div>
            </div>

            <div id="add_biz_box" class="add-on-box">
                <h6 class="fw-bold text-primary mb-2"><i class="fa-solid fa-building-circle-add me-1"></i> Add Commercial / Business Unit Specs</h6>
                <div class="mb-2">
                    <label class="form-label">COMMERCIAL SYSTEM TYPE</label>
                    <select class="form-select rounded-3">
                        <option value="">Select Equipment Category...</option>
                        <option>Gas System</option>
                        <option>Electric System</option>
                    </select>
                </div>
                <div class="mb-2">
                    <label class="form-label">VOLTAGE SPECIFICATION</label>
                    <select class="form-select rounded-3">
                        <option value="">Select Voltage...</option>
                        <option>230/60/1</option>
                        <option>230/60/3</option>
                        <option>460/60/3</option>
                    </select>
                </div>
                <div class="mb-2">
                    <label class="form-label">SYSTEM TYPE</label>
                    <select class="form-select rounded-3" onchange="toggleCommConfig(this.value)">
                        <option value="">Select Configuration...</option>
                        <option value="rtu">Rooftop Unit (Under 25 Tons)</option>
                        <option value="split">Split System (Under 25 Tons)</option>
                    </select>
                </div>

                <div id="rtu_fields" style="display:none;">
                    <div class="row g-2 mb-2">
                        <div class="col-6"><label class="form-label">RTU MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                        <div class="col-6"><label class="form-label">RTU SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                    </div>
                </div>

                <div id="split_fields" style="display:none;">
                    <div class="row g-2 mb-2">
                        <div class="col-6"><label class="form-label">CONDENSER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                        <div class="col-6"><label class="form-label">CONDENSER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                    </div>
                    <div class="row g-2 mb-2">
                        <div class="col-6"><label class="form-label">AIR HANDLER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                        <div class="col-6"><label class="form-label">AIR HANDLER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                    </div>
                    <div class="row g-2 mb-2">
                        <div class="col-6"><label class="form-label">HEAT KIT MODEL # <span class="text-muted fw-normal">(OPTIONAL)</span></label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                        <div class="col-6"><label class="form-label">HEAT KIT SERIAL # <span class="text-muted fw-normal">(OPTIONAL)</span></label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                    </div>
                </div>

                <button type="button" class="btn btn-sm btn-success fw-bold w-100 rounded-3 mt-2" onclick="toggleAddBox('add_biz_box')">Save Commercial Specs</button>
            </div>

            <!-- SECTION 3: HVAC System Specs -->
            <div class="section-header">
                <span><i class="fa-solid fa-sliders me-1"></i> 3. HVAC System Equipment & Data Plate Specs</span>
                <div class="d-flex gap-1">
                    <button type="button" class="btn btn-outline-secondary add-tab-btn" onclick="toggleAddBox('add_acc_box')"><i class="fa-solid fa-plus me-1"></i> Add Accessory</button>
                    <button type="button" class="btn btn-outline-primary add-tab-btn" onclick="toggleAddBox('add_hvac_box')"><i class="fa-solid fa-plus me-1"></i> Add-On</button>
                </div>
            </div>
            
            <div class="mb-3">
                <label class="form-label">SYSTEM HEATING TYPE</label>
                <select class="form-select rounded-3 fw-bold text-primary" id="main_heating_type_select" onchange="renderDynamicHvacFields(this.value, 'dynamic_hvac_container')">
                    <option value="">Select System Type...</option>
                    <option value="gas_sys">Gas System</option>
                    <option value="elec_sys">Electric System</option>
                    <option value="gas_hp">Gas Heat Pump System</option>
                    <option value="elec_hp">Electric Heat Pump System</option>
                    <option value="res_pkg">Residential Package Unit</option>
                    <option value="comm_pkg">Commercial Package Unit</option>
                    <option value="comm_split">Commercial Split System</option>
                    <option value="mini_single">Mini Splits - Single Zone</option>
                    <option value="mini_multi">Mini Splits - Multi-Zone</option>
                    <option value="comm_mini_single">Commercial Mini Splits - Single Zone</option>
                    <option value="comm_mini_multi">Commercial Mini Splits - Multi-Zone</option>
                </select>
            </div>

            <!-- DYNAMIC HVAC CONTAINER -->
            <div id="dynamic_hvac_container"></div>

            <div class="mb-3">
                <label class="form-label"><i class="fa-solid fa-image me-1 text-primary"></i> UNIT RATING PLATE PHOTO URL / UPLOAD <span class="text-muted fw-normal">(OPTIONAL)</span></label>
                <input type="text" id="prof_tag_url" class="form-control rounded-3" placeholder="Upload or paste image URL of equipment tag">
            </div>

            <!-- ACCESSORY ADD-ON BOX (WITH TOP-RIGHT DELETE BUTTON) -->
            <div id="add_acc_box" class="add-on-box">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="fw-bold text-primary mb-0"><i class="fa-solid fa-sliders me-1"></i> Add Additional Accessory</h6>
                    <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2 fw-bold" onclick="toggleAddBox('add_acc_box')"><i class="fa-solid fa-trash me-1"></i> Delete</button>
                </div>
                <div class="mb-2">
                    <label class="form-label">ACCESSORY TYPE / NAME</label>
                    <input type="text" class="form-control rounded-3" placeholder="e.g., Smart Thermostat, Surge Protector, Dehumidifier">
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <button type="button" class="btn btn-sm btn-success fw-bold w-100 rounded-3 mt-1" onclick="toggleAddBox('add_acc_box')">Save Accessory</button>
            </div>

            <!-- ADDITIONAL HVAC TAG BOX (WITH TOP-RIGHT DELETE BUTTON & SYSTEM HEATING TYPE DROPDOWN) -->
            <div id="add_hvac_box" class="add-on-box">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="fw-bold text-primary mb-0"><i class="fa-solid fa-circle-plus me-1"></i> Add Additional HVAC System Tag</h6>
                    <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2 fw-bold" onclick="toggleAddBox('add_hvac_box')"><i class="fa-solid fa-trash me-1"></i> Delete</button>
                </div>
                <div class="mb-2">
                    <label class="form-label">SYSTEM HEATING TYPE</label>
                    <select class="form-select rounded-3 fw-bold text-primary" onchange="renderDynamicHvacFields(this.value, 'addon_hvac_container')">
                        <option value="">Select System Type...</option>
                        <option value="gas_sys">Gas System</option>
                        <option value="elec_sys">Electric System</option>
                        <option value="gas_hp">Gas Heat Pump System</option>
                        <option value="elec_hp">Electric Heat Pump System</option>
                        <option value="res_pkg">Residential Package Unit</option>
                        <option value="comm_pkg">Commercial Package Unit</option>
                        <option value="comm_split">Commercial Split System</option>
                        <option value="mini_single">Mini Splits - Single Zone</option>
                        <option value="mini_multi">Mini Splits - Multi-Zone</option>
                        <option value="comm_mini_single">Commercial Mini Splits - Single Zone</option>
                        <option value="comm_mini_multi">Commercial Mini Splits - Multi-Zone</option>
                    </select>
                </div>
                <div id="addon_hvac_container" class="mb-2"></div>
                <button type="button" class="btn btn-sm btn-success fw-bold w-100 rounded-3 mt-1" onclick="toggleAddBox('add_hvac_box')">Save Additional HVAC Specs</button>
            </div>

            <!-- SECTION 4: Saved Payment Cards & Wallet -->
            <div class="section-header">
                <span><i class="fa-solid fa-credit-card me-1"></i> 4. Saved Payment Cards & Wallet</span>
                <button type="button" class="btn btn-outline-primary add-tab-btn" onclick="toggleAddBox('add_card_box')"><i class="fa-solid fa-plus me-1"></i> Add Additional Card</button>
            </div>

            <div id="card_list_container">
                <div class="card-box" id="card_1004">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="d-flex align-items-center gap-2">
                            <span class="fw-bold text-dark"><i class="fa-brands fa-cc-visa text-primary me-1 fs-5"></i> Visa ending in 1004</span>
                            <span class="badge bg-primary me-1">Primary</span>
                        </div>
                        <div class="d-flex align-items-center gap-1">
                            <button type="button" class="btn btn-sm btn-success py-0 px-2 fw-bold" onclick="alert('Card Saved Successfully!')"><i class="fa-solid fa-floppy-disk me-1"></i> Save</button>
                            <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2 fw-bold" onclick="deleteCard('card_1004')"><i class="fa-solid fa-trash me-1"></i> Delete</button>
                        </div>
                    </div>
                    <div class="row g-2 mt-1">
                        <div class="col-12"><input type="text" class="form-control rounded-3 mb-1" placeholder="Cardholder Name" value="John Doe"></div>
                        <div class="col-8"><input type="text" class="form-control rounded-3" placeholder="Card Number (XXXX-XXXX-XXXX-1004)" value="**** **** **** 1004"></div>
                        <div class="col-4"><input type="text" class="form-control rounded-3" placeholder="MM/YY" value="12/28"></div>
                    </div>
                </div>
            </div>

            <div id="add_card_box" class="add-on-box">
                <h6 class="fw-bold text-primary mb-2"><i class="fa-solid fa-credit-card me-1"></i> Add New Payment Card</h6>
                <input type="text" id="new_card_name" class="form-control rounded-3 mb-2" placeholder="Cardholder Name">
                <div class="row g-2 mb-2">
                    <div class="col-8"><input type="text" id="new_card_num" class="form-control rounded-3" placeholder="Card Number"></div>
                    <div class="col-4"><input type="text" class="form-control rounded-3" placeholder="MM/YY"></div>
                </div>
                <button type="button" class="btn btn-sm btn-success fw-bold w-100 rounded-3" onclick="addNewCard()">Save Card to Wallet</button>
            </div>

            <!-- SECTION 5: Additional Property Locations -->
            <div class="section-header">
                <span><i class="fa-solid fa-location-dot me-1"></i> 5. Manage Additional Property Locations</span>
                <button type="button" class="btn btn-outline-primary add-tab-btn" onclick="toggleAddBox('add_location_box')"><i class="fa-solid fa-plus me-1"></i> Add Location Specs</button>
            </div>

            <div class="mb-3">
                <select class="form-select rounded-3 mb-2">
                    <option value="">Select Property Address...</option>
                </select>
            </div>

            <div id="add_location_box" class="add-on-box">
                <h6 class="fw-bold text-primary mb-2"><i class="fa-solid fa-house-chimney-medical me-1"></i> Add Additional Location Specs</h6>
                <div class="mb-2">
                    <label class="form-label">PROPERTY ADDRESS</label>
                    <input type="text" class="form-control rounded-3" placeholder="Street Address, City, State">
                </div>
                <div class="mb-2">
                    <label class="form-label">SYSTEM TYPE</label>
                    <select class="form-select rounded-3">
                        <option value="">Select Gas or Electric...</option>
                        <option>Gas System</option>
                        <option>Electric System</option>
                    </select>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <button type="button" class="btn btn-sm btn-success fw-bold w-100 rounded-3" onclick="toggleAddBox('add_location_box')">Save Location Specs</button>
            </div>

            <div class="row g-2 mb-3 mt-4">
                <div class="col-6">
                    <button type="submit" class="btn btn-amber w-100 py-2.5 rounded-3 fw-bold shadow-sm">
                        <i class="fa-solid fa-floppy-disk me-1"></i> Save Profile
                    </button>
                </div>
                <div class="col-6">
                    <button type="button" class="btn btn-outline-danger w-100 py-2.5 rounded-3 fw-bold" onclick="if(confirm('Are you sure you want to delete this profile?')) window.location.href='/';">
                        <i class="fa-solid fa-trash me-1"></i> Delete Profile
                    </button>
                </div>
            </div>
        </form>

        <a href="/customer_home" class="btn btn-secondary w-100 py-2 rounded-3 fw-bold"><i class="fa-solid fa-house me-1"></i> Home Page</a>
    </div>

    <script>
    var multiZoneCount = 3;

    function previewProfilePic(e) {
        if(e.target.files && e.target.files[0]) {
            let reader = new FileReader();
            reader.onload = function(evt) { 
                document.getElementById('profile_avatar_preview').src = evt.target.result;
                localStorage.setItem('olmios_profile_pic', evt.target.result);
            }
            reader.readAsDataURL(e.target.files[0]);
        }
    }

    function toggleAddBox(boxId) {
        let box = document.getElementById(boxId);
        box.style.display = (box.style.display === 'block') ? 'none' : 'block';
    }

    function toggleCommConfig(val) {
        document.getElementById('rtu_fields').style.display = (val === 'rtu') ? 'block' : 'none';
        document.getElementById('split_fields').style.display = (val === 'split') ? 'block' : 'none';
    }

    function addMoreIndoorUnit(targetContainerId) {
        multiZoneCount++;
        let container = document.getElementById(targetContainerId + '_indoor_units');
        if(container) {
            let unitHtml = `
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">INDOOR UNIT #${multiZoneCount} MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">INDOOR UNIT #${multiZoneCount} SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>`;
            container.insertAdjacentHTML('beforeend', unitHtml);
        }
    }

    function renderDynamicHvacFields(systemType, targetId) {
        let container = document.getElementById(targetId);
        if(!container) return;
        let html = '';

        if (systemType === 'gas_sys') {
            html = `
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">CONDENSER MODEL #</label><input type="text" id="m_cond_mod" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">CONDENSER SERIAL #</label><input type="text" id="m_cond_ser" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">EVAPORATOR COIL MODEL #</label><input type="text" id="m_coil_mod" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">COIL SERIAL #</label><input type="text" id="m_coil_ser" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">FURNACE MODEL #</label><input type="text" id="m_furn_mod" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">FURNACE SERIAL #</label><input type="text" id="m_furn_ser" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>`;
        } else if (systemType === 'elec_sys') {
            html = `
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">CONDENSER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">CONDENSER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">AIR HANDLER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">AIR HANDLER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">HEAT KIT MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">HEAT KIT SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>`;
        } else if (systemType === 'gas_hp') {
            html = `
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">HP CONDENSER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">HP CONDENSER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">EVAPORATOR COIL MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">COIL SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">FURNACE MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">FURNACE SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>`;
        } else if (systemType === 'elec_hp') {
            html = `
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">HP CONDENSER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">HP CONDENSER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">AIR HANDLER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">AIR HANDLER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">HEAT KIT MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">HEAT KIT SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>`;
        } else if (systemType === 'res_pkg' || systemType === 'comm_pkg') {
            html = `
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">UNIT MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">UNIT SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>`;
        } else if (systemType === 'comm_split') {
            html = `
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">COMMERCIAL CONDENSER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">COMMERCIAL CONDENSER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">AIR HANDLER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">AIR HANDLER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">HEAT KIT MODEL # <span class="text-muted fw-normal">(OPTIONAL)</span></label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">HEAT KIT SERIAL # <span class="text-muted fw-normal">(OPTIONAL)</span></label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>`;
        } else if (systemType === 'mini_single' || systemType === 'comm_mini_single') {
            html = `
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">OUTDOOR UNIT MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">OUTDOOR UNIT SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">INDOOR UNIT MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">INDOOR UNIT SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>`;
        } else if (systemType === 'mini_multi' || systemType === 'comm_mini_multi') {
            multiZoneCount = 3;
            html = `
                <div class="row g-2 mb-2">
                    <div class="col-6"><label class="form-label">OUTDOOR CONDENSER MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                    <div class="col-6"><label class="form-label">OUTDOOR CONDENSER SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                </div>
                <div id="${targetId}_indoor_units">
                    <div class="row g-2 mb-2">
                        <div class="col-6"><label class="form-label">INDOOR UNIT #1 MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                        <div class="col-6"><label class="form-label">INDOOR UNIT #1 SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                    </div>
                    <div class="row g-2 mb-2">
                        <div class="col-6"><label class="form-label">INDOOR UNIT #2 MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                        <div class="col-6"><label class="form-label">INDOOR UNIT #2 SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                    </div>
                    <div class="row g-2 mb-2">
                        <div class="col-6"><label class="form-label">INDOOR UNIT #3 MODEL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Model #" oninput="this.value = this.value.toUpperCase()"></div>
                        <div class="col-6"><label class="form-label">INDOOR UNIT #3 SERIAL #</label><input type="text" class="form-control rounded-3 uppercase-input" placeholder="Serial #" oninput="this.value = this.value.toUpperCase()"></div>
                    </div>
                </div>
                <button type="button" class="btn btn-sm btn-outline-primary fw-bold w-100 mb-2 rounded-3" onclick="addMoreIndoorUnit('${targetId}')"><i class="fa-solid fa-plus me-1"></i> Add Indoor Unit</button>`;
        }

        container.innerHTML = html;
        restoreFormValues();
    }

    function deleteCard(cardId) {
        let cardEl = document.getElementById(cardId);
        if(cardEl && confirm('Are you sure you want to delete this payment card?')) {
            cardEl.remove();
        }
    }

    function addNewCard() {
        let name = document.getElementById('new_card_name').value || 'New Card';
        let num = document.getElementById('new_card_num').value || '4000';
        let last4 = num.slice(-4) || '4000';
        let newId = 'card_' + Date.now();

        let newCardHtml = `
            <div class="card-box" id="${newId}">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="d-flex align-items-center gap-2">
                        <span class="fw-bold text-dark"><i class="fa-solid fa-credit-card text-success me-1 fs-5"></i> Card ending in ${last4}</span>
                    </div>
                    <div class="d-flex align-items-center gap-1">
                        <button type="button" class="btn btn-sm btn-success py-0 px-2 fw-bold" onclick="alert('Card Saved Successfully!')"><i class="fa-solid fa-floppy-disk me-1"></i> Save</button>
                        <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2 fw-bold" onclick="deleteCard('${newId}')"><i class="fa-solid fa-trash me-1"></i> Delete</button>
                    </div>
                </div>
                <div class="row g-2 mt-1">
                    <div class="col-12"><input type="text" class="form-control rounded-3 mb-1" value="${name}"></div>
                    <div class="col-8"><input type="text" class="form-control rounded-3" value="**** **** **** ${last4}"></div>
                    <div class="col-4"><input type="text" class="form-control rounded-3" placeholder="MM/YY"></div>
                </div>
            </div>`;
        document.getElementById('card_list_container').insertAdjacentHTML('beforeend', newCardHtml);
        toggleAddBox('add_card_box');
    }

    function saveProfileToLocal(e) {
        let fname = document.getElementById('prof_fname').value.trim();
        let lname = document.getElementById('prof_lname').value.trim();
        let phone = document.getElementById('prof_phone').value.trim();
        let email = document.getElementById('prof_email').value.trim();
        let addr = document.getElementById('primary_street_addr').value.trim();
        let dl = document.getElementById('prof_dl').value.trim();
        let comp = document.getElementById('prof_company').value.trim();
        let tax = document.getElementById('prof_taxid').value.trim();
        let ap = document.getElementById('prof_ap_email').value.trim();
        let tag = document.getElementById('prof_tag_url').value.trim();

        if(fname || lname) localStorage.setItem('olmios_fullname', (fname + ' ' + lname).trim());
        if(phone) localStorage.setItem('olmios_phone', phone);
        if(email) localStorage.setItem('olmios_email', email);
        if(addr) localStorage.setItem('olmios_saved_address', addr);
        if(dl) localStorage.setItem('olmios_dl', dl);
        if(comp) localStorage.setItem('olmios_company', comp);
        if(tax) localStorage.setItem('olmios_taxid', tax);
        if(ap) localStorage.setItem('olmios_ap_email', ap);
        if(tag) localStorage.setItem('olmios_tag_url', tag);

        let hvacType = document.getElementById('main_heating_type_select').value;
        if(hvacType) localStorage.setItem('olmios_hvac_type', hvacType);

        if(document.getElementById('m_cond_mod')) localStorage.setItem('olmios_cond_mod', document.getElementById('m_cond_mod').value);
        if(document.getElementById('m_cond_ser')) localStorage.setItem('olmios_cond_ser', document.getElementById('m_cond_ser').value);
        if(document.getElementById('m_coil_mod')) localStorage.setItem('olmios_coil_mod', document.getElementById('m_coil_mod').value);
        if(document.getElementById('m_coil_ser')) localStorage.setItem('olmios_coil_ser', document.getElementById('m_coil_ser').value);
        if(document.getElementById('m_furn_mod')) localStorage.setItem('olmios_furn_mod', document.getElementById('m_furn_mod').value);
        if(document.getElementById('m_furn_ser')) localStorage.setItem('olmios_furn_ser', document.getElementById('m_furn_ser').value);
    }

    function restoreFormValues() {
        if(document.getElementById('m_cond_mod') && localStorage.getItem('olmios_cond_mod')) document.getElementById('m_cond_mod').value = localStorage.getItem('olmios_cond_mod');
        if(document.getElementById('m_cond_ser') && localStorage.getItem('olmios_cond_ser')) document.getElementById('m_cond_ser').value = localStorage.getItem('olmios_cond_ser');
        if(document.getElementById('m_coil_mod') && localStorage.getItem('olmios_coil_mod')) document.getElementById('m_coil_mod').value = localStorage.getItem('olmios_coil_mod');
        if(document.getElementById('m_coil_ser') && localStorage.getItem('olmios_coil_ser')) document.getElementById('m_coil_ser').value = localStorage.getItem('olmios_coil_ser');
        if(document.getElementById('m_furn_mod') && localStorage.getItem('olmios_furn_mod')) document.getElementById('m_furn_mod').value = localStorage.getItem('olmios_furn_mod');
        if(document.getElementById('m_furn_ser') && localStorage.getItem('olmios_furn_ser')) document.getElementById('m_furn_ser').value = localStorage.getItem('olmios_furn_ser');
    }

    window.onload = function() {
        let savedName = localStorage.getItem('olmios_fullname') || '';
        let parts = savedName.split(' ');
        if(parts.length > 0) document.getElementById('prof_fname').value = parts[0] || '';
        if(parts.length > 1) document.getElementById('prof_lname').value = parts.slice(1).join(' ') || '';
        
        if(localStorage.getItem('olmios_phone')) document.getElementById('prof_phone').value = localStorage.getItem('olmios_phone');
        if(localStorage.getItem('olmios_email')) document.getElementById('prof_email').value = localStorage.getItem('olmios_email');
        if(localStorage.getItem('olmios_saved_address')) document.getElementById('primary_street_addr').value = localStorage.getItem('olmios_saved_address');
        if(localStorage.getItem('olmios_dl')) document.getElementById('prof_dl').value = localStorage.getItem('olmios_dl');
        if(localStorage.getItem('olmios_company')) document.getElementById('prof_company').value = localStorage.getItem('olmios_company');
        if(localStorage.getItem('olmios_taxid')) document.getElementById('prof_taxid').value = localStorage.getItem('olmios_taxid');
        if(localStorage.getItem('olmios_ap_email')) document.getElementById('prof_ap_email').value = localStorage.getItem('olmios_ap_email');
        if(localStorage.getItem('olmios_tag_url')) document.getElementById('prof_tag_url').value = localStorage.getItem('olmios_tag_url');

        let savedPic = localStorage.getItem('olmios_profile_pic');
        if(savedPic) document.getElementById('profile_avatar_preview').src = savedPic;

        let savedType = localStorage.getItem('olmios_hvac_type') || 'gas_sys';
        document.getElementById('main_heating_type_select').value = savedType;
        renderDynamicHvacFields(savedType, 'dynamic_hvac_container');
    }
    </script>
</body>
</html>"""
    return html.replace('{{HEADER}}', COMMON_HEADER).replace('{{PHOENIX}}', get_phoenix_svg(42, 42)).replace('{{SAVED_MSG}}', saved_msg)

# --- 5. INVOICES & REFUND REQUESTS ('/invoices') ---
@app.route('/invoices')
def invoices():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Invoices</title>
    {{HEADER}}
    <style>
        body { background-color: #0b1329; color: white; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }
        .main-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .form-label { font-weight: 800; color: #475569 !important; font-size: 0.75rem; letter-spacing: 0.5px; text-transform: uppercase; }
        .invoice-card { border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; background: #f8fafc; margin-bottom: 12px; }
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <h5 class="fw-bold text-dark mb-0"><i class="fa-solid fa-receipt me-1 text-primary"></i> Service Invoices</h5>
            <a href="/customer_home" title="Home">{{PHOENIX}}</a>
        </div>

        <div class="bg-light p-3 rounded-3 border mb-3">
            <h6 class="fw-bold text-dark mb-2 small"><i class="fa-solid fa-filter me-1 text-primary"></i> FILTER INVOICES</h6>
            <div class="row g-2">
                <div class="col-6">
                    <label class="form-label">LAST 4 CARD DIGITS</label>
                    <input type="text" id="filter_card" class="form-control form-control-sm rounded-2" placeholder="e.g. 1004" onkeyup="filterInvoices()">
                </div>
                <div class="col-6">
                    <label class="form-label">SERVICE DATE</label>
                    <input type="date" id="filter_date" class="form-control form-control-sm rounded-2" onchange="filterInvoices()">
                </div>
                <div class="col-6">
                    <label class="form-label">PO NUMBER</label>
                    <input type="text" id="filter_po" class="form-control form-control-sm rounded-2" placeholder="PO #" onkeyup="filterInvoices()">
                </div>
                <div class="col-6">
                    <label class="form-label">AMOUNT ($)</label>
                    <input type="text" id="filter_amount" class="form-control form-control-sm rounded-2" placeholder="e.g. 185" onkeyup="filterInvoices()">
                </div>
            </div>
        </div>
        
        <div id="invoice_list">
            <div class="invoice-card" data-card="1004" data-po="88204" data-amount="185.00" data-date="2026-08-01">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="fw-bold text-dark">INV-1002 (Capacitor Replacement)</span>
                    <span class="badge bg-success">Paid</span>
                </div>
                <div class="small text-muted mb-2">Date: 08/01/2026 | Card: **** 1004 | PO: 88204 | Amount: $185.00</div>
                <div class="row g-2">
                    <div class="col-6">
                        <button class="btn btn-outline-danger btn-sm w-100 fw-bold rounded-2" onclick="alert('Refund Request Submitted.')">
                            <i class="fa-solid fa-rotate-left me-1"></i> Request Refund
                        </button>
                    </div>
                    <div class="col-6">
                        <button class="btn btn-outline-primary btn-sm w-100 fw-bold rounded-2" onclick="window.print()">
                            <i class="fa-solid fa-print me-1"></i> Print Invoice
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <a href="/customer_home" class="btn btn-secondary w-100 py-2 rounded-3 fw-bold mt-2"><i class="fa-solid fa-house me-1"></i> Home Page</a>
    </div>

    <script>
    function filterInvoices() {
        let card = document.getElementById('filter_card').value.toLowerCase();
        let po = document.getElementById('filter_po').value.toLowerCase();
        let amount = document.getElementById('filter_amount').value.toLowerCase();
        let date = document.getElementById('filter_date').value;

        document.querySelectorAll('.invoice-card').forEach(cardEl => {
            let cCard = cardEl.getAttribute('data-card').toLowerCase();
            let cPo = cardEl.getAttribute('data-po').toLowerCase();
            let cAmt = cardEl.getAttribute('data-amount').toLowerCase();
            let cDate = cardEl.getAttribute('data-date');

            let match = true;
            if (card && !cCard.includes(card)) match = false;
            if (po && !cPo.includes(po)) match = false;
            if (amount && !cAmt.includes(amount)) match = false;
            if (date && cDate !== date) match = false;

            cardEl.style.display = match ? 'block' : 'none';
        });
    }
    </script>
</body>
</html>"""
    return html.replace('{{HEADER}}', COMMON_HEADER).replace('{{PHOENIX}}', get_phoenix_svg(42, 42))

# --- 6. DOWNLOAD PHOENIX LOGO PAGE ('/download_logo') ---
@app.route('/download_logo')
def download_logo():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Download Phoenix Logo (.JPG)</title>
    {{HEADER}}
    <style>
        body { background-color: #0b1329; color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 20px; }
        .logo-card { background: #ffffff; padding: 40px; border-radius: 24px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); max-width: 480px; width: 100%; color: #0f172a; }
    </style>
</head>
<body>
    <div class="logo-card">
        <h4 class="fw-bold text-dark mb-1">Olmios Phoenix Symbol</h4>
        <p class="text-muted small mb-3">High-Resolution .JPG Format</p>
        
        <div id="svg_container" style="display:none;">
            {{PHOENIX_BIG}}
        </div>

        <div class="p-3 mb-3 border rounded-3 bg-light d-flex justify-content-center align-items-center" style="min-height: 260px;">
            <img id="jpg_preview" style="max-width: 220px; height: auto;" alt="Olmios Phoenix Logo JPG">
        </div>

        <canvas id="jpg_canvas" width="1200" height="1200" style="display:none;"></canvas>

        <button class="btn btn-warning btn-lg w-100 fw-bold rounded-3 shadow-sm mb-2 text-dark" onclick="downloadJPG()">
            <i class="fa-solid fa-file-image me-1"></i> Download .JPG Logo File
        </button>
        <a href="/customer_home" class="btn btn-outline-secondary w-100 fw-bold rounded-3">Return to Dashboard</a>
    </div>

    <script>
    function renderJPG() {
        let svgElement = document.querySelector('#svg_container svg');
        let svgData = new XMLSerializer().serializeToString(svgElement);
        let svgBlob = new Blob([svgData], {type: "image/svg+xml;charset=utf-8"});
        let URLObj = window.URL || window.webkitURL || window;
        let blobURL = URLObj.createObjectURL(svgBlob);
        
        let img = new Image();
        img.onload = function() {
            let canvas = document.getElementById('jpg_canvas');
            let ctx = canvas.getContext('2d');
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            let jpgDataUrl = canvas.toDataURL('image/jpeg', 0.95);
            document.getElementById('jpg_preview').src = jpgDataUrl;
        };
        img.src = blobURL;
    }

    function downloadJPG() {
        let canvas = document.getElementById('jpg_canvas');
        let jpgUrl = canvas.toDataURL('image/jpeg', 0.95);
        let downloadLink = document.createElement("a");
        downloadLink.href = jpgUrl;
        downloadLink.download = "olmios_phoenix_logo.jpg";
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    }

    window.onload = renderJPG;
    </script>
</body>
</html>"""
    return html.replace('{{HEADER}}', COMMON_HEADER).replace('{{PHOENIX_BIG}}', get_phoenix_svg(600, 600))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
