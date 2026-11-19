# Smart Mobility: Sistem Informasi Lokasi SPKLU Bandar Lampung

Cara menjalankan (Python 3.10+, Tkinter bawaan Python, tanpa library tambahan):

    python main.py                      # menjalankan aplikasi
    python -m unittest discover -v      # menjalankan unit test

## Struktur
| File | Isi |
|---|---|
| main.py | Titik masuk aplikasi |
| spklu/models.py | Class `Lokasi` |
| spklu/validasi.py | Validasi input (`raise ValidasiError`) |
| spklu/storage.py | Class `PenyimpananCSV` (file handling `with open` r/w/a/x) |
| spklu/services.py | Class `LokasiService` + Merge Sort, Binary/Linear Search, `*args`, `**kwargs`, lambda |
| spklu/ui.py | Class `FormLokasi` & `AplikasiSPKLU` (Tkinter) |
| tests/test_spklu.py | 3 class uji, 13 fungsi uji (unittest) |
| data/spklu.csv | Dibuat otomatis saat pertama dijalankan |

## Tabel Refactoring Kode
| No | Sebelum | Sesudah | Alasan / Manfaat |
|---|---|---|---|
| 1 | Pengurutan memakai Bubble Sort (dua loop bersarang, O(n²)) | `merge_sort()` di services.py (O(n log n), stabil) dengan `key` berupa lambda | Lebih cepat untuk data besar; urutan elemen sama tetap terjaga |
| 2 | Pencarian id memakai loop linear tiap kali (O(n)) | `cari_id()` memakai Binary Search (O(log n)); data dijaga selalu terurut menurut id | Pencarian id (ubah/hapus/pilih baris) lebih efisien |
| 3 | Pencarian kata kunci memakai `if` berulang per kolom | Satu list comprehension + `any()` dengan parameter `kolom` | Kode lebih ringkas; kolom pencarian mudah ditambah |
| 4 | Validasi tersebar di UI dan penyimpanan | Dipusatkan di `validasi.py` (`validasi_lokasi`) | Tidak ada duplikasi; mudah diuji tanpa UI |
| 5 | Satu file besar berisi UI + logika + file | Dipisah menjadi package (models, validasi, storage, services, ui) | Tanggung jawab jelas (separation of concerns), mudah dirawat |
| 6 | Banyak `if` untuk tiap filter | Dictionary aturan berisi lambda + `**kwargs` | Menambah kriteria baru cukup satu baris |
