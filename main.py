import json
import httpx
import datetime
import os
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
ADMIN_ID = str(os.getenv("ADMIN_ID")) # Lo pasamos a str para comparar
ARCHIVO_USUARIOS = os.getenv("ARCHIVO_USUARIOS") or "usuarios.json"
BOT_USER = "@OFICIAL_DATA_BOT"
BOT_NAME = "⚜ DATA_PERU⚜"
BASE_URL = "https://api-codart.cgrt.org"

PRECIOS = {
    "dni": 4, "agv": 8, "telx": 15, "ruc": 5,
    "denuncia": 10, "placa": 12, "nm": 6, "hsoat": 8
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
    texto = f"""Hola

INFORMACION DEL BOT

- Nombre ➾ {BOT_NAME}
- Usuario ➾ {BOT_USER}
- Versión ➾ v2.1 CODART V1

COMANDOS GENERALES

- Registra tu cuenta ➾ /register
- Lista de comandos ➾ /cmds
- Revisa tu perfil ➾ /me
- Revisa el staff ➾ /staff
- Compra Creditos/Dias ➾ /buy

Servicio gestionado por
SISTEMAS PERU"""
    await update.message.reply_text(texto)

async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("RENIEC", callback_data="cmd_reniec"), InlineKeyboardButton("RUC", callback_data="cmd_ruc")],
        [InlineKeyboardButton("VEHICULOS", callback_data="cmd_vehiculos"), InlineKeyboardButton("TELEFONO", callback_data="cmd_telx")],
        [InlineKeyboardButton("FAMILIARES", callback_data="cmd_familiares"), InlineKeyboardButton("DENUNCIA", callback_data="cmd_denuncia")],
        [InlineKeyboardButton("NOMBRE", callback_data="cmd_nm")],
        [InlineKeyboardButton("PERFIL", callback_data="cmd_me"), InlineKeyboardButton("COMPRAR", callback_data="cmd_buy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    texto = f"""[ PANEL DE COMANDOS ]

Precios por consulta:
DNI: 4 | RUC: 5 | PLACA: 12 | TEL: 15
AGV: 8 | DENUNCIA: 10 | NOMBRE: 6

Selecciona un boton para ver el uso 👇"""
    await update.message.reply_text(texto, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    comandos = {
        "cmd_reniec": """❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨 ❱ ➾ RENIEC
✦ ──────────────── ✦
ᴄᴏᴍᴀɴᴅᴏs ᴅɪsᴘᴏɴɪʙʟᴇs ➾ 5
ᴘᴀ‌ɢɪɴᴀ ➾ 1/1

1. DNI ELECTRONICO
• ᴇsᴛᴀᴅᴏ ➾ MUY PRONTO [❌]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /dnie 44445555
• ᴘʀᴇᴄɪᴏ ➾ 15 ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ Dni electronico

2. DNI VIRTUAL
• ᴇsᴛᴀᴅᴏ ➾ MUY PRONTO [❌]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /dniva 78323583
• ᴘʀᴇᴄɪᴏ ➾ 10 ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ DNI virtual amarillo

3. DNI VIRTUAL
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /dniv 46193350
• ᴘʀᴇᴄɪᴏ ➾ 8 ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ DNI virtual Azul

4. DNI TARJETA 
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /dnit 44445555
• ᴘʀᴇᴄɪᴏ ➾ 5 ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ texto con foto y firma
5. DNI POR NOMBRES 
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /nm juan quispe 
• ᴘʀᴇᴄɪᴏ ➾ 4 ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ dni por nombre y apellido 

Página: 1/1""","cmd_ruc": "Uso: /ruc 20538856674",
        "cmd_vehiculos": """❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨   ❱ ➾ VEHICULARES
✦ ──────────────── ✦
ᴄᴏᴍᴀɴᴅᴏs ᴅɪsᴘᴏɴɪʙʟᴇs ➾ 4
ᴘᴀ‌ɢɪɴᴀ ➾ 1/1

1. PLACA TEXTO
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /placa ABC123
• ᴘʀᴇᴄɪᴏ ➾ 2 ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ Detalles del vehículo en texto

2. SOAT VIGENTE
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /hsoat ABC123
• ᴘʀᴇᴄɪᴏ ➾ 8 ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ Consulta SOAT en por placa 

3. Datos por placa 
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /plat ABC123
• ᴘʀᴇᴄɪᴏ ➾ 5  ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ Consulta datos completos del vehículo y propietarios por placa.
 
4. PLACA TEXTO
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /denpla ABC123
• ᴘʀᴇᴄɪᴏ ➾ 30 ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ Denuncia pdf a una placa 



Página: 1/1""",
        "cmd_telx": "Uso: /telx 987654321",
        "cmd_agv": "Uso: /agv 12345678",
        "cmd_denuncia": "Uso: /denuncia 12345678",
        "cmd_nm": "Uso: /nm JUAN PEREZ GOMEZ"
    }
    if query.data in comandos: await query.message.reply_text(comandos[query.data])
    elif query.data == "cmd_me": await me(update, context)
    elif query.data == "cmd_buy":
        await buy(update, context)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios =cargar_usuarios()
    if user_id in usuarios: return await update.message.reply_text("Ya estas registrado")
    usuarios[user_id] = {"creditos": 0, "consultas": 0, "nombre": update.effective_user.first_name, "username": update.effective_user.username, "fecha_registro": get_fecha(), "rol": "PENDIENTE", "plan": "FREE"}
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
    await update.message.reply_text(f"COMPRAR CREDITOS\nYapeas y manda tu comprobante + tu ID: {update.effective_user.id}\nLuego contacta a @Xxxxxxx_Gatito_xxxxxxx")

async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("STAFF: @Xxxxxxx_Gatito_xxxxxxx - ADMIN")

async def addcreditos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id!= ADMIN_ID: return await update.message.reply_text("IMBECIL! no eres admin")
    if len(context.args)!= 2: return await update.message.reply_text("Uso: /addcreditos ID 20")
    target_id, cantidad = context.args[0], int(context.args[1])
    usuarios = cargar_usuarios()
    usuarios.setdefault(target_id, {"creditos": 0, "consultas": 0})
    usuarios[target_id]["creditos"] += cantidad
    guardar_usuarios(usuarios)
    await update.message.reply_text(f"Se agregaron {cantidad} creditos a {target_id}")

# ===== COMANDOS DE CONSULTA CODART V1 =====
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
    texto = f"""🔎 CONSULTA DNI
DNI: {d.get('completo')}
Nombre: {res.get('nombres')} {res.get('apellidos')}
Genero: {res.get('genero')}
Nac: {n.get('fecha')} | {n.get('edad')}
Dir: {dom.get('direccion')} - {dom.get('distrito')}
Padre: {info.get('padre')}
Madre: {info.get('madre')}
💰 Creditos: {usuarios[user_id]['creditos']}"""
    await m.edit_text(texto, parse_mode="Markdown")

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
    placa_data = res.get("placa")
    cantidad = res.get("cantidad_registros")
    historial = res.get("historial", [])

    # Descontar créditos
    usuarios[user_id]["creditos"] -= PRECIOS["hsoat"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)

    # Armar mensaje
    texto = f"""[#BOT DATA] ➾ HSOAT
[🚗] PLACA ➾ {placa_data}
[📊] REGISTROS ➾ {cantidad}
"""
    for i, h in enumerate(historial, 1):
        texto += f"""
--- SOAT {i} ---
[🏢] COMPAÑIA ➾ {h.get('compania')}
[✅] ESTADO ➾ {h.get('estado')}
[📄] PÓLIZA ➾ {h.get('poliza')}
[📅] VIGENCIA ➾ {h.get('fecha_inicio')} al {h.get('fecha_fin')}
[👮] CONTROL ➾ {h.get('control_policial')}"""

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
    placa_data = res.get("placa")
    cantidad = res.get("cantidad_denuncias")
    denuncias = res.get("denuncias", [])

    # Descontar créditos
    usuarios[user_id]["creditos"] -= PRECIOS["denpla"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)

    # Armar mensaje
    texto = f"""[#BOT DATA] ➾ DENUNCIAS POLICIALES
[🚗] PLACA ➾ {placa_data}
[🚨] TOTAL DENUNCIAS ➾ {cantidad}
"""
    for d in denuncias:
        texto += f"""
--- DENUNCIA {d.get('numero')} ---
[📌] TIPO ➾ {d.get('tipo')}
[🏛️] COMISARIA ➾ {d.get('comisaria')}
[📄] N° ORDEN ➾ {d.get('n_orden')}
[📅] F. HECHO ➾ {d.get('f_hecho')}
[📅] F. REGISTRO ➾ {d.get('f_registro')}
[📎] ARCHIVO ➾ {d.get('nombre')}"""

    texto += f"\n\n💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto)
    
async def telx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "telx", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /telx 987654321")
    num = context.args[0]
    m = await update.message.reply_text("📱 Consultando telefono... -15 creditos")
    url =f"{BASE_URL}/api/v1/consultas/fd/telp/cel/{num}"
    data = await consultar_api_get(url)
    if not data.get("success"): return await m.edit_text("Numero no encontrado")
    res = data.get("data", {}); titulares = res.get("titulares", [])
    usuarios[user_id]["creditos"] -= PRECIOS["telx"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    t = titulares[0] if titulares else {}
    texto = f"""📱 CONSULTA TELEFONO
Numero: {t.get('telefono')}
Titular: {t.get('titular')}
DNI/RUC: {t.get('dni_ruc')}
Operador: {t.get('operador')}
Empresa: {t.get('empresa')}
💰 Creditos: {usuarios[user_id]['creditos']}"""
    await m.edit_text(texto, parse_mode="Markdown")

async def placa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "placa", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /placa D5G960")
    pla = context.args[0].upper()
    m = await update.message.reply_text("🚗 Consultando placa... -12 creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/plat/{pla}"
    data = await consultar_api_get(url)
    if not data.get("success"): return await m.edit_text("Placa no encontrada")
    res = data.get("data", {}); car = res.get("caracteristicas", {}); prop = res.get("propietarios", [{}])[0]
    usuarios[user_id]["creditos"] -= PRECIOS["placa"]
    guardar_usuarios(usuarios)
    texto = f"""🚗 CONSULTA PLACA
Placa: {res.get('placa')}
Marca: {car.get('marca')} {car.get('modelo')}
Estado: {car.get('estado')}
Propietario: {prop.get('nombres')}
Direccion: {prop.get('direccion')}
💰 Creditos: {usuarios[user_id]['creditos']}"""
    await m.edit_text(texto, parse_mode="Markdown")

async def agv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "agv", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /agv 12345678")
    dni_num = context.args[0]
    m = await update.message.reply_text("👨‍👩‍👧 Consultando arbol... -8 creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/ag/{dni_num}"
    data = await consultar_api_get(url)
    if not data.get("success"): return await m.edit_text("No se encontraron familiares")
    res = data.get("data", {}); rel = res.get("relaciones", [])
    usuarios[user_id]["creditos"] -= PRECIOS["agv"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"👨‍👩‍👧 ARBOL GENEALOGICO\nDNI: {res.get('consulta')}\nTotal: {res.get('familiares')}\n\n"
    for f in rel:
        texto += f"{f.get('relacion')}: {f.get('nombres')} {f.get('apellidos')} | {f.get('dni')} | {f.get('verificacion')}\n"
    texto += f"\n💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto, parse_mode="Markdown")

async def denuncia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "denuncia", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /denuncia 12345678")
    dni_num = context.args[0]
    m = await update.message.reply_text("🚨 Consultando denuncias... -10 creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/den/{dni_num}"
    data = await consultar_api_get(url)
    if not data.get("success"): return await m.edit_text("Sin denuncias")
    res = data.get("data", {}); den = res.get("denuncias", [])
    usuarios[user_id]["creditos"] -= PRECIOS["denuncia"]
    guardar_usuarios(usuarios) # Arregle la identacion que estaba mal
    texto = f"🚨 DENUNCIAS DNI: {res.get('consulta')}\nTotal: {res.get('cantidad_denuncias')}\n\n"
    for d in den[:3]:
        texto += f"#{d.get('numero')} {d.get('tipo')}\nOrden: {d.get('n_orden')}\nHecho: {d.get('f_hecho')}\nResumen: {d.get('resumen')}\n\n"
    texto += f"💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto, parse_mode="Markdown")

async def nm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "nm", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if len(context.args) < 2: return await update.message.reply_text("Uso: /nm JUAN PEREZ GOMEZ")
    nombre = context.args
    n1 = nombre[0]
    ap1 = nombre[1] if len(nombre) > 1 else ""
    ap2 = nombre[2] if len(nombre) > 2 else ""
    m = await update.message.reply_text(f"🔍 Buscando: {' '.join(nombre)}... -6 creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/nm?n1={n1}&ap1={ap1}&ap2={ap2}"
    data = await consultar_api_get(url)
    if not data.get("success"): return await m.edit_text("No se encontro")
    res = data.get("data", {}); resultados = res.get("resultados", [])
    usuarios[user_id]["creditos"] -= PRECIOS["nm"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"🔍 RESULTADOS: {res.get('cantidad_resultados')}\n\n"
    for i, p in enumerate(resultados[:5], 1):
        texto += f"{i}. {p.get('nombres')} {p.get('apellidos')} - DNI: {p.get('dni')} - {p.get('edad')} años\n"
    texto += f"\n💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto, parse_mode="Markdown")

# ===== MAIN =====
def main():
    keep_alive()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cmds", cmds))
    application.add_handler(CommandHandler("hsoat", hsoat))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("me", me))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("staff", staff))
    application.add_handler(CommandHandler("addcreditos", addcreditos))
    application.add_handler(CommandHandler("dni", dni))
    application.add_handler(CommandHandler("telx", telx))
    application.add_handler(CommandHandler("placa", placa))
    application.add_handler(CommandHandler("agv", agv))
    application.add_handler(CommandHandler("denuncia", denuncia))
    application.add_handler(CommandHandler("nm", nm))

    print("Bot iniciado v2.1...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()