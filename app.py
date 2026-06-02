# app.py
# ==============================================================================
# WEB APP OPTIMASI STARTING XI SEPAKBOLA
# Menggunakan Algoritma Branch and Bound Teroptimasi & Streamlit Visualizer
# ==============================================================================

import streamlit as st
import pandas as pd
import heapq
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Any
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Optimasi Starting XI - Pemrograman Linear",
    page_icon="⚽",
    layout="wide"
)

# ==============================================================================
# 1. KONFIGURASI FORMASI, KOMPATIBILITAS & KOORDINAT LAPANGAN
# ==============================================================================

# Definisikan Formasi Utama (Total Kuota per Formasi Selalu Tepat 11 Slot)
FORMASI_TERSEDIA: Dict[str, Dict[str, int]] = {
    "4-3-3": {"GK": 1, "LB": 1, "CB": 2, "RB": 1, "CDM": 1, "CM": 2, "LW": 1, "RW": 1, "ST": 1},
    "4-4-2": {"GK": 1, "LB": 1, "CB": 2, "RB": 1, "CDM": 1, "CM": 3, "ST": 2},
    "4-2-3-1": {"GK": 1, "LB": 1, "CB": 2, "RB": 1, "CDM": 2, "CAM": 2, "LW": 1, "ST": 1},
    "3-5-2": {"GK": 1, "CB": 3, "CDM": 1, "CM": 2, "CAM": 1, "RB": 1, "ST": 2},
}

# Aturan Kompatibilitas Posisi Alternatif beserta Penalti Ratingnya
# Format: Taktis_Slot -> List Tuple (Posisi_Asli_Dataset, Penalti_Rating)
ATURAN_KOMPATIBILITAS: Dict[str, List[Tuple[str, int]]] = {
    "GK": [("GK", 0)],
    "CB": [("CB", 0)],
    "LB": [("LB", 0), ("RB", -5)],
    "RB": [("RB", 0), ("LB", -5)],
    "CDM": [("CDM", 0), ("CM", 0)],
    "CM": [("CM", 0), ("CDM", 0), ("CAM", 0)],
    "CAM": [("CAM", 0), ("CM", 0), ("ST", -10)],
    "LW": [("LW", 0), ("RW", -5)],
    "RW": [("RW", 0), ("LW", -5)],
    "ST": [("ST", 0)]
}

# Koordinat Spasial Unik Lapangan (X: 0-100, Y: 0-100) untuk Mencegah Pemain Bertumpuk
FORMASI_POSISI: Dict[str, Dict[str, List[Tuple[float, float]]]] = {
    "4-3-3": {
        "GK": [(50.0, 8.0)],
        "LB": [(15.0, 26.0)],
        "CB": [(38.0, 23.0), (62.0, 23.0)],
        "RB": [(85.0, 26.0)],
        "txt_offset": [(50, 10)], 
        "CDM": [(50.0, 42.0)],
        "CM": [(33.0, 56.0), (67.0, 56.0)],
        "LW": [(20.0, 80.0)],
        "RW": [(80.0, 80.0)],
        "ST": [(50.0, 88.0)]
    },
    "4-4-2": {
        "GK": [(50.0, 8.0)],
        "LB": [(15.0, 26.0)],
        "CB": [(38.0, 23.0), (62.0, 23.0)],
        "RB": [(85.0, 26.0)],
        "CM": [(25.0, 54.0), (50.0, 58.0), (75.0, 54.0)],
        "txt_offset": [(50, 10)], 
        "CDM": [(50.0, 40.0)],
        "ST": [(35.0, 86.0), (65.0, 86.0)]
    },
    "4-2-3-1": {
        "GK": [(50.0, 8.0)],
        "LB": [(15.0, 26.0)],
        "CB": [(38.0, 23.0), (62.0, 23.0)],
        "RB": [(85.0, 26.0)],
        "CDM": [(35.0, 44.0), (65.0, 44.0)],
        "CAM": [(35.0, 66.0), (65.0, 66.0)],
        "LW": [(18.0, 80.0)],
        "ST": [(50.0, 88.0)]
    },
    "3-5-2": {
        "GK": [(50.0, 8.0)],
        "CB": [(25.0, 23.0), (50.0, 23.0), (75.0, 23.0)],
        "CDM": [(50.0, 42.0)],
        "CM": [(30.0, 58.0), (70.0, 58.0)],
        "CAM": [(50.0, 68.0)],
        "RB": [(85.0, 48.0)],
        "ST": [(35.0, 88.0), (65.0, 88.0)]
    }
}


