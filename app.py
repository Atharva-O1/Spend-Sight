import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="City Budget Visualizer", page_icon="📊", layout="wide")

@st.cache_data
def load_data(filename):
    df = pd.read_csv(filename)
    return df

st.sidebar.header("Data Source")

# --- DATASET DROPDOWN ---
available_datasets = {
    "Nagpur Budget 2024-25": "nagpur_budget.csv",
    "Nagpur Budget 2023-24": "nagpur_budget_23_24.csv",
    "Nagpur Budget 2022-23": "nagpur_budget_22_23.csv"
}

selected_dataset_name = st.sidebar.selectbox(
    "Select Budget Year:", 
    options=list(available_datasets.keys())
)

selected_filename = available_datasets[selected_dataset_name]

try:
    df = load_data(selected_filename)
except FileNotFoundError:
    st.sidebar.error(f"⚠️ {selected_filename} not found.")
    st.error(f"Please ensure you have created the '{selected_filename}' file in your project folder.")
    st.stop()

st.sidebar.divider()

st.sidebar.header("Dashboard Controls")
st.sidebar.write("Use these filters to drill down into specific civic sectors.")

# --- SECTOR FILTER ---
all_sectors = df['Sector'].unique().tolist()
selected_sectors = st.sidebar.multiselect(
    "Select Sectors:", 
    options=all_sectors, 
    default=all_sectors 
)

# --- STATUS FILTER ---
all_statuses = df['Status'].unique().tolist()
selected_statuses = st.sidebar.multiselect(
    "Select Project Status:",
    options=all_statuses,
    default=all_statuses
)

filtered_df = df[
    (df['Sector'].isin(selected_sectors)) & 
    (df['Status'].isin(selected_statuses))
]

if filtered_df.empty:
    st.warning("Please select at least one Sector and Status from the sidebar.")
    st.stop()

# --- NEW: DOWNLOAD BUTTON ---
st.sidebar.divider()
st.sidebar.header("Export")
st.sidebar.write("Download the currently filtered dataset for offline analysis.")

csv_data = filtered_df.to_csv(index=False).encode('utf-8')

st.sidebar.download_button(
    label="📥 Download Filtered CSV",
    data=csv_data,
    file_name=f"nagpur_budget_export_{selected_dataset_name[:4]}.csv",
    mime="text/csv",
    use_container_width=True
)

# --- MAIN DASHBOARD UI ---
st.title(f"📊 Transparent City: {selected_dataset_name}")
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
    
    chart_df = filtered_df.copy()
    chart_df['Clean_Name'] = chart_df['Project_Name'].str.replace(r'^B\s+', '', regex=True).str.title()
    chart_df['Short_Name'] = chart_df['Clean_Name'].apply(lambda x: x if len(x) <= 35 else x[:32] + '...')

    fig_bar = px.bar(
        chart_df, 
        x='Allocated_Amount_Cr', 
        y='Short_Name', 
        color='Sector', 
        orientation='h',
        log_x=True, 
        color_discrete_sequence=px.colors.qualitative.Pastel, 
        labels={'Allocated_Amount_Cr': 'Amount (₹ Cr, Log Scale)', 'Short_Name': ''},
        hover_data={'Clean_Name': True, 'Status': True, 'Short_Name': False, 'Sector': False} 
    )
    
    fig_bar.update_layout(
        yaxis={'categoryorder':'total ascending'},
        showlegend=False, 
        margin=dict(l=0, r=20, t=10, b=0), 
        height=500 
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()
with st.expander("🔍 View Raw Financial Data"):
    st.dataframe(filtered_df, use_container_width=True)