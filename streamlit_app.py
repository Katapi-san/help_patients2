import streamlit as st
import requests
import pandas as pd

def fetch_studies_v2(cond_value, overall_status_value, location_value):
    """
    ClinicalTrials.gov v2 API (Beta) からデータを取得する関数。
    :param cond_value: query.cond に相当。例: "lung cancer" など
    :param overall_status_value: filter.overallStatus に相当。例: "RECRUITING" など
    :param location_value: query.locn に相当。例: "Japan" など
    :return: API レスポンス(JSON)を Python の辞書 として返す
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": cond_value,                  
        "filter.overallStatus": overall_status_value,  
        "query.locn": location_value               
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()  # 4xx/5xx エラー時は例外

    return response.json()


def parse_studies_to_table(json_data):
    """
    レスポンスの JSON から特定の項目を抽出し、pandas DataFrame を返す。
    対象項目(例):
      - nctId
      - title -> Study Title
      - studyPageUrl -> Study URL
      - status -> Study Status
      - briefSummary -> Brief Summary
      - conditions -> Conditions (配列をカンマ区切りで連結)
      - interventions -> Interventions (配列をカンマ区切りで連結)
      - sponsor -> Sponsor
      - phase -> Phases
      - startDate -> Start Date
      - primaryCompletionDate -> Primary Completion Date
      - completionDate -> Completion Date
      - lastUpdatePostDate -> Last Update Posted
    """
    import pandas as pd

    if not isinstance(json_data, dict):
        return pd.DataFrame()

    data_obj = json_data.get("data", {})
    studies = data_obj.get("studies", [])
    if not isinstance(studies, list):
        return pd.DataFrame()

    rows = []
    for study in studies:
        # 返ってくるJSONを st.write(study) で確認し、キー名を調整してください。
        nct_id = study.get("nctId", "")
        title = study.get("title", "")
        study_url = study.get("studyPageUrl", "")
        status = study.get("status", "")
        brief_summary = study.get("briefSummary", "")

        # conditions は配列の可能性がある
        conditions = study.get("conditions", [])
        if isinstance(conditions, list):
            conditions = ", ".join(conditions)

        # interventions も配列の可能性がある
        interventions = study.get("interventions", [])
        if isinstance(interventions, list):
            interventions = ", ".join(interventions)

        # sponsor は文字列か辞書の場合がある
        sponsor = study.get("sponsor", "")
        if isinstance(sponsor, dict):
            sponsor = sponsor.get("name", "") or sponsor.get("agency", "")

        phase_data = study.get("phase", "")
        # 単一文字列か、リストか
        if isinstance(phase_data, list):
            phase_data = ", ".join(phase_data)

        start_date = study.get("startDate", "")
        primary_completion_date = study.get("primaryCompletionDate", "")
        completion_date = study.get("completionDate", "")
        last_update_posted = study.get("lastUpdatePostDate", "")

        row = {
            "nctId": nct_id,
            "Study Title": title,
            "Study URL": study_url,
            "Study Status": status,
            "Brief Summary": brief_summary,
            "Conditions": conditions,
            "Interventions": interventions,
            "Sponsor": sponsor,
            "Phases": phase_data,
            "Start Date": start_date,
            "Primary Completion Date": primary_completion_date,
            "Completion Date": completion_date,
            "Last Update Posted": last_update_posted,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def main():
    st.title("ClinicalTrials.gov v2 検索ツール（ベータ版）")

    # 入力フォーム
    cond_value = st.text_input("Condition (query.cond)", "lung cancer")
    overall_status_value = st.text_input("Overall Status (filter.overallStatus)", "RECRUITING")
    location_value = st.text_input("Location (query.locn)", "Japan")

    # 検索ボタン押下時に API 呼び出し
    if st.button("Search"):
        try:
            # ---------------------
            # 1) データ取得
            # ---------------------
            data = fetch_studies_v2(cond_value, overall_status_value, location_value)

            # ---------------------
            # 2) まずレスポンスをそのままパンダテーブル化（全フィールドをフラットに！）
            #    → data["data"]["studies"] がリストになっているはずなので、それを json_normalize する
            # ---------------------
            if "data" in data and "studies" in data["data"]:
                studies_raw = data["data"]["studies"]  # リスト
                # pd.json_normalize を使ってフラットにする
                df_raw = pd.json_normalize(studies_raw)
                st.subheader("■ 生テーブル (全フィールドの json_normalize)")
                st.dataframe(df_raw)
            else:
                st.warning("レスポンスに 'data' または 'studies' がありません。raw JSON を表示します。")
                st.json(data)
                return  # ここで終了

            # ---------------------
            # 3) 特定の項目だけを抽出して表に
            # ---------------------
            df_parsed = parse_studies_to_table(data)

            st.subheader("■ 抽出項目テーブル")
            if df_parsed.empty:
                st.warning("検索結果がないか、抽出できるデータがありませんでした。")
            else:
                st.dataframe(df_parsed)

        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: {e}")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
