import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

base_url = "https://www.itjobs.pt/emprego?q=data+analyst&sort=relevance&page={}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
}

all_jobs = []

for page in range(1, 10):  # tenta até 10 páginas
    print(f"🔎 A ler página {page}...")
    url = base_url.format(page)
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")

    # encontrar todos os blocos diários na página
    blocks = soup.select("div.block.borderless")
    if not blocks:
        print("🚫 Sem mais resultados — a parar.")
        break

    for block in blocks:
        # extrair a data do bloco
        date_box = block.select_one(".date-box")
        if date_box:
            day = date_box.select_one(".d-d").text.strip() if date_box.select_one(".d-d") else ""
            month = date_box.select_one(".d-m").text.strip() if date_box.select_one(".d-m") else ""
            date = f"{day} {month}"
        else:
            date = None

        # ofertas dentro desse bloco
        for li in block.select("ul.listing > li"):
            title_tag = li.select_one(".list-title a")
            title = title_tag.text.strip() if title_tag else None
            link = title_tag["href"] if title_tag else None
            if link and link.startswith("/"):
                link = "https://www.itjobs.pt" + link

            company_tag = li.select_one(".list-name a")
            company = company_tag.text.strip() if company_tag else None

            details_tag = li.select_one(".list-details")
            details = details_tag.get_text(" ", strip=True) if details_tag else None

            all_jobs.append({
                "date": date,
                "title": title,
                "company": company,
                "details": details,
                "link": link
            })

    time.sleep(1.5)  # boa prática para evitar bloqueios

df = pd.DataFrame(all_jobs)
# converter campo "date" para datetime com o ano atual
from datetime import datetime
# dicionário de meses em português → inglês
meses = {
    "jan": "Jan", "fev": "Feb", "mar": "Mar", "abr": "Apr", "mai": "May", "jun": "Jun",
    "jul": "Jul", "ago": "Aug", "set": "Sep", "out": "Oct", "nov": "Nov", "dez": "Dec"
}

# traduzir mês antes de converter
df["date"] = df["date"].replace(meses, regex=True)

# converter para datetime com o ano atual
from datetime import datetime
df["date"] = pd.to_datetime(
    df["date"].apply(lambda x: f"{x} {datetime.now().year}"),
    format="%d %b %Y", errors="coerce"
)
df = df.sort_values("date", ascending=False)

import os
from datetime import datetime

csv_path = "itjobs_data_analyst.csv"

# Adiciona coluna "ativo" = 1 às novas extrações
df["ativo"] = 1

if os.path.exists(csv_path):
    # Carrega histórico existente
    df_hist = pd.read_csv(csv_path)

    # 1️⃣ Verificar novos anúncios (novos links)
    novos = df[~df["link"].isin(df_hist["link"])]
    if not novos.empty:
        print(f"🆕 {len(novos)} novas ofertas adicionadas.")

    # 2️⃣ Atualizar estado dos existentes
    df_hist["ativo"] = df_hist["link"].isin(df["link"]).astype(int)

    # 3️⃣ Juntar tudo
    df_final = pd.concat([df_hist, novos], ignore_index=True)
else:
    print("📁 Criado novo histórico.")
    df_final = df.copy()

# 4️⃣ Eliminar duplicados por link (caso o mesmo apareça mais de uma vez)
df_final = df_final.drop_duplicates(subset="link", keep="last")
# ✅ Standardize the format of the “date” column to avoid problems in CSV.
df_final["date"] = pd.to_datetime(df_final["date"], errors="coerce").dt.strftime("%Y-%m-%d")
# 5️⃣ Guardar o CSV atualizado
df_final.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"💾 Histórico atualizado: {len(df_final)} registos guardados em '{csv_path}'")

print("✅ Execução concluída com sucesso!")