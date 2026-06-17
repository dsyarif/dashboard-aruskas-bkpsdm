import streamlit as st
import pandas as pd
import gspread, os, json
from google.oauth2.service_account import Credentials
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards
import altair as alt

# ------------------------
# SETUP PAGE (must be first)
# ------------------------
st.set_page_config(page_title="Dashboard BKPSDM", layout="wide")

# --- Session state untuk navigasi ---
if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"

# --- Auth ke Google Sheet Lokal / Cloud ---
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]
creds = None
try:
    # --- Cloud (Streamlit Secrets) ---
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
except Exception:
    # --- Lokal (File JSON) ---
    creds = Credentials.from_service_account_file(
        r"C:/Users/MyBook Hype AMD/Videos/Dashboard Arus Kas/proven-mystery-471102-k6-0d7bdda0bcd4.json",
        scopes=scope
    )

client = gspread.authorize(creds)
# Konsistensi variabel worksheet di seluruh halaman
sheet_data = client.open("KASVA 1.0 - Aplikasi Cash Flow BKPSDM").worksheet("Data")
sheet_kasir = client.open("KASVA 1.0 - Aplikasi Cash Flow BKPSDM").worksheet("Data Kasir")
sheet_tw = client.open("KASVA 1.0 - Aplikasi Cash Flow BKPSDM").worksheet("Tenggat Waktu")

# ========================
# HEADER STYLING
# ========================
theme_base = st.get_option("theme.base")
if theme_base == "dark":
    title_color = "#E5E7EB"
    accent_color = "#818CF8"
    subtitle_color = "#9CA3AF"
else:
    title_color = "#1F2937"
    accent_color = "#4F46E5"
    subtitle_color = "#6B7280"

st.markdown(
    f"""
    <h1 style='font-size:38px; font-weight:800; color:{title_color}; margin-bottom:5px;'>
        Dashboard <span style='color:{accent_color}'>KASVA</span> (Kas Virtual)
    </h1>
    <h4 style='margin-top:-15px; margin-bottom:20px; color:{subtitle_color}; font-weight:500;'>
        BKPSDM Kota Pekalongan
    </h4>
    """,
    unsafe_allow_html=True
)

if "logged_in" in st.session_state and st.session_state["logged_in"]: 
    st.markdown(f"<div style='margin-bottom:15px; font-weight:600;'>👋 Selamat Datang, <b>{st.session_state['user'].title()}</b></div>", unsafe_allow_html=True)

# ========================
# NAVIGASI UTAMA (HORIZONTAL MENU)
# ========================
def nav_button(label, page_name, emoji=""):
    is_active = st.session_state["page"] == page_name
    # Style tombol aktif (ungu) vs tidak aktif (abu-abu)
    if is_active:
        style = "background-color:#4F46E5; color:white; font-weight:600; border:none; border-radius:8px; padding:8px 16px;"
    else:
        style = "background-color:#F3F4F6; color:#111827; border:1px solid #E5E7EB; border-radius:8px; padding:8px 16px;"
    
    clicked = st.button(f"{emoji} {label}", key=f"btn_{page_name}", use_container_width=True)
    
    # Inject CSS khusus untuk key button ini
    st.markdown(
        f"<style>div[data-testid='stButton'] button[key='btn_{page_name}'] {{{style}}}</style>",
        unsafe_allow_html=True
    )
    if clicked:
        st.session_state["page"] = page_name
        st.rerun()

# Layout Navbar
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([2, 2, 2, 2, 6])

with col_nav1:
    nav_button("Dashboard", "dashboard", "🏠")

with col_nav2:
    nav_button("Tenggat Waktu", "tenggang", "📅")

with col_nav3:
    # Logic target halaman tambah data / login
    target_page = "tambah_data" if st.session_state.get("logged_in") else "login"
    nav_button("Tambah Data", target_page, "➕")

with col_nav4:
    st.link_button("📘 Panduan", "https://www.canva.com/design/DAG2aSa3Pcw/p12_M5MLYKVqYiVZW9De1Q/edit?utm_content=DAG2aSa3Pcw&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton", use_container_width=True)

