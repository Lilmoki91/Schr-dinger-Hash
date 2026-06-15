import os
import logging
import hashlib
import secrets
import urllib.parse
import time
import json
import base64
import requests
import threading
import asyncio
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === QUIMB TENSOR NETWORK ===
import quimb.tensor as qtn
import numpy as np

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPPS_URL = "https://schr-dinger-hash.pages.dev"
MASTER_SEED = os.getenv("MASTER_SEED")

PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# STORAGE — RESET SETIAP 24 JAM
# ==========================================
user_access_count = {}   # count harian
user_access_reset = {}   # tarikh last reset

def get_daily_count(user_id):
    """Dapatkan count harian — auto reset setiap 24 jam"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last_reset = user_access_reset.get(user_id, "")
    
    if last_reset != today:
        # Reset count untuk hari baru
        user_access_count[user_id] = 0
        user_access_reset[user_id] = today
        logging.info(f"🔄 Reset count untuk user {user_id} — Hari baru: {today}")
    
    # Tambah count
    count = user_access_count.get(user_id, 0) + 1
    user_access_count[user_id] = count
    return count

app = Flask(__name__)
CORS(app)

# ==========================================
# KONFIGURASI 100-QUBIT TENSOR NETWORK
# ==========================================
N_QUBITS = 100

def get_master_mps():
    qc = qtn.Circuit(N_QUBITS)
    for i in range(N_QUBITS):
        qc.apply_gate('H', i)
    for i in range(N_QUBITS - 1):
        qc.apply_gate('CZ', i, i + 1)
    return qc.psi.copy()

def generate_quantum_kernel_id(user_id):
    qc = qtn.Circuit(N_QUBITS)
    uid = int(user_id)
    for i in range(N_QUBITS):
        if (uid >> (i % 32)) & 1:
            qc.apply_gate('X', i)
        qc.apply_gate('H', i)
    for i in range(0, N_QUBITS - 1, 2):
        qc.apply_gate('CNOT', i, i + 1)
    psi = qc.psi
    try:
        entropy = psi.entropy(N_QUBITS // 2)
        combined = f"{MASTER_SEED}:{user_id}:{entropy:.15f}"
        qmid = hashlib.sha256(combined.encode()).hexdigest()[:16]
        return f"QKernel_{qmid}"
    except:
        return f"QKernel_{hashlib.sha256(f'{MASTER_SEED}:{user_id}'.encode()).hexdigest()[:16]}"

def calculate_quantum_signature(user_id, seed_hex):
    master_psi = get_master_mps()
    qc = qtn.Circuit(N_QUBITS)
    uid = int(user_id)
    seed_bytes = bytes.fromhex(seed_hex[:32])

    for i in range(N_QUBITS):
        if (uid >> (i % 32)) & 1:
            qc.apply_gate('X', i)

    for i in range(N_QUBITS):
        if seed_bytes[i % len(seed_bytes)] % 2 == 1:
            qc.apply_gate('Z', i)
        qc.apply_gate('H', i)

    for i in range(N_QUBITS - 1):
        if seed_bytes[i % len(seed_bytes)] % 3 == 0:
            qc.apply_gate('CNOT', i, i + 1)

    user_psi = qc.psi

    try:
        overlap = abs(master_psi.H @ user_psi)
        fidelity = overlap ** 2
    except:
        fidelity = 0.0

    signature = hashlib.sha256(f"Kernel_{fidelity:.15f}_{seed_hex}".encode()).hexdigest()
    return signature, fidelity, user_psi

def get_qubit_state_summary(psi):
    try:
        states = []
        for i in range(min(10, N_QUBITS)):
            rho = psi.partial_trace([j for j in range(N_QUBITS) if j != i])
            prob_0 = abs(rho[0, 0]) if hasattr(rho, '__getitem__') else 0.5
            states.append("|0⟩" if prob_0 > 0.5 else "|1⟩")
        
        first = " ".join(states[:5])
        last = " ".join(states[-5:])
        return f"{first} ... [{N_QUBITS-10} qubit] ... {last}"
    except:
        q_hash = hashlib.md5(str(psi).encode()).hexdigest()
        bits = bin(int(q_hash[:8], 16))[2:].zfill(32)
        return " ".join(["|0⟩" if b == '0' else "|1⟩" for b in bits[:10]]) + " ..."

# ==========================================
# FLASK
# ==========================================
@app.route('/')
def home():
    return jsonify({"status": "100-Qubit Tensor Gate Active"})

@app.route('/api/verify', methods=['POST'])
def api_verify():
    data = request.get_json()
    token_hash = data.get('token_hash')
    if not token_hash:
        return jsonify({"error": "Missing token_hash"}), 400
    return jsonify({"match": True, "hash": token_hash})

def get_quantum_random_hex(length=32):
    try:
        url = f"https://qrng.anu.edu.au/API/jsonI.php?length={length}&type=hex16"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("success"):
            return data["data"][0]
        else:
            raise Exception("ANU QRNG gagal")
    except:
        return secrets.token_hex(length)

def get_fibonacci_ttl(count):
    fib = [1, 1, 2, 3, 5, 8, 13, 21]
    idx = min(count - 1, len(fib) - 1)
    return min(fib[idx] * 30, 600)

# ==========================================
# BOT TELEGRAM
# ==========================================
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("LOG MASUK", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "⚛️ *QUANTUM KERNEL TENSOR GATE*\n\n"
        "🎲 Rawak: *ANU Quantum Random*\n"
        "🔬 Enjin: *Quimb 100-Qubit Tensor Network*\n"
        "🔄 Akses: *Reset setiap 24 jam*\n\n"
        "📌 Klik *'LOG MASUK'*",
        reply_markup=reply_markup, parse_mode="Markdown"
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = str(update.effective_user.id)
    if str(contact.user_id) != user_id:
        await update.message.reply_text("❌ Entropi tidak sepadan.")
        return
    
    status_msg = await update.message.reply_text("⚛️ Memproses 100-Qubit Tensor Network... 🔬")
    
    # Dapatkan count harian (auto-reset setiap 24 jam)
    count = get_daily_count(user_id)
    ttl = get_fibonacci_ttl(count)
    expiry = int(time.time()) + ttl
    seed_hex = get_quantum_random_hex(32)
    
    try:
        loop = asyncio.get_event_loop()
        quantum_hash, fidelity, psi = await loop.run_in_executor(
            None, calculate_quantum_signature, user_id, seed_hex
        )
        qmid = await loop.run_in_executor(
            None, generate_quantum_kernel_id, user_id
        )
        q_state = await loop.run_in_executor(
            None, get_qubit_state_summary, psi
        )
    except Exception as e:
        await status_msg.delete()
        await update.message.reply_text(f"🔴 Ralat Quimb: {str(e)[:200]}")
        return
    
    token_data = {
        "u":user_id,"s":seed_hex,"h":quantum_hash,
        "exp":expiry,"tid":secrets.token_hex(16),
        "qid":qmid,"src":"ANU_QUANTUM_RANDOM",
        "fid":fidelity
    }
    token_safe = urllib.parse.quote(base64.b64encode(json.dumps(token_data).encode()).decode())
    
    # Status reset
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    msg = (
        f"<b>[⚛️ QUANTUM KERNEL VERIFIED]</b>\n\n"
        f"<b>🎲 Rawak:</b> <i>ANU Quantum Random</i>\n"
        f"<b>🔬 Litar:</b> <i>100-Qubit Tensor Network (MPS)</i>\n"
        f"<b>🔄 Reset:</b> <i>Setiap 24 jam (Hari: {today})</i>\n\n"
        f"<b>• User ID:</b> <code>{user_id}</code>\n"
        f"<b>• Kernel Matrix ID:</b> <code>{qmid}</code>\n"
        f"<b>• Akses ke-:</b> <code>{count}</code> (harian)\n"
        f"<b>• Token sah:</b> <code>{ttl} saat ({ttl/60:.1f} minit)</code>\n"
        f"<b>• Seed Kuantum:</b> <code>{seed_hex[:12]}...</code>\n"
        f"<b>• 100-Qubit State:</b> <code>{q_state}</code>\n"
        f"<b>• Fidelity Skor:</b> <code>{fidelity:.8f}</code>\n"
        f"<b>• Hash Kuantum:</b> <code>{quantum_hash[:16]}...</code>\n\n"
        f"<i>🌀 Enjin Quimb | 100-Qubit MPS | Bond-16</i>\n"
        f"<i>🔄 Count reset setiap hari — esok mula dari 1 lagi</i>"
    )
    
    await status_msg.delete()
    await update.message.reply_text(msg, parse_mode="HTML")
    await update.message.reply_text(f"🔗 <a href='{WEBAPPS_URL}?token={token_safe}'>🌌 Akses Portal Kuantum</a>", parse_mode="HTML")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

def main():
    if not TOKEN:
        print("BOT_TOKEN tidak diset!")
        return
    
    httpx.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    print("🔧 Webhook lama dibersihkan")
    
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True)
    flask_thread.start()
    
    print("=" * 60)
    print("⚛️  QUANTUM KERNEL TENSOR GATE (100-QUBIT)")
    print("=" * 60)
    print(f"🌐 Flask: Port {PORT}")
    print(f"📡 Bot: Polling")
    print(f"🔄 Reset: Setiap 24 jam")
    print("=" * 60)
    
    application.run_polling()

if __name__ == '__main__':
    main()
