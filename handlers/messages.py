import os
import html
import asyncio
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import ADMIN_IDS, NOTIF_CHANNEL_ID
from database import (
    user_terdaftar,
    get_semua_produk,
    get_produk_by_id,
    tambah_produk,
    update_stok,
    tambah_stok_items,
    update_promo,
    update_nama_produk,
    update_harga_produk,
    update_deskripsi_produk,
    get_semua_kategori,
    tambah_kategori,
    is_user_blocked,
    simpan_update_user_profile,
    get_user_profile,
    get_semua_users_data,
    get_order_aktif_user,
    get_semua_user_ids,
)
from helpers import ambil_gambar_gate
from qris import generate_dynamic_qris, buat_gambar_qris_bytes
from ui import (
    buat_tampilan_utama,
    buat_tampilan_katalog,
    buat_tampilan_detail_produk,
    buat_tampilan_invoice_qris,
    buat_tampilan_riwayat_pesanan,
    buat_tampilan_admin_panel,
    buat_tampilan_kelola_produk_menu,
    buat_tampilan_daftar_stok,
    buat_tampilan_admin_detail_produk,
    buat_tampilan_daftar_users,
    buat_tampilan_detail_user,
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
    buat_reply_keyboard_katalog,
    buat_reply_keyboard_stok_admin,
    buat_reply_keyboard_users_admin,
    buat_reply_keyboard_utama,
    buat_tampilan_daftar_kategori_pelanggan,
    buat_inline_keyboard_kategori_pelanggan,
    buat_tampilan_support,
    hitung_pagination,
)

