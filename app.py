import json
import smtplib
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from flask import Flask, Response, redirect, request, url_for

app = Flask(__name__)

# ==========================================
# FREE EMAIL-TO-SMS CONFIGURATION
# ==========================================
ENABLE_SMS_ALERTS = False

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "olvera.jose030322@gmail.com"
SENDER_PASSWORD = "your-16-char-app-password"

OWNER_PHONE_GATEWAY = "8323884957@vtext.com"


def send_sms_alert(req_id, customer_name, phone, equipment, urgency):
    if not ENABLE_SMS_ALERTS:
        return

    subject = f"NEW HVAC ORDER #{req_id}"
    body = (
        f"OLMIOS HVAC ALERT #{req_id}\n"
        f"Client: {customer_name}\n"
        f"Phone: {phone}\n"
        f"Type: {equipment}\n"
        f"Urgency: {urgency}"
    )

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = OWNER_PHONE_GATEWAY

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, OWNER_PHONE_GATEWAY, msg.as_string())
        server.quit()
        print(f"[SMS ALERT] Notification sent for Ticket #{req_id}")
    except Exception as e:
        print(f"[SMS ERROR] Could not send alert: {e}")


def get_lat_lng(address_str):
    if not address_str or len(address_str.strip()) < 3:
        return 29.7604, -95.3698

    try:
        url = (
            "https://nominatim.openstreetmap.org/search?format=json&q="
            + urllib.parse.quote(address_str)
        )
        req = urllib.request.Request(
            url, headers={"User-Agent": "OlmiosHVACDispatch/1.0"}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"[GEOCODE NOTICE] Using Houston center for '{address_str}': {e}")

    return 29.7604, -95.3698


def init_db():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT DEFAULT 'John',
            last_name TEXT DEFAULT 'Doe',
            phone TEXT DEFAULT '(832) 388-4957',
            email TEXT DEFAULT 'john.doe@example.com',
            dl_number TEXT DEFAULT 'TX-88492014',
            profile_photo TEXT DEFAULT 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
            primary_address TEXT DEFAULT '3217 Montrose Blvd, Suite 100',
            city TEXT DEFAULT 'Houston',
            zip_code TEXT DEFAULT '77006',
            add_address_2 TEXT DEFAULT '18510 Ranch View Trail, Houston, TX 77073',
            add_address_3 TEXT DEFAULT '',
            sys_type TEXT DEFAULT 'Gas System',
            condenser_mn TEXT DEFAULT '4TTR6036N',
            condenser_sn TEXT DEFAULT '21045XY892',
            coil_mn TEXT DEFAULT '4PXCB004AC',
            coil_sn TEXT DEFAULT '19204AB882',
            furnace_ah_mn TEXT DEFAULT 'S8X1B040M',
            furnace_ah_sn TEXT DEFAULT '24001MN091',
            heatkit_mn TEXT DEFAULT '',
            heatkit_sn TEXT DEFAULT '',
            unit_plate_photo TEXT DEFAULT '',
            fam_first_name TEXT DEFAULT 'Jane',
            fam_last_name TEXT DEFAULT 'Doe',
            fam_relation TEXT DEFAULT 'Spouse',
            fam_phone TEXT DEFAULT '(832) 555-0199',
            is_business INTEGER DEFAULT 0,
            business_name TEXT DEFAULT '',
            manager_name TEXT DEFAULT '',
            manager_phone TEXT DEFAULT '',
            is_tax_exempt INTEGER DEFAULT 0,
            tax_id TEXT DEFAULT '',
            card_1 TEXT DEFAULT 'VISA ending in •••• 4242',
            card_2 TEXT DEFAULT 'Mastercard ending in •••• 8812',
            card_3 TEXT DEFAULT 'AMEX ending in •••• 1004',
            card_4 TEXT DEFAULT '',
            biz_address_1 TEXT DEFAULT '5000 Westheimer Rd, Suite 200, Houston, TX 77056',
            biz_address_2 TEXT DEFAULT ''
        )
    """
    )

    cursor.execute("SELECT COUNT(*) FROM customer_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO customer_profile (
                first_name, last_name, phone, email, primary_address, city, zip_code
            ) VALUES ('John', 'Doe', '(832) 388-4957', 'john.doe@example.com', '3217 Montrose Blvd, Suite 100', 'Houston', '77006')
        """
        )

    cursor.execute(
        """
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
            trade_type TEXT DEFAULT 'Cooling & AC',
            urgency TEXT,
            equipment TEXT NOT NULL,
            model_number TEXT,
            serial_number TEXT,
            issue_description TEXT NOT NULL,
            payment_card TEXT DEFAULT 'VISA •••• 4242',
            card_last4 TEXT DEFAULT '4242',
            po_number TEXT DEFAULT 'PO-99201',
            is_business INTEGER DEFAULT 0,
            is_tax_exempt INTEGER DEFAULT 0,
            tax_id TEXT,
            assigned_tech TEXT DEFAULT 'Unassigned',
            est_value REAL DEFAULT 150.00,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Pending'
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sms_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_type TEXT NOT NULL,
            sender_name TEXT NOT NULL,
            sender_phone TEXT NOT NULL,
            message_text TEXT NOT NULL,
            photo_url TEXT DEFAULT '',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_new INTEGER DEFAULT 1
        )
    """
    )

    conn.commit()
    conn.close()


init_db()

# ==========================================
# ANDROID PWA MANIFEST & META HEADERS
# ==========================================
PWA_HEAD_TAGS = """
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0f172a">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Olmios">
"""

COMMON_CSS = """
    body {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
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
    }
    .brand-logo {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: 4px;
        color: #0f172a;
        text-transform: uppercase;
        margin: 10px 0 0 0;
    }
    .btn {
        display: inline-block;
        padding: 12px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
        border: none;
        cursor: pointer;
        text-align: center;
    }
    .btn-primary {
        background-color: #2563eb;
        color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    .btn-primary:hover { background-color: #1d4ed8; }
    .btn-accent {
        background-color: #d97706;
        color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(217, 119, 6, 0.2);
    }
    .btn-accent:hover { background-color: #b45309; }
    .btn-nav {
        background-color: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
    }
    .btn-nav:hover { background-color: #e2e8f0; color: #1e293b; }
    
    .home-phoenix-btn {
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px;
        border-radius: 10px;
        transition: transform 0.2s ease, background 0.2s ease;
    }
    .home-phoenix-btn:hover {
        transform: scale(1.08);
        background: #f1f5f9;
    }
"""


def get_phoenix_svg(width=120, height=120):
    return f"""
<svg width="{width}" height="{height}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="goldFeathers" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fbbf24" />
            <stop offset="50%" stop-color="#d97706" />
            <stop offset="100%" stop-color="#92400e" />
        </linearGradient>
    </defs>
    <path d="M50 8 C72 8 88 18 88 42 C88 68 50 92 50 92 C50 92 12 68 12 42 C12 18 28 8 50 8 Z" fill="#f8fafc" stroke="#e2e8f0" stroke-width="2"/>
    <path d="M50 22 C52 22 55 24 55 27 C55 30 52 32 50 34 C49 36 49 42 50 50 C51 58 53 68 50 78 C47 68 49 58 50 50 C51 42 51 36 50 34 C48 32 45 30 45 27 C45 24 48 22 50 22 Z" fill="url(#goldFeathers)" />
    <path d="M50 18 L53 23 L50 21 L47 23 Z" fill="#d97706"/>
    <path d="M53 26 L58 28 L54 30 Z" fill="#b45309"/>
    <path d="M48 36 C38 30 26 28 16 34 C24 38 32 40 40 46 C28 46 18 50 14 58 C22 58 32 56 42 58 C32 62 24 68 22 74 C30 72 38 68 46 64 Z" fill="url(#goldFeathers)" />
    <path d="M52 36 C62 30 74 28 84 34 C76 38 68 40 60 46 C72 46 82 50 86 58 C68 62 76 68 78 74 C70 72 62 68 54 64 Z" fill="url(#goldFeathers)" />
    <path d="M50 70 L44 86 L50 82 L56 86 Z" fill="url(#goldFeathers)"/>
</svg>
"""


def calculate_age(created_at_str):
    if not created_at_str:
        return "Just now", False
    try:
        created_time = datetime.strptime(
            created_at_str[:19], "%Y-%m-%d %H:%M:%S"
        )
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
# ANDROID MANIFEST JSON ROUTE
# ==========================================
@app.route("/manifest.json")
def manifest():
    manifest_data = {
        "short_name": "Olmios",
        "name": "Olmios",
        "icons": [
            {
                "src": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=512",
                "type": "image/png",
                "sizes": "512x512",
            }
        ],
        "start_url": "/customer_home",
        "background_color": "#0f172a",
        "theme_color": "#0f172a",
        "display": "standalone",
        "orientation": "portrait",
    }
    return Response(json.dumps(manifest_data), mimetype="application/json")

