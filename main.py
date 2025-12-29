import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import date, timedelta, datetime
import os
import time

# --- Tənzimləmələr ---
FILE_NAME = "CBAR_Gold_Rates.xlsx"
START_DATE_DEFAULT = date(2024, 1, 1)

def get_gold_rate(query_date):
    date_str = query_date.strftime("%d.%m.%Y")
    url = f"https://www.cbar.az/currencies/{date_str}.xml"
    
    # Bloklanmamaq üçün başlıqlar
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            xau_node = root.find(".//Valute[@Code='XAU']")
            if xau_node is not None:
                val = xau_node.find('Value').text
                return float(val.replace(',', '.'))
        elif response.status_code == 404:
            print(f"⚠ {date_str}: XML tapılmadı (Hələ dərc olunmayıb?)")
        else:
            print(f"⚠ Server xətası ({date_str}): Kod {response.status_code}")
            
    except Exception as e:
        print(f"❌ Xəta ({date_str}): {e}")
    
    return None

def main():
    print("Skript işə düşdü...")
    current_date = START_DATE_DEFAULT
    existing_data = []
    
    # 1. Mövcud faylı və son tarixi yoxla
    if os.path.exists(FILE_NAME):
        print(f"Fayl tapıldı: {FILE_NAME}")
        try:
            df_existing = pd.read_excel(FILE_NAME)
            if not df_existing.empty:
                # Son sətri götürürük
                last_val = df_existing.iloc[-1]['Tarix']
                
                # Tarix formatını dəqiqləşdiririk (String vs Timestamp problemi həlli)
                if isinstance(last_val, (pd.Timestamp, datetime)):
                    last_date = last_val.date()
                else:
                    last_date = datetime.strptime(str(last_val), "%d.%m.%Y").date()
                
                print(f"Fayldakı son tarix: {last_date.strftime('%d.%m.%Y')}")
                current_date = last_date + timedelta(days=1)
                existing_data = df_existing.to_dict('records')
            else:
                print("Fayl boşdur, başlanğıcdan başlanılır.")
        except Exception as e:
            print(f"❌ Fayl oxunarkən KRİTİK xəta: {e}")
            print("Məlumatlar yenidən toplanacaq (Backup rejimi).")
    else:
        print("Fayl yoxdur, yeni yaradılır.")

    target_date = date.today()
    print(f"Hədəf tarix: {target_date.strftime('%d.%m.%Y')}")

    if current_date > target_date:
        print("✅ Məlumatlar artıq ən son tarixə qədər yenilənib. İş dayandırılır.")
        return

    print(f"📥 Məlumat toplanır: {current_date.strftime('%d.%m.%Y')} - {target_date.strftime('%d.%m.%Y')}")
    
    new_data = []
    changes_made = False

    while current_date <= target_date:
        # Həftə sonlarını burax (0=Bazar ertəsi, 5=Şənbə, 6=Bazar)
        if current_date.weekday() < 5: 
            rate = get_gold_rate(current_date)
            if rate is not None:
                print(f"✔ {current_date.strftime('%d.%m.%Y')}: {rate}")
                new_data.append({
                    "Tarix": current_date.strftime("%d.%m.%Y"),
                    "XAU_Qiymeti": rate
                })
                changes_made = True
            else:
                print(f"✖ {current_date.strftime('%d.%m.%Y')}: Məlumat yoxdur")
        else:
             # Şənbə-Bazar mesajını gizlət ki, log təmiz qalsın
             pass

        current_date += timedelta(days=1)
        time.sleep(1) # CBAR-ı yükləməmək üçün fasilə

    # 3. Məlumatları yadda saxla
    if changes_made:
        all_data = existing_data + new_data
        df_final = pd.DataFrame(all_data)
        
        # Excel-ə yazarkən format problemi olmaması üçün hamısını string edirik
        df_final.to_excel(FILE_NAME, index=False)
        print(f"✅ Uğurla tamamlandı! {len(new_data)} yeni sətir əlavə olundu.")
    else:
        print("⚠ Heç bir yeni məlumat tapılmadı (və ya bu gün bayramdır).")

if __name__ == "__main__":
    main()
