import streamlit as st
import pandas as pd
import gspread, os, json
from google.oauth2.service_account import Credentials
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards

# ------------------------
# SETUP PAGE (harus paling atas)
# ------------------------
st.set_page_config(page_title="Dashboard BKPSDM", layout="wide")

# --- Session state untuk navigasi ---
if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"  # default halaman

# --- Auth ke Google Sheet Lokal ---
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]
creds = None
try:
    # --- Cloud (pakai Streamlit Secrets) ---
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
except Exception:
    # --- Lokal (pakai file json) ---
    creds = Credentials.from_service_account_file(
        r"C:/Users/MyBook Hype AMD/Videos/Dashboard Arus Kas/proven-mystery-471102-k6-0d7bdda0bcd4.json",
        scopes=scope
    )

client = gspread.authorize(creds)
# Gunakan st.secrets untuk menyimpan kredensial
# scope = ["https://spreadsheets.google.com/feeds",
#          "https://www.googleapis.com/auth/drive"]

# creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
# client = gspread.authorize(creds)

# ------------------------
# HALAMAN DASHBOARD
# ------------------------
if st.session_state["page"] == "dashboard":
    st.title("📊 Dashboard Aplikasi Cash Flow BKPSDM")

    # Tombol ke halaman Tenggang Waktu
    if st.button("➡️ Halaman Tenggang Waktu"):
        st.session_state["page"] = "tenggang"
        st.rerun()

    # --- Load Data dari sheet Data ---
    sheet = client.open("KASVA 1.0 - Aplikasi Cash Flow BKPSDM").worksheet("Data")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # --- Bersihin Data ---
    for col in ["UMK", "SPJ"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("Rp", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
            .replace("", "0")
            .astype(float)
        )

    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=True)
    df = df.dropna(how="all")

    # --- Filter ---
    st.subheader("🔍 Filter Data")
    df["Tahun"] = df["Tanggal"].dt.year
    df["Kategori"] = df["Kategori"].replace("", pd.NA)
    df["Kasir"] = df["Kasir"].replace("", pd.NA)

    c1, c2 = st.columns(2)
    with c1:
        tahun_list = sorted(df.loc[df["Tahun"].notna(), "Tahun"].astype(int).unique().tolist())
        tahun = st.selectbox("📅 Tahun", options=["Semua"] + tahun_list)
    with c2:
        kategori_list = sorted(df["Kategori"].dropna().unique().tolist())
        kategori = st.selectbox("📂 Kategori", options=["Semua"] + kategori_list)

    df_filtered = df.copy()
    if tahun != "Semua":
        df_filtered = df_filtered[df_filtered["Tahun"] == tahun]
    if kategori != "Semua":
        df_filtered = df_filtered[df_filtered["Kategori"] == kategori]

    kasir_list = sorted(df_filtered["Kasir"].dropna().unique().tolist())
    kasir = st.selectbox("👤 Kasir", options=["Semua"] + kasir_list)
    if kasir != "Semua":
        df_filtered = df_filtered[df_filtered["Kasir"] == kasir]

    df = df_filtered.copy()

    # Filter rentang tanggal
    if df["Tanggal"].notna().any():
        min_tgl = df["Tanggal"].min().date()
        max_tgl = df["Tanggal"].max().date()
    else:
        today = datetime.today().date()
        min_tgl, max_tgl = today, today

    tgl_range = st.date_input(
        "⏳ Rentang Tanggal:",
        value=[min_tgl, max_tgl],
        format="DD-MM-YYYY"
    )
    if isinstance(tgl_range, (list, tuple)) and len(tgl_range) == 2:
        tgl_awal, tgl_akhir = tgl_range
    else:
        tgl_awal, tgl_akhir = min_tgl, max_tgl

    tgl_awal = pd.to_datetime(tgl_awal)
    tgl_akhir = pd.to_datetime(tgl_akhir)
    df = df[(df["Tanggal"] >= tgl_awal) & (df["Tanggal"] <= tgl_akhir)]

    # --- Hitung Sisa Saldo ---
    df = df.sort_values("Tanggal").reset_index(drop=True)
    sisa = []
    saldo = 0
    for _, row in df.iterrows():
        saldo = saldo - row["SPJ"] + row["UMK"]
        sisa.append(saldo)
    df["Sisa Saldo"] = sisa

  # fungsi helper rupiah
    def format_rupiah(x):
        return f"Rp{int(x):,}".replace(",", ".")

    # --- Statistik ---
    st.subheader("📊 Statistik")
    total_umk = df["UMK"].sum()
    total_spj = df["SPJ"].sum()
    sisa_akhir = total_umk - total_spj
    realisasi = (total_spj / total_umk * 100) if total_umk > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total UMK", format_rupiah(total_umk))
    c2.metric("📑 Total SPJ", format_rupiah(total_spj))
    c3.metric("📊 Realisasi SPJ", f"{realisasi:.1f}%")
    c4.metric("🏦 Sisa Saldo", format_rupiah(sisa_akhir))


    # Apply styling
    style_metric_cards(
        background_color="#FFFFFF",
        border_left_color="#4F46E5",
        border_size_px=4,
        border_radius_px=12,
        box_shadow=True,
    )

    # Inject CSS biar font jadi hitam
    st.markdown(
        """
        <style>
        [data-testid="stMetricValue"] {
            color: black !important;
        }
        [data-testid="stMetricLabel"] {
            color: black !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- Data Table ---
    st.subheader("📋 Data Detail")
    if not df.empty:
        df_tampil = df.copy()
        df_tampil["Tanggal"] = df_tampil["Tanggal"].dt.strftime("%d-%m-%Y")

        cols = ["Tanggal", "Kategori", "Kasir", "Uraian", "UMK", "SPJ"]
        if kategori != "Semua" or kasir != "Semua":
            cols.append("Sisa Saldo")
        df_tampil = df_tampil[cols]

        for col in ["UMK", "SPJ", "Sisa Saldo"]:
            if col in df_tampil.columns:
                df_tampil[col] = df_tampil[col].apply(
                    lambda x: f"Rp{int(x):,}".replace(",", ".")
                )

        st.dataframe(df_tampil, use_container_width=True)
    else:
        st.warning("⚠️ Tidak ada data sesuai filter.")

    # --- Grafik ---
    if not df.empty:
        st.subheader("📊 Grafik UMK, SPJ, & Sisa Saldo per Kategori")
        grafik = df.groupby("Kategori")[["UMK", "SPJ"]].sum()
        grafik["Sisa Saldo"] = grafik["UMK"] - grafik["SPJ"]
        st.bar_chart(grafik)

# ------------------------
# HALAMAN TENGGANG WAKTU
# ------------------------
elif st.session_state["page"] == "tenggang":
    st.title("📅 Halaman Tenggang Waktu")

    # Tombol kembali ke Dashboard
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()

    # Loader HTML (full screen overlay)
    loader_html = """
    <div id="loader-overlay" style="
        position: fixed; 
        top: 0; left: 0; 
        width: 100%; height: 100%; 
        background: rgba(255, 255, 255, 0.9); 
        display: flex; 
        justify-content: center; 
        align-items: center;
        z-index: 9999;">
        <div class="dot-pulse"></div>
    </div>

    <style>
    .dot-pulse {
      position: relative;
      left: -9999px;
      width: 12px;
      height: 12px;
      border-radius: 6px;
      background-color: #3498db;
      color: #3498db;
      box-shadow: 9999px 0 0 -5px;
      animation: dotPulse 1.5s infinite linear;
      animation-delay: .25s;
    }
    .dot-pulse::before, .dot-pulse::after {
      content: '';
      display: inline-block;
      position: absolute;
      top: 0;
      width: 12px;
      height: 12px;
      border-radius: 6px;
      background-color: #3498db;
      color: #3498db;
    }
    .dot-pulse::before {
      box-shadow: 9984px 0 0 -5px;
      animation: dotPulseBefore 1.5s infinite linear;
      animation-delay: 0s;
    }
    .dot-pulse::after {
      box-shadow: 10014px 0 0 -5px;
      animation: dotPulseAfter 1.5s infinite linear;
      animation-delay: .5s;
    }
    @keyframes dotPulseBefore {
      0% { box-shadow: 9984px 0 0 -5px; }
      30% { box-shadow: 9984px 0 0 2px; }
      60%,100% { box-shadow: 9984px 0 0 -5px; }
    }
    @keyframes dotPulse {
      0% { box-shadow: 9999px 0 0 -5px; }
      30% { box-shadow: 9999px 0 0 2px; }
      60%,100% { box-shadow: 9999px 0 0 -5px; }
    }
    @keyframes dotPulseAfter {
      0% { box-shadow: 10014px 0 0 -5px; }
      30% { box-shadow: 10014px 0 0 2px; }
      60%,100% { box-shadow: 10014px 0 0 -5px; }
    }
    </style>
    """

    loader = st.empty()
    loader.markdown(loader_html, unsafe_allow_html=True)

    # --- Load Data dari sheet Tenggang Waktu ---
    sheet_tw = client.open("KASVA 1.0 - Aplikasi Cash Flow BKPSDM").worksheet("Tenggang Waktu")
    data_tw = sheet_tw.get_all_records()
    df_tw = pd.DataFrame(data_tw)

    # Hapus loader setelah data siap
    loader.empty()

    if not df_tw.empty:
        # Hilangkan kolom SPJ dan Keterangan kalau ada
        for col in ["SPJ", "Keterangan"]:
            if col in df_tw.columns:
                df_tw = df_tw.drop(columns=[col])

        st.subheader("📋 Data Tenggang Waktu")

        # Fungsi pewarnaan Sisa Hari
        def warna_cell(sisa):
            try:
                sisa = int(sisa)
            except:
                return "#9d8c8c"  # default putih
            if sisa <= 5:
                return "#e74c3c"  # merah
            elif 5 < sisa <= 10:
                return "#f1c40f"  # kuning
            elif 10 < sisa <= 21:
                return "#2ecc71"  # hijau
            else:
                return "#ffffff"

        # Bangun tabel HTML manual
        html = "<table style='width:100%; border-collapse: collapse;'>"

        # Header
        html += "<tr style='background-color:#262730; color:white;'>"
        for col in df_tw.columns:
            html += f"<th style='padding:8px; border:1px solid #ddd; text-align:center;'>{col}</th>"
        html += "</tr>"

        # Rows
        for i, row in df_tw.iterrows():
            html += "<tr>"
            for col in df_tw.columns:
                val = row[col]

                # Kolom Link → tombol
                if col == "Link" and pd.notna(val) and str(val).startswith("http"):
                    val = f"""
                        <a href="{val}" target="_blank">
                            <button style="background-color:#43C354; color:white;
                                           padding:4px 10px; border:none;
                                           border-radius:5px; cursor:pointer;">
                                <img width="24" height="24" src="https://img.icons8.com/color/48/whatsapp--v1.png" alt="whatsapp--v1"/>
                            </button>
                        </a>
                    """
                # Kolom Sisa Hari → warnain background
                elif col == "Sisa Hari":
                    color = warna_cell(val)
                    val = f"<div style='background-color:{color}; padding:6px; text-align:center;'>{val}</div>"
                # Kolom No → tengah
                elif col == "No":
                    val = f"<div style='text-align:center;'>{val}</div>"

                html += f"<td style='padding:8px; border:1px solid #ddd; text-align:center;'>{val}</td>"
            html += "</tr>"

        html += "</table>"

        st.markdown(html, unsafe_allow_html=True)

    else:
        st.info("⚠️ Tidak ada data tenggang waktu.")


