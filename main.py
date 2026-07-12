import json
import httpx
import datetime
import os
import base64
import io
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from flask import Flask
from threading import Thread
import asyncio

# Forzar la creación de un event loop si no existe en este hilo
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot activo"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = [str(os.getenv("ADMIN_ID"))] # Lista para poder agregar varios admins
ARCHIVO_USUARIOS = os.getenv("ARCHIVO_USUARIOS") or "usuarios.json"
BOT_USER = "@OFICIAL_DATA_BOT"
BOT_NAME = "⚜ DATA_PERU⚜"
BASE_URL = "https://api-codart.cgrt.org"

PRECIOS = {
    "dni": 4, "agv": 8, "telx": 15, "ruc": 5,
    "denuncia": 10, "placa": 12, "nm": 6, "hsoat": 8, "denpla": 30, "dnit": 5, "telp": 15
}

# ===== FUNCIONES BASE =====
def cargar_usuarios():
    try:
        with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_usuarios(data):
    with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_fecha():
    return datetime.datetime.now().strftime("%d/%m/%Y - %I:%M:%S %p")

async def validar_creditos(user_id, comando, usuarios):
    costo = PRECIOS[comando]
    if usuarios.get(user_id, {}).get("creditos", 0) < costo:
        return False, f"No tienes creditos suficientes. Necesitas {costo}. Usa /buy"
    return True, costo

async def consultar_api_get(url):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=headers)
            return r.json()
    except Exception as e:
        return {"error": str(e)}

# ===== COMANDOS GENERALES =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = f"""⚜️ <b>¡BIENVENIDO A DATA PERÚ!</b> ⚜️

━━━━━━━━━━━━━━━━━━

📌 <b>INFORMACIÓN DEL BOT</b>

🏷️ <b>Nombre:</b> {BOT_NAME}
👤 <b>Usuario:</b> {BOT_USER}
🚀 <b>Versión:</b> v2.1 CODART V1

━━━━━━━━━━━━━━━━━━

📚 <b>COMANDOS GENERALES</b>

📝 /register ➾ Registrar cuenta
📖 /cmds ➾ Lista de comandos
👤 /me ➾ Ver tu perfil
🛡️ /staff ➾ Ver el staff
💳 /buy ➾ Comprar créditos/días

━━━━━━━━━━━━━━━━━━

⚡ <b>EN CONSTANTE EVOLUCIÓN</b>

Gracias por utilizar <b>DATA PERÚ</b>.
"""

    await update.message.reply_text(
        texto,
        parse_mode="HTML"
    )
async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("RENIEC", callback_data="cmd_reniec"),
            InlineKeyboardButton("RUC", callback_data="cmd_ruc")
        ],
        [
            InlineKeyboardButton("VEHÍCULOS", callback_data="cmd_vehiculos"),
            InlineKeyboardButton("TELÉFONO", callback_data="cmd_telefono")
        ],
        [
            InlineKeyboardButton("DENUNCIAS", callback_data="cmd_denuncia"),
            InlineKeyboardButton("NOMBRES", callback_data="cmd_nm")
        ],
        [
            InlineKeyboardButton("PERFIL", callback_data="cmd_me"),
            InlineKeyboardButton("COMPRAR", callback_data="cmd_buy")
        ]
    ])

    texto = f"""[ PANEL DE COMANDOS ]

Precios por consulta:
DNI: {PRECIOS['dni']} | RUC: {PRECIOS['ruc']} | PLACA: {PRECIOS['placa']} | TEL: {PRECIOS['telp']}
AGV: {PRECIOS['agv']} | DENUNCIA: {PRECIOS['denuncia']} | NOMBRE: {PRECIOS['nm']}

Selecciona un boton para ver el uso 👇"""

    await update.message.reply_text(texto, reply_markup=teclado)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Botón volver
    if query.data == "volver_cmds":
        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("RENIEC", callback_data="cmd_reniec"),
                InlineKeyboardButton("RUC", callback_data="cmd_ruc")
            ],
            [
                InlineKeyboardButton("VEHÍCULOS", callback_data="cmd_vehiculos"),
                InlineKeyboardButton("TELÉFONO", callback_data="cmd_telefono")
            ],
            [
                InlineKeyboardButton("DENUNCIAS", callback_data="cmd_denuncia"),
                InlineKeyboardButton("NOMBRES", callback_data="cmd_nm")
            ],
            [
                InlineKeyboardButton("PERFIL", callback_data="cmd_me"),
                InlineKeyboardButton("COMPRAR", callback_data="cmd_buy")
            ]
        ])

        texto = f"""[ PANEL DE COMANDOS ]

