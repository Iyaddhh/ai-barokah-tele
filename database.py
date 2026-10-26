import os
import json
from datetime import datetime, timezone, timedelta
from config import DATA_FILE, PRODUCTS_FILE, CATEGORIES_FILE, USERS_PROFILE_FILE, BLOCKED_USERS_FILE, ORDERS_FILE

# Set global memori user terdaftar & profil & pesanan
registered_users = set()
users_profile = {}
blocked_users = set()
orders = {}

# ==================== PENGELOLAAN USER & BLOKIR ====================

def muat_users() -> set:
    """Memuat data user terdaftar, profil, dan user terblokir dari file JSON"""
    global registered_users, users_profile, blocked_users
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                registered_users = set(data)
        except Exception as e:
            print(f"[ERROR MUAT USERS]: {e}")
            registered_users = set()
    else:
        registered_users = set()

    if os.path.exists(USERS_PROFILE_FILE):
        try:
            with open(USERS_PROFILE_FILE, "r", encoding="utf-8") as f:
                users_profile = json.load(f)
        except Exception as e:
            print(f"[ERROR MUAT PROFIL]: {e}")
            users_profile = {}
    else:
        users_profile = {}

    if os.path.exists(BLOCKED_USERS_FILE):
        try:
            with open(BLOCKED_USERS_FILE, "r", encoding="utf-8") as f:
                data_b = json.load(f)
                blocked_users = set(data_b)
        except Exception as e:
            print(f"[ERROR MUAT BLOKIR]: {e}")
            blocked_users = set()
    else:
        blocked_users = set()

    return registered_users

def simpan_users():
    """Menyimpan data user terdaftar, profil, dan blokir ke file JSON secara atomik"""
    # 1. Simpan registered_users.json
    temp_reg = f"{DATA_FILE}.tmp"
    try:
        with open(temp_reg, "w", encoding="utf-8") as f:
            json.dump(list(registered_users), f, indent=2)
        os.replace(temp_reg, DATA_FILE)
    except Exception as e:
        print(f"[ERROR SIMPAN USERS]: {e}")
        if os.path.exists(temp_reg):
            try:
                os.remove(temp_reg)
            except Exception:
                pass

    # 2. Simpan users_profile.json
    temp_prof = f"{USERS_PROFILE_FILE}.tmp"
    try:
        with open(temp_prof, "w", encoding="utf-8") as f:
            json.dump(users_profile, f, indent=2, ensure_ascii=False)
        os.replace(temp_prof, USERS_PROFILE_FILE)
    except Exception as e:
        print(f"[ERROR SIMPAN PROFIL]: {e}")
        if os.path.exists(temp_prof):
            try:
                os.remove(temp_prof)
            except Exception:
                pass

    # 3. Simpan blocked_users.json
    temp_blk = f"{BLOCKED_USERS_FILE}.tmp"
    try:
        with open(temp_blk, "w", encoding="utf-8") as f:
            json.dump(list(blocked_users), f, indent=2)
        os.replace(temp_blk, BLOCKED_USERS_FILE)
    except Exception as e:
        print(f"[ERROR SIMPAN BLOKIR]: {e}")
        if os.path.exists(temp_blk):
            try:
                os.remove(temp_blk)
            except Exception:
                pass

def simpan_update_user_profile(user_id: int, username: str = None, first_name: str = None):
    """Menyimpan atau memperbarui data profil pengguna"""
    uid_str = str(user_id)
    now_str = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M:%S WIB")

    if uid_str not in users_profile:
        users_profile[uid_str] = {
            "id": user_id,
            "username": (username or "").replace("@", ""),
            "first_name": first_name or "Pengguna",
            "joined_at": now_str,
            "is_blocked": user_id in blocked_users
        }
    else:
        if username is not None:
            users_profile[uid_str]["username"] = username.replace("@", "")
        if first_name is not None:
            users_profile[uid_str]["first_name"] = first_name
        users_profile[uid_str]["is_blocked"] = user_id in blocked_users

    simpan_users()

