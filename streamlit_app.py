# app.py
#############################################################################


from datetime import datetime

import folium
import pandas as pd
import PublicDataReader as pdr
import requests
import streamlit as st
from auth import geocodeKey, serviceKey
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

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


def makeDf(sigunguName):
    # 5. 지역, 월 별 데이터 프레임 만들기
    df = pd.DataFrame()
    now = datetime.now()

    prod = "오피스텔"  # 부동산 상품 종류 (ex. 아파트, 오피스텔, 단독다가구 등)
    trans = "전월세"  # 부동산 거래 유형 (ex. 매매, 전월세)
    sigunguCode = findcode(sigunguName)
    startYearMonth = 202101
    endYearMonth = now.date().strftime("%Y%m")
    df1 = ts.collect_data(prod, trans, sigunguCode, startYearMonth, endYearMonth)
    df = pd.concat([df, df1])

    df["경도"], df["위도"] = (df["시군구"] + " " + df["법정동"] + " " + df["지번"]).apply(geocode)

    df.to_csv("DB.csv", index=False, encoding="utf-8-sig")


def main(sigunguName, size, deposit, rent, floor):

    df = df[
        df["층"].between(floor[0], floor[1])
        & df["전용면적"].between(size[0], size[1])
        & df["보증금"].between(deposit[0], deposit[1])
        & df["월세"].between(rent[0], rent[1])
    ]
    m = folium.Map(location=[37.5197424168999, 126.940030048557], zoom_start=13)

    coords = df[["위도", "경도", "단지", "보증금", "월세", "건축년도", "층", "전용면적", "년", "월"]]

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
        iframe = "거래연월: {5}년 {6}월 \n건축연도: {2}\n보증금: {0}만원\n월세: {1}만원\n 평수:{3}\n 층:{4}".format(
            saveMoney, money, byear, round(size * 0.3025, 1), floor, year, month
        )
        popup = folium.Popup(iframe, min_width=200, max_width=500)
        folium.Marker(
            [lat, long], icon=folium.Icon(color="green"), popup=popup, tooltip=name
        ).add_to(marker_cluster)

    return m


st.sidebar.header("시세는 알고 가자")
name = st.sidebar.selectbox("Name", ["전·월세", "매매"])

if name == "전·월세":
    st.title("epi1_100_face")

    rent = st.slider("월세", value=(30, 80), max_value=300)
    st.write("생각하시는 월세는 {0} ~ {1} 만원입니다.".format(rent[0], rent[1]))

    deposit = st.slider("보증금", value=(800, 20000))
    st.write("생각하시는 보증금은 {0} ~ {1} 만원입니다.".format(deposit[0], deposit[1]))

    size = st.slider("평수", value=(8, 24))
    st.write("생각하는 평수는 {0} ~ {1}평.".format(size[0], size[1]))
    size = (round(size[0] / 0.3025, 1), round(size[1] / 0.3025, 1))
    floor = st.slider("층수", value=(1, 2), max_value=125)
    st.write("생각하는 층수는 {0} ~ {1}층.".format(floor[0], floor[1]))

    sigunguName = st.text_input("검색할 지역을 입력해주세요.")
    if sigunguName:
        m = main(sigunguName, size, deposit, rent, floor)
        st_data = folium_static(m, width=500, height=700)

elif name == "매매":
    st.title("epi1_100_face")
    allPrice = st.slider("전세", value=(15000, 70000))
    st.write("생각하시는 매매가는 {0} ~ {1} 만원입니다.".format(allPrice[0], allPrice[1]))