Precios por consulta:
DNI: {PRECIOS['dni']} | RUC: {PRECIOS['ruc']} | PLACA: {PRECIOS['placa']} | TEL: {PRECIOS['telp']}
AGV: {PRECIOS['agv']} | DENUNCIA: {PRECIOS['denuncia']} | NOMBRE: {PRECIOS['nm']}

Selecciona un boton para ver el uso 👇"""

        await query.edit_message_text(
            texto,
            reply_markup=teclado
        )
        return

    comandos = {
        "cmd_reniec": """❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨 ❱ ➾ RENIEC
✦ ──────────────── ✦
ᴄᴏᴍᴀɴᴅᴏs ᴅɪsᴘᴏɴɪʙʟᴇs ➾ 5
ᴘᴀɢɪɴᴀ ➾ 1/1

1. DNI TARJETA
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /dnit 44445555
• ᴘʀᴇᴄɪᴏ ➾ 5 ᴄʀᴇ́ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ texto con foto y firma

2. DNI POR NOMBRES
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /nm juan quispe
• ᴘʀᴇᴄɪᴏ ➾ 6 ᴄʀᴇ́ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ dni por nombre y apellido

3. DNI SIMPLE
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /dni 44445555
• ᴘʀᴇᴄɪᴏ ➾ 4 ᴄʀᴇ́ᴅɪᴛᴏs

Página: 1/1""",

        "cmd_ruc": "Uso: /ruc 20538856674",

        "cmd_vehiculos": f"""❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨 ❱ ➾ VEHICULARES
✦ ──────────────── ✦

1. PLACA TEXTO
• ᴄᴏᴍᴀɴᴅᴏ ➾ /placa ABC123
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['placa']} créditos

2. SOAT VIGENTE
• ᴄᴏᴍᴀɴᴅᴏ ➾ /hsoat ABC123
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['hsoat']} créditos

3. DENUNCIAS
• ᴄᴏᴍᴀɴᴅᴏ ➾ /denpla ABC123
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['denpla']} créditos""",

        "cmd_telefono": f"""❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨 ❱ ➾ TELEFONIA

1. TELX POR DNI
• ᴄᴏᴍᴀɴᴅᴏ ➾ /telp 44445555
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['telp']} créditos

