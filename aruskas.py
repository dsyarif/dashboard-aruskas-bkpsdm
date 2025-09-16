import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import matplotlib.pyplot as plt

# ------------------------
# AUTH
# ------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    r"C:/Users/MyBook Hype AMD/Videos/Program Python/Dashboard Arus Kas/proven-mystery-471102-k6-0d7bdda0bcd4.json",
    scope
)
client = gspread.authorize(creds)

# ------------------------
# LOAD DATA
# ------------------------
sheet = client.open("KASVA 1.0 - Aplikasi Cash Flow BKPSDM").worksheet("Data")
data = sheet.get_all_records()
df = pd.DataFrame(data)

# cek kolom wajib
required = ["Tanggal", "Kategori", "Uraian", "UMK", "SPJ"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Kolom hilang di sheet: {missing}")
    st.stop()

# ------------------------
# PARSE TANGGAL (aman)
# ------------------------
def parse_tanggal(val):
    if pd.isna(val) or str(val).strip() == "":
        return pd.NaT
    # kalau sudah datetime/date
    if isinstance(val, (datetime.date, datetime.datetime, pd.Timestamp)):
        return pd.to_datetime(val)
    s = str(val).strip()
    # coba beberapa format eksplisit yang umum di sheet (dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy)
    fmts = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%Y/%m/%d"]
    for f in fmts:
        try:
            return pd.to_datetime(datetime.datetime.strptime(s, f))
        except Exception:
            pass
    # fallback: biarkan pandas parse tapi dengan dayfirst=True
    try:
        return pd.to_datetime(s, dayfirst=True, errors="coerce")
    except Exception:
        return pd.NaT

df["Tanggal"] = df["Tanggal"].apply(parse_tanggal)

# ------------------------
# BERSIHKAN UANG jadi numeric
# ------------------------
def clean_money(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
         .str.replace("Rp", "", regex=False)
         .str.replace(" ", "", regex=False)
         .str.replace(".", "", regex=False)
         .str.replace(",", ".", regex=False)
         .str.strip()
         .replace("", "0")
         .pipe(pd.to_numeric, errors="coerce")
         .fillna(0.0)
    )

df["UMK"] = clean_money(df["UMK"])
df["SPJ"] = clean_money(df["SPJ"])

# ------------------------
# HITUNG RUNNING SALDO per kategori
# rule:
#   baris1 = UMK pertama (tidak dikurangi SPJ)
#   baris i>1 = (sisa_prev - SPJ_i) + UMK_i
# ------------------------
df = df.sort_values(by=["Kategori", "Tanggal"], na_position="last").reset_index(drop=True)
df["Sisa Saldo"] = 0.0

for kat in df["Kategori"].dropna().unique():
    mask = df["Kategori"] == kat
    idxs = df[mask].sort_values("Tanggal", na_position="last").index.tolist()
    prev_sisa = None
    for i, idx in enumerate(idxs):
        umk = float(df.at[idx, "UMK"])
        spj = float(df.at[idx, "SPJ"])
        if i == 0:
            sisa = umk  # baris pertama = UMK pertama
        else:
            sisa = (prev_sisa - spj) + umk
        df.at[idx, "Sisa Saldo"] = sisa
        prev_sisa = sisa

# ------------------------
# DASHBOARD
# ------------------------
st.set_page_config(page_title="Dashboard BKPSDM", layout="wide")
st.title("📊 Dashboard Cash Flow BKPSDM")
st.caption("Data live dari Google Sheets — tanggal ditampilkan dd-mm-yyyy")

# filter kategori
kategori_list = ["Semua"] + sorted(df["Kategori"].dropna().unique().tolist())
kategori = st.selectbox("Pilih Kategori:", kategori_list)

# metrics (pakai data yang sudah dihitung)
if kategori != "Semua":
    dff = df[df["Kategori"] == kategori].sort_values("Tanggal").copy()
else:
    dff = df.copy()

total_umk = dff["UMK"].sum()
total_spj = dff["SPJ"].sum()
sisa_akhir = dff["Sisa Saldo"].iloc[-1] if not dff.empty else 0.0
progress = (total_spj / total_umk * 100) if total_umk > 0 else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total UMK", f"Rp{total_umk:,.0f}")
c2.metric("Total SPJ", f"Rp{total_spj:,.0f}")
c3.metric("Realisasi SPJ", f"{progress:.1f}%")
c4.metric("Sisa Saldo Akhir", f"Rp{sisa_akhir:,.0f}")

st.progress(min(progress/100, 1.0))

# ------------------------
# TAMPILAN TABEL
# format tanggal ke string dd-mm-yyyy dulu biar pasti tampil sesuai
# ------------------------
st.subheader("📋 Data Detail")
display_df = dff.copy()
# kalau kolom Tanggal datetime, ubah ke string format; kalo NaT -> ""
if "Tanggal" in display_df.columns:
    display_df["Tanggal"] = display_df["Tanggal"].dt.strftime("%d-%m-%Y")
    display_df["Tanggal"] = display_df["Tanggal"].fillna("")

if kategori != "Semua":
    cols = ["Tanggal", "Uraian", "UMK", "SPJ", "Sisa Saldo"]
    if display_df.empty:
        st.warning("Data kosong untuk kategori ini.")
    else:
        st.dataframe(
            display_df[cols].style.format({"UMK": "Rp{:,.0f}", "SPJ": "Rp{:,.0f}", "Sisa Saldo": "Rp{:,.0f}"}),
            use_container_width=True
        )
else:
    cols_all = ["Tanggal", "Kategori", "Uraian", "UMK", "SPJ", "Sisa Saldo"]
    st.dataframe(
        display_df[cols_all].style.format({"UMK": "Rp{:,.0f}", "SPJ": "Rp{:,.0f}", "Sisa Saldo": "Rp{:,.0f}"}),
        use_container_width=True
    )

# ------------------------
# GRAFIK: grup per kategori (UMK, SPJ, Sisa Saldo akhir)
# ------------------------
st.subheader("📊 UMK, SPJ, & Sisa Saldo per Kategori")
agg = df.groupby("Kategori")[["UMK", "SPJ"]].sum()
agg["Sisa Saldo"] = df.groupby("Kategori")["Sisa Saldo"].last()

agg_plot = agg.loc[[kategori]] if kategori != "Semua" else agg
if not agg_plot.empty:
    st.bar_chart(agg_plot)
else:
    st.info("Belum ada data untuk digrafikkan.")
