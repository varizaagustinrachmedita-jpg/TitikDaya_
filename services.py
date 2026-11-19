"""Modul service: logika pengolahan data (CRUD, searching, sorting, filter, agregat).

Tidak bergantung pada UI sehingga bisa diuji terpisah (lihat tests/).
"""
from .models import Lokasi
from .storage import PenyimpananCSV
from .validasi import validasi_lokasi

KOLOM_KUNCI = {
    "id": lambda l: l.id,
    "nama": lambda l: l.nama.lower(),
    "alamat": lambda l: l.alamat.lower(),
    "kecamatan": lambda l: l.kecamatan.lower(),
    "fasilitas": lambda l: l.fasilitas.lower(),
    "daya_kw": lambda l: l.daya_kw,
    "jumlah_port": lambda l: l.jumlah_port,
}


def _gabung(kiri, kanan, key, reverse):
    """Menggabungkan dua list yang sudah terurut (langkah 'merge' pada Merge Sort)."""
    hasil, i, j = [], 0, 0
    while i < len(kiri) and j < len(kanan):
        a, b = key(kiri[i]), key(kanan[j])
        # Memakai <= / >= (bukan < / >) agar sort bersifat STABIL.
        ambil_kiri = a >= b if reverse else a <= b
        if ambil_kiri:
            hasil.append(kiri[i]); i += 1
        else:
            hasil.append(kanan[j]); j += 1
    hasil.extend(kiri[i:])
    hasil.extend(kanan[j:])
    return hasil


def merge_sort(data, key=lambda x: x, reverse=False):
    """Algoritma Merge Sort (divide & conquer), kompleksitas O(n log n).

    Args:
        data: list yang akan diurutkan (tidak diubah).
        key: fungsi (lambda) pengambil nilai pembanding.
        reverse: True untuk urutan menurun.

    Returns:
        list baru yang sudah terurut.
    """
    if len(data) <= 1:
        return list(data)
    tengah = len(data) // 2
    kiri = merge_sort(data[:tengah], key, reverse)
    kanan = merge_sort(data[tengah:], key, reverse)
    return _gabung(kiri, kanan, key, reverse)


