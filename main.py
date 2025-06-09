import pandas as pd
import plotly.express as px
import streamlit as st
import re                             # 🆕 정규식 패턴 검사용
from datetime import datetime

# ----------------------
# 1. 데이터 로딩 및 전처리
# ----------------------
@st.cache_data
def load_data():
    filename = "소득5분위별_가구당_가계수지__전국_1인이상_실질__20250605122557.csv"

    try:
        df = pd.read_csv(filename, encoding='utf-8-sig')
        st.success("✅ UTF-8-SIG로 읽기 성공")
    except Exception:
        try:
            df = pd.read_csv(filename, encoding='cp949')
            st.success("✅ CP949로 읽기 성공")
        except Exception:
            st.error("❌ CSV 파일을 불러오지 못했습니다.")
            return pd.DataFrame()

    # ---- 전처리 -----------------------------------------------------------
    if df.shape[0] > 0:
        if str(df.iloc[0, 0]).strip() == "소득분위":
            df = df.drop(index=0)

        df = df.rename(columns={df.columns[0]: "소득분위", df.columns[1]: "항목"})
        df["소득분위"] = df["소득분위"].astype(str).str.strip()
        df = df[df["소득분위"].str.contains("분위")]
        df = df.dropna(axis=1, how='all')

        # (1) 날짜 컬럼 이름 정제 ------------------------------------------
        time_cols = df.columns[2:]
        new_cols = []
        for col in time_cols:
            # '2003/1' → '2003Q1' 형태로 변환
            try:
                year, quarter = col.split("/")
                new_cols.append(f"{year}Q{quarter}")
            except ValueError:
                new_cols.append(col)
        df.columns = list(df.columns[:2]) + new_cols

        # (2) **날짜(분기) 패턴 컬럼만 유지**      # 🔧 핵심 수정
        quarter_pattern = re.compile(r"^\d{4}Q[1-4]$")   # 1999Q4 같은 형식
        valid_time_cols = [c for c in df.columns[2:] if quarter_pattern.match(c)]
        df = df[["소득분위", "항목"] + valid_time_cols]  # 잘못된 컬럼 제외

    return df

# ----------------------
# 2. Streamlit 레이아웃
# ----------------------
st.set_page_config(page_title="소득 분위별 소비 분석", layout="wide")
st.title("💸 소득 5분위별 소비 패턴 변화 분석")

st.markdown("""
**분석 목표**  
물가 상승률(CPI)과 함께, 소득 5분위별 **실질 소비 항목** 변화를 비교하고 인플레이션의 영향을 분석합니다.
""")

# ----------------------
# 3. 데이터 불러오기 및 선택 위젯
# ----------------------
df = load_data()

if not df.empty:
    소득분위_list = df['소득분위'].unique().tolist()
    항목_list = df['항목'].unique().tolist()

    col1, col2 = st.columns(2)
    with col1:
        selected_소득분위 = st.selectbox("소득 분위 선택", 소득분위_list)
    with col2:
        기본값_후보 = ['소비지출', '식료품·비주류음료', '교통']
        유효한_기본값 = [항목 for 항목 in 기본값_후보 if 항목 in 항목_list]
        selected_항목 = st.multiselect("소비 항목 선택", 항목_list, default=유효한_기본값)

    # ----------------------
    # 4. 시각화용 데이터 가공
    # ----------------------
    filtered_df = df[
        (df['소득분위'] == selected_소득분위) &
        (df['항목'].isin(selected_항목))
    ]

    # **melt 시 value_vars로 valid_time_cols만 사용**  # 🔧 핵심 수정
    value_vars = [c for c in filtered_df.columns if re.match(r"^\d{4}Q[1-4]$", c)]
    df_melted = filtered_df.melt(
        id_vars=['소득분위', '항목'],
        value_vars=value_vars,
        var_name='시점',
        value_name='지출'
    )

    # 안전한 날짜 변환   # 🔧 수정
    df_melted['시점'] = pd.PeriodIndex(df_melted['시점'], freq='Q').to_timestamp()
    df_melted['지출'] = pd.to_numeric(df_melted['지출'], errors='coerce')

    # ----------------------
    # 5. Plotly 라인 차트
    # ----------------------
    fig = px.line(
        df_melted,
        x='시점',
        y='지출',
        color='항목',
        markers=True,
        title=f"{selected_소득분위} 소비 항목별 변화 추이",
        labels={'지출': '지출 금액(원)', '시점': '분기'}
    )
    fig.update_layout(legend_title="소비 항목", height=500)
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------
    # 6. 요약 인사이트
    # ----------------------
    st.subheader("🔍 분석 인사이트")
    st.markdown("""
    - **소득이 낮을수록** 필수 지출 항목(식료품, 주거비)의 비중이 높게 유지됩니다.  
    - **상위 소득 분위**에선 문화·교육·보건 소비의 증감이 상대적으로 큽니다.  
    - 분기별 CPI와 병합하면 **인플레이션 영향**을 정밀 분석할 수 있습니다.  
    """)
else:
    st.warning("⚠️ 데이터프레임이 비어 있습니다. CSV 파일의 형식과 내용을 다시 확인해주세요.")
