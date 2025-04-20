import streamlit as st
import pandas as pd
import requests
import time
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Chrome driver path for Streamlit Cloud
CHROME_BINARY_PATH = "/usr/bin/chromium"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"

# Chrome Options
def get_chrome_options():
    options = Options()
    options.binary_location = CHROME_BINARY_PATH
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0")
    return options


# CSVダウンロードリンク生成
def get_csv_download_link(df, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">CSVとしてダウンロード</a>'
    return href


# ====== jRCT検索関数 ======
def search_jrct(disease_name, free_keyword):
    options = get_chrome_options()
    results = []

    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    try:
        driver.get("https://jrct.mhlw.go.jp/search")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "reg-plobrem-1"))).send_keys(disease_name)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "demo-1"))).send_keys(free_keyword)

        checkbox = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "reg-recruitment-2")))
        if not checkbox.is_selected():
            checkbox.click()

        search_btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "検索")]')))
        driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
        time.sleep(1)
        search_btn.click()

        rows = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.table-search tbody tr"))
        )

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            results.append({
                "臨床研究実施計画番号": cols[0].text.strip(),
                "研究の名称": cols[1].text.strip(),
                "対象疾患名": cols[2].text.strip(),
                "研究の進捗状況": cols[3].text.strip(),
                "公表日": cols[4].text.strip(),
                "詳細": cols[5].find_element(By.TAG_NAME, "a").get_attribute("href")
            })

    finally:
        driver.quit()

    return pd.DataFrame(results)


# ====== ClinicalTrials.gov API 検索関数 ======
def fetch_ctgov(cond_value, status_value, loc_value, other_terms="EGFR"):
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": cond_value,
        "query.term": other_terms,
        "filter.overallStatus": status_value,
        "query.locn": loc_value
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    studies = response.json().get("studies", [])
    
    records = []
    for study in studies:
        records.append({
            "Study ID": study.get("protocolSection", {}).get("identificationModule", {}).get("nctId", "N/A"),
            "Title": study.get("protocolSection", {}).get("identificationModule", {}).get("officialTitle", "N/A"),
            "Status": study.get("protocolSection", {}).get("statusModule", {}).get("overallStatus", "N/A"),
            "Conditions": ", ".join(study.get("protocolSection", {}).get("conditionsModule", {}).get("conditions", [])),
            "URL": f'https://clinicaltrials.gov/study/{study.get("protocolSection", {}).get("identificationModule", {}).get("nctId", "")}'
        })

    return pd.DataFrame(records)


# ====== Streamlit UI ======
st.set_page_config(page_title="臨床試験 検索アプリ", layout="wide")
st.title("🧪 臨床試験検索ツール（jRCT & ClinicalTrials.gov）")

tab1, tab2 = st.tabs(["🔍 jRCT", "🌐 ClinicalTrials.gov"])

# ----- jRCT -----
with tab1:
    st.subheader("jRCT 検索")
    disease = st.text_input("疾患名", "肺がん")
    keyword = st.text_input("フリーワード", "EGFR")
    if st.button("jRCTで検索"):
        with st.spinner("検索中..."):
            df_jrct = search_jrct(disease, keyword)
            if not df_jrct.empty:
                st.success(f"{len(df_jrct)} 件の結果が見つかりました。")
                st.dataframe(df_jrct)
                st.markdown(get_csv_download_link(df_jrct, "jrct_results.csv"), unsafe_allow_html=True)
            else:
                st.warning("結果が見つかりませんでした。")

# ----- ClinicalTrials.gov -----
with tab2:
    st.subheader("ClinicalTrials.gov 検索")
    cond = st.text_input("Condition (例: lung cancer)", "lung cancer")
    status = st.text_input("Recruitment Status", "RECRUITING")
    loc = st.text_input("Location (国や地域)", "Japan")
    other_terms = st.text_input("Other terms (例: EGFR)", "EGFR")
    if st.button("ClinicalTrials.gov で検索"):
        with st.spinner("検索中..."):
            df_ctgov = fetch_ctgov(cond, status, loc, other_terms)
            if not df_ctgov.empty:
                st.success(f"{len(df_ctgov)} 件の結果が見つかりました。")
                st.dataframe(df_ctgov)
                st.markdown(get_csv_download_link(df_ctgov, "ctgov_results.csv"), unsafe_allow_html=True)
            else:
                st.warning("結果が見つかりませんでした。")
