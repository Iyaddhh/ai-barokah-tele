import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
import ui

def test_riwayat():
    test_uid = 999888777
    test_prod = {
        "id": 9999,
        "nama": "Akun Netflix Premium Test",
        "kategori": "Streaming",
        "harga": 50000,
        "harga_promo": 0,
        "stok": 5,
        "items": ["netflix_test_1@gmail.com | pass1"]
    }
    
    # Buat order baru
    order = database.buat_order(
        user_id=test_uid,
        username="test_buyer",
        first_name="Buyer",
        produk=test_prod,
        jumlah=1,
        qris_payload="000201...",
        durasi_menit=5
    )
    order_id = order["order_id"]
    print(f"[TEST 1] Order dibuat: {order_id}, status: {order['status']}")

    # Selesaikan order (PAID)
    order["delivered_items"] = ["netflix_test_1@gmail.com | pass1"]
    order["status"] = "PAID"
    import datetime
    now_wib = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S WIB")
    order["paid_at"] = now_wib
    order["waktu_beli"] = now_wib
    database.orders[order_id] = order
    database.simpan_orders()
    print(f"[TEST 2] Order di-mark PAID dengan waktu beli: {now_wib}")

    # Cek get_riwayat_pesanan_user
    riwayat = database.get_riwayat_pesanan_user(test_uid)
    assert len(riwayat) >= 1, "Riwayat harus memiliki minimal 1 pesanan"
    matched = [o for o in riwayat if o["order_id"] == order_id]
    assert len(matched) == 1, "Pesanan harus ditemukan di riwayat"
    saved_order = matched[0]
    assert saved_order["nama_produk"] == "Akun Netflix Premium Test"
    assert saved_order["waktu_beli"] == now_wib
    assert saved_order["paid_at"] == now_wib
    print(f"[TEST 3] get_riwayat_pesanan_user PASS. Produk: {saved_order['nama_produk']}, Waktu: {saved_order['waktu_beli']}")

    # Cek UI buat_tampilan_riwayat_pesanan
    pesan, markup = ui.buat_tampilan_riwayat_pesanan(test_uid)
    assert "Akun Netflix Premium Test" in pesan
    assert now_wib in pesan
    assert order_id in pesan
    print("[TEST 4] buat_tampilan_riwayat_pesanan PASS memuat nama produk dan waktu beli!")

    # Cleanup
    if order_id in database.orders:
        del database.orders[order_id]
        database.simpan_orders()
    print("[ALL RIWAYAT PESANAN TESTS PASSED OK]")

if __name__ == "__main__":
    test_riwayat()
