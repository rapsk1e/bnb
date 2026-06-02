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
    slots_kandidat = []
    
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
        
        list_pemain_kompatibel.sort(key=lambda x: x.rating_efektif, reverse=True)
        
        for _ in range(jumlah_slot):
            slots_kandidat.append((posisi_taktis, list_pemain_kompatibel))
            
    return slots_kandidat

def hitung_estimasi_range_budget(slots: List[Tuple[str, List[KandidatPemain]]]) -> Tuple[float, float]:
    min_total = 0.0
    max_total = 0.0
    set_terpakai_min = set()
    set_terpakai_max = set()
    
    for _, kandidat_list in slots:
        kandidat_urut_murah = sorted(kandidat_list, key=lambda x: x.harga)
        terpilih = False
        for p in kandidat_urut_murah:
            if p.nama not in set_terpakai_min:
                min_total += p.harga
                set_terpakai_min.add(p.nama)
                terpilih = True
                break
        if not terpilih and kandidat_list:
            min_total += kandidat_list[-1].harga

    for _, kandidat_list in slots:
        kandidat_urut_mahal = sorted(kandidat_list, key=lambda x: x.harga, reverse=True)
        terpilih = False
        for p in kandidat_urut_mahal:
            if p.nama not in set_terpakai_max:
                max_total += p.harga
                set_terpakai_max.add(p.nama)
                terpilih = True
                break
        if not terpilih and kandidat_list:
            max_total += kandidat_list[0].harga
            
    return min_total, max_total


# ==============================================================================
# 3. ALGORITMA BRANCH AND BOUND (TEROPTIMASI + LOGGING TREE)
# ==============================================================================

@dataclass(order=True)
class NodeBB:
    neg_ub: float
    level: int = field(compare=False)
    rating_akumulasi: int = field(compare=False)
    budget_sisa: float = field(compare=False)
    tim_dipilih: list = field(compare=False)
    set_nama_terpakai: frozenset = field(compare=False)
    node_id: int = field(default=0, compare=False)
    parent_id: int = field(default=-1, compare=False)
    nama_cabang: str = field(default="Root", compare=False)

def hitung_upper_bound(level: int, rating_kini: int, sisa_budget: float, 
                       slots: List[Tuple[str, List[KandidatPemain]]], 
                       set_terpakai: frozenset) -> float:
    ub = float(rating_kini)
    budget_temp = sisa_budget
    
    for i in range(level, len(slots)):
        _, kandidat_list = slots[i]
        pemain_terpilih = None
        
        for p in kandidat_list:
            if p.nama not in set_terpakai:
                pemain_terpilih = p
                break
                
        if not pemain_terpilih:
            return float('-inf')
            
        if pemain_terpilih.harga <= budget_temp:
            ub += pemain_terpilih.rating_efektif
            budget_temp -= pemain_terpilih.harga
        else:
            if pemain_terpilih.harga > 0:
                ub += pemain_terpilih.rating_efektif * (budget_temp / pemain_terpilih.harga)
            break
            
    return ub

