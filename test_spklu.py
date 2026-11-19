"""Unit test (unittest) untuk logika data, searching, sorting, validasi, dan file handling.

Semua pengujian berjalan TANPA UI. Jalankan:  python -m unittest discover -v
"""
import os
import tempfile
import unittest

from spklu.models import Lokasi
from spklu.services import LokasiService, merge_sort
from spklu.storage import PenyimpananCSV
from spklu.validasi import ValidasiError, validasi_lokasi


def buat_data():
    """Data contoh kecil untuk pengujian."""
    return [
        Lokasi(1, "SPKLU Alpha", "Jl. A", "Kedaton", "Toilet;Musala", 50, 2),
        Lokasi(2, "SPKLU Charlie", "Jl. C", "Rajabasa", "Kafe", 22, 1),
        Lokasi(3, "SPKLU Bravo", "Jl. B", "Kedaton", "Toilet", 25, 2),
        Lokasi(4, "SPKLU Delta", "Jl. D", "Panjang", "Wi-Fi", 50, 1),
    ]


class TestLokasiService(unittest.TestCase):
    """Menguji pengolahan data, pencarian, dan pengurutan pada LokasiService."""

    def setUp(self):
        self.service = LokasiService(data=buat_data())

    def test_cari_kata_kunci_nama_dan_kecamatan(self):
        """Pencarian substring tidak peka huruf besar/kecil pada nama & kecamatan."""
        self.assertEqual([l.id for l in self.service.cari("bravo")], [3])
        self.assertEqual([l.id for l in self.service.cari("KEDATON")], [1, 3])
        self.assertEqual(self.service.cari("tidak-ada"), [])

    def test_cari_id_binary_search(self):
        """Binary search menemukan id yang ada dan mengembalikan None bila tidak ada."""
        self.assertEqual(self.service.cari_id(3).nama, "SPKLU Bravo")
        self.assertIsNone(self.service.cari_id(99))

    def test_urutkan_nama_naik_dan_turun(self):
        """Merge sort mengurutkan teks naik & turun."""
        naik = [l.nama for l in self.service.urutkan("nama")]
        self.assertEqual(naik, ["SPKLU Alpha", "SPKLU Bravo", "SPKLU Charlie", "SPKLU Delta"])
        turun = [l.id for l in self.service.urutkan("nama", menurun=True)]
        self.assertEqual(turun, [4, 2, 3, 1])

    def test_merge_sort_stabil(self):
        """Elemen berkunci sama harus mempertahankan urutan semula (stabil)."""
        hasil = [l.id for l in merge_sort(buat_data(), key=lambda l: l.daya_kw)]
        self.assertEqual(hasil, [2, 3, 1, 4])  

    def test_urutkan_kolom_tidak_valid(self):
        """Kolom tak dikenal memicu ValueError."""
        with self.assertRaises(ValueError):
            self.service.urutkan("warna")

    def test_filter_kwargs_dan_hitung_total_args(self):
        """**kwargs pada filter dan *args pada agregat bekerja benar."""
        hasil = self.service.filter_lokasi(kecamatan="Kedaton", min_daya=50)
        self.assertEqual([l.id for l in hasil], [1])
        total = self.service.hitung_total("daya_kw", "jumlah_port")
        self.assertEqual(total, {"daya_kw": 147, "jumlah_port": 6})

    def test_tambah_dan_hapus(self):
        """Tambah memberi id baru berurutan; hapus menghilangkan data."""
        baru = self.service.tambah(nama="SPKLU Echo", alamat="Jl. E", kecamatan="Sukarame",
                                   fasilitas="Toilet", daya_kw="25", jumlah_port="1")
        self.assertEqual(baru.id, 5)
        self.service.hapus(5)
        self.assertIsNone(self.service.cari_id(5))
        with self.assertRaises(LookupError):
            self.service.hapus(5)


class TestValidasi(unittest.TestCase):
    """Menguji aturan validasi input (raise ValidasiError)."""

    VALID = dict(nama="X", alamat="Jl. X", kecamatan="Kedaton", fasilitas="Toilet", daya_kw="25", jumlah_port="2")

    def test_data_valid_lolos(self):
        self.assertEqual(validasi_lokasi(**self.VALID)["daya_kw"], 25)

    def test_field_wajib_kosong(self):
        with self.assertRaises(ValidasiError):
            validasi_lokasi(**{**self.VALID, "nama": "   "})

    def test_angka_negatif_atau_bukan_angka(self):
        with self.assertRaises(ValidasiError):
            validasi_lokasi(**{**self.VALID, "daya_kw": "-5"})
        with self.assertRaises(ValidasiError):
            validasi_lokasi(**{**self.VALID, "jumlah_port": "abc"})


class TestPenyimpanan(unittest.TestCase):
    """Menguji file handling: simpan-muat ulang, file hilang, dan data rusak."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "data.csv")

    def tearDown(self):
        self.tmp.cleanup()

    def test_file_hilang_dibuat_dari_data_awal(self):
        """FileNotFoundError ditangani: file dibuat otomatis, tidak crash."""
        storage = PenyimpananCSV(self.path)
        data = storage.muat()
        self.assertTrue(os.path.exists(self.path))
        self.assertGreaterEqual(len(data), 10)
        self.assertTrue(storage.peringatan)

    def test_simpan_lalu_muat_ulang(self):
        """Data tetap ada setelah disimpan lalu dimuat kembali (permanen)."""
        storage = PenyimpananCSV(self.path)
        LokasiService(storage).tambah(nama="SPKLU Uji", alamat="Jl. Uji", kecamatan="Enggal",
                                      fasilitas="Toilet", daya_kw=25, jumlah_port=1)
        nama = [l.nama for l in LokasiService(PenyimpananCSV(self.path)).semua]
        self.assertIn("SPKLU Uji", nama)

    def test_baris_rusak_dilewati(self):
        """ValueError pada baris corrupt ditangani: baris dilewati, sisanya dimuat."""
        PenyimpananCSV(self.path).muat()  
        with open(self.path, "a", encoding="utf-8") as f:
            f.write("abc,Rusak,Jl,Kedaton,Toilet,xx,yy\n")
        storage = PenyimpananCSV(self.path)
        data = storage.muat()
        self.assertEqual(len(data), 10)
        self.assertTrue(any("rusak" in p for p in storage.peringatan))


if __name__ == "__main__":
    unittest.main(verbosity=2)
