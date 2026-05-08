import requests
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Tokens
BOT_TOKEN = "8714125008:AAGnNawfd0A_mVoZStJsrASu1bNylaYvJOg"
API_TOKEN = "94f30484e79c3073cc4e01667f63960eaac4a6ddb04fc59e7f6b7ea012f52c11" # Tu token de CODART

BASE_URL = "https://docs.consultasperu.com/~gitbook/mcp/api"
TIMEOUT = 60
LOG_FILE = "consultas_codart.txt"

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

def api_request(endpoint):
    """Ahora usa el token en los headers"""
    try:
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

        # Si el token está mal, la API tira 401
        if response.status_code == 401:
            return {"error": "Token de API inválido o expirado"}
        elif response.status_code == 429:
            return {"error": "Límite de consultas alcanzado"}

        data = response.json()
        return data if data.get("success") else None
    except Exception as e:
        print(f"Error API: {e}")
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
    print("Bot con Token CODART corriendo...")
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot online')

def run_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

Thread(target=run_server).start()

app.run_polling()