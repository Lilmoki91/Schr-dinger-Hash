import os
import logging
import hashlib
import secrets
import urllib.parse
import cirq
import json
import base64
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Muatkan pembolehubah dari .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
# Pastikan URL ini menuju tepat ke index.html (Gerbang Kuantum)
WEBAPPS_URL = "https://lilmoki91.github.io/Schr-dinger-Hash/index.html"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def calculate_quantum_signature(user_id, seed_hex):
    """Enjin Cirq: State Vector 8-qubit + CNOT Entanglement"""
    qubits = cirq.LineQubit.range(8)
    circuit = cirq.Circuit()
    
    # 1. Inisialisasi: 6 Qubit dinamik (seed)
    seed_bytes = bytes.fromhex(seed_hex[:12])
    for i in range(6):
        if (seed_bytes[i] % 2 == 1):
            circuit.append(cirq.X(qubits[i]))
            
    # 2. Inisialisasi: 2 Qubit statik (user_id anchor)
    uid = int(user_id)
    if (uid % 256) > 128: circuit.append(cirq.X(qubits[6]))
    if ((uid >> 8) % 256) > 128: circuit.append(cirq.X(qubits[7]))
    
    # 3. CNOT Entanglement (Control: Qubit 6, Target: Qubit 0-5)
    for i in range(6):
        circuit.append(cirq.CNOT(qubits[6], qubits[i]))
        
    # 4. Simulasi Cirq Sebenar
    simulator = cirq.Simulator()
    result = simulator.simulate(circuit)
    
    # 5. Ekstrak amplitud kepada senarai integer 0 dan 1 (Mengelakkan ralat JSON complex object)
    state_list = [1 if abs(val) > 0.5 else 0 for val in result.final_state_vector]
    
    # 6. Serialization seragam untuk JS (output: "[0,0,0,1,0...]")
    state_str = json.dumps(state_list, separators=(',', ':'))
    
    return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("Kongsikan Nombor Telefon Rasmi", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Sistem Kedaulatan Kuantum Aktif. Sila sahkan entiti fizikal.", reply_markup=reply_markup)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    user_id = str(update.effective_user.id)
    
    if str(contact.user_id) != user_id:
        await update.message.reply_text("Ralat: Entropi fizikal tidak sepadan. Klon dikesan.")
        return

    # Jana data kuantum
    seed_hex = secrets.token_hex(32)
    quantum_hash = calculate_quantum_signature(user_id, seed_hex)
    
    # --- PROSES ENKRIPSI BASE64 (Sesuai dengan webapps terkini) ---
    token_data = {
        "u": user_id,
        "s": seed_hex,
        "h": quantum_hash
    }
    # Tukar ke format JSON string
    json_str = json.dumps(token_data)
    # Enkod ke Base64
    token_bytes = base64.b64encode(json_str.encode("utf-8"))
    # Pastikan URL selamat (buang aksara bermasalah)
    token_safe = urllib.parse.quote(token_bytes.decode("utf-8"))
    # --------------------------------------------------------------
    
    msg = (
        "<b>[LITAR CIRQ TERKUNCI]</b>\n\n"
        f"<b>• User ID:</b> <code>{user_id}</code>\n"
        f"<b>• Seed (Dinamic):</b> <code>{seed_hex[:12]}...</code>\n"
        f"<b>• Hash Kuantum:</b> <code>{quantum_hash[:16]}...</code>\n\n"
    )
    
    # Pautan Webapps yang telah disulitkan (hanya menggunakan parameter ?token=)
    full_url = f"{WEBAPPS_URL}?token={token_safe}"
    
    await update.message.reply_text(msg, parse_mode="HTML")
    await update.message.reply_text(f"🔗 <a href='{full_url}'>Akses Portal Kuantum</a>", parse_mode="HTML")

def main() -> None:
    if not TOKEN:
        print("[RALAT FATAL] Fail .env tiada atau BOT_TOKEN tidak diset!")
        return
        
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    print("Enjin Cirq sedang beroperasi. Menunggu jalinan litar...")
    application.run_polling()

if __name__ == '__main__':
    main()
