import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="City Budget Visualizer", page_icon="📊", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("nagpur_budget.csv")
    return df

df = load_data()

st.sidebar.header("Dashboard Controls")
st.sidebar.write("Use these filters to drill down into specific civic sectors.")

all_sectors = df['Sector'].unique().tolist()
selected_sectors = st.sidebar.multiselect(
    "Select Sectors:", 
    options=all_sectors, 
    default=all_sectors 
)

filtered_df = df[df['Sector'].isin(selected_sectors)]

st.title("📊 Transparent City: Local Budget Visualizer")
st.markdown("Translating complex municipal financial data into clear, interactive insights.")

total_budget = filtered_df['Allocated_Amount_Cr'].sum()
st.metric(label="Total Allocated Budget (Selected)", value=f"₹ {total_budget:,.2f} Cr")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Macro View: Allocation by Sector")
    sector_group = filtered_df.groupby('Sector')['Allocated_Amount_Cr'].sum().reset_index()
    
    fig_pie = px.pie(
        sector_group, 
        values='Allocated_Amount_Cr', 
        names='Sector', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("Micro View: Project Breakdown")
    fig_bar = px.bar(
        filtered_df, 
        x='Allocated_Amount_Cr', 
        y='Project_Name', 
        color='Sector', 
        orientation='h',
        labels={'Allocated_Amount_Cr': 'Amount (₹ Crores)', 'Project_Name': ''}
    )
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()
with st.expander("🔍 View Raw Financial Data"):
    st.dataframe(filtered_df, use_container_width=True)