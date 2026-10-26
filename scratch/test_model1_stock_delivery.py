import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import ui

def test_model1():
    print("=== TEST 1: Tambah Produk dengan Akun (Model 1) ===")
    sample_accounts = [
        "canva_user1@gmail.com | pass123 | PIN: 1111",
        "canva_user2@gmail.com | pass456 | PIN: 2222",
        "canva_user3@gmail.com | pass789 | PIN: 3333"
    ]
    prod = database.tambah_produk(
        nama="Test Akun Canva Model 1",
        harga=15000,
        stok=0,
        deskripsi="Akun garansi 30 hari",
        kategori="Akun",
        items=sample_accounts
    )
    pid = prod["id"]
    assert prod["stok"] == 3, f"Expected stok 3, got {prod['stok']}"
    assert len(prod["items"]) == 3, "Items count must be 3"
    print(f"[PASS] Produk #{pid} dibuat dengan {prod['stok']} akun.")

    print("\n=== TEST 2: Tambah / Restock Akun Baru ===")
    new_accounts = [
        "canva_user4@gmail.com | pass999 | PIN: 4444",
        "canva_user5@gmail.com | pass888 | PIN: 5555"
    ]
    sukses, total_stok = database.tambah_stok_items(pid, new_accounts)
    assert sukses and total_stok == 5, f"Expected total stok 5, got {total_stok}"
    print(f"[PASS] Berhasil restock. Total stok sekarang: {total_stok}")

    print("\n=== TEST 3: Order & Pemotongan Stok Otomatis (Fulfillment) ===")
    order = database.buat_order(
        user_id=987654321,
        username="buyer_test",
        first_name="Pembeli Test",
        produk=prod,
        jumlah=2,
        qris_payload="000201...",
        durasi_menit=5
    )
    oid = order["order_id"]
    assert order["status"] == "PENDING"

    # Selesaikan pesanan & potong stok otomatis
    sukses_selesai, upd_order, err = database.selesaikan_order(oid)
    assert sukses_selesai, f"Gagal selesaikan order: {err}"
    assert upd_order["status"] == "PAID", f"Expected PAID, got {upd_order['status']}"
    assert len(upd_order["delivered_items"]) == 2, f"Expected 2 delivered items, got {len(upd_order['delivered_items'])}"
    assert upd_order["delivered_items"][0] == "canva_user1@gmail.com | pass123 | PIN: 1111"
    assert upd_order["delivered_items"][1] == "canva_user2@gmail.com | pass456 | PIN: 2222"
    print(f"[PASS] Order {oid} berstatus PAID.")
    print("Akun yang diserahkan ke pembeli:")
    for it in upd_order["delivered_items"]:
        print(" -", it)

    # Cek sisa stok produk di database
    prod_check = database.get_produk_by_id(pid)
    assert prod_check["stok"] == 3, f"Expected sisa stok 3, got {prod_check['stok']}"
    assert prod_check["items"][0] == "canva_user3@gmail.com | pass789 | PIN: 3333"
    print(f"[PASS] Stok produk berkurang tepat 2. Sisa stok: {prod_check['stok']} akun.")

    print("\n=== TEST 4: UI Invoice PAID & Tampilan Akun Admin ===")
    caption_paid, markup_paid = ui.buat_tampilan_invoice_qris(upd_order)
    assert "PEMBAYARAN DITERIMA & PESANAN SELESAI" in caption_paid
    assert "canva_user1@gmail.com" in caption_paid
    assert "canva_user2@gmail.com" in caption_paid
    print("[PASS] Invoice PAID memuat akun yang diserahkan.")

    pesan_lihat, markup_lihat = ui.buat_tampilan_admin_lihat_akun(prod_check)
    assert "DAFTAR AKUN / STOK PRODUK" in pesan_lihat
    assert "canva_user3@gmail.com" in pesan_lihat
    print("[PASS] Tampilan admin lihat akun berfungsi normal.")

    # Cleanup test product & order
    semua_p = database.muat_produk()
    semua_p = [p for p in semua_p if p["id"] != pid]
    database.simpan_produk(semua_p)
    if oid in database.orders:
        del database.orders[oid]
        database.simpan_orders()

    print("\nALL MODEL 1 STOCK & DELIVERY TESTS PASSED SUCCESSFULLY! OK")

if __name__ == "__main__":
    test_model1()
