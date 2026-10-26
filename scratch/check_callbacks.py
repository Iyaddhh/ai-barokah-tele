import re

with open('ui.py', encoding='utf-8') as f:
    ui_content = f.read()

with open('handlers/callbacks.py', encoding='utf-8') as f:
    cb_content = f.read()

callbacks_in_ui = re.findall(r'callback_data=["\']([^"\']+)["\']', ui_content)
callbacks_fmt = re.findall(r'callback_data=f["\']([^"\']+)["\']', ui_content)

print(f'Total static callbacks in ui: {len(callbacks_in_ui)}')
print(f'Total formatted callbacks in ui: {len(callbacks_fmt)}')

prefixes = [
    'katalog_hal_', 'pelanggan_kat_hal_', 'pelanggan_kat_pilih_',
    'admin_stok_hal_', 'admin_kat_menu_hal_', 'admin_kat_del_hal_',
    'admin_users_hal_', 'admin_edit_hal_', 'admin_hapus_hal_', 'admin_promo_hal_',
    'produk_detail_', 'beli_kurang_', 'beli_tambah_', 'beli_qris_',
    'konfirmasi_order_', 'cek_order_', 'batal_order_', 'ulang_order_',
    'admin_approve_order_', 'admin_reject_order_', 'admin_stok_detail_',
    'admin_detail_stok_tambah_', 'admin_detail_stok_kurang_', 'admin_restock_',
    'admin_lihat_akun_', 'admin_kat_del_', 'admin_user_detail_',
    'admin_user_blokir_', 'admin_user_unblock_', 'admin_edit_pilih_',
    'admin_hapus_produk_', 'admin_stok_tambah_', 'admin_stok_kurang_',
    'admin_stok_input_', 'admin_konfirm_hapus_', 'admin_edit_nama_',
    'admin_edit_harga_', 'admin_edit_deskripsi_', 'admin_pilih_promo_',
    'admin_promo_mati_', 'admin_promo_input_', 'wizard_kat_hal_',
    'wizard_pilih_kat_'
]

unhandled = []
for cb in set(callbacks_in_ui):
    if cb in cb_content or f'"{cb}"' in cb_content:
        continue
    matched = any(cb.startswith(p) for p in prefixes)
    if not matched:
        unhandled.append(cb)

print('Unhandled static callbacks:', unhandled)

unhandled_fmt = []
for cb in set(callbacks_fmt):
    prefix = cb.split('{')[0]
    matched = prefix in cb_content or any(prefix.startswith(p) for p in prefixes)
    if not matched:
        unhandled_fmt.append(cb)

print('Unhandled formatted callbacks:', unhandled_fmt)
