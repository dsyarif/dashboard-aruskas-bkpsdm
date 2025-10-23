import streamlit as st
import pandas as pd
import gspread, os, json
from google.oauth2.service_account import Credentials
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards
import altair as alt

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
sheet_data = client.open("KASVA 1.0 - Aplikasi Cash Flow BKPSDM").worksheet("Data")
sheet_kasir = client.open("KASVA 1.0 - Aplikasi Cash Flow BKPSDM").worksheet("Data Kasir")
# Gunakan st.secrets untuk menyimpan kredensial
# scope = ["https://spreadsheets.google.com/feeds",
#          "https://www.googleapis.com/auth/drive"]

# creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
# client = gspread.authorize(creds)

# ========================
# NAVIGASI UTAMA (HORIZONTAL MENU)
# ========================

# Fungsi buat tombol aktif
theme_base = st.get_option("theme.base")

    # sesuaikan warna berdasarkan tema
if theme_base == "dark":
        title_color = "#565D6B"  # putih keabu
        accent_color = "#818CF8"  # ungu lembut
        subtitle_color = "#9CA3AF"
else:
        title_color = "#E5E7EB"  # abu tua
        accent_color = "#4F46E5"  # ungu utama
        subtitle_color = "#6B7280"

    # tampilkan title
st.markdown(
        f"""
        <h1 style='
            font-size:38px; 
            font-weight:800; 
            color:{title_color}; 
            margin-bottom:5px;
        '>
            Dashboard <span style='color:{accent_color}'>KASVA</span> (Kas Virtual)
        </h1>
        <h4 style='
            margin-top:-35px; 
            color:{subtitle_color};
            font-weight:500;
        '>
            BKPSDM Kota Pekalongan
        </h4>
        """,
        unsafe_allow_html=True
    )
if "logged_in" in st.session_state and st.session_state["logged_in"]: 
    st.markdown( f"<div font-weight:600; style='margin-bottom:15px;'>Selamat Datang, <b>{st.session_state['user'].title()}</b>", unsafe_allow_html=True )
# ========================
# NAVIGASI UTAMA (HORIZONTAL MENU)
# ========================

# Fungsi buat tombol aktif
def nav_button(label, page_name, emoji=""):
    is_active = st.session_state["page"] == page_name
    style = (
        "background-color:#4F46E5; color:white; font-weight:600; border:none; border-radius:8px; padding:8px 16px;"
        if is_active else
        "background-color:#F3F4F6; color:#111827; border:none; border-radius:8px; padding:8px 16px;"
    )
    clicked = st.button(f"{emoji} {label}", key=page_name, use_container_width=True)
    st.markdown(
        f"<style>div[data-testid='stButton'] button#{page_name} {{{style}}}</style>",
        unsafe_allow_html=True
    )
    if clicked:
        st.session_state["page"] = page_name
        st.rerun()

# --- Layout Navbar ---
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([2, 2, 2, 2, 6])