# ==============================================================================
# 2. STRUKTUR DATA & ENGINE DATA PRE-PROCESSING
# ==============================================================================

@dataclass
class KandidatPemain:
    nama: str
    posisi_asli: str
    rating_efektif: int
    harga: float

def bangun_kandidat_per_slot(df: pd.DataFrame, formasi: Dict[str, int]) -> List[Tuple[str, List[KandidatPemain]]]:
    """
    Membangun daftar kandidat pemain per slot taktis lengkap dengan kalkulasi rating efektif.
    """
    slots_kandidat = []
    
    # Validasi dasar kolom dataset
    kolom_wajib = {"Name", "Position", "Overall", "Value_EUR"}
    if not kolom_wajib.issubset(df.columns):
        st.error(f"Dataset harus memiliki kolom-kolom berikut: {kolom_wajib}")
        return []

    for posisi_taktis, jumlah_slot in formasi.items():
        aturan_pos = ATURAN_KOMPATIBILITAS.get(posisi_taktis, [(posisi_taktis, 0)])
        list_pemain_kompatibel = []
        
        for pos_asli, penalti in aturan_pos:
            sub_df = df[df["Position"] == pos_asli].copy()
            for _, row in sub_df.iterrows():
                rating_ef = int(row["Overall"] + penalti)
                list_pemain_kompatibel.append(
                    KandidatPemain(
                        nama=str(row["Name"]),
                        posisi_asli=str(row["Position"]),
                        rating_efektif=max(0, rating_ef),
                        harga=float(row["Value_EUR"])
                    )
                )
        
        # Urutkan berdasarkan rating efektif terbaik untuk optimasi bounding
        list_pemain_kompatibel.sort(key=lambda x: x.rating_efektif, reverse=True)
        
        # Setiap slot taktis direplikasi secara independen sesuai kuota formasi
        for _ in range(jumlah_slot):
            slots_kandidat.append((posisi_taktis, list_pemain_kompatibel))
            
    return slots_kandidat


# ==============================================================================
# 3. ALGORITMA BRANCH AND BOUND (TEROPTIMASI)
# ==============================================================================

@dataclass(order=True)
class NodeBB:
    neg_ub: float  # Digunakan sebagai prioritas di Max-Heap (Heapq secara default Min-Heap)
    level: int = field(compare=False)
    rating_akumulasi: int = field(compare=False)
    budget_sisa: float = field(compare=False)
    tim_dipilih: list = field(compare=False)
    set_nama_terpakai: frozenset = field(compare=False)

def hitung_upper_bound(level: int, rating_kini: int, sisa_budget: float, 
                       slots: List[Tuple[str, List[KandidatPemain]]], 
                       set_terpakai: frozenset) -> float:
    """
    Menghitung batas atas rating menggunakan pendekatan Relaksasi Pecahan Knapsack (Fractional Upper Bound).
    """
    ub = float(rating_kini)
    budget_temp = sisa_budget
    
    for i in range(level, len(slots)):
        _, kandidat_list = slots[i]
        pemain_terpilih = None
        
        # Cari pemain terbaik yang belum digunakan pada silsilah node ini
        for p in kandidat_list:
            if p.nama not in set_terpakai:
                pemain_terpilih = p
                break
                
        if not pemain_terpilih:
            return float('-inf')  # Invalid branch, tidak cukup pemain unik tersedia
            
        if pemain_terpilih.harga <= budget_temp:
            ub += pemain_terpilih.rating_efektif
            budget_temp -= pemain_terpilih.harga
        else:
            if pemain_terpilih.harga > 0:
                # Ambil nilai fraksional dari rating pemain jika budget tersisa tidak mencukupi sepenuhnya
                ub += pemain_terpilih.rating_efektif * (budget_temp / pemain_terpilih.harga)
            break
            
    return ub

