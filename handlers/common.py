import html
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from database import (
    user_terdaftar,
    tambah_user,
    hapus_user,
    is_user_blocked,
    simpan_update_user_profile,
)
from helpers import check_user_channels, ambil_gambar_gate
from ui import (
    buat_tampilan_utama,
    buat_keyboard_gate,
    buat_tampilan_admin_panel,
    buat_reply_keyboard_utama,
)

async def edit_pesan_aman(query, text: str, markup=None, parse_mode=ParseMode.HTML):
    """Mengedit pesan teks atau caption secara aman dengan proteksi error Telegram"""
    try:
        if query.message and query.message.photo:
            # Jika teks melebihi limit caption (1024 char) atau menu teks murni,
            # hapus foto dan kirim pesan teks baru agar tidak memicu error caption
            if len(text) > 1000:
                try:
                    await query.message.delete()
                except Exception:
                    pass
                await query.message.get_bot().send_message(
                    chat_id=query.message.chat_id,
                    text=text,
                    reply_markup=markup,
                    parse_mode=parse_mode
                )
                return
            elif query.message.caption is not None:
                await query.edit_message_caption(caption=text, reply_markup=markup, parse_mode=parse_mode)
                return

        await query.edit_message_text(text=text, reply_markup=markup, parse_mode=parse_mode)
    except Exception as e:
        if "Message is not modified" in str(e):
            return
        try:
            await query.message.reply_text(text=text, reply_markup=markup, parse_mode=parse_mode)
        except Exception:
            pass

async def mulai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler perintah /mulai dan /start"""
    user = update.effective_user
    chat_id = user.id

    # Cek apakah user diblokir oleh admin
    if is_user_blocked(chat_id):
        await update.message.reply_text("⛔ Akses Anda telah diblokir secara permanen oleh Administrator.")
        return

    # Perbarui data profil pengguna
    simpan_update_user_profile(chat_id, username=user.username, first_name=user.first_name)

    # Reset state admin jika ada
    context.user_data.clear()

    # Cek status keanggotaan di kedua channel secara langsung
    all_joined, unjoined = await check_user_channels(context.bot, chat_id)

    # Jika keluar dari salah satu channel atau belum pernah join
    if not all_joined:
        if user_terdaftar(chat_id):
            hapus_user(chat_id)
            print(f"[MEMBER KELUAR]: User {chat_id} terdeteksi keluar dari channel saat /mulai, dihapus dari data.")

        user_nama_safe = html.escape(user.first_name or "Pelanggan")
        pesan_gate = (
            f"👋 <b>Halo, {user_nama_safe}! Selamat datang di AI Barokah Store.</b>\n\n"
            f"Satu langkah kecil sebelum mulai berbelanja! Untuk memastikan Anda mendapatkan "
            f"info pembaruan produk, promo eksklusif, dan pelacakan transaksi otomatis, "
            f"silakan bergabung ke dua channel resmi kami:\n\n"
            f"📢 <b>1. Store AI Barokah</b> (Katalog & Promo Spesial)\n"
            f"🔔 <b>2. Channel Notifikasi</b> (Bukti Transaksi & Status Layanan)\n\n"
            f"Klik kedua tombol channel di bawah untuk bergabung, lalu tekan "
            f"<b>'✅ Sudah Join Keduanya'</b> untuk membuka menu utama."
        )

        await update.message.reply_text(
            text=pesan_gate,
            reply_markup=buat_keyboard_gate(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return

    # Jika sudah lolos verifikasi kedua channel, simpan user ke database
    tambah_user(chat_id, username=user.username, first_name=user.first_name)

    pesan, markup = buat_tampilan_utama(user)
    reply_kb = buat_reply_keyboard_utama(user)
    gambar = ambil_gambar_gate()
    if gambar:
        with open(gambar, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=pesan,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
        await update.message.reply_text(
            text="🏠 Silakan pilih menu di atas atau gunakan navigasi keyboard di bawah:",
            reply_markup=reply_kb
        )
    else:
        await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
        await update.message.reply_text(
            text="🏠 Silakan pilih menu di atas atau gunakan navigasi keyboard di bawah:",
            reply_markup=reply_kb
        )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler perintah /admin khusus untuk Administrator"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Anda bukan Administrator bot ini.")
        return

    context.user_data.clear()
    pesan, markup = buat_tampilan_admin_panel()
    await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
    await update.message.reply_text(
        text="⚙️ Panel Administrator aktif. Gunakan menu di atas atau tombol navigasi di bawah:",
        reply_markup=buat_reply_keyboard_utama(user)
    )

async def batal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler perintah /batal untuk membatalkan proses wizard atau input apa pun"""
    user = update.effective_user
    context.user_data.clear()
    if user.id in ADMIN_IDS:
        await update.message.reply_text(
            "❌ Proses dibatalkan. Ketik /admin untuk kembali ke menu admin.",
            reply_markup=buat_reply_keyboard_utama(user)
        )
    else:
        await update.message.reply_text(
            "❌ Proses dibatalkan. Silakan pilih menu di bawah ini:",
            reply_markup=buat_reply_keyboard_utama(user)
        )