def run_branch_and_bound(slots: List[Tuple[str, List[KandidatPemain]]], budget_total: float, max_tree_nodes: int = 25) -> Tuple[int, List[Dict], Dict, List[Dict]]:
    n_slots = len(slots)
    best_rating = -1
    best_lineup: List[Dict] = []
    
    nodes_explored = 0
    nodes_pruned = 0
    node_counter = 0
    waktu_mulai = time.time()
    
    # List untuk menampung struktur data pohon untuk visualisasi Graphviz
    tree_log: List[Dict] = []
    
    ub_root = hitung_upper_bound(0, 0, budget_total, slots, frozenset())
    if ub_root == float('-inf'):
        return 0, [], {"error": "Jumlah skuad dalam dataset kurang."}, []
        
    root = NodeBB(
        neg_ub=-ub_root,
        level=0,
        rating_akumulasi=0,
        budget_sisa=budget_total,
        tim_dipilih=[],
        set_nama_terpakai=frozenset(),
        node_id=node_counter,
        parent_id=-1,
        nama_cabang="Start"
    )
    
    priority_queue = [root]
    
    # Log node akar ke tree visualizer
    if len(tree_log) < max_tree_nodes:
        tree_log.append({
            "id": root.node_id, "parent": root.parent_id, "label": root.nama_cabang,
            "ub": ub_root, "status": "Explored", "level": root.level
        })
    
    while priority_queue:
        node_aktif = heapq.heappop(priority_queue)
        nodes_explored += 1
        
        # Cari node ini di log dan perbarui statusnya jika dia dieksplorasi penuh
        for node_data in tree_log:
            if node_data["id"] == node_aktif.node_id:
                node_data["status"] = "Explored"
        
        if -node_aktif.neg_ub <= best_rating:
            nodes_pruned += 1
            for node_data in tree_log:
                if node_data["id"] == node_aktif.node_id:
                    node_data["status"] = "Pruned (UB)"
            continue
            
        if node_aktif.level == n_slots:
            if node_aktif.rating_akumulasi > best_rating:
                best_rating = node_aktif.rating_akumulasi
                best_lineup = node_aktif.tim_dipilih
                for node_data in tree_log:
                    if node_data["id"] == node_aktif.node_id:
                        node_data["status"] = "Best Sol"
            continue
            
        posisi_slot, kandidat_list = slots[node_aktif.level]
        
        count_branch = 0
        for p in kandidat_list:
            if p.nama in node_aktif.set_nama_terpakai:
                continue
                
            node_counter += 1
            nama_singkat_pemain = p.nama.split()[-1] if len(p.nama.split()) > 0 else p.nama
            label_cabang = f"{posisi_slot}\n{nama_singkat_pemain}"
            
            if p.harga > node_aktif.budget_sisa:
                nodes_pruned += 1
                if len(tree_log) < max_tree_nodes:
                    tree_log.append({
                        "id": node_counter, "parent": node_aktif.node_id, "label": label_cabang,
                        "ub": 0, "status": "Pruned (Budget)", "level": node_aktif.level + 1
                    })
                continue
                
            count_branch += 1
            if count_branch > 15: # Batasi branching factor agar bnb tidak meledak
                break
                
            next_set_terpakai = node_aktif.set_nama_terpakai | {p.nama}
            next_rating = node_aktif.rating_akumulasi + p.rating_efektif
            next_budget = node_aktif.budget_sisa - p.harga
            
            detail_pemain = {
                "Slot": posisi_slot, "Nama": p.nama, "Posisi Asli": p.posisi_asli,
                "Rating Efektif": p.rating_efektif, "Harga EUR": p.harga
            }
            next_lineup = node_aktif.tim_dipilih + [detail_pemain]
            
            ub_child = hitung_upper_bound(node_aktif.level + 1, next_rating, next_budget, slots, next_set_terpakai)
            
            if ub_child <= best_rating:
                nodes_pruned += 1
                if len(tree_log) < max_tree_nodes:
                    tree_log.append({
                        "id": node_counter, "parent": node_aktif.node_id, "label": label_cabang,
                        "ub": ub_child, "status": "Pruned (UB)", "level": node_aktif.level + 1
                    })
                continue
                
            child_node = NodeBB(
                neg_ub=-ub_child, level=node_aktif.level + 1, rating_akumulasi=next_rating,
                budget_sisa=next_budget, tim_dipilih=next_lineup, set_nama_terpakai=next_set_terpakai,
                node_id=node_counter, parent_id=node_aktif.node_id, nama_cabang=label_cabang
            )
            
            if len(tree_log) < max_tree_nodes:
                tree_log.append({
                    "id": child_node.node_id, "parent": child_node.parent_id, "label": child_node.nama_cabang,
                    "ub": ub_child, "status": "In Queue", "level": child_node.level
                })
                
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
    
    return best_rating, best_lineup, statistik, tree_log


