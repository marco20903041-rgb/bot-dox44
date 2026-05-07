from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8714125008:AAGnNawfd0A_mVoZStJsrASu1bNylaYvJOg" 
 # El que revocaste

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(">>> SI VES ESTO, EL BOT SÍ RECIBIÓ EL /START <<<")
    await update.message.reply_text('Ahora sí respondo bro 🥳')

async def post_init(application):
    """Borra el webhook al iniciar"""
    print('Borrando webhook viejo...')
    await application.bot.delete_webhook(drop_pending_updates=True)

def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler('start', start))
    
    print('Bot encendido... Esperando mensajes')
    app.run_polling()  # Este ya maneja el asyncio por dentro

if __name__ == '__main__':
    main()
