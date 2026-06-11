import os
import logging
import hashlib
import secrets
import urllib.parse
import time
import cirq
import json
import base64
import numpy as np
import requests
import threading
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPPS_URL = "https://schr-dinger-hash.pages.dev"
MASTER_SEED = os.getenv("MASTER_SEED")

PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

user_access_count = {}

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "Quantum Gate Active"})

@app.route('/api/verify', methods=['POST'])
def api_verify():
    data = request.get_json()
    user_id = data.get('user_id')
    seed_hex = data.get('seed_hex')
    token_hash = data.get('token_hash')
    
    if not all([user_id, seed_hex, token_hash]):
        return jsonify({"error": "Missing data"}), 400
    
    local_hash = calculate_quantum_signature(user_id, seed_hex)
    match = local_hash == token_hash
    return jsonify({"match": match})

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

def generate_quantum_matrix_id(user_id):
    try:
        combined = f"{MASTER_SEED}:{user_id}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        matrix = np.frombuffer(hash_bytes, dtype=np.uint8).reshape(16, 16).astype(np.float64)
        det = abs(np.linalg.det(matrix))
        trace = abs(np.trace(matrix))
        eigen = abs(np.linalg.eigvals(matrix)[0].real)
        combined_id = f"{det:.10f}:{trace:.10f}:{eigen:.10f}"
        matrix_id = hashlib.sha256(combined_id.encode()).hexdigest()[:16]
        return f"QuantumMatrix_{matrix_id}"
    except:
        return f"QuantumMatrix_{hashlib.sha256(f'{MASTER_SEED}:{user_id}'.encode()).hexdigest()[:16]}"

def calculate_quantum_signature(user_id, seed_hex):
    qubits = cirq.LineQubit.range(8)
    circuit = cirq.Circuit()
    
    # Init qubit dari seed (qubit 0-5)
    seed_bytes = bytes.fromhex(seed_hex[:12])
    for i in range(6):
        if (seed_bytes[i] % 2 == 1):
            circuit.append(cirq.X(qubits[i]))
    
    # User ID ke qubit 6 & 7
    uid = int(user_id)
    if (uid % 256) > 128: circuit.append(cirq.X(qubits[6]))
    if ((uid >> 8) % 256) > 128: circuit.append(cirq.X(qubits[7]))
    
    # Hadamard pada QUBIT 0 SAHAJA — bukan semua!
    circuit.append(cirq.H(qubits[0]))
    
    # CNOT — Entanglement
    pairs = [(0,1),(2,3),(4,5),(6,7),(0,3),(1,5),(2,7),(4,6)]
    for c, t in pairs:
        circuit.append(cirq.CNOT(qubits[c], qubits[t]))
    
    # ✅ MEASURE DENGAN KEY
    circuit.append(cirq.measure(*qubits, key='result'))
    
    # Simulasi dengan 1000 shots — RAWAK!
    simulator = cirq.Simulator()
    result = simulator.run(circuit, repetitions=1000)
    
    # ✅ GUNA HISTOGRAM
    counts = result.histogram(key='result')
    
    # Hash dari counts (dict)
    return hashlib.sha256(json.dumps(counts, sort_keys=True).encode()).hexdigest()

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("LOG MASUK", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "⚛️ *ANU QUANTUM ENTANGLEMENT GATE*\n\n"
        "🎲 Rawak: *ANU Quantum Random*\n"
        "🔬 Litar: *Cirq 8-Qubit + Measurement*\n\n"
        "📌 Klik *'LOG MASUK'*",
        reply_markup=reply_markup, parse_mode="Markdown"
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = str(update.effective_user.id)
    if str(contact.user_id) != user_id:
        await update.message.reply_text("❌ Entropi tidak sepadan.")
        return
    
    count = user_access_count.get(user_id, 0) + 1
    user_access_count[user_id] = count
    ttl = get_fibonacci_ttl(count)
    expiry = int(time.time()) + ttl
    
    seed_hex = get_quantum_random_hex(32)
    quantum_hash = calculate_quantum_signature(user_id, seed_hex)
    qmid = generate_quantum_matrix_id(user_id)
    q_state = " ".join(["|0⟩" if int(c,16)%2==0 else "|1⟩" for c in quantum_hash[:8]])
    
    token_data = {"u":user_id,"s":seed_hex,"h":quantum_hash,"exp":expiry,"tid":secrets.token_hex(16),"qid":qmid,"src":"ANU_QUANTUM_RANDOM"}
    token_safe = urllib.parse.quote(base64.b64encode(json.dumps(token_data).encode()).decode())
    
    msg = (
        f"<b>[⚛️ ANU QUANTUM — RAWAK SEBENAR]</b>\n\n"
        f"<b>🎲 Rawak:</b> <i>ANU Quantum Random</i>\n"
        f"<b>🔬 Litar:</b> <i>Cirq 8-Qubit + Measurement</i>\n\n"
        f"<b>• User ID:</b> <code>{user_id}</code>\n"
        f"<b>• Quantum Matrix ID:</b> <code>{qmid}</code>\n"
        f"<b>• Akses ke-:</b> <code>{count}</code>\n"
        f"<b>• Token sah:</b> <code>{ttl} saat ({ttl/60:.1f} minit)</code>\n"
        f"<b>• Seed:</b> <code>{seed_hex[:12]}...</code>\n"
        f"<b>• State 8-Qubit:</b> <code>{q_state}</code>\n"
        f"<b>• Hash Kuantum:</b> <code>{quantum_hash[:16]}...</code>\n\n"
        f"<i>🌀 Quantum Matrix ID kekal untuk ID Telegram ini</i>"
    )
    
    await update.message.reply_text(msg, parse_mode="HTML")
    await update.message.reply_text(f"🔗 <a href='{WEBAPPS_URL}?token={token_safe}'>🌌 Akses Portal Kuantum</a>", parse_mode="HTML")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

def main():
    if not TOKEN:
        print("BOT_TOKEN tidak diset!")
        return
    
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True)
    flask_thread.start()
    
    print("=" * 60)
    print("⚛️  ANU QUANTUM ENTANGLEMENT GATE")
    print("=" * 60)
    print(f"🌐 Flask: Port {PORT}")
    print(f"📡 Bot: Polling")
    print("=" * 60)
    
    application.run_polling()

if __name__ == '__main__':
    main()
