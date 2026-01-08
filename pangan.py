import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
from difflib import get_close_matches
import plotly.express as px

# ======================================================
# 1️⃣ KONFIGURASI HALAMAN
# ======================================================
st.set_page_config(
    page_title="Dashboard Ketahanan Pangan Sumatera",
    layout="wide",
    page_icon="🌾"
)

# ======================================================
# 🎨 GLOBAL CSS (FSVA-LIKE)
# ======================================================
st.markdown("""
<style>

/* ===== BACKGROUND UTAMA ===== */
.stApp {
    background: linear-gradient(180deg, #edf5ee 0%, #f8fbf9 40%, #ffffff 100%);
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background-color: #f1faee;
}

/* ===== CONTAINER ===== */
.block-container {
    padding: 2rem 3rem 3rem 3rem;
}

/* ===== JUDUL ===== */
.main-title {
    text-align:center;
    font-size:40px;
    font-weight:800;
    color:#1b4332;
}

.sub-header {
    text-align:center;
    font-size:18px;
    color:#40916c;
    margin-bottom:30px;
}

/* ===== METRIC CARD ===== */
div[data-testid="metric-container"] {
    background-color: #ffffff;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    border: 1px solid #e5e7eb;
}

/* ===== RADIO MENU ===== */
div[role="radiogroup"] > label {
    background-color: #ffffff;
    padding: 10px 18px;
    border-radius: 14px;
    margin-right: 10px;
    border: 1px solid #d1d5db;
    font-weight: 600;
}

div[role="radiogroup"] > label:hover {
    background-color: #e9f5ee;
    border-color: #40916c;
}

div[role="radiogroup"] input:checked + div {
    background-color: #40916c !important;
    color: white !important;
    border-radius: 14px;
}

/* ===== DATAFRAME ===== */
div[data-testid="stDataFrame"] {
    background-color: #ffffff;
    border-radius: 14px;
    padding: 8px;
}

/* ===== SUBHEADER ===== */
h2, h3 {
    color: #1b4332;
}

</style>
""", unsafe_allow_html=True)

# ======================================================
# 🏷️ JUDUL
# ======================================================
st.markdown("<div class='main-title'>📊 Dashboard Ketahanan Pangan Pulau Sumatera</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-header'>Analisis klasterisasi kabupaten/kota berbasis Self-Organizing Map (SOM)</div>",
    unsafe_allow_html=True
)

# ======================================================
# 🔘 MENU NAVIGASI (FSVA STYLE)
# ======================================================
menu = st.radio(
    "",
    ["📘 Keterangan Indikator", "📊 Tabel Data", "📄 Laporan FSVA/IKP", "❓ Panduan/Tutorial"],
    horizontal=True
)

st.markdown("---")

# ======================================================
# 2️⃣ LOAD & PREPROCESS DATA
# ======================================================
@st.cache_data
def load_data():
    gdf = gpd.read_file("Sumatera.shp")
    df_cluster = pd.read_excel("hasil_cluster_som.xlsx")

    def clean_name(x):
        if pd.isna(x):
            return ""
        return str(x).upper().replace("KABUPATEN", "").replace("KOTA", "").strip()

    gdf["NAME_CLEAN"] = gdf["NAME_2"].apply(clean_name)
    df_cluster["Kab_CLEAN"] = df_cluster["Kabupaten/Kota"].apply(clean_name)

    merged = gdf.merge(
        df_cluster,
        left_on="NAME_CLEAN",
        right_on="Kab_CLEAN",
        how="left"
    )

    unmatched = merged[merged["Cluster"].isna()]
    for idx, row in unmatched.iterrows():
        match = get_close_matches(row["NAME_CLEAN"], df_cluster["Kab_CLEAN"], n=1, cutoff=0.75)
        if match:
            matched_row = df_cluster[df_cluster["Kab_CLEAN"] == match[0]].iloc[0]
            for col in df_cluster.columns:
                merged.at[idx, col] = matched_row[col]

    cluster_labels = {
        0: "Sangat Tahan",
        1: "Agak Tahan",
        2: "Agak Rentan",
        3: "Rentan",
        4: "Tahan",
        5: "Sangat Rentan"
    }

    merged["Kategori_Ketahanan_Pangan"] = merged["Cluster"].map(cluster_labels)
    return merged

sumatera = load_data()

# ======================================================
# 3️⃣ SIDEBAR FILTER
# ======================================================
st.sidebar.header("🔍 Filter & Informasi")

selected_provinsi = st.sidebar.selectbox(
    "Pilih Provinsi",
    sorted(sumatera["NAME_1"].unique())
)

filtered_data = sumatera[sumatera["NAME_1"] == selected_provinsi]

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Indikator Utama**
- IKP – Indeks Ketahanan Pangan  
- Produktivitas & Produksi Padi  
- PDRB  
- RLS, UHH, TPAK, P0, PPK
""")

# ======================================================
# 📘 MENU KONTEN
# ======================================================
if menu == "📘 Keterangan Indikator":
    st.subheader("📘 Keterangan Indikator")
    st.markdown("""
    Dashboard ini mengadopsi pendekatan **FSVA** untuk analisis ketahanan pangan.
    Klasterisasi dilakukan menggunakan **Self-Organizing Map (SOM)**.
    """)

elif menu == "📊 Tabel Data":
    st.subheader("📊 Tabel Data")
    st.dataframe(filtered_data, use_container_width=True, height=520)

elif menu == "📄 Laporan FSVA/IKP":
    st.subheader("📄 Laporan FSVA / IKP")
    st.info("📌 Laporan PDF dapat diintegrasikan pada tahap implementasi selanjutnya.")

elif menu == "❓ Panduan/Tutorial":
    st.subheader("❓ Panduan Penggunaan")
    st.markdown("""
    1. Pilih provinsi  
    2. Amati ringkasan indikator  
    3. Gunakan peta untuk eksplorasi  
    """)

# ======================================================
# 🎯 METRIK RINGKASAN
# ======================================================
st.subheader(f"📈 Ringkasan Cluster – {selected_provinsi}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("IKP Rata-rata", f"{filtered_data['IKP'].mean():.2f}")
c2.metric("Produktivitas Padi", f"{filtered_data['Produktivitas_Padi'].mean():.2f} ku/ha")
c3.metric("Produksi Padi", f"{filtered_data['Produksi_Padi'].sum():,.0f} ton")
c4.metric("PDRB", f"{filtered_data['PDRB'].sum():,.0f}")

# ======================================================
# 🗺️ PETA
# ======================================================
cluster_color = {
    0: "#1B4332",
    1: "#52B69A",
    2: "#F4A261",
    3: "#E63946",
    4: "#FFD166",
    5: "#8B0000"
}

st.subheader(f"🗺️ Peta Ketahanan & Kerentanan Pangan – {selected_provinsi}")

center = filtered_data.geometry.centroid.unary_union.centroid
m = folium.Map([center.y, center.x], zoom_start=7, tiles="CartoDB positron")

folium.GeoJson(
    filtered_data,
    style_function=lambda f: {
        "fillColor": cluster_color.get(f["properties"]["Cluster"], "#ccc"),
        "color": "black",
        "weight": 0.6,
        "fillOpacity": 0.8
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["NAME_2", "Kategori_Ketahanan_Pangan", "IKP"],
        aliases=["Wilayah", "Kategori (SOM)", "IKP"]
    )
).add_to(m)

st_folium(m, width=1100, height=620)

st.caption(
    "Klasterisasi menggunakan algoritma Self-Organizing Map (SOM). "
    "Penomoran cluster merupakan hasil pembelajaran pola data."
)
