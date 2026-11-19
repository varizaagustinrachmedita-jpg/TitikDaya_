import os
import tkinter as tk

from spklu.services import LokasiService
from spklu.storage import PenyimpananCSV
from spklu.ui import AplikasiSPKLU

FOLDER = os.path.dirname(os.path.abspath(__file__))
PATH_DATA = os.path.join(FOLDER, "data", "spklu.csv")


def main():
    """Membuat storage, service, lalu menjalankan jendela utama."""
    storage = PenyimpananCSV(PATH_DATA)
    service = LokasiService(storage)   
    root = tk.Tk()
    AplikasiSPKLU(root, service)
    root.mainloop()


if __name__ == "__main__":
    main()
