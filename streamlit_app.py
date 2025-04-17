import requests

def fetch_studies_lung_cancer_in_japan():
    """
    ClinicalTrials.gov v2 API を使い、
    - "lung cancer" キーワード
    - 日本国内（Location: Japan）
    - 実施中 (オプション; 例として OverallStatus=RECRUITING や ACTIVE_NOT_RECRUITING 等)
    等で絞り込んだ治験を取得し、簡易的にデータを抽出する例。
    """

    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    # 例: lung cancerかつLocationがJapanで、現時点でrecruiting(または実施中)のものを絞り込みたいケース
    # "filter.overallStatus":"RECRUITING" を指定する等、実際は仕様に合わせて変更
    # ※ 最新の公式ドキュメント/サンプルURLを確認の上、クエリパラメータをアップデートしてください
    
    params = {
        "query": "lung cancer",
        "country": "Japan",                # 国名を指定
        "status": "Recruiting",           # 例: 実際には 'Active, not recruiting' など複数条件をOR検索したい場合がある
        "pageSize": 20,                   # 1ページ当たりの取得件数
        "page": 1                         # ページ番号
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()  # 4xx/5xx エラー時は例外

    data = response.json()
    # このあたりで data["data"]["studies"] という構造を想定 (v2 Beta 仕様)
    # 実際に返ってくるレスポンスを st.json() などで確認して、キー名を合わせてください
    return data

def main():
    try:
        # API呼び出し
        raw_data = fetch_studies_lung_cancer_in_japan()
        
        # raw_data全体を確認したい場合は print(raw_data) などで出力
        # ここでは data["data"]["studies"] の中身を簡単に表示する例
        if "data" in raw_data and "studies" in raw_data["data"]:
            studies_list = raw_data["data"]["studies"]
            print(f"取得した治験数: {len(studies_list)}")
            
            for study in studies_list:
                # キー名は実際のレスポンスで確認してください
                # 例: nctId, title, status, conditions, locations...
                nct_id = study.get("nctId", "N/A")
                title = study.get("title", "N/A")
                status = study.get("overallStatus", "N/A")
                # v2では location も構造が異なる可能性があるので要確認
                locations = study.get("locations", [])

                print("NCT ID:", nct_id)
                print("Title:", title)
                print("Status:", status)
                print("Locations:")
                for loc in locations:
                    facility = loc.get("facility", "N/A")
                    country = loc.get("country", "N/A")
                    # もし country=="Japan" をさらにチェックしたければここで判定
                    print(f" - Facility: {facility}, Country: {country}")
                print("-" * 80)

        else:
            print("Expected 'data' or 'studies' key not found in the response.")
            # 必要があれば raw_data をprintして内容をチェックする
            print(raw_data)

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
