"""Modul antarmuka pengguna (GUI) berbasis Tkinter.

Berisi dua class:
    FormLokasi    -> jendela dialog tambah/ubah data.
    AplikasiSPKLU -> jendela utama (menu, pencarian, filter, pengurutan, tabel, detail).
"""
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox
from tkinter import font as tkfont

from .services import LokasiService
from .validasi import KECAMATAN, validasi_lokasi, ValidasiError

KOLOM_TABEL = [
    ("id", "ID", 45),
    ("nama", "Nama SPKLU", 230),
    ("alamat", "Alamat", 240),
    ("kecamatan", "Kecamatan", 150),
    ("fasilitas", "Fasilitas", 260),
    ("daya_kw", "Daya (kW)", 80),
    ("jumlah_port", "Port", 55),
]
JUDUL = {k: j for k, j, _ in KOLOM_TABEL}


FONT_PILIHAN = ("Poppins", "Segoe UI", "Helvetica", "Arial")


def pilih_font(root: tk.Tk) -> str:
    """Memilih font pertama dari FONT_PILIHAN yang terpasang di sistem.

    Args:
        root: objek tk.Tk (dibutuhkan untuk membaca daftar font sistem).

    Returns:
        str: nama keluarga font yang dipakai (Poppins bila tersedia).
    """
    terpasang = set(tkfont.families(root))
    return next((f for f in FONT_PILIHAN if f in terpasang), "TkDefaultFont")


class FormLokasi(tk.Toplevel):
    """Dialog modal untuk menambah atau mengubah satu lokasi.

    Args:
        parent: jendela induk.
        judul: judul dialog.
        awal: dict nilai awal (untuk mode ubah), atau None.
    Attributes:
        hasil: dict data tervalidasi bila user menekan Simpan, selain itu None.
    """

    def __init__(self, parent, judul: str, awal: dict | None = None):
        super().__init__(parent)
        self.title(judul)
        self.resizable(False, False)
        self.hasil = None
        awal = awal or {}
        self.vars = {}
        isian = [("nama", "Nama SPKLU"), ("alamat", "Alamat"), ("kecamatan", "Kecamatan"),
                 ("fasilitas", "Fasilitas (pisah ;)"), ("daya_kw", "Daya (kW)"), ("jumlah_port", "Jumlah Port")]
        frame = ttk.Frame(self, padding=15)
        frame.pack()
        for baris, (kunci, label) in enumerate(isian):
            ttk.Label(frame, text=label).grid(row=baris, column=0, sticky="w", pady=4, padx=(0, 10))
            var = tk.StringVar(value=str(awal.get(kunci, "")))
            self.vars[kunci] = var
            if kunci == "kecamatan":
                widget = ttk.Combobox(frame, textvariable=var, values=KECAMATAN, state="readonly", width=33)
            else:
                widget = ttk.Entry(frame, textvariable=var, width=36)
            widget.grid(row=baris, column=1, pady=4)
        tombol = ttk.Frame(frame)
        tombol.grid(row=len(isian), column=0, columnspan=2, pady=(12, 0))
        ttk.Button(tombol, text="Simpan", command=self._simpan).pack(side="left", padx=5)
        ttk.Button(tombol, text="Batal", command=self.destroy).pack(side="left", padx=5)
        self.transient(parent)
        self.grab_set()  

    def _simpan(self):
        """Validasi input; bila gagal tampilkan pesan, bila lolos simpan ke self.hasil."""
        try:
            self.hasil = validasi_lokasi(**{k: v.get() for k, v in self.vars.items()})
        except ValidasiError as err:  
            messagebox.showerror("Input tidak valid", str(err), parent=self)
            return
        self.destroy()


