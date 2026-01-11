import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import akshare as ak

# 禁用 akshare 缓存写入（防止云环境权限错误）
ak.set_options(cache_path=None)

st.set_page_config(page_title="紫气东来收益分析", layout="wide")
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

st.title("📈 紫气东来基金 vs 上证指数")
uploaded_file = st.file_uploader("上传 Excel 文件", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        date_col = next((c for c in df.columns if '日期' in c), None)
        nav_col = next((c for c in df.columns if '累计净值' in c and '紫气东来' in c), None)
        
        if not date_col or not nav_col:
            st.error("未找到日期或净值列")
            st.stop()

        df[date_col] = pd.to_datetime(df[date_col])
        df = df.dropna(subset=[date_col, nav_col]).sort_values(date_col)
        df.rename(columns={date_col: 'date', nav_col: 'nav'}, inplace=True)

        start = df['date'].min().strftime('%Y%m%d')
        end = df['date'].max().strftime('%Y%m%d')
        idx = ak.index_zh_a_hist(symbol="000001", period="daily", start_date=start, end_date=end)
        idx.rename(columns={'日期': 'date', '收盘': 'close'}, inplace=True)
        idx['date'] = pd.to_datetime(idx['date'])

        merged = pd.merge(df[['date', 'nav']], idx[['date', 'close']], on='date')
        merged['fund_norm'] = merged['nav'] / merged['nav'].iloc[0]
        merged['idx_norm'] = merged['close'] / merged['close'].iloc[0]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(merged['date'], merged['fund_norm'], label='紫气东来', color='red')
        ax.plot(merged['date'], merged['idx_norm'], label='上证指数', color='blue')
        ax.set_title('累计收益对比', fontsize=16, color='red')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=30)
        st.pyplot(fig)

        fund_ret = (merged['fund_norm'].iloc[-1] - 1) * 100
        idx_ret = (merged['idx_norm'].iloc[-1] - 1) * 100
        st.success(f"最终收益：紫气东来 {fund_ret:.2f}% | 上证指数 {idx_ret:.2f}%")

    except Exception as e:
        st.error(f"处理失败：{str(e)}")
