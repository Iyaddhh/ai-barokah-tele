import html
import urllib.parse
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_IDS, ADMIN_USERNAME
from database import (
    get_total_users,
    get_semua_produk,
    get_total_stok,
    get_semua_kategori,
    get_jumlah_produk_by_kategori,
    get_total_blocked_users,
    get_semua_users_data,
    get_riwayat_pesanan_user,
    get_order_aktif_user,
)
from helpers import get_greeting

def buat_keyboard_gate():
    """Membuat tombol akses tautan kedua channel dan verifikasi"""
    keyboard = [
        [InlineKeyboardButton("📢 1. Gabung Store AI Barokah", url="https://t.me/aibarokahstore")],
        [InlineKeyboardButton("🔔 2. Gabung Channel Notifikasi", url="https://t.me/notifikasiAiBarokah")],
        [InlineKeyboardButton("✅ Sudah Join Keduanya", callback_data="verifikasi_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

def buat_tampilan_utama(user):
    """Membuat pesan format profil dan tombol menu utama toko"""
    greeting = get_greeting()
    nama = html.escape(user.first_name or "Pelanggan")
    chat_id = user.id
    username = f"@{user.username}" if user.username else "Tidak ada"

    total_transaksi_idr = 0
    total_transaksi_usdt = 0
    saldo = 0
    total_pengguna = get_total_users()
    total_pesanan = 3091

    pesan = (
        f"🌅 <b>Selamat {greeting}, {nama} — selamat datang di AI BAROKAH STORE</b>\n"
        f"────────────────────────\n"
        f"🥷 <b>Profil Saya</b>\n"
        f"<blockquote>"
        f"↗️ <b>ID Telegram:</b> <code>{chat_id}</code>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"💵 <b>Total Transaksi:</b> Rp {total_transaksi_idr:,} / {total_transaksi_usdt} USDT\n"
        f"🩵 <b>Saldo Saya:</b> Rp {saldo:,}"
        f"</blockquote>\n\n"
        f"📊 <b>Aktivitas Toko</b>\n"
        f"<blockquote>"
        f"🥷 <b>Pengguna Telegram:</b> {total_pengguna}\n"
        f"🧾 <b>Pesanan berhasil:</b> {total_pesanan}"
        f"</blockquote>\n\n"
        f"🔹 <b>Promo, update stok, dan bukti transaksi terbaru tersedia di channel resmi kami.</b>\n\n"
        f"Mau ngapain dulu? Pilih tombol di bawah ya."
    )

    keyboard = [
        [InlineKeyboardButton("🛍️ Lihat Produk", callback_data="menu_produk")],
        [
            InlineKeyboardButton("🩵 Saldo", callback_data="menu_saldo"),
            InlineKeyboardButton("📨 Pesanan", callback_data="menu_pesanan"),
        ],
        [InlineKeyboardButton("🗣️ Support", callback_data="menu_support")],
    ]

    # Jika yang membuka adalah Administrator, munculkan tombol Admin Panel
    if chat_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel Toko", callback_data="admin_panel")])

    return pesan, InlineKeyboardMarkup(keyboard)

def buat_tampilan_support():
    """Tampilan informasi bantuan & kontak customer support admin"""
    uname_clean = ADMIN_USERNAME.replace("@", "")
    pesan = (
        "🗣️ <b>PUSAT BANTUAN & CUSTOMER SERVICE</b>\n"
        "────────────────────────\n"
        "Membutuhkan bantuan terkait pemesanan, top up saldo, kendala transaksi, atau informasi produk?\n\n"
        f"Silakan hubungi Administrator kami langsung:\n"
        f"• 👤 <b>Username Telegram:</b> {ADMIN_USERNAME}\n"
        f"• 🔗 <b>Tautan Chat:</b> https://t.me/{uname_clean}\n\n"
        "<i>Silakan tekan tombol di bawah untuk langsung membuka percakapan dengan Admin.</i>"
    )
    keyboard = [
        [InlineKeyboardButton(f"💬 Hubungi Admin ({ADMIN_USERNAME})", url=f"https://t.me/{uname_clean}")],
        [InlineKeyboardButton("🔙 Menu Utama", callback_data="kembali_ke_menu")]
    ]
    return pesan, InlineKeyboardMarkup(keyboard)

# ==================== TAMPILAN KATALOG PRODUK (PELANGGAN) ====================

# ==================== SISTEM PAGINATION (MAKSIMAL 10 ITEM / HALAMAN) ====================

ITEMS_PER_PAGE = 10

def hitung_pagination(total_items: int, current_page: int = 1, per_page: int = 10):
    """Menghitung total halaman, index awal dan akhir, serta memastikan current_page valid"""
    if total_items <= 0:
        return 1, 1, 0, 0
    total_pages = (total_items + per_page - 1) // per_page
    page = max(1, min(current_page, total_pages))
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    return total_pages, page, start_idx, end_idx

def buat_baris_inline_pagination(total_pages: int, current_page: int, prefix_callback: str):
    """Membuat baris tombol inline pagination: [⬅️ Hal X] [ Hal X/Y ] [Hal Z ➡️]"""
    if total_pages <= 1:
        return []
    baris = []
    if current_page > 1:
        baris.append(InlineKeyboardButton("⬅️ Sebelumnya", callback_data=f"{prefix_callback}_{current_page - 1}"))
    baris.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="noop"))
    if current_page < total_pages:
        baris.append(InlineKeyboardButton("Selanjutnya ➡️", callback_data=f"{prefix_callback}_{current_page + 1}"))
    return [baris]

def buat_baris_reply_pagination(total_pages: int, current_page: int):
    """Membuat baris tombol reply keyboard pagination untuk bawah layar"""
    if total_pages <= 1:
        return []
    baris = []
    if current_page > 1:
        baris.append(KeyboardButton("⬅️ Halaman Sebelumnya"))
    if current_page < total_pages:
        baris.append(KeyboardButton("Halaman Selanjutnya ➡️"))
    return [baris] if baris else []

# ==================== TAMPILAN KATALOG PRODUK (PELANGGAN) ====================

def buat_tampilan_katalog(kategori_filter=None, page=1):
    """Teks dan keyboard daftar katalog produk untuk pelanggan dengan pagination (10 item/hal)"""
    semua_produk = get_semua_produk()
    if kategori_filter:
        semua_produk = [p for p in semua_produk if p.get("kategori", "Umum").lower() == kategori_filter.lower()]
        judul_kat = f" — Kategori: {html.escape(kategori_filter)}"
    else:
        judul_kat = ""

    total_pages, page, start_idx, end_idx = hitung_pagination(len(semua_produk), page, per_page=ITEMS_PER_PAGE)
    produk_halaman = semua_produk[start_idx:end_idx]

    pesan = (
        f"🛍️ <b>KATALOG PRODUK AI BAROKAH STORE{judul_kat}</b>\n"
        "────────────────────────\n"
    )

    if not semua_produk:
        pesan += "<i>Belum ada produk yang tersedia pada katalog ini.</i>\n\n"
        pesan += "Gunakan tombol di bawah untuk kembali ke menu utama atau lihat kategori."
        keyboard = [[InlineKeyboardButton("🔙 Menu Utama", callback_data="kembali_ke_menu")]]
        return pesan, InlineKeyboardMarkup(keyboard)

    for idx, p in enumerate(produk_halaman, start=start_idx + 1):
        harga_final = p["harga_promo"] if (p.get("harga_promo", 0) > 0) else p["harga"]
        stok_label = f"Ready ({p.get('stok', 0)})" if p.get("stok", 0) > 0 else "Habis"
        promo_icon = "🔥 " if p.get("harga_promo", 0) > 0 else ""
        kat_label = f" [🏷️ {html.escape(p.get('kategori', 'Umum'))}]"
        p_nama = html.escape(p.get("nama", "Produk"))
        pesan += (
            f"<b>{idx}.</b> {promo_icon}<b>{p_nama}</b>{kat_label}\n"
            f"   • Harga: <b>Rp {harga_final:,}</b>\n"
            f"   • Status: <b>{stok_label}</b>\n\n"
        )

    pesan += "────────────────────────\n"
    if total_pages > 1:
        pesan += f"📄 <b>Halaman {page} dari {total_pages}</b> <i>(Total: {len(semua_produk)} produk)</i>\n"
    pesan += "💡 <i>Tekan nomor produk pada papan tombol (keyboard) di bawah untuk melihat detail & memesan!</i>"

    keyboard = []
    baris_inline = []
    for idx, p in enumerate(produk_halaman, start=start_idx + 1):
        baris_inline.append(InlineKeyboardButton(f"{idx}", callback_data=f"produk_detail_{p['id']}"))
        if len(baris_inline) == 5:
            keyboard.append(baris_inline)
            baris_inline = []
    if baris_inline:
        keyboard.append(baris_inline)

    if total_pages > 1:
        keyboard.extend(buat_baris_inline_pagination(total_pages, page, "katalog_hal"))

    keyboard.append([
        InlineKeyboardButton("🗂️ Pilih Kategori", callback_data="pelanggan_pilih_kategori"),
        InlineKeyboardButton("🔙 Menu Utama", callback_data="kembali_ke_menu")
    ])
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_reply_keyboard_katalog(semua_produk=None, page=1):
    """Reply Keyboard di bawah layar dengan nomor produk halaman aktif & navigasi pagination"""
    if semua_produk is None:
        semua_produk = get_semua_produk()

    keyboard = [
        [KeyboardButton("🛒 Daftar Produk"), KeyboardButton("💰 Cek Saldo")],
        [KeyboardButton("💳 Isi Saldo")],
    ]

    total_pages, page, start_idx, end_idx = hitung_pagination(len(semua_produk), page, per_page=ITEMS_PER_PAGE)
    produk_halaman = semua_produk[start_idx:end_idx]

    if produk_halaman:
        baris_angka = []
        for idx in range(start_idx + 1, end_idx + 1):
            baris_angka.append(KeyboardButton(str(idx)))
            if len(baris_angka) == 6:
                keyboard.append(baris_angka)
                baris_angka = []
        if baris_angka:
            keyboard.append(baris_angka)

    if total_pages > 1:
        keyboard.extend(buat_baris_reply_pagination(total_pages, page))

    keyboard.append([KeyboardButton("« Daftar Kategori")])
    keyboard.append([KeyboardButton("« Menu Utama")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=False, one_time_keyboard=True)

def buat_reply_keyboard_stok_admin(semua_produk=None, page=1):
    """Reply Keyboard di bawah layar untuk admin saat melihat daftar stok produk dengan pagination"""
    if semua_produk is None:
        semua_produk = get_semua_produk()

    keyboard = [
        [KeyboardButton("📋 Lihat Stok"), KeyboardButton("➕ Tambah Produk")],
    ]

    total_pages, page, start_idx, end_idx = hitung_pagination(len(semua_produk), page, per_page=ITEMS_PER_PAGE)
    produk_halaman = semua_produk[start_idx:end_idx]

    if produk_halaman:
        baris_angka = []
        for idx in range(start_idx + 1, end_idx + 1):
            baris_angka.append(KeyboardButton(str(idx)))
            if len(baris_angka) == 6:
                keyboard.append(baris_angka)
                baris_angka = []
        if baris_angka:
            keyboard.append(baris_angka)

    if total_pages > 1:
        keyboard.extend(buat_baris_reply_pagination(total_pages, page))

    keyboard.append([KeyboardButton("« Kelola Produk"), KeyboardButton("« Admin Panel")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=False, one_time_keyboard=True)

def buat_reply_keyboard_users_admin(semua_users=None, page=1):
    """Reply Keyboard di bawah layar untuk admin saat melihat daftar pengguna dengan pagination"""
    if semua_users is None:
        semua_users = get_semua_users_data()

    keyboard = [
        [KeyboardButton("👥 Kelola Pengguna"), KeyboardButton("🔄 Segarkan")],
    ]

    total_pages, page, start_idx, end_idx = hitung_pagination(len(semua_users), page, per_page=ITEMS_PER_PAGE)
    users_halaman = semua_users[start_idx:end_idx]

    if users_halaman:
        baris_angka = []
        for idx in range(start_idx + 1, end_idx + 1):
            baris_angka.append(KeyboardButton(str(idx)))
            if len(baris_angka) == 6:
                keyboard.append(baris_angka)
                baris_angka = []
        if baris_angka:
            keyboard.append(baris_angka)

    if total_pages > 1:
        keyboard.extend(buat_baris_reply_pagination(total_pages, page))

    keyboard.append([KeyboardButton("« Admin Panel")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=False, one_time_keyboard=True)

def buat_reply_keyboard_utama(user):
    """Reply Keyboard menu utama toko di bawah layar"""
    keyboard = [
        [KeyboardButton("🛍️ Lihat Produk"), KeyboardButton("🩵 Cek Saldo")],
        [KeyboardButton("📨 Pesanan"), KeyboardButton("🗣️ Support")]
    ]
    if user.id in ADMIN_IDS:
        keyboard.append([KeyboardButton("⚙️ Admin Panel Toko")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=False, one_time_keyboard=True)

def buat_tampilan_daftar_kategori_pelanggan(page=1):
    """Tampilan daftar kategori produk untuk pelanggan beserta reply keyboard dengan pagination"""
    kategori_list = get_semua_kategori()
    total_pages, page, start_idx, end_idx = hitung_pagination(len(kategori_list), page, per_page=ITEMS_PER_PAGE)
    kat_halaman = kategori_list[start_idx:end_idx]

    pesan = (
        "🗂️ <b>DAFTAR KATEGORI PRODUK</b>\n"
        "────────────────────────\n"
        "Pilih nomor kategori pada keyboard di bawah untuk melihat produknya:\n\n"
    )
    if not kategori_list:
        pesan += "<i>Belum ada kategori yang tersedia saat ini.</i>"
    else:
        for idx, kat in enumerate(kat_halaman, start=start_idx + 1):
            jml = get_jumlah_produk_by_kategori(kat)
            pesan += f"<b>{idx}.</b> {html.escape(kat)} <i>({jml} produk)</i>\n"

    pesan += "\n────────────────────────\n"
    if total_pages > 1:
        pesan += f"📄 <b>Halaman {page} dari {total_pages}</b> <i>(Total: {len(kategori_list)} kategori)</i>\n"
    pesan += "<i>Tekan nomor kategori di bawah atau pilih '🛒 Daftar Produk' untuk melihat semua:</i>"

    keyboard = [
        [KeyboardButton("🛒 Daftar Produk"), KeyboardButton("💰 Cek Saldo")],
    ]
    if kat_halaman:
        baris_angka = []
        for idx in range(start_idx + 1, end_idx + 1):
            baris_angka.append(KeyboardButton(str(idx)))
            if len(baris_angka) == 6:
                keyboard.append(baris_angka)
                baris_angka = []
        if baris_angka:
            keyboard.append(baris_angka)

    if total_pages > 1:
        keyboard.extend(buat_baris_reply_pagination(total_pages, page))

    keyboard.append([KeyboardButton("« Menu Utama")])
    return pesan, ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=False, one_time_keyboard=True)

def buat_inline_keyboard_kategori_pelanggan(kategori_list=None, page=1):
    """Inline keyboard pilihan nomor kategori untuk pelanggan dengan pagination jika > 10"""
    if kategori_list is None:
        kategori_list = get_semua_kategori()

    total_pages, page, start_idx, end_idx = hitung_pagination(len(kategori_list), page, per_page=ITEMS_PER_PAGE)
    kat_halaman = kategori_list[start_idx:end_idx]

    keyboard = []
    baris = []
    for idx in range(start_idx + 1, end_idx + 1):
        baris.append(InlineKeyboardButton(f"{idx}", callback_data=f"pelanggan_kat_pilih_{idx}"))
        if len(baris) == 5:
            keyboard.append(baris)
            baris = []
    if baris:
        keyboard.append(baris)

    if total_pages > 1:
        keyboard.extend(buat_baris_inline_pagination(total_pages, page, "pelanggan_kat_hal"))

    keyboard.append([
        InlineKeyboardButton("🛒 Semua Produk", callback_data="menu_produk"),
        InlineKeyboardButton("🔙 Menu Utama", callback_data="kembali_ke_menu")
    ])
    return InlineKeyboardMarkup(keyboard)

def buat_tampilan_detail_produk(produk, jumlah: int = 1):
    """Menampilkan detail spesifik dari satu produk dengan tombol kuantitas (- / +), kalkulasi preview, dan tombol beli"""
    stok = produk.get("stok", 0)
    nama_p = html.escape(produk.get("nama", "Produk"))
    desk_p = html.escape(produk.get("deskripsi", "-"))
    kategori_p = html.escape(produk.get("kategori", "Umum"))
    pid = produk.get("id", 0)

    # Validasi kuantitas belanja
    if stok > 0:
        jumlah = max(1, min(jumlah, stok))
        stok_teks = f"<b>{stok} item</b> (Tersedia ✅)"
    else:
        jumlah = 0
        stok_teks = "<b>❌ Stok Habis</b>"

    harga_normal = produk.get("harga", 0)
    harga_promo = produk.get("harga_promo", 0)
    harga_satuan = harga_promo if (harga_promo > 0) else harga_normal

    if harga_promo > 0:
        harga_teks = f"<s>Rp {harga_normal:,}</s> ➔ <b>Rp {harga_promo:,}</b> 🔥 (PROMO)"
    else:
        harga_teks = f"<b>Rp {harga_normal:,}</b>"

    pesan = (
        f"📦 <b>{nama_p}</b>\n"
        f"────────────────────────\n"
        f"🏷️ <b>Kategori:</b> {kategori_p}\n"
        f"💵 <b>Harga Satuan:</b> {harga_teks}\n"
        f"📊 <b>Ketersediaan:</b> {stok_teks}\n\n"
        f"📝 <b>Deskripsi:</b>\n"
        f"<blockquote>{desk_p}</blockquote>\n"
    )

    keyboard = []
    if stok > 0:
        total_harga = harga_satuan * jumlah
        pesan += (
            f"────────────────────────\n"
            f"🛍️ <b>Rincian Pesanan:</b>\n"
            f"• Jumlah: <b>{jumlah} item</b>\n"
            f"• Total Bayar: <b>Rp {harga_satuan:,} x {jumlah} = Rp {total_harga:,}</b>\n"
            f"────────────────────────\n"
            f"💡 <i>Gunakan tombol <b>[-]</b> dan <b>[+]</b> di bawah untuk mengatur jumlah barang:</i>"
        )

        # Baris 1: Tombol Minus, Jumlah Qty, Tombol Plus
        keyboard.append([
            InlineKeyboardButton("➖", callback_data=f"beli_kurang_{pid}_{jumlah}"),
            InlineKeyboardButton(f"📦 {jumlah} item", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data=f"beli_tambah_{pid}_{jumlah}"),
        ])

        # Baris 2: Tombol Beli Sekarang
        keyboard.append([
            InlineKeyboardButton(f"🛒 Beli Sekarang (Rp {total_harga:,})", callback_data=f"beli_qris_{pid}_{jumlah}")
        ])
    else:
        pesan += (
            f"────────────────────────\n"
            f"⚠️ <i>Maaf, stok produk ini sedang habis. Silakan pilih produk lainnya.</i>"
        )

    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Katalog", callback_data="menu_produk")])
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_tampilan_invoice_qris(order: dict):
    """Membuat teks rincian invoice dan inline keyboard untuk transaksi QRIS (timer 5 menit)"""
    order_id = order.get("order_id", "-")
    nama_p = order.get("nama_produk", "Produk")
    qty = order.get("jumlah", 1)
    total = order.get("total_bayar", 0)
    exp_str = order.get("expires_at", "-")
    status = order.get("status", "PENDING")

    status_badge = "⏳ MENUNGGU PEMBAYARAN"
    if status == "WAITING_ADMIN":
        status_badge = "🟡 MENUNGGU KONFIRMASI ADMIN"
    elif status == "PAID":
        status_badge = "✅ PEMBAYARAN SUDAH DITERIMA"
    elif status == "EXPIRED":
        status_badge = "❌ TRANSAKSI GAGAL (KEDALUWARSA)"
    elif status == "CANCELLED":
        status_badge = "🚫 DIBATALKAN"

    waktu_beli = order.get("paid_at") or order.get("waktu_beli")
    info_waktu = f"⏰ <b>Waktu Pembelian:</b> <code>{waktu_beli}</code>\n" if waktu_beli and status == "PAID" else ""

    pesan = (
        "🧾 <b>INVOICE PEMBAYARAN QRIS</b>\n"
        "────────────────────────\n"
        f"🆔 <b>No. Invoice:</b> <code>{order_id}</code>\n"
        f"📊 <b>Status:</b> <b>{status_badge}</b>\n"
        f"📦 <b>Produk:</b> {nama_p}\n"
        f"🔢 <b>Jumlah:</b> {qty} item\n"
        f"💰 <b>Total Tagihan:</b> <b>Rp {total:,}</b>\n"
        f"{info_waktu}"
        "────────────────────────\n"
        f"⏳ <b>Batas Waktu Bayar:</b> <b>5 Menit</b>\n"
        f"⏰ <b>Kedaluwarsa Pada:</b> <code>{exp_str}</code>\n"
        "────────────────────────\n"
        "📱 <b>Langkah Pembayaran:</b>\n"
        "1. Buka <b>GoPay, BCA, Dana, Mandiri, OVO, ShopeePay</b>, atau Bank/E-Wallet apa pun.\n"
        "2. Pindai / Scan QR Code di atas.\n"
        "3. Pastikan nama merchant: <b>AI Barokah, GN PUTRI</b>.\n"
        f"4. Nominal otomatis terisi: <b>Rp {total:,}</b>.\n"
        "5. Selesaikan pembayaran sebelum batas waktu!\n"
        "────────────────────────\n"
    )

    if status == "PENDING":
        pesan += "💡 <i>Jika sudah transfer, tekan tombol <b>Konfirmasi Sudah Bayar</b> di bawah:</i>"
    elif status == "WAITING_ADMIN":
        pesan += "ℹ️ <i>Admin sedang memeriksa pembayaran Anda. Mohon tunggu sejenak:</i>"
    elif status == "PAID":
        pesan += "🎉 <b>PEMBAYARAN DITERIMA & PESANAN SELESAI!</b>\n"
        delivered = order.get("delivered_items", [])
        if delivered:
            pesan += "\n🎁 <b>DATA AKUN / PESANAN ANDA:</b>\n"
            for i, it in enumerate(delivered, 1):
                pesan += f"<b>{i}.</b> <code>{html.escape(str(it))}</code>\n"
            pesan += "\n⚠️ <i>Harap segera simpan dan amankan data akun di atas.</i>\n"
            pesan += "💬 <i>Garansi & Bantuan: Hubungi Admin @aibarokah</i>"
        else:
            pesan += "\n✅ <i>Pesanan telah diverifikasi oleh admin. Terima kasih telah berbelanja!</i>"
    elif status == "EXPIRED":
        pesan += (
            "⚠️ <b>WAKTU PEMBAYARAN TELAH HABIS (TRANSAKSI GAGAL)</b>\n"
            "Batas waktu 5 menit telah berakhir. Kode QR di atas sudah kedaluwarsa dan tidak berlaku lagi.\n\n"
            "👇 <i>Jika ingin melanjutkan pembayaran, silakan tekan tombol <b>Lanjutkan Bayar (Generate QR Baru)</b> di bawah:</i>"
        )
    elif status == "CANCELLED":
        pesan += "🚫 <i>Pesanan ini telah dibatalkan.</i>"

    keyboard = []
    if status == "PENDING":
        keyboard.append([
            InlineKeyboardButton("✅ Konfirmasi Sudah Bayar", callback_data=f"konfirmasi_order_{order_id}")
        ])
        keyboard.append([
            InlineKeyboardButton("🔄 Cek Status", callback_data=f"cek_order_{order_id}"),
            InlineKeyboardButton("❌ Batalkan Pesanan", callback_data=f"batal_order_{order_id}")
        ])
    elif status == "PAID":
        keyboard.append([
            InlineKeyboardButton("📨 Riwayat Pesanan", callback_data="menu_pesanan"),
            InlineKeyboardButton("🛍️ Beli Produk Lainnya", callback_data="menu_produk")
        ])
    elif status == "EXPIRED":
        keyboard.append([
            InlineKeyboardButton("🔄 Lanjutkan Bayar (Generate QR Baru)", callback_data=f"ulang_order_{order_id}")
        ])
    elif status == "WAITING_ADMIN":
        keyboard.append([
            InlineKeyboardButton("🔄 Cek Status", callback_data=f"cek_order_{order_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Katalog", callback_data="menu_produk")])
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_tampilan_riwayat_pesanan(user_id: int, page=1):
    """Menampilkan daftar riwayat pesanan (pembelian sukses & pesanan aktif) milik pelanggan"""
    order_aktif = get_order_aktif_user(user_id)
    riwayat_selesai = get_riwayat_pesanan_user(user_id)

    pesan = (
        "📨 <b>RIWAYAT PESANAN ANDA</b>\n"
        "────────────────────────\n"
    )

    keyboard = []

    # 1. Pesanan yang sedang aktif (Menunggu Bayar / Menunggu Admin)
    if order_aktif:
        st = order_aktif.get("status")
        badge = "🟡 Menunggu Admin" if st == "WAITING_ADMIN" else "⏳ Menunggu Bayar"
        inv = order_aktif.get("order_id")
        p_name = html.escape(order_aktif.get("nama_produk", "Produk"))
        tot = order_aktif.get("total_bayar", 0)
        qty = order_aktif.get("jumlah", 1)

        pesan += (
            "⏳ <b>PESANAN AKTIF (SEDANG PROSES):</b>\n"
            f"• <b>{p_name}</b> ({qty} item)\n"
            f"• Tagihan: <b>Rp {tot:,}</b> | Status: <b>{badge}</b>\n"
            f"• No. Invoice: <code>#{inv}</code>\n"
            "────────────────────────\n\n"
        )
        keyboard.append([InlineKeyboardButton(f"🧾 Buka Tagihan #{inv}", callback_data=f"buka_order_{inv}")])

    # 2. Riwayat Pesanan yang sudah selesai dibeli (PAID)
    if not riwayat_selesai:
        if not order_aktif:
            pesan += (
                "<i>Anda belum memiliki riwayat pembelian produk.</i>\n\n"
                "💡 <i>Silakan buka katalog produk kami untuk memilih dan membeli produk yang tersedia!</i>"
            )
        else:
            pesan += "<i>Belum ada riwayat pembelian produk yang telah selesai.</i>\n"
    else:
        pesan += f"🛍️ <b>RIWAYAT PEMBELIAN SELESAI ({len(riwayat_selesai)} Transaksi):</b>\n\n"

        PER_PAGE = 5
        total_pages, page, start_idx, end_idx = hitung_pagination(len(riwayat_selesai), page, per_page=PER_PAGE)
        halaman_items = riwayat_selesai[start_idx:end_idx]

        for i, o in enumerate(halaman_items, start=start_idx + 1):
            p_name = html.escape(o.get("nama_produk", "Produk"))
            qty = o.get("jumlah", 1)
            tot = o.get("total_bayar", 0)
            waktu_beli = o.get("paid_at") or o.get("waktu_beli") or o.get("created_at") or "-"
            inv = o.get("order_id")

            pesan += (
                f"<b>{i}. {p_name}</b> ({qty} item)\n"
                f"   • 💰 Total Bayar: <b>Rp {tot:,}</b>\n"
                f"   • ⏰ Waktu Beli: <code>{waktu_beli}</code>\n"
                f"   • 🆔 Invoice: <code>#{inv}</code>\n"
                f"   • 📦 Status: <b>Selesai (PAID) ✅</b>\n\n"
            )
            keyboard.append([
                InlineKeyboardButton(f"📦 Detail #{inv}", callback_data=f"buka_order_{inv}")
            ])

        if total_pages > 1:
            baris_pag = []
            if page > 1:
                baris_pag.append(InlineKeyboardButton("⬅️ Sebelumnya", callback_data=f"riwayat_hal_{page-1}"))
            baris_pag.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
            if page < total_pages:
                baris_pag.append(InlineKeyboardButton("Selanjutnya ➡️", callback_data=f"riwayat_hal_{page+1}"))
            keyboard.append(baris_pag)

    keyboard.append([InlineKeyboardButton("🛒 Buka Katalog Toko", callback_data="menu_produk")])
    keyboard.append([InlineKeyboardButton("🏠 Menu Utama", callback_data="kembali_ke_menu")])

    return pesan, InlineKeyboardMarkup(keyboard)

# ==================== TAMPILAN ADMIN PANEL ====================

def buat_tampilan_admin_panel():
    """Teks dan tombol menu utama Administrator"""
    semua_produk = get_semua_produk()
    total_stok = get_total_stok()
    total_users = get_total_users()
    total_blocked = get_total_blocked_users()
    total_promo = sum(1 for p in semua_produk if p.get("harga_promo", 0) > 0)
    kategori_list = get_semua_kategori()

    info_blocked = f" (Terblokir: {total_blocked})" if total_blocked > 0 else ""

    pesan = (
        "⚙️ <b>PANEL ADMINISTRATOR TOKO</b>\n"
        "────────────────────────\n"
        f"👤 <b>Status:</b> Super Admin ({ADMIN_USERNAME})\n"
        f"👥 <b>Total Pengguna:</b> {total_users}{info_blocked}\n"
        f"📦 <b>Total Jenis Produk:</b> {len(semua_produk)}\n"
        f"📊 <b>Total Stok Tersedia:</b> {total_stok} item\n"
        f"🗂️ <b>Total Kategori:</b> {len(kategori_list)}\n"
        f"🔥 <b>Produk Sedang Promo:</b> {total_promo}\n"
        "────────────────────────\n"
        "Pilih tindakan administrasi di bawah:"
    )

    keyboard = [
        [InlineKeyboardButton("📦 Kelola Stok Produk", callback_data="admin_list_stok")],
        [InlineKeyboardButton("🗂️ Kelola Kategori", callback_data="admin_menu_kategori")],
        [InlineKeyboardButton("👥 Kelola Pengguna", callback_data="admin_menu_users")],
        [InlineKeyboardButton("🏷️ Promo", callback_data="admin_list_promo")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 Kembali ke menu toko", callback_data="kembali_ke_menu")]
    ]

    return pesan, InlineKeyboardMarkup(keyboard)

def buat_tampilan_kelola_produk_menu():
    """Menu utama Kelola Produk di panel admin"""
    semua = get_semua_produk()
    total_stok = get_total_stok()
    pesan = (
        "📦 <b>MENU KELOLA PRODUK & STOK</b>\n"
        "────────────────────────\n"
        f"📊 <b>Total Jenis Produk:</b> {len(semua)}\n"
        f"📦 <b>Total Akumulasi Stok:</b> {total_stok} item\n"
        "────────────────────────\n"
        "Pilih tindakan pengelolaan produk di bawah:"
    )
    keyboard = [
        [InlineKeyboardButton("📋 Lihat Stok Produk", callback_data="admin_lihat_stok")],
        [InlineKeyboardButton("➕ Tambah Produk Baru", callback_data="admin_tambah_produk")],
        [
            InlineKeyboardButton("✏️ Edit Produk", callback_data="admin_menu_edit_produk"),
            InlineKeyboardButton("🗑️ Hapus Produk", callback_data="admin_menu_hapus_produk"),
        ],
        [InlineKeyboardButton("🔙 Kembali ke Admin Panel", callback_data="admin_panel")]
    ]
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_tampilan_daftar_stok(page=1):
    """Tampilan daftar rincian stok semua produk untuk admin dengan pagination (10 item/hal)"""
    semua = get_semua_produk()
    total_stok = get_total_stok()
    total_pages, page, start_idx, end_idx = hitung_pagination(len(semua), page, per_page=ITEMS_PER_PAGE)
    produk_halaman = semua[start_idx:end_idx]

    pesan = (
        "📋 <b>DAFTAR RINCIAN STOK PRODUK</b>\n"
        "────────────────────────\n"
    )

    keyboard = []

    if not semua:
        pesan += "<i>Belum ada produk yang tersimpan di toko.</i>\n\n"
    else:
        for idx, p in enumerate(produk_halaman, start=start_idx + 1):
            stok = p.get("stok", 0)
            if stok > 0:
                status_stok = f"<b>{stok} item</b> (Ready ✅)"
            else:
                status_stok = "<b>0 item</b> (Habis ❌)"

            promo_info = f" | Promo: Rp {p['harga_promo']:,}" if p.get("harga_promo", 0) > 0 else ""
            kat_nama = html.escape(p.get("kategori", "Umum"))
            p_nama = html.escape(p.get("nama", "Produk"))
            pesan += (
                f"{idx}. <b>{p_nama}</b> [🏷️ {kat_nama}]\n"
                f"   • Stok: {status_stok}\n"
                f"   • Harga: Rp {p['harga']:,}{promo_info}\n\n"
            )

        pesan += (
            "────────────────────────\n"
            f"📊 <b>Total Jenis:</b> {len(semua)} produk | 📦 <b>Total Stok:</b> {total_stok} item\n"
        )
        if total_pages > 1:
            pesan += f"📄 <b>Halaman {page} dari {total_pages}</b>\n"
        pesan += "\n🔍 <i>Tekan tombol nomor di bawah untuk melihat rincian detail lengkap:</i>"

        baris_nomor = []
        for idx, p in enumerate(produk_halaman, start=start_idx + 1):
            baris_nomor.append(InlineKeyboardButton(f"{idx}", callback_data=f"admin_stok_detail_{p['id']}"))
            if len(baris_nomor) == 5:
                keyboard.append(baris_nomor)
                baris_nomor = []
        if baris_nomor:
            keyboard.append(baris_nomor)

        if total_pages > 1:
            keyboard.extend(buat_baris_inline_pagination(total_pages, page, "admin_stok_hal"))

    if not semua:
        pesan += (
            "────────────────────────\n"
            f"📊 <b>Total Jenis:</b> 0 produk | 📦 <b>Total Stok:</b> 0 item"
        )

    keyboard.append([InlineKeyboardButton("🔄 Segarkan", callback_data="admin_lihat_stok")])
    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Kelola Produk", callback_data="admin_list_stok")])
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_tampilan_admin_detail_produk(produk, nomor=None):
    """Tampilan detail produk lengkap untuk admin (semua info dari harga sampai deskripsi)"""
    nama_p = html.escape(produk.get("nama", "Produk"))
    kat_p = html.escape(produk.get("kategori", "Umum"))
    desk_p = html.escape(produk.get("deskripsi", "-"))
    harga = produk.get("harga", 0)
    promo = produk.get("harga_promo", 0)
    stok = produk.get("stok", 0)
    pid = produk.get("id", 0)

    if stok > 0:
        stok_status = f"<b>{stok} item</b> (Ready ✅)"
    else:
        stok_status = "<b>0 item</b> (Habis ❌)"

    if promo > 0:
        status_promo = f"🔥 <b>Aktif</b> (Rp {promo:,})"
        harga_berlaku = f"<s>Rp {harga:,}</s> ➔ <b>Rp {promo:,}</b> 🔥"
    else:
        status_promo = "❌ <b>Tidak Aktif</b>"
        harga_berlaku = f"<b>Rp {harga:,}</b>"

    header_no = f"No. {nomor} — " if nomor is not None else ""

    pesan = (
        f"📦 <b>DETAIL LENGKAP PRODUK</b>\n"
        f"────────────────────────\n"
        f"🆔 <b>ID Produk:</b> <code>#{pid}</code>\n"
        f"🏷️ <b>Nama Produk:</b> {header_no}{nama_p}\n"
        f"🗂️ <b>Kategori:</b> {kat_p}\n"
        f"💵 <b>Harga Normal:</b> Rp {harga:,}\n"
        f"🏷️ <b>Promo Diskon:</b> {status_promo}\n"
        f"💰 <b>Harga Jual Saat Ini:</b> {harga_berlaku}\n"
        f"📊 <b>Jumlah Stok:</b> {stok_status}\n"
        f"────────────────────────\n"
        f"📝 <b>Deskripsi Produk:</b>\n"
        f"<blockquote>{desk_p}</blockquote>\n"
        f"────────────────────────\n"
        f"Pilih tindakan untuk produk ini di bawah:"
    )

    keyboard = [
        [
            InlineKeyboardButton("➕ Tambah (+1)", callback_data=f"admin_detail_stok_tambah_{pid}"),
            InlineKeyboardButton("➖ Kurang (-1)", callback_data=f"admin_detail_stok_kurang_{pid}"),
        ],
        [
            InlineKeyboardButton("📥 Restock Akun (Bulk)", callback_data=f"admin_restock_{pid}"),
            InlineKeyboardButton(f"📋 Lihat Akun ({stok})", callback_data=f"admin_lihat_akun_{pid}"),
        ],
        [
            InlineKeyboardButton("✏️ Edit Produk", callback_data=f"admin_edit_pilih_{pid}"),
            InlineKeyboardButton("🗑️ Hapus Produk", callback_data=f"admin_hapus_produk_{pid}"),
        ],
        [
            InlineKeyboardButton("🔙 Kembali ke Lihat Stok", callback_data="admin_lihat_stok"),
            InlineKeyboardButton("📦 Kelola Stok", callback_data="admin_list_stok"),
        ]
    ]
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_tampilan_admin_lihat_akun(produk):
    """Menampilkan daftar akun/stok yang tersimpan pada produk tertentu"""
    nama_p = html.escape(produk.get("nama", "Produk"))
    pid = produk.get("id", 0)
    items = produk.get("items", [])

    pesan = (
        "📋 <b>DAFTAR AKUN / STOK PRODUK</b>\n"
        "────────────────────────\n"
        f"📦 <b>Produk:</b> {nama_p} (<code>#{pid}</code>)\n"
        f"📊 <b>Total Tersedia:</b> <b>{len(items)} item</b>\n"
        "────────────────────────\n"
    )
    if items:
        for i, item in enumerate(items[:20], 1):
            pesan += f"<b>{i}.</b> <code>{html.escape(str(item))}</code>\n"
        if len(items) > 20:
            pesan += f"\n<i>... dan {len(items) - 20} akun lainnya.</i>\n"
    else:
        pesan += "⚠️ <i>Belum ada akun/stok yang diisi pada produk ini (Stok Kosong).</i>\n"

    pesan += "\n────────────────────────\n💡 <i>Klik tombol <b>📥 Tambah / Restock Akun</b> untuk menambahkan akun baru.</i>"
    keyboard = [
        [InlineKeyboardButton("📥 Tambah / Restock Akun", callback_data=f"admin_restock_{pid}")],
        [InlineKeyboardButton("🔙 Kembali ke Detail Produk", callback_data=f"admin_stok_detail_{pid}")]
    ]
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_keyboard_pilih_edit(daftar_produk, page=1):
    """List produk yang bisa dipilih untuk diedit (pagination jika > 10)"""
    total_pages, page, start_idx, end_idx = hitung_pagination(len(daftar_produk), page, per_page=ITEMS_PER_PAGE)
    produk_halaman = daftar_produk[start_idx:end_idx]

    keyboard = []
    for p in produk_halaman:
        btn_text = f"✏️ {p['nama']} (Stok: {p.get('stok', 0)})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"admin_edit_pilih_{p['id']}")])

    if total_pages > 1:
        keyboard.extend(buat_baris_inline_pagination(total_pages, page, "admin_edit_hal"))

    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="admin_list_stok")])
    return InlineKeyboardMarkup(keyboard)

def buat_tampilan_edit_detail(produk):
    """Pilihan bagian produk mana yang ingin diedit"""
    promo_info = f" (Promo: Rp {produk['harga_promo']:,})" if produk.get("harga_promo", 0) > 0 else ""
    nama_p = html.escape(produk.get("nama", "Produk"))
    desk_p = html.escape(produk.get("deskripsi", "-"))
    pesan = (
        f"✏️ <b>Edit Produk: {nama_p}</b>\n"
        f"────────────────────────\n"
        f"🏷️ <b>Nama:</b> {nama_p}\n"
        f"💵 <b>Harga:</b> Rp {produk['harga']:,}{promo_info}\n"
        f"📊 <b>Stok Saat Ini:</b> <b>{produk.get('stok', 0)} item</b>\n"
        f"📝 <b>Deskripsi:</b>\n<blockquote>{desk_p}</blockquote>\n"
        f"────────────────────────\n"
        f"Pilih bagian yang ingin diedit:"
    )
    keyboard = [
        [
            InlineKeyboardButton("➕ Stok (+1)", callback_data=f"admin_stok_tambah_{produk['id']}"),
            InlineKeyboardButton("➖ Stok (-1)", callback_data=f"admin_stok_kurang_{produk['id']}"),
        ],
        [InlineKeyboardButton("📊 Set Angka Stok Manual", callback_data=f"admin_stok_input_{produk['id']}")],
        [
            InlineKeyboardButton("🏷️ Ubah Nama", callback_data=f"admin_edit_nama_{produk['id']}"),
            InlineKeyboardButton("💵 Ubah Harga", callback_data=f"admin_edit_harga_{produk['id']}"),
        ],
        [InlineKeyboardButton("📝 Ubah Deskripsi", callback_data=f"admin_edit_deskripsi_{produk['id']}")],
        [
            InlineKeyboardButton("🔙 Kembali ke Detail Produk", callback_data=f"admin_stok_detail_{produk['id']}"),
            InlineKeyboardButton("📋 Lihat Stok", callback_data="admin_lihat_stok")
        ]
    ]
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_keyboard_pilih_hapus(daftar_produk, page=1):
    """List produk yang bisa dipilih untuk dihapus (pagination jika > 10)"""
    total_pages, page, start_idx, end_idx = hitung_pagination(len(daftar_produk), page, per_page=ITEMS_PER_PAGE)
    produk_halaman = daftar_produk[start_idx:end_idx]

    keyboard = []
    for p in produk_halaman:
        btn_text = f"🗑️ {p['nama']} (Stok: {p.get('stok', 0)})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"admin_hapus_produk_{p['id']}")])

    if total_pages > 1:
        keyboard.extend(buat_baris_inline_pagination(total_pages, page, "admin_hapus_hal"))

    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="admin_list_stok")])
    return InlineKeyboardMarkup(keyboard)