class AplikasiSPKLU:
    """Jendela utama aplikasi Smart Mobility - Lokasi SPKLU Bandar Lampung.

    Args:
        root: objek tk.Tk.
        service: objek LokasiService yang mengelola data.
    """

    def __init__(self, root: tk.Tk, service: LokasiService):
        self.root = root
        self.service = service
        self.kolom_urut = "id"      
        self.menurun = False        
        self.font = pilih_font(root) 
        self._bangun_ui()
        self._tampilkan()
        
        if self.service.storage and self.service.storage.peringatan:
            self.root.after(300, lambda: messagebox.showwarning(
                "Info Data", "\n".join(self.service.storage.peringatan)))

   
    def _bangun_ui(self):
        """Membuat seluruh widget: menu, header, toolbar, tabel, detail, tombol, status."""
        self.root.title("Smart Mobility - Lokasi SPKLU Bandar Lampung")
        self.root.geometry("1280x720")
        self.root.minsize(900, 520)
        gaya = ttk.Style()
        gaya.theme_use("clam")
        f = self.font
        gaya.configure(".", font=(f, 10))                              # font dasar semua widget
        gaya.configure("Treeview", rowheight=30, font=(f, 10))         # isi tabel
        gaya.configure("Treeview.Heading", font=(f, 10, "bold"))       # header kolom TEBAL
        gaya.configure("Judul.TLabel", font=(f, 17, "bold"), foreground="#0b6e4f")  # judul TEBAL
        gaya.configure("Sub.TLabel", font=(f, 10))
        gaya.configure("Nama.TLabel", font=(f, 12, "bold"), foreground="#0b6e4f")    # nama lokasi TEBAL
        gaya.configure("TLabelframe.Label", font=(f, 10, "bold"))      # judul kotak (Cari, Detail) TEBAL
        gaya.configure("TButton", font=(f, 10, "bold"), padding=5)     # tombol TEBAL
        gaya.configure("TEntry", font=(f, 10))
        gaya.configure("TCombobox", font=(f, 10))
        self.root.option_add("*TCombobox*Listbox.font", (f, 10))       # daftar dropdown

       
        menubar = tk.Menu(self.root)
        m_data = tk.Menu(menubar, tearoff=0, font=(self.font, 10))
        m_data.add_command(label="Tambah Lokasi", command=self.tambah)
        m_data.add_command(label="Ubah Lokasi", command=self.ubah)
        m_data.add_command(label="Hapus Lokasi", command=self.hapus)
        m_data.add_separator()
        m_data.add_command(label="Keluar", command=self.keluar)
        menubar.add_cascade(label="Data", menu=m_data)
        m_lihat = tk.Menu(menubar, tearoff=0, font=(self.font, 10))
        m_lihat.add_command(label="Buka Google Maps", command=self.buka_maps)
        m_lihat.add_command(label="Reset Filter", command=self.reset)
        menubar.add_cascade(label="Lihat", menu=m_lihat)
        self.root.config(menu=menubar)

        # Header
        head = ttk.Frame(self.root, padding=(12, 10, 12, 0))
        head.pack(fill="x")
        ttk.Label(head, text="⚡ Sistem Informasi Lokasi Pengisian Daya Kendaraan Listrik",
                  style="Judul.TLabel").pack(anchor="w")
        ttk.Label(head, text="Smart City - Pilar Smart Mobility | Kota Bandar Lampung",
                  style="Sub.TLabel").pack(anchor="w")

        # Toolbar: pencarian, filter, pengurutan
        bar = ttk.LabelFrame(self.root, text="Cari, Filter & Urutkan", padding=8)
        bar.pack(fill="x", padx=12, pady=8)
        ttk.Label(bar, text="Cari (nama/kecamatan):").grid(row=0, column=0, padx=4)
        self.var_cari = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.var_cari, width=28)
        entry.grid(row=0, column=1, padx=4)
        entry.bind("<KeyRelease>", lambda e: self._tampilkan())  # cari langsung saat mengetik
        entry.bind("<Return>", self._cari_enter)  # tekan Enter -> munculkan pop up bila tidak ditemukan
        ttk.Label(bar, text="Kecamatan:").grid(row=0, column=2, padx=(14, 4))
        self.var_kec = tk.StringVar(value="Semua")
        cb_kec = ttk.Combobox(bar, textvariable=self.var_kec, values=["Semua"] + KECAMATAN,
                              state="readonly", width=20)
        cb_kec.grid(row=0, column=3, padx=4)
        cb_kec.bind("<<ComboboxSelected>>", lambda e: self._tampilkan())
        ttk.Label(bar, text="Daya min:").grid(row=0, column=4, padx=(14, 4))
        self.var_daya = tk.StringVar(value="Semua")
        cb_daya = ttk.Combobox(bar, textvariable=self.var_daya, values=["Semua", "22", "25", "50"],
                               state="readonly", width=7)
        cb_daya.grid(row=0, column=5, padx=4)
        cb_daya.bind("<<ComboboxSelected>>", lambda e: self._tampilkan())

        ttk.Label(bar, text="Urutkan:").grid(row=1, column=0, padx=4, pady=(8, 0))
        self.var_urut = tk.StringVar(value=JUDUL["id"])
        cb_urut = ttk.Combobox(bar, textvariable=self.var_urut, values=list(JUDUL.values()),
                               state="readonly", width=26)
        cb_urut.grid(row=1, column=1, padx=4, pady=(8, 0))
        cb_urut.bind("<<ComboboxSelected>>", self._ganti_urutan)
        self.var_arah = tk.StringVar(value="Naik (A-Z / kecil-besar)")
        cb_arah = ttk.Combobox(bar, textvariable=self.var_arah, state="readonly", width=22,
                               values=["Naik (A-Z / kecil-besar)", "Turun (Z-A / besar-kecil)"])
        cb_arah.grid(row=1, column=3, columnspan=2, padx=4, pady=(8, 0), sticky="w")
        cb_arah.bind("<<ComboboxSelected>>", self._ganti_urutan)
        ttk.Button(bar, text="Reset", command=self.reset).grid(row=1, column=5, pady=(8, 0))

        # Tabel data (Treeview)
        tengah = ttk.Frame(self.root)
        tengah.pack(fill="both", expand=True, padx=12)
        self.tabel = ttk.Treeview(tengah, columns=[k for k, _, _ in KOLOM_TABEL],
                                  show="headings", selectmode="browse")
        for kunci, judul, lebar in KOLOM_TABEL:
            # Klik header = urutkan berdasarkan kolom tsb (klik lagi = balik arah)
            self.tabel.heading(kunci, text=judul, command=lambda k=kunci: self._klik_header(k))
            self.tabel.column(kunci, width=lebar, anchor="center" if kunci in ("id", "daya_kw", "jumlah_port") else "w")
        scroll = ttk.Scrollbar(tengah, orient="vertical", command=self.tabel.yview)
        self.tabel.configure(yscrollcommand=scroll.set)
        self.tabel.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tabel.tag_configure("genap", background="#eef7f2")
        self.tabel.bind("<<TreeviewSelect>>", lambda e: self._tampil_detail())
        self.tabel.bind("<Double-1>", lambda e: self.buka_maps())

        # Panel detail lokasi terpilih
        self.var_detail = tk.StringVar(value="Pilih satu lokasi pada tabel untuk melihat detail.")
        detail = ttk.LabelFrame(self.root, text="Detail Lokasi", padding=8)
        detail.pack(fill="x", padx=12, pady=8)
        self.var_nama = tk.StringVar()  # nama lokasi dibuat tebal (style Nama.TLabel)
        ttk.Label(detail, textvariable=self.var_nama, style="Nama.TLabel").pack(anchor="w")
        ttk.Label(detail, textvariable=self.var_detail, justify="left", wraplength=1180).pack(anchor="w")

        # Tombol aksi
        aksi = ttk.Frame(self.root, padding=(12, 0, 12, 6))
        aksi.pack(fill="x")
        for teks, cmd in [("➕ Tambah", self.tambah), ("✏️ Ubah", self.ubah), ("🗑️ Hapus", self.hapus),
                          ("🗺️ Buka Google Maps", self.buka_maps)]:
            ttk.Button(aksi, text=teks, command=cmd).pack(side="left", padx=4)
        ttk.Button(aksi, text="Keluar", command=self.keluar).pack(side="right", padx=4)

        # Status bar (agregat data)
        self.var_status = tk.StringVar()
        ttk.Label(self.root, textvariable=self.var_status, relief="sunken", anchor="w",
                  padding=4).pack(fill="x", side="bottom")

    # --------------------------------------------------------------- tampilan
    def _tampilkan(self):
        """Pipeline tampilan: filter -> cari -> urutkan -> isi tabel -> update status."""
        data = self.service.filter_lokasi(kecamatan=self.var_kec.get(), min_daya=self.var_daya.get())
        data = self.service.cari(self.var_cari.get(), data=data)
        data = self.service.urutkan(self.kolom_urut, menurun=self.menurun, data=data)

        self.tabel.delete(*self.tabel.get_children())
        for no, l in enumerate(data):
            self.tabel.insert("", "end", iid=str(l.id), tags=("genap",) if no % 2 else (),
                              values=(l.id, l.nama, l.alamat, l.kecamatan, l.fasilitas, l.daya_kw, l.jumlah_port))
        # Tanda panah ▲▼ pada header kolom aktif
        for kunci, judul, _ in KOLOM_TABEL:
            tanda = (" ▼" if self.menurun else " ▲") if kunci == self.kolom_urut else ""
            self.tabel.heading(kunci, text=judul + tanda)
        total = self.service.hitung_total("daya_kw", "jumlah_port", data=data)
        self.var_status.set(f"Menampilkan {len(data)} dari {len(self.service.semua)} lokasi  |  "
                            f"Total daya: {total['daya_kw']} kW  |  Total port: {total['jumlah_port']}")
        self._tampil_detail()

    def _cari_enter(self, _event=None):
        """Dipanggil saat user menekan Enter pada kolom pencarian.

        Menyegarkan tabel, lalu menampilkan pop up bila tidak ada lokasi yang cocok.
        """
        self._tampilkan()
        if not self.tabel.get_children():
            messagebox.showinfo("Hasil Pencarian", "Lokasi tidak ditemukan")

    def _tampil_detail(self):
        """Menampilkan detail lokasi yang dipilih pada panel bawah."""
        l = self._terpilih()
        if l is None:
            self.var_nama.set("")
            self.var_detail.set("Pilih satu lokasi pada tabel untuk melihat detail.")
            return
        self.var_nama.set(l.nama)
        self.var_detail.set(f"Alamat     : {l.alamat}, Kec. {l.kecamatan}\n"
                            f"Fasilitas  : {l.fasilitas.replace(';', ', ')}\n"
                            f"Pengisian  : {l.daya_kw} kW, {l.jumlah_port} port\nGoogle Maps: {l.maps_url}")

    def _terpilih(self):
        """Mengembalikan objek Lokasi yang dipilih di tabel (None bila tidak ada)."""
        pilihan = self.tabel.selection()
        return self.service.cari_id(int(pilihan[0])) if pilihan else None

    # ---------------------------------------------------------------- event
    def _klik_header(self, kolom):
        """Klik header: urutkan kolom; klik kolom yang sama membalik arah."""
        self.menurun = (not self.menurun) if kolom == self.kolom_urut else False
        self.kolom_urut = kolom
        self.var_urut.set(JUDUL[kolom])
        self.var_arah.set("Turun (Z-A / besar-kecil)" if self.menurun else "Naik (A-Z / kecil-besar)")
        self._tampilkan()

    def _ganti_urutan(self, _event=None):
        """Dipanggil saat combobox urutan/arah diubah."""
        balik = {j: k for k, j in JUDUL.items()}
        self.kolom_urut = balik[self.var_urut.get()]
        self.menurun = self.var_arah.get().startswith("Turun")
        self._tampilkan()

    def reset(self):
        """Mengembalikan pencarian, filter, dan urutan ke kondisi awal."""
        self.var_cari.set("")
        self.var_kec.set("Semua")
        self.var_daya.set("Semua")
        self.kolom_urut, self.menurun = "id", False
        self.var_urut.set(JUDUL["id"])
        self.var_arah.set("Naik (A-Z / kecil-besar)")
        self._tampilkan()

    # ----------------------------------------------------------------- aksi
    def tambah(self):
        """Membuka form tambah lalu menyimpan data baru."""
        form = FormLokasi(self.root, "Tambah Lokasi SPKLU")
        self.root.wait_window(form)
        if form.hasil:
            try:
                self.service.tambah(**form.hasil)
            except OSError as err:  # gagal menulis file
                messagebox.showerror("Gagal menyimpan", str(err))
            self._tampilkan()

    def ubah(self):
        """Membuka form ubah untuk lokasi terpilih."""
        l = self._terpilih()
        if l is None:
            messagebox.showinfo("Ubah", "Pilih lokasi pada tabel terlebih dahulu.")
            return
        form = FormLokasi(self.root, "Ubah Lokasi SPKLU", awal=l.to_dict())
        self.root.wait_window(form)
        if form.hasil:
            try:
                self.service.ubah(l.id, **form.hasil)
            except (LookupError, OSError) as err:
                messagebox.showerror("Gagal mengubah", str(err))
            self._tampilkan()

    def hapus(self):
        """Menghapus lokasi terpilih setelah konfirmasi."""
        l = self._terpilih()
        if l is None:
            messagebox.showinfo("Hapus", "Pilih lokasi pada tabel terlebih dahulu.")
            return
        if messagebox.askyesno("Konfirmasi", f"Hapus '{l.nama}'?"):
            try:
                self.service.hapus(l.id)
            except (LookupError, OSError) as err:
                messagebox.showerror("Gagal menghapus", str(err))
            self._tampilkan()

    def buka_maps(self):
        """Membuka tautan Google Maps lokasi terpilih di browser."""
        l = self._terpilih()
        if l is None:
            messagebox.showinfo("Google Maps", "Pilih lokasi pada tabel terlebih dahulu.")
            return
        webbrowser.open(l.maps_url)

    def keluar(self):
        """Menutup aplikasi (data sudah tersimpan otomatis tiap perubahan)."""
        if messagebox.askyesno("Keluar", "Tutup aplikasi?"):
            self.root.destroy()
