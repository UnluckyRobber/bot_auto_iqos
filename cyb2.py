print("--- START SKRYPTU ---")

from playwright.sync_api import sync_playwright
import random
import imaplib
import email
import re
import time
import requests
import os

# --- KONFIGURACJA CYBERYOZH API ---
API_KEY = "M46cMXRX.z2IOfCRr74dlUDR3ALTTHvgHVVotBbJD"

# --- FUNKCJA DO POBIERANIA I PRZENOSZENIA E-MAILI ---
def get_and_move_email(source_file="aliases.txt", used_file="email.txt"):
    if not os.path.exists(source_file):
        print(f"Błąd: Nie znaleziono pliku {source_file} z aliasami!")
        return None
        
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    lines = [line for line in lines if line.strip()]
        
    if not lines:
        return None
        
    email_to_use = lines[0].strip()
    
    with open(source_file, 'w', encoding='utf-8') as f:
        f.writelines(lines[1:])
        
    with open(used_file, 'a', encoding='utf-8') as f:
        f.write(email_to_use + "\n")
        
    return email_to_use

# --- FUNKCJE CYBERYOZH ---
def buy_number():
    headers = {
        'accept': 'application/json',
        'X-Api-Key': API_KEY,
        'Content-Type': 'application/json'
    }

    country_code = "117" # Portugalia
    try:
        c_res = requests.get("https://app.cyberyozh.com/api/v1/numbers/countries/", headers=headers, timeout=15)
        if c_res.status_code == 200:
            for c in c_res.json():
                if "portugal" in c["name"].lower():
                    country_code = c["code"]
                    break
    except Exception as e:
        print(f"[DEBUG] Błąd pobierania listy krajów: {e}")

    service_code = "ot" # Any Other
    try:
        s_res = requests.get("https://app.cyberyozh.com/api/v1/numbers/services/", headers=headers, timeout=15)
        if s_res.status_code == 200:
            for s in s_res.json():
                if "other" in s["name"].lower() or "any" in s["name"].lower():
                    service_code = s["code"]
                    break
    except Exception as e:
        print(f"[DEBUG] Błąd pobierania listy usług: {e}")

    url = "https://app.cyberyozh.com/api/v1/numbers/"
    payload = {
        "provider": "virtual",
        "period": "MIN_15",
        "service_code": service_code,
        "country_code": country_code,
        "need_fraud_score": False
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 201:
            data = response.json()
            order_id = data.get("id")
            print(f"[DEBUG CyberYozh] Utworzono zamówienie ({order_id}).")

            for attempt in range(40):
                print(f"[{attempt+1}/40] Oczekiwanie na przydzielenie numeru przez CyberYozh...")
                time.sleep(4)
                
                check_url = f"https://app.cyberyozh.com/api/v1/numbers/{order_id}/"
                try:
                    check_res = requests.get(check_url, headers=headers, timeout=15)
                    if check_res.status_code == 200:
                        order_info = check_res.json()
                        status = order_info.get("status")
                        
                        if status == "waiting":
                            phone = order_info.get("phone_number")
                            if phone:
                                print("[DEBUG CyberYozh] Numer został pomyślnie przydzielony!")
                                return phone, order_id
                                
                        elif status in ["canceled", "refund"]:
                            print("[DEBUG CyberYozh] Zamówienie anulowane przez serwer (Brak numerów w puli).")
                            return None, None
                except Exception:
                    pass
            
            print("Błąd: Serwer CyberYozh nie przypisał numeru w wyznaczonym czasie.")
            try:
                requests.put(f"https://app.cyberyozh.com/api/v1/numbers/{order_id}/cancel/", headers=headers, timeout=10)
            except Exception:
                pass
                
            return None, order_id
        else:
            print(f"Błąd API CyberYozh przy zakupie ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Błąd sieciowy zakupu numeru: {e}")
    return None, None

def get_sms_code(order_id):
    headers = {
        'accept': 'application/json',
        'X-Api-Key': API_KEY
    }
    
    url = f"https://app.cyberyozh.com/api/v1/numbers/{order_id}/messages/"
    
    for attempt in range(24):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    latest_msg = results[0]
                    raw_sms_code = str(latest_msg.get("sms_code", ""))
                    raw_text = str(latest_msg.get("text", ""))
                    combined_text = f"{raw_sms_code} {raw_text}"
                    
                    match = re.search(r'\b\d{4,6}\b', combined_text)
                    if match:
                        extracted_code = match.group(0)
                        print(f"[{attempt+1}/24] SUKCES! Wyodrębniono sam kod: {extracted_code}")
                        return extracted_code
                    else:
                        print(f"[{attempt+1}/24] SMS dotarł, ale nie potrafię znaleźć w nim cyfr.")
                else:
                    print(f"[{attempt+1}/24] Oczekiwanie na SMS od CyberYozh...")
            else:
                print(f"[{attempt+1}/24] Oczekiwanie (Status odp: {response.status_code})")
                
        except Exception as e:
            print(f"Błąd sieciowy podczas sprawdzania SMS: {e}")
            
        time.sleep(5)
    return None

# --- FUNKCJA MAILCOW ---
def get_otp_from_mailcow(main_email, main_password, target_alias, imap_server):
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(main_email, main_password)
        mail.select("inbox")

        print("Szukam maila z kodem OTP...")
        for _ in range(15):
            status, messages = mail.search(None, f'(UNSEEN TO "{target_alias}")')
            message_ids = messages[0].split()

            if message_ids:
                latest_email_id = message_ids[-1]
                status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()

                        match = re.search(r'\b\d{4}\b', body)
                        if match:
                            otp_code = match.group(0)
                            mail.store(latest_email_id, '+FLAGS', '\\Seen')
                            mail.logout()
                            return otp_code
            time.sleep(4)
        mail.logout()
    except Exception as e:
        print(f"Błąd poczty: {e}")
    return None

# --- GŁÓWNA AUTOMATYZACJA ---
def run(playwright):
    MAIN_MAILBOX = "admin@yuhoo.pl"
    MAIN_PASSWORD = "2C3ombc94236977"
    IMAP_SERVER = "mail.yuhoo.pl"

    first_names = [
        "Alessia", "Lorenzo", "Sofia", "Matteo", "Giulia", 
        "Leonardo", "Aurora", "Alessandro", "Giorgia", "Francesco", 
        "Martina", "Andrea", "Chiara", "Davide", "Francesca", 
        "Federico", "Beatrice", "Simone", "Alice", "Mattia"
    ]
    last_names = [
        "Conti", "Rossi", "Rizzo", "Romano", "Costa", 
        "Ferrari", "Marino", "Gallo", "Bruno", "Bianchi", 
        "Esposito", "DeLuca", "Colombo", "Ricci", "Moretti", 
        "Giordano", "Barbieri", "Fontana", "Santoro", "Marchetti"
    ]
    
    # Uruchamiamy przeglądarkę tylko raz, aby zaoszczędzić czas
    browser = playwright.chromium.launch(
        headless=False,
        args=["--start-maximized", "--incognito"] 
    )
    
    konto_licznik = 1

    # GŁÓWNA PĘTLA
    while True:
        print(f"\n=======================================================")
        print(f"--- ROZPOCZYNAM TWORZENIE KONTA NR {konto_licznik} ---")
        print(f"=======================================================")

        selected_alias = get_and_move_email("aliases.txt", "email.txt")
        if not selected_alias:
            print("Brak kolejnych aliasów e-mail w pliku. Zakończenie pracy skryptu.")
            break
            
        print(f"Używam aliasu e-mail: {selected_alias}")

        # Otwieramy całkowicie czysty profil (nowy kontekst pozbawiony ciasteczek)
        context = browser.new_context(no_viewport=True) 
        page = context.new_page()

        try:
            print("Otwieranie strony rejestracji...")
            page.goto("https://www.ploom.it/it/auth#/register")
            page.evaluate("document.body.style.zoom = '0.65'")
            page.wait_for_timeout(3000)

            # Cookies i Popup
            try:
                if page.locator("#onetrust-accept-btn-handler").is_visible():
                    page.locator("#onetrust-accept-btn-handler").click(force=True)
                    page.wait_for_timeout(1000)
                if page.locator('[data-testid="confirm-button"]').is_visible():
                    page.locator('[data-testid="confirm-button"]').click(force=True)
                    page.wait_for_timeout(1000)
            except Exception:
                pass

            # Wypełnianie danych
            page.locator("#firstnameField").wait_for(state="visible")
            
            if page.locator("#email_control").is_editable():
                page.locator("#email_control").fill(selected_alias)
                page.keyboard.press("Tab")
                page.wait_for_timeout(500)

            page.locator("#firstnameField").fill(random.choice(first_names))
            page.locator("#lastnameField").fill(random.choice(last_names))
            page.locator("#password_input").fill("Haslo1212@")

            # Ustawienie roku
            try:
                page.locator("#dobYearSelectInput").click(force=True)
                page.keyboard.type("2000", delay=100)
                page.keyboard.press("Enter")
                page.wait_for_timeout(500)
            except Exception as e:
                print(f"Błąd ustawiania roku: {e}")

            # Zgody
            for consent in page.locator('input[name^="purposes."] + span').all():
                consent.click(force=True)
                page.wait_for_timeout(100)

            for radio in page.locator('input[type="radio"][value="true"] + span').all():
                radio.click(force=True)
                page.wait_for_timeout(100)

            # --- KROK 1: MAIL ---
            print("Czekam na kod mailowy...")
            email_otp = get_otp_from_mailcow(MAIN_MAILBOX, MAIN_PASSWORD, selected_alias, IMAP_SERVER)
            
            if email_otp:
                for index, digit in enumerate(email_otp):
                    field = page.locator(f'[data-testid="otpInput-{index}"]')
                    field.click(force=True)
                    field.fill("")
                    field.type(digit, delay=100)
                    page.wait_for_timeout(100)
                page.wait_for_timeout(2000) 
            else:
                print("Błąd: Nie odebrano maila. Zamykam sesję i przechodzę do następnego.")
                context.close()
                continue

            # --- KROK 2: SMS ---
            print("Kupuję numer w CyberYozh...")
            phone_number, order_id = buy_number()
            if not phone_number:
                print("Błąd numeru. Zamykam sesję i przechodzę do następnego.")
                context.close()
                continue
            
            clean_phone = str(phone_number).replace("+", "")
            if not clean_phone.startswith("351"):
                clean_phone = "351" + clean_phone
            final_phone_to_type = "+" + clean_phone
            
            phone_input = page.locator('input.PhoneInputInput')
            phone_input.wait_for(state="visible")
            phone_input.fill(final_phone_to_type)
            page.wait_for_timeout(1000)

            try:
                send_code_btn = page.locator('[data-testid="sendCode"]')
                page.click("body") 
                send_code_btn.wait_for(state="visible", timeout=5000)
                send_code_btn.click(force=True)
                page.wait_for_timeout(2000)
            except Exception as e:
                pass

            sms_otp = get_sms_code(order_id)
            if sms_otp:
                for index, digit in enumerate(sms_otp[:4]):
                    sms_field = page.locator(f'div[data-testid="otpContainer"] input[data-testid="otpInput-{index}"]')
                    sms_field.click(force=True)
                    sms_field.fill("")
                    sms_field.type(digit, delay=150)
                    page.wait_for_timeout(150)
                
                page.wait_for_timeout(1000)

                try:
                    continua_btn = page.locator('[data-testid="mergedRegistrationSubmitBtn"]')
                    continua_btn.wait_for(state="visible", timeout=5000)
                    continua_btn.click(force=True)
                except Exception:
                    pass
            else:
                print("Błąd odebrania SMS. Zamykam sesję i przechodzę do następnego.")
                context.close()
                continue

            # --- ZAKOŃCZENIE I RESTART ---
            print("Oczekuję na wczytanie okna powitalnego w Dashboardzie...")
            page.wait_for_url(re.compile(r".*/profile.*"), timeout=45000)
            
            # Wyszukiwanie popupu z powitaniem
            try:
                welcome_dialog = page.locator('dialog[data-testid="welcome-dialog"]')
                welcome_dialog.wait_for(state="visible", timeout=15000)
                print("Wykryto okno powitalne! Rejestracja zakończona sukcesem.")
                
                # Klikamy przycisk OK na oknie powitalnym
                ok_btn = page.locator('button[data-testid="okButton"]')
                if ok_btn.is_visible():
                    ok_btn.click(force=True)
                    page.wait_for_timeout(2000)
            except Exception:
                print("Nie wykryto okna powitalnego w czasie 15 sekund, ale adres to dashboard.")
            
            print(f"--- KONTO NR {konto_licznik} ZROBIONE POMYŚLNIE ---")
            konto_licznik += 1
            
        except Exception as e:
            print(f"Wystąpił niespodziewany błąd w trakcie obsługi konta: {e}")
            
        # Zawsze wykonaj to na końcu obrotu pętli (nawet po sukcesie)
        print("Czyszczenie historii, ciasteczek i zamykanie karty profilu...")
        context.close()
        time.sleep(2) # Krótki oddech dla przeglądarki przed startem nowego konta

    # Kiedy pętla się skończy (brak adresów e-mail)
    browser.close()

with sync_playwright() as p:
    run(p)