def buat_grafik_graphviz(tree_log: List[Dict]) -> str:
    """Mengubah log bnb node menjadi string DOT format untuk dibaca Graphviz."""
    dot = "digraph G {\n"
    dot += "  bgcolor=\"#0f172a\";\n"
    dot += "  edge [color=\"#94a3b8\", arrowhead=vee, arrowsize=0.6];\n"
    dot += "  node [fontname=\"sans-serif\", fontsize=10, shape=box, style=\"filled,rounded\", width=1.2, height=0.6];\n"
    
    for node in tree_log:
        lbl = f"{node['label']}\nUB: {node['ub']:.1f}" if node['ub'] > 0 else node['label']
        
        # Pewarnaan dinamis berdasarkan status pruning/eksplorasi
        if node["status"] == "Explored":
            fillcolor = "#1e3a8a" # Biru Tua
            fontcolor = "#ffffff"
        elif node["status"] == "Best Sol":
            fillcolor = "#16a34a" # Hijau Sukses
            fontcolor = "#ffffff"
        elif "Pruned (UB)" in node["status"]:
            fillcolor = "#7f1d1d" # Merah Marun (Pruned rating jelek)
            fontcolor = "#fca5a5"
        elif "Pruned (Budget)" in node["status"]:
            fillcolor = "#b45309" # Jingga Tua (Pruned overbudget)
            fontcolor = "#fef3c7"
        else:
            fillcolor = "#334155" # Abu-abu antrean
            fontcolor = "#cbd5e1"
            
        dot += f'  {node["id"]} [label="{lbl}", fillcolor="{fillcolor}", fontcolor="{fontcolor}", color=\"#ffffff\", linewidth=0.5];\n'
        
        if node["parent"] != -1:
            dot += f'  {node["parent"]} -> {node["id"]};\n'
            
    dot += "}"
    return dot


# ==============================================================================
# 4. ENGINE VISUALISASI LAPANGAN SEPAKBOLA
# ==============================================================================