def get_user_profile(user_id: int) -> dict:
    """Mengambil rincian profil pengguna"""
    uid_str = str(user_id)
    if uid_str in users_profile:
        prof = dict(users_profile[uid_str])
        prof["is_blocked"] = user_id in blocked_users
        return prof

    return {
        "id": user_id,
        "username": "",
        "first_name": "Pengguna",
        "joined_at": "-",
        "is_blocked": user_id in blocked_users
    }

def get_semua_users_data() -> list:
    """Mengambil daftar seluruh pengguna terdaftar untuk panel admin"""
    hasil = []
    # Urutkan registered_users
    for uid in list(registered_users):
        hasil.append(get_user_profile(uid))
    return hasil

def is_user_blocked(user_id: int) -> bool:
    """Mengecek apakah user sedang dalam daftar blokir"""
    return user_id in blocked_users

def blokir_user(user_id: int) -> bool:
    """Memblokir user secara permanen dan mencabut status terdaftar"""
    blocked_users.add(user_id)
    registered_users.discard(user_id)
    uid_str = str(user_id)
    if uid_str in users_profile:
        users_profile[uid_str]["is_blocked"] = True
    else:
        users_profile[uid_str] = {
            "id": user_id,
            "username": "",
            "first_name": "Pengguna",
            "joined_at": "-",
            "is_blocked": True
        }
    simpan_users()
    return True

def unblock_user(user_id: int) -> bool:
    """Membuka blokir user"""
    blocked_users.discard(user_id)
    uid_str = str(user_id)
    if uid_str in users_profile:
        users_profile[uid_str]["is_blocked"] = False
    simpan_users()
    return True

def tambah_user(user_id: int, username: str = None, first_name: str = None):
    """Menambahkan user ke database jika belum terdaftar dan tidak diblokir"""
    if is_user_blocked(user_id):
        return

    simpan_update_user_profile(user_id, username=username, first_name=first_name)
    if user_id not in registered_users:
        registered_users.add(user_id)
        simpan_users()

def hapus_user(user_id: int):
    """Menghapus user dari database jika terdaftar"""
    if user_id in registered_users:
        registered_users.discard(user_id)
        simpan_users()

def user_terdaftar(user_id: int) -> bool:
    """Mengecek apakah user sudah terdaftar dan tidak diblokir"""
    if is_user_blocked(user_id):
        return False
    return user_id in registered_users

def get_total_users() -> int:
    """Mengambil total jumlah user terdaftar"""
    return len(registered_users)

def get_total_blocked_users() -> int:
    """Mengambil total jumlah user terblokir"""
    return len(blocked_users)

def get_semua_user_ids() -> list:
    """Mengambil seluruh daftar ID pengguna terdaftar yang aktif (tidak diblokir)"""
    return [uid for uid in list(registered_users) if not is_user_blocked(uid)]

# ==================== PENGELOLAAN PRODUK & STOK ====================

def muat_produk() -> list:
    """Memuat daftar produk dari products.json dan memastikan field items tersedia"""
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                daftar = json.load(f)
                diubah = False
                for p in daftar:
                    if "items" not in p:
                        # Inisialisasi items dengan dummy sesuai stok awal jika ada
                        p["items"] = [f"Akun #{i+1} ({p.get('nama')})" for i in range(p.get("stok", 0))]
                        diubah = True
                    else:
                        p["stok"] = len(p["items"])
                if diubah:
                    simpan_produk(daftar)
                return daftar
        except Exception as e:
            print(f"[ERROR MUAT PRODUK]: {e}")
            return []
    else:
        simpan_produk([])
        return []