2. TELX POR NUMERO
• ᴄᴏᴍᴀɴᴅᴏ ➾ /telx 999888777
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['telx']} créditos""",

        "cmd_denuncia": f"Uso: /denuncia 12345678\nPrecio: {PRECIOS['denuncia']} créditos",

        "cmd_nm": f"Uso: /nm JUAN PEREZ GOMEZ\nPrecio: {PRECIOS['nm']} créditos"
    }

    if query.data in comandos:
        volver = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Volver al inicio", callback_data="volver_cmds")]
        ])
        await query.edit_message_text(
            comandos[query.data],
            reply_markup=volver
        )

    elif query.data == "cmd_me":
        await me(update, context)

    elif query.data == "cmd_buy":
        await buy(update, context)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    if user_id in usuarios: return await update.message.reply_text("Ya estas registrado")
    usuarios[user_id] = {"creditos": 0, "nombre": update.effective_user.first_name, "username": update.effective_user.username, "fecha_registro": get_fecha(), "rol": "PENDIENTE", "plan": "FREE"}
    guardar_usuarios(usuarios)
    await update.message.reply_text(f"Registro exitoso! Bienvenido {update.effective_user.first_name}")

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    u = usuarios.get(user_id, {})
    texto = f"""[#BOT DATA] ➾ PERFIL DE USUARIO
PERFIL DE ➾ {u.get("nombre", "Usuario")}
[🙎‍♂️] ID ➾ {user_id}
[👨🏻‍💻] USER ➾ @{u.get("username", "")}
[💰] CREDITOS ➾ {u.get('creditos', 0)}
[📊] CONSULTAS ➾ {u.get('consultas', 0)}"""
    await update.message.reply_text(texto)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"CONSULTA PRECIOS {update.effective_user.id}\nLuego contacta a @Xxxxxxx_Gatito_xxxxxxx")

async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("STAFF: @Xxxxxxx_Gatito_xxxxxxx - ADMIN")

async def quitarcrd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_ID:
        return await update.message.reply_text("⛔ No tienes permiso")
    if len(context.args) < 2:
        return await update.message.reply_text("Uso: /quitarcrd ID_USUARIO CANTIDAD")
    target_id = context.args[0]
    try:
        cantidad = int(context.args[1])
    except:
        return await update.message.reply_text("La cantidad debe ser un número")
    usuarios = cargar_usuarios()
    if target_id not in usuarios:
        return await update.message.reply_text(f"El usuario {target_id} no existe en la BD")
    saldo_anterior = usuarios[target_id]["creditos"]
    usuarios[target_id]["creditos"] -= cantidad
    if usuarios[target_id]["creditos"] < 0:
        usuarios[target_id]["creditos"] = 0
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ CREDITOS QUITADOS
[👤] USUARIO ➾ {target_id}
[➖] QUITADOS ➾ {cantidad} Créditos
[💰] SALDO ANTERIOR ➾ {saldo_anterior}
[💰] SALDO ACTUAL ➾ {usuarios[target_id]['creditos']}"""
    await update.message.reply_text(texto)

async def addcreditos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_ID: return await update.message.reply_text("⛔ No eres ADMIN")
    if len(context.args)!= 2: return await update.message.reply_text("Uso: /addcreditos ID 20")
    target_id, cantidad = context.args[0], int(context.args[1])
    usuarios = cargar_usuarios()
    usuarios.setdefault(target_id, {"creditos": 0, "consultas": 0})
    usuarios[target_id]["creditos"] += cantidad
    guardar_usuarios(usuarios)
    await update.message.reply_text(f"Se agregaron {cantidad} creditos a {target_id}")

# ===== COMANDOS DE CONSULTA =====
async def dni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "dni", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /dni 12345678")
    dni_num = context.args[0]
    m = await update.message.reply_text("🔎 Consultando DNI... -4 creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/dni/{dni_num}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','DNI no encontrado')}")
    res = data.get("data", {}); d = res.get("dni", {}); n = res.get("nacimiento", {}); dom = res.get("domicilio", {}); info = res.get("informacion_general", {})
    usuarios[user_id]["creditos"] -= PRECIOS["dni"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ CONSULTA DNI
[🆔] DNI: {d.get('completo')}
[👤] Nombre: {res.get('nombres')} {res.get('apellidos')}
[⚧] Genero: {res.get('genero')}
[📅] Nac: {n.get('fecha')} | {n.get('edad')}
[🏠] Dir: {dom.get('direccion')} - {dom.get('distrito')}
[👨] Padre: {info.get('padre')}
[👩] Madre: {info.get('madre')}
💰 Creditos: {usuarios[user_id]['creditos']}"""
    await m.edit_text(texto)

async def dnit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "dnit", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /dnit 12345678")
    dni_num = context.args[0]
    m = await update.message.reply_text(f"🔎 Consultando DNI-T de {dni_num}... -{PRECIOS['dnit']} creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/dnit/{dni_num}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','DNI no encontrado')}")
    res = data.get("data", {})
    d = res.get("dni", {}); n = res.get("nacimiento", {}); dom = res.get("domicilio", {}); info = res.get("informacion_general", {})
    images = res.get("images", [])
    usuarios[user_id]["creditos"] -= PRECIOS["dnit"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ DNI-T
[🆔] DNI ➾ {d.get('completo')}
[👤] NOMBRE ➾ {res.get('nombres')} {res.get('apellidos')}
[⚧] GENERO ➾ {res.get('genero')}
[📅] NACIMIENTO ➾ {n.get('fecha')} | {n.get('edad')}
[🏠] DIRECCION ➾ {dom.get('direccion')}
[📚] EDUCACION ➾ {info.get('nivel_educativo')}
[💍] ESTADO CIVIL ➾ {info.get('estado_civil')}
[📄] EMISION ➾ {info.get('fecha_emision')} | CADUCA ➾ {info.get('fecha_caducidad')}
💰 Creditos: {usuarios[user_id]['creditos']}"""
    await m.edit_text(texto)
    for i, img_data in enumerate(images, 1):
        try:
            base64_str = img_data.get('data_uri', '').split(',')[1]
            img_bytes = base64.b64decode(base64_str)
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=io.BytesIO(img_bytes), caption=f"Foto {i} de {d.get('completo')}")
        except:
            pass

async def hsoat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "hsoat", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /hsoat ABC123")
    placa = context.args[0].upper()
    m = await update.message.reply_text(f"🔎 Consultando HSOAT de {placa}... -{PRECIOS['hsoat']} creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/hsoat/{placa}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','Placa no encontrada')}")
    res = data.get("data", {})
    placa_data = res.get("placa"); cantidad = res.get("cantidad_registros"); historial = res.get("historial", [])
    usuarios[user_id]["creditos"] -= PRECIOS["hsoat"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ HSOAT
[🚗] PLACA ➾ {placa_data}
[📊] REGISTROS ➾ {cantidad}"""
    for i, h in enumerate(historial, 1):
        texto += f"\n\n--- SOAT {i} ---\n[🏢] COMPAÑIA ➾ {h.get('compania')}\n[✅] ESTADO ➾ {h.get('estado')}\n[📄] PÓLIZA ➾ {h.get('poliza')}"
    texto += f"\n\n💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto)

async def denpla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "denpla", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /denpla ABC123")
    placa = context.args[0].upper()
    m = await update.message.reply_text(f"🔎 Consultando DENUNCIAS de {placa}... -{PRECIOS['denpla']} creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/denpla/{placa}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','Placa no encontrada')}")
    res = data.get("data", {})
    placa_data = res.get("placa"); cantidad = res.get("cantidad_denuncias"); denuncias = res.get("denuncias", [])
    usuarios[user_id]["creditos"] -= PRECIOS["denpla"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ DENUNCIAS POLICIALES
[🚗] PLACA ➾ {placa_data}
[🚨] TOTAL DENUNCIAS ➾ {cantidad}"""
    for d in denuncias:
        texto += f"\n\n--- DENUNCIA {d.get('numero')} ---\n[📌] TIPO ➾ {d.get('tipo')}\n[🏛️] COMISARIA ➾ {d.get('comisaria')}"
    texto += f"\n\n💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto)

async def telp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "telp", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /telp 12345678")
    dni_num = context.args[0]
    m = await update.message.reply_text(f"🔎 Consultando TELÉFONOS de {dni_num}... -{PRECIOS['telp']} creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/telp/{dni_num}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','DNI no encontrado')}")
    res = data.get("data", {})
    lineas = res.get("lineas", []); cantidad = res.get("lineas_encontradas")
    usuarios[user_id]["creditos"] -= PRECIOS["telp"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ TELEFONOS
[🆔] DNI ➾ {dni_num}
[📞] LINEAS ENCONTRADAS ➾ {cantidad}"""
    for i, l in enumerate(lineas, 1):
        periodo = l.get('periodo')
        periodo_fmt = f"{periodo[4:6]}/{periodo[:4]}" if periodo and len(periodo)==6 else periodo
        texto += f"\n\n--- LINEA {i} ---\n[📱] NUMERO ➾ {l.get('telefono')}\n[📡] OPERADOR ➾ {l.get('operador')}"
    texto += f"\n\n💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto)

#... aqui van tus otros comandos: placa, agv, denuncia, nm, telx

# ===== MAIN =====
def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cmds", cmds))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("me", me))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("staff", staff))
    application.add_handler(CommandHandler("addcreditos", addcreditos))
    application.add_handler(CommandHandler("quitarcrd", quitarcrd))
    application.add_handler(CommandHandler("dni", dni))
    application.add_handler(CommandHandler("dnit", dnit))
    application.add_handler(CommandHandler("hsoat", hsoat))
    application.add_handler(CommandHandler("denpla", denpla))
    application.add_handler(CommandHandler("telp", telp))
    # agrega los demas handlers aqui
    print("Bot iniciado v2.1...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()