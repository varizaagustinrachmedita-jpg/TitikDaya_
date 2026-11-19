"""Modul validasi input.

Dipisahkan dari UI & service agar aturan validasi mudah diuji dan dipakai ulang.
"""

KECAMATAN = [
    "Bumi Waras", "Enggal", "Kedamaian", "Kedaton", "Kemiling",
    "Labuhan Ratu", "Langkapura", "Panjang", "Rajabasa", "Sukabumi",
    "Sukarame", "Tanjung Karang Barat", "Tanjung Karang Pusat",
    "Tanjung Karang Timur", "Tanjung Senang", "Teluk Betung Barat",
    "Teluk Betung Selatan", "Teluk Betung Timur", "Teluk Betung Utara",
    "Way Halim",
]


FIELD_WAJIB = ("nama", "alamat", "kecamatan", "fasilitas")


class ValidasiError(ValueError):
    """Error khusus untuk input yang tidak memenuhi aturan validasi."""


def validasi_lokasi(**data):
    """Memvalidasi data lokasi SPKLU.

    Args:
        **data: nama, alamat, kecamatan, fasilitas, daya_kw, jumlah_port.

    Returns:
        dict: data yang sudah dibersihkan (spasi dipangkas, angka jadi int).

    Raises:
        ValidasiError: jika field wajib kosong, kecamatan tidak dikenal,
            atau angka bukan bilangan bulat positif.
    """
    bersih = {}
   
    for field in FIELD_WAJIB:
        nilai = str(data.get(field, "")).strip()
        if not nilai:
            raise ValidasiError(f"Field '{field}' wajib diisi.")
        bersih[field] = nilai

    
    if bersih["kecamatan"] not in KECAMATAN:
        raise ValidasiError(f"Kecamatan '{bersih['kecamatan']}' tidak dikenal di Bandar Lampung.")

    
    for field in ("daya_kw", "jumlah_port"):
        try:
            angka = int(str(data.get(field, "")).strip())
        except ValueError:
            raise ValidasiError(f"Field '{field}' harus berupa angka bulat.") from None
        if angka <= 0:
            raise ValidasiError(f"Field '{field}' harus lebih besar dari 0.")
        bersih[field] = angka
    return bersih