class LokasiService:
    """Mengelola kumpulan lokasi SPKLU di memori dan menyinkronkannya ke penyimpanan.

    Args:
        storage: objek PenyimpananCSV (opsional; bila None data tidak disimpan ke file,
            berguna untuk unit test).
        data: daftar awal Lokasi bila storage tidak dipakai.
    """

    def __init__(self, storage: PenyimpananCSV | None = None, data: list[Lokasi] | None = None):
        self.storage = storage
        self._data: list[Lokasi] = storage.muat() if storage else sorted(data or [], key=lambda l: l.id)

    @property
    def semua(self) -> list[Lokasi]:
        """Salinan seluruh data (urut berdasarkan id)."""
        return list(self._data)

    def _simpan(self, pesan: str) -> None:
        """Menyimpan perubahan + mencatat log, bila storage tersedia."""
        if self.storage:
            self.storage.simpan(self._data)
            self.storage.catat_log(pesan)

    def cari_id(self, id_lokasi: int) -> Lokasi | None:
        """Binary Search berdasarkan id, O(log n). Data selalu terurut menurut id."""
        kiri, kanan = 0, len(self._data) - 1
        while kiri <= kanan:
            tengah = (kiri + kanan) // 2
            nilai = self._data[tengah].id
            if nilai == id_lokasi:
                return self._data[tengah]
            if nilai < id_lokasi:
                kiri = tengah + 1
            else:
                kanan = tengah - 1
        return None

    def cari(self, kata: str, data: list[Lokasi] | None = None, kolom=("nama", "kecamatan")) -> list[Lokasi]:
        """Linear Search kata kunci (substring, tidak peka huruf besar/kecil).

        Args:
            kata: kata kunci; kosong = kembalikan semua data.
            data: sumber data (default seluruh data).
            kolom: kolom yang dicari (default nama & kecamatan).
        """
        sumber = self._data if data is None else data
        kata = kata.strip().lower()
        if not kata:
            return list(sumber)
        return [l for l in sumber if any(kata in str(getattr(l, k)).lower() for k in kolom)]


    def urutkan(self, kolom: str, menurun: bool = False, data: list[Lokasi] | None = None) -> list[Lokasi]:
        """Mengurutkan data berdasarkan kolom memakai Merge Sort.

        Raises:
            ValueError: jika nama kolom tidak dikenal.
        """
        if kolom not in KOLOM_KUNCI:
            raise ValueError(f"Kolom '{kolom}' tidak dapat diurutkan.")
        sumber = self._data if data is None else data
        return merge_sort(sumber, key=KOLOM_KUNCI[kolom], reverse=menurun)

    def filter_lokasi(self, data: list[Lokasi] | None = None, **kriteria) -> list[Lokasi]:
        """Menyaring data dengan kriteria fleksibel (**kwargs).

        Kriteria yang didukung: kecamatan (teks), min_daya (angka),
        min_port (angka), fasilitas (teks, substring).
        Kriteria kosong/None diabaikan. Contoh: filter_lokasi(kecamatan="Kedaton", min_daya=50).
        """
        hasil = self._data if data is None else data
        aturan = {  
            "kecamatan": lambda l, v: l.kecamatan == v,
            "min_daya": lambda l, v: l.daya_kw >= int(v),
            "min_port": lambda l, v: l.jumlah_port >= int(v),
            "fasilitas": lambda l, v: v.lower() in l.fasilitas.lower(),
        }
        for nama, nilai in kriteria.items():
            if nilai in (None, "", "Semua"):
                continue
            if nama not in aturan:
                raise ValueError(f"Kriteria filter '{nama}' tidak dikenal.")
            hasil = [l for l in hasil if aturan[nama](l, nilai)]
        return list(hasil)

    def hitung_total(self, *kolom: str, data: list[Lokasi] | None = None) -> dict:
        """Menjumlahkan kolom numerik (*args). Contoh: hitung_total("daya_kw", "jumlah_port").

        Raises:
            ValueError: jika tidak ada kolom / kolom bukan numerik.
        """
        if not kolom:
            raise ValueError("Minimal satu nama kolom harus diberikan.")
        for k in kolom:
            if k not in ("daya_kw", "jumlah_port"):
                raise ValueError(f"Kolom '{k}' bukan kolom numerik.")
        sumber = self._data if data is None else data
        return {k: sum(getattr(l, k) for l in sumber) for k in kolom}

    
    def tambah(self, **data) -> Lokasi:
        """Menambah lokasi baru (divalidasi dulu). Raises ValidasiError bila tidak valid."""
        bersih = validasi_lokasi(**data)
        id_baru = (self._data[-1].id + 1) if self._data else 1  # id terbesar + 1 (tetap terurut)
        lokasi = Lokasi(id=id_baru, **bersih)
        self._data.append(lokasi)
        self._simpan(f"TAMBAH id={id_baru} '{lokasi.nama}'")
        return lokasi

    def ubah(self, id_lokasi: int, **data) -> Lokasi:
        """Mengubah data lokasi. Raises LookupError bila id tidak ada."""
        lokasi = self.cari_id(id_lokasi)
        if lokasi is None:
            raise LookupError(f"Lokasi dengan id {id_lokasi} tidak ditemukan.")
        for k, v in validasi_lokasi(**data).items():
            setattr(lokasi, k, v)
        self._simpan(f"UBAH id={id_lokasi}")
        return lokasi

    def hapus(self, id_lokasi: int) -> None:
        """Menghapus lokasi berdasarkan id. Raises LookupError bila id tidak ada."""
        lokasi = self.cari_id(id_lokasi)
        if lokasi is None:
            raise LookupError(f"Lokasi dengan id {id_lokasi} tidak ditemukan.")
        self._data.remove(lokasi)
        self._simpan(f"HAPUS id={id_lokasi} '{lokasi.nama}'")
