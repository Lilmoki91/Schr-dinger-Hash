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

# Muatkan pembolehubah dari persekitaran (Environment Variables)
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPPS_URL = "https://lilmoki91.github.io/Schr-dinger-Hash/index.html"

# Pembolehubah khusus untuk Web Service di Render
PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def calculate_quantum_signature(user_id, seed_hex):
    """Enjin Cirq: State Vector 8-qubit + CNOT Entanglement"""
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

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    user_id = str(update.effective_user.id)
    
    if str(contact.user_id) != user_id:
        await update.message.reply_text("Ralat: Entropi fizikal tidak sepadan. Klon dikesan.")
        return

    seed_hex = secrets.token_hex(32)
    quantum_hash = calculate_quantum_signature(user_id, seed_hex)
    
    q_state_visual = " ".join(["|0⟩" if int(char, 16) % 2 == 0 else "|1⟩" for char in quantum_hash[:8]])
    
    token_data = {
        "u": user_id,
        "s": seed_hex,
        "h": quantum_hash
    }
    json_str = json.dumps(token_data)
    token_bytes = base64.b64encode(json_str.encode("utf-8"))
    token_safe = urllib.parse.quote(token_bytes.decode("utf-8"))
    
    msg = (
        "<b>[LITAR CIRQ TERKUNCI]</b>\n\n"
        f"<b>• User ID:</b> <code>{user_id}</code>\n"
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
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Deteksi persekitaran secara dinamik
    if RENDER_EXTERNAL_URL:
        # Mod Web Service (Webhook) untuk server Render
        print(f"Mengikat Web Service pada port {PORT}. Menunggu isyarat masuk...")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        )
    else:
        # Mod Polling jika dijalankan pada komputer tempatan (Local)
        print("Tiada URL Render dikesan. Menjalankan fallback Polling tempatan...")
        application.run_polling()

if __name__ == '__main__':
    main()
