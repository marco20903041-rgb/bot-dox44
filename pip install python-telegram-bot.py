
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8714125008:AAGnNawfd0A_mVoZStJsrASu1bNylaYvJOg"
  # El que sacaste de @BotFather

async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start."""
    print(">>> SI VES ESTO, EL BOT SÍ RECIBIÓ EL /START <<<")
    print(f"¡Llegó /start de {update.effective_user.first_name}!")
    await update.message.reply_text('Ahora sí respondo bro')

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    
    print('Borrando webhook viejo...')
    asyncio.run(app.bot.delete_webhook(drop_pending_updates=True))
    
    print('Bot encendido... Esperando mensajes')
    app.run_polling()

if __name__ == '__main__':
    main()
