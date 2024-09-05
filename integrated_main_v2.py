import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from modified_heikinashi_fibonacci_functions_upbit import MRHATradingSystem, preprocess_codes, check_buy_signal
import os

import streamlit as st
from streamlit_option_menu import option_menu
import base64




def reset_session():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def load_tickers(file_path, column_index):
    df = pd.read_csv(file_path)
    return df.iloc[:, column_index].tolist()


def run_fibonacci_analysis(file_path, market_type):
    end_date = datetime.now()
    codes = preprocess_codes(file_path, market_type)
    
    st.write(f"총 {market_type} 개수: {len(codes)}")
    
    buy_signal_codes = []
    progress_bar = st.progress(0)
    
    for i, code in enumerate(codes):
        if check_buy_signal(code, end_date):
            buy_signal_codes.append(code)
        progress_bar.progress((i + 1) / len(codes))
    
    st.write(f"\n현재 매수 신호가 있는 {market_type} 개수: {len(buy_signal_codes)}")
    
    if buy_signal_codes:
        for code in buy_signal_codes:
            st.write(f"매수 신호 {market_type}: {code}")
            
        for code in buy_signal_codes:
            st.write(f"\n{code}에 대한 상세 분석:")
            analyze_single_code_krx(code, end_date)
    else:
        st.write(f"현재 매수 신호가 있는 {market_type}가 없습니다.")


def analyze_single_code_krx(code, end_date):
    try:
        trading_system = MRHATradingSystem(code, end_date - timedelta(days=365), end_date,source ='yfinance')
        trading_system.run_analysis()
        
        results = trading_system.get_results()
        
        if "error" in results:
            st.error(results["error"])
            return
        st.write(f"총 수익률: {results['Total Return']:.2%}")
        st.write(f"연간 수익률: {results['Annualized Return']:.2%}")
        st.write(f"샤프 비율: {results['Sharpe Ratio']:.2f}")
        st.write(f"최대 낙폭: {results['Max Drawdown']:.2%}")
        st.write(f"총 거래 횟수: {results['Total Trades']}")
        
        fig = trading_system.plot_results()
        st.plotly_chart(fig)
    except ValueError as e:
        st.error(f"오류: {str(e)}")
    except Exception as e:
        st.error(f"예기치 못한 오류: 종목코드를 확인해서 다시 입력해 주세요: {str(e)}")

def analyze_single_code_upbit(code, end_date):
    try:
        trading_system = MRHATradingSystem(code, end_date - timedelta(days=365), end_date,source="upbit")
        trading_system.run_analysis()
        
        results = trading_system.get_results()
        
        if "error" in results:
            st.error(results["error"])
            return
        st.write(f"총 수익률: {results['Total Return']:.2%}")
        st.write(f"연간 수익률: {results['Annualized Return']:.2%}")
        st.write(f"샤프 비율: {results['Sharpe Ratio']:.2f}")
        st.write(f"최대 낙폭: {results['Max Drawdown']:.2%}")
        st.write(f"총 거래 횟수: {results['Total Trades']}")
        
        fig = trading_system.plot_results()
        st.plotly_chart(fig)
    except ValueError as e:
        st.error(f"오류: {str(e)}")
    except Exception as e:
        st.error(f"예기치 못한 오류: 종목코드를 확인해서 다시 입력해 주세요: {str(e)}")


# def load_tickers(file_path, column_index):
#     df = pd.read_csv(file_path)
#     return df.iloc[:, column_index].tolist()


def load_tickers(file_path, columns):
    encodings = ['utf-8', 'cp949', 'euc-kr']
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if isinstance(columns, int):
                columns = [columns]
            if len(columns) == 1:
                return df.iloc[:, columns[0]].tolist()
            else:
                tickers = df.iloc[:, columns[0]].tolist()
                names = df.iloc[:, columns[1]].tolist()
                return [f"{ticker} - {name}" for ticker, name in zip(tickers, names)]
        except UnicodeDecodeError:
            continue
    
    raise ValueError(f"Unable to read the file {file_path} with any of the attempted encodings.")


