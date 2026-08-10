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
            est_value REAL DEFAULT 99.00,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Pending',
            is_backorder INTEGER DEFAULT 0,
            backorder_notes TEXT DEFAULT '',
            quote_amount REAL DEFAULT 0.00,
            quote_status TEXT DEFAULT 'Draft'
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refund_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            customer_name TEXT NOT NULL,
            amount REAL NOT NULL,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'Pending Manager Approval',
            requested_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tech_timecards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tech_name TEXT NOT NULL,
            clock_in DATETIME,
            clock_out DATETIME,
            hours_logged REAL DEFAULT 0.00,
            is_apprentice INTEGER DEFAULT 1
        )
    """)

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
        padding: 20px;
    }
    .brand-logo {
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 4px;
        color: #0f172a;
        text-transform: uppercase;
    }
    .btn-admin {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 700;
        font-size: 12px;
        border: none;
        cursor: pointer;
        text-align: center;
        transition: all 0.2s ease;
    }
    .btn-primary-admin { background-color: #2563eb; color: #ffffff; }
    .btn-primary-admin:hover { background-color: #1d4ed8; color: white; }
    .btn-accent-admin { background-color: #d97706; color: #ffffff; }
    .btn-accent-admin:hover { background-color: #b45309; color: white; }
    .btn-outline-admin { border: 1px solid #cbd5e1; background: #ffffff; color: #1e293b; }
    .btn-outline-admin:hover { background: #f1f5f9; color: #2563eb; }
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

def clean_str(val):
    if not val:
        return ""
    return str(val).replace('"', '').replace("'", '').replace('\n', ' ').strip()

# ==========================================
# CUSTOMER APP ROUTES
# ==========================================
@app.route('/')
def index():
    return redirect('/customer_home')

@app.route('/customer_home')
def customer_home():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Customer Portal</title>
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
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <div class="d-flex align-items-center gap-2">
                <img id="home_avatar" src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80" style="width: 45px; height: 45px; border-radius: 50%; object-fit: cover;">
                <div>
                    <h6 class="fw-bold mb-0 text-muted small" id="greeting_title">WELCOME BACK</h6>
                    <span class="fw-bold text-dark fs-6" id="display_fullname">Ian Olvera</span>
                </div>
            </div>
            <a href="/customer_home" title="Home">{{PHOENIX}}</a>
        </div>

        <div class="row g-2 mb-3">
            <div class="col-4"><a href="/customer_quotes" class="btn btn-outline-primary w-100 py-2 fw-bold small"><i class="fa-solid fa-calculator me-1"></i> Quote</a></div>
            <div class="col-4"><a href="/customer_work_orders" class="btn btn-outline-warning text-dark w-100 py-2 fw-bold small"><i class="fa-solid fa-clock-rotate-left me-1"></i> Open Order</a></div>
            <div class="col-4"><a href="/invoices" class="btn btn-outline-success w-100 py-2 fw-bold small"><i class="fa-solid fa-file-invoice-dollar me-1"></i> Invoice</a></div>
        </div>

        <div id="map"></div>

        <a href="/dispatch_request" class="btn btn-amber w-100 py-3 rounded-3 fw-bold fs-6 mb-3 shadow-sm">
            <i class="fa-solid fa-bolt me-1"></i> REQUEST INSTANT HVAC SERVICE ($99.00)
        </a>
        
        <div class="row g-2 mb-3">
            <div class="col-6"><a href="/profile" class="btn btn-nav-thin w-100 py-2.5 small"><i class="fa-solid fa-user-gear me-1 text-primary"></i> Profile & Wallet</a></div>
            <div class="col-6"><a href="/invoices" class="btn btn-nav-thin w-100 py-2.5 small"><i class="fa-solid fa-receipt me-1 text-primary"></i> View Invoices</a></div>
        </div>

        <div class="guarantee-box shadow-sm mb-3">
            <i class="fa-solid fa-shield-halved me-1"></i> VERIFIED OLMIOS GUARANTEE - 100% Licensed & Background-Checked
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([29.7604, -95.3698], 10);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
        L.marker([29.7604, -95.3698]).addTo(map).bindPopup("<b>🏠 Saved Residence Location</b><br>18510 Ranch View Trail Cir, Houston, TX").openPopup();
    </script>
</body>
</html>"""
    return html.replace('{{HEADER}}', COMMON_HEADER).replace('{{PHOENIX}}', get_phoenix_svg(45, 45))

