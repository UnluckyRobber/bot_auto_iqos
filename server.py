# server.py (TWÓJ SERWER)
import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)
PLIK_BAZY = "licencje.json"

def wczytaj_licencje():
    if not os.path.exists(PLIK_BAZY):
        domyslna_baza = {
            "PRO-TRIAL-30M": {
                "hwid": None, 
                "aktywna": True,
                "czas_trwania_minuty": 30,
                "wygasa_o": None
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

    now = datetime.now()

    # 3. AKTYWACJA NOWEGO KLUCZA (Pierwsze użycie)
    if licencja.get("hwid") is None:
        czas_minuty = licencja.get("czas_trwania_minuty", 60) # Domyślnie 60 min, jeśli nie podano
        data_wygasniecia = now + timedelta(minutes=czas_minuty)
        
        # Zapisujemy do bazy HWID oraz dokładną datę wygaśnięcia
        baza[klucz]["hwid"] = hwid
        baza[klucz]["wygasa_o"] = data_wygasniecia.isoformat() 
        zapisz_licencje(baza) 
        
        czas_sformatowany = data_wygasniecia.strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({
            "valid": True, 
            "message": f"Aktywowano! Licencja ważna do: {czas_sformatowany}"
        }), 200

    # 4. WERYFIKACJA UŻYWANEGO KLUCZA (Sprawdzanie HWID)
    if licencja["hwid"] != hwid:
        return jsonify({"valid": False, "message": "Klucz jest przypisany do innego urządzenia!"}), 403

    # 5. SPRAWDZANIE CZASU (Czy klucz już wygasł?)
    wygasa_o_str = licencja.get("wygasa_o")
    if wygasa_o_str:
        data_wygasniecia = datetime.fromisoformat(wygasa_o_str)
        if now > data_wygasniecia:
            return jsonify({"valid": False, "message": "Twój czas minął! Licencja wygasła."}), 403
            
        # Obliczanie pozostałego czasu dla klienta
        pozostalo = data_wygasniecia - now
        minuty_pozostalo = int(pozostalo.total_seconds() / 60)
        
        return jsonify({
            "valid": True, 
            "message": f"Weryfikacja pomyślna. Pozostało Ci {minuty_pozostalo} minut."
        }), 200
        
    return jsonify({"valid": True, "message": "Weryfikacja pomyślna (Licencja dożywotnia)."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
