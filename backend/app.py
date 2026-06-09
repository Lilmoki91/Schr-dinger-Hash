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
# ⚛️ ORIGIN QUANTUM — HARDWARE SEBENAR SAHAJA
# ============================================================
try:
    from pyqpanda import *
    ORIGIN_QUANTUM_AVAILABLE = True
    print("✅ pyQPanda loaded — Origin Quantum Hardware TERSEDIA!")
except ImportError:
    ORIGIN_QUANTUM_AVAILABLE = False
    print("🔴 pyQPanda TIDAK dijumpai! Sistem tidak boleh berjalan.")
    print("🔴 Sila install: pip install pyqpanda")
    raise SystemExit("Origin Quantum SDK diperlukan!")

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPPS_URL = "https://schr-dinger-hash.pages.dev"
MASTER_SEED = os.getenv("MASTER_SEED")
ORIGINQ_API_KEY = os.getenv("ORIGINQ_API_KEY")
ORIGINQ_URL = os.getenv("ORIGINQ_URL", "https://qcloud.originqc.com.cn/")

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
# ⚛️ ORIGIN QUANTUM — CLOUD HARDWARE
# ============================================================
def calculate_quantum_hash_cloud(user_id, seed_hex):
    """Jana Quantum Hash menggunakan Origin Quantum Cloud SEBENAR"""
    
    logging.info("🇨🇳 Menyambung ke Origin Quantum Cloud...")
    
    # Init quantum machine dengan API key
    machine = init_quantum_machine(QMachineType.QCLOUD)
    machine.set_config({
        "api_key": ORIGINQ_API_KEY,
        "url": ORIGINQ_URL
    })
    
    logging.info("✅ CloudQVM bersedia — Hardware sebenar!")
    
    # Alokasi 8 qubit + 8 classical bit
    qubits = qAlloc_many(8)
    cbits = cAlloc_many(8)
    prog = QProg()
    
    # Init qubit dari seed
    seed_bytes = bytes.fromhex(seed_hex[:12])
    for i in range(6):
        if (seed_bytes[i] % 2 == 1):
            prog << X(qubits[i])
    
    # User ID ke qubit 6 & 7
    uid = int(user_id)
    if (uid % 256) > 128:
        prog << X(qubits[6])
    if ((uid >> 8) % 256) > 128:
        prog << X(qubits[7])
    
    # Hadamard — Superposisi
    for i in range(8):
        prog << H(qubits[i])
    
    # CNOT — Entanglement
    entanglement_pairs = [
        (0, 1), (2, 3), (4, 5), (6, 7),
        (0, 3), (1, 5), (2, 7), (4, 6),
    ]
    for control, target in entanglement_pairs:
        prog << CNOT(qubits[control], qubits[target])
    
    # Measure
    for i in range(8):
        prog << Measure(qubits[i], cbits[i])
    
    # Hantar ke hardware
    logging.info("⚛️ Menghantar litar ke Origin Quantum Hardware...")
    result = run_with_configuration(prog, cbits, 1000)
    
    # Generate hash dari quantum result
    result_str = json.dumps(result, sort_keys=True)
    quantum_hash = hashlib.sha256(result_str.encode()).hexdigest()
    
    finalize()
    
    logging.info(f"✅ Quantum Hash dari Origin Cloud: {quantum_hash[:16]}...")
    return quantum_hash, "ORIGIN_QUANTUM_CLOUD"

# ============================================================
# ⚛️ ORIGIN QUANTUM — CPUQVM (FALLBACK TEMPATAN)
# ============================================================
def calculate_quantum_hash_cpuqvm(user_id, seed_hex):
    """Fallback: Guna Origin CPUQVM (simulator tempatan Origin)"""
    
    logging.info("💻 Menggunakan Origin CPUQVM (simulator tempatan)...")
    
    # Init local quantum machine
    init(QMachineType.CPU)
    
    # Alokasi 8 qubit + 8 classical bit
    qubits = qAlloc_many(8)
    cbits = cAlloc_many(8)
    prog = QProg()
    
    # Init qubit dari seed
    seed_bytes = bytes.fromhex(seed_hex[:12])
    for i in range(6):
        if (seed_bytes[i] % 2 == 1):
            prog << X(qubits[i])
    
    # User ID ke qubit 6 & 7
    uid = int(user_id)
    if (uid % 256) > 128:
        prog << X(qubits[6])
    if ((uid >> 8) % 256) > 128:
        prog << X(qubits[7])
    
    # Hadamard — Superposisi
    for i in range(8):
        prog << H(qubits[i])
    
    # CNOT — Entanglement
    entanglement_pairs = [
        (0, 1), (2, 3), (4, 5), (6, 7),
        (0, 3), (1, 5), (2, 7), (4, 6),
    ]
    for control, target in entanglement_pairs:
        prog << CNOT(qubits[control], qubits[target])
    
    # Measure
    for i in range(8):
        prog << Measure(qubits[i], cbits[i])
    
    # Run pada simulator tempatan
    result = run_with_configuration(prog, cbits, 1000)
    
    # Generate hash dari quantum result
    result_str = json.dumps(result, sort_keys=True)
    quantum_hash = hashlib.sha256(result_str.encode()).hexdigest()
    
    finalize()
    
    logging.info(f"✅ Quantum Hash dari Origin CPUQVM: {quantum_hash[:16]}...")
    return quantum_hash, "ORIGIN_CPUQVM"

