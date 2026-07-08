import os
import json
from datetime import datetime
import threading
from flask import Flask

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
ARCHIVO_USUARIOS = "usuarios.json"
ADMIN_ID = 8771814419 # <-- PON AQUI TU ID DE TELEGRAM

COSTOS = {
    "dni": 4,
    "agv": 8,
    "telx": 15
}
CREDITOS_INICIALES = 3

def cargar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS):
        return {}
    with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_usuarios(data):
    with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def guardar_log(cmd, user_id, param, res):
    with open("consultas_PERU.txt", "a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now()} | {user_id} | {cmd} | {param}\n"
            f"{json.dumps(res, ensure_ascii=False, indent=2)}\n\n"
        )

async def consulta_api(tipo, numero):
    urls = {
        "dni": f"https://api-codart.cgrt.org/api/v1/consultas/fd/dni/{numero}",
        "agv": f"https://api-codart.cgrt.org/api/v1/consultas/fd/ag/{numero}",
        "telx": f"https://api-codart.cgrt.org/api/v1/consultas/fd/telp/{numero}",
    }
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(urls[tipo], headers=headers)
            if response.status_code == 200:
                return response.json()
            return {"error": response.status_code, "detalle": response.text}
    except Exception as e:
        return {"error": str(e)}

def es_admin(user_id):
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        [InlineKeyboardButton("🪪 DNI - 4crd", callback_data="dni")],
        [InlineKeyboardButton("🏢 AGV - 8crd", callback_data="agv")],
        [InlineKeyboardButton("📱 TEL - 15crd", callback_data="telx")],
    ]
    await update.message.reply_text(
        f"""🎯 BIENVENIDO A DATA BOT 🎯

PRECIOS:
- /dni → {COSTOS['dni']} créditos
- /agv → {COSTOS['agv']} créditos
- /telx → {COSTOS['telx']} créditos

COMANDOS:
- /register → +{CREDITOS_INICIALES} créditos gratis
- /me → Ver tus créditos
- /buy → Comprar créditos""",
        reply_markup=InlineKeyboardMarkup(teclado),
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    if user_id in usuarios:
        return await update.message.reply_text("Ya estás registrado ✅")

    usuarios[user_id] = {
        "nombre": update.effective_user.first_name,
        "username": update.effective_user.username,
        "creditos": CREDITOS_INICIALES,
        "registro": str(datetime.now())
    }
    guardar_usuarios(usuarios)
    await update.message.reply_text(f"Registrado! Te di {CREDITOS_INICIALES} créditos gratis 🎁\nUsa /me para verlos")

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    if user_id not in usuarios:
        return await update.message.reply_text("No estás registrado. Usa /register")

    creditos = usuarios[user_id]["creditos"]
    await update.message.reply_text(f"👤 {usuarios[user_id]['nombre']}\n💎 Créditos: {creditos}")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        [InlineKeyboardButton("10 Créditos - S/10", callback_data="buy_10")],[InlineKeyboardButton("25 Créditos - S/25", callback_data="buy_25")],
        [InlineKeyboardButton("50 Créditos - S/50", callback_data="buy_50")],
    ]
    await update.message.reply_text(
        "Elige tu paquete. Paga a @marco44xxdox y te recargo al toque:",
        reply_markup=InlineKeyboardMarkup(teclado)
    )

async def addcreditos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_admin(update.effective_user.id):
        return await update.message.reply_text("No tienes permisos ❌")

    if len(context.args)!= 2:
        return await update.message.reply_text("Uso: /addcreditos ID CANTIDAD")

    user_id, cantidad = context.args[0], int(context.args[1])
    usuarios = cargar_usuarios()
    if user_id not in usuarios:
        return await update.message.reply_text("Usuario no encontrado")

    usuarios[user_id]["creditos"] += cantidad
    guardar_usuarios(usuarios)
    await update.message.reply_text(f"✅ Se agregaron {cantidad} créditos a {usuarios[user_id]['nombre']}\nTotal: {usuarios[user_id]['creditos']}")

