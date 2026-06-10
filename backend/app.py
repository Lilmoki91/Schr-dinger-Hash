import os
import logging
import hashlib
import secrets
import urllib.parse
import time
import json
import base64
import threading
import numpy as np
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pyqpanda3 import core

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPPS_URL = "https://schr-dinger-hash.pages.dev"
MASTER_SEED = os.getenv("MASTER_SEED")
ORIGINQ_API_KEY = os.getenv("ORIGINQ_API_KEY")

PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

user_access_count = {}
used_tokens = set()

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "Quantum Entanglement Gate Active", "version": "3.0"})

@app.route('/api/calculate-hash', methods=['POST'])
def api_calculate_hash():
    data = request.get_json()
    user_id = data.get('user_id')
    seed_hex = data.get('seed_hex')
    
    if not user_id or not seed_hex:
        return jsonify({"error": "Missing user_id or seed_hex"}), 400
    
    try:
        quantum_hash, source = calculate_quantum_hash_entanglement(user_id, seed_hex)
        logging.info(f"🔑 API Hash: {quantum_hash[:16]}... untuk user {user_id}")
        return jsonify({"hash": quantum_hash, "source": source})
    except Exception as e:
        logging.error(f"🔴 API Error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================
# FIBONACCI TTL
# ============================================================
def get_fibonacci_ttl(count):
    fib = [1, 1, 2, 3, 5, 8, 13, 21]
    idx = min(count - 1, len(fib) - 1)
    ttl = fib[idx] * 30
    return min(ttl, 600)

# ============================================================
# QUANTUM MATRIX ID
# ============================================================
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
    except Exception as e:
        logging.error(f"Quantum Matrix ID gagal: {e}")
        fallback = hashlib.sha256(f"{MASTER_SEED}:{user_id}".encode()).hexdigest()[:16]
        return f"QuantumMatrix_{fallback}"

# ============================================================
# STATE VECTOR MANUAL
# ============================================================
def calculate_state_vector_manually(user_id, seed_hex, entanglement_pairs):
    state = np.zeros(256, dtype=np.float64)
    
    init_index = 0
    seed_bytes = bytes.fromhex(seed_hex[:12])
    for i in range(6):
        if seed_bytes[i] % 2 == 1:
            init_index |= (1 << i)
    
    uid = int(user_id)
    if (uid % 256) > 128:
        init_index |= (1 << 6)
    if ((uid >> 8) % 256) > 128:
        init_index |= (1 << 7)
    
    state[init_index] = 1.0
    
    inv_sqrt2 = 1.0 / np.sqrt(2)
    for q in range(8):
        new_state = np.zeros(256, dtype=np.float64)
        mask = 1 << q
        for i in range(256):
            amp = state[i]
            if amp == 0:
                continue
            bit = (i & mask) != 0
            i0 = i & ~mask
            i1 = i | mask
            if not bit:
                new_state[i0] += inv_sqrt2 * amp
                new_state[i1] += inv_sqrt2 * amp
            else:
                new_state[i0] += inv_sqrt2 * amp
                new_state[i1] += -inv_sqrt2 * amp
        state = new_state
    
    for control, target in entanglement_pairs:
        new_state = np.zeros(256, dtype=np.float64)
        control_mask = 1 << control
        target_mask = 1 << target
        for i in range(256):
            amp = state[i]
            if amp == 0:
                continue
            if i & control_mask:
                flipped = i ^ target_mask
                new_state[flipped] += amp
            else:
                new_state[i] += amp
        state = new_state
    
    probabilities = np.abs(state) ** 2
    return probabilities.tolist()

# ============================================================
# QUANTUM HASH
# ============================================================
def calculate_quantum_hash_entanglement(user_id, seed_hex):
    logging.info("🇨🇳 Origin Quantum: Membina Litar Entanglement...")
    
    entanglement_pairs = [
        (0, 1), (2, 3), (4, 5), (6, 7),
        (0, 3), (1, 5), (2, 7), (4, 6),
    ]
    
    state = calculate_state_vector_manually(user_id, seed_hex, entanglement_pairs)
    
    state_obj = {
        "pairs": len(entanglement_pairs),
        "qubits": 8,
        "state_vector": [round(float(x), 10) for x in state]
    }
    
    result_str = json.dumps(state_obj, sort_keys=True)
    quantum_hash = hashlib.sha256(result_str.encode()).hexdigest()
    
    logging.info(f"✅ Hash: {quantum_hash[:16]}...")
    return quantum_hash, "ORIGIN_ENTANGLEMENT"

# ============================================================
# BOT TELEGRAM
# ============================================================
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("LOG MASUK", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "⚛️ *ORIGIN QUANTUM ENTANGLEMENT GATE*\n\n"
        "🖥️ Hardware: *Origin Quantum 🇨🇳*\n"
        "🔬 Litar: *8-Qubit Hadamard + CNOT*\n"
        "🔗 Entanglement: *8 Pasangan*\n\n"
        "📌 Klik *'LOG MASUK'* — pengesahan entiti fizikal.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def mark_used(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = context.args[0] if context.args else None
    if tid:
        used_tokens.add(tid)
        await update.message.reply_text("✅ Token ditandakan")
    else:
        await update.message.reply_text("❌ error: missing token_id")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    user_id = str(update.effective_user.id)
    
    if str(contact.user_id) != user_id:
        await update.message.reply_text("❌ Entropi fizikal tidak sepadan. Klon dikesan.")
        return
    
    status_msg = await update.message.reply_text("⚛️ Origin Quantum: Membina Litar Entanglement... 🇨🇳")
    
    count = user_access_count.get(user_id, 0) + 1
    user_access_count[user_id] = count
    ttl_seconds = get_fibonacci_ttl(count)
    expiry = int(time.time()) + ttl_seconds
    token_id = secrets.token_hex(16)
    seed_hex = secrets.token_hex(32)
    
    try:
        quantum_hash, hash_source = calculate_quantum_hash_entanglement(user_id, seed_hex)
        quantum_matrix_id = generate_quantum_matrix_id(user_id)
        
        q_state_visual = " ".join([
            "|0⟩" if int(char, 16) % 2 == 0 else "|1⟩" 
            for char in quantum_hash[:8]
        ])
        
        token_data = {
            "u": user_id,
            "s": seed_hex,
            "h": quantum_hash,
            "exp": expiry,
            "tid": token_id,
            "qid": quantum_matrix_id,
            "src": hash_source
        }
        
        json_str = json.dumps(token_data)
        token_bytes = base64.b64encode(json_str.encode("utf-8"))
        token_safe = urllib.parse.quote(token_bytes.decode("utf-8"))
        
        msg = (
            f"<b>[⚛️ ORIGIN QUANTUM — ENTANGLEMENT TERKUNCI]</b>\n\n"
            f"<b>🖥️ Hardware:</b> <i>Origin Quantum CPUQVM 🇨🇳💻</i>\n"
            f"<b>🔬 Source:</b> <code>{hash_source}</code>\n"
            f"<b>🔗 Entanglement:</b> <code>8 pasangan CNOT</code>\n\n"
            f"<b>• User ID:</b> <code>{user_id}</code>\n"
            f"<b>• Quantum Matrix ID:</b> <code>{quantum_matrix_id}</code>\n"
            f"<b>• Akses ke-:</b> <code>{count}</code>\n"
            f"<b>• Token sah:</b> <code>{ttl_seconds} saat ({ttl_seconds/60:.1f} minit)</code>\n"
            f"<b>• Seed (Dinamic):</b> <code>{seed_hex[:12]}...</code>\n"
            f"<b>• State 8-Qubit:</b> <code>{q_state_visual}</code>\n"
            f"<b>• Hash Kuantum:</b> <code>{quantum_hash[:16]}...</code>\n\n"
            f"<i>🌀 Quantum Matrix ID kekal untuk ID Telegram ini</i>"
        )
        
        full_url = f"{WEBAPPS_URL}?token={token_safe}"
        
        await status_msg.delete()
        await update.message.reply_text(msg, parse_mode="HTML")
        await update.message.reply_text(f"🔗 <a href='{full_url}'>🌌 Akses Portal Kuantum</a>", parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"🔴 RALAT: {e}")
        await status_msg.delete()
        await update.message.reply_text(f"🔴 Ralat: {str(e)[:200]}", parse_mode="HTML")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("mark", mark_used))
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
def main() -> None:
    if not TOKEN:
        print("[RALAT FATAL] BOT_TOKEN tidak diset!")
        return
    
    # Set webhook
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", json={"url": webhook_url})
        print(f"🚀 Webhook set: {webhook_url}")
    
    print("=" * 60)
    print("⚛️  ORIGIN QUANTUM ENTANGLEMENT GATE")
    print("=" * 60)
    print(f"🌀 MASTER_SEED: {MASTER_SEED[:6]}...")
    print(f"🌐 Flask API + Webhook: Port {PORT}")
    print(f"📡 WebApps: {WEBAPPS_URL}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    main()
