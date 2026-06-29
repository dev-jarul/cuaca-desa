import streamlit as st
import requests
import json
import os

# 1. KONFIGURASI HALAMAN MODERN
st.set_page_config(
    page_title="Portal Cuaca Desa Mandiri Jatim", 
    page_icon="⛈️", 
    layout="centered"
)

# Fungsi cerdas membaca FULL database wilayah JSON lokal milik Mas Jarul
@st.cache_data
def muat_data_wilayah():
    if os.path.exists("wilayah.json"):
        with open("wilayah.json", "r") as f:
            return json.load(f)
    else:
        # Cadangan otomatis jika file wilayah.json tidak sengaja terhapus/pindah folder
        return {
            "Pasuruan (Kabupaten)": ["Pandaan", "Bangil", "Prigen"],
            "Bangkalan (Kabupaten)": ["Arosbaya", "Bangkalan Kota"],
            "Sidoarjo (Kabupaten)": ["Sidoarjo Kota", "Waru"]
        }

data_wilayah = muat_data_wilayah()

# HEADER UTAMA
st.markdown("<h2 style='text-align: center; color: #8B4513; margin-bottom: 0;'>⛈️ PORTAL CUACA DESA MANDIRI</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555555; font-size: 14px;'>Sistem Radar Satelit Bergerak Berbasis Otomatis GPS & Full Database Jatim</p>", unsafe_allow_html=True)
st.markdown("---")

# 2. FUNGSI GEOCODING (Mencari Koordinat Otomatis dari Pilihan Manual Wilayah JSON)
@st.cache_data(ttl=86400)
def cari_koordinat_otomatis(kab, kec):
    try:
        kab_clean = kab.split("(")[0].strip()
        query = f"{kec}, {kab_clean}, Jawa Timur, Indonesia"
        url_peta = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1&language=id&format=json"
        respon = requests.get(url_peta, timeout=10)
        if respon.status_code == 200 and "results" in respon.json():
            hasil = respon.json()["results"][0]
            return {"sukses": True, "lat": hasil["latitude"], "lon": hasil["longitude"]}
        
        # Backup jika pencarian terlalu ketat
        url_peta_backup = f"https://geocoding-api.open-meteo.com/v1/search?name={kec}&count=1&language=id&format=json"
        respon_b = requests.get(url_peta_backup, timeout=10)
        if respon_b.status_code == 200 and "results" in respon_b.json():
            hasil = respon_b.json()["results"][0]
            return {"sukses": True, "lat": hasil["latitude"], "lon": hasil["longitude"]}
        return {"sukses": False, "pesan": "Koordinat tidak ditemukan."}
    except:
        return {"sukses": False, "pesan": "Gagal terhubung ke server navigasi."}