def buat_tampilan_konfirmasi_hapus(produk):
    """Konfirmasi sebelum menghapus produk"""
    nama_p = html.escape(produk.get("nama", "Produk"))
    pesan = (
        f"⚠️ <b>KONFIRMASI HAPUS PRODUK</b>\n"
        f"────────────────────────\n"
        f"Apakah Anda yakin ingin menghapus produk ini secara permanen?\n\n"
        f"📦 <b>{nama_p}</b>\n"
        f"💵 Harga: Rp {produk['harga']:,}\n"
        f"📊 Sisa Stok: {produk.get('stok', 0)} item"
    )
    keyboard = [
        [InlineKeyboardButton("🗑️ Ya, Hapus Permanen", callback_data=f"admin_konfirm_hapus_{produk['id']}")],
        [InlineKeyboardButton("❌ Batal (Kembali)", callback_data=f"admin_stok_detail_{produk['id']}")]
    ]
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_keyboard_kelola_promo(daftar_produk, page=1):
    """List produk untuk dipilih saat ingin mengatur promo diskon (pagination jika > 10)"""
    total_pages, page, start_idx, end_idx = hitung_pagination(len(daftar_produk), page, per_page=ITEMS_PER_PAGE)
    produk_halaman = daftar_produk[start_idx:end_idx]

    keyboard = []
    for p in produk_halaman:
        promo_info = f"🔥 Rp {p['harga_promo']:,}" if p.get("harga_promo", 0) > 0 else "Normal"
        btn_text = f"{p['nama']} [{promo_info}]"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"admin_pilih_promo_{p['id']}")])

    if total_pages > 1:
        keyboard.extend(buat_baris_inline_pagination(total_pages, page, "admin_promo_hal"))

    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

