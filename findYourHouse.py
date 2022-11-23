from datetime import datetime

import folium
import pandas as pd
import PublicDataReader as pdr
import requests
from auth import geocodeKey, myKey
from folium.plugins import MarkerCluster

# 2. 공공 데이터 포털 OpenAPI 서비스 인증키 입력하기
serviceKey = myKey

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
        pass


# 4. 지역코드(시군구코드) 검색하기
# sigunguName = "금천구"                            # 시군구코드: 41135
def findcode(sigunguName):
    code = pdr.code_bdong()
    return code.loc[
        (code["시군구명"].str.contains(sigunguName, na=False)) & (code["읍면동명"].isna())
    ].iloc[0, 2]


# 5. 지역, 월 별 데이터 프레임 만들기
df = pd.DataFrame()
now = datetime.now()
sigunguNames = []
num = int(input("몇 군데 정보를 가져오길 원하십니까?"))

sigunguNames = [input("지역구를 입력해주세요. ex) 영등포구") for _ in range(num)]
months = input("언제부터 자료를 원해요? ex) 202201")
for sigunguName in sigunguNames:
    prod = "오피스텔"  # 부동산 상품 종류 (ex. 아파트, 오피스텔, 단독다가구 등)
    trans = "전월세"  # 부동산 거래 유형 (ex. 매매, 전월세)
    sigunguCode = findcode(sigunguName)
    startYearMonth = months
    endYearMonth = now.date().strftime("%Y%m")
    df1 = ts.collect_data(prod, trans, sigunguCode, startYearMonth, endYearMonth)
    df = pd.concat([df, df1])


minsize = round(int(input('몇 평 이상을 원하십니까?')) / 0.3025, 1)
maxDeposit = int(input('최대 보증금은? (단위: 만원)'))
maxRent = int(input('최대 월세는?(단위: 만원)'))
minFloor = int(input('몇 층이상을 원하십니까?'))

df = df[
    df['층'] >= minFloor,
    df['전용면적'] >= minFloor,
    df['보증금'] <= maxDeposit,
    df['월세'] <= maxRent
]

df["경도"], df["위도"] = (df["시군구"] + " " + df["법정동"] + " " + df["지번"]).apply(geocode)


m = folium.Map(location=[37.5197424168999, 126.940030048557], zoom_start=13)

coords = df[["위도", "경도", "단지", "보증금", "월세", "건축년도", "층", "전용면적", "년", "월"]]
coords_half = df1[["위도", "경도", "단지", "보증금", "월세", "건축년도", "층", "전용면적", "년", "월"]]

marker_cluster = MarkerCluster().add_to(m)

for lat, long, name, saveMoney, money, byear, floor, size, year, month in zip(
    coords["위도"],
    coords["경도"],
    coords["단지"],
    coords["보증금"],
    coords["월세"],
    coords["건축년도"],
    coords["층"],
    coords["전용면적"],
    coords["년"],
    coords["월"],
):

    if not pd.isna(byear):
        byear = int(byear)
    iframe = (
        "거래연월: {5}년 {6}월 \n건축연도: {2}\n보증금: {0}만원\n월세: {1}만원\n 평수:{3}\n 층:{4}".format(
            saveMoney, money, byear, round(size * 0.3025, 1), floor, year, month
        )
    )
    popup = folium.Popup(iframe, min_width=200, max_width=500)
    folium.Marker(
        [lat, long], icon=folium.Icon(color="green"), popup=popup, tooltip=name
    ).add_to(marker_cluster)
for lat, long, name, saveMoney, money, byear, floor, size, year, month in zip(
    coords_half["위도"],
    coords_half["경도"],
    coords_half["단지"],
    coords_half["보증금"],
    coords_half["월세"],
    coords_half["건축년도"],
    coords_half["층"],
    coords_half["전용면적"],
    coords_half["년"],
    coords_half["월"],
):

    if not pd.isna(byear):
        byear = int(byear)
    iframe = "거래연월: {5}년 {6}월 \n건축연도: {2}\n보증금: {0}만원\n월세: {1}만원\n {3}평\n {4}층".format(
        saveMoney, money, byear, round(size * 0.3025, 1), floor, year, month
    )
    popup = folium.Popup(iframe, min_width=200, max_width=500)
    folium.Marker(
        [lat, long], icon=folium.Icon(color="red"), popup=popup, tooltip=name
    ).add_to(marker_cluster)

m.save("test.html")
