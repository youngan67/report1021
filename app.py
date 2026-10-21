import pandas as pd
import streamlit as st
import plotly.express as px

# ★ 화면 설정과 제목
st.set_page_config(page_title="철도 데이터 분석", layout="wide")
st.title("철도 데이터 분석 대시보드")
st.caption("교육용 가상 자료입니다. AI 확인후보는 고장 확정이 아닙니다.")

# 데이터 읽기: 2일차 설비 결과
df = pd.read_csv("analysis_result.csv")
df["측정시각"] = pd.to_datetime(df["측정시각"])
df["목표시각"] = pd.to_datetime(df["목표시각"])

# ★ 데이터 읽기: 1일차 역별 이용 자료
passengers = pd.read_csv("station_daily_usage.csv")
passengers["일자"] = pd.to_datetime(passengers["일자"])
passengers["이용건수"] = passengers["승차건수"] + passengers["하차건수"]

# ★ 왼쪽 사이드바: 조회 조건
st.sidebar.header("조회 조건")
equipment = st.sidebar.selectbox("설비 선택", df["설비ID"].unique())
view = df[df["설비ID"] == equipment]

start = st.sidebar.date_input("시작일", view["측정시각"].min().date())
end = st.sidebar.date_input("종료일", view["측정시각"].max().date())
view = view[(view["측정시각"].dt.date >= start) & (view["측정시각"].dt.date <= end)]

# 계산: 후보와 예측 오차
candidates = view[view["AI결과"] == "확인후보"]
pred = view.dropna(subset=["다음온도_C", "AI예측온도_C"])
mae = (pred["다음온도_C"] - pred["AI예측온도_C"]).abs().mean()

# ★ 탭 3개
tab1, tab2, tab3 = st.tabs(["1일차 · 역별 이용 현황", "2일차 · 설비 점검과 예측", "업무 보고"])

# ---------- 탭 1: 1일차 ----------
with tab1:
    station = passengers.groupby("역명")[["이용건수", "민원건수"]].sum().reset_index()
    daily = passengers.groupby("일자")["이용건수"].sum().reset_index()

    st.dataframe(station)
    st.plotly_chart(px.bar(station, x="역명", y="이용건수", title="역별 이용건수"))
    st.plotly_chart(px.bar(station, x="역명", y="민원건수", title="역별 민원건수"))
    st.plotly_chart(px.line(daily, x="일자", y="이용건수", title="날짜별 이용건수(4개 역 합계)"))
    st.caption("이용건수는 승차·하차 기록의 합이며, 고유 이용자 수가 아닙니다.")

# ---------- 탭 2: 2일차 ----------
with tab2:
    if len(view) == 0:
        st.warning("조회 결과가 없습니다. 왼쪽에서 날짜를 다시 선택하세요.")

    # ★ 숫자 카드 3개를 한 줄에
    col1, col2, col3 = st.columns(3)
    col1.metric("조회 건수", len(view))
    col2.metric("AI 확인후보", len(candidates))
    col3.metric("예측 MAE", f"{mae:.2f} ℃")

    fig = px.line(view, x="측정시각", y="온도_C", title="온도 추이와 AI 확인후보")
    fig.add_scatter(x=candidates["측정시각"], y=candidates["온도_C"],
                    mode="markers", name="확인후보", marker=dict(color="red", size=10))
    st.plotly_chart(fig)

    fig2 = px.line(pred, x="목표시각", y=["다음온도_C", "AI예측온도_C"], title="실제 온도와 AI 예측 온도")
    st.plotly_chart(fig2)

    st.write("AI 확인후보 목록")
    st.dataframe(candidates)

# ---------- 탭 3: 업무 보고 ----------
with tab3:
    note = st.text_area("확인할 사항 및 조치 제안", "센서 상태와 운전 조건을 확인한 후 담당자 검토가 필요합니다.")

    report = f"""설비: {equipment}
조회 기간: {start} ~ {end}
조회 건수: {len(view)}건
AI 확인후보: {len(candidates)}건
온도 예측 MAE: {mae:.2f} ℃ ({len(pred)}건 비교)
업무 메모: {note}
교육용 가상 자료이며, 확인후보는 고장 확정이 아닙니다."""
    st.text(report)

    st.download_button("조회 결과 CSV", view.to_csv(index=False).encode("utf-8-sig"), "dashboard_result.csv")
    st.download_button("점검 후보 CSV", candidates.to_csv(index=False).encode("utf-8-sig"), "inspection_candidates.csv")
    st.download_button("보고서 TXT", report.encode("utf-8-sig"), "dashboard_report.txt")
