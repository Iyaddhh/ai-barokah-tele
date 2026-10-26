from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes
from database import user_terdaftar, hapus_user

async def status_member_berubah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mendeteksi secara real-time saat user keluar atau dibanned dari channel"""
    result = update.chat_member
    if not result:
        return

    new_status = result.new_chat_member.status
    user_id = result.new_chat_member.user.id

    if new_status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
        if user_terdaftar(user_id):
            hapus_user(user_id)
            print(f"[MEMBER KELUAR REAL-TIME]: User ID {user_id} keluar dari channel, otomatis dihapus dari database bot.")
