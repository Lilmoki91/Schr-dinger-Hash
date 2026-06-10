import os
import logging
import hashlib
import secrets
import urllib.parse
import time
import json
import base64
import asyncio
import numpy as np
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pyqpanda3 import core
import httpx

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
    return jsonify({"status": "Quantum Entanglement Gate Active"})

@app.route('/api/calculate-hash', methods=['POST'])
def api_calculate_hash():
    data = request.get_json()
    user_id = data.get('user_id')
    seed_hex = data.get('seed_hex')
    
    if not user_id or not seed_hex:
        return jsonify({"error": "Missing data"}), 400
    
    try:
        quantum_hash, source = calculate_quantum_hash_entanglement(user_id, seed_hex)
        return jsonify({"hash": quantum_hash, "source": source})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# FUNGSI QUANTUM
# ============================================================
def get_fibonacci_ttl(count):
    fib = [1, 1, 2, 3, 5, 8, 13, 21]
    return min(fib[min(count-1, len(fib)-1)] * 30, 600)

def generate_quantum_matrix_id(user_id):
    try:
        combined = f"{MASTER_SEED}:{user_id}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        matrix = np.frombuffer(hash_bytes, dtype=np.uint8).reshape(16, 16).astype(np.float64)
        det, trace = abs(np.linalg.det(matrix)), abs(np.trace(matrix))
        eigen = abs(np.linalg.eigvals(matrix)[0].real)
        matrix_id = hashlib.sha256(f"{det:.10f}:{trace:.10f}:{eigen:.10f}".encode()).hexdigest()[:16]
        return f"QuantumMatrix_{matrix_id}"
    except:
        return f"QuantumMatrix_{hashlib.sha256(f'{MASTER_SEED}:{user_id}'.encode()).hexdigest()[:16]}"

def calculate_state_vector_manually(user_id, seed_hex, pairs):
    state = np.zeros(256, dtype=np.float64)
    init_index = 0
    seed_bytes = bytes.fromhex(seed_hex[:12])
    for i in range(6):
        if seed_bytes[i] % 2 == 1: init_index |= (1 << i)
    uid = int(user_id)
    if (uid % 256) > 128: init_index |= (1 << 6)
    if ((uid >> 8) % 256) > 128: init_index |= (1 << 7)
    state[init_index] = 1.0
    
    inv_sqrt2 = 1.0 / np.sqrt(2)
    for q in range(8):
        ns = np.zeros(256, dtype=np.float64)
        mask = 1 << q
        for i in range(256):
            amp = state[i]
            if amp == 0: continue
            bit = (i & mask) != 0
            i0, i1 = i & ~mask, i | mask
            if not bit:
                ns[i0] += inv_sqrt2 * amp; ns[i1] += inv_sqrt2 * amp
            else:
                ns[i0] += inv_sqrt2 * amp; ns[i1] += -inv_sqrt2 * amp
        state = ns
    
    for c, t in pairs:
        ns = np.zeros(256, dtype=np.float64)
        cm, tm = 1 << c, 1 << t
        for i in range(256):
            amp = state[i]
            if amp == 0: continue
            if i & cm: ns[i ^ tm] += amp
            else: ns[i] += amp
        state = ns
    
    return (np.abs(state) ** 2).tolist()

def calculate_quantum_hash_entanglement(user_id, seed_hex):
    pairs = [(0,1),(2,3),(4,5),(6,7),(0,3),(1,5),(2,7),(4,6)]
    state = calculate_state_vector_manually(user_id, seed_hex, pairs)
    state_obj = {"pairs": 8, "qubits": 8, "state_vector": [round(float(x), 10) for x in state]}
    return hashlib.sha256(json.dumps(state_obj, sort_keys=True).encode()).hexdigest(), "ORIGIN_ENTANGLEMENT"

# ============================================================
# BOT TELEGRAM
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("LOG MASUK", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⚛️ *ORIGIN QUANTUM ENTANGLEMENT GATE*\n\n📌 Klik *'LOG MASUK'*", reply_markup=reply_markup, parse_mode="Markdown")

async def mark_used(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = context.args[0] if context.args else None
    if tid:
        used_tokens.add(tid)
        await update.message.reply_text("✅ Token ditandakan")
    else:
        await update.message.reply_text("❌ error")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    user_id = str(update.effective_user.id)
    
    if str(contact.user_id) != user_id:
        await update.message.reply_text("❌ Entropi tidak sepadan.")
        return
    
    count = user_access_count.get(user_id, 0) + 1
    user_access_count[user_id] = count
    ttl_seconds = get_fibonacci_ttl(count)
    expiry = int(time.time()) + ttl_seconds
    seed_hex = secrets.token_hex(32)
    
    try:
        quantum_hash, hash_source = calculate_quantum_hash_entanglement(user_id, seed_hex)
        quantum_matrix_id = generate_quantum_matrix_id(user_id)
        q_state_visual = " ".join(["|0⟩" if int(c,16)%2==0 else "|1⟩" for c in quantum_hash[:8]])
        
        token_data = {"u":user_id,"s":seed_hex,"h":quantum_hash,"exp":expiry,"tid":secrets.token_hex(16),"qid":quantum_matrix_id,"src":hash_source}
        token_safe = urllib.parse.quote(base64.b64encode(json.dumps(token_data).encode()).decode())
        
        msg = f"<b>[⚛️ ORIGIN QUANTUM]</b>\n\n• Hash: <code>{quantum_hash[:16]}...</code>\n• State: <code>{q_state_visual}</code>\n• Akses ke-: <code>{count}</code>"
        
        await update.message.reply_text(msg, parse_mode="HTML")
        await update.message.reply_text(f"🔗 <a href='{WEBAPPS_URL}?token={token_safe}'>🌌 Akses Portal</a>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"🔴 Ralat: {str(e)[:200]}", parse_mode="HTML")

# ============================================================
# MAIN
# ============================================================
def main() -> None:
    if not TOKEN:
        print("[RALAT FATAL] BOT_TOKEN tidak diset!")
        return
    
    # Build application
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mark", mark_used))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Initialize application
    asyncio.run(application.initialize())
    
    # Flask route untuk webhook
    @app.route(f'/{TOKEN}', methods=['POST'])
    def telegram_webhook():
        async def process():
            update = Update.de_json(request.get_json(force=True), application.bot)
            await application.process_update(update)
        asyncio.run(process())
        return 'OK'
    
    # Set webhook
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        httpx.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", json={"url": webhook_url})
        print(f"🚀 Webhook set: {webhook_url}")
    
    print("=" * 60)
    print("⚛️  ORIGIN QUANTUM ENTANGLEMENT GATE")
    print("=" * 60)
    print(f"🌐 Flask + Webhook: Port {PORT}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    main()