# 3. SISTEM AMBIL DATA CUACA NYATA (OPEN-METEO)
@st.cache_data(ttl=600)
def ambil_data_open_meteo(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=Asia%2FJakarta"
        respon = requests.get(url, timeout=10)
        if respon.status_code == 200:
            data = respon.json()["current"]
            code = data["weather_code"]
            
            if code in [0]: cuaca_teks = "Cerah"
            elif code in [1, 2, 3]: cuaca_teks = "Cerah Berawan"
            elif code in [45, 48]: cuaca_teks = "Berkabut"
            elif code in [51, 53, 55, 61, 63, 65]: cuaca_teks = "Hujan Ringan"
            elif code in [80, 81, 82, 95, 96, 99]: cuaca_teks = "Hujan Lebat & Badai Petir"
            else: cuaca_teks = "Berawan"
                
            return {
                "sukses": True,
                "suhu": f"{data['temperature_2m']}°C",
                "kelembaban": f"{data['relative_humidity_2m']}%",
                "angin": f"{data['wind_speed_10m']} km/jam",
                "cuaca": cuaca_teks
            }
        return {"sukses": False, "pesan": "Server satelit sibuk."}
    except:
        return {"sukses": False, "pesan": "Gagal kontak satelit."}

# 4. METODE PEMANTAUAN DENGAN KODE MODERN CLOUD
st.subheader("📍 Metode Pemantauan")

# Menggunakan st.query_params standar modern (menggantikan fungsi lama yang error)
params = st.query_params
gps_lat = params.get("lat")
gps_lon = params.get("lon")

# TOMBOL TRIGGER GPS
html_tombol_gps = """
<button onclick="getLokasi()" style="
    background-color: #4CAF50; color: white; padding: 12px 20px; 
    border: none; border-radius: 8px; cursor: pointer; font-weight: bold;
    width: 100%; font-size: 16px; margin-bottom: 10px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
">📍 KLIK DISINI: Deteksi Otomatis Lokasi Saya via GPS HP</button>

<script>
function getLokasi() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            let lat = position.coords.latitude;
            let lon = position.coords.longitude;
            window.parent.location.search = `?lat=${lat}&lon=${lon}`;
        }, function(error) {
            alert("Gagal mendeteksi GPS. Mohon pastikan fitur Lokasi/GPS di HP Anda sudah dinyalakan.");
        });
    } else {
        alert("Browser Anda tidak mendukung fitur deteksi GPS.");
    }
}
</script>
"""
st.components.v1.html(html_tombol_gps, height=65)

# KOTAK PENCARIAN MANUAL (Membaca file wilayah.json milik Mas Jarul)
with st.expander("🔍 Atau Cari Wilayah Secara Manual (Menggunakan Data wilayah.json)"):
    daftar_kab = sorted(list(data_wilayah.keys()))
    kab_pilih = st.selectbox("Pilih Kabupaten:", options=daftar_kab)
    daftar_kec = sorted(data_wilayah[kab_pilih])
    kec_pilih = st.selectbox("Pilih Kecamatan:", options=daftar_kec)
    
    if st.button("Pantau Wilayah Manual Ini"):
        koordinat_manual = cari_koordinat_otomatis(kab_pilih, kec_pilih)
        if koordinat_manual["sukses"]:
            # Update URL parameter dengan gaya modern standar Cloud
            st.query_params["lat"] = str(koordinat_manual["lat"])
            st.query_params["lon"] = str(koordinat_manual["lon"])
            st.rerun()
        else:
            st.error(f"Gagal mengunci koordinat kecamatan: {koordinat_manual['pesan']}")

# 5. PENENTUAN KOORDINAT AKHIR
if gps_lat and gps_lon:
    latitude = float(gps_lat)
    longitude = float(gps_lon)
    label_lokasi = "📍 Lokasi GPS Aktif Anda"
else:
    # Posisi default saat pertama kali aplikasi dibuka sebelum ada input/GPS (Prigen, Pasuruan)
    latitude = -7.6853
    longitude = 112.6264
    label_lokasi = "📍 Prigen, Pasuruan (Default Sistem)"

st.markdown("---")

# 6. EKSEKUSI TAMPIL DATA & RADAR BERGERAK
info_cuaca = ambil_data_open_meteo(latitude, longitude)

if info_cuaca["sukses"]:
    st.subheader(f"📊 Laporan Cuaca Nyata ({label_lokasi})")
    st.caption(f"Koordinat Terkunci: {latitude}, {longitude}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🌡️ Suhu Udara", value=info_cuaca["suhu"])
    with col2:
        st.metric(label="💧 Kelembaban", value=info_cuaca["kelembaban"])
    with col3:
        st.metric(label="💨 Kec. Angin", value=info_cuaca["angin"])
        
    status_cuaca = info_cuaca["cuaca"]
    st.info(f"**Kondisi Udara Riil Saat Ini:** {status_cuaca}")
    
    # 🚨 LOGIKA PERINGATAN DARURAT SPESIFIK PEKERJA LAPANGAN & PETANI
    if "Petir" in status_cuaca or "Badai" in status_cuaca:
        st.markdown("""
            <style>
            @keyframes kilat { 0%, 100% { background-color: #ff4b4b; box-shadow: 0 0 10px #ff0000; } 50% { background-color: #ffe600; box-shadow: 0 0 25px #ffe600; } }
            .kotak-petir { padding: 18px; border-radius: 8px; color: black; font-weight: bold; animation: kilat 0.8s infinite; text-align: center; font-size: 16px; margin-bottom: 15px; }
            </style>
            <div class="kotak-petir">⚡ ⚠️ PERINGATAN DARURAT BADAI PETIR AKTIF! ⚠️ ⚡</div>
        """, unsafe_allow_html=True)
        
        st.error("""
        **PANDUAN KESELAMATAN SEGERA:**
        * **Bagi Petani:** Segera naik dari area sawah atau ladang terbuka. Cangkul dan sabit berbahan besi bisa memicu petir, taruh di gubuk dan segera amankan diri ke tempat aman.
        * **Bagi Pekerja Bangunan:** Segera turun dari atap, scaffolding (steger), atau struktur rangka baja. Putus aliran listrik alat-alat konstruksi luar ruangan untuk menghindari lonjakan korsleting akibat induksi sambaran petir.
        """)
        # Trigger HP Bergetar Otomatis
        st.components.v1.html("<script>if(navigator.vibrate){navigator.vibrate([500,250,500]);}</script>", height=0)

    elif "Hujan" in status_cuaca:
        st.warning("""
        ### 🌧️ Peringatan Hujan di Lokasi Anda
        * **Bagi Petani:** Harap segera selamatkan jemuran hasil bumi (gabah, jagung, cengkeh) ke area teduh agar terhindar dari jamur.
        * **Bagi Pekerja Bangunan:** Amankan tumpukan semen agar tidak basah, dialihkan sementara ke pengerjaan interior dalam ruangan.
        """)
    else:
        st.success("""
        ### 🟢 Kondisi Cuaca Sangat Bersahabat
        * Sangat aman dan ideal untuk penjemuran komoditas panen maksimal, pengecoran proyek luar ruangan, serta aktivitas kerja di lapangan terbuka.
        """)

    # 7. MAPS SATELIT RADAR BERGERAK
    st.subheader("📡 Radar Satelit Bergerak Menit Ini")
    url_radar = f"https://www.rainviewer.com/map.html?loc={latitude},{longitude},12&oColor=1&tLoop=1&ext=0&cb=1&v=1&sm=1&sn=1"
    st.components.v1.html(f'<iframe src="{url_radar}" width="100%" height="450" frameborder="0" style="border:0; border-radius:12px;"></iframe>', height=460)
    
    # 🎨 PENJELASAN WARNA RADAR UNTUK WARGA DESA
    st.markdown("---")
    st.markdown("### 🎨 Panduan Membaca Warna Awan & Radar Hujan")
    st.markdown("""
    | Warna di Peta | Tingkat Intensitas Hujan | Peringatan & Dampak bagi Lapangan |
    | :--- | :--- | :--- |
    | **🟦 Biru Laut** | Gerimis / Hujan Sangat Ringan | Cuaca mulai basah, jemuran komoditas sebaiknya dipantau. |
    | **🟩 Hijau** | Hujan Ringan - Sedang | Mulai terjadi hujan merata. Pekerjaan luar ruangan bisa tertunda. |
    | **🟨 Kuning** | Hujan Lebat / Deras | Potensi air tergenang di sawah. Amankan semen dan hasil panen! |
    | **🟥 Merah** | Hujan Sangat Lebat | **Bahaya!** Pandangan mata terbatas, waspada banjir luapan saluran. |
    | **🟪 Ungu / Merah Tua** | Hujan Ekstrem & Badai | **Darurat!** Segera cari perlindungan kokoh, rawan petir dan angin kencang. |
    """)
    st.caption("💡 *Petunjuk: Tekan tombol ▶️ (Play) di pojok bawah peta radar untuk melihat ke mana arah pergerakan awan hujan dalam 1 jam ke depan.*")
    
else:
    st.error("Gagal memuat informasi cuaca satelit.")