with col_nav5:
    if st.session_state.get("logged_in"):
        col_space, col_btn = st.columns([3, 1.5])
        with col_btn:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state["logged_in"] = False
                st.session_state["page"] = "dashboard"
                st.rerun()

st.markdown("---")

# ========================
# FITUR LOGIN DAN TAMBAH DATA
# ========================
USERS = {"yusuf": "cakep", "dasio": "123"}

if st.session_state.get("page") == "login":
    st.title("🔐 Login Tambah Data")
    with st.form("login_form"):
        email = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
            if email in USERS and USERS[email] == password:
                st.session_state["logged_in"] = True
                st.session_state["user"] = email
                st.session_state["page"] = "tambah_data"
                st.success("Login berhasil! 🎉")
                st.rerun()
            else:
                st.error("Username atau password salah!")

if st.session_state.get("page") == "tambah_data":
    st.subheader("➕ Tambah Data Transaksi")

    kasir_list = sheet_kasir.col_values(2)[1:]

    col1, col2, col3 = st.columns([3, 3, 2])
    with col1:
        kategori = st.selectbox("Kategori", ["UMPEG", "RENVAL", "PIP", "SPPD", "MP", "BANGKOM"], key="kategori_filter")
    with col2:
        kasir = st.selectbox("Kasir", kasir_list, key="kasir_filter")
    with col3:
        jenis_input = st.radio("Pilih Jenis Data yang Akan Dientri:", ["UMK", "SPJ"], horizontal=True)

    with st.form("form_tambah_data"):
        tanggal = st.date_input("Tanggal", datetime.today())
        uraian = st.text_input("Uraian")

        umk, spj = 0, 0
        if jenis_input == "UMK":
            umk = st.number_input("Nominal UMK", min_value=0, step=1000, format="%d")
        else:
            spj = st.number_input("Nominal SPJ", min_value=0, step=1000, format="%d")

        keterangan = st.text_area("Keterangan", placeholder="Opsional...")
        submit = st.form_submit_button("💾 Simpan Data")

    # Ambil data untuk preview 5 data terakhir
    raw_data = sheet_data.get_all_values()
    header = raw_data[0][1:8]  # Kolom B-H
    rows = [r[1:8] for r in raw_data[1:]]
    df_preview = pd.DataFrame(rows, columns=header)

    if not df_preview.empty and "Kategori" in df_preview.columns and "Kasir" in df_preview.columns:
        df_filter = df_preview[(df_preview["Kategori"] == kategori) & (df_preview["Kasir"] == kasir)].tail(5)
        st.subheader(f"📋 5 Transaksi Terakhir ({kategori} - {kasir})")
        if not df_filter.empty:
            st.dataframe(df_filter, use_container_width=True)
        else:
            st.info("ℹ️ Belum ada data untuk kombinasi kategori dan kasir ini.")

    if submit:
        if not uraian:
            st.error("⚠️ Uraian tidak boleh kosong!")
        elif jenis_input == "UMK" and umk == 0:
            st.error("⚠️ Nominal UMK harus lebih dari 0!")
        elif jenis_input == "SPJ" and spj == 0:
            st.error("⚠️ Nominal SPJ harus lebih dari 0!")
        else:
            next_row = len(raw_data) + 1
            # Simpan tanggal dengan format standar Indonesia DD-MM-YYYY agar sinkron saat load
            tgl_str = tanggal.strftime("%d-%m-%Y")
            sheet_data.update(
                f"B{next_row}:H{next_row}",
                [[tgl_str, kategori, kasir, uraian, umk, spj, keterangan]]
            )
            st.success("✅ Data berhasil disimpan ke Spreadsheet!")
            st.rerun()