def fibonacci_analysis():
    st.header("Modified Heikin Ashi Fibonacci Signal")
    
    analysis_type = st.radio("분석 유형을 선택하세요:", ("ETF/KOSPI/UPBIT 리스트", "사용자 지정 코드"))
    
    if analysis_type == "ETF/KOSPI/UPBIT 리스트":
        market_type = st.radio("분석할 시장을 선택하세요:", ("ETF", "KOSPI", "UPBIT"))
        
        if market_type == "ETF":
            file_path = "korea_etfs.csv"
        elif market_type == "KOSPI":
            file_path = "kospi200_equity.csv"
        else:
            file_path = "upbit_krw_coins.csv"
        
        if st.button(f"{market_type} 분석 시작"):
            run_fibonacci_analysis(file_path, market_type)
           
    else:  # 사용자 지정 코드
        input_type = st.radio("분석할 거래소를 선택하세요:", ("KRX", "UPBIT"))
        
        if input_type == "KRX":
            try:
                etf_tickers = load_tickers("korea_etfs.csv", [0, 1])  # 첫 번째와 두 번째 열
                kospi_tickers = load_tickers("kospi200_equity.csv", [1, 2])  # 두 번째와 세 번째 열
            except ValueError as e:
                st.error(f"파일 로딩 중 오류 발생: {str(e)}")
                return
            
            with st.sidebar:
                st.subheader("종목 선택")
                etf_selected = st.selectbox("ETF 선택", etf_tickers, key="etf_select")
                kospi_selected = st.selectbox("KOSPI 선택", kospi_tickers, key="kospi_select")
            
            if etf_selected:
                selected_ticker = etf_selected.split('-')[0]
            else:
                selected_ticker = kospi_selected.split('-')[0]

           selected_ticker = etf_selected.split(' - ')[0] if etf_selected else kospi_selected.split(' - ')[0]
            user_code = st.text_input("분석할 종목 코드를 입력하세요 (예: 005930.KS):", value=selected_ticker)

            if st.button("사용자 지정 코드 분석 시작"):
                if user_code:
                    st.write(f"{user_code}에 대한 상세 분석:")
                    user_code = user_code + ".KS" if not user_code.endswith(".KS") else user_code
                    analyze_single_code_krx(user_code, datetime.now())
                else:
                    st.error("종목 코드를 입력해주세요.")
        else:
            try:
                upbit_tickers = load_tickers("upbit_krw_coins.csv", [0])  # 첫 번째 열만 사용
            except ValueError as e:
                st.error(f"파일 로딩 중 오류 발생: {str(e)}")
                return
            
            with st.sidebar:
                st.subheader("코인 선택")
                upbit_selected = st.selectbox("Crypto Currency 선택", upbit_tickers, key="upbit_select")
            
            user_code = st.text_input("분석할 코인 코드를 입력하세요 (예: KRW-BTC):", value=upbit_selected)

            if st.button("사용자 지정 코드 분석 시작"):
                if user_code:
                    st.write(f"{user_code}에 대한 상세 분석:")
                    analyze_single_code_upbit(user_code, datetime.now())
                else:
                    st.error("종목 코드를 입력해주세요.")


def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"png"};base64,{encoded_string});
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

def main():
    st.set_page_config(page_title="RhythmSphere Cycle Analysis", layout="centered")

    # 배경 이미지 추가 (이미지 파일이 있다고 가정)
    add_bg_from_local('background.png')  

    # 커스텀 CSS
    st.markdown("""
    <style>
    .big-font {
        font-size: 50px !important;
        font-weight: bold;
        color: #1E90FF;
        text-align: center;
        text-shadow: 2px 2px 4px #000000;
    }
    .subtitle {
        font-size: 25px;
        color: #4682B4;
        text-align: center;
        margin-bottom: 50px;
    }
    .stButton>button {
        width: 100%;
        height: 60px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">RhythmSphere Cycle Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Modified Heikin Ashi Fibonacci Cycle 분석을 위한 통합 플랫폼</p>', unsafe_allow_html=True)

    # 사이드바에 메뉴 추가
    with st.sidebar:
        choice = option_menu("메인 메뉴", ["HOME", "Fibonacci Cycle 분석"],
                             icons=['house', 'graph-up'],
                             menu_icon="cast", default_index=0)


    if choice == "HOME":
        st.write("## 환영합니다!")
        st.write("이 애플리케이션은 Fibonacci cycle 을 이용하여 ETF/주식/크립토커런시 분석을 제공합니다.")
        st.write("왼쪽 사이드바에서 원하는 분석을 선택해주세요.")
    

        col1, col2 = st.columns(2)
        with col1:
            st.info("### Heikin Ashi 분석\n\n Fibonacci 수열을 활용하여 매수종목 추천")
        with col2:
            st.info("### Fibonacci Cycle 분석\n\nFibonacci 수열을 활용한 종목별 Chart 분석.")

        st.markdown('<div class="footer"> © 2024 RhythmSphere Inc. All rights reserved.</div>', unsafe_allow_html=True)


    elif choice == "Fibonacci Cycle 분석":
        fibonacci_analysis()
  
if __name__ == "__main__":
    main()
