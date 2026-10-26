import os
from datetime import datetime, timezone, timedelta
from telegram.constants import ChatMemberStatus
from config import BASE_DIR, CHANNELS

def ambil_gambar_gate():
    """Mencari lokasi gambar_gate.jpg baik di folder assets maupun root"""
    path_assets = os.path.join(BASE_DIR, "assets", "gambar_gate.jpg")
    if os.path.exists(path_assets):
        return path_assets
    path_root = os.path.join(BASE_DIR, "gambar_gate.jpg")
    if os.path.exists(path_root):
        return path_root
    return None

def get_greeting():
    """Menentukan ucapan selamat berdasarkan zona waktu WIB (UTC+7)"""
    wib = timezone(timedelta(hours=7))
    hour = datetime.now(wib).hour
    if 4 <= hour < 11:
        return "pagi"
    elif 11 <= hour < 15:
        return "siang"
    elif 15 <= hour < 18:
        return "sore"
    else:
        return "malam"

async def check_user_channels(bot, user_id: int):
    """
    Mengecek status keanggotaan user di kedua channel.
    Mengembalikan tuple: (is_all_joined, list_channel_belum_join)
    """
    unjoined = []
    valid_statuses = [
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ]

    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
            if member.status not in valid_statuses:
                unjoined.append(ch)
        except Exception as e:
            if "Member list is inaccessible" in str(e):
                print(f"[PERINGATAN]: Bot (@storeaibarokah_bot) BELUM jadi ADMIN di channel {ch['id']}! Telegram mewajibkan bot menjadi Administrator di channel untuk mengecek member.")
            else:
                print(f"[ERROR CEK {ch['id']}]: {e}")
            unjoined.append(ch)

    return len(unjoined) == 0, unjoined
