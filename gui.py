import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import subprocess
import platform
import threading
import sys
import random
from faker import Faker

PLIK_ZADAN = "zadania.json"

class BotControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel Sterowania - Bot Octo (Wersja PRO)")
        self.root.geometry("1000x750")
        self.root.configure(padx=10, pady=10)
        
        self.zadania = []
        self.process = None 
        self.faker = Faker('pl_PL') # Inicjalizacja generatora polskich danych
        
        # Style
        style = ttk.Style()
        style.configure("TLabelframe.Label", font=("Arial", 10, "bold"))
        
        # -----------------------------------------------------
        # GÓRNA RAMKA - INPUTY
        # -----------------------------------------------------
        self.frame_inputs = ttk.LabelFrame(self.root, text="Dane Nowego Profilu", padding=(15, 15))
        self.frame_inputs.pack(fill="x", pady=(0, 10))
        self.utworz_pola_input()
        
        # -----------------------------------------------------
        # DOLNA RAMKA - ZAKŁADKI (NOTEBOOK)
        # -----------------------------------------------------
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # ZAKŁADKA 1: Kolejka
        self.tab_kolejka = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_kolejka, text="📋 Kolejka Zadań")
        
        # ZAKŁADKA 2: Konsola
        self.tab_konsola = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_konsola, text="💻 Konsola (Logi Bota)")

        # Budowanie zawartości zakładek
        self.utworz_liste_zadan()
        self.utworz_konsole()
        
        # Wczytanie z pliku na start
        self.wczytaj_z_pliku()

    def utworz_pola_input(self):
        # Zmienne
        self.var_uuid = tk.StringVar()
        self.var_zachowanie = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_haslo = tk.StringVar()
        self.var_imie = tk.StringVar()
        self.var_nazwisko = tk.StringVar()
        self.var_dzien = tk.StringVar()
        self.var_miesiac = tk.StringVar()
        self.var_rok = tk.StringVar()
        self.var_ulica = tk.StringVar()
        self.var_miasto = tk.StringVar()
        self.var_telefon = tk.StringVar()

        profile_opcje = [
            "profile_zdezorientowany", "profile_mala_klawiatura",
            "profile_senior", "profile_multitasker", "profile_rozproszony",
            "profile_czytelnik", "profile_sceptyk", "profile_niezdecydowany", 
            "profile_wizualny", "profile_zabiegany", "profile_nerwowy",
            "profile_tabulator", "profile_marzyciel", "profile_wizualny",
            "profile_zabiegany", "profile_nerwowy"
        ]

        # Wiersz 0
        ttk.Label(self.frame_inputs, text="UUID Octo:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(self.frame_inputs, textvariable=self.var_uuid, width=35).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.frame_inputs, text="Zachowanie Bota:").grid(row=0, column=2, sticky="w", padx=(20,0), pady=5)
        combo_zachowanie = ttk.Combobox(self.frame_inputs, textvariable=self.var_zachowanie, values=profile_opcje, state="readonly", width=32)
        combo_zachowanie.grid(row=0, column=3, padx=5, pady=5)
        if profile_opcje: combo_zachowanie.current(0)

        # Wiersz 1
        ttk.Label(self.frame_inputs, text="E-mail:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(self.frame_inputs, textvariable=self.var_email, width=35).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.frame_inputs, text="Hasło:").grid(row=1, column=2, sticky="w", padx=(20,0), pady=5)
        ttk.Entry(self.frame_inputs, textvariable=self.var_haslo, width=35).grid(row=1, column=3, padx=5, pady=5)

        # Wiersz 2
        ttk.Label(self.frame_inputs, text="Imię:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(self.frame_inputs, textvariable=self.var_imie, width=35).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self.frame_inputs, text="Nazwisko:").grid(row=2, column=2, sticky="w", padx=(20,0), pady=5)
        ttk.Entry(self.frame_inputs, textvariable=self.var_nazwisko, width=35).grid(row=2, column=3, padx=5, pady=5)

        # Wiersz 3
        ttk.Label(self.frame_inputs, text="Data Ur. (DD/MM/YYYY):").grid(row=3, column=0, sticky="w", pady=5)
        frame_data = ttk.Frame(self.frame_inputs)
        frame_data.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        ttk.Entry(frame_data, textvariable=self.var_dzien, width=5).pack(side="left")
        ttk.Label(frame_data, text=" / ").pack(side="left")
        ttk.Entry(frame_data, textvariable=self.var_miesiac, width=5).pack(side="left")
        ttk.Label(frame_data, text=" / ").pack(side="left")
        ttk.Entry(frame_data, textvariable=self.var_rok, width=8).pack(side="left")

        ttk.Label(self.frame_inputs, text="Telefon:").grid(row=3, column=2, sticky="w", padx=(20,0), pady=5)
        ttk.Entry(self.frame_inputs, textvariable=self.var_telefon, width=35).grid(row=3, column=3, padx=5, pady=5)

        # Wiersz 4
        ttk.Label(self.frame_inputs, text="Ulica i nr:").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(self.frame_inputs, textvariable=self.var_ulica, width=35).grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(self.frame_inputs, text="Miasto:").grid(row=4, column=2, sticky="w", padx=(20,0), pady=5)
        ttk.Entry(self.frame_inputs, textvariable=self.var_miasto, width=35).grid(row=4, column=3, padx=5, pady=5)

        # Wiersz 5 - Przyciski
        frame_buttons = ttk.Frame(self.frame_inputs)
        frame_buttons.grid(row=5, column=0, columnspan=4, pady=(15, 0), sticky="we")
        
        btn_generuj = tk.Button(frame_buttons, text="🎲 Generuj Losową Tożsamość", bg="#9C27B0", fg="white", font=("Arial", 10, "bold"), command=self.generuj_dane_faker)
        btn_generuj.pack(side="left", padx=5)

        btn_dodaj = tk.Button(frame_buttons, text="➕ Dodaj do Kolejki", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.dodaj_zadanie)
        btn_dodaj.pack(side="right", padx=5)

    def utworz_liste_zadan(self):
        kolumny = ("uuid", "profil", "email", "imie", "nazwisko", "telefon")
        self.drzewo = ttk.Treeview(self.tab_kolejka, columns=kolumny, show="headings", height=10)
        
        self.drzewo.heading("uuid", text="UUID Octo")
        self.drzewo.heading("profil", text="Profil Zachowania")
        self.drzewo.heading("email", text="E-mail")
        self.drzewo.heading("imie", text="Imię")
        self.drzewo.heading("nazwisko", text="Nazwisko")
        self.drzewo.heading("telefon", text="Telefon")

        self.drzewo.column("uuid", width=150, anchor="center")
        self.drzewo.column("profil", width=150, anchor="center")
        self.drzewo.column("email", width=180)
        self.drzewo.column("imie", width=100)
        self.drzewo.column("nazwisko", width=100)
        self.drzewo.column("telefon", width=100, anchor="center")
        
        self.drzewo.pack(fill="both", expand=True, padx=10, pady=10)

        frame_przyciski = ttk.Frame(self.tab_kolejka)
        frame_przyciski.pack(fill="x", padx=10, pady=5)

        btn_usun = tk.Button(frame_przyciski, text="❌ Usuń zaznaczone", bg="#f44336", fg="white", command=self.usun_zaznaczone)
        btn_usun.pack(side="left")

        btn_wyczysc = tk.Button(frame_przyciski, text="🗑 Wyczyść całą listę", command=self.wyczysc_liste)
        btn_wyczysc.pack(side="left", padx=10)

        self.btn_uruchom = tk.Button(frame_przyciski, text="🚀 ZAPISZ I URUCHOM BOTA", bg="#FF9800", fg="white", font=("Arial", 11, "bold"), command=self.zapisz_i_uruchom)
        self.btn_uruchom.pack(side="right", padx=5)

        btn_zapisz = tk.Button(frame_przyciski, text="💾 Tylko Zapisz", bg="#2196F3", fg="white", font=("Arial", 10), command=self.zapisz_do_pliku)
        btn_zapisz.pack(side="right", padx=5)

    def utworz_konsole(self):
        """Tworzy czarne pole tekstowe udające prawdziwą konsolę CMD."""
        self.txt_console = scrolledtext.ScrolledText(
            self.tab_konsola, wrap=tk.WORD, bg="black", fg="#00FF00", 
            font=("Consolas", 10), state="disabled"
        )
        self.txt_console.pack(fill="both", expand=True, padx=10, pady=10)

    # -------------------------------------------------------------
    # LOGIKA APLIKACJI
    # -------------------------------------------------------------

    def generuj_dane_faker(self):
        """Wypełnia pola formularza wiarygodnymi, losowymi danymi dla Polaka. 
        Omija numer telefonu."""
        self.var_imie.set(self.faker.first_name())
        self.var_nazwisko.set(self.faker.last_name())
        
        # Data urodzenia dla osoby w wieku 19-55 lat
        data_ur = self.faker.date_of_birth(minimum_age=19, maximum_age=55)
        self.var_dzien.set(f"{data_ur.day:02d}")
        self.var_miesiac.set(f"{data_ur.month:02d}")
        self.var_rok.set(str(data_ur.year))
        
        # Adres
        self.var_ulica.set(self.faker.street_address())
        self.var_miasto.set(self.faker.city())
        
        # Uwaga! Telefon nie jest generowany. Pozostawiamy bez zmian.

    def dodaj_zadanie(self):
        if not self.var_email.get() or not self.var_uuid.get():
            messagebox.showwarning("Błąd", "Pola UUID i E-mail są absolutnie wymagane!")
            return
            
        if not self.var_telefon.get():
            messagebox.showwarning("Uwaga!", "Zapomniałeś o numerze telefonu!\nWpisz go ręcznie przed dodaniem zadania do kolejki.")
            return

        nowe_zadanie = {
            "uuid": self.var_uuid.get().strip(),
            "zachowanie": self.var_zachowanie.get(),
            "dane": {
                "email": self.var_email.get().strip(),
                "haslo": self.var_haslo.get().strip(),
                "imie": self.var_imie.get().strip(),
                "nazwisko": self.var_nazwisko.get().strip(),
                "dzien_ur": self.var_dzien.get().strip(),
                "miesiac_ur": self.var_miesiac.get().strip(),
                "rok_ur": self.var_rok.get().strip(),
                "ulica": self.var_ulica.get().strip(),
                "miasto": self.var_miasto.get().strip(),
                "telefon": self.var_telefon.get().strip()
            }
        }
        
        self.zadania.append(nowe_zadanie)
        self.odswiez_tabele()
        
        # Czyścimy tylko wrażliwe i zmienne rzeczy
        self.var_email.set("")
        self.var_imie.set("")
        self.var_nazwisko.set("")
        self.var_telefon.set("") # Telefon czyścimy, by upewnić się, że przy nowym fakowaniu user wpisze nowy

    def odswiez_tabele(self):
        for item in self.drzewo.get_children():
            self.drzewo.delete(item)
        for z in self.zadania:
            self.drzewo.insert("", "end", values=(
                z["uuid"], z["zachowanie"], z["dane"]["email"], 
                z["dane"]["imie"], z["dane"]["nazwisko"], z["dane"]["telefon"]
            ))

    def usun_zaznaczone(self):
        selected = self.drzewo.selection()
        if not selected: return
        for item in selected:
            wartosci = self.drzewo.item(item, "values")
            self.zadania = [z for z in self.zadania if not (z["uuid"] == wartosci[0] and z["dane"]["email"] == wartosci[2])]
            self.drzewo.delete(item)

    def wyczysc_liste(self):
        if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć wszystkie zadania z listy?"):
            self.zadania = []
            self.odswiez_tabele()

    def zapisz_do_pliku(self, pokaz_info=True):
        try:
            with open(PLIK_ZADAN, "w", encoding="utf-8") as f:
                json.dump(self.zadania, f, indent=4, ensure_ascii=False)
            if pokaz_info:
                messagebox.showinfo("Sukces", f"Zapisano {len(self.zadania)} zadań do pliku.")
            return True
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas zapisu:\n{e}")
            return False

    def wczytaj_z_pliku(self):
        if os.path.exists(PLIK_ZADAN):
            try:
                with open(PLIK_ZADAN, "r", encoding="utf-8") as f:
                    self.zadania = json.load(f)
                self.odswiez_tabele()
            except Exception:
                pass

    # -------------------------------------------------------------
    # LOGIKA URUCHAMIANIA BOTA WEWNĄTRZ GUI
    # -------------------------------------------------------------
    def wypisz_w_konsoli(self, tekst, wyczysc=False):
        """Wypisuje tekst w zakładce Konsola."""
        self.txt_console.config(state='normal')
        if wyczysc:
            self.txt_console.delete('1.0', tk.END)
        self.txt_console.insert(tk.END, tekst)
        self.txt_console.see(tk.END) # Zawsze przewija na dół (auto-scroll)
        self.txt_console.config(state='disabled')

    def czytaj_wyjscie_bota(self):
        """Wątek działający w tle, który czyta linijka po linijce z pliku main.py"""
        for line in iter(self.process.stdout.readline, ''):
            self.root.after(0, self.wypisz_w_konsoli, line)
            
        self.process.stdout.close()
        self.process.wait()
        
        msg = f"\n[!] PROCES ZAKOŃCZONY (Kod: {self.process.returncode})\n"
        self.root.after(0, self.wypisz_w_konsoli, msg)
        self.root.after(0, lambda: self.btn_uruchom.config(state="normal"))

    def zapisz_i_uruchom(self):
        if not self.zadania:
            messagebox.showwarning("Błąd", "Kolejka zadań jest pusta! Dodaj konto przed uruchomieniem.")
            return
            
        zapisano = self.zapisz_do_pliku(pokaz_info=False)
        
        if zapisano:
            self.btn_uruchom.config(state="disabled")
            self.notebook.select(self.tab_konsola)
            self.wypisz_w_konsoli("=== URUCHAMIANIE BOTA (main.py) ===\n", wyczysc=True)
            
            try:
                flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                
                # Używamy -X utf8, by logi konsoli z Pythona kodowały poprawnie znaki z main.py
                self.process = subprocess.Popen(
                    [sys.executable, "-X", "utf8", "-u", "main.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, 
                    text=True,
                    encoding="utf-8",
                    bufsize=1,
                    creationflags=flags
                )
                
                threading.Thread(target=self.czytaj_wyjscie_bota, daemon=True).start()
                
            except Exception as e:
                self.btn_uruchom.config(state="normal")
                messagebox.showerror("Błąd Uruchamiania", f"Nie udało się uruchomić pliku main.py:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BotControllerApp(root)
    root.mainloop()