# ============================================================
# WRAPPER — PILIH CLOUD ATAU CPUQVM
# ============================================================
def calculate_quantum_signature(user_id, seed_hex):
    """Pilih Origin Cloud dulu, fallback ke CPUQVM jika gagal"""
    
    # Cuba Cloud dulu
    if ORIGINQ_API_KEY:
        try:
            return calculate_quantum_hash_cloud(user_id, seed_hex)
        except Exception as cloud_error:
            logging.warning(f"⚠️ Origin Cloud gagal: {cloud_error}")
            logging.info("🔄 Fallback ke Origin CPUQVM...")
            try:
                return calculate_quantum_hash_cpuqvm(user_id, seed_hex)
            except Exception as cpu_error:
                logging.error(f"🔴 Origin CPUQVM juga gagal: {cpu_error}")
                raise Exception(f"Kedua-dua backend gagal. Cloud: {cloud_error}, CPU: {cpu_error}")
    else:
        # Tiada API key — guna CPUQVM terus
        logging.info("📝 Tiada API Key. Menggunakan Origin CPUQVM...")
        return calculate_quantum_hash_cpuqvm(user_id, seed_hex)

# ============================================================
# BOT HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("LOG MASUK", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    backend = "Origin Quantum Cloud 🇨🇳☁️" if ORIGINQ_API_KEY else "Origin CPUQVM 🇨🇳💻"
    
    await update.message.reply_text(
        f"⚛️ *ORIGIN QUANTUM IDENTITY GATE*\n\n"
        f"🖥️ Backend: *{backend}*\n"
        f"🔬 Litar: *8-Qubit Hadamard + CNOT*\n\n"
        f"📌 Klik *'LOG MASUK'* untuk verifikasi entiti fizikal.",
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

    status_msg = await update.message.reply_text("⚛️ Menjana litar kuantum... 🇨🇳")

    count = user_access_count.get(user_id, 0) + 1
    user_access_count[user_id] = count
    ttl_seconds = get_fibonacci_ttl(count)
    expiry = int(time.time()) + ttl_seconds
    token_id = secrets.token_hex(16)

    seed_hex = secrets.token_hex(32)
    
    try:
        quantum_hash, hash_source = calculate_quantum_signature(user_id, seed_hex)
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
        
        hw_map = {
            "ORIGIN_QUANTUM_CLOUD": "🇨🇳☁️ Origin Quantum Cloud",
            "ORIGIN_CPUQVM": "🇨🇳💻 Origin CPUQVM"
        }
        hw_label = hw_map.get(hash_source, hash_source)
        
        msg = (
            f"<b>[⚛️ ORIGIN QUANTUM — LITAR TERKUNCI]</b>\n\n"
            f"<b>🖥️ Hardware:</b> <i>{hw_label}</i>\n"
            f"<b>🔬 Source:</b> <code>{hash_source}</code>\n\n"
            f"<b>• User ID:</b> <code>{user_id}</code>\n"
            f"<b>• Quantum Matrix ID:</b> <code>{quantum_matrix_id}</code>\n"
            f"<b>• Akses ke-:</b> <code>{count}</code>\n"
            f"<b>• Token sah:</b> <code>{ttl_seconds} saat ({ttl_seconds/60:.1f} minit)</code>\n"
            f"<b>• Seed:</b> <code>{seed_hex[:12]}...</code>\n"
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
        await update.message.reply_text(
            f"🔴 <b>RALAT QUANTUM!</b>\n\n"
            f"<code>{str(e)[:200]}</code>\n\n"
            f"<i>Sila cuba lagi nanti.</i>",
            parse_mode="HTML"
        )

def main() -> None:
    if not TOKEN:
        print("[RALAT FATAL] BOT_TOKEN tidak diset!")
        return
    
    print("=" * 50)
    print("⚛️  ORIGIN QUANTUM IDENTITY GATE")
    print("=" * 50)
    print(f"🌀 MASTER_SEED: {MASTER_SEED[:6]}...")
    print(f"🖥️ Backend: {'Cloud 🇨🇳☁️' if ORIGINQ_API_KEY else 'CPUQVM 🇨🇳💻'}")
    print(f"🔗 WebApps: {WEBAPPS_URL}")
    print("=" * 50)
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mark", mark_used))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    if RENDER_EXTERNAL_URL:
        print(f"🚀 Webhook: {RENDER_EXTERNAL_URL}/{TOKEN}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        )
    else:
        print("📡 Polling...")
        application.run_polling()

if __name__ == '__main__':
    main()
