"""
Modul Generator QRIS Dinamis (EMVCo) untuk GoPay Merchant / QRIS Nasional
Mendukung konversi QRIS Statis menjadi Dinamis dengan nominal tagihan spesifik,
kalkulasi checksum CRC-16 otomatis, serta rendering gambar QR Code.
"""

import io
import re
import random
from datetime import datetime, timezone, timedelta
import qrcode
from config import GOPAY_QRIS_STRING

def hitung_crc16(data: str) -> str:
    """
    Menghitung checksum CRC-16/CCITT-FALSE untuk payload QRIS EMVCo.
    Polinomial: 0x1021, Nilai awal: 0xFFFF.
    """
    crc = 0xFFFF
    for byte in data.encode("latin-1"):
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"

def generate_dynamic_qris(base_qris: str = None, nominal: int = 0) -> str:
    """
    Mengubah payload QRIS Statis menjadi QRIS Dinamis dengan menyisipkan nominal (Tag 54)
    dan menghitung ulang checksum CRC16 (Tag 63).
    
    :param base_qris: String QRIS statis (jika None, mengambil dari config.GOPAY_QRIS_STRING)
    :param nominal: Jumlah tagihan (integer, misal: 25000)
    :return: String QRIS Dinamis lengkap
    """
    raw = (base_qris or GOPAY_QRIS_STRING).strip()
    if not raw:
        raise ValueError("String QRIS Dasar (GOPAY_QRIS_STRING) belum dikonfigurasikan di .env!")

    # 1. Ubah Point of Initiation Method (Tag 01) dari 11 (Statis) menjadi 12 (Dinamis)
    # Tag 01 format: 010211 -> 010212
    if "010211" in raw:
        payload = raw.replace("010211", "010212", 1)
    else:
        payload = raw

    # 2. Hapus Tag 63 (CRC) lama dari ujung string jika ada
    # Format Tag 63: 6304XXXX
    idx_crc = payload.rfind("6304")
    if idx_crc != -1:
        payload = payload[:idx_crc]

    # 3. Hapus Tag 54 lama jika sebelumnya sudah ada dalam string
    # Tag 54 format: 54[panjang:2 digit][nominal]
    payload = re.sub(r"54\d{2}\d+", "", payload)

    # 4. Format Tag 54 baru jika nominal > 0
    str_nominal = str(int(nominal)) if nominal > 0 else "0"
    tag_54 = f"54{len(str_nominal):02d}{str_nominal}"

    # 5. Sisipkan Tag 54 sebelum Tag 58 (Country Code, misal: 5802ID)
    idx_58 = payload.find("5802")
    if idx_58 != -1:
        payload_with_amount = payload[:idx_58] + tag_54 + payload[idx_58:]
    else:
        payload_with_amount = payload + tag_54

    # 6. Tambahkan awalan Tag 63 ('6304') dan hitung CRC16 baru
    payload_to_sign = payload_with_amount + "6304"
    crc_hex = hitung_crc16(payload_to_sign)

    return payload_to_sign + crc_hex

def buat_gambar_qris_bytes(payload: str, box_size: int = 8, border: int = 2) -> bytes:
    """
    Membuat gambar QR Code dari string payload QRIS dan mengembalikannya dalam bentuk bytes PNG.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio.getvalue()

def buat_kode_invoice(prefix: str = "INV") -> str:
    """
    Menghasilkan kode invoice unik berdasarkan tanggal dan nomor acak.
    Contoh: INV-261012-7890
    """
    wib = timezone(timedelta(hours=7))
    tgl_str = datetime.now(wib).strftime("%y%m%d")
    acak = random.randint(1000, 9999)
    return f"{prefix}-{tgl_str}-{acak}"
