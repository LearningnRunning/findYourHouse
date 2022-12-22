from datetime import datetime

import pandas as pd
import PublicDataReader as pdr
import requests
from auth import geocodeKey, serviceKey

# 3. 국토교통부 실거래가 정보 조회 OpenAPI 세션 정의하기
# debug: True이면 모든 메시지 출력, False이면 오류 메시지만 출력 (기본값: False)
ts = pdr.Transaction(serviceKey, debug=True)


def geocode(address):
    apiurl = "http://api.vworld.kr/req/address?"
    params = {
        "service": "address",
        "request": "getcoord",
        "crs": "epsg:4326",
        "address": address,
        "format": "json",
        "type": "parcel",
        "key": geocodeKey,
    }
    try:
        response = requests.get(apiurl, params=params)

        json_data = response.json()

        if json_data["response"]["status"] == "OK":
            x = json_data["response"]["result"]["point"]["x"]
            y = json_data["response"]["result"]["point"]["y"]
            print(json_data["response"]["refined"]["text"])
            print("\n경도: ", x, "\n위도: ", y)
            return x, y
    except Exception as e:
        print(e)
        print(address)
        return 0, 0


# 4. 지역코드(시군구코드) 검색하기
# sigunguName = "금천구"                            # 시군구코드: 41135
def findcode(sigunguName):
    code = pdr.code_bdong()
    return code.loc[
        (code["시군구명"].str.contains(sigunguName, na=False)) & (code["읍면동명"].isna())
    ].iloc[0, 2]


def makeDf(sigunguName):
    # 5. 지역, 월 별 데이터 프레임 만들기

    now = datetime.now()

    prods = ["오피스텔", "아파트", "단독다가구"]  # 부동산 상품 종류 (ex. 아파트, 오피스텔, 단독다가구 등)
    trans = ["전월세", "매매"]  # 부동산 거래 유형 (ex. 매매, 전월세)
    sigunguCode = findcode(sigunguName)
    print(sigunguName)
    startYearMonth = 202101
    endYearMonth = now.date().strftime("%Y%m")

    for prod in prods:
        for tran in trans:
            df1 = ts.collect_data(prod, tran, sigunguCode, startYearMonth, endYearMonth)

    # df["경도"], df["위도"] = (df["시군구"] + " " + df["법정동"] + " " + df["지번"]).apply(geocode)
    df1["region"] = sigunguName
    return df1


if __name__ == "__main__":
    sigunguNames = (
        "종로구중구용산구성동구광진구동대문구중랑구성북구강북구도봉구노원구은평구서대문구마포구양천구강서구구로구금천구영등포구동작구관악구서초구강남구송파구강동구"
    )
    sigunguNames = sigunguNames.split("구")
    df = pd.DataFrame()
    for sigunguName in sigunguNames:
        tmp_df = makeDf(sigunguName + "구")
        df = pd.concat([df, tmp_df])

    df.to_csv("DB.csv", index=False, encoding="utf-8-sig")
