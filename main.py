import os
import asyncio
import requests
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from aiohttp import web

# Tokens
BOT_TOKEN = "8714125008:AAGnNawfd0A_mVoZStJsrASu1bNylaYvJOg"
API_TOKEN = os.environ.get("API_PERU_TOKEN")
 # Tu token de CODART.

BASE_URL = "https://api.consultasperu.com/api/v1/query"
TIMEOUT = 60
LOG_FILE = "consultas_PERU.txt"

# Headers con el token de CODART
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json"
}

def guardar_log(comando, parametro, resultado):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'='*60}\nFECHA: {fecha}\nCOMANDO: {comando} {parametro}\n")
        f.write(f"RESULTADO:\n{json.dumps(resultado, indent=2, ensure_ascii=False)}\n{'='*60}\n")

def consulta_api(type_document, document_number):
    """Función corregida para ConsultasPeru - usa POST"""
    headers = {"Content-Type": "application/json"}
    body = {
        "token": API_PERU_TOKEN,
        "type_document": type_document,  # "dni" o "ruc"
        "document_number": document_number
    }
    try:
        r = requests.post(BASE_URL, headers=headers, json=body, timeout=15)
        data = r.json()
        if r.status_code == 200 and data.get("success") == True:
            return data.get("data")
        else:
            return {"error": data.get("message", "Error en API pe mano")}
    except Exception as e:
        return {"error": f"API caída o sin saldo: {e} 3"}
        return None

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
🤖 *Bot XXXDATAXXX prueba*

Selecciona o usa comandos:
    """
    
    # Manda tu foto + texto + botones
    try:
        with open('yo.jpg', 'rb') as foto:
            await update.message.reply_photo(
                photo=foto,
                caption=texto,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except FileNotFoundError:
        # Si no encuentra la foto, manda solo texto
        await update.message.reply_text(
            texto + "\n\n⚠️ Falta yo.jpg",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ejemplos = {
        'menu_ruc': "Envía: `/ruc 20538856674`",
        'menu_dni': "Envía: `/dni 12345678`",
        'menu_osiptel': "Envía: `/osiptel 12345678`",
        'menu_telx': "Envía: `/telx 999888777`",
        'menu_ag': "Envía: `/ag 12345678`"
    }
    await query.edit_message_text(f"✅ {ejemplos[query.data]}", parse_mode='Markdown')

# 1. API SUNAT RUC
async def ruc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args[0])!= 11:
        await update.message.reply_text("❌ Uso: /ruc 20538856674")
        return
    ruc_num = context.args[0]
    msg = await update.message.reply_text("🔍 Consultando SUNAT...")
    data = api_request(f"sunat/ruc/{ruc_num}")

    if data and "error" not in data:
        r = data["result"]
        texto = f"*{r['razon_social']}*\n\n*RUC:* `{r['numero_documento']}`\n"
        texto += f"*Estado:* {r['estado']} - {r['condicion']}\n"
        texto += f"*Dirección:* {r['direccion']}\n*Ubicación:* {r['distrito']} / {r['provincia']}"
        guardar_log("/ruc", ruc_num, data)
        await msg.edit_text(texto, parse_mode='Markdown')
    elif data and "error" in data:
        await msg.edit_text(f"❌ {data['error']}")
    else:
        await msg.edit_text("❌ RUC no encontrado")

# 2. API RENIEC DNI
async def dni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args[0])!= 8:
        await update.message.reply_text("❌ Uso: /dni 12345678")
        return
    dni_num = context.args[0]
    msg = await update.message.reply_text("🔍 Consultando RENIEC...")
    data = api_request(f"reniec/dni/{dni_num}")

    if data and "error" not in data:
        r = data["result"]
        texto = f"*{r['nombres']} {r['apellido_paterno']} {r['apellido_materno']}*\n\n"
        texto += f"*DNI:* `{r['dni']}`\n*Edad:* {r.get('edad', 'N/A')}\n"
        texto += f"*Sexo:* {r.get('sexo', 'N/A')}\n*Dirección:* {r.get('direccion', 'N/A')}"
        guardar_log("/dni", dni_num, data)
        await msg.edit_text(texto, parse_mode='Markdown')
    elif data and "error" in data:
        await msg.edit_text(f"❌ {data['error']}")
    else:
        await msg.edit_text("❌ DNI no encontrado")

# 3. API BD AG
async def ag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Uso: /ag 12345678")
        return
    dni_num = context.args[0]
    msg = await update.message.reply_text("🔍 Buscando en BD AG...")
    data = api_request(f"bd/ag/{dni_num}")
    if data and "error" not in data:
        guardar_log("/ag", dni_num, data)
        await msg.edit_text(f"```json\n{json.dumps(data['result'], indent=2, ensure_ascii=False)}```", parse_mode='Markdown')
    else:
        await msg.edit_text(f"❌ {data.get('error', 'Sin resultados en BD AG')}")

# 4. API BD TELX
async def telx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Uso: /telx 999888777")
        return
    num = context.args[0]
    msg = await update.message.reply_text("🔍 Consultando número...")
    data = api_request(f"bd/telx/{num}")
    if data and "error" not in data:
        guardar_log("/telx", num, data)
        await msg.edit_text(f"```json\n{json.dumps(data['result'], indent=2, ensure_ascii=False)}```", parse_mode='Markdown')
    else:
        await msg.edit_text(f"❌ {data.get('error', 'Número no encontrado')}")

# 5. API BD OSIPTEL
async def osiptel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args[0])!= 8:
        await update.message.reply_text("❌ Uso: /osiptel 12345678")
        return
    dni_num = context.args[0]
    msg = await update.message.reply_text("🔍 Consultando OSIPTEL...")
    data = api_request(f"bd/osiptel/{dni_num}")
    if data and "error" not in data:
        guardar_log("/osiptel", dni_num, data)
        await msg.edit_text(f"```json\n{json.dumps(data['result'], indent=2, ensure_ascii=False)}```", parse_mode='Markdown')
    else:
        await msg.edit_text(f"❌ {data.get('error', 'Sin líneas registradas')}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler('ruc', ruc))
    app.add_handler(CommandHandler('dni', dni))
    app.add_handler(CommandHandler('ag', ag))
    app.add_handler(CommandHandler('telx', telx))
    app.add_handler(CommandHandler('osiptel', osiptel))

async def handle(request):
    return web.Response(text="Bot online")

async def main():
    print("Bot con Token CODART corriendo...")
    
    webapp = web.Application()
    webapp.add_routes([web.get('/', handle)])
    runner = web.AppRunner(webapp)
    await runner.setup()
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print("Servidor web iniciado")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())