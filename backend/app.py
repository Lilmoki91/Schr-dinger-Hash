import os
import logging
import hashlib
import secrets
import urllib.parse
import time
import json
import base64
import numpy as np
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================================
# ⚛️ ORIGIN QUANTUM — pyqpanda3 ENTANGLEMENT
# ============================================================
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
# FIBONACCI TTL
# ============================================================
def get_fibonacci_ttl(count):
    fib = [1, 1, 2, 3, 5, 8, 13, 21]
    idx = min(count - 1, len(fib) - 1)
    ttl = fib[idx] * 30
    return min(ttl, 600)

# ============================================================
# QUANTUM MATRIX ID (ALGEBRA LINEAR)
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
# ⚛️ ORIGIN QUANTUM — STATE VECTOR ENTANGLEMENT
# ============================================================
def calculate_quantum_hash_entanglement(user_id, seed_hex):
    """
    Litar Entanglement 8-Qubit menggunakan Origin Quantum.
    Output: STATE VECTOR (deterministik) — BUKAN counts.
    """
    
    logging.info("🇨🇳 Origin Quantum: Membina Litar Entanglement 8-Qubit...")
    
    # ========== BINA LITAR ==========
    prog = core.QProg()
    
    # Step 1: Init qubit dari seed (qubit 0-5)
    seed_bytes = bytes.fromhex(seed_hex[:12])
    for i in range(6):
        if (seed_bytes[i] % 2 == 1):
            prog << core.X(i)
    
    # Step 2: User ID ke qubit 6 & 7
    uid = int(user_id)
    if (uid % 256) > 128:
        prog << core.X(6)
    if ((uid >> 8) % 256) > 128:
        prog << core.X(7)
    
    # Step 3: Hadamard pada SEMUA 8 qubit — SUPERPOSISI
    for i in range(8):
        prog << core.H(i)
    
    # Step 4: CNOT — ENTANGLEMENT (8 pasangan)
    entanglement_pairs = [
        (0, 1), (2, 3), (4, 5), (6, 7),
        (0, 3), (1, 5), (2, 7), (4, 6),
    ]
    for control, target in entanglement_pairs:
        prog << core.CNOT(control, target)
    
    # ========== TANPA MEASURE — AMBIK STATE VECTOR ==========
    machine = core.CPUQVM()
    machine.run(prog)  # NO shots — dapatkan state vector penuh
    
    # Dapatkan state vector
    state_vector = machine.get_qstate()
    
    # Convert ke list Python
    if hasattr(state_vector, 'tolist'):
        state_list = state_vector.tolist()
    else:
        state_list = list(state_vector)
    
    # ========== BINA OBJEK STATE (SAMA DENGAN JAVASCRIPT) ==========
    state_obj = {
        "pairs": len(entanglement_pairs),
        "qubits": 8,
        "state_vector": [round(abs(float(x))**2, 10) for x in state_list]
    }
    
    # JSON dengan sorted keys (macam JavaScript)
    result_str = json.dumps(state_obj, sort_keys=True)
    
    # SHA-256 Hash
    quantum_hash = hashlib.sha256(result_str.encode()).hexdigest()
    
    logging.info(f"✅ Origin Entanglement Hash: {quantum_hash[:16]}...")
    
    return quantum_hash, "ORIGIN_ENTANGLEMENT"

# ============================================================
# BOT: /start
# ============================================================
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

# ============================================================
# BOT: /mark
# ============================================================
async def mark_used(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = context.args[0] if context.args else None
    if tid:
        used_tokens.add(tid)
        await update.message.reply_text("✅ Token ditandakan")
    else:
        await update.message.reply_text("❌ error: missing token_id")

# ============================================================
# BOT: HANDLE CONTACT (LOG MASUK)
# ============================================================
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    user_id = str(update.effective_user.id)
    
    # Sahkan identiti
    if str(contact.user_id) != user_id:
        await update.message.reply_text("❌ Entropi fizikal tidak sepadan. Klon dikesan.")
        return
    
    # Status processing
    status_msg = await update.message.reply_text("⚛️ Origin Quantum: Membina Litar Entanglement... 🇨🇳")
    
    # Kira akses
    count = user_access_count.get(user_id, 0) + 1
    user_access_count[user_id] = count
    ttl_seconds = get_fibonacci_ttl(count)
    expiry = int(time.time()) + ttl_seconds
    token_id = secrets.token_hex(16)
    
    # Generate seed dinamik
    seed_hex = secrets.token_hex(32)
    
    try:
        # ========== QUANTUM ENTANGLEMENT HASH ==========
        quantum_hash, hash_source = calculate_quantum_hash_entanglement(user_id, seed_hex)
        quantum_matrix_id = generate_quantum_matrix_id(user_id)
        
        # Visualisasi State 8-Qubit
        q_state_visual = " ".join([
            "|0⟩" if int(char, 16) % 2 == 0 else "|1⟩" 
            for char in quantum_hash[:8]
        ])
        
        # Bina token
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
        
        # Mesej ke user
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
            f"<i>🌀 Quantum Matrix ID kekal untuk ID Telegram ini</i>\n"
            f"<i>🔑 Hash dari State Vector (Deterministik)</i>"
        )
        
        full_url = f"{WEBAPPS_URL}?token={token_safe}"
        
        await status_msg.delete()
        await update.message.reply_text(msg, parse_mode="HTML")
        await update.message.reply_text(
            f"🔗 <a href='{full_url}'>🌌 Akses Portal Kuantum</a>", 
            parse_mode="HTML"
        )
        
        logging.info(f"✅ Token dijana untuk user {user_id} — Hash: {quantum_hash[:16]}...")
        
    except Exception as e:
        logging.error(f"🔴 RALAT ENTANGLEMENT: {e}")
        await status_msg.delete()
        await update.message.reply_text(
            f"🔴 <b>RALAT QUANTUM!</b>\n\n"
            f"<code>{str(e)[:200]}</code>\n\n"
            f"<i>Sila cuba lagi atau hubungi pembangun.</i>",
            parse_mode="HTML"
        )

# ============================================================
# MAIN
# ============================================================
def main() -> None:
    if not TOKEN:
        print("[RALAT FATAL] BOT_TOKEN tidak diset!")
        return
    
    print("=" * 60)
    print("⚛️  ORIGIN QUANTUM ENTANGLEMENT GATE")
    print("=" * 60)
    print(f"🌀 MASTER_SEED: {MASTER_SEED[:6]}...")
    print(f"🖥️ Backend: Origin Quantum CPUQVM 🇨🇳")
    print(f"🔗 Litar: 8-Qubit Hadamard + 8 Pasangan CNOT")
    print(f"📡 WebApps: {WEBAPPS_URL}")
    print("=" * 60)
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mark", mark_used))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    if RENDER_EXTERNAL_URL:
        print(f"🚀 Webhook aktif: {RENDER_EXTERNAL_URL}/{TOKEN}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        )
    else:
        print("📡 Polling tempatan...")
        application.run_polling()

if __name__ == '__main__':
    main()
