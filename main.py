import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
import chardet

# ----------------------
# 1. 데이터 로딩 및 전처리
# ----------------------
@st.cache_data
def load_data():
    # 인코딩 자동 감지
    with open("소득5분위별_가구당_가계수지.csv", "rb") as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    print(f"Detected file encoding: {encoding}")

    df = pd.read_csv("소득5분위별_가구당_가계수지.csv", encoding=encoding)
    df = df.drop([0])  # 불필요한 첫 번째 행 제거 (반복되는 헤더)
    df = df.rename(columns={df.columns[0]: "소득분위", df.columns[1]: "항목"})
    df = df[df["소득분위"].isin(['1분위', '2분위', '3분위', '4분위', '5분위'])]  # 전체 평균 제외
    df = df.dropna(axis=1, how='any')

    # 열 이름 정제 (분기 -> datetime 형식)
    time_cols = df.columns[2:]
    new_cols = []
    for col in time_cols:
        try:
            year, quarter = col.split("/")
            dt = f"{year}Q{quarter}"
            new_cols.append(dt)
        except:
            new_cols.append(col)
    df.columns = list(df.columns[:2]) + new_cols

    return df

# ----------------------
# 2. 스트림릿 앱 레이아웃 설정
# ----------------------
st.set_page_config(page_title="소득 분위별 소비 분석", layout="wide")
st.title("💸 소득 5분위별 소비 패턴 변화 분석")

st.markdown("""
**분석 목표**: 물가 상승률(CPI)과 함께, 소득 5분위별 실질 소비 항목 변화를 비교하고 인플레이션의 영향을 분석합니다.
""")

# ----------------------
# 3. 데이터 불러오기 및 사용자 선택
# ----------------------
df = load_data()
소득분위_list = df['소득분위'].unique().tolist()
항목_list = df['항목'].unique().tolist()

col1, col2 = st.columns(2)
with col1:
    selected_소득분위 = st.selectbox("소득 분위 선택", 소득분위_list)
with col2:
    # default에 포함된 항목이 실제 항목 리스트에 있는지 확인
    기본값_후보 = ['소비지출', '식료품·비주류음료', '교통']
    유효한_기본값 = [항목 for 항목 in 기본값_후보 if 항목 in 항목_list]
    selected_항목 = st.multiselect("소비 항목 선택", 항목_list, default=유효한_기본값)

# ----------------------
# 4. 시각화 데이터 처리
# ----------------------
filtered_df = df[(df['소득분위'] == selected_소득분위) & (df['항목'].isin(selected_항목))]

df_melted = filtered_df.melt(id_vars=['소득분위', '항목'], var_name='시점', value_name='지출')
df_melted['시점'] = pd.PeriodIndex(df_melted['시점'], freq='Q').to_timestamp()
df_melted['지출'] = pd.to_numeric(df_melted['지출'], errors='coerce')

# ----------------------
# 5. Plotly 시각화
# ----------------------
fig = px.line(df_melted, x='시점', y='지출', color='항목', markers=True,
              title=f"{selected_소득분위} 소비 항목별 변화 추이",
              labels={'지출': '지출 금액(원)', '시점': '분기'})
fig.update_layout(legend_title="소비 항목", height=500)
st.plotly_chart(fig, use_container_width=True)

# ----------------------
# 6. 요약 인사이트 출력
# ----------------------
st.subheader("🔍 분석 인사이트")
st.markdown("""
- 소득이 낮을수록 필수 지출 항목(식료품, 주거비)의 비중이 상대적으로 높게 유지됩니다.
- 상위 분위는 문화, 교육, 보건 분야의 소비 증감이 뚜렷하게 나타날 수 있습니다.
- 분기별로 CPI와 병합하여 추가 분석할 수 있습니다.
""")









#진단용 코드
st.write("✅ 데이터프레임 로딩 여부 확인:")
st.write(df.head())
st.write("📌 소득분위 목록:", 소득분위_list)
st.write("📌 항목 목록:", 항목_list)
