import os
from flask import Flask, render_template_string, request, redirect, url_for, jsonify

app = Flask(__name__)

def get_phoenix_svg(width=120, height=120):
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
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
    <path d="M52 36 C62 30 74 28 84 34 C76 38 68 40 60 46 C72 46 82 50 86 58 C68 58 68 56 58 58 C68 62 76 68 78 74 C70 72 62 68 54 64 Z" fill="url(#goldFeathers)" />
    <path d="M50 70 L44 86 L50 82 L56 86 Z" fill="url(#goldFeathers)"/>
</svg>"""

COMMON_HEADER = f"""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800;900&display=swap" rel="stylesheet">
"""

# --- 1. SIGN IN / REGISTER GATEWAY ('/') ---
@app.route('/')
def index():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Customer Portal</title>
    {COMMON_HEADER}
    <style>
        body {{ background-color: #0b1329; color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 20px; }}
        .auth-card {{ background: #162038; border: 1px solid #2a3756; border-radius: 24px; padding: 32px 28px; width: 100%; max-width: 420px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); text-align: center; }}
        .brand-title {{ font-size: 2.6rem; font-weight: 900; letter-spacing: 6px; background: linear-gradient(135deg, #ffffff 30%, #fbbf24 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase; margin-top: 10px; margin-bottom: 6px; }}
        .hero-badge {{ display: inline-block; background: rgba(217, 119, 6, 0.18); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); padding: 6px 16px; border-radius: 50px; font-weight: 700; font-size: 0.82rem; letter-spacing: 0.5px; margin-bottom: 24px; }}
        .nav-pills {{ background: #0b1329; padding: 5px; border-radius: 14px; border: 1px solid #2a3756; }}
        .nav-pills .nav-link {{ color: #94a3b8; border-radius: 10px; font-weight: 800; font-size: 0.95rem; transition: all 0.2s ease; }}
        .nav-pills .nav-link.active {{ background: #3b82f6; color: white; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }}
        .form-label {{ color: #ffffff !important; font-weight: 800; font-size: 0.8rem; letter-spacing: 1px; display: block; text-align: left; margin-bottom: 6px; }}
        .form-control {{ height: 48px; border-radius: 12px; font-weight: 600; border: 1px solid #334155; font-size: 0.95rem; background: #ffffff; color: #0f172a; }}
        .btn-amber {{ background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 800; font-size: 1.05rem; height: 50px; border-radius: 12px; box-shadow: 0 10px 20px -5px rgba(217, 119, 6, 0.5); }}
    </style>
</head>
<body>
    <div class="auth-card">
        {get_phoenix_svg(130, 130)}
        <div class="brand-title">OLMIOS</div>
        <div class="hero-badge"><i class="fa-solid fa-bolt me-1"></i> On-Demand HVAC Techs at Your Door</div>

        <ul class="nav nav-pills nav-justified mb-4">
            <li class="nav-item"><button class="nav-link active py-2.5" id="tab-login" onclick="toggleAuth('login')">Sign In</button></li>
            <li class="nav-item"><button class="nav-link py-2.5" id="tab-register" onclick="toggleAuth('register')">Register</button></li>
        </ul>

        <div id="form-login">
            <div class="mb-3">
                <label class="form-label"><i class="fa-solid fa-envelope me-1"></i> USERNAME / EMAIL</label>
                <input type="text" class="form-control" placeholder="Enter username or email">
            </div>
            <div class="mb-4">
                <label class="form-label"><i class="fa-solid fa-lock me-1"></i> PASSWORD</label>
                <input type="password" class="form-control" placeholder="Enter password">
            </div>
            <a href="/customer_home" class="btn btn-amber w-100 d-flex align-items-center justify-content-center">Access Dashboard</a>
        </div>

        <div id="form-register" style="display: none;">
            <div class="mb-2">
                <label class="form-label"><i class="fa-solid fa-user me-1"></i> FULL NAME</label>
                <input type="text" class="form-control" placeholder="Enter full name">
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
                <input type="text" class="form-control" placeholder="Enter street address, city, state">
            </div>
            <a href="/customer_home" class="btn btn-amber w-100 d-flex align-items-center justify-content-center">Create Account & Continue</a>
        </div>
    </div>

    <script>
    function toggleAuth(mode) {{
        if(mode === 'login') {{
            document.getElementById('form-login').style.display = 'block';
            document.getElementById('form-register').style.display = 'none';
            document.getElementById('tab-login').className = 'nav-link active py-2.5';
            document.getElementById('tab-register').className = 'nav-link py-2.5';
        }} else {{
            document.getElementById('form-login').style.display = 'none';
            document.getElementById('form-register').style.display = 'block';
            document.getElementById('tab-login').className = 'nav-link py-2.5';
            document.getElementById('tab-register').className = 'nav-link active py-2.5';
        }}
    }}
    </script>
</body>
</html>"""