def buat_tampilan_atur_promo(produk):
    """Tampilan atur promo untuk 1 produk tertentu"""
    status_promo = f"🔥 Aktif (Rp {produk['harga_promo']:,})" if produk.get("harga_promo", 0) > 0 else "❌ Tidak Aktif"
    nama_p = html.escape(produk.get("nama", "Produk"))

    pesan = (
        f"🏷️ <b>Pengaturan Promo Diskon</b>\n"
        f"────────────────────────\n"
        f"Nama: <b>{nama_p}</b>\n"
        f"Harga Normal: <b>Rp {produk['harga']:,}</b>\n"
        f"Status Promo: <b>{status_promo}</b>\n"
        f"────────────────────────\n"
        f"Pilih aksi promo:"
    )

    keyboard = [
        [InlineKeyboardButton("🏷️ Atur Harga Promo Diskon", callback_data=f"admin_promo_input_{produk['id']}")],
        [InlineKeyboardButton("❌ Matikan Promo (Harga Normal)", callback_data=f"admin_promo_mati_{produk['id']}")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="admin_list_promo")]
    ]
    return pesan, InlineKeyboardMarkup(keyboard)

# ==================== TAMPILAN KELOLA KATEGORI ====================

def buat_tampilan_kelola_kategori(page=1):
    """Tampilan menu kelola kategori (tambah dan hapus) dengan pagination jika > 10"""
    kategori_list = get_semua_kategori()
    total_pages, page, start_idx, end_idx = hitung_pagination(len(kategori_list), page, per_page=ITEMS_PER_PAGE)
    kat_halaman = kategori_list[start_idx:end_idx]

    pesan = (
        "🗂️ <b>MENU KELOLA KATEGORI PRODUK</b>\n"
        "────────────────────────\n"
        "Daftar kategori aktif saat ini:\n\n"
    )
    if not kategori_list:
        pesan += "<i>Belum ada kategori yang tersimpan.</i>\n"
    else:
        for idx, kat in enumerate(kat_halaman, start=start_idx + 1):
            jml = get_jumlah_produk_by_kategori(kat)
            status_pakai = f"<b>{jml} produk</b>" if jml > 0 else "<i>Kosong</i>"
            pesan += f"<b>{idx}.</b> {html.escape(kat)} — {status_pakai}\n"

    pesan += (
        "\n────────────────────────\n"
        f"📊 <b>Total Kategori:</b> {len(kategori_list)}\n"
    )
    if total_pages > 1:
        pesan += f"📄 <b>Halaman {page} dari {total_pages}</b>\n"
    pesan += (
        "⚠️ <i>Catatan: Kategori yang memiliki produk tidak dapat dihapus.</i>\n\n"
        "Pilih tindakan di bawah:"
    )

    keyboard = [
        [InlineKeyboardButton("➕ Tambah Kategori", callback_data="admin_kategori_tambah_input")],
        [InlineKeyboardButton("🗑️ Hapus Kategori", callback_data="admin_kategori_hapus_menu")],
    ]
    if total_pages > 1:
        keyboard.extend(buat_baris_inline_pagination(total_pages, page, "admin_kat_menu_hal"))

    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Admin Panel", callback_data="admin_panel")])
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_keyboard_hapus_kategori(daftar_kategori, page=1):
    """Keyboard daftar kategori untuk dipilih saat ingin menghapus (pagination jika > 10)"""
    total_pages, page, start_idx, end_idx = hitung_pagination(len(daftar_kategori), page, per_page=ITEMS_PER_PAGE)
    kat_halaman = daftar_kategori[start_idx:end_idx]

    keyboard = []
    for idx, kat in enumerate(kat_halaman, start=start_idx):
        jml = get_jumlah_produk_by_kategori(kat)
        if jml > 0:
            btn_text = f"🔒 {idx + 1}. {kat} ({jml} produk)"
        else:
            btn_text = f"🗑️ {idx + 1}. {kat} (Kosong)"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"admin_kat_del_{idx}")])

    if total_pages > 1:
        keyboard.extend(buat_baris_inline_pagination(total_pages, page, "admin_kat_del_hal"))

    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="admin_menu_kategori")])
    return InlineKeyboardMarkup(keyboard)

