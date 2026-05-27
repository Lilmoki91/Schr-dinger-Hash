import hashlib
import time
import asyncio
import os
import nest_asyncio
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- FLASK WEB SERVER (Untuk Render Web Service) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Schrödinger Hash Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ENJIN KRIPTOGRAFI KUANTUM ---
class SchrödingerPythonEngine:
    @staticmethod
    def run_deterministic_circuit(seed_hex, challenge_str):
        combined_seed = seed_hex + challenge_str
        entropy_source = hashlib.sha256(combined_seed.encode()).hexdigest()
        quantum_nonce = ""
        for i in range(4):
            char_code = ord(entropy_source[i])
            control_qubit = "0" if (char_code % 2 == 0) else "1"
            quantum_nonce += control_qubit + control_qubit
        return quantum_nonce
    
    @staticmethod
    def verify_quantum_handshake(user_id_str, input_hash):
        seed_hex = hashlib.sha256(user_id_str.encode()).hexdigest()
        current_time_block = int(time.time() // 30)
        # Semak blok masa sekarang dan sebelumnya (untuk toleransi)
        for offset in [0, -1]:
            target_block = str(current_time_block + offset)
            q_nonce = SchrödingerPythonEngine.run_deterministic_circuit(seed_hex, target_block)
            combined_input = seed_hex + target_block + q_nonce
            calculated_hash = hashlib.sha256(combined_input.encode()).hexdigest()[:8].upper()
            if calculated_hash == input_hash.upper():
                return True, q_nonce, target_block
        return False, None, None

# --- TELEGRAM BOT LOGIC ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if context.args:
        incoming_hash = context.args[0].upper()
        success, matched_nonce, block_id = SchrödingerPythonEngine.verify_quantum_handshake(user_id, incoming_hash)
        if success:
            await update.message.reply_text(
                f"✅ *QUANTUM ENTANGLEMENT: SUCCESS*\n\n"
                f"🔐 *Hash:* `{incoming_hash}`\n"
                f"⚛️ *Nonce:* `{matched_nonce}`\n"
                f"⏳ *Block ID:* `{block_id}`\n\n"
                f"Akses disahkan.", parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ *WAVEFUNCTION COLLAPSE: MISMATCH*", parse_mode="Markdown")
        return
    await update.message.reply_text("Sila jana kod melalui WebApp.")

async def main():
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("RALAT: BOT_TOKEN tiada!")
        return

    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_handler))
    
    print("⚛️ SCHRÖDINGER HASH PLATFORM - STARTING...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    # Event loop untuk pastikan bot terus berjalan
    await asyncio.Event().wait()

if __name__ == "__main__":
    nest_asyncio.apply()
    # Jalankan Flask dalam thread berasingan
    threading.Thread(target=run_flask, daemon=True).start()
    # Jalankan bot
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"FATAL ERROR: {e}")
