# server.py (TWÓJ SERWER)
import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
PLIK_BAZY = "licencje.json"

# Funkcja wczytująca klucze z pliku JSON
def wczytaj_licencje():
    if not os.path.exists(PLIK_BAZY):
        # Jeśli pliku nie ma, tworzymy przykładową bazę z jednym darmowym kluczem
        domyslna_baza = {
            "PRO-TRIAL-2024": {"hwid": None, "aktywna": True}
        }
        zapisz_licencje(domyslna_baza)
        return domyslna_baza
    
    with open(PLIK_BAZY, "r", encoding="utf-8") as f:
        return json.load(f)

# Funkcja zapisująca zmiany do pliku JSON
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

    # 1. Sprawdzamy czy klucz istnieje
    if not licencja:
        return jsonify({"valid": False, "message": "Klucz licencyjny nie istnieje."}), 401

    # 2. Sprawdzamy czy nie został zablokowany
    if not licencja.get("aktywna", True):
        return jsonify({"valid": False, "message": "Twoja licencja została zablokowana."}), 403

    # 3. Jeśli klucz jest nowy (brak przypisanego HWID), przypisujemy go!
    if licencja.get("hwid") is None:
        baza[klucz]["hwid"] = hwid
        zapisz_licencje(baza) # Zapisujemy zmianę w pliku na serwerze!
        return jsonify({"valid": True, "message": "Licencja aktywowana i przypisana do tego komputera!"}), 200

    # 4. Jeśli klucz jest już przypisany, sprawdzamy czy HWID z komputera zgadza się z tym w bazie
    if licencja["hwid"] == hwid:
        return jsonify({"valid": True, "message": "Weryfikacja pomyślna."}), 200
    else:
        return jsonify({"valid": False, "message": "Klucz jest przypisany do innego urządzenia (Inne HWID)!"}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