# ==========================================
# SHOT #5 & SHOT #4: TECHNICIAN MOBILE APP (/tech_home)
# NO "YOU'RE OFFLINE" TEXT - ONLY DISPLAY CUSTOMER NAME WHEN OFFLINE
# ==========================================
@app.route('/tech_home')
def tech_home():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios Field Tech Portal</title>
    {{HEADER}}
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background-color: #0b1329; color: white; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 10px; min-height: 100vh; }
        .tech-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 18px; max-width: 450px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.4); position: relative; }
        #tech_map { height: 280px; border-radius: 14px; margin-bottom: 12px; border: 1px solid #cbd5e1; }
        
        .open-world-go-btn {
            width: 75px; height: 75px; border-radius: 50%; background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white; font-weight: 900; font-size: 1.2rem; border: 3px solid #ffffff; box-shadow: 0 8px 20px rgba(37, 99, 235, 0.5);
            display: flex; align-items: center; justify-content: center; margin: -40px auto 12px auto; z-index: 1000; position: relative; cursor: pointer;
        }

        .ping-banner { background: #fef3c7; border: 2px solid #f59e0b; border-radius: 14px; padding: 12px; margin-bottom: 12px; display: none; }
        .drawer-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; }
        .tech-menu-drawer { position: fixed; top: 0; left: -280px; width: 270px; height: 100%; background: #ffffff; color: #0f172a; z-index: 2100; transition: left 0.3s ease; padding: 20px; box-sizing: border-box; }
        .tech-menu-drawer.open { left: 0; }
    </style>
</head>
<body>
    <div class="tech-card">
        <!-- HEADER WITH OFFLINE ASSIGNED CUSTOMER NAME (NO "YOU'RE OFFLINE" TEXT) -->
        <div class="d-flex align-items-center justify-content-between mb-2 pb-2 border-bottom">
            <div class="d-flex align-items-center gap-2">
                <button type="button" class="btn btn-light btn-sm rounded-circle shadow-sm" onclick="toggleTechMenu()"><i class="fa-solid fa-bars fs-5"></i></button>
                <div>
                    <!-- ASSIGNED CUSTOMER'S NAME DISPLAYED DIRECTLY -->
                    <h6 class="fw-bold mb-0 text-dark" id="assigned_cust_heading">👤 Assigned Client: Ian Olvera</h6>
                    <span class="text-muted small" id="online_status_sub">18510 Ranch View Trail Cir, Houston TX</span>
                </div>
            </div>
            <span class="badge bg-success py-1.5 px-2.5 rounded-pill fs-7">$0.00 Today</span>
        </div>

        <div id="tech_map"></div>

        <!-- SHOT #5 OPEN WORLD TOGGLE BUTTON -->
        <div class="open-world-go-btn" id="open_world_btn" onclick="toggleOpenWorld()">
            GO
        </div>

        <!-- 30-SECOND DISPATCH RADAR PING (SHOT #4) -->
        <div id="dispatch_ping_banner" class="ping-banner">
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-bold text-dark"><i class="fa-solid fa-bolt text-warning me-1"></i> INSTANT DISPATCH PING!</span>
                <span class="badge bg-danger fs-6" id="ping_timer">30s</span>
            </div>
            <p class="small text-muted mb-2">📍 18510 Ranch View Trail Cir — A/C Condenser Diagnostic</p>
            <button class="btn btn-sm btn-success w-100 fw-bold py-2 rounded-3" onclick="acceptDispatchPing()"><i class="fa-solid fa-circle-check me-1"></i> Accept Dispatch & Launch Route</button>
        </div>

        <!-- 45-MINUTE DIAGNOSTIC TIMER ENGINE (SHOT #4) -->
        <div id="diagnostic_timer_box" class="p-3 bg-light border rounded-3 text-center mb-2" style="display: none;">
            <span class="text-muted fw-bold small d-block mb-1">ON-SITE DIAGNOSTIC TIMEFRAME</span>
            <h3 class="fw-bold text-primary mb-2" id="diag_countdown">45:00</h3>
            <div class="row g-2">
                <div class="col-6"><button class="btn btn-sm btn-outline-warning w-100 fw-bold" onclick="alert('Requested 15m Extension from Dispatch')">+15m Extension</button></div>
                <div class="col-6"><button class="btn btn-sm btn-primary w-100 fw-bold" onclick="alert('Quote Form Launched')">Submit Quote</button></div>
            </div>
        </div>

        <div class="bg-light p-2.5 rounded-3 border">
            <span class="fw-bold text-dark small d-block mb-1"><i class="fa-solid fa-user-graduate me-1 text-primary"></i> Apprentice Field Hours Log</span>
            <div class="progress mb-1" style="height: 10px;">
                <div class="progress-bar bg-warning" style="width: 65%;">650 / 1,000 Hrs</div>
            </div>
            <span class="text-muted style-small" style="font-size: 0.72rem;">Working under Licensed Contractor: Olmios Local Mentorship</span>
        </div>
    </div>

    <!-- SHOT #5 CLEANED MENU DRAWER -->
    <div class="drawer-overlay" id="drawer_overlay" onclick="toggleTechMenu()"></div>
    <div class="tech-menu-drawer" id="tech_drawer">
        <div class="d-flex align-items-center gap-2 mb-4 border-bottom pb-3">
            <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;">
            <div>
                <h6 class="fw-bold mb-0">Jose (Field Tech)</h6>
                <span class="text-warning small fw-bold">★ 4.99 Rating</span>
            </div>
        </div>
        <ul class="list-unstyled d-flex flex-column gap-3 fw-bold text-dark">
            <li><a href="#" class="text-dark text-decoration-none"><i class="fa-solid fa-inbox me-2 text-primary"></i> Inbox <span class="badge bg-primary rounded-pill float-end">4</span></a></li>
            <li><a href="#" class="text-dark text-decoration-none"><i class="fa-solid fa-chart-line me-2 text-success"></i> Earnings</a></li>
            <li><a href="#" class="text-dark text-decoration-none"><i class="fa-solid fa-wallet me-2 text-warning"></i> Wallet / Instant Payout</a></li>
            <li><a href="#" class="text-dark text-decoration-none"><i class="fa-solid fa-user me-2 text-info"></i> Account Settings</a></li>
            <li><a href="#" class="text-dark text-decoration-none"><i class="fa-solid fa-circle-question me-2 text-secondary"></i> Help Center</a></li>
            <li><a href="#" class="text-dark text-decoration-none"><i class="fa-solid fa-graduation-cap me-2 text-danger"></i> Apprentice Learning Center</a></li>
        </ul>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var techMap = L.map('tech_map').setView([29.7604, -95.3698], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(techMap);
        L.marker([29.7604, -95.3698]).addTo(techMap).bindPopup("<b>Ian Olvera Residence</b><br>18510 Ranch View Trail Cir");

        var isOnline = false;

        function toggleOpenWorld() {
            isOnline = !isOnline;
            let btn = document.getElementById('open_world_btn');
            let heading = document.getElementById('assigned_cust_heading');
            let sub = document.getElementById('online_status_sub');
            let ping = document.getElementById('dispatch_ping_banner');

            if(isOnline) {
                btn.innerText = "OFF";
                btn.style.background = "linear-gradient(135deg, #dc2626, #991b1b)";
                heading.innerText = "⚡ You're Online — Open World Radar Active";
                sub.innerText = "Scanning 15 mile radius for instant dispatches...";
                ping.style.display = "block";
            } else {
                btn.innerText = "GO";
                btn.style.background = "linear-gradient(135deg, #2563eb, #1d4ed8)";
                heading.innerText = "👤 Assigned Client: Ian Olvera";
                sub.innerText = "18510 Ranch View Trail Cir, Houston TX";
                ping.style.display = "none";
            }
        }

        function acceptDispatchPing() {
            document.getElementById('dispatch_ping_banner').style.display = "none";
            document.getElementById('diagnostic_timer_box').style.display = "block";
            alert("Route Loaded! Navigating to customer location. Dispatch & Customer notified of your arrival.");
        }

        function toggleTechMenu() {
            document.getElementById('tech_drawer').classList.toggle('open');
            let overlay = document.getElementById('drawer_overlay');
            overlay.style.display = (overlay.style.display === 'block') ? 'none' : 'block';
        }
    </script>
</body>
</html>"""
    return html.replace('{{HEADER}}', COMMON_HEADER).replace('{{PHOENIX}}', get_phoenix_svg(42, 42))

# ==========================================
# SHOT #6: ENTERPRISE BACKOFFICE ERP ENGINE (/backoffice)
# ==========================================
@app.route('/backoffice')
def backoffice():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios Enterprise Backoffice ERP</title>
    {{HEADER}}
    <style>
        body { background-color: #0f172a; color: white; font-family: 'Outfit', sans-serif; padding: 20px; min-height: 100vh; }
        .erp-card { background: #ffffff; color: #0f172a; border-radius: 20px; padding: 25px; max-width: 1100px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .nav-pills .nav-link { color: #475569; font-weight: 700; border-radius: 10px; font-size: 0.85rem; }
        .nav-pills .nav-link.active { background: #2563eb; color: white; }
    </style>
</head>
<body>
    <div class="erp-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-3">
            <div class="d-flex align-items-center gap-2">
                {{PHOENIX}}
                <div>
                    <h4 class="fw-bold mb-0 text-dark">OLMIOS Enterprise Backoffice ERP</h4>
                    <span class="text-muted small">Offline Operations, Payroll, Inventory, CPQ & Supplier Sync</span>
                </div>
            </div>
            <a href="/admin" class="btn btn-sm btn-outline-primary fw-bold"><i class="fa-solid fa-headset me-1"></i> Dispatch Center</a>
        </div>

        <ul class="nav nav-pills nav-justified mb-4 bg-light p-1.5 rounded-3 border">
            <li class="nav-item"><button class="nav-link active" onclick="switchErpTab('payroll')"><i class="fa-solid fa-money-check-dollar me-1"></i> Payroll & Timecards</button></li>
            <li class="nav-item"><button class="nav-link" onclick="switchErpTab('personnel')"><i class="fa-solid fa-users-gear me-1"></i> Onboarding / Subcontractors</button></li>
            <li class="nav-item"><button class="nav-link" onclick="switchErpTab('inventory')"><i class="fa-solid fa-boxes-packing me-1"></i> Inventory & CPQ</button></li>
            <li class="nav-item"><button class="nav-link" onclick="switchErpTab('financials')"><i class="fa-solid fa-chart-pie me-1"></i> Financials & Supplier API</button></li>
        </ul>

        <!-- TAB 1: PAYROLL & TIMECARDS -->
        <div id="erp_payroll" class="erp-section">
            <h6 class="fw-bold text-primary mb-3"><i class="fa-solid fa-clock me-1"></i> Apprentice & Technician Timecard Management (Tax-Ready)</h6>
            <table class="table table-bordered align-middle small">
                <thead class="table-light">
                    <tr><th>Tech / Apprentice</th><th>Clock In</th><th>Clock Out</th><th>Logged Hours</th><th>Hourly Rate</th><th>Instant Payout</th></tr>
                </thead>
                <tbody>
                    <tr><td>Jose (Apprentice)</td><td>08:00 AM</td><td>04:30 PM</td><td>8.5 hrs</td><td>$28.00 / hr</td><td><button class="btn btn-sm btn-success py-0 px-2 fw-bold" onclick="alert('Instant Payout Released!')">⚡ 1-Click Payout</button></td></tr>
                </tbody>
            </table>
        </div>

        <!-- TAB 2: PERSONNEL ONBOARDING -->
        <div id="erp_personnel" class="erp-section" style="display:none;">
            <h6 class="fw-bold text-primary mb-3"><i class="fa-solid fa-id-card-clip me-1"></i> Employee & Subcontractor Onboarding / Offboarding</h6>
            <div class="row g-2">
                <div class="col-6"><input type="text" class="form-control form-control-sm" placeholder="Full Name"></div>
                <div class="col-6"><select class="form-select form-select-sm"><option>W-2 Employee</option><option>1099 Subcontractor</option></select></div>
                <div class="col-12"><button class="btn btn-sm btn-primary fw-bold w-100" onclick="alert('Onboarding Packet Issued!')">Issue Onboarding Documents</button></div>
            </div>
        </div>

        <!-- TAB 3: INVENTORY & CPQ -->
        <div id="erp_inventory" class="erp-section" style="display:none;">
            <h6 class="fw-bold text-primary mb-3"><i class="fa-solid fa-box-open me-1"></i> Parts CPQ Catalog & Supplier Data Sync (Johnstone / Carrier API)</h6>
            <div class="p-3 bg-light rounded-3 border mb-3">
                <span class="fw-bold text-dark small">Live Supplier API Sync Status: <span class="text-success">Connected</span></span>
            </div>
        </div>

        <!-- TAB 4: FINANCIALS -->
        <div id="erp_financials" class="erp-section" style="display:none;">
            <h6 class="fw-bold text-primary mb-3"><i class="fa-solid fa-file-invoice-dollar me-1"></i> Real-Time Profit & Loss (P&L) Ledger</h6>
            <div class="p-3 bg-light rounded-3 border">
                <div class="d-flex justify-content-between mb-1"><span class="fw-bold">Gross Revenue ($99 Dispatches + Repairs):</span><span class="text-success fw-bold">$12,450.00</span></div>
                <div class="d-flex justify-content-between mb-1"><span class="fw-bold">Vendor Parts Costs:</span><span class="text-danger fw-bold">-$4,200.00</span></div>
                <hr>
                <div class="d-flex justify-content-between"><span class="fw-bold fs-6">Net Operating Margin:</span><span class="text-primary fw-bold fs-6">$8,250.00</span></div>
            </div>
        </div>
    </div>

    <script>
        function switchErpTab(tabName) {
            document.querySelectorAll('.erp-section').forEach(s => s.style.display = 'none');
            document.getElementById('erp_' + tabName).style.display = 'block';
        }
    </script>
</body>
</html>"""
    return html.replace('{{HEADER}}', COMMON_HEADER).replace('{{PHOENIX}}', get_phoenix_svg(35, 35))

# ==========================================
# DISPATCH COMMAND CENTER (/admin)
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

    try:
        cursor.execute("SELECT COUNT(*) FROM service_requests WHERE is_backorder = 1")
        backorder_count = cursor.fetchone()[0]
    except Exception:
        backorder_count = 0

    cursor.execute("SELECT SUM(est_value) FROM service_requests WHERE status != 'Completed'")
    total_pipeline_val = cursor.fetchone()[0]
    total_pipeline_val = total_pipeline_val if total_pipeline_val else 0.00

    active_count = pending_count + progress_count

    cursor.execute("SELECT COUNT(*) FROM sms_messages WHERE sender_type = 'Customer' AND is_new = 1")
    new_customer_sms = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sms_messages WHERE sender_type = 'Tech' AND is_new = 1")
    new_tech_sms = cursor.fetchone()[0]

    try:
        cursor.execute("""
            SELECT id, first_name, last_name, customer_name, phone, email, 
                   address, city, zip_code, urgency, equipment, model_number, 
                   serial_number, issue_description, assigned_tech, status, est_value, created_at, is_backorder, backorder_notes 
            FROM service_requests ORDER BY id DESC
        """)
        rows = cursor.fetchall()
    except Exception:
        cursor.execute("""
            SELECT id, first_name, last_name, customer_name, phone, email, 
                   address, city, zip_code, urgency, equipment, model_number, 
                   serial_number, issue_description, assigned_tech, status, est_value, created_at 
            FROM service_requests ORDER BY id DESC
        """)
        raw_rows = cursor.fetchall()
        rows = [r + (0, '') for r in raw_rows]

    cursor.execute("SELECT id, sender_type, sender_name, sender_phone, message_text, timestamp, is_new FROM sms_messages ORDER BY id DESC")
    sms_rows = cursor.fetchall()
    conn.close()

    map_markers = []
    table_rows = ""

    for idx, r in enumerate(rows):
        (req_id, first_name, last_name, old_cust_name, phone, email,
         address, city, zip_code, urgency, equip, model_no,
         serial_no, desc, assigned_tech, status, est_value, created_at, is_backorder, bo_notes) = r
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

        if "Emergency" in urgency or "Dispatch Now" in urgency:
            urgency_bg = "#fee2e2"
            urgency_color = "#dc2626"
            circle_color = "#dc2626"
            is_emergency = True
        elif "Routine" in urgency:
            urgency_bg = "#f0fdf4"
            urgency_color = "#166534"
            circle_color = "#16a34a"

        full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else old_cust_name
        full_name_clean = clean_str(full_name)
        phone_clean = clean_str(phone)
        full_address = f"{address}, {city}, {zip_code}".strip(", ")
        full_address_clean = clean_str(full_address)
        equip_clean = clean_str(equip)
        desc_clean = clean_str(desc)
        assigned_tech_clean = clean_str(assigned_tech)

        contact_info = f"<a href='tel:{phone}' style='color: #0f172a; text-decoration: none; font-weight: 700; white-space: nowrap;' title='Click to Call/Text'>📞 {phone}</a>"
        if email:
            contact_info += f"<br><span style='font-size: 11px; color: #64748b; word-break: break-all;'>{email}</span>"

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
        bo_badge = "<span class='badge bg-warning text-dark ms-1'>Backorder</span>" if is_backorder else ""

        table_rows += f"""
        <tr class="data-row job-row" data-status="{status}" data-backorder="{is_backorder}" style="{initial_display}">
            <td style="width: 35px;"><strong style="color: #64748b;">#{req_id}</strong></td>
            <td style="min-width: 110px;">
                <a href="javascript:void(0);" onclick="openDrawer({req_id}, '{full_name_clean}', '{phone_clean}', '{full_address_clean}', '{equip_clean}', '{desc_clean}', '{assigned_tech_clean}')" style="color: #0f172a; text-decoration: underline; font-weight: 700;">
                    {full_name}
                </a>{bo_badge}<br>
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
        {COMMON_HEADER}
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            {COMMON_ADMIN_CSS}
            .container-admin {{ max-width: 100%; margin: 0 auto; padding: 10px; }}
            .header-admin {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }}
            
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

            .controls-bar {{ display: flex; justify-content: flex-start; align-items: center; margin-bottom: 15px; gap: 10px; flex-wrap: wrap; }}
            .search-input {{ width: 220px; max-width: 220px; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; font-family: inherit; }}
            
            .filter-tabs {{ display: flex; gap: 5px; flex-wrap: wrap; align-items: center; }}
            .tab-btn {{ padding: 6px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; border: 1px solid #cbd5e1; background: #f1f5f9; color: #475569; display: flex; align-items: center; gap: 4px; }}
            .tab-btn.active {{ background: #2563eb; color: #ffffff; border-color: #2563eb; }}
            .tab-sms-cust {{ border-color: #2563eb; color: #2563eb; background: #eff6ff; }}
            .tab-sms-tech {{ border-color: #d97706; color: #b45309; background: #fffbe3; }}
            .tab-backorder {{ border-color: #d97706; color: #d97706; background: #fef3c7; }}

            .table-wrapper {{ overflow-x: auto; width: 100%; }}
            table {{ width: 100%; border-collapse: collapse; table-layout: auto; }}
            th, td {{ padding: 10px 8px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 12px; vertical-align: top; box-sizing: border-box; color: #0f172a; }}
            th {{ background: #f8fafc; color: #64748b; font-weight: 700; text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px; white-space: nowrap; }}
            
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
                if (btn) btn.classList.add('active');
                
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
                    let isBo = r.getAttribute('data-backorder');

                    if (view === 'Backorder') {{
                        r.style.display = (isBo === '1') ? '' : 'none';
                    }} else if (view === 'Active') {{
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
            
            <!-- SHOT #1: BRAND LOGO WITH SUBTITLE & ACTION GROUP -->
            <div class="header-admin">
                <div class="d-flex align-items-center gap-3">
                    <div>
                        <h1 class="brand-logo mb-0">OLMIOS</h1>
                        <!-- SHOT #1 SUBTITLE REQUIREMENT -->
                        <span class="fw-bold text-primary" style="font-size: 0.72rem; letter-spacing: 1px;">Dispatch Command Center</span>
                    </div>
                    <div class="d-flex align-items-center gap-1 ms-2">
                        <a href="/admin/new_customer" class="btn-admin btn-primary-admin"><i class="fa-solid fa-user-plus me-1"></i> + New Customer</a>
                        <a href="/admin/new_request" class="btn-admin btn-accent-admin"><i class="fa-solid fa-bolt me-1"></i> Service Request</a>
                        <button type="button" class="btn-admin btn-outline-admin" data-bs-toggle="modal" data-bs-target="#existingCustomerModal"><i class="fa-solid fa-address-book me-1"></i> Existing Customer</button>
                        <button type="button" class="btn-admin btn-outline-admin" onclick="switchView('Active', document.querySelector('.filter-tabs .tab-btn'))"><i class="fa-solid fa-ticket me-1"></i> Open Service Ticket</button>
                        <button type="button" class="btn-admin btn-outline-admin text-danger border-danger-subtle" data-bs-toggle="modal" data-bs-target="#refundsModal"><i class="fa-solid fa-shield-cat me-1"></i> Refunds/Warranty Pending</button>
                    </div>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <a href="/backoffice" class="btn btn-sm btn-dark fw-bold"><i class="fa-solid fa-building me-1"></i> Enterprise ERP</a>
                    <a href="/tech_home" class="btn btn-sm btn-success fw-bold"><i class="fa-solid fa-mobile-screen-button me-1"></i> Field Tech App</a>
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
                        <input type="text" id="searchInput" class="search-input" onkeyup="searchTable()" placeholder="🔍 Search customer, phone...">
                        
                        <div class="filter-tabs">
                            <button class="tab-btn active" onclick="switchView('Active', this)">Active Jobs ({active_count})</button>
                            <button class="tab-btn tab-sms-cust" onclick="switchView('CustomerSMS', this)">💬 Customer Texts {cust_alert_badge}</button>
                            <button class="tab-btn tab-sms-tech" onclick="switchView('TechSMS', this)">📱 Tech/Driver Texts {tech_alert_badge}</button>
                            <button class="tab-btn tab-backorder" onclick="switchView('Backorder', this)">📦 Backorder ({backorder_count})</button>
                            
                            <span style="color:#cbd5e1; margin:0 1px;">|</span>
                            
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
                    <select id="drawerTechSelect" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: 700; color: #0f172a;">
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

        <!-- EXISTING CUSTOMER HISTORY MODAL -->
        <div class="modal fade" id="existingCustomerModal" tabindex="-1">
            <div class="modal-dialog modal-xl modal-dialog-centered">
                <div class="modal-content rounded-4 border-0">
                    <div class="modal-header bg-dark text-white border-0">
                        <h5 class="modal-title fw-bold"><i class="fa-solid fa-address-book text-primary me-2"></i> Existing Customer History & Lifetime Records</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4 text-dark">
                        <div class="table-responsive">
                            <table class="table table-bordered table-striped align-middle">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Customer Name</th>
                                        <th>Serviced Equipment / Parts</th>
                                        <th>Servicing Tech</th>
                                        <th>Linked Job Photos</th>
                                        <th>Vendor Invoices</th>
                                        <th>Sales History</th>
                                        <th>Card History</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td class="fw-bold">Ian Olvera<br><span class="text-muted small">8323884957</span></td>
                                        <td>Trane Condenser (5TTR6048) + Evaporator Coil (5TXCC007)</td>
                                        <td>Tech A (Lead)</td>
                                        <td><span class="badge bg-primary">📸 3 Photos Linked</span></td>
                                        <td><span class="badge bg-secondary">📄 Johnstone INV-9902</span></td>
                                        <td class="fw-bold text-success">$99.00 Diagnostic + $1,850 Repair</td>
                                        <td>💳 Visa ending in 1004</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- REFUNDS & WARRANTY MANAGER APPROVAL MODAL -->
        <div class="modal fade" id="refundsModal" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content rounded-4 border-0">
                    <div class="modal-header bg-danger text-white border-0">
                        <h5 class="modal-title fw-bold"><i class="fa-solid fa-shield-cat me-2"></i> Refunds & Warranty Pending Manager Approval</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4 text-dark">
                        <div class="alert alert-warning small fw-bold">
                            <i class="fa-solid fa-lock me-1"></i> Manager sign-off is required before finalizing any refund or processing card reversals.
                        </div>
                        <div class="card p-3 border shadow-sm">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="fw-bold text-dark">REFUND REQUEST #1002 — Ian Olvera</span>
                                <span class="badge bg-danger">Pending Manager Approval</span>
                            </div>
                            <p class="small text-muted mb-2">Requested Amount: <strong>$99.00</strong> | Diagnostic Fee Adjustment</p>
                            <div class="d-flex gap-2">
                                <button type="button" class="btn btn-sm btn-success fw-bold w-50" onclick="alert('Refund Approved by Manager & Processed to Card ending 1004.')"><i class="fa-solid fa-check me-1"></i> Manager Approve & Issue Refund</button>
                                <button type="button" class="btn btn-sm btn-outline-danger fw-bold w-50" onclick="alert('Refund Request Declined.')"><i class="fa-solid fa-xmark me-1"></i> Decline Request</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

# ==========================================
# ADMIN ACTIONS & ENDPOINTS
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
