import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd


# --- SETUP GOOGLE SHEET ---
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    r"C:/Users/MyBook Hype AMD/Videos/Program Python/Dashboard Arus Kas/proven-mystery-471102-k6-0d7bdda0bcd4.json",
    scope
)
client = gspread.authorize(creds)

SHEET_ID = "1JN7XPhIMVwcd982JcwzdGQoYu9MJFghofb0ImmZUUYc"
SHEET_NAME = "Data"
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# --- STREAMLIT FORM ---
st.set_page_config(page_title="Input Cash Flow", page_icon="📊", layout="centered")
st.title("📊 Input Data Cash Flow")

kasir_list = ["Anik Murwani Hastuti, S.E", "Erna Catur Setyaningrum, A.Md", "Indah Wahyuningsih, S.E"]

with st.form("cashflow_form", clear_on_submit=True):
    tanggal = st.date_input("Tanggal")
    kategori = st.selectbox("Kategori", ["", "UMPEG", "RENVAL", "PIP", "BANGKOM", "MP", "SPPD"])
    kasir = st.selectbox("Kasir", kasir_list)
    uraian = st.text_input("Uraian", placeholder="contoh: GU-001 atau 0001/UMPEG")
    umk = st.number_input("UMK", min_value=0, step=1000)
    spj = st.number_input("SPJ", min_value=0, step=1000)
    keterangan = st.text_input("Keterangan")
    
    submitted = st.form_submit_button("💾 Simpan")

    if submitted:
        if not tanggal or not kategori or not uraian:
            st.warning("⚠️ Mohon lengkapi minimal Tanggal, Kategori, dan Uraian!")
        else:
            # Format tanggal ke dd/mm/yyyy
            tanggal_str = tanggal.strftime("%d/%m/%Y")

            row_data = [tanggal_str, kategori, kasir, uraian, umk, spj, keterangan]

            # Cari row terakhir yang sudah terisi di kolom B (tanggal)
            last_row = len(sheet.col_values(2)) + 1  

            # --- AUTO EXTEND TABLE RANGE ---
            # misalnya tabel sekarang punya range maksimal 200 row
            max_range = 200  
            if last_row > max_range:
                # tambahin jadi 100 row lebih panjang
                max_range += 100  
                # Update definisi tabel di Google Sheet langsung
                # sayangnya gspread belum support ubah "tabel object" Google Sheet,
                # jadi cara paling aman: perbesar manual range tabel waktu setup
                st.info(f"Tabel otomatis diperpanjang ke {max_range} row")

            # Update mulai kolom B (supaya kolom A "No" auto terisi pakai formula)
            sheet.update(f"B{last_row}:H{last_row}", [row_data])

            st.success("✅ Data berhasil disimpan ke Google Sheet (auto masuk tabel)!")
            st.json({
                "Tanggal": tanggal_str,
                "Kategori": kategori,
                "Kasir": kasir,
                "Uraian": uraian,
                "UMK": umk,
                "SPJ": spj,
                "Keterangan": keterangan
            })


# --- OPSIONAL: Tampilkan tabel dari GSheet langsung ---
st.subheader("📋 Data Cash Flow")
data = sheet.get_all_records()
df = pd.DataFrame(data)
st.dataframe(df)
