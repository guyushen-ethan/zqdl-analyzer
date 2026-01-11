import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import akshare as ak
import os

os.environ['AKSHARE_CACHE_PATH'] = 'NUL'  # Windows

# === Streamlit 页面设置 ===
st.set_page_config(
    page_title="紫气东来基金收益分析",
    page_icon="📈",
    layout="wide"
)

# === 中文字体支持（兼容在线环境）===
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

st.title("📊 紫气东来基金累计收益 vs 上证指数")
st.markdown("请上传包含「紫气东来」日净值的 Excel 文件（需含「日期」和「累计净值」列）")

# === 文件上传组件 ===
uploaded_file = st.file_uploader(
    "选择 Excel 文件（如 F紫气东来日净值.xls）",
    type=["xls", "xlsx"],
    help="支持 .xls 或 .xlsx 格式"
)

if uploaded_file is not None:
    try:
        # === 1. 读取基金数据 ===
        df_fund = pd.read_excel(uploaded_file, sheet_name=0)
        df_fund.columns = df_fund.columns.str.strip()

        # 自动匹配列名（更鲁棒）
        date_col = next((col for col in df_fund.columns if '日期' in col), None)
        nav_col = next((col for col in df_fund.columns if '紫气东来' in col and '累计净值' in col), None)

        if not date_col or not nav_col:
            st.error(f"❌ 未能识别日期或净值列。可用列：{list(df_fund.columns)}")
            st.stop()

        df_fund[date_col] = pd.to_datetime(df_fund[date_col], errors='coerce')
        df_fund = df_fund.dropna(subset=[date_col, nav_col])
        df_fund = df_fund.sort_values(by=date_col).reset_index(drop=True)
        df_fund.rename(columns={date_col: 'date', nav_col: 'fund_nav'}, inplace=True)

        # === 2. 获取上证指数数据 ===
        start_date = df_fund['date'].min().strftime('%Y%m%d')
        end_date = df_fund['date'].max().strftime('%Y%m%d')

        with st.spinner(f"🌐 正在获取上证指数数据（{start_date} 至 {end_date}）..."):
            try:
                index_data = ak.index_zh_a_hist(
                    symbol="000001",
                    period="daily",
                    start_date=start_date,
                    end_date=end_date
                )
                index_data.rename(columns={'日期': 'date', '收盘': 'sh_close'}, inplace=True)
                index_data['date'] = pd.to_datetime(index_data['date'])
                index_df = index_data[['date', 'sh_close']].copy()
            except Exception as e:
                st.error(f"❌ 获取上证指数失败：{e}\n请检查网络或稍后重试。")
                st.stop()

        # === 3. 合并数据 & 归一化 ===
        merged = pd.merge(df_fund[['date', 'fund_nav']], index_df, on='date', how='inner')
        if merged.empty:
            st.error("❌ 基金与上证指数无重叠日期，请检查数据时间范围。")
            st.stop()

        merged['fund_norm'] = merged['fund_nav'] / merged['fund_nav'].iloc[0]
        merged['sh_norm'] = merged['sh_close'] / merged['sh_close'].iloc[0]

        # === 4. 绘图 ===
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(merged['date'], merged['fund_norm'], label='紫气东来', color='red', linewidth=1.5)
        ax.plot(merged['date'], merged['sh_norm'], label='上证指数', color='blue', linewidth=1.5)

        # 填充收益区域
        ax.fill_between(
            merged['date'], merged['fund_norm'], 1.0,
            where=(merged['fund_norm'] >= 1.0),
            interpolate=True,
            color='red', alpha=0.2
        )

        # 添加水印（适配 Streamlit）
        watermark_text = "紫气东来"
        rows, cols = 6, 6
        font_size = 30
        alpha = 0.3
        rotation = -30
        color = 'lightgray'

        for i in range(rows):
            for j in range(cols):
                x = (j + 0.5) / cols
                y = (i + 0.5) / rows
                ax.text(
                    x, y, watermark_text,
                    transform=ax.transAxes,
                    fontsize=font_size,
                    color=color,
                    alpha=alpha,
                    ha='center',
                    va='center',
                    rotation=rotation,
                    zorder=0
                )

        ax.set_title('紫气东来基金累计收益', color='red', fontsize=16)
        ax.set_ylabel('归一化净值（起始=1.0）')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        # 显示图表
        st.pyplot(fig)

        # 显示最终收益
        fund_ret = (merged['fund_norm'].iloc[-1] - 1) * 100
        sh_ret = (merged['sh_norm'].iloc[-1] - 1) * 100
        st.success(f"📈 最终收益：紫气东来 **{fund_ret:.2f}%** | 上证指数 **{sh_ret:.2f}%**")

    except Exception as e:
        st.error(f"❌ 处理失败：{str(e)}")
        st.info("常见原因：文件格式错误、列名不匹配、网络问题等。")

else:

    st.info("👆 请上传 Excel 文件以开始分析。")