def run_branch_and_bound(df: pd.DataFrame, nama_formasi: str, budget_total: float) -> Tuple[int, List[Dict], Dict]:
    """
    Eksekusi Algoritma Branch and Bound untuk Pencarian Komposisi Pemain Optimal.
    """
    formasi = FORMASI_TERSEDIA[nama_formasi]
    slots = bangun_kandidat_per_slot(df, formasi)
    n_slots = len(slots)
    
    # Validasi Awal: Memastikan jumlah slot tepat 11 pemain
    if n_slots != 11:
        return 0, [], {"error": "Konfigurasi slot formasi tidak valid (Harus 11)."}
        
    # State Variabel Tracker
    best_rating = -1
    best_lineup: List[Dict] = []
    
    nodes_explored = 0
    nodes_pruned = 0
    waktu_mulai = time.time()
    
    # Hitung Bounding awal root node
    ub_root = hitung_upper_bound(0, 0, budget_total, slots, frozenset())
    if ub_root == float('-inf'):
        return 0, [], {"error": "Jumlah skuad dalam dataset kurang untuk memenuhi kriteria keunikan formasi."}
        
    root = NodeBB(
        neg_ub=-ub_root,
        level=0,
        rating_akumulasi=0,
        budget_sisa=budget_total,
        tim_dipilih=[],
        set_nama_terpakai=frozenset()
    )
    
    priority_queue = [root]
    
    while priority_queue:
        node_aktif = heapq.heappop(priority_queue)
        nodes_explored += 1
        
        # Pruning: Jika batas atas node saat ini sudah lebih kecil atau sama dengan rating terbaik yang ditemukan
        if -node_aktif.neg_ub <= best_rating:
            nodes_pruned += 1
            continue
            
        # Base Case: Skuad 11 pemain telah lengkap terbentuk di leaf node
        if node_aktif.level == n_slots:
            if node_aktif.rating_akumulasi > best_rating:
                best_rating = node_aktif.rating_akumulasi
                best_lineup = node_aktif.tim_dipilih
            continue
            
        posisi_slot, kandidat_list = slots[node_aktif.level]
        
        # Percabangan Branching berdasarkan daftar kandidat
        count_branch = 0
        for p in kandidat_list:
            if p.nama in node_aktif.set_nama_terpakai:
                continue
                
            # Constraint Budget Check
            if p.harga > node_aktif.budget_sisa:
                nodes_pruned += 1
                continue
                
            count_branch += 1
            # Batasi percabangan heuristik per tingkat demi menghindari kombinasi meledak (max 15 cabang terbaik)
            if count_branch > 15:
                break
                
            next_set_terpakai = node_aktif.set_nama_terpakai | {p.nama}
            next_rating = node_aktif.rating_akumulasi + p.rating_efektif
            next_budget = node_aktif.budget_sisa - p.harga
            
            detail_pemain = {
                "Slot": posisi_slot,
                "Nama": p.nama,
                "Posisi Asli": p.posisi_asli,
                "Rating Efektif": p.rating_efektif,
                "Harga EUR": p.harga
            }
            next_lineup = node_aktif.tim_dipilih + [detail_pemain]
            
            # Hitung Bound Anak Node
            ub_child = hitung_upper_bound(node_aktif.level + 1, next_rating, next_budget, slots, next_set_terpakai)
            
            if ub_child <= best_rating:
                nodes_pruned += 1
                continue
                
            child_node = NodeBB(
                neg_ub=-ub_child,
                level=node_aktif.level + 1,
                rating_akumulasi=next_rating,
                budget_sisa=next_budget,
                tim_dipilih=next_lineup,
                set_nama_terpakai=next_set_terpakai
            )
            heapq.heappush(priority_queue, child_node)
            
    waktu_eksekusi = time.time() - waktu_mulai
    total_nodes = nodes_explored + nodes_pruned
    efisiensi = (nodes_pruned / total_nodes * 100) if total_nodes > 0 else 0
    
    statistik = {
        "nodes_explored": nodes_explored,
        "nodes_pruned": nodes_pruned,
        "waktu_eksekusi": f"{waktu_eksekusi:.4f} detik",
        "efisiensi_pruning": f"{efisiensi:.2f}%"
    }
    
    return best_rating, best_lineup, statistik


# ==============================================================================
# 4. ENGINE VISUALISASI LAPANGAN SEPAKBOLA MODERN
# ==============================================================================