async def handle_pesan_teks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler input teks pesan untuk proses administrasi (stok, promo, tambah produk, broadcast)"""
    user = update.effective_user
    chat_id = user.id
    teks = update.message.text.strip()

    # Cek apakah user diblokir
    if is_user_blocked(chat_id):
        return

    # Perbarui profil
    simpan_update_user_profile(chat_id, username=user.username, first_name=user.first_name)

    state = context.user_data.get("admin_state")
    teks_bersih = " ".join(teks.split())

    # Tombol navigasi reply keyboard yang harus selalu diutamakan daripada input state form
    TOMBOL_NAVIGASI_UTAMA = {
        "⚙️ Admin Panel Toko", "« Admin Panel", "Admin Panel",
        "« Kelola Produk", "Kelola Produk",
        "« Menu Utama", "Menu Utama", "🔙 Menu Utama", "🏠 Menu Utama",
        "❌ Batalkan", "Batalkan", "Batal", "« Kembali", "🔙 Kembali", "Kembali",
        "🛒 Daftar Produk", "🛍️ Lihat Produk", "Daftar Produk", "Lihat Produk",
        "💰 Cek Saldo", "🩵 Cek Saldo", "Cek Saldo", "🩵 Saldo", "Saldo",
        "💳 Isi Saldo", "Isi Saldo",
        "« Daftar Kategori", "Daftar Kategori",
        "📋 Lihat Stok", "Lihat Stok", "📋 Lihat Stok Produk",
        "➕ Tambah Produk", "Tambah Produk", "➕ Tambah Produk Baru",
        "👥 Kelola Pengguna", "Kelola Pengguna",
        "📨 Pesanan", "Pesanan",
        "🗣️ Support", "Support",
    }

    # Jika user/admin menekan tombol navigasi saat sedang dalam input wizard/state,
    # batalkan state tersebut agar teks tombol tidak tersimpan sebagai nama kategori/produk
    if state and (teks_bersih in TOMBOL_NAVIGASI_UTAMA or teks.startswith("/")):
        context.user_data.pop("admin_state", None)
        state = None

    # Jika BUKAN sedang dalam input wizard/state admin, proses reply keyboard & nomor tombol
    if not (state and chat_id in ADMIN_IDS):
        # Penanganan pembatalan lewat teks/tombol
        if teks_bersih in ["❌ Batalkan", "Batalkan", "Batal"]:
            context.user_data.clear()
            await update.message.reply_text(
                "❌ Proses dibatalkan.\nKetik /admin untuk panel admin atau /mulai untuk menu utama.",
                parse_mode=ParseMode.HTML
            )
            return

        # ==========================================================
        # 1. TOMBOL AKSI DARI REPLY KEYBOARD (Katalog & Pelanggan)
        # ==========================================================
        if teks_bersih in ["🛒 Daftar Produk", "🛍️ Lihat Produk", "Daftar Produk", "Lihat Produk"]:
            context.user_data["menu_aktif"] = "katalog"
            context.user_data["katalog_filter"] = None
            context.user_data["katalog_page"] = 1
            semua_produk = get_semua_produk()
            pesan, markup = buat_tampilan_katalog(page=1)
            await update.message.reply_text(
                text=pesan,
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
            await update.message.reply_text(
                text="👇 <b>Keyboard Nomor Produk:</b>\nTekan tombol nomor di bawah untuk melihat rincian produk:",
                reply_markup=buat_reply_keyboard_katalog(semua_produk, page=1),
                parse_mode=ParseMode.HTML
            )
            return

        if teks_bersih in ["💰 Cek Saldo", "🩵 Cek Saldo", "Cek Saldo", "🩵 Saldo", "Saldo"]:
            await update.message.reply_text(
                "🩵 <b>Informasi Saldo</b>\n"
                "────────────────────────\n"
                "Saldo Anda saat ini: <b>Rp 0</b>\n\n"
                "<i>Untuk melakukan pengisian saldo (top up), silakan tekan tombol '💳 Isi Saldo' atau hubungi customer service kami.</i>",
                parse_mode=ParseMode.HTML
            )
            return

        if teks_bersih in ["💳 Isi Saldo", "Isi Saldo"]:
            await update.message.reply_text(
                "💳 <b>Pengisian Saldo (Top Up)</b>\n"
                "────────────────────────\n"
                "Layanan pengisian saldo otomatis & manual via QRIS/Transfer Bank.\n"
                "Silakan hubungi customer service / Administrator kami untuk panduan top up saldo.",
                parse_mode=ParseMode.HTML
            )
            return

        if teks_bersih in ["« Daftar Kategori", "Daftar Kategori"]:
            context.user_data["menu_aktif"] = "kategori_pelanggan"
            context.user_data["kategori_page"] = 1
            pesan, reply_kb = buat_tampilan_daftar_kategori_pelanggan(page=1)
            inline_kb = buat_inline_keyboard_kategori_pelanggan(page=1)
            await update.message.reply_text(
                text=pesan,
                reply_markup=inline_kb,
                parse_mode=ParseMode.HTML
            )
            await update.message.reply_text(
                text="👇 <b>Keyboard Nomor Kategori:</b>\nTekan tombol nomor kategori di bawah untuk melihat produknya:",
                reply_markup=reply_kb,
                parse_mode=ParseMode.HTML
            )
            return

        if teks_bersih in ["« Menu Utama", "Menu Utama", "🔙 Menu Utama"]:
            context.user_data.clear()
            pesan, markup = buat_tampilan_utama(user)
            gambar = ambil_gambar_gate()
            if gambar:
                with open(gambar, "rb") as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=pesan,
                        reply_markup=markup,
                        parse_mode=ParseMode.HTML
                    )
            else:
                await update.message.reply_text(
                    text=pesan,
                    reply_markup=markup,
                    parse_mode=ParseMode.HTML
                )
            await update.message.reply_text(
                text="🏠 Menu utama siap digunakan:",
                reply_markup=buat_reply_keyboard_utama(user)
            )
            return

        # PAGINATION NAVIGASI MELALUI REPLY KEYBOARD
        if teks_bersih in ["Halaman Selanjutnya ➡️", "Selanjutnya ➡️", "⬅️ Halaman Sebelumnya", "⬅️ Sebelumnya"]:
            is_next = "Selanjutnya" in teks_bersih
            menu_aktif = context.user_data.get("menu_aktif", "katalog")

            if menu_aktif == "admin_stok" and chat_id in ADMIN_IDS:
                curr = context.user_data.get("stok_page", 1)
                semua = get_semua_produk()
                total_pages, _, _, _ = hitung_pagination(len(semua), curr, per_page=10)
                page = min(curr + 1, total_pages) if is_next else max(1, curr - 1)
                context.user_data["stok_page"] = page
                pesan, markup = buat_tampilan_daftar_stok(page=page)
                await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                await update.message.reply_text(
                    text=f"📄 Halaman {page} dari {total_pages}:",
                    reply_markup=buat_reply_keyboard_stok_admin(semua, page=page)
                )
                return

            if menu_aktif == "admin_users" and chat_id in ADMIN_IDS:
                curr = context.user_data.get("users_page", 1)
                semua = get_semua_users_data()
                total_pages, _, _, _ = hitung_pagination(len(semua), curr, per_page=10)
                page = min(curr + 1, total_pages) if is_next else max(1, curr - 1)
                context.user_data["users_page"] = page
                pesan, markup = buat_tampilan_daftar_users(semua, page=page)
                await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                await update.message.reply_text(
                    text=f"📄 Halaman {page} dari {total_pages}:",
                    reply_markup=buat_reply_keyboard_users_admin(semua, page=page)
                )
                return

            if menu_aktif == "kategori_pelanggan":
                curr = context.user_data.get("kategori_page", 1)
                kat_list = get_semua_kategori()
                total_pages, _, _, _ = hitung_pagination(len(kat_list), curr, per_page=10)
                page = min(curr + 1, total_pages) if is_next else max(1, curr - 1)
                context.user_data["kategori_page"] = page
                pesan, reply_kb = buat_tampilan_daftar_kategori_pelanggan(page=page)
                inline_kb = buat_inline_keyboard_kategori_pelanggan(page=page)
                await update.message.reply_text(text=pesan, reply_markup=inline_kb, parse_mode=ParseMode.HTML)
                await update.message.reply_text(
                    text=f"📄 Halaman {page} dari {total_pages}:",
                    reply_markup=reply_kb
                )
                return

            # Default: Katalog Pelanggan
            curr = context.user_data.get("katalog_page", 1)
            kat_filter = context.user_data.get("katalog_filter")
            semua = get_semua_produk()
            if kat_filter:
                daftar = [p for p in semua if p.get("kategori", "Umum").lower() == kat_filter.lower()]
            else:
                daftar = semua
            total_pages, _, _, _ = hitung_pagination(len(daftar), curr, per_page=10)
            page = min(curr + 1, total_pages) if is_next else max(1, curr - 1)
            context.user_data["katalog_page"] = page
            pesan, markup = buat_tampilan_katalog(kategori_filter=kat_filter, page=page)
            await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
            await update.message.reply_text(
                text=f"📄 Halaman {page} dari {total_pages}:",
                reply_markup=buat_reply_keyboard_katalog(daftar, page=page)
            )
            return

        if teks_bersih in ["📨 Pesanan", "Pesanan", "Riwayat Pesanan", "📨 Riwayat Pesanan"]:
            pesan, markup = buat_tampilan_riwayat_pesanan(chat_id, page=1)
            await update.message.reply_text(
                text=pesan,
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
            return

        if teks_bersih in ["🗣️ Support", "Support"]:
            pesan, markup = buat_tampilan_support()
            await update.message.reply_text(
                text=pesan,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            return

        # ==========================================================
        # 2. TOMBOL AKSI REPLY KEYBOARD KHUSUS ADMINISTRATOR
        # ==========================================================
        if chat_id in ADMIN_IDS:
            if teks_bersih in ["📋 Lihat Stok", "Lihat Stok", "📋 Lihat Stok Produk"]:
                context.user_data.clear()
                context.user_data["menu_aktif"] = "admin_stok"
                context.user_data["stok_page"] = 1
                semua_produk = get_semua_produk()
                pesan, markup = buat_tampilan_daftar_stok(page=1)
                await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                await update.message.reply_text(
                    text="👇 <b>Keyboard Nomor Produk (Admin):</b>\nTekan tombol nomor di bawah untuk melihat rincian detail & stok:",
                    reply_markup=buat_reply_keyboard_stok_admin(semua_produk, page=1),
                    parse_mode=ParseMode.HTML
                )
                return

            if teks_bersih in ["➕ Tambah Produk", "Tambah Produk", "➕ Tambah Produk Baru"]:
                context.user_data.clear()
                context.user_data["admin_state"] = "tambah_step_nama"
                pesan_nama = buat_pesan_wizard_step1()
                await update.message.reply_text(
                    text=pesan_nama,
                    reply_markup=buat_keyboard_wizard_step1(),
                    parse_mode=ParseMode.HTML
                )
                return

            if teks_bersih in ["👥 Kelola Pengguna", "Kelola Pengguna"] or (teks_bersih == "🔄 Segarkan" and context.user_data.get("menu_aktif") == "admin_users"):
                context.user_data.clear()
                context.user_data["menu_aktif"] = "admin_users"
                context.user_data["users_page"] = 1
                semua_users = get_semua_users_data()
                pesan, markup = buat_tampilan_daftar_users(semua_users, page=1)
                await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                await update.message.reply_text(
                    text="👇 <b>Keyboard Nomor Pengguna (Admin):</b>\nTekan nomor pengguna di bawah untuk melihat detail profil & kelola akses:",
                    reply_markup=buat_reply_keyboard_users_admin(semua_users, page=1),
                    parse_mode=ParseMode.HTML
                )
                return

            if teks_bersih == "🔄 Segarkan" and context.user_data.get("menu_aktif") == "admin_stok":
                page = context.user_data.get("stok_page", 1)
                semua_produk = get_semua_produk()
                pesan, markup = buat_tampilan_daftar_stok(page=page)
                await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                await update.message.reply_text(
                    text="🔄 Daftar stok diperbarui.",
                    reply_markup=buat_reply_keyboard_stok_admin(semua_produk, page=page)
                )
                return

            if teks_bersih in ["« Kelola Produk", "Kelola Produk"]:
                context.user_data.clear()
                pesan, markup = buat_tampilan_kelola_produk_menu()
                await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                return

            if teks_bersih in ["« Admin Panel", "Admin Panel", "⚙️ Admin Panel Toko"]:
                context.user_data.clear()
                pesan, markup = buat_tampilan_admin_panel()
                await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                return

        # ==========================================================
        # 3. PEMILIHAN DENGAN NOMOR DARI KEYPAD (teks.isdigit())
        # ==========================================================
        if teks.isdigit():
            idx = int(teks)
            menu_aktif = context.user_data.get("menu_aktif")

            # 3A. ADMIN SEDANG LIHAT DAFTAR STOK PRODUK
            if menu_aktif == "admin_stok" and chat_id in ADMIN_IDS:
                semua_p = get_semua_produk()
                if 1 <= idx <= len(semua_p):
                    target_prod = semua_p[idx - 1]
                    pesan, markup = buat_tampilan_admin_detail_produk(target_prod, nomor=idx)
                    await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                    return
                else:
                    await update.message.reply_text(
                        f"⚠️ Nomor produk <b>{idx}</b> tidak ditemukan.\n"
                        f"Silakan pilih nomor antara <b>1 - {len(semua_p)}</b>.",
                        parse_mode=ParseMode.HTML
                    )
                    return

            # 3B. ADMIN SEDANG LIHAT DAFTAR PENGGUNA TERDAFTAR
            if menu_aktif == "admin_users" and chat_id in ADMIN_IDS:
                semua_u = get_semua_users_data()
                if 1 <= idx <= len(semua_u):
                    target_u = semua_u[idx - 1]
                    u_prof = get_user_profile(target_u["id"])
                    pesan, markup = buat_tampilan_detail_user(u_prof, nomor=idx)
                    await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                    return
                else:
                    await update.message.reply_text(
                        f"⚠️ Nomor pengguna <b>{idx}</b> tidak ditemukan.\n"
                        f"Silakan pilih nomor antara <b>1 - {len(semua_u)}</b>.",
                        parse_mode=ParseMode.HTML
                    )
                    return

            # 3C. PELANGGAN SEDANG LIHAT DAFTAR KATEGORI
            if menu_aktif == "kategori_pelanggan":
                kat_list = get_semua_kategori()
                if 1 <= idx <= len(kat_list):
                    kat_dipilih = kat_list[idx - 1]
                    context.user_data["menu_aktif"] = "katalog"
                    context.user_data["katalog_filter"] = kat_dipilih
                    semua_p = [p for p in get_semua_produk() if p.get("kategori") == kat_dipilih]
                    pesan, markup = buat_tampilan_katalog(kategori_filter=kat_dipilih)
                    await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                    await update.message.reply_text(
                        text=f"👇 Pilih nomor produk pada kategori <b>{html.escape(kat_dipilih)}</b>:",
                        reply_markup=buat_reply_keyboard_katalog(semua_p),
                        parse_mode=ParseMode.HTML
                    )
                    return
                else:
                    await update.message.reply_text(
                        f"⚠️ Nomor kategori <b>{idx}</b> tidak ditemukan.\n"
                        f"Silakan pilih nomor antara <b>1 - {len(kat_list)}</b>.",
                        parse_mode=ParseMode.HTML
                    )
                    return

            # 3D. PELANGGAN SEDANG LIHAT DAFTAR KATALOG PRODUK (DEFAULT)
            kat_filter = context.user_data.get("katalog_filter")
            semua_p = get_semua_produk()
            if kat_filter:
                daftar_tampil = [p for p in semua_p if p.get("kategori") == kat_filter]
            else:
                daftar_tampil = semua_p

            if 1 <= idx <= len(daftar_tampil):
                target_prod = daftar_tampil[idx - 1]
                pesan, markup = buat_tampilan_detail_produk(target_prod)
                await update.message.reply_text(text=pesan, reply_markup=markup, parse_mode=ParseMode.HTML)
                return
            elif daftar_tampil:
                await update.message.reply_text(
                    f"⚠️ Nomor produk <b>{idx}</b> tidak ditemukan.\n"
                    f"Silakan pilih nomor antara <b>1 - {len(daftar_tampil)}</b>.",
                    parse_mode=ParseMode.HTML
                )
                return

        # Jika bukan tombol yang dikenali dan bukan digit
        await update.message.reply_text(
            "👋 Silakan gunakan tombol menu di bawah ini untuk berinteraksi dengan bot:",
            reply_markup=buat_reply_keyboard_utama(user)
        )
        return

    # Proteksi: Pastikan sedang dalam state admin aktif
    if not state or chat_id not in ADMIN_IDS:
        return

    # 1. STATE INPUT STOK
    if state.startswith("set_stok_"):
        pid = int(state.split("_")[2])
        if not teks.isdigit():
            await update.message.reply_text("❌ Mohon masukkan angka stok yang valid (contoh: 10).")
            return

        jumlah = int(teks)
        update_stok(pid, jumlah)
        context.user_data.clear()
        produk = get_produk_by_id(pid)
        markup_nav = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Lihat Detail Produk", callback_data=f"admin_stok_detail_{pid}")],
            [InlineKeyboardButton("📋 Lihat Stok Produk", callback_data="admin_lihat_stok")]
        ])
        await update.message.reply_text(
            f"✅ Stok <b>{produk['nama']}</b> berhasil diubah menjadi <b>{jumlah} item</b>!\n\n"
            f"Pilih menu di bawah atau ketik /admin:",
            reply_markup=markup_nav,
            parse_mode=ParseMode.HTML
        )
        return

    # 1b. STATE EDIT NAMA PRODUK
    if state.startswith("edit_nama_"):
        pid = int(state.split("_")[2])
        update_nama_produk(pid, teks)
        context.user_data.clear()
        produk = get_produk_by_id(pid)
        markup_nav = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Lihat Detail Produk", callback_data=f"admin_stok_detail_{pid}")],
            [InlineKeyboardButton("📋 Lihat Stok Produk", callback_data="admin_lihat_stok")]
        ])
        await update.message.reply_text(
            f"✅ Nama produk berhasil diubah menjadi:\n<b>{produk['nama']}</b>\n\n"
            f"Pilih menu di bawah atau ketik /admin:",
            reply_markup=markup_nav,
            parse_mode=ParseMode.HTML
        )
        return

    # 1c. STATE EDIT HARGA PRODUK
    if state.startswith("edit_harga_"):
        pid = int(state.split("_")[2])
        clean_harga = teks.lower().replace("rp", "").replace(".", "").replace(",", "").strip()
        if not clean_harga.isdigit() or int(clean_harga) <= 0:
            await update.message.reply_text("❌ Mohon masukkan angka harga yang valid (contoh: <code>45000</code>).", parse_mode=ParseMode.HTML)
            return

        harga_baru = int(clean_harga)
        update_harga_produk(pid, harga_baru)
        context.user_data.clear()
        produk = get_produk_by_id(pid)
        p_nama = html.escape(produk['nama']) if produk else "Produk"
        markup_nav = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Lihat Detail Produk", callback_data=f"admin_stok_detail_{pid}")],
            [InlineKeyboardButton("📋 Lihat Stok Produk", callback_data="admin_lihat_stok")]
        ])
        await update.message.reply_text(
            f"✅ Harga <b>{p_nama}</b> berhasil diubah menjadi <b>Rp {harga_baru:,}</b>!\n\n"
            f"Pilih menu di bawah atau ketik /admin:",
            reply_markup=markup_nav,
            parse_mode=ParseMode.HTML
        )
        return

    # 1d. STATE EDIT DESKRIPSI PRODUK
    if state.startswith("edit_deskripsi_"):
        pid = int(state.split("_")[2])
        update_deskripsi_produk(pid, teks)
        context.user_data.clear()
        produk = get_produk_by_id(pid)
        p_nama = html.escape(produk['nama']) if produk else "Produk"
        p_desk = html.escape(produk.get('deskripsi', '-')) if produk else "-"
        markup_nav = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Lihat Detail Produk", callback_data=f"admin_stok_detail_{pid}")],
            [InlineKeyboardButton("📋 Lihat Stok Produk", callback_data="admin_lihat_stok")]
        ])
        await update.message.reply_text(
            f"✅ Deskripsi <b>{p_nama}</b> berhasil diperbarui:\n\n"
            f"<blockquote>{p_desk}</blockquote>\n\n"
            f"Pilih menu di bawah atau ketik /admin:",
            reply_markup=markup_nav,
            parse_mode=ParseMode.HTML
        )
        return

    # 2. STATE INPUT PROMO
    if state.startswith("set_promo_"):
        pid = int(state.split("_")[2])
        clean_promo = teks.lower().replace("rp", "").replace(".", "").replace(",", "").strip()
        if not clean_promo.isdigit() or int(clean_promo) < 0:
            await update.message.reply_text("❌ Mohon masukkan nominal angka harga promo (contoh: <code>25000</code>).", parse_mode=ParseMode.HTML)
            return

        harga_promo = int(clean_promo)
        update_promo(pid, harga_promo)
        context.user_data.clear()
        produk = get_produk_by_id(pid)
        p_nama = html.escape(produk['nama']) if produk else "Produk"
        await update.message.reply_text(
            f"🔥 Promo <b>{p_nama}</b> berhasil diatur menjadi <b>Rp {harga_promo:,}</b>!\n\n"
            f"Ketik /admin untuk kembali ke Admin Panel.",
            parse_mode=ParseMode.HTML
        )
        return

    # 2b. STATE INPUT KATEGORI BARU (DARI PANEL ADMIN)
    if state == "kategori_tambah":
        nama_kat = teks.strip()
        if not nama_kat:
            await update.message.reply_text("❌ Nama kategori tidak boleh kosong.")
            return

        sukses = tambah_kategori(nama_kat)
        context.user_data.clear()
        if sukses:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗂️ Menu Kategori", callback_data="admin_menu_kategori")],
                [InlineKeyboardButton("⚙️ Panel Admin", callback_data="admin_panel")]
            ])
            kat_safe = html.escape(nama_kat)
            await update.message.reply_text(
                f"✅ Kategori <b>{kat_safe}</b> berhasil ditambahkan!\n\n"
                f"Ketik /admin untuk kembali ke panel admin.",
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
        else:
            kat_safe = html.escape(nama_kat)
            await update.message.reply_text(
                f"⚠️ Kategori <b>{kat_safe}</b> sudah ada atau tidak valid.\n"
                f"Silakan ketik nama kategori lain, atau ketik /batal untuk membatalkan.",
                parse_mode=ParseMode.HTML
            )
        return

    # 3a. WIZARD STEP 1 (1/5) -> NAMA PRODUK DIINPUT
    if state == "tambah_step_nama":
        context.user_data["new_prod_nama"] = teks
        context.user_data["admin_state"] = "tambah_step_kategori"
        curr_kat = context.user_data.get("new_prod_kategori")
        pesan_tanya_kat = buat_pesan_wizard_step2(teks, curr_kat)
        await update.message.reply_text(
            text=pesan_tanya_kat,
            reply_markup=buat_keyboard_wizard_step2(curr_kat),
            parse_mode=ParseMode.HTML
        )
        return

    # 3b. WIZARD STEP 2 (2/5) -> PILIH NO KATEGORI / LAINNYA
    if state == "tambah_step_kategori":
        kategori_list = get_semua_kategori()
        nama = context.user_data.get("new_prod_nama", "Produk")

        # Admin memilih dengan mengetik nomor (1..N atau nomor di luar kategori)
        if teks.isdigit():
            pilihan_no = int(teks)
            if 1 <= pilihan_no <= len(kategori_list):
                kat_dipilih = kategori_list[pilihan_no - 1]
                context.user_data["new_prod_kategori"] = kat_dipilih
                context.user_data["admin_state"] = "tambah_step_harga"

                curr_harga = context.user_data.get("new_prod_harga")
                pesan_harga = buat_pesan_wizard_step3(nama, kat_dipilih, curr_harga)
                await update.message.reply_text(
                    text=f"✅ Kategori dipilih: <b>{html.escape(kat_dipilih)}</b>\n\n{pesan_harga}",
                    reply_markup=buat_keyboard_wizard_step3(curr_harga),
                    parse_mode=ParseMode.HTML
                )
                return
            else:
                # Nomor di luar kategori yang tersedia -> Catatan Lainnya
                context.user_data["admin_state"] = "tambah_step_kategori_custom"
                markup_batal = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("⬅️ Kembali", callback_data="wizard_ke_step2"),
                        InlineKeyboardButton("❌ Batalkan", callback_data="batal_tambah_produk")
                    ]
                ])
                await update.message.reply_text(
                    f"✍️ <b>KATEGORI BARU (LAINNYA)</b>\n"
                    f"────────────────────────\n"
                    f"Produk: <b>{html.escape(nama)}</b>\n\n"
                    f"Silakan ketik nama kategori baru di chat:",
                    reply_markup=markup_batal,
                    parse_mode=ParseMode.HTML
                )
                return
        else:
            # Jika admin langsung mengetik teks nama kategori (bukan nomor)
            tambah_kategori(teks)
            context.user_data["new_prod_kategori"] = teks
            context.user_data["admin_state"] = "tambah_step_harga"

            curr_harga = context.user_data.get("new_prod_harga")
            pesan_harga = buat_pesan_wizard_step3(nama, teks, curr_harga)
            await update.message.reply_text(
                text=f"✅ Kategori baru <b>{html.escape(teks)}</b> disimpan!\n\n{pesan_harga}",
                reply_markup=buat_keyboard_wizard_step3(curr_harga),
                parse_mode=ParseMode.HTML
            )
            return

    # 3c. WIZARD STEP 2b -> INPUT TEKS KATEGORI BARU (CATATAN LAINNYA)
    if state == "tambah_step_kategori_custom":
        nama_kat = teks.strip()
        if not nama_kat:
            await update.message.reply_text("❌ Nama kategori tidak boleh kosong.")
            return

        tambah_kategori(nama_kat)
        context.user_data["new_prod_kategori"] = nama_kat
        context.user_data["admin_state"] = "tambah_step_harga"

        nama = context.user_data.get("new_prod_nama", "Produk")
        curr_harga = context.user_data.get("new_prod_harga")
        pesan_harga = buat_pesan_wizard_step3(nama, nama_kat, curr_harga)
        await update.message.reply_text(
            text=f"✅ Kategori baru <b>{html.escape(nama_kat)}</b> berhasil ditambahkan!\n\n{pesan_harga}",
            reply_markup=buat_keyboard_wizard_step3(curr_harga),
            parse_mode=ParseMode.HTML
        )
        return

    # 3d. WIZARD STEP 3 (3/5) -> HARGA PRODUK DIINPUT
    if state == "tambah_step_harga":
        clean_harga = teks.lower().replace("rp", "").replace(".", "").replace(",", "").strip()
        if not clean_harga.isdigit() or int(clean_harga) <= 0:
            await update.message.reply_text(
                "❌ Harga tidak valid! Harap masukkan nominal angka saja (contoh: <code>45000</code>).",
                parse_mode=ParseMode.HTML
            )
            return

        harga = int(clean_harga)
        context.user_data["new_prod_harga"] = harga
        context.user_data["admin_state"] = "tambah_step_stok"
        nama = context.user_data.get("new_prod_nama", "Produk")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        curr_stok = context.user_data.get("new_prod_stok")
        pesan_tanya_stok = buat_pesan_wizard_step4(nama, kat, harga, curr_stok)
        await update.message.reply_text(
            text=pesan_tanya_stok,
            reply_markup=buat_keyboard_wizard_step4(curr_stok),
            parse_mode=ParseMode.HTML
        )
        return

    # 3e. WIZARD STEP 4 (4/5) -> STOK / ISIAN AKUN DIINPUT (Model 1)
    if state == "tambah_step_stok":
        lines = [line.strip() for line in teks.splitlines() if line.strip()]
        if not lines:
            await update.message.reply_text(
                "❌ Format tidak valid! Harap kirimkan daftar akun (1 baris = 1 akun) atau ketik <code>0</code> jika tanpa stok awal.",
                parse_mode=ParseMode.HTML
            )
            return

        if len(lines) == 1 and lines[0].isdigit():
            jumlah_stok = int(lines[0])
            prod_name = context.user_data.get('new_prod_nama', 'Produk')
            items = [f"Akun #{i+1} ({prod_name})" for i in range(jumlah_stok)]
        else:
            items = lines
            jumlah_stok = len(items)

        context.user_data["new_prod_items"] = items
        context.user_data["new_prod_stok"] = jumlah_stok
        context.user_data["admin_state"] = "tambah_step_deskripsi"
        nama = context.user_data.get("new_prod_nama", "Produk")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        harga = context.user_data.get("new_prod_harga", 0)
        curr_desk = context.user_data.get("new_prod_deskripsi")
        pesan_tanya_deskripsi = buat_pesan_wizard_step5(nama, kat, harga, jumlah_stok, curr_desk)
        await update.message.reply_text(
            text=f"✅ <b>{jumlah_stok} akun berhasil dimuat!</b>\n\n{pesan_tanya_deskripsi}",
            reply_markup=buat_keyboard_wizard_step5(curr_desk),
            parse_mode=ParseMode.HTML
        )
        return

    # 3f. WIZARD STEP 5 (5/5) -> DESKRIPSI DIINPUT
    if state == "tambah_step_deskripsi":
        context.user_data["new_prod_deskripsi"] = teks
        context.user_data["admin_state"] = "tambah_konfirmasi"

        nama = context.user_data.get("new_prod_nama", "-")
        kat = context.user_data.get("new_prod_kategori", "Umum")
        harga = context.user_data.get("new_prod_harga", 0)
        stok = context.user_data.get("new_prod_stok", 0)

        pesan_preview = buat_pesan_wizard_preview(nama, kat, harga, stok, teks)
        await update.message.reply_text(
            text=pesan_preview,
            reply_markup=buat_keyboard_konfirmasi_tambah(),
            parse_mode=ParseMode.HTML
        )
        return

    # 3g. RESTOCK AKUN BULK OLEH ADMIN
    if state and state.startswith("restock_produk_"):
        pid = int(state.replace("restock_produk_", ""))
        produk = get_produk_by_id(pid)
        if not produk:
            await update.message.reply_text("❌ Produk tidak ditemukan.")
            context.user_data.clear()
            return

        lines = [line.strip() for line in teks.splitlines() if line.strip()]
        if not lines:
            await update.message.reply_text("❌ Mohon kirimkan minimal 1 baris akun baru.")
            return

        sukses, total_stok = tambah_stok_items(pid, lines)
        context.user_data.clear()
        produk_terbaru = get_produk_by_id(pid)
        pesan_sukses = (
            "✅ <b>RESTOCK BERHASIL!</b>\n"
            "────────────────────────\n"
            f"📦 <b>Produk:</b> {html.escape(produk_terbaru['nama'])}\n"
            f"➕ <b>Akun Ditambahkan:</b> <b>+{len(lines)} item</b>\n"
            f"📊 <b>Total Stok Sekarang:</b> <b>{total_stok} item</b>\n"
            "────────────────────────\n"
            "Data akun siap dikirimkan otomatis ke pembeli."
        )
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📋 Lihat Daftar Akun ({total_stok})", callback_data=f"admin_lihat_akun_{pid}")],
            [InlineKeyboardButton("📦 Kembali ke Detail Produk", callback_data=f"admin_stok_detail_{pid}")]
        ])
        await update.message.reply_text(text=pesan_sukses, reply_markup=markup, parse_mode=ParseMode.HTML)
        return

    # 4. STATE BROADCAST PESAN
    if state == "broadcast":
        context.user_data.clear()
        sukses = 0
        gagal = 0
        targets = get_semua_user_ids()
        total_target = len(targets)

        status_msg = await update.message.reply_text(f"⏳ Sedang mengirim broadcast ke {total_target} pengguna...")

        for uid in targets:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=teks,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                sukses += 1
            except Exception:
                try:
                    # Fallback plain text jika terdapat HTML syntax error
                    await context.bot.send_message(
                        chat_id=uid,
                        text=teks,
                        parse_mode=None,
                        disable_web_page_preview=True
                    )
                    sukses += 1
                except Exception:
                    gagal += 1
            await asyncio.sleep(0.04)  # Mencegah flood rate limit Telegram

        await status_msg.edit_text(
            f"📢 <b>Hasil Broadcast Selesai</b>\n"
            f"────────────────────────\n"
            f"✅ Berhasil terkirim: <b>{sukses}</b> user\n"
            f"❌ Gagal: <b>{gagal}</b> user\n"
            f"👥 Total Target: <b>{total_target}</b> user",
            parse_mode=ParseMode.HTML
        )
        return