def gambar_stadium_formasi(best_lineup: List[Dict], nama_formasi: str):
    fig, ax = plt.subplots(figsize=(11, 8.5))
    fig.patch.set_facecolor("#0f172a") 
    ax.set_facecolor("#15803d")        
    
    for y_strip in range(0, 100, 10):
        warna_rumput = "#166534" if (y_strip // 10) % 2 == 0 else "#15803d"
        ax.axhspan(y_strip, y_strip + 10, facecolor=warna_rumput, alpha=1.0, zorder=0)
        
    ax.plot([0, 100, 100, 0, 0], [0, 0, 100, 100, 0], color="#f8fafc", linewidth=2.5, zorder=1)
    ax.plot([0, 100], [50, 50], color="#f8fafc", linewidth=2.5, zorder=1)
    
    lingkaran_tengah = plt.Circle((50, 50), 12, color="#f8fafc", fill=False, linewidth=2.5, zorder=1)
    ax.add_patch(lingkaran_tengah)
    ax.scatter(50, 50, color="#f8fafc", s=40, zorder=2)
    
    ax.add_patch(patches.Rectangle((20, 80), 60, 20, fill=False, edgecolor="#f8fafc", linewidth=2.5, zorder=1))
    ax.add_patch(patches.Rectangle((35, 92), 30, 8, fill=False, edgecolor="#f8fafc", linewidth=1.5, zorder=1))
    ax.add_patch(patches.Rectangle((20, 0), 60, 20, fill=False, edgecolor="#f8fafc", linewidth=2.5, zorder=1))
    ax.add_patch(patches.Rectangle((35, 0), 30, 8, fill=False, edgecolor="#f8fafc", linewidth=1.5, zorder=1))
    
    skema_warna: Dict[str, str] = {
        "GK": "#38bdf8", "LB": "#fb7185", "CB": "#60a5fa", "RB": "#c084fc",
        "CDM": "#f59e0b", "CM": "#4ade80", "CAM": "#a3e635", "LW": "#f43f5e",
        "RW": "#e2e8f0", "ST": "#f43f5e"
    }
    
    peta_koordinat = FORMASI_POSISI[nama_formasi]
    indeks_counter: Dict[str, int] = {}
    
    for pemain in best_lineup:
        pos = pemain["Slot"]
        idx = indeks_counter.get(pos, 0)
        indeks_counter[pos] = idx + 1
        
        if pos in peta_koordinat and idx < len(peta_koordinat[pos]):
            x, y = peta_koordinat[pos][idx]
        else:
            x, y = 50.0, 50.0
            
        warna_node = skema_warna.get(pos, "#94a3b8")
        ax.scatter(x, y - 1.2, s=2100, color="#020617", alpha=0.4, zorder=2)
        ax.scatter(x, y, s=1800, color=warna_node, edgecolors="#ffffff", linewidths=2.5, zorder=3)
        
        nama_pendek = pemain["Nama"].split()[-1] if len(pemain["Nama"].split()) > 0 else pemain["Nama"]
        if len(nama_pendek) > 10:
            nama_pendek = nama_pendek[:9] + ".."
            
        ax.text(x, y + 1.8, nama_pendek, ha="center", va="center", fontsize=10, color="#ffffff", weight="bold", zorder=4)
        ax.text(x, y - 1.0, f"OVR {pemain['Rating Efektif']}", ha="center", va="center", fontsize=11, color="#0f172a", weight="black", zorder=4)
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
formasi_terpilih = st.sidebar.selectbox("Pilih Pola Formasi Taktis Utama:", list(FORMASI_TERSEDIA.keys()))

uploaded_file = st.file_uploader("Unggah File Dataset Pemain (.CSV):", type=["csv"])

if uploaded_file:
    df_pemain = pd.read_csv(uploaded_file)
    
    st.subheader("📊 Analisis Kelayakan & Rentang Budget Dataset Semesta Formasi")
    
    ringkasan_formasi = []
    for f_nama, f_obj in FORMASI_TERSEDIA.items():
        slots_temp = bangun_kandidat_per_slot(df_pemain, f_obj)
        
        is_aman = True
        for pos_req, kuota in f_obj.items():
            pos_alternatif = [p_asli for p_asli, _ in ATURAN_KOMPATIBILITAS.get(pos_req, [(pos_req, 0)])]
            tersedia = df_pemain[df_pemain["Position"].isin(pos_alternatif)].shape[0]
            if tersedia < kuota:
                is_aman = False
                break
                
        if is_aman and len(slots_temp) == 11:
            min_b, max_b = hitung_estimasi_range_budget(slots_temp)
            status_pemain = "✅ Cukup Pemain"
        else:
            min_b, max_b = 0.0, 0.0
            status_pemain = "❌ Kurang Pemain"
            
        ringkasan_formasi.append({
            "Formasi": f_nama,
            "Min Budget (Juta EUR)": round(min_b / 1_000_000, 2) if min_b > 0 else "N/A",
            "Max Budget (Juta EUR)": round(max_b / 1_000_000, 2) if max_b > 0 else "N/A",
            "Ketersediaan Skuad": status_pemain,
            "Kelayakan B&B": "🚀 Siap Dioptimasi" if is_aman else "🛑 Data Tidak Mendukung"
        })
        
    df_ringkasan = pd.DataFrame(ringkasan_formasi)
    st.dataframe(df_ringkasan, use_container_width=True, hide_index=True)
    st.caption("ℹ️ *Min Budget menunjukkan ongkos minimum membangun tim isi 11 pemain unik yang valid, sedangkan Max Budget adalah total harga jika Anda memborong semua opsi pemain termahal.*")
    
    formasi_obj = FORMASI_TERSEDIA[formasi_terpilih]
    slots_kandidat = bangun_kandidat_per_slot(df_pemain, formasi_obj)
    
    if len(slots_kandidat) == 11:
        min_budget_eur, max_budget_eur = hitung_estimasi_range_budget(slots_kandidat)
        min_budget_juta = min_budget_eur / 1_000_000
        max_budget_juta = max_budget_eur / 1_000_000
        
        st.sidebar.info(
            f"🎯 **Formasi Aktif: {formasi_terpilih}**\n"
            f"- 🛑 Min Budget: €{min_budget_juta:.2f} M\n"
            f"- 🚀 Max Budget: €{max_budget_juta:.2f} M"
        )
    else:
        min_budget_juta = 1.0
        max_budget_juta = 2000.0

    budget_input_juta = st.sidebar.number_input(
        "Batas Maksimal Anggaran Budget Anda (Juta EUR):", 
        min_value=1.0, max_value=5000.0, value=max(min_budget_juta, 150.0), step=10.0
    )
    budget_aktual_eur = budget_input_juta * 1_000_000

    st.markdown("---")
    col_preview, col_config_check = st.columns([1.8, 1.2])
    with col_preview:
        st.subheader("📋 Sampel Dataset Pemain")
        st.dataframe(df_pemain.head(6), use_container_width=True)
        
    with col_config_check:
        st.subheader(f"🔍 Status Kompatibilitas Formasi {formasi_terpilih}")
        is_data_aman = True
        status_list = []
        for pos_req, kuota in formasi_obj.items():
            pos_alternatif = [p_asli for p_asli, _ in ATURAN_KOMPATIBILITAS.get(pos_req, [(pos_req, 0)])]
            tersedia_di_csv = df_pemain[df_pemain["Position"].isin(pos_alternatif)].shape[0]
            if tersedia_di_csv < kuota:
                status_list.append(f"❌ **{pos_req}**: Butuh {kuota}, hanya ada {tersedia_di_csv}")
                is_data_aman = False
            else:
                status_list.append(f"✅ **{pos_req}**: Terpenuhi ({tersedia_di_csv} pemain)")
                
        st.markdown("\n".join(status_list))
        
    if not is_data_aman:
        st.error(f"Gagal Melanjutkan: Dataset Anda tidak memiliki cukup pemain untuk formasi {formasi_terpilih}.")
    else:
        if budget_input_juta < min_budget_juta:
            st.warning(f"⚠️ Budget Anda (€{budget_input_juta:.2f}M) di bawah batas minimum teoretis (€{min_budget_juta:.2f}M) untuk formasi ini. B&B dipastikan mengembalikan hasil nihil.")
        elif budget_input_juta >= max_budget_juta:
            st.success(f"⚡ Budget Anda (€{budget_input_juta:.2f}M) melampaui harga skuad termahal. Algoritma otomatis mengambil pemain rating tertinggi!")

        if st.button("🚀 Jalankan Optimasi Pencarian Starting XI Terbaik"):
            with st.spinner("Algoritma sedang mengeksplorasi pohon ruang status (Branch and Bound)..."):
                total_rating, lineup_final, stats, bnb_tree_data = run_branch_and_bound(slots_kandidat, budget_aktual_eur, max_tree_nodes=30)
                
            if "error" in stats:
                st.error(stats["error"])
            elif not lineup_final:
                st.error(f"Solusi Tidak Ditemukan! Batas Anggaran €{budget_input_juta:.2f}M terlalu rendah.")
            else:
                st.success("Solusi Optimal Berhasil Diekstrak!")
                
                df_lineup = pd.DataFrame(lineup_final)
                df_lineup["Harga (Juta EUR)"] = df_lineup["Harga EUR"] / 1_000_000
                df_lineup_display = df_lineup[["Slot", "Nama", "Posisi Asli", "Rating Efektif", "Harga (Juta EUR)"]]
                
                total_pengeluaran_juta = df_lineup["Harga (Juta EUR)"].sum()
                sisa_budget_juta = budget_input_juta - total_pengeluaran_juta
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Efektivitas Rating Skuad", f"{total_rating} OVR")
                m2.metric("Total Investasi Skuad (EUR)", f"€{total_pengeluaran_juta:.2f} M")
                m3.metric("Sisa Alokasi Dana Budget", f"€{sisa_budget_juta:.2f} M")
                
                st.markdown("---")
                
                # --- STRATEGI TAB UNTUK MEMISAHKAN VISUALISASI AGAR RAPI ---
                tab_lapangan, tab_tabel, tab_pohon = st.tabs([
                    "🏟️ Penempatan Lapangan", 
                    "📋 Daftar Pemain Utama", 
                    "🌳 Pohon Keputusan Branch & Bound"
                ])
                
                with tab_lapangan:
                    st.subheader("🏟️ Penempatan Posisi Taktis Lapangan Stadion")
                    gambar_stadium_formasi(lineup_final, formasi_terpilih)
                    
                with tab_tabel:
                    col_l, col_r = st.columns([1.2, 0.8])
                    with col_l:
                        st.subheader("📋 Daftar Sebelas Pemain Utama")
                        st.dataframe(df_lineup_display, use_container_width=True, height=440)
                    with col_r:
                        st.subheader("📊 Statistik Kinerja Pemangkasan Node")
                        st.json(stats)
                        
                with tab_pohon:
                    st.subheader("🌳 Struktur Pemangkasan Node Pohon Status (30 Node Pertama)")
                    st.markdown("""
                    **Legenda Warna Node:**
                    * 🔵 **Biru**: Node yang dieksplorasi penuh (*Explored*)
                    * 🟢 **Hijau**: Node yang menghasilkan Solusi Terbaik Sementara (*Best Solution*)
                    * 🔴 **Merah**: Cabang dipangkas karena tak akan melampaui rating terbaik (*Pruned by Bound*)
                    * 🟤 **Cokelat**: Cabang dipangkas karena melampaui sisa budget (*Pruned by Budget*)
                    * ⚪ **Abu-abu**: Node mengantre di dalam *Priority Queue*
                    """)
                    
                    # Bangun dan render graphviz string
                    dot_string = buat_grafik_graphviz(bnb_tree_data)
                    st.graphviz_chart(dot_string, use_container_width=True)
else:
    st.info("💡 Silakan unggah dataset pemain sepak bola berformat .CSV")