with col_nav1:
    if st.button("🏠 Dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()

with col_nav2:
    if st.button("📅 Tenggat Waktu"):
        st.session_state["page"] = "tenggang"
        st.rerun()

with col_nav3:
    if st.button("➕ Tambah Data"):
        if "logged_in" in st.session_state and st.session_state["logged_in"]:
            st.session_state["page"] = "tambah_data"
        else:
            st.session_state["page"] = "login"
        st.rerun()

with col_nav4:
    st.link_button("📘 Panduan", "https://www.canva.com/design/DAG2aSa3Pcw/p12_M5MLYKVqYiVZW9De1Q/edit?utm_content=DAG2aSa3Pcw&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton")

with col_nav5:
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        # Tampilan salam + tombol logout
        col_user, col_btn = st.columns([3, 1])
        with col_user:
            st.markdown(
                f"""
              
                """,
                unsafe_allow_html=True
            )
        with col_btn:
            logout_clicked = st.button("🚪 Logout", use_container_width=True)

        # Aksi Logout
        if logout_clicked:
            st.session_state["logged_in"] = False
            st.session_state["page"] = "dashboard"
            st.rerun()

# ========================
# FITUR LOGIN DAN TAMBAH DATA
# ========================

# --- Daftar user yang diizinkan ---
USERS = {
    "yusuf": "123",
    "dasio": "123"
}

# --- Halaman login ---
if st.session_state["page"] == "login":
    st.title("🔐 Login Tambah Data")
    email = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if email in USERS and USERS[email] == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = email
            st.success("Login berhasil! 🎉")
            st.session_state["page"] = "tambah_data"
            st.rerun()
        else:
            st.error("Username atau password salah!")

# --- Fungsi logout ---
# def logout():
#     if "logged_in" in st.session_state:
#         del st.session_state["logged_in"]
#         del st.session_state["user"]
#         st.session_state["page"] = "dashboard"
#         st.success("Berhasil logout!")
#         st.rerun()

# --- Halaman Tambah Data ---
if st.session_state["page"] == "tambah_data":
    # st.title("➕ Tambah Data")
    st.subheader("➕ Tambah Data")
    # --- Ambil daftar kasir dari Sheet "Data Kasir" ---
    kasir_list = sheet_kasir.col_values(2)[1:]  # kolom B, skip header

    # --- Pilih jenis input (UMK atau SPJ) ---
    jenis_input = st.radio("Pilih Jenis Data yang Akan Dientri:", ["UMK", "SPJ"], horizontal=True)

    # --- Input Form ---
    tanggal = st.date_input("Tanggal", datetime.today())
    kategori = st.selectbox("Kategori", ["UMPEG", "RENVAL", "PIP", "SPPD", "MP", "BANGKOM"])
    kasir = st.selectbox("Kasir", kasir_list)
    uraian = st.text_input("Uraian")

    umk, spj = 0, 0
    if jenis_input == "UMK":
        umk = st.number_input("UMK", min_value=0, step=1000, format="%d")
    else:
        spj = st.number_input("SPJ", min_value=0, step=1000, format="%d")

    keterangan = st.text_area("Keterangan", placeholder="Opsional...")

    # --- Auto-update data setiap kategori atau kasir berubah ---
    # --- Tampilkan 5 Data Terakhir berdasarkan Kategori & Kasir ---
    data = sheet_data.get_all_values()

    # Ambil kolom B sampai H aja
    data = [row[1:9] for row in data[1:]]  # [1:8] artinya kolom B–H, [1:] skip header
    header = sheet_data.row_values(1)[1:9]  # header kolom B–I

    df = pd.DataFrame(data, columns=header)

    if not df.empty and "Kategori" in df.columns and "Kasir" in df.columns:
        if kategori and kasir:
            df_filter = df[
                (df["Kategori"] == kategori) &
                (df["Kasir"] == kasir)
            ].tail(5)

            st.subheader(f"📋 5 Transaksi Terakhir ({kategori} - {kasir})")
            if not df_filter.empty:
                st.dataframe(df_filter, use_container_width=True)
            else:
                st.info("ℹ️ Belum ada data untuk kombinasi kategori dan kasir ini.")
    else:
        st.warning("⚠️ Tidak ada data atau kolom tidak lengkap di spreadsheet.")

    # --- Tombol Simpan ---
    submit = st.button("💾 Simpan Data")

    if submit:
        # Dapatkan jumlah baris terakhir
        next_row = len(sheet_data.get_all_values()) + 1

        # Simpan ke kolom B–H
        sheet_data.update(
            f"B{next_row}:H{next_row}",
            [[str(tanggal), kategori, kasir, uraian, umk, spj, keterangan]]
        )

        st.success("✅ Data berhasil disimpan ke Spreadsheet!")

       

        # Optional biar langsung kelihatan perubahan tanpa reload
        st.rerun()


    # --- Logout ---
    # st.button("🚪 Logout", on_click=lambda: st.session_state.update({"logged_in": False, "page": "login"}))

# ------------------------
# HALAMAN DASHBOARD
# ------------------------
if st.session_state["page"] == "dashboard":
    

    # Bikin kolom kosong buat dorong tombol ke kanan
    # col1, col2 = st.columns([10, 2])

    # with col1:
    #     tenggat = st.button("➡️ Halaman Tenggat Waktu")

    
    # with col2:
    #     st.link_button("📘 Panduan", "https://drive.google.com/file/d/1b_rnjxVg_1bm2SDAAgcS5bP8CUAK_vDl/view")

    # if tenggat:
    #     st.session_state["page"] = "tenggang"
    #     st.rerun()

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

    # Bikin 3 kolom
    c1, c2, c3 = st.columns(3)

    with c1:
        tahun_list = sorted(df.loc[df["Tahun"].notna(), "Tahun"].astype(int).unique().tolist())
        tahun = st.selectbox("📅 Tahun", options=["Semua"] + tahun_list)

    with c2:
        kategori_list = sorted(df["Kategori"].dropna().unique().tolist())
        kategori = st.selectbox("📂 Kategori", options=["Semua"] + kategori_list)

    # Filter sementara untuk ambil daftar kasir sesuai kategori
    df_temp = df.copy()
    if tahun != "Semua":
        df_temp = df_temp[df_temp["Tahun"] == tahun]
    if kategori != "Semua":
        df_temp = df_temp[df_temp["Kategori"] == kategori]

    with c3:
        kasir_list = sorted(df_temp["Kasir"].dropna().unique().tolist())
        kasir = st.selectbox("👤 Kasir", options=["Semua"] + kasir_list)

    # Filter utama
    df_filtered = df_temp.copy()
    if kasir != "Semua":
        df_filtered = df_filtered[df_filtered["Kasir"] == kasir]

    df = df_filtered.copy()


    # --- ✅ FITUR 1: Transaksi Terakhir ---
    st.markdown("### 🧾 Transaksi Terakhir")
    if not df.empty:
        last_tx = df.sort_values("Tanggal", ascending=False).head(1)[
            ["Tanggal", "Kategori", "Kasir", "Uraian", "UMK", "SPJ"]
        ].copy()
        last_tx["Tanggal"] = last_tx["Tanggal"].dt.strftime("%d-%m-%Y")
        for col in ["UMK", "SPJ"]:
            last_tx[col] = last_tx[col].apply(lambda x: f"Rp{int(x):,}".replace(",", "."))
        st.dataframe(last_tx, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada transaksi yang sesuai filter.")


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
        border_left_color="#FC5185",
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

   
    st.subheader("📋 Data Detail")

    if not df.empty:
        df_tampil = df.copy()
        df_tampil["Tanggal"] = pd.to_datetime(df_tampil["Tanggal"], errors="coerce")

        df_tampil["Tenggat Waktu"] = pd.NaT

        # --- Hitung Tenggat Waktu berdasarkan UMK dan SPJ ---
        for (kategori_g, kasir_g), group in df_tampil.groupby(["Kategori", "Kasir"], group_keys=False):
            group = group.sort_values(["Tanggal"]).reset_index()

            for i, row in group.iterrows():
                if row["UMK"] > 0:
                    spj_setelah = group[
                        (group.index > i) &
                        (group["SPJ"] > 0) &
                        (group["Tanggal"] >= row["Tanggal"])
                    ]

                    if not spj_setelah.empty:
                        continue

                    spj_sama_tanggal = group[
                        (group.index < i) &
                        (group["SPJ"] > 0) &
                        (group["Tanggal"] == row["Tanggal"])
                    ]

                    # Tetap hitung tenggat kalau UMK muncul setelah SPJ di tanggal yang sama
                    tenggat = row["Tanggal"] + pd.Timedelta(days=21)
                    df_tampil.loc[row["index"], "Tenggat Waktu"] = tenggat

        # Format tanggal dan rupiah
        df_tampil["Tanggal"] = df_tampil["Tanggal"].dt.strftime("%d/%m/%Y")
        df_tampil["Tenggat Waktu"] = df_tampil["Tenggat Waktu"].dt.strftime("%A, %d/%m/%Y")

        for col in ["UMK", "SPJ", "Sisa Saldo"]:
            if col in df_tampil.columns:
                df_tampil[col] = df_tampil[col].apply(
                    lambda x: f"Rp{int(x):,}".replace(",", ".") if pd.notna(x) and x != "" and x != 0 else "-"
                )

        # --- Tentukan kolom tampil berdasarkan filter ---
        if kategori == "Semua" and kasir == "Semua":
            cols = ["Tanggal", "Kategori", "Kasir", "Uraian", "UMK", "SPJ"]
        else:
            cols = ["Tanggal", "Kategori", "Kasir", "Uraian", "UMK", "SPJ"]
            if "Sisa Saldo" in df_tampil.columns:
                cols.append("Sisa Saldo")
            if "Tenggat Waktu" in df_tampil.columns:
                cols.append("Tenggat Waktu")

        df_tampil = df_tampil[cols]

        st.dataframe(df_tampil, use_container_width=True)

    else:
        st.warning("⚠️ Tidak ada data sesuai filter.")


    # --- ✅ FITUR 2: Grafik SPJ per Uraian ---
    if not df.empty:
        st.subheader("📈 Grafik SPJ per Uraian")

        # 🔍 Filter: hanya ambil baris dengan SPJ > 0
        df_spj = df[df["SPJ"].fillna(0) > 0]

        if not df_spj.empty:
            # 🧮 Kelompokkan per Uraian dan jumlahkan SPJ
            spj_uraian = df_spj.groupby("Uraian")["SPJ"].sum().reset_index()

            # 🅰️ Urutkan berdasarkan nama Uraian (A-Z)
            spj_uraian = spj_uraian.sort_values("Uraian", ascending=True)

            # 🎨 Chart batang utama
            bars = (
                alt.Chart(spj_uraian)
                .mark_bar(color="#FC5185")
                .encode(
                    x=alt.X("Uraian:N", sort=None, title="Uraian"),
                    y=alt.Y("SPJ:Q", title="Total SPJ (Rp)"),
                    tooltip=[
                        alt.Tooltip("Uraian", title="Uraian"),
                        alt.Tooltip("SPJ", title="Total SPJ", format=",")
                    ]
                )
            )

            # 💬 Tambahkan label nominal di atas batang
            text = (
                alt.Chart(spj_uraian)
                .mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-5,  # jarak teks dari batang
                    color="#111827",
                    fontWeight="bold"
                )
                .encode(
                    x=alt.X("Uraian:N", sort=None),
                    y=alt.Y("SPJ:Q"),
                    text=alt.Text("SPJ:Q", format=",")
                )
            )

            # Gabungkan chart batang + label
            chart_spj = (bars + text).properties(height=400)

            st.altair_chart(chart_spj, use_container_width=True)
        else:
            st.info("📭 Belum ada transaksi dengan nilai SPJ > 0.")

    
    # --- Grafik ---
    if not df.empty:
        st.subheader("📊 Grafik UMK & SPJ per Kategori")

        # Kelompokkan data
        grafik = df.groupby("Kategori")[["UMK", "SPJ"]].sum()
        grafik_reset = grafik.reset_index().melt("Kategori", var_name="Jenis", value_name="Jumlah")

        # 🎨 Tentukan warna custom per jenis data
        warna_custom = alt.Scale(
            domain=["UMK", "SPJ"],  # nama-nama kategori di kolom "Jenis"
            range=["#FC5185", "#3FC1C9"]  # warna yang kamu mau (bisa diganti)
        )

        # --- Chart Batang ---
        bar = (
            alt.Chart(grafik_reset)
            .mark_bar()
            .encode(
                x=alt.X("Kategori:N", title="Kategori"),
                y=alt.Y("Jumlah:Q", title="Jumlah (Rp)"),
                color=alt.Color("Jenis:N", scale=warna_custom, title="Jenis"),
                xOffset="Jenis:N"
            )
        )

        # --- Label Nominal ---
        text = (
            alt.Chart(grafik_reset)
            .mark_text(
                align="center",
                baseline="bottom",
                dy=-5,
                color="#111827",
                fontWeight="bold"
            )
            .encode(
                x=alt.X("Kategori:N"),
                y=alt.Y("Jumlah:Q"),
                text=alt.Text("Jumlah:Q", format=",.0f"),
                xOffset="Jenis:N"
            )
        )

        # Gabung bar + teks
        chart = (bar + text).properties(height=400)
        st.altair_chart(chart, use_container_width=True)

    # --- ✅ FITUR 3: Tombol Download / Export Excel ---
    st.subheader("📥 Download / Export Data")
    if not df.empty:
        csv = df_tampil.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Download Data (.CSV)",
            data=csv,
            file_name=f"Kasva_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Tidak ada data untuk diunduh.")
  

# ------------------------
# HALAMAN TENGGANG WAKTU
# ------------------------
elif st.session_state["page"] == "tenggang":
    # st.title("📅 Halaman Tenggat Waktu")

    # Tombol kembali ke Dashboard
    # if st.button("⬅️ Kembali ke Dashboard"):
    #     st.session_state["page"] = "dashboard"
    #     st.rerun()

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
    sheet_tw = client.open("KASVA 1.0 - Aplikasi Cash Flow BKPSDM").worksheet("Tenggat Waktu")
    data_tw = sheet_tw.get_all_records()
    df_tw = pd.DataFrame(data_tw)

    # Hapus loader setelah data siap
    loader.empty()

    if not df_tw.empty:
        # Hilangkan kolom SPJ dan Keterangan kalau ada
        for col in ["SPJ", "Keterangan"]:
            if col in df_tw.columns:
                df_tw = df_tw.drop(columns=[col])

        st.subheader("📋 Data Tenggat Waktu")

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
        st.info("⚠️ Tidak ada data tenggat waktu.")