# ==================== TAMPILAN KELOLA PENGGUNA ====================

def buat_tampilan_daftar_users(daftar_users, page=1):
    """Tampilan daftar pengguna terdaftar untuk administrator dengan pagination (10 item/hal)"""
    pesan = (
        "👥 <b>DAFTAR PENGGUNA TERDAFTAR</b>\n"
        "────────────────────────\n"
    )

    keyboard = []
    total_pages, page, start_idx, end_idx = hitung_pagination(len(daftar_users), page, per_page=ITEMS_PER_PAGE)
    users_halaman = daftar_users[start_idx:end_idx]

    if not daftar_users:
        pesan += "<i>Belum ada pengguna terdaftar saat ini.</i>\n\n"
    else:
        for idx, u in enumerate(users_halaman, start=start_idx + 1):
            uid = u.get("id")
            uname = u.get("username")
            uname_teks = f"@{uname}" if uname else "<i>(tanpa username)</i>"
            first_name = html.escape(u.get("first_name", "Pengguna"))
            is_blocked = u.get("is_blocked", False)
            status_tag = "⛔ [DIBLOKIR]" if is_blocked else "✅ [Aktif]"
            admin_tag = " 👑 [Admin]" if uid in ADMIN_IDS else ""

            pesan += (
                f"{idx}. <b>{first_name}</b>{admin_tag}\n"
                f"   • ID: <code>{uid}</code> | {uname_teks}\n"
                f"   • Status: {status_tag}\n\n"
            )

        pesan += (
            "────────────────────────\n"
            f"📊 <b>Total:</b> {len(daftar_users)} pengguna\n"
        )
        if total_pages > 1:
            pesan += f"📄 <b>Halaman {page} dari {total_pages}</b>\n"
        pesan += "\n🔍 <i>Tekan tombol nomor di bawah untuk melihat rincian detail & opsi blokir:</i>"

        baris_nomor = []
        for idx, u in enumerate(users_halaman, start=start_idx + 1):
            baris_nomor.append(InlineKeyboardButton(f"{idx}", callback_data=f"admin_user_detail_{u['id']}"))
            if len(baris_nomor) == 5:
                keyboard.append(baris_nomor)
                baris_nomor = []
        if baris_nomor:
            keyboard.append(baris_nomor)

        if total_pages > 1:
            keyboard.extend(buat_baris_inline_pagination(total_pages, page, "admin_users_hal"))

    keyboard.append([InlineKeyboardButton("🔄 Segarkan", callback_data="admin_menu_users")])
    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Admin Panel", callback_data="admin_panel")])
    return pesan, InlineKeyboardMarkup(keyboard)

