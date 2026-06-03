import os
import logging
import hashlib
import secrets
import urllib.parse
import time
import cirq
import json
import base64
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPPS_URL = "https://schr-dinger-hash.pages.dev"

PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ======================= TAMBAHAN BARU =======================
# 1. Fibonacci TTL
# 2. Sekali pakai (tracking token)
# =============================================================
user_access_count = {}
used_tokens = set()  # Track token yang sudah digunakan

def get_fibonacci_ttl(count):
    fib = [1, 1, 2, 3, 5, 8, 13, 21]
    idx = min(count - 1, len(fib) - 1)
    ttl = fib[idx] * 30
    return min(ttl, 600)

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
    
    for i in range(6):
        circuit.append(cirq.CNOT(qubits[6], qubits[i]))
        
    simulator = cirq.Simulator()
    result = simulator.simulate(circuit)
    
    state_list = [1 if abs(val) > 0.5 else 0 for val in result.final_state_vector]
    state_str = json.dumps(state_list, separators=(',', ':'))
    
    return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("Kongsikan Nombor Telefon Rasmi", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Sistem Kedaulatan Kuantum Aktif. Sila sahkan entiti fizikal.", reply_markup=reply_markup)

# ========== TAMBAHAN: HANDLER CHECK TOKEN ==========
async def check_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Semak sama ada token_id sudah digunakan"""
    tid = context.args[0] if context.args else None
    if tid and tid in used_tokens:
        await update.message.reply_text("used")
    else:
        await update.message.reply_text("ok")
# ===================================================

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    user_id = str(update.effective_user.id)
    
    if str(contact.user_id) != user_id:
        await update.message.reply_text("Ralat: Entropi fizikal tidak sepadan. Klon dikesan.")
        return

    # ========== KIRA ACCESS COUNT & FIBONACCI TTL ==========
    count = user_access_count.get(user_id, 0) + 1
    user_access_count[user_id] = count
    ttl_seconds = get_fibonacci_ttl(count)
    expiry = int(time.time()) + ttl_seconds
    token_id = secrets.token_hex(16)  # Untuk "sekali pakai"
    # =======================================================

    seed_hex = secrets.token_hex(32)
    quantum_hash = calculate_quantum_signature(user_id, seed_hex)
    
    q_state_visual = " ".join(["|0⟩" if int(char, 16) % 2 == 0 else "|1⟩" for char in quantum_hash[:8]])
    
    # ========== TOKEN DENGAN TAMBAHAN ==========
    token_data = {
        "u": user_id,
        "s": seed_hex,
        "h": quantum_hash,
        "exp": expiry,      # TTL Fibonacci
        "tid": token_id     # Untuk sekali pakai
    }
    # ===========================================
    json_str = json.dumps(token_data)
    token_bytes = base64.b64encode(json_str.encode("utf-8"))
    token_safe = urllib.parse.quote(token_bytes.decode("utf-8"))
    
    msg = (
        "<b>[LITAR CIRQ TERKUNCI]</b>\n\n"
        f"<b>• User ID:</b> <code>{user_id}</code>\n"
        f"<b>• Akses ke-:</b> <code>{count}</code>\n"
        f"<b>• Token sah:</b> <code>{ttl_seconds} saat ({ttl_seconds/60:.1f} minit)</code>\n"
        f"<b>• Seed (Dinamic):</b> <code>{seed_hex[:12]}...</code>\n"
        f"<b>• State 8-Qubit:</b> <code>{q_state_visual}</code>\n"
        f"<b>• Hash Kuantum:</b> <code>{quantum_hash[:16]}...</code>\n\n"
    )
    
    full_url = f"{WEBAPPS_URL}?token={token_safe}"
    
    await update.message.reply_text(msg, parse_mode="HTML")
    await update.message.reply_text(f"🔗 <a href='{full_url}'>Akses Portal Kuantum</a>", parse_mode="HTML")

def main() -> None:
    if not TOKEN:
        print("[RALAT FATAL] Fail .env tiada atau BOT_TOKEN tidak diset!")
        return
        
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_token))  # <-- TAMBAH HANDLER
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    if RENDER_EXTERNAL_URL:
        print(f"Mengikat Web Service pada port {PORT}. Menunggu isyarat masuk...")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        )
    else:
        print("Tiada URL Render dikesan. Menjalankan fallback Polling tempatan...")
        application.run_polling()

if __name__ == '__main__':
    main()
