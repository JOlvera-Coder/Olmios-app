with open('app.py', 'w', encoding='utf-8') as f:
    f.write('''import os
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

def format_doc_id(prefix, num):
    try:
        val = int(num)
    except Exception:
        val = 1
    return f"{prefix}{val:06d}"

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

# ==========================================
# NEW CONFIDENTIAL LEGAL PITCH DECK ROUTE
# ==========================================
@app.route('/pitch')
def pitch_deck_page():
    if os.path.exists('pitch_deck.html'):
        with open('pitch_deck.html', 'r', encoding='utf-8') as f:
            return f.read()
    return "Pitch Deck HTML file not found. Please upload pitch_deck.html.", 404

# ==========================================
# CUSTOMER AUTH / GATEWAY ROUTE
# ==========================================
@app.route('/')
def auth_gateway():
    return redirect('/customer_home')

@app.route('/customer_home')
def customer_home():
    return render_template_string("""<!DOCTYPE html>
<html><head><title>Olmios - Customer Home</title>{{HEADER}}</head>
<body style="background:#0b1329; color:white; padding:20px; font-family:'Outfit',sans-serif;">
<div style="max-width:500px; margin:0 auto; background:white; color:#0f172a; padding:20px; border-radius:20px;">
    <h4>Welcome Back, Ian Olvera</h4>
    <a href="/pitch" class="btn btn-warning w-100 fw-bold my-2">📋 View Confidential Legal Pitch Deck</a>
    <a href="/dispatch_request" class="btn btn-primary w-100 fw-bold my-2">⚡ Request HVAC Service & Dispatch - ($99)</a>
</div></body></html>""".replace('{{HEADER}}', COMMON_HEADER))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
''')