def buat_tampilan_detail_user(user_profile, nomor=None):
    """Tampilan detail satu pengguna dengan opsi blokir/unblock"""
    uid = user_profile.get("id")
    uname = user_profile.get("username")
    uname_teks = f"@{uname}" if uname else "<i>(Tidak memiliki username)</i>"
    first_name = html.escape(user_profile.get("first_name", "Pengguna"))
    joined_at = user_profile.get("joined_at", "-")
    is_blocked = user_profile.get("is_blocked", False)
    is_admin = uid in ADMIN_IDS

    if is_blocked:
        status_teks = "⛔ <b>TERBLOKIR (Akses Dicabut & Di-kick)</b>"
    elif is_admin:
        status_teks = "👑 <b>Super Administrator (Aktif)</b>"
    else:
        status_teks = "✅ <b>Pengguna Aktif</b>"

    header_no = f"No. {nomor} — " if nomor is not None else ""

    pesan = (
        f"👤 <b>DETAIL PENGGUNA ({header_no}{first_name})</b>\n"
        f"────────────────────────\n"
        f"🆔 <b>ID Telegram:</b> <code>#{uid}</code>\n"
        f"👤 <b>Nama:</b> {first_name}\n"
        f"🔗 <b>Username:</b> {uname_teks}\n"
        f"⏰ <b>Waktu Terdaftar:</b> {joined_at}\n"
        f"🛡️ <b>Status Akses:</b> {status_teks}\n"
        f"────────────────────────\n"
        f"Pilih tindakan untuk pengguna ini:"
    )

    keyboard = []
    if not is_admin:
        if not is_blocked:
            keyboard.append([InlineKeyboardButton("🚫 Blokir & Kick Pengguna", callback_data=f"admin_user_blokir_{uid}")])
        else:
            keyboard.append([InlineKeyboardButton("🔓 Buka Blokir Pengguna", callback_data=f"admin_user_unblock_{uid}")])

    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Daftar Pengguna", callback_data="admin_menu_users")])
    keyboard.append([InlineKeyboardButton("⚙️ Panel Administrator", callback_data="admin_panel")])
    return pesan, InlineKeyboardMarkup(keyboard)