# --- 2. MAIN CUSTOMER DASHBOARD ('/customer_home') ---
@app.route('/customer_home')
def customer_home():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Customer Home</title>
    {COMMON_HEADER}
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {{ background-color: #0b1329; color: white; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }}
        .main-card {{ background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
        #map {{ height: 260px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #cbd5e1; }}
        .btn-amber {{ background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 800; }}
        .btn-amber:hover {{ background: #b45309; color: white; }}
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <div class="d-flex align-items-center gap-2">
                <img id="home_avatar" src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80" style="width: 45px; height: 45px; border-radius: 50%; object-fit: cover;">
                <div>
                    <h6 class="fw-bold mb-0 text-muted small">WELCOME BACK</h6>
                    <span class="fw-bold text-dark fs-6">Customer Account</span>
                </div>
            </div>
            {get_phoenix_svg(45, 45)}
        </div>

        <div class="bg-light p-2 rounded-3 text-center mb-3 border">
            <span class="fw-bold text-dark fs-6"><i class="fa-solid fa-star text-warning"></i> <i class="fa-solid fa-star text-warning"></i> <i class="fa-solid fa-star text-warning"></i> <i class="fa-solid fa-star text-warning"></i> <i class="fa-solid fa-star text-warning"></i> 4.9</span>
        </div>

        <h6 class="fw-bold text-muted small text-center mb-2"><i class="fa-solid fa-map-location-dot me-1"></i> LIVE ACTIVE FIELD TECHNICIAN COVERAGE BY ZIP CODE</h6>
        <div id="map"></div>

        <a href="/dispatch_request" class="btn btn-amber w-100 py-3 rounded-3 fw-bold fs-6 mb-2">
            <i class="fa-solid fa-bolt me-1"></i> REQUEST INSTANT HVAC SERVICE
        </a>
        
        <div class="row g-2 mb-2">
            <div class="col-6"><a href="/profile" class="btn btn-outline-secondary w-100 py-2 fw-bold small"><i class="fa-solid fa-id-card me-1"></i> Profile & Wallet</a></div>
            <div class="col-6"><a href="/invoices" class="btn btn-outline-secondary w-100 py-2 fw-bold small"><i class="fa-solid fa-file-invoice-dollar me-1"></i> View Invoices</a></div>
        </div>

        <div class="text-center bg-success text-white py-2 rounded-3 small fw-bold">
            <i class="fa-solid fa-shield-halved me-1"></i> VERIFIED OLMIOS GUARANTEE - 100% Licensed & Background-Checked
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([29.7604, -95.3698], 10);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19 }}).addTo(map);

        // ZIP Code Coverage Overlay Polygons
        var activeZip = L.polygon([
            [29.85, -95.45], [29.90, -95.35], [29.82, -95.30], [29.78, -95.40]
        ], {{ color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.4 }}).addTo(map).bindPopup("<b>Active Tech Zip: 77037</b><br>Immediate Dispatch Available");

        var emergencyZip = L.polygon([
            [29.75, -95.38], [29.72, -95.32], [29.68, -95.36], [29.70, -95.42]
        ], {{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.4 }}).addTo(map).bindPopup("<b>Emergency High-Priority Zip: 77021</b>");

        L.marker([29.7604, -95.3698]).addTo(map).bindPopup('Active Field Technician Unit #402').openPopup();
    </script>
</body>
</html>"""

# --- 3. INSTANT DISPATCH REQUEST ('/dispatch_request') ---
@app.route('/dispatch_request')
def dispatch_request():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Request Service</title>
    {COMMON_HEADER}
    <style>
        body {{ background-color: #0b1329; color: white; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }}
        .main-card {{ background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
        .btn-amber {{ background: linear-gradient(135deg, #d97706, #b45309); color: white; border: none; font-weight: 800; }}
        .form-label {{ font-weight: 800; color: #334155 !important; font-size: 0.8rem; letter-spacing: 0.5px; }}
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <div>
                <h5 class="fw-bold text-dark mb-0"><i class="fa-solid fa-truck-fast me-1 text-primary"></i> Instant HVAC Dispatch</h5>
                <small class="text-success fw-bold"><i class="fa-solid fa-circle-check me-1"></i> Verified & Ready</small>
            </div>
            {get_phoenix_svg(45, 45)}
        </div>

        <div class="mb-3">
            <label class="form-label"><i class="fa-solid fa-hashtag me-1"></i> PURCHASE ORDER (PO) # (OPTIONAL)</label>
            <input type="text" class="form-control rounded-3" placeholder="Enter PO Number">
        </div>

        <div class="mb-3">
            <label class="form-label"><i class="fa-solid fa-fan me-1"></i> EQUIPMENT TYPE</label>
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
                <i class="fa-solid fa-robot text-primary fs-5"></i>
                <h6 class="fw-bold mb-0 text-primary">OLMIOS Diagnostic Assistant</h6>
            </div>
            <p class="small text-muted mb-2">Describe symptoms or drag & drop equipment photos:</p>
            
            <div id="drop_zone" style="border: 2px dashed #93c5fd; background: #ffffff; border-radius: 12px; padding: 10px;">
                <textarea id="chat_assistant_input" class="form-control border-0 bg-transparent" rows="3" placeholder="Describe symptoms or drop images..."></textarea>
                
                <div class="d-flex justify-content-between align-items-center mt-2 pt-2 border-top">
                    <label class="btn btn-sm btn-light border text-primary fw-bold mb-0" style="cursor: pointer;">
                        <i class="fa-solid fa-camera me-1"></i> Attach Photo <input type="file" id="image_upload_input" accept="image/*" multiple style="display: none;" onchange="handleFileSelect(event)">
                    </label>
                    <span class="small text-muted" id="file_count_badge">Drop images here</span>
                </div>
                <div id="image_preview_container" class="d-flex gap-2 flex-wrap mt-2"></div>
            </div>

            <button type="button" class="btn btn-primary w-100 mt-3 py-2 fw-bold rounded-3 shadow-sm" onclick="autoFillDescription()">
                <i class="fa-solid fa-wand-magic-sparkles me-1"></i> AUTO-FILL ISSUE DESCRIPTION
            </button>
        </div>

        <div class="mb-3">
            <label class="form-label"><i class="fa-solid fa-file-pen me-1"></i> ISSUE DESCRIPTION (FINAL DISPATCH SUMMARY)</label>
            <textarea id="issue_description" class="form-control rounded-3" rows="3" placeholder="Describe issue or click Auto-Fill above..."></textarea>
        </div>

        <div class="mb-3">
            <label class="form-label"><i class="fa-solid fa-credit-card me-1"></i> SELECT PAYMENT METHOD</label>
            <select class="form-select rounded-3">
                <option value="">Select Payment Method...</option>
                <option>Visa ending in 1004</option>
            </select>
        </div>

        <button type="button" class="btn btn-amber w-100 py-3 rounded-3 fw-bold mb-2" onclick="alert('Service Request Dispatched! Technician assigned.')">
            <i class="fa-solid fa-credit-card me-1"></i> Request Service & Dispatch Tech
        </button>
        
        <a href="/customer_home" class="btn btn-outline-secondary w-100 py-2 rounded-3 fw-bold small"><i class="fa-solid fa-house me-1"></i> Home Page</a>
    </div>

    <script>
    function autoFillDescription() {{
        let chatInput = document.getElementById('chat_assistant_input').value.trim();
        let issueBox = document.getElementById('issue_description');
        let lowerChat = chatInput.toLowerCase();
        
        let isOutdoor = lowerChat.includes('condenser') || lowerChat.includes('outdoor') || lowerChat.includes('outside') || lowerChat.includes('compressor');
        let isIndoorBlower = lowerChat.includes('blower') || lowerChat.includes('furnace') || lowerChat.includes('air handler');
        let isCommercial = lowerChat.includes('rtu') || lowerChat.includes('rooftop');
        
        let specText = "";
        if (isCommercial) {{
            specText = " | RTU M/N: Commercial Packaged Unit";
        }} else if (isIndoorBlower) {{
            specText = " | Furnace M/N: S8X1B040M (S/N: 24001MN091)";
        }} else if (isOutdoor) {{
            specText = " | Condenser M/N: 4TTR6036N (S/N: 21045XY892)";
        }} else {{
            specText = " | Condenser M/N: 4TTR6036N, Furnace M/N: S8X1B040M";
        }}

        if (chatInput !== "") {{
            issueBox.value = chatInput + specText;
        }}
    }}

    let dropZone = document.getElementById('drop_zone');
    let previewContainer = document.getElementById('image_preview_container');
    let fileBadge = document.getElementById('file_count_badge');

    ['dragenter', 'dragover'].forEach(e => dropZone.addEventListener(e, (evt) => {{ evt.preventDefault(); dropZone.style.background = '#e0f2fe'; }}));
    ['dragleave', 'drop'].forEach(e => dropZone.addEventListener(e, (evt) => {{ evt.preventDefault(); dropZone.style.background = '#ffffff'; }}));

    dropZone.addEventListener('drop', (e) => {{ handleFiles(e.dataTransfer.files); }});
    function handleFileSelect(e) {{ handleFiles(e.target.files); }}

    function handleFiles(files) {{
        if (files.length > 0) {{
            fileBadge.innerText = files.length + " photo(s) attached";
            fileBadge.className = "small text-success fw-bold";
        }}
        Array.from(files).forEach(file => {{
            if (file.type.startsWith('image/')) {{
                let reader = new FileReader();
                reader.onload = function(e) {{
                    let img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.cssText = "width: 45px; height: 45px; object-fit: cover; border-radius: 6px; border: 1px solid #cbd5e1;";
                    previewContainer.appendChild(img);
                }};
                reader.readAsDataURL(file);
            }}
        }});
    }}
    </script>
</body>
</html>"""

# --- 4. CUSTOMER PROFILE & WALLET ('/profile') ---
@app.route('/profile')
def profile():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Profile</title>
    {COMMON_HEADER}
    <style>
        body {{ background-color: #0b1329; color: white; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }}
        .main-card {{ background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
        .form-label {{ font-weight: 800; color: #334155 !important; font-size: 0.8rem; letter-spacing: 0.5px; }}
        .section-header {{ font-weight: 800; color: #1e3a8a; font-size: 0.95rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 12px; margin-top: 18px; }}
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <h5 class="fw-bold text-dark mb-0"><i class="fa-solid fa-address-card me-1 text-primary"></i> Customer Profile & Wallet</h5>
            {get_phoenix_svg(45, 45)}
        </div>

        <div class="mb-3 text-center">
            <img id="profile_avatar_preview" src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" style="width: 85px; height: 85px; object-fit: cover; border-radius: 50%; border: 3px solid #3b82f6;" class="mb-2">
            <div>
                <label class="btn btn-sm btn-outline-primary fw-bold rounded-3">
                    <i class="fa-solid fa-camera me-1"></i> Upload Profile Picture
                    <input type="file" accept="image/*" style="display: none;" onchange="previewProfilePic(event)">
                </label>
            </div>
        </div>

        <div class="section-header"><i class="fa-solid fa-user me-1"></i> 1. Basic Personal Information & Residence</div>
        
        <div class="row g-2 mb-2">
            <div class="col-6">
                <label class="form-label">FIRST NAME</label>
                <input type="text" class="form-control rounded-3" placeholder="Enter first name">
            </div>
            <div class="col-6">
                <label class="form-label">LAST NAME</label>
                <input type="text" class="form-control rounded-3" placeholder="Enter last name">
            </div>
        </div>
        
        <div class="mb-2">
            <label class="form-label">PHONE NUMBER</label>
            <input type="text" class="form-control rounded-3" placeholder="Enter phone number">
        </div>

        <div class="mb-2">
            <label class="form-label">EMAIL ADDRESS</label>
            <input type="email" class="form-control rounded-3" placeholder="Enter email address">
        </div>

        <div class="mb-2">
            <label class="form-label">DRIVER'S LICENSE / STATE ID #</label>
            <input type="text" class="form-control rounded-3" placeholder="Enter Driver's License #">
        </div>

        <div class="mb-3">
            <label class="form-label">PRIMARY RESIDENCE STREET ADDRESS</label>
            <input type="text" class="form-control rounded-3" placeholder="Enter street address">
        </div>

        <div class="section-header"><i class="fa-solid fa-sliders me-1"></i> 2. HVAC System Equipment & Data Plate Specs</div>
        
        <div class="mb-2">
            <label class="form-label">SYSTEM HEATING TYPE</label>
            <select class="form-select rounded-3">
                <option value="">Select System Type...</option>
                <option>Gas Heating System (Condenser, Coil, Furnace)</option>
                <option>Electric Heat Pump System</option>
                <option>Commercial Packaged RTU</option>
            </select>
        </div>

        <div class="row g-2 mb-2">
            <div class="col-6">
                <label class="form-label">CONDENSER MODEL #</label>
                <input type="text" class="form-control rounded-3" placeholder="Model #">
            </div>
            <div class="col-6">
                <label class="form-label">CONDENSER SERIAL #</label>
                <input type="text" class="form-control rounded-3" placeholder="Serial #">
            </div>
        </div>

        <div class="row g-2 mb-2">
            <div class="col-6">
                <label class="form-label">EVAPORATOR COIL MODEL #</label>
                <input type="text" class="form-control rounded-3" placeholder="Model #">
            </div>
            <div class="col-6">
                <label class="form-label">COIL SERIAL #</label>
                <input type="text" class="form-control rounded-3" placeholder="Serial #">
            </div>
        </div>

        <div class="row g-2 mb-2">
            <div class="col-6">
                <label class="form-label">FURNACE MODEL #</label>
                <input type="text" class="form-control rounded-3" placeholder="Model #">
            </div>
            <div class="col-6">
                <label class="form-label">FURNACE SERIAL #</label>
                <input type="text" class="form-control rounded-3" placeholder="Serial #">
            </div>
        </div>

        <div class="mb-3">
            <label class="form-label"><i class="fa-solid fa-image me-1 text-primary"></i> UNIT RATING PLATE PHOTO URL / UPLOAD</label>
            <input type="text" class="form-control rounded-3" placeholder="Upload or paste image URL of equipment tag">
        </div>

        <div class="p-3 mb-3 border rounded-3 bg-light">
            <h6 class="fw-bold text-dark mb-2"><i class="fa-solid fa-location-dot me-1 text-danger"></i> Manage Additional Property Locations</h6>
            <select class="form-select rounded-3 mb-2">
                <option value="">Select Property Address...</option>
            </select>
            <button class="btn btn-sm btn-outline-primary fw-bold rounded-3 w-100" onclick="alert('Form opened to register additional location equipment.')">
                <i class="fa-solid fa-plus me-1"></i> Add Additional Location Equipment
            </button>
        </div>

        <a href="/customer_home" class="btn btn-secondary w-100 py-2 rounded-3 fw-bold"><i class="fa-solid fa-house me-1"></i> Home Page</a>
    </div>

    <script>
    function previewProfilePic(e) {{
        if(e.target.files && e.target.files[0]) {{
            let reader = new FileReader();
            reader.onload = function(evt) {{ document.getElementById('profile_avatar_preview').src = evt.target.result; }}
            reader.readAsDataURL(e.target.files[0]);
        }}
    }}
    </script>
</body>
</html>"""

# --- 5. INVOICES & REFUND REQUESTS ('/invoices') ---
@app.route('/invoices')
def invoices():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Invoices</title>
    {COMMON_HEADER}
    <style>
        body {{ background-color: #0b1329; color: white; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 15px; min-height: 100vh; }}
        .main-card {{ background: #ffffff; color: #0f172a; border-radius: 20px; padding: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
    </style>
</head>
<body>
    <div class="main-card">
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <h5 class="fw-bold text-dark mb-0"><i class="fa-solid fa-receipt me-1 text-primary"></i> Service Invoices</h5>
            {get_phoenix_svg(45, 45)}
        </div>
        
        <div class="border rounded-3 p-3 mb-3 bg-light">
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-bold">INV-1002 (Capacitor Replacement)</span>
                <span class="badge bg-success">Paid</span>
            </div>
            <div class="small text-muted mb-2">Service Date: 08/01/2026 | Amount: $185.00</div>
            <button class="btn btn-outline-danger btn-sm w-100 fw-bold rounded-3" onclick="alert('Refund Request Submitted. Billing department will follow up within 24 hours.')">
                <i class="fa-solid fa-rotate-left me-1"></i> Request Refund
            </button>
        </div>

        <a href="/customer_home" class="btn btn-secondary w-100 py-2 rounded-3 fw-bold"><i class="fa-solid fa-house me-1"></i> Home Page</a>
    </div>
</body>
</html>"""

# --- 6. DOWNLOAD PHOENIX LOGO PAGE ('/download_logo') ---
# --- 6. DOWNLOAD PHOENIX LOGO PAGE ('/download_logo') ---
@app.route('/download_logo')
def download_logo():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Olmios - Download Phoenix Logo (.JPG)</title>
    {COMMON_HEADER}
    <style>
        body {{ background-color: #0b1329; color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Outfit', system-ui, -apple-system, sans-serif; padding: 20px; }}
        .logo-card {{ background: #ffffff; padding: 40px; border-radius: 24px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); max-width: 480px; width: 100%; color: #0f172a; }}
    </style>
</head>
<body>
    <div class="logo-card">
        <h4 class="fw-bold text-dark mb-1">Olmios Phoenix Symbol</h4>
        <p class="text-muted small mb-3">High-Resolution .JPG Format</p>
        
        <!-- Hidden SVG Source -->
        <div id="svg_container" style="display:none;">
            {get_phoenix_svg(600, 600)}
        </div>

        <!-- Rendered Native JPG Preview -->
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
    function renderJPG() {{
        let svgElement = document.querySelector('#svg_container svg');
        let svgData = new XMLSerializer().serializeToString(svgElement);
        let svgBlob = new Blob([svgData], {{type: "image/svg+xml;charset=utf-8"}});
        let URLObj = window.URL || window.webkitURL || window;
        let blobURL = URLObj.createObjectURL(svgBlob);
        
        let img = new Image();
        img.onload = function() {{
            let canvas = document.getElementById('jpg_canvas');
            let ctx = canvas.getContext('2d');
            
            // Clean white background for JPG
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            
            let jpgDataUrl = canvas.toDataURL('image/jpeg', 0.95);
            document.getElementById('jpg_preview').src = jpgDataUrl;
        }};
        img.src = blobURL;
    }}

    function downloadJPG() {{
        let canvas = document.getElementById('jpg_canvas');
        let jpgUrl = canvas.toDataURL('image/jpeg', 0.95);
        let downloadLink = document.createElement("a");
        downloadLink.href = jpgUrl;
        downloadLink.download = "olmios_phoenix_logo.jpg";
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    }}

    window.onload = renderJPG;
    </script>
</body>
</html>"""


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