@app.route("/")
def home():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Olmios Technologies</title>
        {PWA_HEAD_TAGS}
        <style>
            {COMMON_CSS}
            .container {{ display: flex; justify-content: center; align-items: center; min-height: 80vh; }}
            .card {{ padding: 45px 40px; text-align: center; max-width: 440px; width: 100%; }}
            p {{ color: #64748b; font-size: 13px; margin: 6px 0 30px; letter-spacing: 1.5px; font-weight: 600; }}
            .actions {{ display: flex; flex-direction: column; gap: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="panel card">
                <a href="/" class="home-phoenix-btn" title="Olmios Technologies Home">
                    {get_phoenix_svg(120, 120)}
                </a>
                <h1 class="brand-logo">OLMIOS</h1>
                <p>TECHNOLOGIES DISPATCH</p>
                <div class="actions">
                    <a href="/customer_home" class="btn btn-accent">📲 CUSTOMER MOBILE HOME & MAP</a>
                    <a href="/tech_app" class="btn btn-primary" style="background-color: #059669;">🚚 TECH / DRIVER MOBILE APP</a>
                    <a href="/admin" class="btn btn-primary">💻 DISPATCH COMMAND CENTER</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/customer_home")
def customer_home():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customer_profile WHERE id = 1")
    profile = cursor.fetchone()

    cursor.execute(
        "SELECT id, assigned_tech, status, equipment, address, city, urgency FROM service_requests WHERE status != 'Completed' ORDER BY id DESC LIMIT 1"
    )
    active_req = cursor.fetchone()

    chat_html = ""
    if active_req:
        req_id = active_req[0]
        cursor.execute(
            "SELECT sender_type, sender_name, message_text, timestamp FROM sms_messages ORDER BY id ASC"
        )
        msgs = cursor.fetchall()
        for m in msgs:
            stype, sname, mtext, tstamp = m
            bg = "#e0f2fe" if stype == "Customer" else "#f1f5f9"
            align = "flex-end" if stype == "Customer" else "flex-start"
            chat_html += f"""
            <div style="display:flex; justify-content:{align}; margin-bottom:8px;">
                <div style="background:{bg}; color:#0f172a; padding:8px 12px; border-radius:12px; max-width:80%; font-size:12px;">
                    <div style="font-weight:700; font-size:10px; color:#64748b;">{sname} • {tstamp[11:16]}</div>
                    {mtext}
                </div>
            </div>
            """

    conn.close()

    zip_code_shapes = [
        {
            "zip": "77032",
            "area_name": "Aldine / Greenspoint Area",
            "color": "#dc2626",
            "coords": [
                [29.965, -95.420],
                [29.972, -95.365],
                [29.950, -95.315],
                [29.905, -95.320],
                [29.902, -95.385],
                [29.925, -95.425],
            ],
            "status": "🚨 HIGH DEMAND / EMERGENCY ZONE",
        },
        {
            "zip": "77006",
            "area_name": "Montrose / Neartown Houston",
            "color": "#16a34a",
            "coords": [
                [29.758, -95.405],
                [29.755, -95.378],
                [29.728, -95.375],
                [29.725, -95.395],
                [29.738, -95.408],
            ],
            "status": "🟢 ACTIVE TECH COVERAGE AVAILABLE",
        },
        {
            "zip": "77073",
            "area_name": "Westfield / North Houston",
            "color": "#0284c7",
            "coords": [
                [30.055, -95.435],
                [30.062, -95.372],
                [30.008, -95.360],
                [29.998, -95.418],
                [30.020, -95.442],
            ],
            "status": "🔵 STANDARD SERVICE COVERAGE ZONE",
        },
    ]

    active_ticket_card = ""
    if active_req:
        r_id, r_tech, r_status, r_equip, r_addr, r_city, r_urgency = active_req
        tech_photo = (
            "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150"
            if r_tech != "Unassigned"
            else "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"
        )

        active_ticket_card = f"""
        <div style="background: #ffffff; color: #0f172a; border-radius: 12px; padding: 18px; margin-bottom: 20px; border: 2px solid #2563eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
                <span style="font-size:12px; font-weight:800; color:#2563eb;">ACTIVE ORDER #{r_id}</span>
                <span style="background:#dbeafe; color:#1d4ed8; padding:3px 8px; border-radius:12px; font-size:10px; font-weight:800;">{r_status.upper()}</span>
            </div>
            
            <div style="display:flex; gap:12px; align-items:center; margin-bottom: 12px;">
                <img src="{tech_photo}" style="width:48px; height:48px; border-radius:50%; object-fit:cover; border:2px solid #cbd5e1;">
                <div>
                    <div style="font-size:14px; font-weight:800; color:#0f172a;">Assigned Tech: {r_tech}</div>
                    <div style="font-size:11px; color:#64748b;">Licensed Master HVAC Specialist</div>
                </div>
            </div>

            <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:10px; max-height:160px; overflow-y:auto; margin-bottom:10px;">
                {chat_html if chat_html else '<div style="font-size:11px; color:#94a3b8; text-align:center;">No messages yet. Send a note or photo to your tech below.</div>'}
            </div>

            <form action="/customer_send_msg/{r_id}" method="POST" style="display:flex; gap:6px;">
                <input type="text" name="msg_text" placeholder="Send note or upload photo..." required style="flex:1; padding:8px; border-radius:6px; border:1px solid #cbd5e1; font-size:12px;">
                <button type="submit" class="btn btn-primary" style="padding:8px 12px; font-size:12px;">SEND</button>
            </form>
        </div>
        """

    profile_pic = profile[6] if profile[6] else "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Olmios Technologies</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {PWA_HEAD_TAGS}
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            {COMMON_CSS}
            body {{ padding: 15px; max-width: 480px; margin: 0 auto; }}
            .app-top-bar {{ display: flex; justify-content: space-between; align-items: center; background: #ffffff; padding: 12px 16px; border-radius: 12px; color: #0f172a; margin-bottom: 15px; }}
            .profile-avatar {{ width: 42px; height: 42px; border-radius: 50%; object-fit: cover; border: 2px solid #2563eb; }}
            
            .trust-badge-bottom {{
                background: linear-gradient(135deg, #059669 0%, #047857 100%);
                color: #ffffff;
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 10px;
                font-weight: 700;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                margin-top: 15px;
                width: 100%;
                box-sizing: border-box;
                box-shadow: 0 2px 4px rgba(0,0,0,0.15);
            }}

            #fieldMap {{ height: 260px; width: 100%; border-radius: 12px; margin-bottom: 12px; border: 1px solid #cbd5e1; }}
            .nav-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }}
            
            .zone-legend {{ display: flex; justify-content: space-around; font-size: 10px; font-weight: 800; color: #475569; margin-top: 6px; }}
            .zone-item {{ display: flex; align-items: center; gap: 4px; }}
            .zone-box {{ width: 12px; height: 12px; border-radius: 3px; opacity: 0.8; }}
            
            .star-rating-pill {{
                background: #fffbe3;
                color: #b45309;
                border: 1px solid #fde68a;
                font-size: 10px;
                font-weight: 800;
                padding: 2px 6px;
                border-radius: 10px;
                display: inline-flex;
                align-items: center;
                gap: 3px;
                margin-top: 2px;
            }}
        </style>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            const zipZones = {json.dumps(zip_code_shapes)};
            window.onload = function() {{
                let map = L.map('fieldMap').setView([29.8500, -95.3800], 10);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 18 }}).addTo(map);

                zipZones.forEach(z => {{
                    let poly = L.polygon(z.coords, {{
                        color: '#ffffff',
                        fillColor: z.color,
                        fillOpacity: 0.40,
                        weight: 2,
                        dashArray: '3, 3'
                    }}).addTo(map);

                    poly.bindPopup(`
                        <div style="font-size:12px; font-family:inherit;">
                            <strong>Zip Code ${{z.zip}}</strong><br>
                            <span style="color:#64748b;">${{z.area_name}}</span><br>
                            ${{z.status}}
                        </div>
                    `);
                }});
            }};
        </script>
    </head>
    <body>
        <div class="app-top-bar">
            <div style="display:flex; align-items:center; gap:10px;">
                <a href="/customer_profile">
                    <img src="{profile_pic}" class="profile-avatar" title="View Profile & Wallet">
                </a>
                <div>
                    <div style="font-size: 10px; color: #64748b; font-weight: 800;">WELCOME BACK</div>
                    <div style="font-size: 15px; font-weight: 800; color: #0f172a;">{profile[1]} {profile[2]}</div>
                    <div class="star-rating-pill">
                        ⭐⭐⭐⭐⭐ 4.9 (1,250+ Verified Reviews)
                    </div>
                </div>
            </div>
            <a href="/" class="home-phoenix-btn">
                {get_phoenix_svg(36, 36)}
            </a>
        </div>

        <div style="background:#ffffff; border-radius:12px; padding:12px; color:#0f172a; margin-bottom:15px; border:1px solid #cbd5e1;">
            <div style="font-size:11px; font-weight:800; color:#64748b; margin-bottom:6px;">LIVE ACTIVE FIELD TECHNICIAN COVERAGE BY ZIP CODE</div>
            <div id="fieldMap"></div>
            
            <div class="zone-legend">
                <span class="zone-item"><span class="zone-box" style="background:#dc2626;"></span> Emergency Zip</span>
                <span class="zone-item"><span class="zone-box" style="background:#0284c7;"></span> Standard Zip</span>
                <span class="zone-item"><span class="zone-box" style="background:#16a34a;"></span> Active Tech Zip</span>
            </div>
        </div>

        {active_ticket_card}

        <a href="/quote" class="btn btn-accent" style="width:100%; box-sizing:border-box; padding:14px; font-size:14px; font-weight:800;">
            ⚡ REQUEST INSTANT HVAC SERVICE
        </a>

        <div class="nav-grid">
            <a href="/customer_profile" class="btn btn-nav" style="box-sizing:border-box; padding:10px; font-size:11px;">
                👤 Profile & Wallet
            </a>
            <a href="/customer_invoices" class="btn btn-nav" style="box-sizing:border-box; padding:10px; font-size:11px; color:#2563eb; border-color:#2563eb;">
                🧾 View Invoices
            </a>
        </div>

        <div class="trust-badge-bottom">
            <span>🛡️</span> VERIFIED OLMIOS GUARANTEE • 100% Licensed, Insured & Background-Checked
        </div>
    </body>
    </html>
    """


@app.route("/customer_send_msg/<int:req_id>", methods=["POST"])
def customer_send_msg(req_id):
    msg_text = request.form.get("msg_text", "")
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sms_messages (sender_type, sender_name, sender_phone, message_text, is_new)
        VALUES ('Customer', 'John Doe', '8323884957', ?, 1)
    """,
        (f"Ticket #{req_id}: {msg_text}",),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("customer_home"))


@app.route("/customer_profile", methods=["GET", "POST"])
def customer_profile():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        dl_number = request.form.get("dl_number")
        profile_photo = request.form.get("profile_photo")
        primary_address = request.form.get("primary_address")
        city = request.form.get("city")
        zip_code = request.form.get("zip_code")
        add_address_2 = request.form.get("add_address_2")
        add_address_3 = request.form.get("add_address_3")

        sys_type = request.form.get("sys_type", "Gas System")
        condenser_mn = request.form.get("condenser_mn", "")
        condenser_sn = request.form.get("condenser_sn", "")
        coil_mn = request.form.get("coil_mn", "")
        coil_sn = request.form.get("coil_sn", "")
        furnace_ah_mn = request.form.get("furnace_ah_mn", "")
        furnace_ah_sn = request.form.get("furnace_ah_sn", "")
        heatkit_mn = request.form.get("heatkit_mn", "")
        heatkit_sn = request.form.get("heatkit_sn", "")
        unit_plate_photo = request.form.get("unit_plate_photo", "")

        fam_first_name = request.form.get("fam_first_name")
        fam_last_name = request.form.get("fam_last_name")
        fam_relation = request.form.get("fam_relation")
        fam_phone = request.form.get("fam_phone")

        is_business = 1 if request.form.get("is_business") == "1" else 0
        business_name = request.form.get("business_name", "")
        manager_name = request.form.get("manager_name", "")
        manager_phone = request.form.get("manager_phone", "")
        is_tax_exempt = 1 if request.form.get("is_tax_exempt") == "1" else 0
        tax_id = request.form.get("tax_id", "")
        biz_address_1 = request.form.get("biz_address_1", "")
        biz_address_2 = request.form.get("biz_address_2", "")

        cursor.execute(
            """
            UPDATE customer_profile SET
                first_name = ?, last_name = ?, phone = ?, email = ?, dl_number = ?, profile_photo = ?,
                primary_address = ?, city = ?, zip_code = ?, add_address_2 = ?, add_address_3 = ?,
                sys_type = ?, condenser_mn = ?, condenser_sn = ?, coil_mn = ?, coil_sn = ?,
                furnace_ah_mn = ?, furnace_ah_sn = ?, heatkit_mn = ?, heatkit_sn = ?, unit_plate_photo = ?,
                fam_first_name = ?, fam_last_name = ?, fam_relation = ?, fam_phone = ?,
                is_business = ?, business_name = ?, manager_name = ?, manager_phone = ?,
                is_tax_exempt = ?, tax_id = ?, biz_address_1 = ?, biz_address_2 = ?
            WHERE id = 1
        """,
            (
                first_name,
                last_name,
                phone,
                email,
                dl_number,
                profile_photo,
                primary_address,
                city,
                zip_code,
                add_address_2,
                add_address_3,
                sys_type,
                condenser_mn,
                condenser_sn,
                coil_mn,
                coil_sn,
                furnace_ah_mn,
                furnace_ah_sn,
                heatkit_mn,
                heatkit_sn,
                unit_plate_photo,
                fam_first_name,
                fam_last_name,
                fam_relation,
                fam_phone,
                is_business,
                business_name,
                manager_name,
                manager_phone,
                is_tax_exempt,
                tax_id,
                biz_address_1,
                biz_address_2,
            ),
        )
        conn.commit()

    cursor.execute("SELECT * FROM customer_profile WHERE id = 1")
    p = cursor.fetchone()
    conn.close()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Olmios Technologies | Profile</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {PWA_HEAD_TAGS}
        <style>
            {COMMON_CSS}
            body {{ padding: 15px; max-width: 500px; margin: 0 auto; }}
            .section-box {{ background: #ffffff; color: #0f172a; border-radius: 12px; padding: 20px; margin-bottom: 15px; border: 1px solid #cbd5e1; position: relative; }}
            label {{ display: block; font-weight: 700; margin-top: 10px; color: #475569; font-size: 11px; text-transform: uppercase; }}
            input, select {{ width: 100%; padding: 8px 10px; margin-top: 4px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 13px; box-sizing: border-box; }}
            
            .add-address-btn {{
                background: #f1f5f9;
                color: #2563eb;
                border: 1px dashed #2563eb;
                width: 100%;
                padding: 10px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 12px;
                cursor: pointer;
                margin-top: 12px;
            }}
            .card-slot-row {{ display: flex; align-items: center; gap: 8px; margin-top: 6px; }}
            .card-del-btn {{ background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; padding: 8px 12px; border-radius: 6px; font-weight: 700; font-size: 11px; cursor: pointer; white-space: nowrap; }}
            .card-del-btn:hover {{ background: #fca5a5; color: #7f1d1d; }}

            .footer-actions {{ display: flex; justify-content: space-between; align-items: center; margin-top: 25px; gap: 10px; }}
            .btn-delete-profile {{ background: #dc2626; color: #ffffff; font-weight: 800; font-size: 12px; padding: 12px; border-radius: 8px; text-decoration: none; border: none; cursor: pointer; }}
            .btn-delete-profile:hover {{ background: #b91c1c; }}
        </style>
        <script>
            function addAddressField() {{
                document.getElementById('extraAddressBox').style.display = 'block';
            }}
            function addBizAddressField() {{
                document.getElementById('extraBizAddressBox').style.display = 'block';
            }}
            function toggleSystemType() {{
                let sys = document.getElementById('sysTypeSelect').value;
                let isGas = sys === 'Gas System';
                document.getElementById('gasLabel').innerText = isGas ? 'Furnace Model Number' : 'Air Handler Model Number';
                document.getElementById('heatkitBox').style.display = isGas ? 'none' : 'block';
            }}
        </script>
    </head>
    <body>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; color:#ffffff;">
            <h2>👤 Customer Profile & Wallet</h2>
            <a href="/customer_home" class="home-phoenix-btn">{get_phoenix_svg(40, 40)}</a>
        </div>

        <form method="POST">
            <div class="section-box">
                <h3 style="margin-top:0; font-size:14px; color:#2563eb;">1. Basic Personal Information & Residence</h3>
                
                <div style="display:flex; gap:12px; align-items:center; margin-bottom:12px;">
                    <img src="{p[6]}" style="width:54px; height:54px; border-radius:50%; object-fit:cover; border:2px solid #2563eb;">
                    <div style="flex:1;">
                        <label style="margin:0;">Profile Picture URL</label>
                        <input type="text" name="profile_photo" value="{p[6]}">
                    </div>
                </div>

                <div style="display:flex; gap:10px;">
                    <div style="flex:1;"><label>First Name</label><input type="text" name="first_name" value="{p[1]}"></div>
                    <div style="flex:1;"><label>Last Name</label><input type="text" name="last_name" value="{p[2]}"></div>
                </div>
                <label>Phone Number</label><input type="text" name="phone" value="{p[3]}">
                <label>Email Address</label><input type="email" name="email" value="{p[4]}">
                
                <label style="color:#2563eb;">Driver's License / State ID #</label>
                <input type="text" name="dl_number" value="{p[5] if len(p)>5 and p[5] else ''}">

                <hr style="border:0; border-top:1px solid #e2e8f0; margin:15px 0;">
                <h4 style="margin:0; font-size:12px; color:#0f172a;">Primary Residence Address</h4>
                <label>Street Address</label><input type="text" name="primary_address" value="{p[7]}">
                <div style="display:flex; gap:10px;">
                    <div style="flex:2;"><label>City</label><input type="text" name="city" value="{p[8]}"></div>
                    <div style="flex:1;"><label>Zip Code</label><input type="text" name="zip_code" value="{p[9]}"></div>
                </div>

                <label>Additional Property Address #2</label>
                <input type="text" name="add_address_2" value="{p[10]}">

                <div id="extraAddressBox" style="display: {'block' if p[11] else 'none'}; margin-top:10px;">
                    <label>Additional Property Address #3</label>
                    <input type="text" name="add_address_3" value="{p[11] if p[11] else ''}">
                </div>

                <button type="button" class="add-address-btn" onclick="addAddressField()">
                    ➕ Add Additional Property Address
                </button>

                <hr style="border:0; border-top:1px solid #e2e8f0; margin:15px 0;">
                <h4 style="margin:0; font-size:12px; color:#0f172a;">Authorized Family Contact</h4>
                <div style="display:flex; gap:10px;">
                    <div style="flex:1;"><label>First Name</label><input type="text" name="fam_first_name" value="{p[21] if len(p)>21 and p[21] else 'Jane'}"></div>
                    <div style="flex:1;"><label>Last Name</label><input type="text" name="fam_last_name" value="{p[22] if len(p)>22 and p[22] else 'Doe'}"></div>
                </div>
                <div style="display:flex; gap:10px;">
                    <div style="flex:1;"><label>Relation</label><input type="text" name="fam_relation" value="{p[23] if len(p)>23 and p[23] else 'Spouse'}"></div>
                    <div style="flex:1;"><label>Phone</label><input type="text" name="fam_phone" value="{p[24] if len(p)>24 and p[24] else '(832) 555-0199'}"></div>
                </div>
            </div>

            <div class="section-box">
                <h3 style="margin-top:0; font-size:14px; color:#2563eb;">2. HVAC System Equipment & Data Plate Specs</h3>
                
                <label>System Heating Type</label>
                <select name="sys_type" id="sysTypeSelect" onchange="toggleSystemType()">
                    <option value="Gas System" {'selected' if len(p)>12 and p[12]=='Gas System' else ''}>🔥 Gas Heating System (Condenser, Coil, Furnace)</option>
                    <option value="Electric System" {'selected' if len(p)>12 and p[12]=='Electric System' else ''}>⚡ Electric Heating System (Condenser, Air Handler, Heat Kit)</option>
                </select>

                <div style="display:flex; gap:10px; margin-top:10px;">
                    <div style="flex:1;"><label>Condenser Model #</label><input type="text" name="condenser_mn" value="{p[13] if len(p)>13 and p[13] else '4TTR6036N'}"></div>
                    <div style="flex:1;"><label>Condenser Serial #</label><input type="text" name="condenser_sn" value="{p[14] if len(p)>14 and p[14] else '21045XY892'}"></div>
                </div>

                <div style="display:flex; gap:10px; margin-top:6px;">
                    <div style="flex:1;"><label>Evaporator Coil Model #</label><input type="text" name="coil_mn" value="{p[15] if len(p)>15 and p[15] else '4PXCB004AC'}"></div>
                    <div style="flex:1;"><label>Coil Serial #</label><input type="text" name="coil_sn" value="{p[16] if len(p)>16 and p[16] else '19204AB882'}"></div>
                </div>

                <div style="display:flex; gap:10px; margin-top:6px;">
                    <div style="flex:1;"><label id="gasLabel">Furnace Model Number</label><input type="text" name="furnace_ah_mn" value="{p[17] if len(p)>17 and p[17] else 'S8X1B040M'}"></div>
                    <div style="flex:1;"><label>Furnace / AH Serial #</label><input type="text" name="furnace_ah_sn" value="{p[18] if len(p)>18 and p[18] else '24001MN091'}"></div>
                </div>

                <div id="heatkitBox" style="display: {'block' if len(p)>12 and p[12]=='Electric System' else 'none'}; margin-top:6px;">
                    <div style="display:flex; gap:10px;">
                        <div style="flex:1;"><label>Electric Heat Kit Model #</label><input type="text" name="heatkit_mn" value="{p[19] if len(p)>19 and p[19] else 'BAYHTR1510'}"></div>
                        <div style="flex:1;"><label>Heat Kit Serial #</label><input type="text" name="heatkit_sn" value="{p[20] if len(p)>20 and p[20] else 'HK-99201'}"></div>
                    </div>
                </div>

                <label style="color:#059669;">📸 Unit Rating Plate Photo URL</label>
                <input type="text" name="unit_plate_photo" value="{p[20] if len(p)>20 and p[20] else ''}" placeholder="Upload or paste image URL of equipment tag">
            </div>

            <div class="section-box">
                <h3 style="margin-top:0; font-size:14px; color:#d97706;">3. Commercial Business Account</h3>
                <label>Do you own a business?</label>
                <select name="is_business">
                    <option value="0" {'selected' if p[25]==0 else ''}>No (Residential Only)</option>
                    <option value="1" {'selected' if p[25]==1 else ''}>Yes (Commercial Account)</option>
                </select>
                <label>Business Name</label><input type="text" name="business_name" value="{p[26] if len(p)>26 else ''}">
                <label>Contact Manager Name</label><input type="text" name="manager_name" value="{p[27] if len(p)>27 else ''}">
                <label>Manager Phone Number</label><input type="text" name="manager_phone" value="{p[28] if len(p)>28 else ''}">
                
                <label>Tax Exempt Status</label>
                <select name="is_tax_exempt">
                    <option value="0" {'selected' if len(p)>29 and p[29]==0 else ''}>No (Standard Tax)</option>
                    <option value="1" {'selected' if len(p)>29 and p[29]==1 else ''}>Yes (Tax Exempt Account)</option>
                </select>
                <label>Tax Exemption Certificate / ID #</label><input type="text" name="tax_id" value="{p[30] if len(p)>30 else ''}">

                <hr style="border:0; border-top:1px solid #e2e8f0; margin:15px 0 10px 0;">
                <h4 style="margin:0; font-size:12px; color:#0f172a;">Commercial Property Addresses</h4>
                <label>Primary Business Location Address</label>
                <input type="text" name="biz_address_1" value="{p[35] if len(p)>35 and p[35] else ''}" placeholder="5000 Westheimer Rd, Suite 200, Houston, TX 77056">

                <div id="extraBizAddressBox" style="display: {'block' if len(p)>36 and p[36] else 'none'}; margin-top:10px;">
                    <label>Additional Commercial Property #2</label>
                    <input type="text" name="biz_address_2" value="{p[36] if len(p)>36 and p[36] else ''}">
                </div>

                <button type="button" class="add-address-btn" style="color:#d97706; border-color:#d97706;" onclick="addBizAddressField()">
                    ➕ Add Additional Commercial Property
                </button>
            </div>

            <div class="section-box">
                <h3 style="margin-top:0; font-size:14px; color:#059669;">4. Saved Cards Wallet (Up to 4 Cards)</h3>
                
                <label>Card 1 (Primary)</label>
                <div class="card-slot-row">
                    <input type="text" value="{p[31] if len(p)>31 else 'VISA •••• 4242'}" readonly style="background:#f1f5f9;">
                    <a href="/delete_card/1" onclick="return confirm('Remove Card 1?');" class="card-del-btn">🗑️ Delete</a>
                </div>

                <label>Card 2</label>
                <div class="card-slot-row">
                    <input type="text" value="{p[32] if len(p)>32 else 'Mastercard •••• 8812'}" readonly style="background:#f1f5f9;">
                    <a href="/delete_card/2" onclick="return confirm('Remove Card 2?');" class="card-del-btn">🗑️ Delete</a>
                </div>

                <label>Card 3</label>
                <div class="card-slot-row">
                    <input type="text" value="{p[33] if len(p)>33 else 'AMEX •••• 1004'}" readonly style="background:#f1f5f9;">
                    <a href="/delete_card/3" onclick="return confirm('Remove Card 3?');" class="card-del-btn">🗑️ Delete</a>
                </div>

                <label>Card 4</label>
                <div class="card-slot-row">
                    <input type="text" value="{p[34] if len(p)>34 and p[34] else 'Empty Slot'}" readonly style="background:#f1f5f9;">
                    <a href="/delete_card/4" onclick="return confirm('Remove Card 4?');" class="card-del-btn">🗑️ Delete</a>
                </div>
            </div>

            <button type="submit" class="btn btn-primary" style="width:100%; padding:14px; font-size:14px;">💾 SAVE PROFILE & WALLET</button>
            
            <div class="footer-actions">
                <a href="/customer_home" class="btn btn-nav" style="padding:10px 20px;">Home Page</a>
                <a href="/delete_profile" onclick="return confirm('ARE YOU SURE? This will permanently delete your user profile and all stored cards.');" class="btn-delete-profile">
                    🗑️ DELETE PROFILE
                </a>
            </div>
        </form>
    </body>
    </html>
    """


@app.route("/customer_invoices")
def customer_invoices():
    card_filter = request.args.get("card_filter", "")
    date_filter = request.args.get("date_filter", "")
    po_filter = request.args.get("po_filter", "").strip().lower()
    amount_filter = request.args.get("amount_filter", "")

    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()

    query = "SELECT id, trade_type, equipment, address, est_value, payment_card, card_last4, po_number, created_at, status FROM service_requests WHERE status = 'Completed'"
    params = []

    if card_filter:
        query += " AND card_last4 = ?"
        params.append(card_filter)
    if date_filter:
        query += " AND created_at LIKE ?"
        params.append(f"{date_filter}%")
    if po_filter:
        query += " AND LOWER(po_number) LIKE ?"
        params.append(f"%{po_filter}%")
    if amount_filter:
        if amount_filter == "100-200":
            query += " AND est_value BETWEEN 100 AND 200"
        elif amount_filter == "200-400":
            query += " AND est_value BETWEEN 200 AND 400"
        elif amount_filter == "400+":
            query += " AND est_value >= 400"

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    invoices = cursor.fetchall()
    conn.close()

    invoice_rows = ""
    for inv in invoices:
        i_id, trade, equip, addr, val, card, last4, po, date_str, status = inv
        date_formatted = date_str[:10] if date_str else "2026-08-01"

        invoice_rows += f"""
        <div style="background:#ffffff; color:#0f172a; border-radius:12px; padding:16px; margin-bottom:12px; border:1px solid #cbd5e1;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:13px; font-weight:800; color:#2563eb;">INVOICE #{i_id}</span>
                <span style="font-size:14px; font-weight:800; color:#16a34a;">${val:,.2f}</span>
            </div>
            
            <div style="font-size:12px; color:#475569; line-height:1.5; margin-bottom:12px;">
                <strong>Date:</strong> {date_formatted}<br>
                <strong>PO #:</strong> {po if po else 'N/A'}<br>
                <strong>Card Used:</strong> {card}<br>
                <strong>Location:</strong> {addr}
            </div>

            <div style="display:flex; gap:6px; flex-wrap:wrap;">
                <a href="/print_invoice/{i_id}?mode=itemized" target="_blank" class="btn btn-primary" style="padding:6px 10px; font-size:10px;">🖨️ Print Itemized Cost</a>
                <a href="/print_invoice/{i_id}?mode=total" target="_blank" class="btn btn-accent" style="padding:6px 10px; font-size:10px;">🖨️ Print Total Only</a>
                <a href="/print_invoice/{i_id}?mode=nopricing" target="_blank" class="btn btn-nav" style="padding:6px 10px; font-size:10px;">🖨️ Print (No Pricing)</a>
            </div>
        </div>
        """

    if not invoice_rows:
        invoice_rows = "<div style='background:#ffffff; color:#64748b; padding:30px; text-align:center; border-radius:12px;'>No matching completed invoices found.</div>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Olmios Technologies | Invoices</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {PWA_HEAD_TAGS}
        <style>
            {COMMON_CSS}
            body {{ padding: 15px; max-width: 520px; margin: 0 auto; }}
            .filter-card {{ background:#ffffff; color:#0f172a; padding:15px; border-radius:12px; margin-bottom:15px; border:1px solid #cbd5e1; }}
            label {{ font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase; display:block; margin-top:8px; }}
            input, select {{ width:100%; padding:8px; margin-top:2px; border-radius:6px; border:1px solid #cbd5e1; font-size:12px; box-sizing:border-box; }}
        </style>
    </head>
    <body>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; color:#ffffff;">
            <h2>🧾 Service Invoices</h2>
            <a href="/customer_home" class="home-phoenix-btn">{get_phoenix_svg(40, 40)}</a>
        </div>

        <div class="filter-card">
            <div style="font-size:12px; font-weight:800; color:#0f172a; margin-bottom:6px;">🔍 FILTER INVOICE HISTORY</div>
            <form method="GET" action="/customer_invoices">
                <div style="display:flex; gap:8px;">
                    <div style="flex:1;">
                        <label>Last 4 Digits of Card</label>
                        <select name="card_filter">
                            <option value="">All Cards</option>
                            <option value="4242" {'selected' if card_filter=='4242' else ''}>•••• 4242</option>
                            <option value="8812" {'selected' if card_filter=='8812' else ''}>•••• 8812</option>
                            <option value="1004" {'selected' if card_filter=='1004' else ''}>•••• 1004</option>
                        </select>
                    </div>
                    <div style="flex:1;">
                        <label>Amount Range</label>
                        <select name="amount_filter">
                            <option value="">All Amounts</option>
                            <option value="100-200" {'selected' if amount_filter=='100-200' else ''}>$100 - $200</option>
                            <option value="200-400" {'selected' if amount_filter=='200-400' else ''}>$200 - $400</option>
                            <option value="400+" {'selected' if amount_filter=='400+' else ''}>$400+</option>
                        </select>
                    </div>
                </div>

                <div style="display:flex; gap:8px; margin-top:6px;">
                    <div style="flex:1;">
                        <label>PO Number</label>
                        <input type="text" name="po_filter" value="{po_filter}" placeholder="e.g. PO-1002">
                    </div>
                    <div style="flex:1;">
                        <label>Service Date</label>
                        <input type="date" name="date_filter" value="{date_filter}">
                    </div>
                </div>

                <div style="display:flex; gap:8px; margin-top:12px;">
                    <button type="submit" class="btn btn-primary" style="flex:1; padding:8px; font-size:11px;">APPLY FILTERS</button>
                    <a href="/customer_invoices" class="btn btn-nav" style="padding:8px 12px; font-size:11px;">RESET</a>
                </div>
            </form>
        </div>

        {invoice_rows}

        <a href="/customer_home" class="btn btn-nav" style="width:100%; box-sizing:border-box; margin-top:10px;">Home Page</a>
    </body>
    </html>
    """


@app.route("/print_invoice/<int:inv_id>")
def print_invoice(inv_id):
    mode = request.args.get("mode", "itemized")
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM service_requests WHERE id = ?", (inv_id,)
    )
    inv = cursor.fetchone()
    conn.close()

    if not inv:
        return "Invoice not found."

    req_id, fn, ln, cust_name, phone, email, addr, city, zip_c, trade, urgency, equip, model_no, serial_no, desc, card, last4, po, is_biz, is_exempt, tax_id, tech, val, created_at, status = inv

    tax_amount = 0.00 if is_exempt else (val * 0.0825)
    total_due = val + tax_amount

    pricing_section = f"""
    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
        <thead>
            <tr style="background:#f1f5f9; border-bottom:2px solid #0f172a;">
                <th style="text-align:left; padding:8px;">Service Item / Labor</th>
                <th style="text-align:right; padding:8px;">Cost</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="padding:10px; border-bottom:1px solid #e2e8f0;">HVAC Diagnostic & Service Fee ({trade})</td>
                <td style="text-align:right; padding:10px; border-bottom:1px solid #e2e8f0;">${val - 35.00:,.2f}</td>
            </tr>
            <tr>
                <td style="padding:10px; border-bottom:1px solid #e2e8f0;">System Component Test & Inspection</td>
                <td style="text-align:right; padding:10px; border-bottom:1px solid #e2e8f0;">$35.00</td>
            </tr>
            <tr>
                <td style="padding:10px; text-align:right;"><strong>Subtotal:</strong></td>
                <td style="padding:10px; text-align:right;">${val:,.2f}</td>
            </tr>
            <tr>
                <td style="padding:10px; text-align:right;"><strong>State Tax (8.25%):</strong></td>
                <td style="padding:10px; text-align:right;">{'$0.00 (TAX EXEMPT)' if is_exempt else f'${tax_amount:,.2f}'}</td>
            </tr>
            <tr style="font-size:16px; font-weight:800;">
                <td style="padding:10px; text-align:right; border-top:2px solid #0f172a;">Total Paid ({card}):</td>
                <td style="padding:10px; text-align:right; border-top:2px solid #0f172a; color:#16a34a;">${total_due if not is_exempt else val:,.2f}</td>
            </tr>
        </tbody>
    </table>
    """

    if mode == "total":
        pricing_section = f"""
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:20px; margin-top:20px; text-align:right;">
            <div style="font-size:13px; color:#64748b;">Grand Total Paid ({card}):</div>
            <div style="font-size:26px; font-weight:800; color:#16a34a; margin-top:4px;">${total_due if not is_exempt else val:,.2f}</div>
            <div style="font-size:10px; color:#64748b; margin-top:4px;">Includes all labor, components, and state tax.</div>
        </div>
        """
    elif mode == "nopricing":
        pricing_section = """
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:15px; margin-top:20px; text-align:center; font-weight:700; color:#475569;">
            ✓ PROOF OF SERVICE RECEIPT — NO PRICING DISPLAYED
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>INVOICE #{inv_id} | OLMIOS TECHNOLOGIES</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; padding: 40px; color: #0f172a; max-width: 800px; margin: 0 auto; background: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0f172a; padding-bottom: 15px; }}
            .brand {{ font-size: 24px; font-weight: 800; letter-spacing: 2px; }}
            .grid {{ display: flex; gap: 20px; margin: 25px 0; }}
            .box {{ flex: 1; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; font-size: 13px; line-height: 1.6; }}
            .box-title {{ font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
            .no-print {{ margin-bottom: 20px; text-align: right; }}
        </style>
    </head>
    <body>
        <div class="no-print">
            <button onclick="window.print()" style="padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: 700; cursor: pointer;">🖨️ PRINT INVOICE</button>
        </div>

        <div class="header">
            <div style="display:flex; align-items:center; gap: 10px;">
                {get_phoenix_svg(48, 48)}
                <div>
                    <div class="brand">OLMIOS TECHNOLOGIES</div>
                    <div style="font-size: 11px; color: #64748b; font-weight: 700;">ON-DEMAND DISPATCH PLATFORM</div>
                </div>
            </div>
            <div style="text-align:right;">
                <h2 style="margin: 0; color: #2563eb;">PAID SERVICE INVOICE</h2>
                <div style="font-size: 13px; font-weight: 700;">INVOICE #{inv_id}</div>
                <div style="font-size: 11px; color: #64748b;">Date: {created_at[:10]}</div>
            </div>
        </div>

        <div class="grid">
            <div class="box">
                <div class="box-title">Customer & Property Info</div>
                <strong>{cust_name}</strong><br>
                📞 {phone}<br>
                📍 {addr}, {city}, {zip_c}<br>
                {f'<strong>Tax ID / Cert:</strong> {tax_id}' if is_exempt else ''}
            </div>
            <div class="box">
                <div class="box-title">Payment & Dispatch Info</div>
                <strong>PO Number:</strong> {po if po else 'N/A'}<br>
                <strong>Payment Method:</strong> {card}<br>
                <strong>Assigned Tech:</strong> {tech}<br>
                <strong>Trade:</strong> {trade}
            </div>
        </div>

        <div class="box">
            <div class="box-title">Work Completed & Equipment</div>
            <strong>System:</strong> {equip}<br>
            <strong>Service Summary:</strong> {desc}
        </div>

        {pricing_section}
    </body>
    </html>
    """


@app.route("/quote", methods=["GET", "POST"])
def quote():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer_profile WHERE id = 1")
    p = cursor.fetchone()

    if request.method == "POST":
        customer_name = f"{p[1]} {p[2]}".strip()
        phone = p[3]
        email = p[4]
        address = request.form.get("address_select")
        city = p[8]
        zip_code = p[9]
        trade_type = request.form.get("trade_type", "Cooling & AC")
        urgency = request.form.get("urgency", "Standard Service")
        equipment = request.form.get("equipment")
        model_number = p[13] if len(p) > 13 and p[13] else "4TTR6036N"
        serial_number = p[14] if len(p) > 14 and p[14] else "21045XY892"
        issue_description = request.form.get("issue_description")
        payment_card = request.form.get("payment_card")
        po_number = request.form.get("po_number", "PO-90214")

        card_last4 = payment_card[-4:] if len(payment_card) >= 4 else "4242"
        est_val = 250.00 if "Emergency" in urgency else 150.00

        cursor.execute(
            """
            INSERT INTO service_requests (
                first_name, last_name, customer_name, phone, email,
                address, city, zip_code, trade_type, urgency, equipment,
                model_number, serial_number, issue_description, payment_card, card_last4, po_number,
                is_business, is_tax_exempt, tax_id,
                assigned_tech, est_value, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Unassigned', ?, 'Pending')
        """,
            (
                p[1],
                p[2],
                customer_name,
                phone,
                email,
                address,
                city,
                zip_code,
                trade_type,
                urgency,
                equipment,
                model_number,
                serial_number,
                issue_description,
                payment_card,
                card_last4,
                po_number,
                p[25],
                p[29],
                p[30],
                est_val,
            ),
        )
        req_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO sms_messages (sender_type, sender_name, sender_phone, message_text, is_new)
            VALUES ('Customer', ?, ?, ?, 1)
        """,
            (
                customer_name,
                phone,
                f"New Paid {trade_type} Order #{req_id}: {issue_description}",
            ),
        )

        conn.commit()
        conn.close()

        send_sms_alert(req_id, customer_name, phone, equipment, urgency)

        return redirect(url_for("confirmation", req_id=req_id))

    saved_condenser_mn = p[13] if len(p) > 13 and p[13] else "4TTR6036N"
    saved_condenser_sn = p[14] if len(p) > 14 and p[14] else "21045XY892"
    saved_furnace_mn = p[17] if len(p) > 17 and p[17] else "S8X1B040M"
    conn.close()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Olmios Technologies | Request Service</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {PWA_HEAD_TAGS}
        <style>
            {COMMON_CSS}
            .container {{ display: flex; justify-content: center; }}
            .card {{ padding: 30px; max-width: 580px; width: 100%; }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            h2 {{ margin: 0; color: #0f172a; font-size: 20px; font-weight: 700; }}
            
            .uber-tabs {{ display: flex; background: #f1f5f9; border-radius: 12px; padding: 4px; margin-bottom: 20px; gap: 4px; }}
            .uber-tab {{ flex: 1; text-align: center; padding: 10px 6px; border-radius: 8px; font-size: 11px; font-weight: 700; color: #64748b; cursor: pointer; user-select: none; }}
            .uber-tab.active {{ background: #ffffff; color: #0f172a; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }}

            label {{ display: block; font-weight: 600; margin-top: 15px; color: #475569; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .optional-tag {{ font-size: 10px; color: #94a3b8; font-weight: normal; text-transform: none; margin-left: 4px; }}
            input, textarea, select {{ width: 100%; padding: 10px 12px; margin-top: 6px; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; color: #0f172a; box-sizing: border-box; font-size: 14px; font-family: inherit; }}
            .prefilled-badge {{ background: #dcfce7; color: #166534; padding: 10px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; margin-bottom: 15px; }}
            
            .ai-conversation-box {{
                background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
                border: 2px solid #2563eb;
                border-radius: 12px;
                padding: 16px;
                margin-top: 15px;
            }}
            .ai-header {{ font-size: 14px; font-weight: 800; color: #1d4ed8; display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
        </style>
        <script>
            const hvacCategories = {{
                'Cooling & AC': [
                    'AC Condenser',
                    'Air Handler Unit',
                    'Mini-Split Heat Pump',
                    'Evaporator Coil',
                    'Commercial Rooftop Unit (RTU)',
                    'VRF Multi-Split System',
                    'Commercial PTAC Unit',
                    'Wall Pack Unit'
                ],
                'Heating & Furnaces': [
                    'Gas Furnace',
                    'Electric Heat Strip Assembly',
                    'Dual-Fuel Heat Pump',
                    'Hydronic / Hot Water Boiler',
                    'Commercial Suspended Gas Heater'
                ],
                'Maintenance & IAQ': [
                    'Filter Replacement & Tune-up',
                    'Ductwork Inspection & Cleaning',
                    'Thermostat / BMS Control Sensor',
                    'Condensate Drain Line Flush',
                    'Coil Wash & Sanitization'
                ]
            }};

            function selectTrade(categoryName, element) {{
                document.querySelectorAll('.uber-tab').forEach(t => t.classList.remove('active'));
                element.classList.add('active');
                document.getElementById('tradeTypeInput').value = categoryName;

                let selectEl = document.getElementById('equipSelect');
                selectEl.innerHTML = '<option value="" disabled selected>Select HVAC Equipment...</option>';

                hvacCategories[categoryName].forEach(item => {{
                    let opt = document.createElement('option');
                    opt.value = item;
                    opt.innerText = item;
                    selectEl.appendChild(opt);
                }});
            }}

            function syncChatToSummary() {{
                let chatText = document.getElementById('ai_chat_input').value;
                let savedCondenser = "{saved_condenser_mn}";
                let savedSerial = "{saved_condenser_sn}";
                let savedFurnace = "{saved_furnace_mn}";

                let fullSummary = chatText + " | [SAVED PROFILE SPECS]: Condenser M/N: " + savedCondenser + " (S/N: " + savedSerial + "), Furnace M/N: " + savedFurnace;
                document.getElementById('issue_desc').value = fullSummary;
                alert('✓ Chat notes & saved profile equipment specs auto-filled below for technician!');
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="panel card">
                <div class="card-header">
                    <h2>Instant HVAC Dispatch Request</h2>
                    <a href="/customer_home" class="home-phoenix-btn">{get_phoenix_svg(42, 42)}</a>
                </div>

                <div class="prefilled-badge">
                    ✓ Profile Verified: {p[1]} {p[2]} ({p[3]})
                </div>

                <div class="uber-tabs">
                    <div class="uber-tab active" onclick="selectTrade('Cooling & AC', this)">❄️ Cooling & AC</div>
                    <div class="uber-tab" onclick="selectTrade('Heating & Furnaces', this)">🔥 Heating</div>
                    <div class="uber-tab" onclick="selectTrade('Maintenance & IAQ', this)">🧹 Maintenance</div>
                </div>

                <form method="POST">
                    <input type="hidden" name="trade_type" id="tradeTypeInput" value="Cooling & AC">

                    <label>Select Job Site Property Address</label>
                    <select name="address_select" required>
                        <option value="{p[7]}">📍 Primary Residential: {p[7]}</option>
                        <option value="{p[10]}">📍 Secondary: {p[10]}</option>
                        <option value="{p[35] if len(p)>35 and p[35] else 'Commercial'}">🏢 Commercial Location: {p[35] if len(p)>35 and p[35] else 'Business'}</option>
                    </select>

                    <label>Purchase Order (PO) # <span class="optional-tag">(Optional)</span></label>
                    <input type="text" name="po_number" placeholder="e.g. PO-88204">

                    <label>Service Urgency</label>
                    <select name="urgency" required>
                        <option value="" disabled selected>Select Urgency Level...</option>
                        <option value="Emergency">🚨 Emergency (No Cooling / Water Leak)</option>
                        <option value="Standard Service">⚙️ Standard Service (Blowing warm, noise)</option>
                        <option value="Routine Maintenance">🧹 Routine Maintenance / Inspection</option>
                    </select>

                    <label>Equipment Type (Includes Residential & Commercial)</label>
                    <select name="equipment" id="equipSelect" required>
                        <option value="" disabled selected>Select HVAC Equipment...</option>
                        <option value="AC Condenser">AC Condenser</option>
                        <option value="Air Handler Unit">Air Handler Unit</option>
                        <option value="Mini-Split Heat Pump">Mini-Split Heat Pump</option>
                        <option value="Evaporator Coil">Evaporator Coil</option>
                        <option value="Commercial Rooftop Unit (RTU)">Commercial Rooftop Unit (RTU)</option>
                        <option value="VRF Multi-Split System">VRF Multi-Split System</option>
                        <option value="Commercial PTAC Unit">Commercial PTAC Unit</option>
                        <option value="Wall Pack Unit">Wall Pack Unit</option>
                    </select>

                    <div class="ai-conversation-box">
                        <div class="ai-header">
                            {get_phoenix_svg(28, 28)}
                            <span>OLMIOS Diagnostic Chat Assistant</span>
                        </div>
                        
                        <p style="font-size:12px; color:#334155; margin:0 0 8px 0; line-height:1.4;">
                            Tell us what's going on! Mention symptoms, specific defective part notes, or paste image URLs:
                        </p>

                        <textarea id="ai_chat_input" rows="4" placeholder="e.g., Fan motor is humming and unit is blowing warm air. Defective capacitor photo: https://example.com/cap.jpg"></textarea>

                        <button type="button" onclick="syncChatToSummary()" class="btn btn-primary" style="width:100%; margin-top:8px; font-size:11px; padding:8px;">
                            ✨ AUTO-FILL ISSUE DESCRIPTION
                        </button>
                    </div>

                    <label>Issue Description (Final Dispatch Summary)</label>
                    <textarea name="issue_description" id="issue_desc" rows="3" placeholder="Describe requested HVAC issue or click Auto-Fill above..." required></textarea>

                    <label>Select Saved Payment Card</label>
                    <select name="payment_card" required>
                        <option value="{p[31] if len(p)>31 else 'VISA •••• 4242'}">💳 {p[31] if len(p)>31 else 'VISA •••• 4242'}</option>
                        <option value="{p[32] if len(p)>32 else 'Mastercard •••• 8812'}">💳 {p[32] if len(p)>32 else 'Mastercard •••• 8812'}</option>
                        <option value="{p[33] if len(p)>33 else 'AMEX •••• 1004'}">💳 {p[33] if len(p)>33 else 'AMEX •••• 1004'}</option>
                    </select>

                    <button type="submit" class="btn btn-accent submit-btn" style="padding:16px; font-size:15px; font-weight:800; margin-bottom:15px;">
                        💳 💳 Request Service & Dispatch Tech
                    </button>
                </form>

                <div style="margin-top: 10px;">
                    <a href="/customer_home" class="btn btn-nav" style="display:inline-block; padding:10px 24px;">Home Page</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/confirmation/<int:req_id>")
def confirmation(req_id):
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT first_name, last_name, customer_name, phone, address, city, zip_code, urgency, equipment, status, is_tax_exempt, trade_type, payment_card 
        FROM service_requests WHERE id = ?
    """,
        (req_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return redirect(url_for("customer_home"))

    (
        first_name,
        last_name,
        old_cust_name,
        phone,
        address,
        city,
        zip_code,
        urgency,
        equip,
        status,
        is_tax_exempt,
        trade_type,
        card,
    ) = row
    full_name = (
        f"{first_name} {last_name}".strip()
        if (first_name or last_name)
        else old_cust_name
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Olmios Technologies | Request Received</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {PWA_HEAD_TAGS}
        <style>
            {COMMON_CSS}
            .container {{ display: flex; justify-content: center; align-items: center; min-height: 85vh; }}
            .card {{ padding: 35px; max-width: 480px; width: 100%; text-align: center; position: relative; }}
            .success-icon {{ width: 64px; height: 64px; background: #dcfce7; color: #166534; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; margin: 0 auto 15px; }}
            h2 {{ margin: 0; color: #0f172a; font-size: 24px; font-weight: 800; }}
            .summary-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: left; margin: 20px 0; }}
            .summary-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 13px; }}
            .summary-row:last-child {{ border-bottom: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="panel card">
                <div class="success-icon">✓</div>
                <h2>Added to Dispatch Queue!</h2>
                <p style="color:#64748b; font-size:13px;">Payment authorized via <strong>{card}</strong>. A tech is en route.</p>

                <div class="summary-box">
                    <div class="summary-row"><span>Ticket Number:</span><strong style="color:#2563eb;">#{req_id}</strong></div>
                    <div class="summary-row"><span>Trade Category:</span><strong>{trade_type}</strong></div>
                    <div class="summary-row"><span>Location:</span><strong>{address}</strong></div>
                </div>

                <a href="/customer_home" class="btn btn-accent" style="width:100%; box-sizing:border-box;">Home Page</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/tech_app")
def tech_app():
    tech_name = request.args.get("tech", "Tech A (Lead)")
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, customer_name, phone, address, city, zip_code, urgency, equipment, issue_description, status, created_at, trade_type
        FROM service_requests 
        WHERE assigned_tech = ? AND status != 'Completed'
        ORDER BY id DESC
    """,
        (tech_name,),
    )
    assigned_jobs = cursor.fetchall()
    conn.close()

    jobs_html = ""
    for job in assigned_jobs:
        (
            j_id,
            cust,
            phone,
            addr,
            city,
            zip_code,
            urgency,
            equip,
            desc,
            status,
            created_at,
            trade_type,
        ) = job
        full_addr = f"{addr}, {city}, {zip_code}".strip(", ")
        maps_url = f"https://maps.google.com/?q={urllib.parse.quote(full_addr)}"

        jobs_html += f"""
        <div style="background: #ffffff; color: #0f172a; border-radius: 12px; padding: 20px; margin-bottom: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
                <span style="font-size:12px; font-weight:800; color:#2563eb;">HVAC ORDER #{j_id} ({trade_type if trade_type else 'Cooling'})</span>
                <span style="background:#dbeafe; color:#1d4ed8; padding:3px 8px; border-radius:12px; font-size:10px; font-weight:800;">{status.upper()}</span>
            </div>
            <h3 style="margin:0 0 4px; font-size:16px;">{cust}</h3>
            <div style="font-size:13px; color:#64748b; margin-bottom:12px;">📞 <a href="tel:{phone}" style="color:#0f172a; font-weight:700; text-decoration:none;">{phone}</a></div>
            
            <div style="background:#f8fafc; padding:10px; border-radius:8px; font-size:12px; margin-bottom:12px; line-height:1.4;">
                <strong>📍 Location:</strong> {full_addr}<br>
                <strong>⚙️ Equip:</strong> {equip}<br>
                <strong>📝 Notes & Saved Specs:</strong> {desc}
            </div>

            <div style="display:flex; gap:8px;">
                <a href="{maps_url}" target="_blank" class="btn btn-primary" style="flex:1; padding:10px; font-size:12px;">🗺️ NAVIGATE MAPS</a>
                <a href="/tech_update_status/{j_id}?tech={tech_name}" class="btn btn-accent" style="flex:1; padding:10px; font-size:12px;">✓ COMPLETE JOB</a>
            </div>
        </div>
        """

    if not jobs_html:
        jobs_html = "<div style='background:#ffffff; color:#64748b; padding:30px; text-align:center; border-radius:12px;'>No active HVAC jobs assigned to you right now.</div>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Olmios Technologies | Tech App</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {PWA_HEAD_TAGS}
        <style>
            {COMMON_CSS}
            body {{ padding: 15px; max-width: 480px; margin: 0 auto; }}
            .app-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: #ffffff; padding: 15px; border-radius: 12px; color: #0f172a; }}
        </style>
    </head>
    <body>
        <div class="app-header">
            <div>
                <div style="font-size: 11px; color: #64748b; font-weight: 800;">FIELD TECH APP</div>
                <div style="font-size: 18px; font-weight: 800; color: #0f172a;">{tech_name}</div>
            </div>
            <a href="/" class="home-phoenix-btn">{get_phoenix_svg(40, 40)}</a>
        </div>

        <div style="margin-bottom: 15px;">
            <form method="GET" action="/tech_app" style="display:flex; gap:8px;">
                <select name="tech" onchange="this.form.submit()" style="width:100%; padding:10px; border-radius:8px; font-weight:700;">
                    <option value="Tech A (Lead)" {'selected' if tech_name=='Tech A (Lead)' else ''}>Tech A (Lead Driver)</option>
                    <option value="Tech B" {'selected' if tech_name=='Tech B' else ''}>Tech B (HVAC Tech)</option>
                    <option value="Tech C" {'selected' if tech_name=='Tech C' else ''}>Tech C (Field Tech)</option>
                </select>
            </form>
        </div>

        {jobs_html}
    </body>
    </html>
    """


@app.route("/tech_update_status/<int:req_id>")
def tech_update_status(req_id):
    tech_name = request.args.get("tech", "Tech A (Lead)")
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE service_requests SET status = 'Completed' WHERE id = ?",
        (req_id,),
    )
    cursor.execute(
        """
        INSERT INTO sms_messages (sender_type, sender_name, sender_phone, message_text, is_new)
        VALUES ('Tech', ?, '8325550199', ?, 1)
    """,
        (tech_name, f"HVAC Order #{req_id} marked COMPLETED by technician."),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("tech_app", tech=tech_name))


@app.route("/admin")
def admin():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM service_requests")
    total_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM service_requests WHERE status = 'Pending' OR status IS NULL"
    )
    pending_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM service_requests WHERE status = 'In Progress'"
    )
    progress_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM service_requests WHERE status = 'Completed'"
    )
    completed_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT SUM(est_value) FROM service_requests WHERE status != 'Completed'"
    )
    total_pipeline_val = cursor.fetchone()[0]
    total_pipeline_val = (
        total_pipeline_val if total_pipeline_val else 0.00
    )

    active_count = pending_count + progress_count

    cursor.execute(
        "SELECT COUNT(*) FROM sms_messages WHERE sender_type = 'Customer' AND is_new = 1"
    )
    new_customer_sms = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM sms_messages WHERE sender_type = 'Tech' AND is_new = 1"
    )
    new_tech_sms = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT id, first_name, last_name, customer_name, phone, email, 
               address, city, zip_code, urgency, equipment, model_number, 
               serial_number, issue_description, assigned_tech, status, est_value, created_at, is_tax_exempt, trade_type 
        FROM service_requests ORDER BY id DESC
    """
    )
    rows = cursor.fetchall()

    cursor.execute(
        "SELECT id, sender_type, sender_name, sender_phone, message_text, timestamp, is_new FROM sms_messages ORDER BY id DESC"
    )
    sms_rows = cursor.fetchall()
    conn.close()

    map_markers = []
    table_rows = ""

    for idx, r in enumerate(rows):
        (
            req_id,
            first_name,
            last_name,
            old_cust_name,
            phone,
            email,
            address,
            city,
            zip_code,
            urgency,
            equip,
            model_no,
            serial_no,
            desc,
            assigned_tech,
            status,
            est_value,
            created_at,
            is_tax_exempt,
            trade_type,
        ) = r
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

        full_name = (
            f"{first_name} {last_name}".strip()
            if (first_name or last_name)
            else old_cust_name
        )

        tax_tag = (
            "<br><span style='background:#dcfce7; color:#15803d; padding:1px 4px; border-radius:4px; font-size:9px; font-weight:800;'>TAX EXEMPT</span>"
            if is_tax_exempt
            else ""
        )

        contact_info = (
            f"<a href='tel:{phone}' style='color: #0f172a; text-decoration: none; font-weight: 700; white-space: nowrap;' title='Click to Call/Text'>"
            f"📞 {phone}</a>"
        )
        if email:
            contact_info += f"<br><span style='font-size: 11px; color: #64748b; word-break: break-all;'>{email}</span>"

        full_address = f"{address}, {city}, {zip_code}".strip(", ")

        if status != "Completed" and address:
            lat, lng = get_lat_lng(full_address)
            map_markers.append(
                {
                    "id": req_id,
                    "name": full_name,
                    "address": full_address,
                    "lat": lat,
                    "lng": lng,
                    "color": circle_color,
                    "urgency": urgency,
                    "equipment": equip,
                    "is_emergency": is_emergency,
                }
            )

        if address:
            location_info = f"<a href='javascript:void(0);' onclick=\"focusMap('{req_id}')\" style='color: #2563eb; text-decoration: none; font-weight: 600; line-height: 1.3; display: inline-block;' title='Focus on Map'>📍 {address}</a>"
            if city or zip_code:
                location_info += f"<br><span style='font-size: 11px; color: #64748b;'>{city}, {zip_code}</span>"
        else:
            location_info = "<em>No address provided</em>"

        trade_badge = f"<span style='background:#e2e8f0; color:#0f172a; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:800;'>{trade_type if trade_type else 'Cooling & AC'}</span>"

        specs_info = f"{trade_badge}<br><span style='background: #f1f5f9; color: #334155; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; margin-top:3px;'>{equip}</span>"
        if model_no or serial_no:
            specs_info += "<br><div style='font-size: 10px; color: #64748b; margin-top: 4px; line-height: 1.2;'>"
            if model_no:
                specs_info += f"<strong>M/N:</strong> {model_no}<br>"
            if serial_no:
                specs_info += f"<strong>S/N:</strong> {serial_no}"
            specs_info += "</div>"

        tech_options = ["Unassigned", "Tech A (Lead)", "Tech B", "Tech C"]
        tech_select = f"<form action='/assign_tech/{req_id}' method='POST' style='margin:0;'><select name='tech' onchange='this.form.submit()' style='padding:4px; font-size:11px; border-radius:6px; border:1px solid #cbd5e1; background:#f8fafc; font-weight:600; color:#334155; max-width: 100%;'>"
        for t in tech_options:
            selected = "selected" if t == assigned_tech else ""
            tech_select += f"<option value='{t}' {selected}>{t}</option>"
        tech_select += "</select></form>"

        initial_display = "display: none;" if status == "Completed" else ""

        age_badge_color = (
            "background: #fee2e2; color: #dc2626;"
            if (is_urgent_age and status == "Pending")
            else "background: #f1f5f9; color: #64748b;"
        )

        table_rows += f"""
        <tr class="data-row job-row" data-status="{status}" style="{initial_display}">
            <td style="width: 35px;"><strong style="color: #64748b;">#{req_id}</strong></td>
            <td style="min-width: 110px;">
                <a href="javascript:void(0);" onclick="openDrawer('{req_id}', '{full_name}', '{phone}', '{full_address}', '{equip}', '{desc}', '{assigned_tech}')" style="color: #0f172a; text-decoration: underline; font-weight: 700;">
                    {full_name}
                </a>{tax_tag}<br>
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
                <a href="/print_invoice/{req_id}?mode=itemized" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 700; font-size: 11px; margin-right: 6px;" title="Print Invoice">📄 Invoice</a>
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

        if sender_type == "Customer":
            customer_sms_html += row_content
        else:
            tech_sms_html += row_content

    if not customer_sms_html:
        customer_sms_html = "<div style='color: #64748b; font-size: 13px; padding: 20px; text-align: center;'>No customer text messages.</div>"
    if not tech_sms_html:
        tech_sms_html = "<div style='color: #64748b; font-size: 13px; padding: 20px; text-align: center;'>No technician/driver text messages.</div>"

    cust_alert_badge = (
        f"<span class='alert-pill'>{new_customer_sms} NEW</span>"
        if new_customer_sms > 0
        else ""
    )
    tech_alert_badge = (
        f"<span class='alert-pill'>{new_tech_sms} NEW</span>"
        if new_tech_sms > 0
        else ""
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Olmios Technologies | Command Center</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            {COMMON_CSS}
            .container {{ max-width: 100%; margin: 0 auto; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            
            .kpi-grid {{ display: flex; gap: 12px; margin-bottom: 20px; }}
            .kpi-card {{ flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; }}
            .kpi-title {{ font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
            .kpi-val {{ font-size: 22px; font-weight: 800; color: #0f172a; margin-top: 2px; }}

            .split-container {{ display: flex; gap: 20px; align-items: flex-start; }}
            .left-pane {{ flex: 3; min-width: 0; background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid #e2e8f0; }}
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
            
            .alert-pill {{ background: #dc2626; color: #ffffff; padding: 1px 6px; border-radius: 10px; font-size: 9px; font-weight: 800; }}

            .table-wrapper {{ overflow-x: auto; width: 100%; }}
            table {{ width: 100%; border-collapse: collapse; table-layout: auto; }}
            th, td {{ padding: 10px 8px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 12px; vertical-align: top; box-sizing: border-box; }}
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
                        <div style="font-family: inherit; font-size: 12px;">
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
        <div class="panel container">
            <div class="header">
                <div>
                    <h1 class="brand-logo" style="font-size: 22px; margin: 0;">OLMIOS</h1>
                    <span style="color: #64748b; font-size: 12px; letter-spacing: 0.5px; font-weight: 600;">TECHNOLOGIES COMMAND CENTER</span>
                </div>
                <div class="nav-actions">
                    <a href="/quote" class="btn btn-primary">+ NEW ORDER</a>
                    <a href="/" class="home-phoenix-btn" title="Return to Portal Home">
                        {get_phoenix_svg(46, 46)}
                    </a>
                </div>
            </div>

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

            <div class="split-container">
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
                                        <th>HVAC & Equipment</th>
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

                    <div id="customerSmsPanel" class="view-panel">
                        <h3 style="margin: 0 0 15px; font-size: 15px; color: #0f172a;">💬 Customer Text Messages</h3>
                        {customer_sms_html}
                    </div>

                    <div id="techSmsPanel" class="view-panel">
                        <h3 style="margin: 0 0 15px; font-size: 15px; color: #0f172a;">📱 Field Tech & Driver Messages</h3>
                        {tech_sms_html}
                    </div>

                </div>

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
                <a id="drawerSmsBtn" href="#" onclick="handleDispatchAccept()" class="btn btn-accent" style="box-sizing: border-box; display: block; font-size: 13px;">
                    📱 DISPATCH & SMS TO TECH
                </a>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/accept_and_dispatch/<int:req_id>", methods=["POST"])
def accept_and_dispatch(req_id):
    tech = request.form.get("tech", "Tech A (Lead)")
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE service_requests SET assigned_tech = ?, status = 'In Progress' WHERE id = ?",
        (tech, req_id),
    )

    cursor.execute(
        """
        INSERT INTO sms_messages (sender_type, sender_name, sender_phone, message_text, is_new)
        VALUES ('Tech', ?, '8325550199', ?, 1)
    """,
        (tech, f"Accepted HVAC Order #{req_id} & En Route to Job Site"),
    )

    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


@app.route("/assign_tech/<int:req_id>", methods=["POST"])
def assign_tech(req_id):
    tech = request.form.get("tech")
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE service_requests SET assigned_tech = ? WHERE id = ?",
        (tech, req_id),
    )
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

        cursor.execute(
            "UPDATE service_requests SET status = ? WHERE id = ?",
            (next_status, req_id),
        )
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


if __name__ == "__main__":
    from waitress import serve

    print("🚀 Olmios Technologies server active on http://0.0.0.0:5000")
    serve(app, host="0.0.0.0", port=5000)