# ==================== WIZARD TAMBAH PRODUK (UI & KEYBOARDS) ====================

def buat_pesan_wizard_step1(current_nama=None):
    """Pesan instruksi Step 1 (1/5): Nama Produk"""
    pesan = (
        "➕ <b>TAMBAH PRODUK BARU (Langkah 1/5)</b>\n"
        "────────────────────────\n"
        "Silakan ketik <b>Nama Produk</b> yang ingin Anda jual di chat:\n"
    )
    if current_nama:
        pesan += f"\n🏷️ <i>Nama saat ini:</i> <b>{html.escape(current_nama)}</b>\n<i>(Ketik nama baru di chat untuk mengubah)</i>"
    else:
        pesan += "\n<i>Contoh: ChatGPT Plus 1 Bulan</i>"
    return pesan

def buat_keyboard_wizard_step1(current_nama=None):
    """Keyboard Step 1: Batalkan (dan opsi lanjut jika sudah pernah diisi)"""
    keyboard = []
    if current_nama:
        keyboard.append([InlineKeyboardButton(f"➡️ Lanjut ({current_nama[:20]})", callback_data="wizard_ke_step2")])
    keyboard.append([InlineKeyboardButton("❌ Batalkan", callback_data="batal_tambah_produk")])
    return InlineKeyboardMarkup(keyboard)

