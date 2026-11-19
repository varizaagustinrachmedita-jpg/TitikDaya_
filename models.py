"""Modul model data: representasi satu lokasi SPKLU."""
from dataclasses import dataclass, asdict
from urllib.parse import quote_plus

FIELDS = ["id", "nama", "alamat", "kecamatan", "fasilitas", "daya_kw", "jumlah_port"]


@dataclass
class Lokasi:
    """Satu lokasi Stasiun Pengisian Kendaraan Listrik Umum (SPKLU).

    Attributes:
        id: nomor unik lokasi.
        nama: nama tempat SPKLU.
        alamat: alamat lengkap.
        kecamatan: kecamatan lokasi.
        fasilitas: fasilitas pendukung (dipisah titik koma).
        daya_kw: daya pengisian maksimum (kilowatt).
        jumlah_port: jumlah colokan/port pengisian.
    """
    id: int
    nama: str
    alamat: str
    kecamatan: str
    fasilitas: str
    daya_kw: int
    jumlah_port: int

    @property
    def maps_url(self) -> str:
        """Tautan Google Maps (pencarian nama + alamat) untuk melihat titik & petunjuk arah."""
        kueri = quote_plus(f"{self.nama}, {self.alamat}, Bandar Lampung")
        return f"https://www.google.com/maps/search/?api=1&query={kueri}"

    def to_dict(self) -> dict:
        """Mengubah objek menjadi dict (untuk ditulis ke CSV)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Lokasi":
        """Membuat objek Lokasi dari dict (hasil baca CSV).

        Raises:
            ValueError: jika id/daya_kw/jumlah_port bukan angka.
            KeyError: jika ada kolom yang hilang.
        """
        return cls(
            id=int(data["id"]),
            nama=data["nama"],
            alamat=data["alamat"],
            kecamatan=data["kecamatan"],
            fasilitas=data["fasilitas"],
            daya_kw=int(data["daya_kw"]),
            jumlah_port=int(data["jumlah_port"]),
        )
