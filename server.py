# server.py (TWÓJ SERWER)
import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)
PLIK_BAZY = "licencje.json"

# ========================================================
# (OPCJONALNE) ZABEZPIECZENIE INTEGRALNOŚCI PLIKÓW
# Jeśli wdrożyłeś sprawdzanie hasha w gui.py, wklej tutaj 
# hash najnowszego pliku .exe. Jeśli wpiszesz None, serwer
# zignoruje sprawdzanie plików.
# ========================================================
OFEKTYWNY_HASH_WERSJI = None 

def wczytaj_licencje():
    if not os.path.exists(PLIK_BAZY):
        # Generowanie pokazowej bazy z nowymi typami kluczy
        domyslna_baza = {
            "PRO-TRIAL-30M": {
                "hwid": None, 
                "aktywna": True,
                "czas_trwania_minuty": 30,
                "wygasa_o": None
            },
            "TRIAL-3-DNI": {
                "aktywna": True,
                "wieloosobowy": True,
                "czas_trwania_dni": 3,
                "uzytkownicy": {}
            },
            "MOJ-SUPER-KLUCZ-ADMINA": {
                "aktywna": True,
                "uniwersalny": True
            }
        }
        zapisz_licencje(domyslna_baza)
        return domyslna_baza
    
    with open(PLIK_BAZY, "r", encoding="utf-8") as f:
        return json.load(f)

def zapisz_licencje(baza):
    with open(PLIK_BAZY, "w", encoding="utf-8") as f:
        json.dump(baza, f, indent=4)

@app.route('/api/verify', methods=['POST'])
def verify_license():
    data = request.json
    klucz = data.get('key')
    hwid = data.get('hwid')
    hash_klienta = data.get('version_hash')

    if not klucz or not hwid:
        return jsonify({"valid": False, "message": "Brak klucza lub HWID."}), 400

    baza = wczytaj_licencje()
    licencja = baza.get(klucz)

    # 1. Sprawdzamy czy klucz istnieje w bazie
    if not licencja:
        return jsonify({"valid": False, "message": "Klucz licencyjny nie istnieje."}), 401

    # 2. Sprawdzamy czy nie został ręcznie zablokowany
    if not licencja.get("aktywna", True):
        return jsonify({"valid": False, "message": "Twoja licencja została zablokowana."}), 403

    # ==========================================================
    # SPRAWDZANIE SPÓJNOŚCI PLIKÓW (Anty-Crack)
    # ==========================================================
    if OFEKTYWNY_HASH_WERSJI and hash_klienta:
        if hash_klienta != OFEKTYWNY_HASH_WERSJI:
            return jsonify({
                "valid": False, 
                "message": "BŁĄD KRYTYCZNY: Używasz zmodyfikowanej lub nieaktualnej wersji bota! Pobierz najnowszą wersję."
            }), 403

    # ==========================================================
    # LOGIKA 1: KLUCZ UNIWERSALNY (ADMINISTRATOR)
    # ==========================================================
    if licencja.get("uniwersalny", False):
        return jsonify({"valid": True, "message": "Zalogowano pomyślnie (Konto Administratora)."}), 200

    now = datetime.now()

    # ==========================================================
    # LOGIKA 2: KLUCZ WIELOOSOBOWY (NP. PUBLICZNY TRIAL NA 3 DNI)
    # ==========================================================
    if licencja.get("wieloosobowy", False):
        if "uzytkownicy" not in licencja:
            licencja["uzytkownicy"] = {}

        uzytkownicy = licencja["uzytkownicy"]

        # A) Klient używa klucza pierwszy raz
        if hwid not in uzytkownicy:
            if "czas_trwania_dni" in licencja:
                dni = licencja["czas_trwania_dni"]
                data_wygasniecia = now + timedelta(days=dni)
                msg_witamy = f"Aktywowano darmowy dostęp na {dni} dni!"
            else:
                minuty = licencja.get("czas_trwania_minuty", 5)
                data_wygasniecia = now + timedelta(minutes=minuty)
                msg_witamy = f"Konto Trial aktywowane! Masz {minuty} minut."

            uzytkownicy[hwid] = data_wygasniecia.isoformat()
            zapisz_licencje(baza)

            return jsonify({"valid": True, "message": msg_witamy}), 200

        # B) Klient używa klucza kolejny raz
        data_wygasniecia = datetime.fromisoformat(uzytkownicy[hwid])
        if now > data_wygasniecia:
            return jsonify({"valid": False, "message": "Twój czas próbny dla tego klucza dobiegł końca."}), 403
        
        # Obliczanie i formatowanie pozostałego czasu
        pozostalo = data_wygasniecia - now
        pozostalo_sekund = pozostalo.total_seconds()
        
        if pozostalo_sekund > 86400:
            msg_czas = f"Licencja Trial aktywna. Pozostało ok. {int(pozostalo_sekund / 86400)} dni."
        elif pozostalo_sekund > 3600:
            msg_czas = f"Licencja Trial aktywna. Pozostało ok. {int(pozostalo_sekund / 3600)} godzin."
        else:
            msg_czas = f"Licencja Trial aktywna. Pozostało ok. {int(pozostalo_sekund / 60)} minut."

        return jsonify({"valid": True, "message": msg_czas}), 200


    # ==========================================================
    # LOGIKA 3: ZWYKŁY KLUCZ JEDNOOSOBOWY (PRZYPISYWANY DO HWID)
    # ==========================================================
    # Aktywacja nowego klucza prywatnego
    if licencja.get("hwid") is None:
        if "czas_trwania_dni" in licencja:
            data_wygasniecia = now + timedelta(days=licencja["czas_trwania_dni"])
        else:
            czas_minuty = licencja.get("czas_trwania_minuty", 60)
            data_wygasniecia = now + timedelta(minutes=czas_minuty)
        
        baza[klucz]["hwid"] = hwid
        baza[klucz]["wygasa_o"] = data_wygasniecia.isoformat() 
        zapisz_licencje(baza) 
        
        czas_sformatowany = data_wygasniecia.strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({
            "valid": True, 
            "message": f"Aktywowano! Licencja ważna do: {czas_sformatowany}"
        }), 200

    # Weryfikacja przypisanego sprzętu
    if licencja["hwid"] != hwid:
        return jsonify({"valid": False, "message": "Klucz jest przypisany do innego urządzenia!"}), 403

    # Sprawdzanie czy klucz prywatny wygasł
    wygasa_o_str = licencja.get("wygasa_o")
    if wygasa_o_str:
        data_wygasniecia = datetime.fromisoformat(wygasa_o_str)
        if now > data_wygasniecia:
            return jsonify({"valid": False, "message": "Twój czas minął! Licencja wygasła."}), 403
            
        pozostalo = data_wygasniecia - now
        pozostalo_sekund = pozostalo.total_seconds()
        
        if pozostalo_sekund > 86400:
            msg_czas = f"Weryfikacja pomyślna. Pozostało Ci ok. {int(pozostalo_sekund / 86400)} dni."
        elif pozostalo_sekund > 3600:
            msg_czas = f"Weryfikacja pomyślna. Pozostało Ci ok. {int(pozostalo_sekund / 3600)} godzin."
        else:
            msg_czas = f"Weryfikacja pomyślna. Pozostało Ci {int(pozostalo_sekund / 60)} minut."
        
        return jsonify({
            "valid": True, 
            "message": msg_czas
        }), 200
        
    # Jeżeli w bazie wygasa_o to null / brak - traktujemy jako lifetime
    return jsonify({"valid": True, "message": "Weryfikacja pomyślna (Licencja dożywotnia)."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
