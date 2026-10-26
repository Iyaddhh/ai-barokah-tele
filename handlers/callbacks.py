import html
import asyncio
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import ADMIN_IDS, NOTIF_CHANNEL_ID, CHANNELS
from database import (
    tambah_user,
    get_semua_produk,
    get_produk_by_id,
    tambah_produk,
    tambah_stok,
    update_promo,
    hapus_produk,
    get_semua_kategori,
    hapus_kategori,
    is_user_blocked,
    blokir_user,
    unblock_user,
    simpan_update_user_profile,
    get_user_profile,
    get_semua_users_data,
    buat_order,
    get_order,
    get_order_aktif_user,
    update_status_order,
    cek_status_order_expired,
    perpanjang_atau_reset_order,
    tambah_stok_items,
    ambil_dan_potong_stok,
    get_items_produk,
    selesaikan_order,
)
from helpers import check_user_channels, ambil_gambar_gate
from qris import generate_dynamic_qris, buat_gambar_qris_bytes
from ui import (
    buat_tampilan_utama,
    buat_tampilan_katalog,
    buat_tampilan_detail_produk,
    buat_tampilan_invoice_qris,
    buat_tampilan_riwayat_pesanan,
    buat_tampilan_admin_lihat_akun,
    buat_tampilan_admin_panel,
    buat_tampilan_kelola_produk_menu,
    buat_tampilan_daftar_stok,
    buat_tampilan_admin_detail_produk,
    buat_tampilan_daftar_users,
    buat_tampilan_detail_user,
    buat_keyboard_pilih_edit,
    buat_tampilan_edit_detail,
    buat_keyboard_pilih_hapus,
    buat_tampilan_konfirmasi_hapus,
    buat_keyboard_kelola_promo,
    buat_tampilan_atur_promo,
    buat_tampilan_kelola_kategori,
    buat_keyboard_hapus_kategori,
    buat_pesan_wizard_step1,
    buat_keyboard_wizard_step1,
    buat_pesan_wizard_step2,
    buat_keyboard_wizard_step2,
    buat_pesan_wizard_step3,
    buat_keyboard_wizard_step3,
    buat_pesan_wizard_step4,
    buat_keyboard_wizard_step4,
    buat_pesan_wizard_step5,
    buat_keyboard_wizard_step5,
    buat_pesan_wizard_preview,
    buat_keyboard_konfirmasi_tambah,
    buat_reply_keyboard_katalog,
    buat_reply_keyboard_stok_admin,
    buat_reply_keyboard_users_admin,
    buat_reply_keyboard_utama,
    buat_tampilan_daftar_kategori_pelanggan,
    buat_inline_keyboard_kategori_pelanggan,
    buat_tampilan_support,
)
from .common import edit_pesan_aman

