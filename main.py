import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import date, timedelta, datetime
import os

# --- Tənzimləmələr ---
FILE_NAME = "CBAR_Gold_Rates.xlsx"
START_DATE_DEFAULT = date(2024, 1, 1) 

def get_gold_rate(query_date):
    date_str = query_date.strftime("%d.%m.%Y")
    url = f"https://www.cbar.az/currencies/{date_str}.xml"
    
    # Brauzer kimi görünmək üçün başlıq (Header) əlavə edirik
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # headers parametrini bura əlavə edirik
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            xau_node = root.find(".//Valute[@Code='XAU']")
            if xau_node is not None:
                val = xau_node.find('Value').text
                return float(val.replace(',', '.'))
        else:
            print(f"Server xətası ({date_str}): Status Code {response.status_code}")
            
    except Exception as e:
        print(f"Xəta ({date_str}): {e}")
    
    return None

def main():
    current_date = START_DATE_DEFAULT
    existing_data = []
    
    # Mövcud faylı yoxla və son tarixi tap
    if os.path.exists(FILE_NAME):
        try:
            df_existing = pd.read_excel(FILE_NAME)
            if not df_existing.empty:
                last_date_str = df_existing.iloc[-1]['Tarix']
                last_date = datetime.strptime(last_date_str, "%d.%m.%Y").date()
                current_date = last_date + timedelta(days=1)
                existing_data = df_existing.to_dict('records')
        except:
            print("Fayl oxunarkən xəta oldu, yenidən yaradılır.")

    # Hədəf: Bu gün (Skript hər işləyəndə bu günə qədər olanı çəkəcək)
    target_date = date.today()

    if current_date > target_date:
        print("Məlumatlar artıq ən son tarixə qədər yenilənib.")
        return

    print(f"Məlumat toplanır: {current_date.strftime('%d.%m.%Y')} - {target_date.strftime('%d.%m.%Y')}")
    new_data = []

    while current_date <= target_date:
        # Şənbə (5) və Bazar (6) günlərini burax
        if current_date.weekday() < 5: 
            rate = get_gold_rate(current_date)
            if rate is not None:
                print(f"✔ {current_date.strftime('%d.%m.%Y')}: {rate}")
                new_data.append({
                    "Tarix": current_date.strftime("%d.%m.%Y"),
                    "XAU_Qiymeti": rate
                })
        current_date += timedelta(days=1)

    # Məlumatları yadda saxla
    if new_data:
        all_data = existing_data + new_data
        df_final = pd.DataFrame(all_data)
        df_final.to_excel(FILE_NAME, index=False)
        print(f"Tamamlandı! {len(new_data)} yeni sətir əlavə olundu.")
    else:
        print("Yeni məlumat yoxdur.")

if __name__ == "__main__":

    main()