# ========================
# HALAMAN DASHBOARD
# ========================
if st.session_state["page"] == "dashboard":
    data = sheet_data.get_all_records()
    df = pd.DataFrame(data)

    # Clean Data
    for col in ["UMK", "SPJ"]:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace("Rp", "", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
                .replace("", "0")
                .astype(float)
            )

    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Tanggal"])

    # Filter Section
   # Filter Section
    st.subheader("🔍 Filter Data")
    df["Tahun"] = df["Tanggal"].dt.year
    df["Kategori"] = df["Kategori"].replace("", pd.NA)
    df["Kasir"] = df["Kasir"].replace("", pd.NA)

    c1, c2, c3 = st.columns(3)
    with c1:
        # 1. Ambil daftar unik tahun dari data
        tahun_list = sorted(df["Tahun"].dropna().astype(int).unique().tolist())
        options_tahun = ["Semua"] + tahun_list
        
        # 2. Ambil tahun berjalan saat ini (Dynamic)
        tahun_sekarang = datetime.now().year
        
        # 3. Cek apakah tahun sekarang ada di dalam data sheet
        if tahun_sekarang in tahun_list:
            default_index = options_tahun.index(tahun_sekarang)
        else:
            default_index = 0 # Jika tahun ini belum ada data sama sekali, default ke "Semua"
            
        # 4. Set selectbox dengan index default tahun berjalan
        tahun = st.selectbox("📅 Tahun", options=options_tahun, index=default_index)
    with c2:
        kategori_list = sorted(df["Kategori"].dropna().unique().tolist())
        kategori = st.selectbox("📂 Kategori", options=["Semua"] + kategori_list)

    df_temp = df.copy()
    if tahun != "Semua":
        df_temp = df_temp[df_temp["Tahun"] == tahun]
    if kategori != "Semua":
        df_temp = df_temp[df_temp["Kategori"] == kategori]

    with c3:
        kasir_list = sorted(df_temp["Kasir"].dropna().unique().tolist())
        kasir = st.selectbox("👤 Kasir", options=["Semua"] + kasir_list)

    if kasir != "Semua":
        df_temp = df_temp[df_temp["Kasir"] == kasir]
    df_filtered = df_temp.copy()

    # --- FITUR 1: Transaksi Terakhir ---
    st.markdown("### 🧾 Transaksi Terakhir")
    if not df_filtered.empty:
        last_tx = df_filtered.sort_values("Tanggal", ascending=False).head(1)[
            ["Tanggal", "Kategori", "Kasir", "Uraian", "UMK", "SPJ"]
        ].copy()
        last_tx["Tanggal"] = last_tx["Tanggal"].dt.strftime("%d-%m-%Y")
        for col in ["UMK", "SPJ"]:
            last_tx[col] = last_tx[col].apply(lambda x: f"Rp{int(x):,}".replace(",", "."))
        st.dataframe(last_tx, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada transaksi yang sesuai filter.")

    # Hitung Saldo Berjalan
    df_filtered = df_filtered.sort_values("Tanggal").reset_index(drop=True)
    sisa = []
    saldo = 0
    for _, row in df_filtered.iterrows():
        saldo = saldo - row["SPJ"] + row["UMK"]
        sisa.append(saldo)
    df_filtered["Sisa Saldo"] = sisa

    def format_rupiah(x):
        return f"Rp{int(x):,}".replace(",", ".")

    # Statistik
    st.subheader("📊 Statistik")
    total_umk = df_filtered["UMK"].sum()
    total_spj = df_filtered["SPJ"].sum()
    sisa_akhir = total_umk - total_spj
    realisasi = (total_spj / total_umk * 100) if total_umk > 0 else 0

    stat1, stat2, stat3, stat4 = st.columns(4)
    stat1.metric("💰 Total UMK", format_rupiah(total_umk))
    stat2.metric("📑 Total SPJ", format_rupiah(total_spj))
    stat3.metric("📊 Realisasi SPJ", f"{realisasi:.1f}%")
    stat4.metric("🏦 Sisa Saldo", format_rupiah(sisa_akhir))

    style_metric_cards(background_color="#FFFFFF", border_left_color="#FC5185", border_size_px=4, border_radius_px=12, box_shadow=True)
    st.markdown("<style>[data-testid='stMetricValue'], [data-testid='stMetricLabel'] {color: black !important;}</style>", unsafe_allow_html=True)

    # Data Detail Table
    st.subheader("📋 Data Detail")
    if not df_filtered.empty:
        df_tampil = df_filtered.copy()
        df_tampil["Tenggat Waktu"] = pd.NaT

        # Hitung Tenggat Otomatis
        for (kategori_g, kasir_g), group in df_tampil.groupby(["Kategori", "Kasir"], group_keys=False):
            group = group.sort_values(["Tanggal"]).reset_index()
            for i, row in group.iterrows():
                if row["UMK"] > 0:
                    spj_setelah = group[(group.index > i) & (group["SPJ"] > 0) & (group["Tanggal"] >= row["Tanggal"])]
                    if not spj_setelah.empty:
                        continue
                    tenggat = row["Tanggal"] + pd.Timedelta(days=21)
                    df_tampil.loc[row["index"], "Tenggat Waktu"] = tenggat

        df_tampil["Tanggal"] = df_tampil["Tanggal"].dt.strftime("%d/%m/%Y")
        # Format Hari Indonesia Manual / Default String
        df_tampil["Tenggat Waktu"] = df_tampil["Tenggat Waktu"].dt.strftime("%d/%m/%Y")
        df_tampil["Tenggat Waktu"] = df_tampil["Tenggat Waktu"].fillna("-")

        for col in ["UMK", "SPJ", "Sisa Saldo"]:
            df_tampil[col] = df_tampil[col].apply(lambda x: f"Rp{int(x):,}".replace(",", ".") if pd.notna(x) and x != 0 else "-")

        cols = ["Tanggal", "Kategori", "Kasir", "Uraian", "UMK", "SPJ"]
        if kategori != "Semua" or kasir != "Semua":
            cols.extend(["Sisa Saldo", "Tenggat Waktu"])
        
        st.dataframe(df_tampil[cols], use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Tidak ada data sesuai filter.")

    # --- FITUR EXTRA 1: Visualisasi & Charts ---
    if not df_filtered.empty:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("📈 Grafik SPJ per Uraian")
            df_spj = df_filtered[df_filtered["SPJ"].fillna(0) > 0]
            if not df_spj.empty:
                spj_uraian = df_spj.groupby("Uraian")["SPJ"].sum().reset_index().sort_values("Uraian")
                bars = alt.Chart(spj_uraian).mark_bar(color="#FC5185").encode(
                    x=alt.X("Uraian:N", sort=None, title="Uraian"),
                    y=alt.Y("SPJ:Q", title="Total SPJ (Rp)"),
                    tooltip=["Uraian", alt.Tooltip("SPJ", format=",")]
                )
                st.altair_chart(bars.properties(height=350), use_container_width=True)
            else:
                st.info("📭 Belum ada data SPJ > 0.")
                
        with chart_col2:
            st.subheader("🍕 Proporsi Realisasi per Kategori")
            if total_spj > 0:
                pie_data = df_filtered[df_filtered["SPJ"] > 0].groupby("Kategori")["SPJ"].sum().reset_index()
                pie_chart = alt.Chart(pie_data).mark_arc(innerRadius=50).encode(
                    color=alt.Color("Kategori:N", title="Kategori"),
                    theta=alt.Theta("SPJ:Q"),
                    tooltip=["Kategori", alt.Tooltip("SPJ", format=",")]
                )
                st.altair_chart(pie_chart.properties(height=350), use_container_width=True)
            else:
                st.info("📭 Belum ada pengeluaran SPJ untuk membuat diagram.")

        # Grafik Kategori UMK vs SPJ (Full Width di Bawah)
        st.subheader("📊 Perbandingan UMK & SPJ per Kategori")
        grafik = df_filtered.groupby("Kategori")[["UMK", "SPJ"]].sum().reset_index().melt("Kategori", var_name="Jenis", value_name="Jumlah")
        warna_custom = alt.Scale(domain=["UMK", "SPJ"], range=["#FC5185", "#3FC1C9"])
        
        bar_mix = alt.Chart(grafik).mark_bar().encode(
            x=alt.X("Kategori:N", title="Kategori"),
            y=alt.Y("Jumlah:Q", title="Jumlah (Rp)"),
            color=alt.Color("Jenis:N", scale=warna_custom),
            xOffset="Jenis:N"
        )
        st.altair_chart(bar_mix.properties(height=350), use_container_width=True)

    # Export Section
    st.subheader("📥 Download / Export Data")
    if not df_filtered.empty:
        csv = df_tampil.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Download Data Terfilter (.CSV)",
            data=csv,
            file_name=f"Kasva_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

# ========================
# HALAMAN TENGGANG WAKTU
# ========================
elif st.session_state["page"] == "tenggang":
    loader_html = """
    <div id="loader-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.8); display: flex; justify-content: center; align-items: center; z-index: 9999;">
        <div class="dot-pulse"></div>
    </div>
    <style>
    .dot-pulse { position: relative; left: -9999px; width: 12px; height: 12px; border-radius: 6px; background-color: #4F46E5; color: #4F46E5; box-shadow: 9999px 0 0 -5px; animation: dotPulse 1.5s infinite linear; }
    @keyframes dotPulse { 0% { box-shadow: 9999px 0 0 -5px; } 30% { box-shadow: 9999px 0 0 2px; } 60%,100% { box-shadow: 9999px 0 0 -5px; } }
    </style>
    """
    loader = st.empty()
    loader.markdown(loader_html, unsafe_allow_html=True)

    data_tw = sheet_tw.get_all_records()
    df_tw = pd.DataFrame(data_tw)
    loader.empty()

    if not df_tw.empty:
        for col in ["SPJ", "Keterangan"]:
            if col in df_tw.columns:
                df_tw = df_tw.drop(columns=[col])

        st.subheader("📋 Data Tenggat Waktu")
        
        # --- FITUR EXTRA 2: Kolom Pencarian Data Tenggat ---
        search_query = st.text_input("🔍 Cari berdasarkan Nama Kasir / Uraian / Kategori:", "")
        if search_query:
            # Filter data berdasarkan text pencarian
            df_tw = df_tw[df_tw.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

        def warna_cell(sisa):
            try: sisa = int(sisa)
            except: return "#9d8c8c"
            if sisa <= 5: return "#e74c3c"
            elif 5 < sisa <= 10: return "#f1c40f"
            elif 10 < sisa <= 21: return "#2ecc71"
            else: return "#ffffff"

        # HTML Table Generator
        html = "<table style='width:100%; border-collapse: collapse;'>"
        html += "<tr style='background-color:#4F46E5; color:white;'>"
        for col in df_tw.columns:
            html += f"<th style='padding:10px; border:1px solid #ddd; text-align:center;'>{col}</th>"
        html += "</tr>"

        for i, row in df_tw.iterrows():
            html += "<tr>"
            for col in df_tw.columns:
                val = row[col]
                if col == "Link" and pd.notna(val) and str(val).startswith("http"):
                    val = f'<a href="{val}" target="_blank"><button style="background-color:#43C354; color:white; padding:4px 10px; border:none; border-radius:5px; cursor:pointer;"><img width="20" height="20" src="https://img.icons8.com/color/48/whatsapp--v1.png"/></button></a>'
                elif col == "Sisa Hari":
                    color = warna_cell(val)
                    # Text disesuaikan agar kontras dengan warna background
                    text_color = "white" if color in ["#e74c3c", "#2ecc71"] else "black"
                    val = f"<div style='background-color:{color}; color:{text_color}; padding:6px; font-weight:bold; border-radius:4px; text-align:center;'>{val} Hari</div>"
                elif col == "No":
                    val = f"<div style='text-align:center;'>{val}</div>"

                html += f"<td style='padding:8px; border:1px solid #ddd; text-align:center;'>{val}</td>"
            html += "</tr>"
        html += "</table>"
        
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("⚠️ Tidak ada data tenggat waktu.")