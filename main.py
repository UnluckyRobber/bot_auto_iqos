# main.py
import asyncio
import requests
import json
import os
from playwright.async_api import async_playwright
from utils import zmien_ip_przez_adb

# Importujemy profile z naszego nowego folderu
from profiles.zdezorientowany import profile_zdezorientowany
from profiles.mala_klawiatura import profile_mala_klawiatura
from profiles.senior import profile_senior
from profiles.multitasker import profile_multitasker
from profiles.rozproszony import profile_rozproszony
from profiles.czytelnik import profile_czytelnik
from profiles.sceptyk import profile_sceptyk
from profiles.niezdecydowany import profile_niezdecydowany
from profiles.tabulator import profile_tabulator
from profiles.marzyciel import profile_marzyciel
from profiles.wizualny import profile_wizualny
from profiles.zabiegany import profile_zabiegany
from profiles.nerwowy import profile_nerwowy

# ==========================================
# MAPOWANIE NAZW PROFILI Z GUI NA FUNKCJE
# ==========================================
MAPOWANIE_PROFILI = {
    "profile_zdezorientowany": profile_zdezorientowany,
    "profile_mala_klawiatura": profile_mala_klawiatura,
    "profile_senior": profile_senior,
    "profile_multitasker": profile_multitasker,
    "profile_rozproszony": profile_rozproszony,
    "profile_czytelnik": profile_czytelnik,
    "profile_sceptyk": profile_sceptyk,
    "profile_niezdecydowany": profile_niezdecydowany,
    "profile_tabulator": profile_tabulator,
    "profile_marzyciel": profile_marzyciel,
    "profile_wizualny": profile_wizualny,
    "profile_zabiegany": profile_zabiegany,
    "profile_nerwowy": profile_nerwowy
}

# ==========================================
# WCZYTYWANIE DANYCH Z PLIKU JSON
# ==========================================
ZADANIA_TESTOWE = []
PLIK_ZADAN = "zadania.json"

if os.path.exists(PLIK_ZADAN):
    try:
        with open(PLIK_ZADAN, "r", encoding="utf-8") as f:
            dane_z_gui = json.load(f)
            
        for zadanie in dane_z_gui:
            # Podmieniamy stringa z zachowaniem na rzeczywistą funkcję profilu
            funkcja_profilu = MAPOWANIE_PROFILI.get(zadanie["zachowanie"], profile_zdezorientowany)
            
            ZADANIA_TESTOWE.append({
                "uuid": zadanie["uuid"],
                "zachowanie": funkcja_profilu,
                "dane": zadanie["dane"]
            })
    except Exception as e:
        print(f"[!] Błąd podczas ładowania pliku {PLIK_ZADAN}: {e}")
        exit()
else:
    print(f"[!] BŁĄD: Nie znaleziono pliku '{PLIK_ZADAN}'.")
    print("[!] Uruchom najpierw program 'gui.py', dodaj konta i kliknij Zapisz!")
    exit()

# ==========================================
# KONTROLER URUCHOMIENIA
# ==========================================
async def main():
    print("[*] Rozpoczynam masowy audyt bezpieczeństwa...")
    
    if not ZADANIA_TESTOWE:
        print("[!] Lista zadań jest pusta! Zakończono działanie.")
        return

    for zadanie in ZADANIA_TESTOWE:
        obecny_uuid = zadanie["uuid"]
        obecne_zachowanie = zadanie["zachowanie"]
        obecne_dane = zadanie["dane"] 
        
        print(f"\n========================================")
        print(f"[*] Przechodzę do testowania profilu: {obecny_uuid} (Konto: {obecne_dane['email']})")
        print(f"========================================")
        
        api_start_url = "http://localhost:58888/api/profiles/start"
        payload = {"uuid": obecny_uuid, "debug_port": True}
        
        try:
            response = requests.post(api_start_url, json=payload).json()
        except requests.exceptions.ConnectionError:
            print(f"[!] Błąd Krytyczny: Nie można połączyć się z API Octo dla profilu {obecny_uuid}.")
            continue 

        ws_endpoint = response.get("ws_endpoint")
        
        if ws_endpoint:
            print(f"[*] Połączono. Adres WebSocket to: {ws_endpoint}")
            
            async with async_playwright() as p:
                browser = await p.chromium.connect_over_cdp(ws_endpoint)
                context = browser.contexts[0]
                page = context.pages[0] if context.pages else await context.new_page()
                
                
                # Uruchomienie wybranego profilu z danymi z GUI
                await obecne_zachowanie(page, obecne_dane) 
                
                print("\n[*] Zadanie zakończone. Odłączanie Playwrighta.")
                await browser.close()
                
            requests.post("http://localhost:58888/api/profiles/stop", json={"uuid": obecny_uuid})
            print(f"[*] Zamknięto okno profilu {obecny_uuid}.")
            
            if zadanie != ZADANIA_TESTOWE[-1]:
                await zmien_ip_przez_adb()
            else:
                print("[*] To był ostatni profil. Koniec audytu!")
            
        else:
            print(f"[!] Błąd uruchamiania profilu po stronie Octo API: {response}")

if __name__ == "__main__":
    asyncio.run(main())