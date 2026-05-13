import os
import httpx
import asyncio
import json
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from aiohttp import web
from flask import Flask

# =====================================================
# TOKENS
# =====================================================
BOT_TOKEN = os.environ.get("TOKEN", "8714125008:AAGnNawfd0A_mVoZStJsrASu1bNylaYvJOg")
API_TOKEN = os.environ.get("API_PERU_TOKEN")

BASE_URL = "https://api.apis.net.pe/v1" # Usa apis.net.pe, es gratis y sin token
TIMEOUT = 60
LOG_FILE = "consultas_PERU.txt"

HEADERS = {
    "Accept": "application/json"
}

# =====================================================
# LOGS
# =====================================================
def guardar_log(comando, parametro, resultado):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(
                f"\n{'='*60}\n"
                f"FECHA: {fecha}\n"
                f"COMANDO: {comando} {parametro}\n"
                f"RESULTADO:\n"
                f"{json.dumps(resultado, indent=2, ensure_ascii=False)}\n"
                f"{'='*60}\n"
            )
    except Exception as e:
        print(f"Error guardando log: {e}")

# =====================================================
# HELPERS
# =====================================================
def get_message(update: Update):
    return update.effective_message or update.message

# =====================================================
# API REQUEST
# =====================================================
async def consulta_api(tipo, numero):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if tipo == "dni":
                url = f"https://api.apis.net.pe/v2/reniec/dni"
                params = {"numero": numero}
            elif tipo == "ruc":
                url = f"https://api.apis.net.pe/v2/sunat/ruc"
                params = {"numero": numero}
            elif tipo == "telx":
                url = f"https://api.apis.net.pe/v1/operator"
                params = {"phone": numero}
            else:
                return {"error": "Tipo de consulta no válido"}

            headers = {"Referer": "https://apis.net.pe"}
            response = await client.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                return response.json()
            return {"error": f"Error {response.status_code} en la API"}

    except Exception as e:
        return {"error": str(e)}

# =====================================================
# START
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📑 RUC SUNAT", callback_data='menu_ruc')],
        [InlineKeyboardButton("🪪 DNI RENIEC", callback_data='menu_dni')],
        [InlineKeyboardButton("📱 Líneas OSIPTEL", callback_data='menu_osiptel')],
        [InlineKeyboardButton("🚨 Buscar Número", callback_data='menu_telx')],
        [InlineKeyboardButton("📁 Base AG", callback_data='menu_ag')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    texto = """
🤖 *BOT CONSULTAS PERÚ*

📌 COMANDOS:
• `/dni 12345678`
• `/ruc 20538856674`
• `/telx 999888777`
"""

    mensaje = get_message(update)
    try:
        with open("yo.jpg", "rb") as foto:
            await mensaje.reply_photo(
                photo=foto,
                caption=texto,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    except FileNotFoundError:
        await mensaje.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")

# =====================================================
# BUTTONS
# =====================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ejemplos = {
        "menu_ruc": "📑 *Consulta RUC*\n\n`/ruc 20538856674`",
        "menu_dni": "🪪 *Consulta DNI*\n\n`/dni 12345678`",
        "menu_osiptel": "📱 *Consulta OSIPTEL*\n\n`/osiptel 12345678`",
        "menu_telx": "🚨 *Buscar Número*\n\n`/telx 999888777`",
        "menu_ag": "📁 *Base AG*\n\n`/ag 12345678`"
    }
    texto = ejemplos.get(query.data, "❌ Opción no encontrada")

    try:
        await query.edit_message_caption(caption=texto, parse_mode="Markdown")
    except:
        await query.edit_message_text(text=texto, parse_mode="Markdown")

# =====================================================
# COMANDOS
# =====================================================
async def dni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = get_message(update)
    if not context.args:
        await mensaje.reply_text("❌ Uso: /dni 12345678")
        return

    dni_num = context.args[0]
    if len(dni_num)!= 8 or not dni_num.isdigit():
        await mensaje.reply_text("❌ DNI inválido")
        return

    msg = await mensaje.reply_text("🔍 Consultando RENIEC...")
    data = await consulta_api("dni", dni_num)

    if "error" in data:
        await msg.edit_text(f"❌ {data['error']}")
        return

    guardar_log("/dni", dni_num, data)
    nombre = f"{data.get('nombres', '')} {data.get('apellidoPaterno', '')} {data.get('apellidoMaterno', '')}"
    texto = f"🪪 *DATOS RENIEC*\n\n✅ DNI: {dni_num}\n👤 Nombre: {nombre}"
    await msg.edit_text(texto, parse_mode="Markdown")

async def ruc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = get_message(update)
    if not context.args:
        await mensaje.reply_text("❌ Uso: /ruc 20538856674")
        return

    ruc_num = context.args[0]
    if len(ruc_num)!= 11 or not ruc_num.isdigit():
        await mensaje.reply_text("❌ RUC inválido")
        return

    msg = await mensaje.reply_text("🔍 Consultando SUNAT...")
    data = await consulta_api("ruc", ruc_num)

    if "error" in data:
        await msg.edit_text(f"❌ {data['error']}")
        return

    guardar_log("/ruc", ruc_num, data)
    razon = data.get("razonSocial", "N/A")
    estado = data.get("estado", "N/A")
    texto = f"📑 *DATOS SUNAT*\n\n✅ RUC: {ruc_num}\n🏢 Razón Social: {razon}\n📊 Estado: {estado}"
    await msg.edit_text(texto, parse_mode="Markdown")

async def telx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = get_message(update)
    if not context.args:
        await mensaje.reply_text("❌ Uso: /telx 999888777")
        return

    numero = context.args[0]
    msg = await mensaje.reply_text("🔍 Consultando número...")
    data = await consulta_api("telx", numero)

    if "error" in data:
        await msg.edit_text(f"❌ {data['error']}")
        return

    guardar_log("/telx", numero, data)
    operador = data.get("operator", "N/A")
    texto = f"📱 *DATOS NÚMERO*\n\n✅ Número: {numero}\n📶 Operador: {operador}"
    await msg.edit_text(texto, parse_mode="Markdown")

# =====================================================
# MAIN
# =====================================================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dni", dni))
    app.add_handler(CommandHandler("ruc", ruc))
    app.add_handler(CommandHandler("telx", telx))
    app.add_handler(CallbackQueryHandler(button_handler))

    sync def main():
    print("Bot con Token CODART corriendo...")
    
    TOKEN = os.environ["TOKEN"]
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo 24/7"

@bot.message_handler(func=lambda m: True)
    bot.reply_to(m, f"Me dijiste: {m.text}")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # Inicia el bot en segundo plano
    threading.Thread(target=run_bot, daemon=True).start()
    # Inicia el servidor web para que Render no lo mate
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))