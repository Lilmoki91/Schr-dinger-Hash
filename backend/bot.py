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
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPPS_URL = "https://schr-dinger-hash.pages.dev"
MASTER_SEED = os.getenv("MASTER_SEED")

PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

user_access_count = {}
used_tokens = set()

# ============================================================
# FLASK APP (Verify API + Webhook)
# ============================================================
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

# ============================================================
# ANU QUANTUM RANDOM
# ============================================================
def get_quantum_random_hex(length=32):
    try:
        url = f"https://qrng.anu.edu.au/API/jsonI.php?length={length}&type=hex16"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("success"):
            quantum_random = data["data"][0]
            logging.info(f"🎲 ANU QRNG: {quantum_random[:16]}...")
            return quantum_random
        else:
            raise Exception("ANU QRNG gagal")
    except Exception as e:
        logging.warning(f"⚠️ ANU QRNG gagal: {e}. Fallback ke secrets.")
        return secrets.token_hex(length)

def get_fibonacci_ttl(count):
    fib = [1, 1, 2, 3, 5, 8, 13, 21]
    idx = min(count - 1, len(fib) - 1)
    ttl = fib[idx] * 30
    return min(ttl, 600)

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
        fallback = hashlib.sha256(f"{MASTER_SEED}:{user_id}".encode()).hexdigest()[:16]
        return f"QuantumMatrix_{fallback}"

def calculate_quantum_signature(user_id, seed_hex):
    qubits = cirq.LineQubit.range(8)
    circuit = cirq.Circuit()
    
    seed_bytes = bytes.fromhex(seed_hex[:12])
    for i in range(6):
        if (seed_bytes[i] % 2 == 1):
            circuit.append(cirq.X(qubits[i]))
    
    uid = int(user_id)
    if (uid % 256) > 128: circuit.append(cirq.X(qubits[6]))
    if ((uid >> 8) % 256) > 128: circuit.append(cirq.X(qubits[7]))
    
    for i in range(8):
        circuit.append(cirq.H(qubits[i]))
    
    entanglement_pairs = [(0,1),(2,3),(4,5),(6,7),(0,3),(1,5),(2,7),(4,6)]
    for c, t in entanglement_pairs:
        circuit.append(cirq.CNOT(qubits[c], qubits[t]))
    
    simulator = cirq.Simulator()
    result = simulator.simulate(circuit)
    
    probabilities = [abs(amp) ** 2 for amp in result.final_state_vector]
    state_obj = {
        "pairs": len(entanglement_pairs),
        "qubits": 8,
        "state_vector": [round(float(p), 10) for p in probabilities]
    }
    
    return hashlib.sha256(json.dumps(state_obj, sort_keys=True).encode()).hexdigest()

# ============================================================
# BOT TELEGRAM
# ============================================================
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("LOG MASUK", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "⚛️ *ANU QUANTUM ENTANGLEMENT GATE*\n\n"
        "🎲 Rawak: *ANU Quantum Random*\n"
        "🔬 Litar: *Cirq 8-Qubit*\n\n"
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
    
    token_data = {
        "u": user_id, "s": seed_hex, "h": quantum_hash,
        "exp": expiry, "tid": secrets.token_hex(16),
        "qid": qmid, "src": "ANU_QUANTUM_RANDOM"
    }
    token_safe = urllib.parse.quote(base64.b64encode(json.dumps(token_data).encode()).decode())
    
    await update.message.reply_text(
        f"<b>[⚛️ ANU QUANTUM]</b>\n\n"
        f"🎲 Rawak: ANU QRNG\n"
        f"Hash: <code>{quantum_hash[:16]}...</code>\n"
        f"Akses ke-: <code>{count}</code>",
        parse_mode="HTML"
    )
    await update.message.reply_text(f"🔗 <a href='{WEBAPPS_URL}?token={token_safe}'>🌌 Portal</a>", parse_mode="HTML")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

# ============================================================
# FLASK HANDLE WEBHOOK
# ============================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return 'OK'

# ============================================================
# MAIN
# ============================================================
def main():
    if not TOKEN:
        print("BOT_TOKEN tidak diset!")
        return
    
    # Set webhook
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        httpx.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", json={"url": webhook_url})
        print(f"🚀 Webhook set: {webhook_url}")
    
    print("=" * 60)
    print("⚛️  ANU QUANTUM ENTANGLEMENT GATE")
    print("=" * 60)
    print(f"🌐 Flask + Webhook: Port {PORT}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    main()
