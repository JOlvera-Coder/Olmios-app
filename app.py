import os
import json
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session

app = Flask(__name__)
app.secret_key = 'olmios_secure_customer_session_key'

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            customer_name TEXT,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            city TEXT,
            zip_code TEXT,
            urgency TEXT,
            equipment TEXT NOT NULL,
            model_number TEXT,
            serial_number TEXT,
            issue_description TEXT NOT NULL,
            assigned_tech TEXT DEFAULT 'Unassigned',
            est_value REAL DEFAULT 150.00,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Pending'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sms_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_type TEXT NOT NULL,
            sender_name TEXT NOT NULL,
            sender_phone TEXT NOT NULL,
            message_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_new INTEGER DEFAULT 1
        )
    """)

    text_cols = [
        "model_number", "serial_number", "email", "first_name",
        "last_name", "address", "city", "zip_code", "urgency", "assigned_tech"
    ]
    for col in text_cols:
        try:
            cursor.execute(f"ALTER TABLE service_requests ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass

    try:
        cursor.execute("ALTER TABLE service_requests ADD COLUMN est_value REAL DEFAULT 150.00")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE service_requests ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT COUNT(*) FROM sms_messages")
    if cursor.fetchone()[0] == 0:
        sample_messages = [
            ("Customer", "John Doe", "8323884957", "Hi, what time will the tech arrive today for #5?"),
            ("Customer", "Ian Olvera", "3468043947", "I unlocked the side gate for the technician."),
            ("Tech", "Tech A (Lead)", "8325550199", "Accepted job #4, heading to site now."),
            ("Tech", "Tech B", "8325550144", "Need a replacement capacitor for unit #2.")
        ]
        cursor.executemany("""
            INSERT INTO sms_messages (sender_type, sender_name, sender_phone, message_text, is_new)
            VALUES (?, ?, ?, ?, 1)
        """, sample_messages)

    conn.commit()
    conn.close()

init_db()

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
    <path d="M48 36 C38 30 26 28 16 34 C24 38 32 40 40 46 C28 46 18 50 14 58 C22 58 32 56 42 58 C32 62 24 68 46 64 Z" fill="url(#goldFeathers)" />
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

COMMON_ADMIN_CSS = """
    body {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        margin: 0;
        padding: 20px;
        min-height: 100vh;
        box-sizing: border-box;
    }
    .panel {
        background: #ffffff;
        color: #1e293b;
        border-radius: 16px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        padding: 24px;
    }
    .brand-logo {
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 5px;
        color: #0f172a;
        text-transform: uppercase;
    }
    .btn-admin {
        display: inline-block;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 700;
        font-size: 13px;
        border: none;
        cursor: pointer;
        text-align: center;
    }
    .btn-primary-admin { background-color: #2563eb; color: #ffffff; }
    .btn-primary-admin:hover { background-color: #1d4ed8; color: white; }
    .btn-accent-admin { background-color: #d97706; color: #ffffff; }
    .btn-accent-admin:hover { background-color: #b45309; color: white; }
    
    .home-phoenix-btn {
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px;
        border-radius: 10px;
        transition: transform 0.2s ease;
    }
    .home-phoenix-btn:hover { transform: scale(1.08); }
"""

def get_lat_lng(address_str):
    if not address_str or len(address_str.strip()) < 3:
        return 29.7604, -95.3698
    try:
        url = "https://nominatim.openstreetmap.org/search?format=json&q=" + urllib.parse.quote(address_str)
        req = urllib.request.Request(url, headers={"User-Agent": "OlmiosDispatchApp/1.0"})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return 29.7604, -95.3698

def calculate_age(created_at_str):
    if not created_at_str:
        return "Just now", False
    try:
        created_time = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        diff = now - created_time
        minutes = int(diff.total_seconds() / 60)
        if minutes < 1:
            return "Just now", False
        elif minutes < 60:
            return f"{minutes}m ago", minutes > 30
        else:
            hours = int(minutes / 60)
            return f"{hours}h ago", True
    except Exception:
        return "Recent", False

# ==========================================
# CUSTOMER APP ROUTES (PRESERVED INTACT)
# ==========================================
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

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
        .btn-service-type { border: 2px solid #3b82f6; background: #ffffff; color: #1e3a8a; font-weight: 800; border-radius: 14px; padding: 14px 10px; font-size: 0.95rem; width: 100%; transition: all 0.2s; cursor: pointer; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15); }
        .btn-service-type:hover { background: #f0f7ff; border-color: #1d4ed8; }
        .btn-category { border: 1.5px solid #cbd5e1; background: #f8fafc; color: #475569; font-weight: 700; border-radius: 12px; padding: 12px 6px; font-size: 0.85rem; width: 100%; transition: all 0.2s; cursor: pointer; }
        .btn-category.active { background: #f0f9ff; border-color: #0284c7; color: #0284c7; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2); }
        .ai-followup-box { background: #e0f2fe; border: 1.5px solid #0284c7; border-radius: 14px; padding: 14px; margin-top: 10px; display: none; }
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

        <!-- INITIAL SERVICE MODE CHOICE: SYSTEM REPAIR VS SYSTEM REPLACEMENT -->
        <div id="service_mode_container" class="mb-3">
            <label class="form-label text-center d-block text-primary fw-bold fs-6 mb-2"><i class="fa-solid fa-list-check me-1"></i> SELECT SERVICE NEED</label>
            <div class="row g-2">
                <div class="col-6">
                    <button type="button" class="btn-service-type" onclick="chooseServiceMode('repair')">
                        <i class="fa-solid fa-screwdriver-wrench text-warning mb-1 d-block fs-4"></i> System Repair
                    </button>
                </div>
                <div class="col-6">
                    <button type="button" class="btn-service-type" onclick="chooseServiceMode('replacement')">
                        <i class="fa-solid fa-arrows-rotate text-success mb-1 d-block fs-4"></i> System Replacement
                    </button>
                </div>
            </div>
        </div>

        <!-- REPAIR OPTION TABS: COOLING, HEATING, THERMOSTAT -->
        <div id="repair_tabs_container" class="row g-2 mb-3" style="display: none;">
            <div class="col-4">
                <button type="button" class="btn-category active" id="cat_cooling" onclick="selectRepairCategory('cooling')">
                    <i class="fa-solid fa-snowflake text-info mb-1 d-block fs-5"></i> Cooling
                </button>
            </div>
            <div class="col-4">
                <button type="button" class="btn-category" id="cat_heating" onclick="selectRepairCategory('heating')">
                    <i class="fa-solid fa-fire text-danger mb-1 d-block fs-5"></i> Heating
                </button>
            </div>
            <div class="col-4">
                <button type="button" class="btn-category" id="cat_thermostat" onclick="selectRepairCategory('thermostat')">
                    <i class="fa-solid fa-sliders text-primary mb-1 d-block fs-5"></i> Thermostat
                </button>
            </div>
        </div>

        <!-- REPLACEMENT EQUIPMENT TABS -->
        <div id="replacement_tabs_container" class="mb-3" style="display: none;">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <label class="form-label small text-muted mb-0">SELECT SAVED EQUIPMENT TO REPLACE:</label>
                <button type="button" class="btn btn-sm btn-outline-secondary py-0 px-2 fw-bold" onclick="resetToServiceMode()"><i class="fa-solid fa-arrow-left me-1"></i> Back</button>
            </div>
            <div id="dynamic_replacement_tabs" class="d-flex flex-column gap-2"></div>
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

        <!-- SERVICE URGENCY -->
        <div class="mb-3">
            <label class="form-label">SERVICE URGENCY</label>
            <select class="form-select rounded-3 fw-bold" id="urgency_select" onchange="toggleUrgencySchedule(this.value)">
                <option value="now" selected>⚡ Dispatch Now</option>
                <option value="other">📅 Other (Select Date & Time)</option>
            </select>
        </div>

        <div id="urgency_schedule_box" class="row g-2 mb-3 p-2 bg-light border rounded-3" style="display: none;">
            <div class="col-6">
                <label class="form-label small mb-1">SELECT DATE</label>
                <input type="date" id="scheduled_date" class="form-control rounded-2">
            </div>
            <div class="col-6">
                <label class="form-label small mb-1">SELECT TIME</label>
                <input type="time" id="scheduled_time" class="form-control rounded-2">
            </div>
        </div>

        <div class="mb-3">
            <label class="form-label">EQUIPMENT TYPE (INCLUDES RESIDENTIAL & COMMERCIAL)</label>
            <select class="form-select rounded-3" id="equipment_type_select">
                <option value="">Select HVAC Equipment...</option>
                <option value="Cooling Issue">Cooling Issue</option>
                <option value="Heating Issue">Heating Issue</option>
                <option value="Control / Thermostat Issue">Control / Thermostat Issue</option>
                <option value="A/C Condenser">A/C Condenser</option>
                <option value="Furnace / Air Handler">Furnace / Air Handler</option>
                <option value="Complete Split System">Complete Split System</option>
                <option value="Commercial RTU">Commercial RTU</option>
            </select>
        </div>

        <div class="p-3 mb-3 rounded-4" style="background: #f0f7ff; border: 1.5px solid #3b82f6;">
            <div class="d-flex align-items-center gap-2 mb-2">
                {{PHOENIX_SMALL}}
                <h6 class="fw-bold mb-0 text-primary">OLMIOS Diagnostic Chat Assistant</h6>
            </div>
            <p class="small text-muted mb-2">Tell us what's going on! Mention symptoms, specific defective part notes, or paste image URLs:</p>
            
            <textarea id="chat_assistant_input" class="form-control mb-2" rows="3" placeholder="e.g., Coil leaking water near furnace..."></textarea>
            
            <button type="button" class="btn btn-primary w-100 py-2 fw-bold rounded-3 shadow-sm" onclick="autoFillDescription()">
                <i class="fa-solid fa-wand-magic-sparkles me-1"></i> AUTO-FILL ISSUE DESCRIPTION
            </button>

            <!-- INTERACTIVE AI FOLLOW-UP PROMPT -->
            <div id="ai_followup_box" class="ai-followup-box">
                <div class="d-flex align-items-center gap-2 mb-2 pb-1 border-bottom border-info-subtle">
                    {{PHOENIX_SMALL}}
                    <span class="fw-bold text-primary small"><i class="fa-solid fa-robot me-1"></i> Olmios AI Diagnostic Follow-Up:</span>
                </div>
                <p class="small text-dark fw-semibold mb-2" id="ai_followup_question">Is the leak on the outdoor condenser coil or the indoor evaporator coil/air handler?</p>
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-sm btn-outline-primary fw-bold w-50" onclick="answerAiLeak('Outdoor Condenser Coil')">Outdoor Condenser Coil</button>
                    <button type="button" class="btn btn-sm btn-primary fw-bold w-50" onclick="answerAiLeak('Indoor Evaporator Coil')">Indoor Evaporator Coil</button>
                </div>
            </div>
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
    var currentCoilSelection = "";
    var currentServiceMode = "";
    var selectedReplacementTabs = [];

    function chooseServiceMode(mode) {
        currentServiceMode = mode;
        document.getElementById('service_mode_container').style.display = 'none';

        if(mode === 'repair') {
            document.getElementById('repair_tabs_container').style.display = 'flex';
            document.getElementById('replacement_tabs_container').style.display = 'none';
        } else if(mode === 'replacement') {
            document.getElementById('repair_tabs_container').style.display = 'none';
            document.getElementById('replacement_tabs_container').style.display = 'block';
            loadProfileEquipmentTabs();
        }
    }

    function resetToServiceMode() {
        document.getElementById('service_mode_container').style.display = 'block';
        document.getElementById('repair_tabs_container').style.display = 'none';
        document.getElementById('replacement_tabs_container').style.display = 'none';
        selectedReplacementTabs = [];
    }

    function toggleUrgencySchedule(val) {
        let scheduleBox = document.getElementById('urgency_schedule_box');
        scheduleBox.style.display = (val === 'other') ? 'flex' : 'none';
    }

    function selectRepairCategory(catName) {
        document.querySelectorAll('#repair_tabs_container .btn-category').forEach(b => b.classList.remove('active'));
        let targetBtn = document.getElementById('cat_' + catName);
        if(targetBtn) targetBtn.classList.add('active');

        let eqSelect = document.getElementById('equipment_type_select');
        if(catName === 'cooling') eqSelect.value = 'Cooling Issue';
        else if(catName === 'heating') eqSelect.value = 'Heating Issue';
        else if(catName === 'thermostat') eqSelect.value = 'Control / Thermostat Issue';

        autoFillDescription();
    }

    function loadProfileEquipmentTabs() {
        let savedType = localStorage.getItem('olmios_hvac_type') || 'gas_sys';
        let condModel = localStorage.getItem('olmios_cond_mod') || '5TTR6048';
        let coilModel = localStorage.getItem('olmios_coil_mod') || '5TXCC007';
        let furnModel = localStorage.getItem('olmios_furn_mod') || 'S8X1C080';

        let typeLabel = "Gas System";
        if(savedType === 'elec_sys') typeLabel = "Electric System";
        else if(savedType === 'gas_hp') typeLabel = "Gas Heat Pump System";
        else if(savedType === 'elec_hp') typeLabel = "Electric Heat Pump System";
        else if(savedType === 'comm_pkg') typeLabel = "Commercial Package Unit";
        else if(savedType === 'comm_split') typeLabel = "Commercial Split System";
        else if(savedType.includes('mini')) typeLabel = "Mini Split System";

        let container = document.getElementById('dynamic_replacement_tabs');
        container.innerHTML = `
            <button type="button" class="btn-category text-start px-3 py-2.5" onclick="toggleMultiReplacementTab(this, 'Complete ${typeLabel} (${condModel})')">
                <i class="fa-solid fa-arrows-rotate text-success me-2"></i> Replace Complete ${typeLabel} (Condenser: ${condModel})
            </button>
            <button type="button" class="btn-category text-start px-3 py-2.5" onclick="toggleMultiReplacementTab(this, 'Evaporator Coil (${coilModel})')">
                <i class="fa-solid fa-box text-info me-2"></i> Replace Evaporator Coil (${coilModel})
            </button>
            <button type="button" class="btn-category text-start px-3 py-2.5" onclick="toggleMultiReplacementTab(this, 'Furnace / Heating Unit (${furnModel})')">
                <i class="fa-solid fa-fire text-danger me-2"></i> Replace Furnace / Heating Unit (${furnModel})
            </button>`;
    }

    function toggleMultiReplacementTab(element, tabName) {
        element.classList.toggle('active');
        let index = selectedReplacementTabs.indexOf(tabName);
        if(index > -1) {
            selectedReplacementTabs.splice(index, 1);
        } else {
            selectedReplacementTabs.push(tabName);
        }

        let issueBox = document.getElementById('issue_description');
        if(selectedReplacementTabs.length > 0) {
            issueBox.value = "Customer requested SYSTEM REPLACEMENT evaluation for: " + selectedReplacementTabs.join(" + ");
        } else {
            issueBox.value = "Customer requested SYSTEM REPLACEMENT evaluation.";
        }
    }

    function parseModelNumberDetails(modelStr) {
        let m = modelStr ? modelStr.toUpperCase().trim() : '';
        let result = { brand: 'Trane', tonnage: '3.0 Tons', SEER: '16 SEER2', refrig: 'R-410A' };

        if(m.includes('5TTR') || m.includes('4TTR') || m.includes('S8X') || m.includes('5TXC')) result.brand = 'Trane';
        else if(m.includes('24AA') || m.includes('59SC')) result.brand = 'Carrier';
        else if(m.includes('GSX') || m.includes('GM9')) result.brand = 'Goodman';
        else if(m.includes('XC') || m.includes('EL19')) result.brand = 'Lennox';

        if(m.startsWith('5')) {
            result.refrig = 'R-454B';
        } else if(m.startsWith('4')) {
            result.refrig = 'R-410A';
        } else if(m.startsWith('2')) {
            result.refrig = 'R-22';
        }

        if(m.includes('048')) result.tonnage = '4.0 Tons';
        else if(m.includes('036')) result.tonnage = '3.0 Tons';
        else if(m.includes('024')) result.tonnage = '2.0 Tons';
        else if(m.includes('060')) result.tonnage = '5.0 Tons';
        else if(m.includes('018')) result.tonnage = '1.5 Tons';

        return result;
    }

    function autoFillDescription() {
        let chatInput = document.getElementById('chat_assistant_input').value.trim();
        let issueBox = document.getElementById('issue_description');
        let followupBox = document.getElementById('ai_followup_box');
        let eqSelectVal = document.getElementById('equipment_type_select').value;

        let condModel = localStorage.getItem('olmios_cond_mod') || '5TTR6048';
        let coilModel = localStorage.getItem('olmios_coil_mod') || '5TXCC007';
        let furnModel = localStorage.getItem('olmios_furn_mod') || 'S8X1C080';
        let sysType = localStorage.getItem('olmios_hvac_type') || 'gas_sys';
        let parsed = parseModelNumberDetails(condModel);

        let isGas = sysType.includes('gas');
        let sysEnergyLabel = isGas ? 'Gas System' : 'Electric System';

        let lowerChat = chatInput.toLowerCase();
        if(lowerChat.includes('leak') || lowerChat.includes('coil')) {
            followupBox.style.display = 'block';
        } else {
            followupBox.style.display = 'none';
        }

        let componentDetails = "Condenser " + condModel + ", Evaporator Coil " + coilModel + ", Furnace " + furnModel;
        if(currentCoilSelection === 'Indoor Evaporator Coil') {
            componentDetails = "Evaporator Coil " + coilModel + " (Indoor Evaporator Coil Specified)";
        } else if(currentCoilSelection === 'Outdoor Condenser Coil') {
            componentDetails = "Condenser " + condModel + " (Outdoor Condenser Coil Specified)";
        }

        let issueContextStr = eqSelectVal ? " | [ISSUE CATEGORY]: " + eqSelectVal : "";

        let prioritizedSpecs = issueContextStr + " | [TECH SPECS SUMMARY]: " +
            "1. Manufacturer: " + parsed.brand + " " +
            "| 2. System Energy: " + sysEnergyLabel + " " +
            "| 3. Tonnage: " + parsed.tonnage + " " +
            "| 4. SEER Rating: " + parsed.SEER + " " +
            "| 5. Refrigerant Type: " + parsed.refrig + " " +
            "| 6. Line Size: 3/8' Liquid x 7/8' Suction " +
            "| 7. Model/Serial Specs: " + componentDetails;

        if (chatInput !== "") {
            issueBox.value = chatInput + prioritizedSpecs;
        } else {
            issueBox.value = "Customer requested diagnostic service." + prioritizedSpecs;
        }
    }

    function answerAiLeak(coilType) {
        currentCoilSelection = coilType;
        document.getElementById('ai_followup_box').style.display = 'none';
        autoFillDescription();
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

# ==========================================
# RESTORED DISPATCH COMMAND CENTER (/admin)
# ==========================================
@app.route('/admin')
def admin():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM service_requests")
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM service_requests WHERE status = 'Pending' OR status IS NULL")
    pending_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM service_requests WHERE status = 'In Progress'")
    progress_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM service_requests WHERE status = 'Completed'")
    completed_count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(est_value) FROM service_requests WHERE status != 'Completed'")
    total_pipeline_val = cursor.fetchone()[0]
    total_pipeline_val = total_pipeline_val if total_pipeline_val else 0.00

    active_count = pending_count + progress_count

    cursor.execute("SELECT COUNT(*) FROM sms_messages WHERE sender_type = 'Customer' AND is_new = 1")
    new_customer_sms = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sms_messages WHERE sender_type = 'Tech' AND is_new = 1")
    new_tech_sms = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, first_name, last_name, customer_name, phone, email, 
               address, city, zip_code, urgency, equipment, model_number, 
               serial_number, issue_description, assigned_tech, status, est_value, created_at 
        FROM service_requests ORDER BY id DESC
    """)
    rows = cursor.fetchall()

    cursor.execute("SELECT id, sender_type, sender_name, sender_phone, message_text, timestamp, is_new FROM sms_messages ORDER BY id DESC")
    sms_rows = cursor.fetchall()
    conn.close()

    map_markers = []
    table_rows = ""

    for idx, r in enumerate(rows):
        (req_id, first_name, last_name, old_cust_name, phone, email,
         address, city, zip_code, urgency, equip, model_no,
         serial_no, desc, assigned_tech, status, est_value, created_at) = r
        status = status if status else "Pending"
        assigned_tech = assigned_tech if assigned_tech else "Unassigned"

        age_text, is_urgent_age = calculate_age(created_at)

        status_bg = "#fef3c7"
        status_color = "#b45309"
        if status == "In Progress":
            status_bg = "#dbeafe"
            status_color = "#1d4ed8"
        elif status == "Completed":
            status_bg = "#dcfce7"
            status_color = "#15803d"

        urgency = urgency if urgency else "Standard Service"

        urgency_bg = "#e0f2fe"
        urgency_color = "#0369a1"
        circle_color = "#0284c7"
        is_emergency = False

        if "Emergency" in urgency:
            urgency_bg = "#fee2e2"
            urgency_color = "#dc2626"
            circle_color = "#dc2626"
            is_emergency = True
        elif "Routine" in urgency:
            urgency_bg = "#f0fdf4"
            urgency_color = "#166534"
            circle_color = "#16a34a"

        full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else old_cust_name

        contact_info = f"<a href='tel:{phone}' style='color: #0f172a; text-decoration: none; font-weight: 700; white-space: nowrap;' title='Click to Call/Text'>📞 {phone}</a>"
        if email:
            contact_info += f"<br><span style='font-size: 11px; color: #64748b; word-break: break-all;'>{email}</span>"

        full_address = f"{address}, {city}, {zip_code}".strip(", ")

        if status != "Completed" and address:
            lat, lng = get_lat_lng(full_address)
            map_markers.append({
                "id": req_id,
                "name": full_name,
                "address": full_address,
                "lat": lat,
                "lng": lng,
                "color": circle_color,
                "urgency": urgency,
                "equipment": equip,
                "is_emergency": is_emergency
            })

        if address:
            location_info = f"<a href='javascript:void(0);' onclick='focusMap({req_id})' style='color: #2563eb; text-decoration: none; font-weight: 600; line-height: 1.3; display: inline-block;' title='Focus on Map'>📍 {address}</a>"
            if city or zip_code:
                location_info += f"<br><span style='font-size: 11px; color: #64748b;'>{city}, {zip_code}</span>"
        else:
            location_info = "<em>No address provided</em>"

        specs_info = f"<span style='background: #f1f5f9; color: #334155; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block;'>{equip}</span>"
        if model_no or serial_no:
            specs_info += "<br><div style='font-size: 10px; color: #64748b; margin-top: 4px; line-height: 1.2;'>"
            if model_no: specs_info += f"<strong>M/N:</strong> {model_no}<br>"
            if serial_no: specs_info += f"<strong>S/N:</strong> {serial_no}"
            specs_info += "</div>"

        tech_options = ["Unassigned", "Tech A (Lead)", "Tech B", "Tech C"]
        tech_select = f"<form action='/assign_tech/{req_id}' method='POST' style='margin:0;'><select name='tech' onchange='this.form.submit()' style='padding:4px; font-size:11px; border-radius:6px; border:1px solid #cbd5e1; background:#f8fafc; font-weight:600; color:#334155; max-width: 100%;'>"
        for t in tech_options:
            selected = "selected" if t == assigned_tech else ""
            tech_select += f"<option value='{t}' {selected}>{t}</option>"
        tech_select += "</select></form>"

        initial_display = "display: none;" if status == "Completed" else ""
        age_badge_color = "background: #fee2e2; color: #dc2626;" if (is_urgent_age and status == "Pending") else "background: #f1f5f9; color: #64748b;"

        table_rows += f"""
        <tr class="data-row job-row" data-status="{status}" style="{initial_display}">
            <td style="width: 35px;"><strong style="color: #64748b;">#{req_id}</strong></td>
            <td style="min-width: 110px;">
                <a href="javascript:void(0);" onclick="openDrawer({req_id}, '{full_name}', '{phone}', '{full_address}', '{equip}', '{desc}', '{assigned_tech}')" style="color: #0f172a; text-decoration: underline; font-weight: 700;">
                    {full_name}
                </a><br>
                <span style="{age_badge_color} font-size: 9px; padding: 2px 5px; border-radius: 4px; font-weight: 700;">⏱️ {age_text}</span>
            </td>
            <td style="min-width: 120px;">{contact_info}</td>
            <td style="min-width: 130px;">{location_info}</td>
            <td style="min-width: 80px;">
                <span style="background: {urgency_bg}; color: {urgency_color}; padding: 3px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; display: inline-block;">
                    {urgency}
                </span>
            </td>
            <td style="min-width: 110px;">{specs_info}</td>
            <td style="min-width: 100px; font-size: 12px; color: #334155;">{desc}</td>
            <td style="min-width: 95px;">{tech_select}</td>
            <td style="min-width: 85px;">
                <a href="/toggle_status/{req_id}" style="background: {status_bg}; color: {status_color}; padding: 4px 8px; border-radius: 20px; text-decoration: none; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; display: inline-block; white-space: nowrap;">
                    {status.upper()} 🔄
                </a>
            </td>
            <td style="width: 75px; white-space: nowrap;">
                <a href="/work_order/{req_id}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 700; font-size: 11px; margin-right: 6px;" title="Print Work Order">📄 Ticket</a>
                <a href="/delete/{req_id}" onclick="return confirm('Delete record #{req_id}?');" style="color: #dc2626; text-decoration: none; font-weight: 600; font-size: 11px;">Delete</a>
            </td>
        </tr>
        """

    customer_sms_html = ""
    tech_sms_html = ""

    for msg in sms_rows:
        msg_id, sender_type, name, phone, text, timestamp, is_new = msg
        new_badge = "<span style='background:#fee2e2; color:#dc2626; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:800; margin-left:6px;'>NEW</span>" if is_new else ""

        row_content = f"""
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-bottom: 4px;">
                <span><strong>{name}</strong> ({phone}) {new_badge}</span>
                <span>{timestamp}</span>
            </div>
            <div style="font-size: 13px; color: #0f172a; font-weight: 600;">{text}</div>
            <div style="margin-top: 8px; display: flex; gap: 8px;">
                <a href="tel:{phone}" style="font-size: 11px; color: #2563eb; text-decoration: none; font-weight: 700;">📞 Call Back</a>
                <a href="sms:{phone}" style="font-size: 11px; color: #d97706; text-decoration: none; font-weight: 700;">💬 Reply SMS</a>
            </div>
        </div>
        """

        if sender_type == "Customer": customer_sms_html += row_content
        else: tech_sms_html += row_content

    if not customer_sms_html: customer_sms_html = "<div style='color: #64748b; font-size: 13px; padding: 20px; text-align: center;'>No customer text messages.</div>"
    if not tech_sms_html: tech_sms_html = "<div style='color: #64748b; font-size: 13px; padding: 20px; text-align: center;'>No technician/driver text messages.</div>"

    cust_alert_badge = f"<span style='background:#dc2626; color:#ffffff; padding:1px 6px; border-radius:10px; font-size:9px; font-weight:800;'>{new_customer_sms} NEW</span>" if new_customer_sms > 0 else ""
    tech_alert_badge = f"<span style='background:#dc2626; color:#ffffff; padding:1px 6px; border-radius:10px; font-size:9px; font-weight:800;'>{new_tech_sms} NEW</span>" if new_tech_sms > 0 else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OLMIOS | Dispatch Command Center</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            {COMMON_ADMIN_CSS}
            .container-admin {{ max-width: 100%; margin: 0 auto; padding: 10px; }}
            .header-admin {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            
            .kpi-grid {{ display: flex; gap: 12px; margin-bottom: 20px; }}
            .kpi-card {{ flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; }}
            .kpi-title {{ font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
            .kpi-val {{ font-size: 22px; font-weight: 800; color: #0f172a; margin-top: 2px; }}

            .split-container {{ display: flex; gap: 20px; align-items: flex-start; }}
            .left-pane {{ flex: 3; min-width: 0; background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid #e2e8f0; color: #0f172a; }}
            .right-pane {{ flex: 2; position: sticky; top: 20px; min-width: 340px; }}

            .map-container {{
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid #cbd5e1;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }}
            .map-header {{
                background: #f8fafc;
                padding: 10px 14px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 11px;
                font-weight: 700;
                color: #475569;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            #leafletMap {{ height: 500px; width: 100%; }}

            .controls-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; gap: 10px; flex-wrap: wrap; }}
            .search-input {{ flex: 1; min-width: 180px; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; font-family: inherit; }}
            
            .filter-tabs {{ display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }}
            .tab-btn {{ padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; border: 1px solid #cbd5e1; background: #f1f5f9; color: #475569; display: flex; align-items: center; gap: 4px; }}
            .tab-btn.active {{ background: #2563eb; color: #ffffff; border-color: #2563eb; }}
            .tab-sms-cust {{ border-color: #2563eb; color: #2563eb; background: #eff6ff; }}
            .tab-sms-tech {{ border-color: #d97706; color: #b45309; background: #fffbe3; }}
            .tab-btn.active.tab-sms-cust {{ background: #2563eb; color: #ffffff; }}
            .tab-btn.active.tab-sms-tech {{ background: #d97706; color: #ffffff; }}

            .table-wrapper {{ overflow-x: auto; width: 100%; }}
            table {{ width: 100%; border-collapse: collapse; table-layout: auto; }}
            th, td {{ padding: 10px 8px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 12px; vertical-align: top; box-sizing: border-box; color: #0f172a; }}
            th {{ background: #f8fafc; color: #64748b; font-weight: 700; text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px; white-space: nowrap; }}
            .nav-actions {{ display: flex; gap: 12px; align-items: center; }}
            
            .view-panel {{ display: none; }}
            .view-panel.active {{ display: block; }}
            
            .map-legend {{ display: flex; gap: 10px; font-size: 10px; font-weight: 700; }}
            .legend-item {{ display: flex; align-items: center; gap: 4px; }}
            .dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.2); }}

            .drawer {{
                position: fixed;
                top: 0; right: -400px;
                width: 380px; height: 100vh;
                background: #ffffff;
                color: #0f172a;
                box-shadow: -10px 0 25px rgba(0,0,0,0.3);
                transition: right 0.3s ease;
                z-index: 9999;
                padding: 25px;
                box-sizing: border-box;
                overflow-y: auto;
            }}
            .drawer.open {{ right: 0; }}
            .drawer-close {{ font-size: 20px; font-weight: 800; cursor: pointer; color: #64748b; float: right; }}
        </style>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            let map;
            let markerStore = {{}};
            const mapData = {json.dumps(map_markers)};
            let currentJobId = null;

            window.onload = function() {{
                map = L.map('leafletMap').setView([29.7604, -95.3698], 10);

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 18,
                    attribution: '© OpenStreetMap contributors'
                }}).addTo(map);

                mapData.forEach(job => {{
                    let circle = L.circleMarker([job.lat, job.lng], {{
                        color: '#0f172a',
                        fillColor: job.color,
                        fillOpacity: 0.95,
                        radius: job.is_emergency ? 12 : 9,
                        weight: job.is_emergency ? 3 : 2
                    }}).addTo(map);

                    let popupContent = `
                        <div style="font-family: inherit; font-size: 12px; color: #0f172a;">
                            <strong>Order #${{job.id}} - ${{job.name}}</strong><br>
                            <span style="color: #64748b;">${{job.address}}</span><br>
                            <strong>Urgency:</strong> ${{job.urgency}}<br>
                            <strong>Type:</strong> ${{job.equipment}}<br><br>
                            <a href="https://www.google.com/maps/search/?api=1&query=${{encodeURIComponent(job.address)}}" target="_blank" style="color: #2563eb; font-weight: 700;">🗺️ Open Directions</a>
                        </div>
                    `;

                    circle.bindPopup(popupContent);
                    markerStore[job.id] = {{ circle: circle, lat: job.lat, lng: job.lng }};
                }});
            }};

            function focusMap(id) {{
                if (markerStore[id]) {{
                    map.setView([markerStore[id].lat, markerStore[id].lng], 14);
                    markerStore[id].circle.openPopup();
                }}
            }}

            function openDrawer(id, name, phone, address, equip, desc, tech) {{
                currentJobId = id;
                document.getElementById('drawerTitle').innerText = "Quick Dispatch #" + id;
                document.getElementById('drawerName').innerText = name;
                document.getElementById('drawerPhone').innerText = phone;
                document.getElementById('drawerAddress').innerText = address;
                document.getElementById('drawerEquip').innerText = equip;
                document.getElementById('drawerDesc').innerText = desc;
                
                let techSelect = document.getElementById('drawerTechSelect');
                if (techSelect) {{
                    techSelect.value = tech && tech !== 'Unassigned' ? tech : 'Tech A (Lead)';
                }}

                updateSmsPayload(id, name, phone, address, equip, desc);
                document.getElementById('quickDrawer').classList.add('open');
            }}

            function updateSmsPayload(id, name, phone, address, equip, desc) {{
                let selectedTech = document.getElementById('drawerTechSelect').value;
                let mapsUrl = "https://maps.google.com/?q=" + encodeURIComponent(address);
                let smsBody = `OLMIOS DISPATCH%0AOrder #${{id}} Accepted by ${{selectedTech}}%0A%0AClient: ${{name}}%0APhone: ${{phone}}%0ALocation: ${{address}}%0AEquip: ${{equip}}%0ANotes: ${{desc}}%0ANavigate: ${{mapsUrl}}`;
                
                document.getElementById('drawerSmsBtn').href = "sms:?body=" + smsBody;
            }}

            function handleDispatchAccept() {{
                if (!currentJobId) return;
                let selectedTech = document.getElementById('drawerTechSelect').value;
                
                let form = document.createElement('form');
                form.method = 'POST';
                form.action = '/accept_and_dispatch/' + currentJobId;
                
                let inputTech = document.createElement('input');
                inputTech.type = 'hidden';
                inputTech.name = 'tech';
                inputTech.value = selectedTech;
                form.appendChild(inputTech);
                
                document.body.appendChild(form);
                form.submit();
            }}

            function closeDrawer() {{
                document.getElementById('quickDrawer').classList.remove('open');
            }}

            function switchView(viewName, btn) {{
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
                
                if (viewName === 'CustomerSMS') {{
                    document.getElementById('customerSmsPanel').classList.add('active');
                }} else if (viewName === 'TechSMS') {{
                    document.getElementById('techSmsPanel').classList.add('active');
                }} else {{
                    document.getElementById('jobsTablePanel').classList.add('active');
                    filterJobs(viewName);
                }}
            }}

            function filterJobs(view) {{
                let rows = document.querySelectorAll('.job-row');
                rows.forEach(r => {{
                    let status = r.getAttribute('data-status');
                    if (view === 'Active') {{
                        r.style.display = (status !== 'Completed') ? '' : 'none';
                    }} else if (view === 'All') {{
                        r.style.display = '';
                    }} else {{
                        r.style.display = (status === view) ? '' : 'none';
                    }}
                }});
            }}

            function searchTable() {{
                let query = document.getElementById('searchInput').value.toLowerCase();
                let rows = document.querySelectorAll('.job-row');
                rows.forEach(r => {{
                    let text = r.innerText.toLowerCase();
                    r.style.display = text.includes(query) ? '' : 'none';
                }});
            }}
        </script>
    </head>
    <body>
        <div class="panel container-admin">
            <div class="header-admin">
                <div>
                    <h1 class="brand-logo" style="margin: 0;">OLMIOS</h1>
                    <span style="color: #64748b; font-size: 12px; letter-spacing: 0.5px; font-weight: 700;">DISPATCH COMMAND CENTER</span>
                </div>
                <div class="nav-actions">
                    <a href="/customer_home" class="btn-admin btn-primary-admin">+ NEW ORDER</a>
                    <a href="/customer_home" class="home-phoenix-btn" title="Return to Customer Home">
                        {get_phoenix_svg(46, 46)}
                    </a>
                </div>
            </div>

            <!-- KPI SUMMARY CARDS -->
            <div class="kpi-grid">
                <div class="kpi-card" style="border-left: 4px solid #64748b;">
                    <div class="kpi-title">Total Orders</div>
                    <div class="kpi-val">{total_count}</div>
                </div>
                <div class="kpi-card" style="border-left: 4px solid #d97706;">
                    <div class="kpi-title">Pending Dispatch</div>
                    <div class="kpi-val" style="color: #b45309;">{pending_count}</div>
                </div>
                <div class="kpi-card" style="border-left: 4px solid #2563eb;">
                    <div class="kpi-title">In Progress</div>
                    <div class="kpi-val" style="color: #1d4ed8;">{progress_count}</div>
                </div>
                <div class="kpi-card" style="border-left: 4px solid #16a34a;">
                    <div class="kpi-title">Active Pipeline Value</div>
                    <div class="kpi-val" style="color: #16a34a;">${total_pipeline_val:,.2f}</div>
                </div>
            </div>

            <!-- SPLIT SCREEN LAYOUT -->
            <div class="split-container">
                
                <!-- LEFT PANE: PRIORITIZED TABS & VIEWS -->
                <div class="left-pane">
                    <div class="controls-bar">
                        <input type="text" id="searchInput" class="search-input" onkeyup="searchTable()" placeholder="🔍 Search customer, phone, or site...">
                        
                        <div class="filter-tabs">
                            <button class="tab-btn active" onclick="switchView('Active', this)">Active Jobs ({active_count})</button>
                            <button class="tab-btn tab-sms-cust" onclick="switchView('CustomerSMS', this)">💬 Customer Texts {cust_alert_badge}</button>
                            <button class="tab-btn tab-sms-tech" onclick="switchView('TechSMS', this)">📱 Tech/Driver Texts {tech_alert_badge}</button>
                            
                            <span style="color:#cbd5e1; margin:0 2px;">|</span>
                            
                            <button class="tab-btn" onclick="switchView('Pending', this)">Pending ({pending_count})</button>
                            <button class="tab-btn" onclick="switchView('In Progress', this)">In Progress ({progress_count})</button>
                            <button class="tab-btn" onclick="switchView('Completed', this)">Archive ({completed_count})</button>
                            <button class="tab-btn" onclick="switchView('All', this)">All ({total_count})</button>
                        </div>
                    </div>

                    <!-- VIEW 1: DISPATCH JOBS TABLE -->
                    <div id="jobsTablePanel" class="view-panel active">
                        <div class="table-wrapper">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Customer & Age</th>
                                        <th>Contact</th>
                                        <th>Job Location</th>
                                        <th>Urgency</th>
                                        <th>Equipment</th>
                                        <th>Details</th>
                                        <th>Tech</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {table_rows if table_rows else '<tr><td colspan="10" style="text-align:center; color: #64748b; padding: 30px;">No active service requests.</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- VIEW 2: CUSTOMER SMS TAB -->
                    <div id="customerSmsPanel" class="view-panel">
                        <h3 style="margin: 0 0 15px; font-size: 15px; color: #0f172a;">💬 Customer Text Messages</h3>
                        {customer_sms_html}
                    </div>

                    <!-- VIEW 3: TECH / DRIVER SMS TAB -->
                    <div id="techSmsPanel" class="view-panel">
                        <h3 style="margin: 0 0 15px; font-size: 15px; color: #0f172a;">📱 Field Tech & Driver Messages</h3>
                        {tech_sms_html}
                    </div>

                </div>

                <!-- RIGHT PANE: COLOR-CODED LIVE MAP -->
                <div class="right-pane">
                    <div class="map-container">
                        <div class="map-header">
                            <span>DISPATCH MAP PANE</span>
                            <div class="map-legend">
                                <span class="legend-item"><span class="dot" style="background:#dc2626;"></span> Emergency</span>
                                <span class="legend-item"><span class="dot" style="background:#0284c7;"></span> Standard</span>
                                <span class="legend-item"><span class="dot" style="background:#16a34a;"></span> Routine</span>
                            </div>
                        </div>
                        <div id="leafletMap"></div>
                    </div>
                </div>

            </div>
        </div>

        <!-- UBER-STYLE QUICK DISPATCH DRAWER -->
        <div id="quickDrawer" class="drawer">
            <span class="drawer-close" onclick="closeDrawer()">✕</span>
            <h3 id="drawerTitle" style="margin-top: 0; color: #0f172a;">Quick Dispatch</h3>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin-bottom: 20px;">

            <div style="font-size: 13px; line-height: 1.8; color: #334155;">
                <p><strong>Customer:</strong> <span id="drawerName"></span></p>
                <p><strong>Phone:</strong> <span id="drawerPhone"></span></p>
                <p><strong>Job Site:</strong> <span id="drawerAddress"></span></p>
                <p><strong>Equipment:</strong> <span id="drawerEquip"></span></p>
                <p><strong>Issue Notes:</strong> <span id="drawerDesc"></span></p>
                
                <div style="margin-top: 15px;">
                    <label style="display: block; font-weight: 700; color: #0f172a; margin-bottom: 5px;">Select Active Tech / Driver:</label>
                    <select id="drawerTechSelect" onchange="updateSmsPayload(currentJobId, document.getElementById('drawerName').innerText, document.getElementById('drawerPhone').innerText, document.getElementById('drawerAddress').innerText, document.getElementById('drawerEquip').innerText, document.getElementById('drawerDesc').innerText)" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: 700; color: #0f172a;">
                        <option value="Tech A (Lead)">Tech A (Lead Driver)</option>
                        <option value="Tech B">Tech B (HVAC Tech)</option>
                        <option value="Tech C">Tech C (Field Tech)</option>
                    </select>
                </div>
            </div>

            <div style="margin-top: 30px; display: flex; flex-direction: column; gap: 10px;">
                <a id="drawerSmsBtn" href="#" onclick="handleDispatchAccept()" class="btn-admin btn-accent-admin" style="box-sizing: border-box; display: block; font-size: 13px;">
                    📱 DISPATCH & SMS TO TECH
                </a>
            </div>
        </div>
    </body>
    </html>
    """

# ==========================================
# ADMIN ACTION ENDPOINTS
# ==========================================
@app.route("/accept_and_dispatch/<int:req_id>", methods=["POST"])
def accept_and_dispatch(req_id):
    tech = request.form.get("tech", "Tech A (Lead)")
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE service_requests SET assigned_tech = ?, status = 'In Progress' WHERE id = ?", (tech, req_id))
    cursor.execute("""
        INSERT INTO sms_messages (sender_type, sender_name, sender_phone, message_text, is_new)
        VALUES ('Tech', ?, '8325550199', ?, 1)
    """, (tech, f"Accepted Order #{req_id} & En Route to Job Site"))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/assign_tech/<int:req_id>", methods=["POST"])
def assign_tech(req_id):
    tech = request.form.get("tech")
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE service_requests SET assigned_tech = ? WHERE id = ?", (tech, req_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/toggle_status/<int:req_id>")
def toggle_status(req_id):
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM service_requests WHERE id = ?", (req_id,))
    row = cursor.fetchone()

    if row:
        current_status = row[0] if row[0] else "Pending"
        next_status = "Pending"
        if current_status == "Pending":
            next_status = "In Progress"
        elif current_status == "In Progress":
            next_status = "Completed"

        cursor.execute("UPDATE service_requests SET status = ? WHERE id = ?", (next_status, req_id))
        conn.commit()

    conn.close()
    return redirect(url_for("admin"))

@app.route("/delete/<int:req_id>")
def delete_request(req_id):
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM service_requests WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/work_order/<int:req_id>")
def work_order(req_id):
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT first_name, last_name, customer_name, phone, email, address, city, zip_code, urgency, equipment, model_number, serial_number, issue_description, assigned_tech, status, est_value, created_at 
        FROM service_requests WHERE id = ?
    """, (req_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return redirect(url_for("admin"))

    (first_name, last_name, old_cust, phone, email, address, city, zip_code,
     urgency, equip, model_no, serial_no, desc, tech, status, est_val, created_at) = row
    full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else old_cust

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WORK ORDER #{req_id} | OLMIOS</title>
        <style>
            body {{ font-family: 'Outfit', sans-serif; padding: 40px; color: #0f172a; max-width: 800px; margin: 0 auto; background: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0f172a; padding-bottom: 15px; }}
            .brand {{ font-size: 26px; font-weight: 800; letter-spacing: 4px; }}
            .wo-title {{ text-align: right; }}
            .grid {{ display: flex; gap: 20px; margin: 25px 0; }}
            .box {{ flex: 1; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; font-size: 13px; line-height: 1.6; }}
            .box-title {{ font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
            .tech-notes {{ border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; min-height: 120px; margin-bottom: 30px; font-size: 13px; color: #94a3b8; }}
            .signatures {{ display: flex; justify-content: space-between; margin-top: 50px; font-size: 12px; font-weight: 600; color: #475569; }}
            .sig-line {{ border-top: 1px solid #0f172a; width: 220px; text-align: center; padding-top: 5px; margin-top: 40px; }}
            .no-print {{ margin-bottom: 20px; text-align: right; }}
        </style>
    </head>
    <body>
        <div class="no-print">
            <button onclick="window.print()" style="padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: 700; cursor: pointer;">🖨️ PRINT WORK ORDER</button>
        </div>
        <div class="header">
            <div>
                <div style="display:flex; align-items:center; gap: 10px;">
                    {get_phoenix_svg(48, 48)}
                    <div>
                        <div class="brand">OLMIOS</div>
                        <div style="font-size: 11px; color: #64748b; font-weight: 700;">SERVICE & DISPATCH MANAGEMENT</div>
                    </div>
                </div>
            </div>
            <div class="wo-title">
                <h2 style="margin: 0; color: #2563eb;">FIELD WORK ORDER</h2>
                <div style="font-size: 13px; font-weight: 700;">TICKET #{req_id}</div>
                <div style="font-size: 11px; color: #64748b;">Issued: {created_at}</div>
            </div>
        </div>

        <div class="grid">
            <div class="box">
                <div class="box-title">Customer & Job Location</div>
                <strong>{full_name}</strong><br>
                📞 {phone}<br>
                ✉️ {email if email else 'N/A'}<br><br>
                📍 <strong>{address}</strong><br>
                {city}, {zip_code}
            </div>
            <div class="box">
                <div class="box-title">Equipment & Service Details</div>
                <strong>System:</strong> {equip}<br>
                <strong>Model:</strong> {model_no if model_no else 'N/A'}<br>
                <strong>Serial:</strong> {serial_no if serial_no else 'N/A'}<br>
                <strong>Urgency:</strong> {urgency}<br>
                <strong>Assigned Tech:</strong> {tech}
            </div>
        </div>

        <div class="box" style="margin-bottom: 20px;">
            <div class="box-title">Reported Issue Description</div>
            {desc}
        </div>

        <div class="box-title" style="margin-top: 20px;">Technician Diagnostic & Resolution Notes</div>
        <div class="tech-notes">
            [ Tech Write-up, Installed Parts, and Recommendations ]
        </div>

        <div class="signatures">
            <div>
                <div class="sig-line">Technician Signature</div>
            </div>
            <div>
                <div class="sig-line">Customer Acceptance Signature</div>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
