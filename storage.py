"""Modul penyimpanan: baca/tulis data lokasi ke file CSV secara permanen.

Seluruh operasi file memakai context manager `with open(...)`.
"""
import csv
import os
from datetime import datetime

from .models import FIELDS, Lokasi

DATA_AWAL = [
    (1, "SPKLU PLN UP3 Tanjung Karang", "Jl. Jenderal Sudirman, Tanjung Karang", "Tanjung Karang Pusat", "Toilet;Musala;Ruang Tunggu", 50, 2),
    (2, "SPKLU Mall Boemi Kedaton", "Jl. Pangeran Antasari, Kedaton", "Kedaton", "Toilet;Musala;Food Court;Parkir Luas", 50, 2),
    (3, "SPKLU Transmart Lampung", "Jl. Z.A. Pagar Alam, Rajabasa", "Rajabasa", "Toilet;Musala;Minimarket;Kafe", 25, 2),
    (4, "SPKLU Lampung City Mall", "Jl. Wolter Monginsidi, Teluk Betung", "Teluk Betung Utara", "Toilet;Musala;Food Court", 25, 1),
    (5, "SPKLU SPBU Way Halim", "Jl. Ryacudu, Way Halim", "Way Halim", "Toilet;Musala;Minimarket", 25, 2),
    (6, "SPKLU SPBU Sukarame", "Jl. Pramuka, Sukarame", "Sukarame", "Toilet;Musala;Warung Makan", 22, 1),
    (7, "SPKLU Kantor PLN Panjang", "Jl. Yos Sudarso, Panjang", "Panjang", "Toilet;Ruang Tunggu", 22, 1),
    (8, "SPKLU Hotel Bukit Randu", "Jl. Pangeran Antasari, Kedaton", "Kedaton", "Toilet;Restoran;Parkir Luas;Wi-Fi", 50, 2),
    (9, "SPKLU Pusat Oleh-oleh Kemiling", "Jl. Imam Bonjol, Kemiling", "Kemiling", "Toilet;Musala;Toko Oleh-oleh", 22, 1),
    (10, "SPKLU Rest Area Enggal", "Jl. Cut Nyak Dien, Enggal", "Enggal", "Toilet;Musala;Kafe;Wi-Fi", 50, 2),
]


class PenyimpananCSV:
    """Mengelola pembacaan dan penyimpanan data lokasi pada file CSV.

    Args:
        path: lokasi file CSV data.
        path_log: lokasi file log aktivitas (mode append).
    """

    def __init__(self, path: str, path_log: str | None = None):
        assert path, "Path file data tidak boleh kosong"
        self.path = path
        self.path_log = path_log or os.path.splitext(path)[0] + ".log"
        self.peringatan: list[str] = []  # pesan masalah saat memuat data

    def _buat_awal(self) -> list[Lokasi]:
        """Membuat file CSV baru berisi data awal (mode 'x' = hanya jika belum ada)."""
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        data = [Lokasi.from_dict(dict(zip(FIELDS, baris))) for baris in DATA_AWAL]
        try:
            with open(self.path, "x", newline="", encoding="utf-8") as f:
                self._tulis(f, data)
        except FileExistsError:
            self.simpan(data)
        return data

    @staticmethod
    def _tulis(f, data: list[Lokasi]) -> None:
        """Menulis header + seluruh baris ke objek file yang sudah terbuka."""
        penulis = csv.DictWriter(f, fieldnames=FIELDS)
        penulis.writeheader()
        for lokasi in data:
            penulis.writerow(lokasi.to_dict())

    def muat(self) -> list[Lokasi]:
        """Memuat seluruh data dari CSV.

        - File tidak ada  -> FileNotFoundError ditangani: dibuat dari data awal.
        - Baris rusak     -> ValueError/KeyError ditangani: baris dilewati + peringatan.
        - Header rusak    -> seluruh file diganti data awal.
        """
        self.peringatan = []
        hasil: list[Lokasi] = []
        try:
            with open(self.path, "r", newline="", encoding="utf-8") as f:
                pembaca = csv.DictReader(f)
                if pembaca.fieldnames != FIELDS:
                    raise KeyError("Header CSV tidak sesuai")
                for no, baris in enumerate(pembaca, start=2):
                    try:
                        hasil.append(Lokasi.from_dict(baris))
                    except (ValueError, KeyError, TypeError):
                        self.peringatan.append(f"Baris {no} rusak dan dilewati.")
        except FileNotFoundError:
            self.peringatan.append("File data tidak ditemukan; dibuat dari data awal.")
            return self._buat_awal()
        except (KeyError, csv.Error, UnicodeDecodeError):
            self.peringatan.append("File data rusak; dipulihkan dari data awal.")
            return self._buat_awal()
        hasil.sort(key=lambda l: l.id)  
        return hasil

    def simpan(self, data: list[Lokasi]) -> None:
        """Menyimpan seluruh data ke CSV (mode 'w' = timpa file)."""
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            self._tulis(f, data)

    def catat_log(self, pesan: str) -> None:
        """Menambahkan satu baris ke file log aktivitas (mode 'a' = append)."""
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.path_log, "a", encoding="utf-8") as f:
            f.write(f"[{waktu}] {pesan}\n")
