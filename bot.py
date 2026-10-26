import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TOKEN, CHANNELS, ADMIN_IDS
from database import get_total_users, get_semua_produk
from handlers import (
    mulai_command,
    admin_command,
    batal_command,
    tombol_callback_handler,
    status_member_berubah,
    handle_pesan_teks,
)

from telegram.request import HTTPXRequest

# Konfigurasi logging standar
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani dan mencatat error tak terduga tanpa menyebabkan bot crash"""
    logging.error("Exception tak terduga saat memproses update:", exc_info=context.error)

def main():
    """Fungsi utama untuk menginisialisasi dan menjalankan bot"""
    request_config = HTTPXRequest(
        connection_pool_size=16,
        read_timeout=30.0,
        write_timeout=30.0,
        connect_timeout=30.0,
        pool_timeout=30.0,
    )
    app = ApplicationBuilder().token(TOKEN).request(request_config).build()

    # Mendaftarkan handler command & interaksi
    app.add_handler(CommandHandler("mulai", mulai_command))
    app.add_handler(CommandHandler("start", mulai_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("batal", batal_command))
    app.add_handler(CallbackQueryHandler(tombol_callback_handler))
    app.add_handler(ChatMemberHandler(status_member_berubah, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pesan_teks))

    # Error handler global
    app.add_error_handler(global_error_handler)

    channels_str = " & ".join([ch["id"] for ch in CHANNELS])
    print("=========================================")
    print("Bot AI Barokah berjalan...")
    print(f"Administrator ID: {ADMIN_IDS}")
    print(f"Total Produk Tersedia: {len(get_semua_produk())}")
    print(f"Total Pengguna Terdaftar: {get_total_users()}")
    print(f"Wajib Join: {channels_str}")
    print("=========================================")

    # Jalankan polling bot
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, timeout=30)

if __name__ == "__main__":
    main()