def buat_pesan_wizard_step2(nama, current_kategori=None, page=1):
    """Pesan instruksi Step 2 (2/5): Kategori Produk dengan pagination jika > 10"""
    kategori_list = get_semua_kategori()
    total_pages, page, start_idx, end_idx = hitung_pagination(len(kategori_list), page, per_page=ITEMS_PER_PAGE)
    kat_halaman = kategori_list[start_idx:end_idx]
    nama_safe = html.escape(nama)
    pesan = (
        "🗂️ <b>TAMBAH PRODUK (Langkah 2/5)</b>\n"
        "────────────────────────\n"
        f"Produk: <b>{nama_safe}</b>\n\n"
        "Pilih <b>Kategori</b> untuk produk ini:\n"
    )
    for idx, kat in enumerate(kat_halaman, start=start_idx + 1):
        pesan += f"<b>{idx}.</b> {html.escape(kat)}\n"
    nomor_lainnya = len(kategori_list) + 1
    pesan += f"<b>{nomor_lainnya}.</b> ✍️ <i>Lainnya (Ketik Kategori Baru)</i>\n"
    pesan += "────────────────────────\n"
    if total_pages > 1:
        pesan += f"📄 <b>Halaman {page} dari {total_pages}</b> <i>(Total: {len(kategori_list)} kategori)</i>\n"
    pesan += f"Silakan <b>klik tombol</b> di bawah atau <b>ketik nomor (1 - {nomor_lainnya})</b> di chat:"
    if current_kategori:
        pesan += f"\n\n🏷️ <i>Kategori saat ini:</i> <b>{html.escape(current_kategori)}</b>"
    return pesan

def buat_keyboard_wizard_step2(current_kategori=None, page=1):
    """Keyboard Step 2: Pilihan Kategori, Lainnya, Kembali, & Batalkan (dengan pagination jika > 10)"""
    kategori_list = get_semua_kategori()
    total_pages, page, start_idx, end_idx = hitung_pagination(len(kategori_list), page, per_page=ITEMS_PER_PAGE)
    kat_halaman = kategori_list[start_idx:end_idx]

    keyboard = []
    baris = []
    for idx, kat in enumerate(kat_halaman, start=start_idx + 1):
        btn_text = f"{idx}. {kat}"
        baris.append(InlineKeyboardButton(btn_text, callback_data=f"wizard_pilih_kat_{idx-1}"))
        if len(baris) == 2:
            keyboard.append(baris)
            baris = []
    if baris:
        keyboard.append(baris)

    if total_pages > 1:
        keyboard.extend(buat_baris_inline_pagination(total_pages, page, "wizard_kat_hal"))

    nomor_lainnya = len(kategori_list) + 1
    keyboard.append([InlineKeyboardButton(f"{nomor_lainnya}. ✍️ Lainnya (Ketik Baru)", callback_data="wizard_pilih_kat_lainnya")])

    if current_kategori:
        keyboard.append([InlineKeyboardButton(f"➡️ Tetap: {current_kategori[:20]}", callback_data="wizard_ke_step3")])

    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali", callback_data="wizard_ke_step1"),
        InlineKeyboardButton("❌ Batalkan", callback_data="batal_tambah_produk")
    ])
    return InlineKeyboardMarkup(keyboard)

