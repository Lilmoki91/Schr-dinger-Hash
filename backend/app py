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
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPPS_URL = "https://schr-dinger-hash.pages.dev"
MASTER_SEED = os.getenv("MASTER_SEED")  # Dari .env atau Render

PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

user_access_count = {}
used_tokens = set()

def get_fibonacci_ttl(count):
    fib = [1, 1, 2, 3, 5, 8, 13, 21]
    idx = min(count - 1, len(fib) - 1)
    ttl = fib[idx] * 30
    return min(ttl, 600)

def generate_quantum_matrix_id(user_id):
    """Hasilkan Quantum Matrix ID dari ID Telegram + Master Seed (Algebra Linear)"""
    try:
        # 1. Gabungkan ID + Master Seed
        combined = f"{MASTER_SEED}:{user_id}"
        
        # 2. Hash ke 256 bit
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        
        # 3. Tukar ke matriks 16x16 (256 elemen)
        matrix = np.frombuffer(hash_bytes, dtype=np.uint8).reshape(16, 16).astype(np.float64)
        
        # 4. Operasi Algebra Linear
        det = abs(np.linalg.det(matrix))
        trace = abs(np.trace(matrix))
        eigen = abs(np.linalg.eigvals(matrix)[0].real)
        
        # 5. Gabungan nilai
        combined_id = f"{det:.10f}:{trace:.10f}:{eigen:.10f}"
        matrix_id = hashlib.sha256(combined_id.encode()).hexdigest()[:16]
        
        return f"QuantumMatrix_{matrix_id}"
    except Exception as e:
        logging.error(f"Quantum Matrix ID gagal: {e}")
        # Fallback: guna hash biasa
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
    
    for i in range(6):
        circuit.append(cirq.CNOT(qubits[6], qubits[i]))
        
    simulator = cirq.Simulator()
    result = simulator.simulate(circuit)
    
    state_list = [1 if abs(val) > 0.5 else 0 for val in result.final_state_vector]
    state_str = json.dumps(state_list, separators=(',', ':'))
    
    return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("*LOG MASUK*", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "⚛️ Sistem Kedaulatan *Kuantum Metrix Aljabar* Aktif.\n\n  📌 Sila klik *'Log Masuk'* — _pengesahan entiti fizikal!._",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def mark_used(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tandakan token_id sebagai sudah digunakan"""
    tid = context.args[0] if context.args else None
    if tid:
        used_tokens.add(tid)
        await update.message.reply_text("marked")
        logging.info(f"Token {tid} marked as used")
    else:
        await update.message.reply_text("error: missing token_id")

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
    token_id = secrets.token_hex(16)
    # =======================================================

    seed_hex = secrets.token_hex(32)
    quantum_hash = calculate_quantum_signature(user_id, seed_hex)
    quantum_matrix_id = generate_quantum_matrix_id(user_id)  # <-- TAMBAH
    
    q_state_visual = " ".join(["|0⟩" if int(char, 16) % 2 == 0 else "|1⟩" for char in quantum_hash[:8]])
    
    token_data = {
        "u": user_id,
        "s": seed_hex,
        "h": quantum_hash,
        "exp": expiry,
        "tid": token_id,
        "qid": quantum_matrix_id   # <-- TAMBAH Quantum Public ID
    }
    
    json_str = json.dumps(token_data)
    token_bytes = base64.b64encode(json_str.encode("utf-8"))
    token_safe = urllib.parse.quote(token_bytes.decode("utf-8"))
    
    msg = (
        "<b>[⚛️ LITAR CIRQ TERKUNCI]</b>\n\n"
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
    
    await update.message.reply_text(msg, parse_mode="HTML")
    await update.message.reply_text(f"🔗 <a href='{full_url}'>🌌 Akses Portal Kuantum</a>", parse_mode="HTML")

def main() -> None:
    if not TOKEN:
        print("[RALAT FATAL] Fail .env tiada atau BOT_TOKEN tidak diset!")
        return
        
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mark", mark_used))
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
    print(f"🌀 Quantum Matrix ID aktif dengan MASTER_SEED: {MASTER_SEED[:6]}...")
    main()
