# server.py (KOD NA TWÓJ SERWER)
from flask import Flask, request, jsonify

app = Flask(__name__)

# To jest nasza prosta "baza danych" w pamięci.
# W przyszłości możesz to zamienić na prawdziwą bazę (np. SQLite lub MySQL).
# "hwid": None oznacza, że klucz jest nowy i czeka na pierwszego klienta.
BAZA_LICENCJI = {
    "IQOS-TEST-1111": {"hwid": None, "aktywna": True},
    "IQOS-TEST-2222": {"hwid": None, "aktywna": True},
    "PRO-VIP-9999":   {"hwid": "ABC123XYZ", "aktywna": True} # Ten klucz jest już przypisany
}

@app.route('/api/verify', methods=['POST'])
def verify_license():
    data = request.json
    klucz = data.get('key')
    hwid = data.get('hwid')

    if not klucz or not hwid:
        return jsonify({"valid": False, "message": "Brak klucza lub HWID."}), 400

    licencja = BAZA_LICENCJI.get(klucz)

    # 1. Sprawdzamy czy klucz w ogóle istnieje
    if not licencja:
        return jsonify({"valid": False, "message": "Klucz licencyjny nie istnieje."}), 401

    # 2. Sprawdzamy czy nie zablokowałeś go np. za brak płatności
    if not licencja["aktywna"]:
        return jsonify({"valid": False, "message": "Twoja licencja została wyłączona/zablokowana."}), 403

    # 3. Jeśli klucz jest wolny, przypisujemy go do komputera tego użytkownika
    if licencja["hwid"] is None:
        licencja["hwid"] = hwid
        # Tutaj w produkcji warto zapisać zmiany do pliku lub bazy danych
        return jsonify({"valid": True, "message": "Licencja aktywowana i przypisana do Twojego komputera!"}), 200

    # 4. Jeśli klucz jest już przypisany, weryfikujemy czy komputer (HWID) się zgadza
    if licencja["hwid"] == hwid:
        return jsonify({"valid": True, "message": "Licencja zweryfikowana pomyślnie."}), 200
    else:
        return jsonify({"valid": False, "message": "Ten klucz jest już przypisany do innego urządzenia!"}), 403

if __name__ == '__main__':
    # Uruchamiamy serwer na porcie 5000 (upewnij się, że port jest odblokowany w zaporze na serwerze)
    app.run(host='0.0.0.0', port=5000)