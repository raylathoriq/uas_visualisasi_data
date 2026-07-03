# app.py - Dashboard SDM Dosen Kampus XYZ (Streamlit + Plotly)
# Jalankan: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ================== Konfigurasi Halaman ==================
st.set_page_config(
    page_title="Dashboard SDM Dosen Kampus XYZ",
    layout="wide",
)

# ================== Load & Siapkan Data ==================
@st.cache_data
def load_data(path="data_pegawai_clean.csv"):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    # Usia (hitung dari tgl_lahir bila belum ada)
    if "usia" not in df.columns and "tgl_lahir" in df.columns:
        df["tgl_lahir"] = pd.to_datetime(df["tgl_lahir"], errors="coerce")
        today = pd.Timestamp(datetime.now())
        df["usia"] = (today - df["tgl_lahir"]).dt.days // 365
    df["usia"] = pd.to_numeric(df.get("usia"), errors="coerce")

    # Status sertifikasi (bila belum ada)
    if "status_sertifikasi" not in df.columns and "sertifikasi" in df.columns:
        df["status_sertifikasi"] = df["sertifikasi"].apply(
            lambda x: "Bersertifikat" if pd.notna(x) and str(x).strip() != "" else "Belum Sertifikasi"
        )

    # Jabatan akademik kosong -> Belum Ada
    if "jabatan_akademik" in df.columns:
        df["jabatan_akademik"] = df["jabatan_akademik"].fillna("Belum Ada").replace("", "Belum Ada")

    # Tahun pengangkatan jabatan (buang anomali < 1990)
    if "tgl_jabatan_akademik" in df.columns:
        df["tgl_jabatan_akademik"] = pd.to_datetime(df["tgl_jabatan_akademik"], errors="coerce")
        df["tahun_jabatan"] = df["tgl_jabatan_akademik"].dt.year
        df.loc[df["tahun_jabatan"] < 1990, "tahun_jabatan"] = pd.NA

    # Tahun sertifikasi bersih
    if "tahun_sertifikasi" in df.columns:
        df["tahun_sertifikasi"] = pd.to_numeric(df["tahun_sertifikasi"], errors="coerce")
        df.loc[df["tahun_sertifikasi"] < 1990, "tahun_sertifikasi"] = pd.NA

    return df

df = load_data()

# ================== Warna Tema ==================
MERAH = "#B03A2E"
ORANYE = "#E67E22"

# ================== Sidebar Filter ==================
st.sidebar.header("🔎 Filter")

def buat_filter(label, kolom):
    if kolom in df.columns:
        opsi = sorted(df[kolom].dropna().unique().tolist())
        return st.sidebar.multiselect(label, opsi, default=opsi)
    return None

f_fak = buat_filter("Fakultas", "fakultas")
f_ser = buat_filter("Status Sertifikasi", "status_sertifikasi")
f_peg = buat_filter("Status Pegawai", "stat_pegawai")

dff = df.copy()
if f_fak is not None:
    dff = dff[dff["fakultas"].isin(f_fak)]
if f_ser is not None:
    dff = dff[dff["status_sertifikasi"].isin(f_ser)]
if f_peg is not None:
    dff = dff[dff["stat_pegawai"].isin(f_peg)]

# ================== Judul ==================
st.title("Dashboard SDM Dosen Kampus XYZ")


# ================== KPI Cards ==================
total = len(dff)
def pct(mask):
    return (mask.mean() * 100) if total else 0

pct_ser = pct(dff["status_sertifikasi"].eq("Bersertifikat")) if "status_sertifikasi" in dff else 0
pct_s3 = pct(dff["pendidikan"].eq("S3")) if "pendidikan" in dff else 0
pct_pen = pct(dff["usia"].gt(55))
jml_prof = int(dff["jabatan_akademik"].eq("Profesor").sum()) if "jabatan_akademik" in dff else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Dosen", f"{total}")
k2.metric("Bersertifikat", f"{pct_ser:.1f}%")
k3.metric("Pendidikan S3", f"{pct_s3:.1f}%")
k4.metric("Usia > 55", f"{pct_pen:.1f}%")
k5.metric("Jumlah Profesor", f"{jml_prof}")

st.divider()

# ================== Baris 1: Perbandingan ==================
c1, c2 = st.columns(2)
with c1:
    st.subheader("Jumlah Dosen per Fakultas")
    d = dff["fakultas"].value_counts().reset_index()
    d.columns = ["Fakultas", "Jumlah"]
    fig = px.bar(d.sort_values("Jumlah"), x="Jumlah", y="Fakultas",
                 orientation="h", text="Jumlah", color_discrete_sequence=[MERAH])
    fig.update_layout(yaxis_title="", xaxis_title="Jumlah Dosen")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("Distribusi Jabatan Akademik")
    d = dff["jabatan_akademik"].value_counts().reset_index()
    d.columns = ["Jabatan", "Jumlah"]
    fig = px.bar(d, x="Jabatan", y="Jumlah", text="Jumlah", color_discrete_sequence=[MERAH])
    fig.update_layout(xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

# ================== Baris 2: Time Series ==================
c3, c4 = st.columns(2)
with c3:
    st.subheader("Tren Sertifikasi per Tahun")
    if "tahun_sertifikasi" in dff:
        d = dff.dropna(subset=["tahun_sertifikasi"])
        d = d["tahun_sertifikasi"].astype(int).value_counts().sort_index().reset_index()
        d.columns = ["Tahun", "Jumlah"]
        fig = px.line(d, x="Tahun", y="Jumlah", markers=True, color_discrete_sequence=[MERAH])
        st.plotly_chart(fig, use_container_width=True)
with c4:
    st.subheader("Pengangkatan Jabatan per Tahun")
    if "tahun_jabatan" in dff:
        d = dff.dropna(subset=["tahun_jabatan"])
        d = d["tahun_jabatan"].astype(int).value_counts().sort_index().reset_index()
        d.columns = ["Tahun", "Jumlah"]
        fig = px.area(d, x="Tahun", y="Jumlah", color_discrete_sequence=[MERAH])
        st.plotly_chart(fig, use_container_width=True)

# ================== Baris 3: Distribusi ==================
c5, c6 = st.columns(2)
with c5:
    st.subheader("Distribusi Usia (Histogram)")
    fig = px.histogram(dff.dropna(subset=["usia"]), x="usia", nbins=12, color_discrete_sequence=[MERAH])
    fig.update_layout(xaxis_title="Usia", yaxis_title="Jumlah Dosen", bargap=0.05)
    st.plotly_chart(fig, use_container_width=True)
with c6:
    st.subheader("Sebaran Usia per Fakultas (Boxplot)")
    fig = px.box(dff.dropna(subset=["usia"]), x="fakultas", y="usia", color_discrete_sequence=[MERAH])
    fig.update_layout(xaxis_title="", yaxis_title="Usia")
    st.plotly_chart(fig, use_container_width=True)

# ================== Baris 4: Relationship ==================
st.subheader("Hubungan Usia dan Jabatan Akademik")
urutan = ["Belum Ada", "Asisten Ahli", "Lektor", "Lektor Kepala", "Profesor"]
d = dff.dropna(subset=["usia"])
fig = px.strip(d, x="usia", y="jabatan_akademik", color="jk",
               category_orders={"jabatan_akademik": urutan},
               color_discrete_sequence=[ORANYE, MERAH])
fig.update_layout(xaxis_title="Usia", yaxis_title="")
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("© Kelompok 3 - Proyek Akhir Visualisasi Data, D3 Sistem Informasi")