def gambar_stadium_formasi(best_lineup: List[Dict], nama_formasi: str):
    """
    Menggambar representasi visual lapangan stadion taktis 2D menggunakan Matplotlib.
    """
    fig, ax = plt.subplots(figsize=(11, 8.5))
    fig.patch.set_facecolor("#0f172a") # Slate Dark modern background
    ax.set_facecolor("#15803d")        # Lapangan Hijau Estetik
    
    # Pola Garis Belang Lapangan Rumput (Zebra Striping Pitch)
    for y_strip in range(0, 100, 10):
        warna_rumput = "#166534" if (y_strip // 10) % 2 == 0 else "#15803d"
        ax.axhspan(y_strip, y_strip + 10, facecolor=warna_rumput, alpha=1.0, zorder=0)
        
    # Gambar Garis Batas Markah Lapangan Luar & Tengah
    ax.plot([0, 100, 100, 0, 0], [0, 0, 100, 100, 0], color="#f8fafc", linewidth=2.5, zorder=1)
    ax.plot([0, 100], [50, 50], color="#f8fafc", linewidth=2.5, zorder=1)
    
    # Lingkaran Titik Tengah Lapangan
    lingkaran_tengah = plt.Circle((50, 50), 12, color="#f8fafc", fill=False, linewidth=2.5, zorder=1)
    ax.add_patch(lingkaran_tengah)
    ax.scatter(50, 50, color="#f8fafc", s=40, zorder=2)
    
    # Kotak Penalti Sisi Atas (Gawang Lawan)
    ax.add_patch(patches.Rectangle((20, 80), 60, 20, fill=False, edgecolor="#f8fafc", linewidth=2.5, zorder=1))
    ax.add_patch(patches.Rectangle((35, 92), 30, 8, fill=False, edgecolor="#f8fafc", linewidth=1.5, zorder=1))
    
    # Kotak Penalti Sisi Bawah (Gawang Kita)
    ax.add_patch(patches.Rectangle((20, 0), 60, 20, fill=False, edgecolor="#f8fafc", linewidth=2.5, zorder=1))
    ax.add_patch(patches.Rectangle((35, 0), 30, 8, fill=False, edgecolor="#f8fafc", linewidth=1.5, zorder=1))
    
    # Palet Warna Khusus untuk Setiap Peran Taktis
    skema_warna: Dict[str, str] = {
        "GK": "#38bdf8", "LB": "#fb7185", "CB": "#60a5fa", "RB": "#c084fc",
        "CDM": "#f59e0b", "CM": "#4ade80", "CAM": "#a3e635", "LW": "#f43f5e",
        "RW": "#e2e8f0", "ST": "#f43f5e"
    }
    
    # Peta koordinat formasi terpilih
    peta_koordinat = FORMASI_POSISI[nama_formasi]
    indeks_counter: Dict[str, int] = {}
    
    # Plotting Pemain ke Titik Lapangan
    for pemain in best_lineup:
        pos = pemain["Slot"]
        idx = indeks_counter.get(pos, 0)
        indeks_counter[pos] = idx + 1
        
        # Validasi keamanan penarikan koordinat
        if pos in peta_koordinat and idx < len(peta_koordinat[pos]):
            x, y = peta_koordinat[pos][idx]
        else:
            # Fallback jika terjadi anomali koordinat
            x, y = 50.0, 50.0
            
        warna_node = skema_warna.get(pos, "#94a3b8")
        
        # Efek Bayangan Belakang (Shadowing) untuk Kedalaman Visual
        ax.scatter(x, y - 1.2, s=2100, color="#020617", alpha=0.4, zorder=2)
        
        # Lingkaran Utama Penanda Pemain
        ax.scatter(x, y, s=1800, color=warna_node, edgecolors="#ffffff", linewidths=2.5, zorder=3)
        
        # Render Informasi Teks Pemain Multi-baris agar Tidak Saling Menimpa
        nama_pendek = pemain["Nama"].split()[-1] if len(pemain["Nama"].split()) > 0 else pemain["Nama"]
        if len(nama_pendek) > 10:
            nama_pendek = nama_pendek[:9] + ".."
            
        # Teks Nama (Tengah Lingkaran Atas)
        ax.text(x, y + 1.8, nama_pendek, ha="center", va="center", fontsize=10, color="#ffffff", weight="bold", zorder=4)
        
        # Teks Rating (Tengah Lingkaran Pusat)
        ax.text(x, y - 1.0, f"OVR {pemain['Rating Efektif']}", ha="center", va="center", fontsize=11, color="#0f172a", weight="black", zorder=4)
        
        # Teks Label Taktis Pemain (Di Bawah Lingkaran Utama)
        ax.text(x, y - 5.5, f"[{pos}]", ha="center", va="center", fontsize=9, color="#f1f5f9", weight="bold",
                bbox=dict(facecolor="#1e293b", alpha=0.8, boxstyle="round,pad=0.2", edgecolor="none"), zorder=4)

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    st.pyplot(fig)


# ==============================================================================
# 5. USER INTERFACE (STREAMLIT DASHBOARD)
# ==============================================================================

st.title("⚽ Sistem Optimasi & Visualisasi Komposisi Pemain Starting XI")
st.markdown("Aplikasi penentu skuad sepak bola terbaik berbasis kecerdasan komputasi algoritma **Branch and Bound**.")

# Panel Sidebar Input Kontrol Konten
st.sidebar.header("⚙️ Parameter Sistem")
formasi_terpilih = st.sidebar.selectbox("Pilih Pola Formasi Taktis:", list(FORMASI_TERSEDIA.keys()))
budget_input_juta = st.sidebar.number_input("Batas Maksimal Anggaran Budget (Juta EUR):", min_value=10.0, max_value=5000.0, value=500.0, step=10.0)
budget_aktual_eur = budget_input_juta * 1_000_000

# Manajemen Layout Halaman Utama
uploaded_file = st.file_uploader("Unggah File Dataset Pemain (.CSV):", type=["csv"])

if uploaded_file:
    df_pemain = pd.read_csv(uploaded_file)
    
    col_preview, col_config_check = st.columns([2, 1])
    with col_preview:
        st.subheader("📋 Data Mentah Pemain (Sampel Dataset)")
        st.dataframe(df_pemain.head(8), use_container_width=True)
        
    with col_config_check:
        st.subheader("🔍 Validasi Ketersediaan Posisi")
        formasi_obj = FORMASI_TERSEDIA[formasi_terpilih]
        
        # Validasi Kecukupan Anggota Pemain per Posisi sebelum Memulai Running
        is_data_aman = True
        status_list = []
        for pos_req, kuota in formasi_obj.items():
            pos_alternatif = [p_asli for p_asli, _ in ATURAN_KOMPATIBILITAS.get(pos_req, [(pos_req, 0)])]
            tersedia_di_csv = df_pemain[df_pemain["Position"].isin(pos_alternatif)].shape[0]
            if tersedia_di_csv < kuota:
                status_list.append(f"❌ **{pos_req}**: Butuh {kuota}, hanya ada {tersedia_di_csv} di CSV.")
                is_data_aman = False
            else:
                status_list.append(f"✅ **{pos_req}**: Terpenuhi ({tersedia_di_csv} tersedia).")
                
        st.markdown("\n".join(status_list))
        
    if not is_data_aman:
        st.error("Gagal Melanjutkan: Dataset Anda kekurangan pemain spesifik posisi untuk membentuk formasi ini.")
    else:
        if st.button("🚀 Jalankan Optimasi Pencarian Starting XI Terbaik"):
            with st.spinner("Algoritma sedang mengeksplorasi pohon ruang status (Branch and Bound)..."):
                total_rating, lineup_final, stats = run_branch_and_bound(df_pemain, formasi_terpilih, budget_aktual_eur)
                
            if "error" in stats:
                st.error(stats["error"])
            elif not lineup_final:
                st.error("Solusi Tidak Ditemukan! Batasan budget terlalu ketat untuk membeli 11 pemain posisi tersebut.")
            else:
                st.success("Solusi Optimal Berhasil Ditemukan!")
                
                # Mengubah output list ke representasi tabel dataframe komersial
                df_lineup = pd.DataFrame(lineup_final)
                df_lineup["Harga (Juta EUR)"] = df_lineup["Harga EUR"] / 1_000_000
                df_lineup_display = df_lineup[["Slot", "Nama", "Posisi Asli", "Rating Efektif", "Harga (Juta EUR)"]]
                
                # Informasi Ringkasan Finansial Tim
                total_pengeluaran_juta = df_lineup["Harga (Juta EUR)"].sum()
                sisa_budget_juta = budget_input_juta - total_pengeluaran_juta
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Efektivitas Rating Skuad", f"{total_rating} OVR")
                m2.metric("Total Investasi Skuad (EUR)", f"€{total_pengeluaran_juta:.2f} M")
                m3.metric("Sisa Alokasi Dana Budget", f"€{sisa_budget_juta:.2f} M")
                
                col_tabel, col_lapangan = st.columns([1, 1.2])
                with col_tabel:
                    st.subheader("📋 Daftar Sebelas Pemain Utama")
                    st.dataframe(df_lineup_display, use_container_width=True, height=440)
                    
                    st.subheader("📊 Statistik Kinerja Pemangkasan Node")
                    st.json(stats)
                    
                with col_lapangan:
                    st.subheader("🏟️ Penempatan Posisi Taktis Lapangan Stadion")
                    gambar_stadium_formasi(lineup_final, formasi_terpilih)
else:
    st.info("💡 Silakan unggah dataset pemain sepak bola berformat .CSV untuk memulai sistem optimasi.")