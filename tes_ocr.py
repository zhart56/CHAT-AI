import easyocr
import torch
import os

print(f"Versi PyTorch yang digunakan: {torch.__version__}")
print("Mencoba menginisialisasi EasyOCR Reader...")

try:
    # Inisialisasi reader, paksa menggunakan CPU untuk tes ini agar lebih stabil
    reader = easyocr.Reader(['en', 'id'], gpu=False)
    print("Reader berhasil diinisialisasi.")

    # --- PENTING: GANTI DENGAN PATH LENGKAP KE GAMBAR ANDA ---
    # Cara mendapatkan path lengkap:
    # 1. Tahan tombol Shift, lalu klik kanan pada file gambar Anda.
    # 2. Pilih "Copy as path".
    # 3. Tempel di bawah ini di antara tanda kutip.
    path_gambar = r"c:\Users\ardra\OneDrive\Pictures\Screenshots\Screenshot 2025-04-13 172335.png"

    # Periksa apakah file ada
    if not os.path.exists(path_gambar):
        print(f"\n--- ERROR ---")
        print(f"File tidak ditemukan di path: {path_gambar}")
        print("Pastikan Anda sudah mengganti placeholder dengan path yang benar.")
        print("---------------------")
    else:
        print(f"Mencoba membaca gambar di: {path_gambar}")

        # Panggil readtext
        hasil = reader.readtext(path_gambar)

        # Jika berhasil, cetak hasilnya
        print("\n--- SUKSES! HASIL OCR ---")
        print(hasil)
        print("------------------------")

except Exception as e:
    print(f"\n--- TERJADI ERROR ---")
    print(f"Error: {e}")
    print("---------------------")