async def tombol_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler event interaksi tombol inline keyboard"""
    query = update.callback_query
    user = query.from_user
    chat_id = user.id
    data = query.data

    # Cek apakah user diblokir oleh admin
    if is_user_blocked(chat_id):
        await query.answer("⛔ Akses Anda telah diblokir secara permanen oleh Administrator.", show_alert=True)
        return

    # Perbarui data profil pengguna
    simpan_update_user_profile(chat_id, username=user.username, first_name=user.first_name)

    # 1. VERIFIKASI DUA CHANNEL
    if data == "verifikasi_join":
        all_joined, unjoined = await check_user_channels(context.bot, chat_id)

        if all_joined:
            tambah_user(chat_id, username=user.username, first_name=user.first_name)
            await query.answer("✅ Verifikasi berhasil! Selamat datang.", show_alert=True)

            waktu_sekarang = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M:%S")
            username_info = f"@{user.username}" if user.username else "Tidak ada"
            user_nama_safe = html.escape(user.first_name or "Pelanggan")

            pesan_notif = (
                f"🔔 <b>MEMBER BARU BERGABUNG</b>\n"
                f"────────────────────────\n"
                f"👤 <b>Nama:</b> {user_nama_safe}\n"
                f"🆔 <b>ID Telegram:</b> <code>{chat_id}</code>\n"
                f"🔗 <b>Username:</b> {username_info}\n"
                f"⏰ <b>Waktu:</b> {waktu_sekarang} WIB\n"
                f"────────────────────────\n"
                f"Status: <i>Berhasil verifikasi 2 channel</i>"
            )

            try:
                await context.bot.send_message(
                    chat_id=NOTIF_CHANNEL_ID,
                    text=pesan_notif,
                    parse_mode=ParseMode.HTML
                )
            except Exception as err:
                print(f"[GAGAL KIRIM NOTIF]: {err}")

            pesan, markup = buat_tampilan_utama(user)
            reply_kb = buat_reply_keyboard_utama(user)
            gambar = ambil_gambar_gate()
            if gambar:
                try:
                    await query.message.delete()
                except Exception:
                    pass
                with open(gambar, "rb") as photo:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=pesan,
                        reply_markup=markup,
                        parse_mode=ParseMode.HTML,
                    )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🏠 Silakan pilih menu di atas atau gunakan navigasi keyboard di bawah:",
                    reply_markup=reply_kb
                )
            else:
                await edit_pesan_aman(query, pesan, markup)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🏠 Silakan pilih menu di atas atau gunakan navigasi keyboard di bawah:",
                    reply_markup=reply_kb
                )
        else:
            nama_channel = "\n".join([f"• {ch['name']}" for ch in unjoined])
            pesan_gagal = f"❌ Anda belum join channel:\n{nama_channel}\n\nSilakan klik tombol di atas untuk gabung!"
            if len(pesan_gagal) > 195:
                pesan_gagal = pesan_gagal[:190] + "..."
            try:
                await query.answer(pesan_gagal, show_alert=True)
            except Exception:
                await query.answer("❌ Anda belum bergabung ke semua channel!", show_alert=True)
        return

    if data == "noop":
        await query.answer()
        return

    # 2. KEMBALI KE MENU UTAMA
    if data == "kembali_ke_menu":
        await query.answer()
        context.user_data.clear()
        pesan, markup = buat_tampilan_utama(user)
        await edit_pesan_aman(query, pesan, markup)
        await context.bot.send_message(
            chat_id=chat_id,
            text="🏠 Kembali ke Menu Utama.",
            reply_markup=buat_reply_keyboard_utama(user)
        )
        return

    # 3. LIHAT KATALOG PRODUK
    if data == "menu_produk":
        await query.answer()
        context.user_data["menu_aktif"] = "katalog"
        context.user_data["katalog_filter"] = None
        context.user_data["katalog_page"] = 1
        semua_produk = get_semua_produk()
        pesan, markup = buat_tampilan_katalog(page=1)
        if query.message.photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=chat_id,
                text=pesan,
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
        else:
            await edit_pesan_aman(query, pesan, markup)
        await context.bot.send_message(
            chat_id=chat_id,
            text="👇 <b>Keyboard Nomor Produk:</b>\nTekan tombol nomor di bawah untuk melihat detail produk langsung:",
            reply_markup=buat_reply_keyboard_katalog(semua_produk, page=1),
            parse_mode=ParseMode.HTML
        )
        return

    # 3a. PAGINATION KATALOG PELANGGAN
    if data.startswith("katalog_hal_"):
        await query.answer()
        page = int(data.split("_")[2])
        context.user_data["katalog_page"] = page
        kat_filter = context.user_data.get("katalog_filter")
        semua_produk = get_semua_produk()
        if kat_filter:
            daftar = [p for p in semua_produk if p.get("kategori", "Umum").lower() == kat_filter.lower()]
        else:
            daftar = semua_produk
        pesan, markup = buat_tampilan_katalog(kategori_filter=kat_filter, page=page)
        await edit_pesan_aman(query, pesan, markup)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📄 Halaman {page} (Katalog Produk):",
            reply_markup=buat_reply_keyboard_katalog(daftar, page=page)
        )
        return

    # 3b. PILIH KATEGORI OLEH PELANGGAN
    if data == "pelanggan_pilih_kategori":
        await query.answer()
        context.user_data["menu_aktif"] = "kategori_pelanggan"
        context.user_data["kategori_page"] = 1
        pesan, reply_kb = buat_tampilan_daftar_kategori_pelanggan(page=1)
        inline_kb = buat_inline_keyboard_kategori_pelanggan(page=1)
        await edit_pesan_aman(query, pesan, inline_kb)
        await context.bot.send_message(
            chat_id=chat_id,
            text="👇 <b>Keyboard Nomor Kategori:</b>\nTekan tombol nomor kategori di bawah untuk melihat produknya:",
            reply_markup=reply_kb,
            parse_mode=ParseMode.HTML
        )
        return

    # 3c. PAGINATION DAFTAR KATEGORI PELANGGAN
    if data.startswith("pelanggan_kat_hal_"):
        await query.answer()
        page = int(data.split("_")[3])
        context.user_data["kategori_page"] = page
        pesan, reply_kb = buat_tampilan_daftar_kategori_pelanggan(page=page)
        inline_kb = buat_inline_keyboard_kategori_pelanggan(page=page)
        await edit_pesan_aman(query, pesan, inline_kb)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📄 Halaman {page} (Daftar Kategori):",
            reply_markup=reply_kb
        )
        return

    if data.startswith("pelanggan_kat_pilih_"):
        await query.answer()
        idx = int(data.split("_")[3])
        kat_list = get_semua_kategori()
        if 1 <= idx <= len(kat_list):
            kat_dipilih = kat_list[idx - 1]
            context.user_data["menu_aktif"] = "katalog"
            context.user_data["katalog_filter"] = kat_dipilih
            context.user_data["katalog_page"] = 1
            semua_p = [p for p in get_semua_produk() if p.get("kategori", "Umum").lower() == kat_dipilih.lower()]
            pesan, markup = buat_tampilan_katalog(kategori_filter=kat_dipilih, page=1)
            await edit_pesan_aman(query, pesan, markup)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"👇 Pilih nomor produk pada kategori <b>{html.escape(kat_dipilih)}</b>:",
                reply_markup=buat_reply_keyboard_katalog(semua_p, page=1),
                parse_mode=ParseMode.HTML
            )
        return

    # 4. DETAIL PRODUK TERTENTU
    if data.startswith("produk_detail_"):
        await query.answer()
        parts = data.split("_")
        pid = int(parts[2])
        jumlah = int(parts[3]) if len(parts) > 3 else 1
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return

        pesan, markup = buat_tampilan_detail_produk(produk, jumlah=jumlah)
        await edit_pesan_aman(query, pesan, markup)
        return

    # 4b. KURANG JUMLAH BELI (-)
    if data.startswith("beli_kurang_"):
        parts = data.split("_")
        pid = int(parts[2])
        jumlah = int(parts[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return

        if jumlah <= 1:
            await query.answer("⚠️ Minimal pembelian adalah 1 item.", show_alert=False)
            return

        jumlah_baru = max(1, jumlah - 1)
        await query.answer()
        pesan, markup = buat_tampilan_detail_produk(produk, jumlah=jumlah_baru)
        await edit_pesan_aman(query, pesan, markup)
        return

    # 4c. TAMBAH JUMLAH BELI (+)
    if data.startswith("beli_tambah_"):
        parts = data.split("_")
        pid = int(parts[2])
        jumlah = int(parts[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return

        stok_max = produk.get("stok", 0)
        if jumlah >= stok_max:
            await query.answer(f"⚠️ Pembelian sudah mencapai batas stok ({stok_max} item)!", show_alert=True)
            return

        jumlah_baru = min(stok_max, jumlah + 1)
        await query.answer()
        pesan, markup = buat_tampilan_detail_produk(produk, jumlah=jumlah_baru)
        await edit_pesan_aman(query, pesan, markup)
        return

    # 4d. BELI VIA QRIS (GOPAY MERCHANT DINAMIS)
    if data.startswith("beli_qris_"):
        parts = data.split("_")
        pid = int(parts[2])
        jumlah = int(parts[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return

        stok = produk.get("stok", 0)
        if jumlah > stok:
            await query.answer(f"⚠️ Stok tidak mencukupi (sisa {stok}).", show_alert=True)
            return

        await query.answer("⏳ Menyiapkan QRIS pembayaran...", show_alert=False)

        harga_satuan = produk.get("harga_promo", 0) if produk.get("harga_promo", 0) > 0 else produk.get("harga", 0)
        total_bayar = harga_satuan * jumlah

        try:
            # Generate QRIS Dinamis & QR Code Image
            dyn_qris = generate_dynamic_qris(nominal=total_bayar)
            qr_bytes = buat_gambar_qris_bytes(dyn_qris)

            # Buat order di database
            order = buat_order(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                produk=produk,
                jumlah=jumlah,
                qris_payload=dyn_qris,
                durasi_menit=5
            )

            caption, markup = buat_tampilan_invoice_qris(order)

            # Hapus pesan lama dan kirim foto QR Code
            try:
                await query.message.delete()
            except Exception:
                pass

            await context.bot.send_photo(
                chat_id=chat_id,
                photo=qr_bytes,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=markup
            )
        except Exception as e:
            print(f"[ERROR BELI QRIS]: {e}")
            await query.message.reply_text(f"⚠️ Gagal membuat QRIS pembayaran: {e}")
        return

    # 4e. KONFIRMASI PEMBAYARAN ORDER
    if data.startswith("konfirmasi_order_"):
        order_id = data.replace("konfirmasi_order_", "")
        is_exp, order = cek_status_order_expired(order_id)
        if not order:
            await query.answer("Pesanan tidak ditemukan!", show_alert=True)
            return

        if is_exp:
            await query.answer("⚠️ Batas waktu 5 menit telah habis! Transaksi gagal. Silakan klik 'Lanjutkan Bayar' untuk kode QR baru.", show_alert=True)
            pesan, markup = buat_tampilan_invoice_qris(order)
            await edit_pesan_aman(query, pesan, markup)
            return

        # Update status order ke WAITING_ADMIN
        update_status_order(order_id, "WAITING_ADMIN")
        order["status"] = "WAITING_ADMIN"

        await query.answer("✅ Konfirmasi pembayaran terkirim! Admin akan segera memverifikasi.", show_alert=True)

        # Kirim notifikasi konfirmasi ke Admin & Channel Notifikasi
        pesan_notif = (
            "🔔 <b>KONFIRMASI PEMBAYARAN QRIS MASUK!</b>\n"
            "────────────────────────\n"
            f"🆔 <b>No. Invoice:</b> <code>{order_id}</code>\n"
            f"👤 <b>Pembeli:</b> {html.escape(order.get('first_name') or 'User')} (@{html.escape(order.get('username') or '-')})\n"
            f"🆔 <b>User ID:</b> <code>{order.get('user_id')}</code>\n"
            f"📦 <b>Produk:</b> {html.escape(order.get('nama_produk', 'Produk'))} ({order.get('jumlah')} item)\n"
            f"💰 <b>Total Tagihan:</b> <b>Rp {order.get('total_bayar', 0):,}</b>\n"
            f"⏰ <b>Waktu Order:</b> {order.get('created_at')}\n"
            "────────────────────────\n"
            "💡 <i>Pembeli telah mengonfirmasi pembayaran QRIS GoPay Merchant. Silakan periksa mutasi akun GoBiz Anda.</i>"
        )

        markup_admin = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Verifikasi & Kirim Barang Otomatis", callback_data=f"admin_approve_order_{order_id}")],
            [InlineKeyboardButton("❌ Tolak Pembayaran", callback_data=f"admin_reject_order_{order_id}")]
        ])

        if NOTIF_CHANNEL_ID:
            try:
                await context.bot.send_message(
                    chat_id=NOTIF_CHANNEL_ID,
                    text=pesan_notif,
                    parse_mode=ParseMode.HTML,
                    reply_markup=markup_admin
                )
            except Exception as e:
                print(f"[ERROR NOTIF CHANNEL]: {e}")

        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=aid,
                    text=pesan_notif,
                    parse_mode=ParseMode.HTML,
                    reply_markup=markup_admin
                )
            except Exception:
                pass

        pesan, markup = buat_tampilan_invoice_qris(order)
        await edit_pesan_aman(query, pesan, markup)
        return

    # 4f. CEK STATUS ORDER / REFRESH
    if data.startswith("cek_order_"):
        order_id = data.replace("cek_order_", "")
        is_exp, order = cek_status_order_expired(order_id)
        if not order:
            await query.answer("Pesanan tidak ditemukan!", show_alert=True)
            return

        if is_exp:
            await query.answer("⚠️ Waktu 5 menit telah habis! Transaksi gagal. Silakan klik 'Lanjutkan Bayar' untuk kode QR baru.", show_alert=True)
        elif order.get("status") == "WAITING_ADMIN":
            await query.answer("🟡 Sedang menunggu pemeriksaan admin.", show_alert=False)
        elif order.get("status") == "PAID":
            await query.answer("✅ Pembayaran telah terverifikasi!", show_alert=True)
        else:
            await query.answer("⏳ Menunggu pembayaran dari Anda...", show_alert=False)

        pesan, markup = buat_tampilan_invoice_qris(order)
        await edit_pesan_aman(query, pesan, markup)
        return

    # 4g. BATALKAN ORDER
    if data.startswith("batal_order_"):
        order_id = data.replace("batal_order_", "")
        order = get_order(order_id)
        if order and order.get("status") in ["PENDING", "WAITING_ADMIN"]:
            update_status_order(order_id, "CANCELLED")
            order["status"] = "CANCELLED"
            await query.answer("🚫 Pesanan telah dibatalkan.", show_alert=True)
            pesan, markup = buat_tampilan_invoice_qris(order)
            await edit_pesan_aman(query, pesan, markup)
        else:
            await query.answer("Pesanan tidak dapat dibatalkan.", show_alert=True)
        return

    # 4h. GENERATE ULANG QR CODE / LANJUTKAN BAYAR JIKA EXPIRED
    if data.startswith("ulang_order_"):
        order_id = data.replace("ulang_order_", "")
        order = get_order(order_id)
        if not order:
            await query.answer("Pesanan tidak ditemukan!", show_alert=True)
            return

        produk = get_produk_by_id(order.get("produk_id"))
        if not produk:
            await query.answer("Produk sudah tidak tersedia!", show_alert=True)
            return

        stok = produk.get("stok", 0)
        jumlah = order.get("jumlah", 1)
        if jumlah > stok:
            await query.answer(f"⚠️ Maaf, stok produk tidak mencukupi (sisa {stok}).", show_alert=True)
            return

        await query.answer("🔄 Menghasilkan kode QR baru...", show_alert=False)

        try:
            total_bayar = order.get("total_bayar", 0)
            dyn_qris = generate_dynamic_qris(nominal=total_bayar)
            qr_bytes = buat_gambar_qris_bytes(dyn_qris)

            # Reset timer dan perbarui payload
            order = perpanjang_atau_reset_order(order_id, durasi_menit=5, qris_payload=dyn_qris)
            caption, markup = buat_tampilan_invoice_qris(order)

            # Ganti media foto QR secara langsung
            try:
                from telegram import InputMediaPhoto
                await query.edit_message_media(
                    media=InputMediaPhoto(media=qr_bytes, caption=caption, parse_mode=ParseMode.HTML),
                    reply_markup=markup
                )
            except Exception:
                try:
                    await query.message.delete()
                except Exception:
                    pass
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=qr_bytes,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=markup
                )
        except Exception as e:
            print(f"[ERROR ULANG ORDER]: {e}")
            await query.message.reply_text(f"⚠️ Gagal memperbarui kode QR: {e}")
        return

    # 4i. ADMIN APPROVE ORDER (VERIFIKASI & KIRIM OTOMATIS)
    if data.startswith("admin_approve_order_"):
        if chat_id not in ADMIN_IDS:
            await query.answer("⛔ Akses ditolak! Khusus Administrator.", show_alert=True)
            return

        order_id = data.replace("admin_approve_order_", "")
        order = get_order(order_id)
        if not order:
            await query.answer("Pesanan tidak ditemukan!", show_alert=True)
            return

        if order.get("status") == "PAID":
            await query.answer("Pesanan ini sudah berstatus PAID sebelumnya.", show_alert=True)
            return

        sukses, order_upd, err = selesaikan_order(order_id)
        if not sukses:
            await query.answer(f"⚠️ Gagal memproses pesanan: {err}", show_alert=True)
            return

        await query.answer("✅ Pembayaran diverifikasi! Barang otomatis dikirimkan ke pembeli.", show_alert=True)

        # Kirim pesan penyerahan barang langsung ke chat pribadi pembeli
        delivered_items = order_upd.get("delivered_items", [])
        nama_p = order_upd.get("nama_produk", "Produk")
        qty = order_upd.get("jumlah", 1)
        total = order_upd.get("total_bayar", 0)

        pesan_buyer = (
            "🎉 <b>PEMBAYARAN DITERIMA & PESANAN SELESAI!</b>\n"
            "────────────────────────\n"
            f"🆔 <b>No. Invoice:</b> <code>{order_id}</code>\n"
            f"📦 <b>Produk:</b> {html.escape(nama_p)} ({qty} item)\n"
            f"💰 <b>Total Bayar:</b> Rp {total:,}\n"
            "────────────────────────\n"
            "🎁 <b>Berikut Data Akun / Pesanan Anda:</b>\n\n"
        )
        for idx, it in enumerate(delivered_items, 1):
            pesan_buyer += f"<b>{idx}.</b> <code>{html.escape(str(it))}</code>\n"

        pesan_buyer += (
            "\n────────────────────────\n"
            "⚠️ <i>Harap segera simpan dan amankan data akun di atas.</i>\n"
            f"💬 <i>Jika ada kendala garansi atau pertanyaan, hubungi Admin: {ADMIN_USERNAME}</i>"
        )

        try:
            await context.bot.send_message(
                chat_id=order_upd["user_id"],
                text=pesan_buyer,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"[ERROR KIRIM KE BUYER]: {e}")

        # Update pesan di chat Admin / Channel
        pesan_admin_done = (
            "✅ <b>PESANAN SELESAI & BARANG SUDAH DIKIRIMKAN!</b>\n"
            "────────────────────────\n"
            f"🆔 <b>No. Invoice:</b> <code>{order_id}</code>\n"
            f"👤 <b>Pembeli:</b> {html.escape(order_upd.get('first_name') or 'User')} (@{html.escape(order_upd.get('username') or '-')})\n"
            f"📦 <b>Produk:</b> {html.escape(nama_p)} ({qty} item)\n"
            f"💰 <b>Total Tagihan:</b> Rp {total:,}\n"
            f"⏰ <b>Waktu Selesai:</b> {order_upd.get('paid_at')}\n"
            "────────────────────────\n"
            f"✨ <i>Stok otomatis dipotong ({qty} item) dan data akun telah dikirimkan ke pembeli.</i>"
        )
        try:
            await query.edit_message_text(text=pesan_admin_done, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    # 4j. ADMIN REJECT ORDER (TOLAK PEMBAYARAN)
    if data.startswith("admin_reject_order_"):
        if chat_id not in ADMIN_IDS:
            await query.answer("⛔ Akses ditolak! Khusus Administrator.", show_alert=True)
            return

        order_id = data.replace("admin_reject_order_", "")
        order = get_order(order_id)
        if not order:
            await query.answer("Pesanan tidak ditemukan!", show_alert=True)
            return

        update_status_order(order_id, "CANCELLED")
        await query.answer("🚫 Pembayaran ditolak dan pesanan dibatalkan.", show_alert=True)

        # Beritahu pembeli
        try:
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    f"❌ <b>PESANAN DIBATALKAN</b>\n"
                    "────────────────────────\n"
                    f"No. Invoice: <code>{order_id}</code>\n"
                    "Konfirmasi pembayaran Anda tidak dapat diverifikasi oleh Admin.\n"
                    f"Jika ada kendala, silakan hubungi {ADMIN_USERNAME} beserta bukti transfer."
                ),
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

        try:
            await query.edit_message_text(
                text=f"🚫 <b>PESANAN DITOLAK</b>\nNo. Invoice: <code>{order_id}</code> telah dibatalkan oleh Admin.",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
        return

    # 5. MENU SALDO & PESANAN (INFO CEPAT)
    if data == "menu_saldo":
        await query.answer("🩵 Saldo Anda saat ini: Rp 0. Hubungi admin untuk top up.", show_alert=True)
        return

    if data == "menu_pesanan":
        await query.answer()
        pesan, markup = buat_tampilan_riwayat_pesanan(user.id, page=1)
        await edit_pesan_aman(query, pesan, markup)
        return

    # BUKA RINCIAN PESANAN DARI RIWAYAT
    if data.startswith("buka_order_"):
        await query.answer()
        order_id = data.replace("buka_order_", "")
        order = get_order(order_id)
        if not order:
            await query.answer("Pesanan tidak ditemukan!", show_alert=True)
            return
        pesan, markup = buat_tampilan_invoice_qris(order)
        await edit_pesan_aman(query, pesan, markup)
        return

    # PAGINATION RIWAYAT PESANAN
    if data.startswith("riwayat_hal_"):
        await query.answer()
        page = int(data.split("_")[2])
        pesan, markup = buat_tampilan_riwayat_pesanan(user.id, page=page)
        await edit_pesan_aman(query, pesan, markup)
        return

    # 6. MENU SUPPORT
    if data == "menu_support":
        await query.answer()
        pesan, markup = buat_tampilan_support()
        await edit_pesan_aman(query, pesan, markup)
        return

    # ==================== FITUR ADMINISTRATOR ====================

    # Pastikan aksi admin & wizard hanya bisa diakses oleh admin
    if data.startswith("admin_") or data.startswith("wizard_") or data.startswith("tambah_") or data == "batal_tambah_produk":
        if chat_id not in ADMIN_IDS:
            await query.answer("⛔ Akses khusus Administrator!", show_alert=True)
            return

    if data == "admin_panel":
        await query.answer()
        context.user_data.clear()
        pesan, markup = buat_tampilan_admin_panel()
        await edit_pesan_aman(query, pesan, markup)
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚙️ Kembali ke Panel Administrator.",
            reply_markup=buat_reply_keyboard_utama(user)
        )
        return

    # LIHAT RINCIAN STOK SEMUA PRODUK
    if data == "admin_lihat_stok":
        await query.answer()
        context.user_data.clear()
        context.user_data["menu_aktif"] = "admin_stok"
        context.user_data["stok_page"] = 1
        semua_produk = get_semua_produk()
        pesan, markup = buat_tampilan_daftar_stok(page=1)
        await edit_pesan_aman(query, pesan, markup)
        await context.bot.send_message(
            chat_id=chat_id,
            text="👇 <b>Keyboard Nomor Produk (Admin):</b>\nTekan nomor produk di bawah untuk melihat rincian detail & stok:",
            reply_markup=buat_reply_keyboard_stok_admin(semua_produk, page=1),
            parse_mode=ParseMode.HTML
        )
        return

    # PAGINATION DAFTAR STOK ADMIN
    if data.startswith("admin_stok_hal_"):
        await query.answer()
        page = int(data.split("_")[3])
        context.user_data["stok_page"] = page
        semua_produk = get_semua_produk()
        pesan, markup = buat_tampilan_daftar_stok(page=page)
        await edit_pesan_aman(query, pesan, markup)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📄 Halaman {page} (Daftar Stok Produk):",
            reply_markup=buat_reply_keyboard_stok_admin(semua_produk, page=page)
        )
        return

    # LIHAT DETAIL LENGKAP PRODUK DARI DAFTAR STOK
    if data.startswith("admin_stok_detail_"):
        await query.answer()
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return

        semua = get_semua_produk()
        nomor = next((i for i, p in enumerate(semua, start=1) if p["id"] == pid), None)
        pesan, markup = buat_tampilan_admin_detail_produk(produk, nomor=nomor)
        await edit_pesan_aman(query, pesan, markup)
        return

    # QUICK ACTION TAMBAH STOK DARI DETAIL
    if data.startswith("admin_detail_stok_tambah_"):
        pid = int(data.split("_")[4])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        tambah_stok(pid, 1)
        produk = get_produk_by_id(pid)
        await query.answer(f"✅ Stok bertambah: {produk['stok']} item", show_alert=False)
        semua = get_semua_produk()
        nomor = next((i for i, p in enumerate(semua, start=1) if p["id"] == pid), None)
        pesan, markup = buat_tampilan_admin_detail_produk(produk, nomor=nomor)
        await edit_pesan_aman(query, pesan, markup)
        return

    # QUICK ACTION KURANG STOK DARI DETAIL
    if data.startswith("admin_detail_stok_kurang_"):
        pid = int(data.split("_")[4])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        tambah_stok(pid, -1)
        produk = get_produk_by_id(pid)
        await query.answer(f"Stok berkurang: {produk['stok']} item", show_alert=False)
        semua = get_semua_produk()
        nomor = next((i for i, p in enumerate(semua, start=1) if p["id"] == pid), None)
        pesan, markup = buat_tampilan_admin_detail_produk(produk, nomor=nomor)
        await edit_pesan_aman(query, pesan, markup)
        return

    # RESTOCK AKUN BULK DARI DETAIL
    if data.startswith("admin_restock_"):
        pid = int(data.replace("admin_restock_", ""))
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return

        context.user_data["admin_state"] = f"restock_produk_{pid}"
        await query.answer()
        pesan_prompt = (
            f"📥 <b>RESTOCK AKUN: {html.escape(produk['nama'])}</b>\n"
            "────────────────────────\n"
            f"📊 <i>Stok saat ini:</i> <b>{produk.get('stok', 0)} item</b>\n\n"
            "Silakan <b>paste / kirimkan daftar akun baru</b> di chat:\n"
            "💡 <i>Format: <b>1 baris = 1 akun</b></i>\n\n"
            "<b>Contoh:</b>\n"
            "<code>userA@gmail.com | pass111 | PIN: 1234</code>\n"
            "<code>userB@gmail.com | pass222 | PIN: 5678</code>\n\n"
            "Kirimkan teks akun sekarang di chat:"
        )
        markup_prompt = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Batalkan", callback_data=f"admin_stok_detail_{pid}")]
        ])
        await edit_pesan_aman(query, pesan_prompt, markup_prompt)
        return

    # LIHAT DAFTAR AKUN PRODUK
    if data.startswith("admin_lihat_akun_"):
        pid = int(data.replace("admin_lihat_akun_", ""))
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        await query.answer()
        pesan, markup = buat_tampilan_admin_lihat_akun(produk)
        await edit_pesan_aman(query, pesan, markup)
        return

    # MENU UTAMA KELOLA PRODUK & STOK
    if data == "admin_list_stok":
        await query.answer()
        context.user_data.clear()
        pesan, markup = buat_tampilan_kelola_produk_menu()
        await edit_pesan_aman(query, pesan, markup)
        return

    # ==================== KELOLA KATEGORI (PANEL ADMIN) ====================
    # MENU UTAMA KELOLA KATEGORI
    if data == "admin_menu_kategori":
        await query.answer()
        context.user_data.clear()
        pesan, markup = buat_tampilan_kelola_kategori(page=1)
        await edit_pesan_aman(query, pesan, markup)
        return

    # PAGINATION MENU KELOLA KATEGORI ADMIN
    if data.startswith("admin_kat_menu_hal_"):
        await query.answer()
        page = int(data.split("_")[4])
        pesan, markup = buat_tampilan_kelola_kategori(page=page)
        await edit_pesan_aman(query, pesan, markup)
        return

    # INPUT TAMBAH KATEGORI BARU
    if data == "admin_kategori_tambah_input":
        await query.answer()
        context.user_data["admin_state"] = "kategori_tambah"
        pesan = (
            "➕ <b>Tambah Kategori Baru</b>\n"
            "────────────────────────\n"
            "Silakan ketik nama kategori baru di chat:\n"
            "<i>(Contoh: Streaming, AI Tools, Voucher Game)</i>"
        )
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Batalkan", callback_data="admin_menu_kategori")]
        ])
        await edit_pesan_aman(query, pesan, markup)
        return

    # MENU PILIH KATEGORI UNTUK DIHAPUS
    if data == "admin_kategori_hapus_menu":
        daftar_kategori = get_semua_kategori()
        if not daftar_kategori:
            await query.answer("❌ Belum ada kategori untuk dihapus.", show_alert=True)
            return
        await query.answer()
        pesan = (
            "🗑️ <b>PILIH KATEGORI UNTUK DIHAPUS</b>\n"
            "────────────────────────\n"
            "Klik kategori di bawah yang ingin Anda hapus:"
        )
        markup = buat_keyboard_hapus_kategori(daftar_kategori, page=1)
        await edit_pesan_aman(query, pesan, markup)
        return

    # PAGINATION HAPUS KATEGORI
    if data.startswith("admin_kat_del_hal_"):
        await query.answer()
        page = int(data.split("_")[4])
        daftar_kategori = get_semua_kategori()
        pesan = (
            "🗑️ <b>PILIH KATEGORI UNTUK DIHAPUS</b>\n"
            "────────────────────────\n"
            "Klik kategori di bawah yang ingin Anda hapus:"
        )
        markup = buat_keyboard_hapus_kategori(daftar_kategori, page=page)
        await edit_pesan_aman(query, pesan, markup)
        return

    # EKSEKUSI HAPUS KATEGORI BERDASARKAN INDEKS
    if data.startswith("admin_kat_del_"):
        idx = int(data.split("_")[3])
        daftar_kategori = get_semua_kategori()
        if 0 <= idx < len(daftar_kategori):
            kat_dihapus = daftar_kategori[idx]
            sukses, pesan_hasil = hapus_kategori(kat_dihapus)
            if not sukses:
                await query.answer(f"⚠️ {pesan_hasil}", show_alert=True)
                return
            await query.answer(f"✅ {pesan_hasil}", show_alert=True)
        else:
            await query.answer("Kategori tidak ditemukan!", show_alert=True)

        pesan, markup = buat_tampilan_kelola_kategori()
        await edit_pesan_aman(query, pesan, markup)
        return

    # ==================== KELOLA PENGGUNA (PANEL ADMIN) ====================
    # MENU UTAMA DAFTAR PENGGUNA TERDAFTAR
    if data == "admin_menu_users":
        await query.answer()
        context.user_data.clear()
        context.user_data["menu_aktif"] = "admin_users"
        context.user_data["users_page"] = 1

        # Sinkronkan profil pengguna dari Telegram jika username/nama belum tercatat
        semua_users = get_semua_users_data()
        for u in semua_users:
            if not u.get("username") or not u.get("first_name") or u.get("first_name") == "Pengguna":
                try:
                    c = await context.bot.get_chat(u["id"])
                    simpan_update_user_profile(u["id"], username=c.username, first_name=c.first_name)
                except Exception:
                    pass

        semua_users = get_semua_users_data()
        pesan, markup = buat_tampilan_daftar_users(semua_users, page=1)
        await edit_pesan_aman(query, pesan, markup)
        await context.bot.send_message(
            chat_id=chat_id,
            text="👇 <b>Keyboard Nomor Pengguna (Admin):</b>\nTekan nomor pengguna di bawah untuk melihat rincian detail & opsi blokir:",
            reply_markup=buat_reply_keyboard_users_admin(semua_users, page=1),
            parse_mode=ParseMode.HTML
        )
        return

    # PAGINATION DAFTAR PENGGUNA ADMIN
    if data.startswith("admin_users_hal_"):
        await query.answer()
        page = int(data.split("_")[3])
        context.user_data["users_page"] = page
        semua_users = get_semua_users_data()
        pesan, markup = buat_tampilan_daftar_users(semua_users, page=page)
        await edit_pesan_aman(query, pesan, markup)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📄 Halaman {page} (Daftar Pengguna):",
            reply_markup=buat_reply_keyboard_users_admin(semua_users, page=page)
        )
        return

    # DETAIL 1 PENGGUNA
    if data.startswith("admin_user_detail_"):
        await query.answer()
        target_uid = int(data.split("_")[3])

        # Sinkronkan info terkini jika belum lengkap
        u_prof = get_user_profile(target_uid)
        if not u_prof.get("username") or not u_prof.get("first_name") or u_prof.get("first_name") == "Pengguna":
            try:
                c = await context.bot.get_chat(target_uid)
                simpan_update_user_profile(target_uid, username=c.username, first_name=c.first_name)
                u_prof = get_user_profile(target_uid)
            except Exception:
                pass

        semua = get_semua_users_data()
        nomor = next((i for i, u in enumerate(semua, start=1) if u["id"] == target_uid), None)
        pesan, markup = buat_tampilan_detail_user(u_prof, nomor=nomor)
        await edit_pesan_aman(query, pesan, markup)
        return

    # BLOKIR & KICK PENGGUNA
    if data.startswith("admin_user_blokir_"):
        target_uid = int(data.split("_")[3])
        if target_uid in ADMIN_IDS:
            await query.answer("⚠️ Anda tidak dapat memblokir akun Administrator!", show_alert=True)
            return

        # 1. Tandai blokir di database & cabut status pendaftar
        blokir_user(target_uid)

        # 2. Kick / Ban dari channel wajib
        for ch in CHANNELS:
            try:
                await context.bot.ban_chat_member(chat_id=ch["id"], user_id=target_uid)
            except Exception as err:
                print(f"[GAGAL BAN DARI {ch['id']}]: {err}")

        u_prof = get_user_profile(target_uid)
        uname = f"@{u_prof.get('username')}" if u_prof.get('username') else f"ID {target_uid}"
        await query.answer(f"🚫 Pengguna {uname} berhasil diblokir, di-kick dari channel, dan akses dicabut!", show_alert=True)

        semua = get_semua_users_data()
        nomor = next((i for i, u in enumerate(semua, start=1) if u["id"] == target_uid), None)
        pesan, markup = buat_tampilan_detail_user(u_prof, nomor=nomor)
        await edit_pesan_aman(query, pesan, markup)
        return

    # BUKA BLOKIR PENGGUNA
    if data.startswith("admin_user_unblock_"):
        target_uid = int(data.split("_")[3])
        unblock_user(target_uid)

        for ch in CHANNELS:
            try:
                await context.bot.unban_chat_member(chat_id=ch["id"], user_id=target_uid, only_if_banned=True)
            except Exception:
                pass

        u_prof = get_user_profile(target_uid)
        uname = f"@{u_prof.get('username')}" if u_prof.get('username') else f"ID {target_uid}"
        await query.answer(f"✅ Blokir pengguna {uname} berhasil dibuka!", show_alert=True)

        semua = get_semua_users_data()
        nomor = next((i for i, u in enumerate(semua, start=1) if u["id"] == target_uid), None)
        pesan, markup = buat_tampilan_detail_user(u_prof, nomor=nomor)
        await edit_pesan_aman(query, pesan, markup)
        return

    # SUB-MENU 1: EDIT PRODUK
    if data == "admin_menu_edit_produk":
        semua = get_semua_produk()
        if not semua:
            await query.answer("❌ Belum ada produk untuk diedit. Silakan tambah produk baru terlebih dahulu.", show_alert=True)
            return
        await query.answer()
        pesan = "✏️ <b>PILIH PRODUK UNTUK DIEDIT</b>\n\nKlik nama produk yang ingin Anda ubah:"
        markup = buat_keyboard_pilih_edit(semua, page=1)
        await edit_pesan_aman(query, pesan, markup)
        return

    # PAGINATION EDIT PRODUK
    if data.startswith("admin_edit_hal_"):
        await query.answer()
        page = int(data.split("_")[3])
        semua = get_semua_produk()
        pesan = "✏️ <b>PILIH PRODUK UNTUK DIEDIT</b>\n\nKlik nama produk yang ingin Anda ubah:"
        markup = buat_keyboard_pilih_edit(semua, page=page)
        await edit_pesan_aman(query, pesan, markup)
        return

    if data.startswith("admin_edit_pilih_"):
        await query.answer()
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        pesan, markup = buat_tampilan_edit_detail(produk)
        await edit_pesan_aman(query, pesan, markup)
        return

    # SUB-MENU 2: HAPUS PRODUK
    if data == "admin_menu_hapus_produk":
        semua = get_semua_produk()
        if not semua:
            await query.answer("❌ Belum ada produk untuk dihapus.", show_alert=True)
            return
        await query.answer()
        pesan = "🗑️ <b>PILIH PRODUK UNTUK DIHAPUS</b>\n\nKlik produk yang ingin dihapus:"
        markup = buat_keyboard_pilih_hapus(semua, page=1)
        await edit_pesan_aman(query, pesan, markup)
        return

    # PAGINATION HAPUS PRODUK
    if data.startswith("admin_hapus_hal_"):
        await query.answer()
        page = int(data.split("_")[3])
        semua = get_semua_produk()
        pesan = "🗑️ <b>PILIH PRODUK UNTUK DIHAPUS</b>\n\nKlik produk yang ingin dihapus:"
        markup = buat_keyboard_pilih_hapus(semua, page=page)
        await edit_pesan_aman(query, pesan, markup)
        return

    # TOMBOL CEPAT TAMBAH STOK (+1) DI MENU EDIT
    if data.startswith("admin_stok_tambah_"):
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        tambah_stok(pid, 1)
        produk = get_produk_by_id(pid)
        await query.answer(f"✅ Stok {produk['nama']} bertambah jadi {produk['stok']}!", show_alert=False)
        pesan, markup = buat_tampilan_edit_detail(produk)
        await edit_pesan_aman(query, pesan, markup)
        return

    # TOMBOL CEPAT KURANG STOK (-1) DI MENU EDIT
    if data.startswith("admin_stok_kurang_"):
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        tambah_stok(pid, -1)
        produk = get_produk_by_id(pid)
        await query.answer(f"Stok {produk['nama']} menjadi {produk['stok']}", show_alert=False)
        pesan, markup = buat_tampilan_edit_detail(produk)
        await edit_pesan_aman(query, pesan, markup)
        return

    # INPUT MANUAL ANGKA STOK
    if data.startswith("admin_stok_input_"):
        await query.answer()
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        context.user_data["admin_state"] = f"set_stok_{pid}"
        nama_safe = html.escape(produk["nama"])
        pesan_minta = (
            f"✏️ <b>Set Stok Manual</b>\n"
            f"Produk: <b>{nama_safe}</b>\n\n"
            f"Ketik angka jumlah stok baru di chat ini (contoh: <code>15</code>):"
        )
        await context.bot.send_message(chat_id=chat_id, text=pesan_minta, parse_mode=ParseMode.HTML)
        return

    # KONFIRMASI HAPUS PRODUK
    if data.startswith("admin_hapus_produk_"):
        await query.answer()
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        pesan, markup = buat_tampilan_konfirmasi_hapus(produk)
        await edit_pesan_aman(query, pesan, markup)
        return

    # EKSEKUSI HAPUS PRODUK
    if data.startswith("admin_konfirm_hapus_"):
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        nama_p = produk["nama"] if produk else "Produk"
        hapus_produk(pid)
        await query.answer(f"🗑️ {nama_p} berhasil dihapus permanen!", show_alert=True)
        semua = get_semua_produk()
        if semua:
            pesan, markup = buat_tampilan_daftar_stok(page=1)
            await edit_pesan_aman(query, pesan, markup)
            await context.bot.send_message(
                chat_id=chat_id,
                text="📋 Daftar stok diperbarui:",
                reply_markup=buat_reply_keyboard_stok_admin(semua, page=1)
            )
        else:
            pesan, markup = buat_tampilan_kelola_produk_menu()
            await edit_pesan_aman(query, pesan, markup)
        return

    # EDIT NAMA PRODUK
    if data.startswith("admin_edit_nama_"):
        await query.answer()
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        context.user_data["admin_state"] = f"edit_nama_{pid}"
        nama_safe = html.escape(produk["nama"])
        pesan_minta = (
            f"✏️ <b>Edit Nama Produk</b>\n"
            f"Nama saat ini: <b>{nama_safe}</b>\n\n"
            f"Ketik nama baru produk ini di chat:"
        )
        await context.bot.send_message(chat_id=chat_id, text=pesan_minta, parse_mode=ParseMode.HTML)
        return

    # EDIT HARGA PRODUK
    if data.startswith("admin_edit_harga_"):
        await query.answer()
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        context.user_data["admin_state"] = f"edit_harga_{pid}"
        nama_safe = html.escape(produk["nama"])
        pesan_minta = (
            f"💵 <b>Edit Harga Produk</b>\n"
            f"Produk: <b>{nama_safe}</b>\n"
            f"Harga saat ini: Rp {produk['harga']:,}\n\n"
            f"Ketik nominal harga baru dalam angka (contoh: <code>45000</code>):"
        )
        await context.bot.send_message(chat_id=chat_id, text=pesan_minta, parse_mode=ParseMode.HTML)
        return

    # EDIT DESKRIPSI PRODUK
    if data.startswith("admin_edit_deskripsi_"):
        await query.answer()
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        context.user_data["admin_state"] = f"edit_deskripsi_{pid}"
        nama_safe = html.escape(produk["nama"])
        desk_safe = html.escape(produk.get("deskripsi", "-"))
        pesan_minta = (
            f"📝 <b>Edit Deskripsi Produk</b>\n"
            f"Produk: <b>{nama_safe}</b>\n"
            f"Deskripsi saat ini:\n<blockquote>{desk_safe}</blockquote>\n\n"
            f"Ketik deskripsi baru untuk produk ini di chat:"
        )
        await context.bot.send_message(chat_id=chat_id, text=pesan_minta, parse_mode=ParseMode.HTML)
        return

    # LIST PROMO
    if data == "admin_list_promo":
        await query.answer()
        context.user_data.clear()
        semua = get_semua_produk()
        if not semua:
            await query.answer("❌ Belum ada produk untuk diatur promonya.", show_alert=True)
            return
        pesan = "🏷️ <b>ATUR PROMO DISKON</b>\n\nPilih produk untuk diatur harga promo diskonnya:"
        markup = buat_keyboard_kelola_promo(semua, page=1)
        await edit_pesan_aman(query, pesan, markup)
        return

    # PAGINATION PROMO PRODUK
    if data.startswith("admin_promo_hal_"):
        await query.answer()
        page = int(data.split("_")[3])
        semua = get_semua_produk()
        pesan = "🏷️ <b>ATUR PROMO DISKON</b>\n\nPilih produk untuk diatur harga promo diskonnya:"
        markup = buat_keyboard_kelola_promo(semua, page=page)
        await edit_pesan_aman(query, pesan, markup)
        return

    # PILIH PRODUK PROMO
    if data.startswith("admin_pilih_promo_"):
        await query.answer()
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        pesan, markup = buat_tampilan_atur_promo(produk)
        await edit_pesan_aman(query, pesan, markup)
        return

    # MATIKAN PROMO
    if data.startswith("admin_promo_mati_"):
        pid = int(data.split("_")[3])
        update_promo(pid, 0)
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        await query.answer("❌ Promo dinonaktifkan!", show_alert=True)
        pesan, markup = buat_tampilan_atur_promo(produk)
        await edit_pesan_aman(query, pesan, markup)
        return

    # INPUT HARGA PROMO
    if data.startswith("admin_promo_input_"):
        await query.answer()
        pid = int(data.split("_")[3])
        produk = get_produk_by_id(pid)
        if not produk:
            await query.answer("Produk tidak ditemukan!", show_alert=True)
            return
        context.user_data["admin_state"] = f"set_promo_{pid}"
        nama_safe = html.escape(produk["nama"])
        pesan_minta = (
            f"🏷️ <b>Set Harga Promo</b>\n"
            f"Produk: <b>{nama_safe}</b>\n"
            f"Harga Normal: Rp {produk['harga']:,}\n\n"
            f"Ketik nominal harga promo diskon (contoh: <code>29000</code>):"
        )
        await context.bot.send_message(chat_id=chat_id, text=pesan_minta, parse_mode=ParseMode.HTML)
        return

    # ==================== WIZARD TAMBAH PRODUK (5 LANGKAH) ====================
    # LANGKAH 1 (NAMA PRODUK)
    if data == "admin_tambah_produk":
        await query.answer()
        context.user_data.clear()
        context.user_data["admin_state"] = "tambah_step_nama"
        pesan_petunjuk = buat_pesan_wizard_step1()
        await edit_pesan_aman(query, pesan_petunjuk, buat_keyboard_wizard_step1())
        return

    # NAVIGASI: STEP 1 (NAMA)
    if data == "wizard_ke_step1":
        await query.answer()
        context.user_data["admin_state"] = "tambah_step_nama"
        curr_nama = context.user_data.get("new_prod_nama")
        pesan = buat_pesan_wizard_step1(curr_nama)
        markup = buat_keyboard_wizard_step1(curr_nama)
        await edit_pesan_aman(query, pesan, markup)
        return

    # NAVIGASI: STEP 2 (KATEGORI)
    if data == "wizard_ke_step2":
        await query.answer()
        context.user_data["admin_state"] = "tambah_step_kategori"
        nama = context.user_data.get("new_prod_nama", "Produk")
        curr_kat = context.user_data.get("new_prod_kategori")
        pesan = buat_pesan_wizard_step2(nama, curr_kat, page=1)
        markup = buat_keyboard_wizard_step2(curr_kat, page=1)
        await edit_pesan_aman(query, pesan, markup)
        return

    # PAGINATION KATEGORI WIZARD STEP 2
    if data.startswith("wizard_kat_hal_"):
        await query.answer()
        page = int(data.split("_")[3])
        nama = context.user_data.get("new_prod_nama", "Produk")
        curr_kat = context.user_data.get("new_prod_kategori")
        pesan = buat_pesan_wizard_step2(nama, curr_kat, page=page)
        markup = buat_keyboard_wizard_step2(curr_kat, page=page)
        await edit_pesan_aman(query, pesan, markup)
        return

    # PILIH KATEGORI - LAINNYA (INPUT MANUAL)
    if data == "wizard_pilih_kat_lainnya":
        await query.answer()
        context.user_data["admin_state"] = "tambah_step_kategori_custom"
        nama = context.user_data.get("new_prod_nama", "Produk")
        pesan = (
            "✍️ <b>KATEGORI BARU (LAINNYA)</b>\n"
            "────────────────────────\n"
            f"Produk: <b>{html.escape(nama)}</b>\n\n"
            "Silakan ketik nama kategori baru di chat:"
        )
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⬅️ Kembali", callback_data="wizard_ke_step2"),
                InlineKeyboardButton("❌ Batalkan", callback_data="batal_tambah_produk")
            ]
        ])
        await edit_pesan_aman(query, pesan, markup)
        return

    # PILIH KATEGORI BERDASARKAN TOMBOL (1..N)
    if data.startswith("wizard_pilih_kat_"):
        idx = int(data.split("_")[3])
        kategori_list = get_semua_kategori()
        if 0 <= idx < len(kategori_list):
            kat_dipilih = kategori_list[idx]
        else:
            kat_dipilih = "Umum"

        await query.answer(f"✅ Kategori: {kat_dipilih}")
        context.user_data["new_prod_kategori"] = kat_dipilih
        context.user_data["admin_state"] = "tambah_step_harga"

        nama = context.user_data.get("new_prod_nama", "Produk")
        curr_harga = context.user_data.get("new_prod_harga")
        pesan = buat_pesan_wizard_step3(nama, kat_dipilih, curr_harga)
        markup = buat_keyboard_wizard_step3(curr_harga)
        await edit_pesan_aman(query, pesan, markup)
        return

    # NAVIGASI: STEP 3 (HARGA)
    if data == "wizard_ke_step3":
        await query.answer()
        context.user_data["admin_state"] = "tambah_step_harga"
        nama = context.user_data.get("new_prod_nama", "Produk")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        curr_harga = context.user_data.get("new_prod_harga")
        pesan = buat_pesan_wizard_step3(nama, kat, curr_harga)
        markup = buat_keyboard_wizard_step3(curr_harga)
        await edit_pesan_aman(query, pesan, markup)
        return

    # NAVIGASI: STEP 4 (STOK / ISIAN AKUN)
    if data == "wizard_ke_step4":
        await query.answer()
        context.user_data["admin_state"] = "tambah_step_stok"
        nama = context.user_data.get("new_prod_nama", "Produk")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        harga = context.user_data.get("new_prod_harga", 0)
        curr_stok = context.user_data.get("new_prod_stok")
        curr_items = context.user_data.get("new_prod_items")
        pesan = buat_pesan_wizard_step4(nama, kat, harga, curr_stok, curr_items)
        markup = buat_keyboard_wizard_step4(curr_stok, curr_items)
        await edit_pesan_aman(query, pesan, markup)
        return

    # WIZARD: SKIP / KOSONGKAN STOK DULU
    if data == "wizard_skip_stok":
        await query.answer()
        context.user_data["new_prod_items"] = []
        context.user_data["new_prod_stok"] = 0
        context.user_data["admin_state"] = "tambah_step_deskripsi"
        nama = context.user_data.get("new_prod_nama", "Produk")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        harga = context.user_data.get("new_prod_harga", 0)
        curr_desk = context.user_data.get("new_prod_deskripsi")
        pesan = buat_pesan_wizard_step5(nama, kat, harga, 0, curr_desk)
        markup = buat_keyboard_wizard_step5(curr_desk)
        await edit_pesan_aman(query, pesan, markup)
        return

    # NAVIGASI: STEP 5 (DESKRIPSI)
    if data == "wizard_ke_step5":
        await query.answer()
        context.user_data["admin_state"] = "tambah_step_deskripsi"
        nama = context.user_data.get("new_prod_nama", "Produk")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        harga = context.user_data.get("new_prod_harga", 0)
        stok = context.user_data.get("new_prod_stok", 0)
        curr_desk = context.user_data.get("new_prod_deskripsi")
        pesan = buat_pesan_wizard_step5(nama, kat, harga, stok, curr_desk)
        markup = buat_keyboard_wizard_step5(curr_desk)
        await edit_pesan_aman(query, pesan, markup)
        return

    # NAVIGASI: PRATINJAU (PREVIEW)
    if data == "wizard_ke_preview":
        await query.answer()
        context.user_data["admin_state"] = "tambah_konfirmasi"
        nama = context.user_data.get("new_prod_nama", "-")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        harga = context.user_data.get("new_prod_harga", 0)
        stok = context.user_data.get("new_prod_stok", 0)
        deskripsi = context.user_data.get("new_prod_deskripsi", "-")
        pesan = buat_pesan_wizard_preview(nama, kat, harga, stok, deskripsi)
        markup = buat_keyboard_konfirmasi_tambah()
        await edit_pesan_aman(query, pesan, markup)
        return

    # WIZARD: LEWATI DESKRIPSI
    if data == "tambah_skip_deskripsi":
        await query.answer()
        context.user_data["new_prod_deskripsi"] = "-"
        context.user_data["admin_state"] = "tambah_konfirmasi"

        nama = context.user_data.get("new_prod_nama", "-")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        harga = context.user_data.get("new_prod_harga", 0)
        stok = context.user_data.get("new_prod_stok", 0)

        pesan_preview = buat_pesan_wizard_preview(nama, kat, harga, stok, "-")
        markup = buat_keyboard_konfirmasi_tambah()
        await edit_pesan_aman(query, pesan_preview, markup)
        return

    # WIZARD: SIMPAN PRODUK KE DATABASE
    if data == "tambah_simpan_produk":
        nama = context.user_data.get("new_prod_nama")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        harga = context.user_data.get("new_prod_harga", 0)
        stok = context.user_data.get("new_prod_stok", 0)
        deskripsi = context.user_data.get("new_prod_deskripsi", "-")
        items = context.user_data.get("new_prod_items", [])

        if not nama:
            await query.answer("Data produk belum lengkap!", show_alert=True)
            return

        baru = tambah_produk(nama=nama, harga=harga, stok=stok, deskripsi=deskripsi, kategori=kat, items=items)
        context.user_data.clear()
        await query.answer("✅ Produk berhasil disimpan!", show_alert=True)

        baru_nama = html.escape(baru['nama'])
        baru_kat = html.escape(baru.get('kategori', 'Umum'))
        pesan_sukses = (
            "🎉 <b>PRODUK BERHASIL DITAMBAHKAN!</b>\n"
            "────────────────────────\n"
            f"📦 <b>Nama:</b> {baru_nama}\n"
            f"🏷️ <b>Kategori:</b> {baru_kat}\n"
            f"💵 <b>Harga:</b> Rp {baru['harga']:,}\n"
            f"📊 <b>Stok:</b> {baru['stok']} item\n"
            "────────────────────────\n"
            "Produk kini telah aktif dan langsung muncul di katalog toko pelanggan."
        )
        markup_sukses = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Kelola Stok Produk", callback_data="admin_list_stok")],
            [InlineKeyboardButton("⚙️ Panel Administrator", callback_data="admin_panel")]
        ])
        await edit_pesan_aman(query, pesan_sukses, markup_sukses)
        return

    # WIZARD: BATALKAN PROSES
    if data == "batal_tambah_produk":
        context.user_data.clear()
        await query.answer("❌ Penambahan produk dibatalkan.", show_alert=True)
        pesan, markup = buat_tampilan_kelola_produk_menu()
        await edit_pesan_aman(query, pesan, markup)
        return

    # BROADCAST PENGUMUMAN
    if data == "admin_broadcast":
        await query.answer()
        context.user_data["admin_state"] = "broadcast"
        pesan_broadcast = (
            "📢 <b>Broadcast Pesan ke Seluruh Pengguna</b>\n"
            "────────────────────────\n"
            "Ketik pesan yang ingin Anda kirimkan kepada semua pengguna terdaftar.\n"
            "Dukungan format HTML tersedia (<b>bold</b>, <i>italic</i>, dll).\n\n"
            "<i>Ketik pesan di bawah ini sekarang:</i>"
        )
        await context.bot.send_message(chat_id=chat_id, text=pesan_broadcast, parse_mode=ParseMode.HTML)
        return