def buat_pesan_wizard_step3(nama, kategori, current_harga=None):
    """Pesan instruksi Step 3 (3/5): Harga Jual"""
    nama_safe = html.escape(nama)
    kat_safe = html.escape(kategori)
    pesan = (
        "💵 <b>TAMBAH PRODUK (Langkah 3/5)</b>\n"
        "────────────────────────\n"
        f"Produk: <b>{nama_safe}</b>\n"
        f"Kategori: <b>{kat_safe}</b>\n\n"
        "Berapa <b>Harga Jual</b> produk ini dalam Rupiah?\n"
    )
    if current_harga:
        pesan += f"\n💵 <i>Harga saat ini:</i> <b>Rp {current_harga:,}</b>\n<i>(Ketik nominal baru, contoh: <code>45000</code>)</i>"
    else:
        pesan += "<i>(Ketik nominal angka saja, contoh: <code>45000</code>)</i>"
    return pesan

def buat_keyboard_wizard_step3(current_harga=None):
    """Keyboard Step 3: Kembali ke Step 2 & Batalkan"""
    keyboard = []
    if current_harga:
        keyboard.append([InlineKeyboardButton(f"➡️ Tetap Gunakan: Rp {current_harga:,}", callback_data="wizard_ke_step4")])
    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali", callback_data="wizard_ke_step2"),
        InlineKeyboardButton("❌ Batalkan", callback_data="batal_tambah_produk")
    ])
    return InlineKeyboardMarkup(keyboard)

def buat_pesan_wizard_step4(nama, kategori, harga, current_stok=None, current_items=None):
    """Pesan instruksi Step 4 (4/5): Isian Stok Akun/Voucher (Model 1: 1 baris = 1 akun)"""
    nama_safe = html.escape(nama)
    kat_safe = html.escape(kategori)
    pesan = (
        "📊 <b>TAMBAH PRODUK (Langkah 4/5) — Isian Akun / Stok</b>\n"
        "────────────────────────\n"
        f"Produk: <b>{nama_safe}</b>\n"
        f"Kategori: <b>{kat_safe}</b>\n"
        f"Harga: <b>Rp {harga:,}</b>\n\n"
        "Silakan <b>paste/kirimkan daftar akun atau data produk</b> di chat:\n"
        "💡 <i>Format: <b>1 baris = 1 akun/item</b></i>\n\n"
        "<b>Contoh:</b>\n"
        "<code>user1@gmail.com | pass123 | PIN: 1234</code>\n"
        "<code>user2@gmail.com | pass456 | PIN: 5678</code>\n\n"
        "Stok otomatis dihitung dari banyaknya baris yang Anda kirim.\n"
        "<i>(Atau tekan tombol 'Kosongkan Stok Dulu' di bawah jika belum ada akun):</i>"
    )
    if current_items:
        pesan += f"\n\n📊 <i>Daftar saat ini:</i> <b>{len(current_items)} akun</b>"
    elif current_stok is not None and current_stok > 0:
        pesan += f"\n\n📊 <i>Stok saat ini:</i> <b>{current_stok} item</b>"
    return pesan

def buat_keyboard_wizard_step4(current_stok=None, current_items=None):
    """Keyboard Step 4: Kembali, Kosongkan Stok, Lanjut jika ada, & Batalkan"""
    keyboard = []
    total = len(current_items) if current_items else (current_stok or 0)
    if total > 0:
        keyboard.append([InlineKeyboardButton(f"➡️ Tetap Gunakan: {total} item", callback_data="wizard_ke_step5")])
    keyboard.append([InlineKeyboardButton("⏩ Kosongkan Stok Dulu (0 item)", callback_data="wizard_skip_stok")])
    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali", callback_data="wizard_ke_step3"),
        InlineKeyboardButton("❌ Batalkan", callback_data="batal_tambah_produk")
    ])
    return InlineKeyboardMarkup(keyboard)

def buat_pesan_wizard_step5(nama, kategori, harga, stok, current_deskripsi=None):
    """Pesan instruksi Step 5 (5/5): Deskripsi Produk"""
    nama_safe = html.escape(nama)
    kat_safe = html.escape(kategori)
    pesan = (
        "📝 <b>TAMBAH PRODUK (Langkah 5/5)</b>\n"
        "────────────────────────\n"
        f"Produk: <b>{nama_safe}</b>\n"
        f"Kategori: <b>{kat_safe}</b>\n"
        f"Harga: <b>Rp {harga:,}</b>\n"
        f"Stok: <b>{stok} item</b>\n\n"
        "Silakan ketik <b>Deskripsi / Garansi / Detail Produk</b>:\n"
    )
    if current_deskripsi and current_deskripsi != "-":
        pesan += f"\n📝 <i>Deskripsi saat ini:</i>\n<blockquote>{html.escape(current_deskripsi)}</blockquote>\n<i>(Ketik deskripsi baru di chat, atau lewati)</i>"
    else:
        pesan += "<i>(Atau tekan tombol 'Lewati' di bawah jika tanpa deskripsi)</i>"
    return pesan

def buat_keyboard_wizard_step5(current_deskripsi=None):
    """Keyboard Step 5: Opsi lewati, Kembali ke Step 4 & Batalkan"""
    keyboard = []
    if current_deskripsi and current_deskripsi != "-":
        keyboard.append([InlineKeyboardButton("➡️ Tetap Gunakan Deskripsi Ini", callback_data="wizard_ke_preview")])
    keyboard.append([InlineKeyboardButton("⏩ Lewati (Tanpa Deskripsi)", callback_data="tambah_skip_deskripsi")])
    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali", callback_data="wizard_ke_step4"),
        InlineKeyboardButton("❌ Batalkan", callback_data="batal_tambah_produk")
    ])
    return InlineKeyboardMarkup(keyboard)

def buat_pesan_wizard_preview(nama, kategori, harga, stok, deskripsi):
    """Pesan pratinjau sebelum konfirmasi simpan"""
    nama_safe = html.escape(nama)
    kat_safe = html.escape(kategori)
    deskripsi_safe = html.escape(deskripsi) if (deskripsi and deskripsi != "-") else None
    deskripsi_teks = "<i>(Tanpa deskripsi)</i>" if not deskripsi_safe else f"<blockquote>{deskripsi_safe}</blockquote>"
    pesan = (
        "✨ <b>PRATINJAU PRODUK BARU</b>\n"
        "────────────────────────\n"
        f"📦 <b>Nama:</b> {nama_safe}\n"
        f"🏷️ <b>Kategori:</b> {kat_safe}\n"
        f"💵 <b>Harga:</b> Rp {harga:,}\n"
        f"📊 <b>Stok Awal:</b> {stok} item\n"
        f"📝 <b>Deskripsi:</b>\n{deskripsi_teks}\n"
        "────────────────────────\n"
        "Apakah data produk di atas sudah sesuai?"
    )
    return pesan

def buat_keyboard_konfirmasi_tambah():
    """Tombol simpan, kembali ke step 5, atau batalkan pada pratinjau produk baru"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Simpan Produk Sekarang", callback_data="tambah_simpan_produk")],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="wizard_ke_step5"),
            InlineKeyboardButton("❌ Batalkan", callback_data="batal_tambah_produk")
        ]
    ])

def buat_keyboard_batal_wizard():
    """Alias kompatibilitas mundur"""
    return buat_keyboard_wizard_step1()

def buat_keyboard_wizard_deskripsi():
    """Alias kompatibilitas mundur"""
    return buat_keyboard_wizard_step5()