async def remcreditos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_admin(update.effective_user.id):
        return await update.message.reply_text("No tienes permisos ❌")

    if len(context.args)!= 2:
        return await update.message.reply_text("Uso: /remcreditos ID CANTIDAD")

    user_id, cantidad = context.args[0], int(context.args[1])
    usuarios = cargar_usuarios()
    if user_id not in usuarios:
        return await update.message.reply_text("Usuario no encontrado")

    usuarios[user_id]["creditos"] = max(0, usuarios[user_id]["creditos"] - cantidad)
    guardar_usuarios(usuarios)
    await update.message.reply_text(f"✅ Se quitaron {cantidad} créditos a {usuarios[user_id]['nombre']}\nTotal: {usuarios[user_id]['creditos']}")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_admin(update.effective_user.id):
        return await update.message.reply_text("No tienes permisos ❌")

    usuarios = cargar_usuarios()
    texto = "📋 USUARIOS REGISTRADOS:\n\n"
    for uid, data in usuarios.items():
        texto += f"ID: {uid}\nNombre: {data['nombre']}\n💎: {data['creditos']}\n\n"

    await update.message.reply_text(texto, parse_mode="Markdown")

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("buy_"):
        creds = int(data.split("_")[1])
        await query.edit_message_text(f"Solicitaste {creds} créditos.\nPaga S/{creds} a @marco44xxdox y te recargo.")
        return

    mensajes = {
        "dni": f"Usa:\n/dni 12345678\nCosto: {COSTOS['dni']} créditos",
        "agv": f"Usa:\n/agv 20123456789\nCosto: {COSTOS['agv']} créditos",
        "telx": f"Usa:\n/telx 999\nCosto: {COSTOS['telx']} créditos",
    }
    await query.edit_message_text(mensajes.get(data, "Opción no disponible."))

async def hacer_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE, tipo):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    costo = COSTOS[tipo]

    if user_id not in usuarios:
        return await update.message.reply_text("Primero regístrate con /register")

    if usuarios[user_id]["creditos"] < costo:
        return await update.message.reply_text(f"Te faltan créditos 😢\nNecesitas {costo} y tienes {usuarios[user_id]['creditos']}\nUsa /buy")

    if not context.args:
        return await update.message.reply_text(f"Uso: /{tipo} NUMERO")

    numero = context.args[0]
    await update.message.reply_text(f"Consultando... ⏳ -{costo} créditos")

    respuesta = await consulta_api(tipo, numero)
    usuarios[user_id]["creditos"] -= costo
    guardar_usuarios(usuarios)
    guardar_log(f"/{tipo}", user_id, numero, respuesta)

    await update.message.reply_text(
        f"`json\n{json.dumps(respuesta, indent=2, ensure_ascii=False)}\n```\n\n💎 Créditos restantes: {usuarios[user_id]['creditos']}",
        parse_mode="Markdown"
    )
async def dni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await hacer_consulta(update, context, "dni")

async def agv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await hacer_consulta(update, context, "agv")

async def telx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await hacer_consulta(update, context, "telx")
# --- SERVIDOR WEB PARA QUE NO SE DUERMA ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot Data Peru esta vivo 24/7 ✅"

def run_web():
    app_web.run(host='0.0.0.0', port=10000)
def main():
    # Inicia el servidor web en un hilo aparte
    threading.Thread(target=run_web).start()
    
    # Inicia el bot normal
    import asyncio
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("addcreditos", addcreditos))
    app.add_handler(CommandHandler("remcreditos", remcreditos))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("dni", dni))
    app.add_handler(CommandHandler("agv", agv))
    app.add_handler(CommandHandler("telx", telx))
    app.add_handler(CallbackQueryHandler(callback))
    print("Bot con sistema de créditos iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
    # Levanta Flask y el bot al mismo tiempo
    threading.Thread(target=run_flask).start()
    run_bot()