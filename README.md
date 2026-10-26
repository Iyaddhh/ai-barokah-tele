# 🤖 AI Barokah — Telegram Bot

Bot Telegram otomatis untuk toko digital **AI Barokah**, dilengkapi fitur manajemen produk, verifikasi member, pembayaran QRIS, dan panel admin.

---

## ✨ Fitur Utama

- 🛒 **Toko Digital** — Katalog produk dengan kategori, stok, dan harga
- 💳 **Pembayaran QRIS** — Generate QR GoPay otomatis saat checkout
- 👤 **Manajemen Member** — Registrasi, verifikasi, dan profil pengguna
- 🔒 **Wajib Join Channel** — Verifikasi keanggotaan channel sebelum akses
- 🛠️ **Panel Admin** — Kelola produk, pesanan, dan pengguna via bot
- 📢 **Notifikasi Otomatis** — Log pesanan masuk ke channel notifikasi

---

## 🚀 Cara Menjalankan

### 1. Clone Repository

```bash
git clone https://github.com/Iyaddhh/ai-barokah-tele.git
cd ai-barokah-tele
```

### 2. Buat Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment

Salin file `.env.example` menjadi `.env`:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Lalu edit file `.env` dan isi dengan data Anda:

```env
BOT_TOKEN=your_bot_token_here          # Token dari @BotFather
ADMIN_IDS=123456789                    # ID Telegram admin (pisah koma jika lebih dari 1)
ADMIN_USERNAME=@your_admin_username    # Username Telegram admin
NOTIF_CHANNEL_ID=@your_notif_channel   # Channel untuk notifikasi pesanan
GOPAY_QRIS_STRING=00020101021126610014COM.GO-JEK.WWW...  # String QRIS GoPay
```

> **Cara mendapatkan BOT_TOKEN:**
> 1. Buka Telegram, cari **@BotFather**
> 2. Kirim `/newbot` dan ikuti instruksinya
> 3. Salin token yang diberikan ke `BOT_TOKEN`

> **Cara mendapatkan ID Telegram:**
> 1. Cari bot **@userinfobot** di Telegram
> 2. Kirim `/start` — bot akan membalas dengan ID Anda

### 5. Jalankan Bot

```bash
python bot.py
```

Jika berhasil, terminal akan menampilkan:

```
=========================================
Bot AI Barokah berjalan...
Administrator ID: [your_id]
Total Produk Tersedia: X
Total Pengguna Terdaftar: X
Wajib Join: @channel1 & @channel2
=========================================
```

---

## 📁 Struktur Project

```
ai-barokah-tele/
├── bot.py              # Entry point utama bot
├── config.py           # Konfigurasi & variabel environment
├── database.py         # Fungsi CRUD data (produk, user, pesanan)
├── helpers.py          # Fungsi utilitas
├── qris.py             # Generator QR Code pembayaran
├── ui.py               # Semua teks & tampilan pesan bot
├── handlers/
│   ├── callbacks.py    # Handler tombol inline keyboard
│   ├── common.py       # Command /start, /admin, /batal
│   ├── members.py      # Logika khusus member
│   └── messages.py     # Handler pesan teks
├── data/
│   ├── products.json   # Database produk
│   ├── categories.json # Daftar kategori produk
│   ├── orders.json     # Riwayat pesanan
│   ├── registered_users.json  # Data user terdaftar
│   └── users_profile.json     # Profil pengguna
├── assets/             # Gambar & media bot
├── requirements.txt    # Daftar dependensi Python
└── .env.example        # Template konfigurasi
```

---

## ⚙️ Konfigurasi Channel

Edit bagian `CHANNELS` di `config.py` untuk mengatur channel yang wajib diikuti pengguna:

```python
CHANNELS = [
    {
        "id": "@nama_channel",
        "name": "1. 📢 Nama Tampilan",
        "link": "https://t.me/nama_channel"
    },
]
```

---

## 📦 Dependensi

| Package | Versi | Fungsi |
|---|---|---|
| `python-telegram-bot` | >= 21.0 | Framework bot Telegram |
| `python-dotenv` | >= 1.0.0 | Load variabel dari `.env` |
| `httpx` | >= 0.25.0 | HTTP client async |
| `qrcode` | >= 8.0.0 | Generate QR Code QRIS |
| `pillow` | >= 10.0.0 | Manipulasi gambar QR |

---

## 🔐 Keamanan

- **Jangan pernah** commit file `.env` ke repository
- File `.env` sudah otomatis diabaikan oleh `.gitignore`
- Gunakan selalu `.env.example` sebagai template

---

## 📜 Lisensi

Project ini dibuat untuk keperluan pribadi/bisnis **AI Barokah Store**.
