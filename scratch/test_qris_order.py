import os
import sys
import json
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import qris
import database
import ui

def run_tests():
    print("=== TEST 1: Config ===")
    assert config.GOPAY_QRIS_STRING, "GOPAY_QRIS_STRING is empty!"
    assert config.ORDERS_FILE.endswith("orders.json"), f"ORDERS_FILE invalid: {config.ORDERS_FILE}"
    print("[PASS] Config QRIS & Orders file OK")
    print("Base QRIS:", config.GOPAY_QRIS_STRING[:30] + "...")

    print("\n=== TEST 2: Dynamic QRIS Generator ===")
    nominal = 25000
    dyn = qris.generate_dynamic_qris(nominal=nominal)
    print("Generated dynamic QRIS:", dyn)
    assert dyn.startswith("000201010212"), "Must start with 000201010212 (dynamic)"
    assert f"54{len(str(nominal)):02d}{nominal}" in dyn, "Must contain tag 54 nominal"
    assert "AI Barokah" in dyn, "Must contain merchant name"
    print("[PASS] Dynamic QRIS format OK")

    print("\n=== TEST 3: QR Image Bytes Rendering ===")
    img_bytes = qris.buat_gambar_qris_bytes(dyn)
    assert len(img_bytes) > 500, f"Image bytes too small: {len(img_bytes)}"
    assert img_bytes[:8] == b'\x89PNG\r\n\x1a\n', "Must be valid PNG header"
    print(f"[PASS] PNG Image generated ({len(img_bytes)} bytes)")

    print("\n=== TEST 4: Database Order Lifecycle ===")
    produk = {
        "id": 999,
        "nama": "Test Akun Premium",
        "kategori": "Streaming",
        "harga": 30000,
        "harga_promo": 25000,
        "stok": 10,
        "deskripsi": "Akun streaming test"
    }
    test_user_id = 123456789
    order = database.buat_order(
        user_id=test_user_id,
        username="tester",
        first_name="Test User",
        produk=produk,
        jumlah=2,
        qris_payload=dyn,
        durasi_menit=5
    )
    assert order["order_id"].startswith("INV-"), f"Invalid order_id: {order['order_id']}"
    assert order["total_bayar"] == 50000, f"Expected 50000, got {order['total_bayar']}"
    assert order["status"] == "PENDING"
    print(f"[PASS] Order created: {order['order_id']} Total: Rp {order['total_bayar']:,}")

    # Active order lookup
    active = database.get_order_aktif_user(test_user_id)
    assert active is not None and active["order_id"] == order["order_id"], "Active order not found!"
    print(f"[PASS] Active order retrieved: {active['order_id']}")

    # Expire check
    is_exp, updated = database.cek_status_order_expired(order["order_id"])
    assert not is_exp, "Newly created order should not be expired yet!"

    # Simulate expiration
    database.orders[order["order_id"]]["expires_timestamp"] = (datetime.now(timezone(timedelta(hours=7))) - timedelta(seconds=10)).timestamp()
    is_exp, updated = database.cek_status_order_expired(order["order_id"])
    assert is_exp, "Past-due order should be marked expired!"
    assert updated["status"] == "EXPIRED"
    print("[PASS] Expiry logic confirmed")

    # Test Regeneration / Reset of Expired Order
    renewed = database.perpanjang_atau_reset_order(order["order_id"], durasi_menit=5)
    assert renewed["status"] == "PENDING"
    assert renewed["expires_timestamp"] > datetime.now(timezone(timedelta(hours=7))).timestamp()
    print("[PASS] Regeneration/Reset logic confirmed")

    # Clean up test order
    if order["order_id"] in database.orders:
        del database.orders[order["order_id"]]
        database.simpan_orders()

    print("\n=== TEST 5: UI Invoice & Product Detail ===")
    caption, markup = ui.buat_tampilan_invoice_qris(order)
    assert "INVOICE PEMBAYARAN QRIS" in caption
    assert "AI Barokah, GN PUTRI" in caption
    assert "5 Menit" in caption
    print("[PASS] Invoice UI rendered properly")

    # Test Expired Invoice UI
    expired_order = dict(order)
    expired_order["status"] = "EXPIRED"
    exp_caption, exp_markup = ui.buat_tampilan_invoice_qris(expired_order)
    assert "TRANSAKSI GAGAL (KEDALUWARSA)" in exp_caption, "Must state transaction failed when expired"
    has_ulang_btn = False
    for row in exp_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("ulang_order_"):
                has_ulang_btn = True
    assert has_ulang_btn, "Expired invoice must have 'ulang_order_' button to regenerate QR!"
    print("[PASS] Expired invoice UI has regenerate QR button")

    p_pesan, p_markup = ui.buat_tampilan_detail_produk(produk, jumlah=2)
    tombol_qris = False
    has_manual_admin_btn = False
    for row in p_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("beli_qris_"):
                tombol_qris = True
            if btn.text and "Pesan Manual" in btn.text:
                has_manual_admin_btn = True
    assert tombol_qris, "Tombol beli_qris_ not found in product detail!"
    assert not has_manual_admin_btn, "Tombol Pesan Manual ke Admin harus dihilangkan!"
    print("[PASS] Product detail has QRIS payment button and NO manual admin button")

    print("\nALL TESTS PASSED SUCCESSFULLY! OK")

if __name__ == "__main__":
    run_tests()