def simpan_produk(daftar_produk: list):
    """Menyimpan daftar produk ke products.json secara atomik dengan fallback Windows"""
    temp_file = f"{PRODUCTS_FILE}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(daftar_produk, f, indent=2, ensure_ascii=False)
        try:
            os.replace(temp_file, PRODUCTS_FILE)
        except OSError:
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                json.dump(daftar_produk, f, indent=2, ensure_ascii=False)
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
    except Exception as e:
        print(f"[ERROR SIMPAN PRODUK]: {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

def get_semua_produk() -> list:
    """Mengambil seluruh produk"""
    return muat_produk()

def get_produk_by_id(produk_id: int):
    """Mengambil satu produk berdasarkan ID"""
    semua = muat_produk()
    for p in semua:
        if p["id"] == produk_id:
            return p
    return None

def tambah_produk(nama: str, harga: int, stok: int, deskripsi: str, harga_promo: int = 0, kategori: str = "Umum", items: list = None):
    """Menambahkan produk baru ke katalog dengan isian items (Model 1)"""
    semua = muat_produk()
    next_id = max([p.get("id", 0) for p in semua], default=0) + 1

    # Sanitasi harga_promo dan kategori jika dipanggil tanpa keyword args
    try:
        clean_promo = int(harga_promo)
    except (ValueError, TypeError):
        clean_promo = 0
        if isinstance(harga_promo, str) and (kategori == "Umum" or not kategori):
            kategori = harga_promo

    list_items = [str(x).strip() for x in items if str(x).strip()] if items else []
    hitung_stok = len(list_items) if list_items else max(0, int(stok))

    baru = {
        "id": next_id,
        "nama": str(nama).strip(),
        "kategori": str(kategori or "Umum").strip(),
        "harga": max(0, int(harga)),
        "harga_promo": max(0, clean_promo),
        "stok": hitung_stok,
        "items": list_items,
        "deskripsi": str(deskripsi or "-").strip()
    }
    semua.append(baru)
    simpan_produk(semua)
    return baru

def update_stok(produk_id: int, new_stok: int) -> bool:
    """Memperbarui stok produk secara langsung"""
    semua = muat_produk()
    for p in semua:
        if p["id"] == produk_id:
            p["stok"] = max(0, new_stok)
            simpan_produk(semua)
            return True
    return False

def tambah_stok(produk_id: int, delta: int) -> bool:
    """Menambah atau mengurangi stok dengan selisih delta (+1 / -1)"""
    semua = muat_produk()
    for p in semua:
        if p["id"] == produk_id:
            p["stok"] = max(0, p.get("stok", 0) + delta)
            simpan_produk(semua)
            return True
    return False

def tambah_stok_items(produk_id: int, new_items: list) -> tuple[bool, int]:
    """Menambahkan daftar akun baru ke produk (1 baris = 1 akun) dan mengupdate stok"""
    semua = muat_produk()
    for p in semua:
        if p["id"] == produk_id:
            if "items" not in p:
                p["items"] = []
            clean_items = [str(line).strip() for line in new_items if str(line).strip()]
            p["items"].extend(clean_items)
            p["stok"] = len(p["items"])
            simpan_produk(semua)
            return True, p["stok"]
    return False, 0

def ambil_dan_potong_stok(produk_id: int, qty: int) -> tuple[bool, list, str]:
    """Mengambil n akun pertama dari stok produk dan memotongnya secara permanen"""
    semua = muat_produk()
    for p in semua:
        if p["id"] == produk_id:
            items = p.get("items", [])
            if len(items) < qty:
                return False, [], f"Stok tidak mencukupi (sisa {len(items)}, diminta {qty})"
            
            terambil = items[:qty]
            sisa = items[qty:]
            p["items"] = sisa
            p["stok"] = len(sisa)
            simpan_produk(semua)
            return True, terambil, ""
    return False, [], "Produk tidak ditemukan"

def get_items_produk(produk_id: int) -> list:
    """Mengambil daftar akun yang tersedia untuk produk tertentu"""
    p = get_produk_by_id(produk_id)
    if p:
        return p.get("items", [])
    return []

def update_nama_produk(produk_id: int, new_nama: str) -> bool:
    """Mengubah nama produk"""
    semua = muat_produk()
    for p in semua:
        if p["id"] == produk_id:
            p["nama"] = new_nama.strip()
            simpan_produk(semua)
            return True
    return False

def update_harga_produk(produk_id: int, new_harga: int) -> bool:
    """Mengubah harga normal produk"""
    semua = muat_produk()
    for p in semua:
        if p["id"] == produk_id:
            p["harga"] = max(0, new_harga)
            simpan_produk(semua)
            return True
    return False

def update_deskripsi_produk(produk_id: int, new_deskripsi: str) -> bool:
    """Mengubah deskripsi produk"""
    semua = muat_produk()
    for p in semua:
        if p["id"] == produk_id:
            p["deskripsi"] = new_deskripsi.strip()
            simpan_produk(semua)
            return True
    return False

def update_promo(produk_id: int, harga_promo: int) -> bool:
    """Mengatur harga promo diskon produk (isi 0 untuk mematikan promo)"""
    semua = muat_produk()
    for p in semua:
        if p["id"] == produk_id:
            p["harga_promo"] = max(0, harga_promo)
            simpan_produk(semua)
            return True
    return False

def hapus_produk(produk_id: int) -> bool:
    """Menghapus produk dari katalog"""
    semua = muat_produk()
    awal = len(semua)
    semua = [p for p in semua if p["id"] != produk_id]
    if len(semua) < awal:
        simpan_produk(semua)
        return True
    return False

def get_total_stok() -> int:
    """Mengambil total akumulasi stok semua produk"""
    semua = muat_produk()
    return sum(p.get("stok", 0) for p in semua)

# ==================== PENGELOLAAN KATEGORI ====================

DEFAULT_KATEGORI = ["Umum", "AI & Software", "Streaming", "Akun Premium"]

def muat_kategori() -> list:
    """Memuat daftar kategori dari categories.json"""
    if os.path.exists(CATEGORIES_FILE):
        try:
            with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception as e:
            print(f"[ERROR MUAT KATEGORI]: {e}")
    # Default jika belum ada file atau kosong
    simpan_kategori(DEFAULT_KATEGORI)
    return list(DEFAULT_KATEGORI)

def simpan_kategori(daftar_kategori: list):
    """Menyimpan daftar kategori ke categories.json secara atomik"""
    temp_file = f"{CATEGORIES_FILE}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(daftar_kategori, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, CATEGORIES_FILE)
    except Exception as e:
        print(f"[ERROR SIMPAN KATEGORI]: {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

def get_semua_kategori() -> list:
    """Mengambil seluruh kategori produk"""
    return muat_kategori()

def tambah_kategori(nama: str) -> bool:
    """Menambahkan kategori baru ke daftar (menolak jika sudah ada atau kata kunci sistem)"""
    nama_clean = nama.strip()
    if not nama_clean:
        return False

    BLOCKED_NAMES = {
        "admin panel", "admin panel toko", "⚙️ admin panel toko",
        "menu utama", "daftar produk", "kelola produk", "lihat stok",
        "tambah produk", "kelola pengguna", "batal", "kembali"
    }
    if nama_clean.lower() in BLOCKED_NAMES:
        return False

    semua = muat_kategori()
    if any(k.lower() == nama_clean.lower() for k in semua):
        return False
    semua.append(nama_clean)
    simpan_kategori(semua)
    return True

def get_jumlah_produk_by_kategori(nama_kategori: str) -> int:
    """Menghitung berapa banyak produk yang terkait dengan kategori ini"""
    semua_produk = get_semua_produk()
    kat_clean = nama_kategori.strip().lower()
    return sum(1 for p in semua_produk if p.get("kategori", "Umum").strip().lower() == kat_clean)

def hapus_kategori(nama: str) -> tuple[bool, str]:
    """Menghapus kategori jika tidak sedang digunakan oleh produk apa pun"""
    nama_clean = nama.strip()
    semua = muat_kategori()

    # Cari kategori (case-insensitive)
    kat_target = None
    for k in semua:
        if k.lower() == nama_clean.lower():
            kat_target = k
            break

    if not kat_target:
        return False, "Kategori tidak ditemukan."

    # Validasi: kategori tidak boleh dihapus jika masih ada produk di dalamnya
    jml_produk = get_jumlah_produk_by_kategori(kat_target)
    if jml_produk > 0:
        return False, f"Kategori '{kat_target}' tidak dapat dihapus karena masih digunakan oleh {jml_produk} produk."

    semua = [k for k in semua if k.lower() != nama_clean.lower()]
    simpan_kategori(semua)
    return True, f"Kategori '{kat_target}' berhasil dihapus."

# ==================== PENGELOLAAN PESANAN (ORDERS & QRIS) ====================

def muat_orders() -> dict:
    """Memuat data transaksi/pesanan dari file JSON"""
    global orders
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                orders = json.load(f)
        except Exception as e:
            print(f"[ERROR MUAT ORDERS]: {e}")
            orders = {}
    else:
        orders = {}
    return orders

def simpan_orders():
    """Menyimpan data pesanan ke file JSON secara atomik"""
    temp_file = f"{ORDERS_FILE}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, ORDERS_FILE)
    except Exception as e:
        print(f"[ERROR SIMPAN ORDERS]: {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

def buat_order(user_id: int, username: str, first_name: str, produk: dict, jumlah: int, qris_payload: str, durasi_menit: int = 5) -> dict:
    """
    Membuat pesanan baru dengan batas waktu kedaluwarsa (default 5 menit).
    """
    import random
    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    expires_at = now + timedelta(minutes=durasi_menit)

    order_id = f"INV-{now.strftime('%y%m%d')}-{random.randint(1000, 9999)}"
    while order_id in orders:
        order_id = f"INV-{now.strftime('%y%m%d')}-{random.randint(1000, 9999)}"

    harga_satuan = produk.get("harga_promo", 0) if produk.get("harga_promo", 0) > 0 else produk.get("harga", 0)
    total_bayar = harga_satuan * jumlah

    order_data = {
        "order_id": order_id,
        "user_id": user_id,
        "username": username or "",
        "first_name": first_name or "",
        "produk_id": produk.get("id"),
        "nama_produk": produk.get("nama", "Produk"),
        "kategori": produk.get("kategori", "Umum"),
        "harga_satuan": harga_satuan,
        "jumlah": jumlah,
        "total_bayar": total_bayar,
        "qris_payload": qris_payload,
        "status": "PENDING",  # PENDING, WAITING_ADMIN, PAID, EXPIRED, CANCELLED
        "delivered_items": [],
        "paid_at": None,
        "created_at": now.strftime("%d/%m/%Y %H:%M:%S WIB"),
        "expires_at": expires_at.strftime("%d/%m/%Y %H:%M:%S WIB"),
        "expires_timestamp": expires_at.timestamp()
    }

    orders[order_id] = order_data
    simpan_orders()
    return order_data

def get_order(order_id: str) -> dict | None:
    """Mengambil data order berdasarkan ID"""
    return orders.get(order_id)

def get_order_aktif_user(user_id: int) -> dict | None:
    """Mengambil pesanan aktif milik user (WAITING_ADMIN atau PENDING yang belum expired)"""
    now_ts = datetime.now(timezone(timedelta(hours=7))).timestamp()
    user_orders = [o for o in orders.values() if o.get("user_id") == user_id]
    user_orders.sort(key=lambda x: x.get("expires_timestamp", 0), reverse=True)

    for o in user_orders:
        status = o.get("status")
        if status == "WAITING_ADMIN":
            return o
        if status == "PENDING":
            if o.get("expires_timestamp", 0) > now_ts:
                return o
            else:
                o["status"] = "EXPIRED"
                simpan_orders()
    return None

def update_status_order(order_id: str, status: str) -> bool:
    """Memperbarui status pesanan"""
    if order_id in orders:
        orders[order_id]["status"] = status
        simpan_orders()
        return True
    return False

def selesaikan_order(order_id: str) -> tuple[bool, dict | None, str]:
    """
    Menyelesaikan order saat pembayaran terverifikasi:
    Memotong stok akun dari produk dan menyimpan delivered_items ke invoice.
    """
    order = orders.get(order_id)
    if not order:
        return False, None, "Pesanan tidak ditemukan."
    if order.get("status") == "PAID":
        return True, order, "Pesanan sudah berstatus PAID sebelumnya."

    pid = order.get("produk_id")
    qty = order.get("jumlah", 1)

    sukses, items, err = ambil_dan_potong_stok(pid, qty)
    if not sukses:
        return False, order, f"Gagal memotong stok: {err}"

    waktu_sukses = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M:%S WIB")
    order["status"] = "PAID"
    order["delivered_items"] = items
    order["paid_at"] = waktu_sukses
    order["waktu_beli"] = waktu_sukses
    simpan_orders()

    # Perbarui data akumulasi transaksi user di profil jika ada
    uid_str = str(order.get("user_id"))
    if uid_str in users_profile:
        users_profile[uid_str]["total_belanja"] = users_profile[uid_str].get("total_belanja", 0) + order.get("total_bayar", 0)
        users_profile[uid_str]["total_order"] = users_profile[uid_str].get("total_order", 0) + 1
        simpan_users()

    return True, order, ""

def get_riwayat_pesanan_user(user_id: int) -> list:
    """Mengambil seluruh riwayat pesanan milik user yang sudah berstatus PAID (sukses dibeli), diurutkan dari yang terbaru"""
    daftar = [o for o in orders.values() if o.get("user_id") == user_id and o.get("status") == "PAID"]
    daftar.sort(key=lambda x: x.get("paid_at") or x.get("waktu_beli") or x.get("created_at") or "", reverse=True)
    return daftar

def cek_status_order_expired(order_id: str) -> tuple[bool, dict | None]:
    """Mengecek apakah pesanan sudah kedaluwarsa (> 5 menit) dan update statusnya jika ya"""
    order = orders.get(order_id)
    if not order:
        return True, None

    # Pesanan PAID, CANCELLED, dan WAITING_ADMIN tidak kedaluwarsa secara otomatis
    if order.get("status") in ["PAID", "CANCELLED", "WAITING_ADMIN"]:
        return False, order

    now_ts = datetime.now(timezone(timedelta(hours=7))).timestamp()
    if now_ts >= order.get("expires_timestamp", 0):
        if order.get("status") != "EXPIRED":
            order["status"] = "EXPIRED"
            simpan_orders()
        return True, order
    return False, order

def perpanjang_atau_reset_order(order_id: str, durasi_menit: int = 5, qris_payload: str = None) -> dict | None:
    """Mereset pesanan yang kedaluwarsa menjadi aktif kembali dengan timer 5 menit baru"""
    order = orders.get(order_id)
    if not order:
        return None
    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    expires_at = now + timedelta(minutes=durasi_menit)

    order["status"] = "PENDING"
    order["created_at"] = now.strftime("%d/%m/%Y %H:%M:%S WIB")
    order["expires_at"] = expires_at.strftime("%d/%m/%Y %H:%M:%S WIB")
    order["expires_timestamp"] = expires_at.timestamp()
    if qris_payload:
        order["qris_payload"] = qris_payload
    simpan_orders()
    return order

# Inisialisasi awal saat modul dimuat
muat_users()
muat_produk()
muat_kategori()
muat_orders()
