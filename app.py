# app.py
# =========================================================
# WEB APP OPTIMASI STARTING XI
# Menggunakan Branch and Bound + Streamlit
# =========================================================


import streamlit as st
import pandas as pd
import heapq
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import matplotlib.patches as patches


st.set_page_config(
    page_title="Optimasi Starting XI",
    page_icon="⚽",
    layout="wide"
)

# =========================================================
# FORMASI
# =========================================================

FORMASI_TERSEDIA = {
    "4-3-3": {"GK":1,"CB":2,"LB":1,"RB":1,"CM":2,"CDM":1,"LW":1,"RW":1,"ST":1},
    "4-4-2": {"GK":1,"CB":2,"LB":1,"RB":1,"CM":3,"CDM":1,"ST":2},
    "4-2-3-1": {"GK":1,"CB":2,"LB":1,"RB":1,"CDM":2,"CAM":2,"LW":1,"ST":1},
    "3-5-2": {"GK":1,"CB":3,"CDM":1,"CM":2,"CAM":1,"RB":1,"ST":2},
}

KOMPATIBILITAS = {
    "GK": ["GK"],
    "CB": ["CB"],
    "LB": ["LB","RB"],
    "RB": ["RB","LB"],
    "CDM": ["CDM","CM"],
    "CM": ["CM","CDM","CAM"],
    "CAM": ["CAM","CM"],
    "LW": ["LW","LB"],
    "RW": ["RW","RB"],
    "ST": ["ST"],
}

# =========================================================
# BANGUN SLOT
# =========================================================

def bangun_kandidat_per_slot(df, formasi):
    slots = []

    for posisi, jumlah in formasi.items():
        posisi_ok = KOMPATIBILITAS.get(posisi, [posisi])

        kandidat = df[df["Position"].isin(posisi_ok)].copy()

        kandidat = kandidat.sort_values(
            "Overall",
            ascending=False
        ).reset_index(drop=True)

        for _ in range(jumlah):
            slots.append((posisi, kandidat))

    return slots

# =========================================================
# UPPER BOUND
# =========================================================

def hitung_upper_bound(level, rating_kini, sisa_budget, slots, terpakai):

    ub = rating_kini
    budget_temp = sisa_budget

    for i in range(level, len(slots)):

        _, kandidat = slots[i]

        tersedia = kandidat[
            ~kandidat["Name"].isin(terpakai)
        ]

        if tersedia.empty:
            return float("inf")

        best = tersedia.iloc[0]

        harga = best["Value_EUR"]
        rating = best["Overall"]

        if harga <= budget_temp:
            ub += rating
            budget_temp -= harga
        else:
            if harga > 0:
                ub += rating * (budget_temp / harga)
            break

    return ub

# =========================================================
# NODE
# =========================================================

@dataclass(order=True)
class Node:

    neg_ub: float

    level: int = field(compare=False)
    rating: float = field(compare=False)
    budget: float = field(compare=False)
    dipilih: list = field(compare=False)
    terpakai: frozenset = field(compare=False)

# =========================================================
# BRANCH AND BOUND
# =========================================================

def branch_and_bound(df, formasi, budget):

    slots = bangun_kandidat_per_slot(df, formasi)

    n_slots = len(slots)

    best_rating = -1
    best_lineup = []

    nodes_explored = 0
    nodes_pruned = 0

    ub_root = hitung_upper_bound(
        0,
        0,
        budget,
        slots,
        frozenset()
    )

    root = Node(
        neg_ub=-ub_root,
        level=0,
        rating=0,
        budget=budget,
        dipilih=[],
        terpakai=frozenset()
    )

    pq = [root]

    while pq:

        node = heapq.heappop(pq)

        nodes_explored += 1

        if -node.neg_ub <= best_rating:
            nodes_pruned += 1
            continue

        if node.level == n_slots:

            if node.rating > best_rating:
                best_rating = node.rating
                best_lineup = node.dipilih[:]

            continue

        posisi_slot, kandidat = slots[node.level]

        tersedia = kandidat[
            ~kandidat["Name"].isin(node.terpakai)
        ]

        for _, baris in tersedia.iterrows():

            nama = baris["Name"]
            harga = baris["Value_EUR"]
            rating = baris["Overall"]

            if harga > node.budget:
                nodes_pruned += 1
                continue

            new_terpakai = node.terpakai | {nama}

            new_rating = node.rating + rating

            new_budget = node.budget - harga

            new_dipilih = node.dipilih + [
                (posisi_slot, nama, rating, harga)
            ]

            ub = hitung_upper_bound(
                node.level + 1,
                new_rating,
                new_budget,
                slots,
                new_terpakai
            )

            if ub <= best_rating:
                nodes_pruned += 1
                continue

            child = Node(
                neg_ub=-ub,
                level=node.level + 1,
                rating=new_rating,
                budget=new_budget,
                dipilih=new_dipilih,
                terpakai=new_terpakai
            )

            heapq.heappush(pq, child)

    statistik = {
        "nodes_explored": nodes_explored,
        "nodes_pruned": nodes_pruned
    }

    return best_rating, best_lineup, statistik

# =========================================================
# VISUALISASI FORMASI MODERN
# =========================================================

def gambar_formasi(best_lineup, formasi_nama):

    fig, ax = plt.subplots(figsize=(12, 8))

    # Background figure
    fig.patch.set_facecolor("#0b1220")

    # Background lapangan
    ax.set_facecolor("#1b8f3a")

    # Pola rumput stadion
    for y in range(0, 100, 10):

        warna = "#1b8f3a" if y % 20 == 0 else "#239b45"

        ax.axhspan(
            y,
            y + 10,
            facecolor=warna,
            alpha=0.9
        )

    # =====================================================
    # GARIS LAPANGAN
    # =====================================================

    ax.plot([0,0],[0,100], color="white", linewidth=2)
    ax.plot([100,100],[0,100], color="white", linewidth=2)
    ax.plot([0,100],[0,0], color="white", linewidth=2)
    ax.plot([0,100],[100,100], color="white", linewidth=2)

    # Tengah
    ax.plot([0,100],[50,50], color="white", linewidth=2)

    center_circle = plt.Circle(
        (50,50),
        10,
        color="white",
        fill=False,
        linewidth=2
    )

    ax.add_patch(center_circle)

    ax.scatter(50, 50, color="white", s=30)

    # Penalti atas
    ax.add_patch(
        patches.Rectangle(
            (30,83),
            40,
            17,
            fill=False,
            edgecolor="white",
            linewidth=2
        )
    )

    # Penalti bawah
    ax.add_patch(
        patches.Rectangle(
            (30,0),
            40,
            17,
            fill=False,
            edgecolor="white",
            linewidth=2
        )
    )

    # Gawang atas
    ax.add_patch(
        patches.Rectangle(
            (42,96),
            16,
            4,
            fill=False,
            edgecolor="white",
            linewidth=2
        )
    )

    # Gawang bawah
    ax.add_patch(
        patches.Rectangle(
            (42,0),
            16,
            4,
            fill=False,
            edgecolor="white",
            linewidth=2
        )
    )

    # =====================================================
    # POSISI BERDASARKAN FORMASI
    # =====================================================

    FORMASI_POSISI = {

        "4-3-3": {

            "GK": [(50,8)],

            "LB": [(18,25)],
            "CB": [(40,22), (60,22)],
            "RB": [(82,25)],

            "CDM": [(50,40)],

            "CM": [(35,50), (65,50)],

            "LW": [(22,78)],
            "RW": [(78,78)],

            "ST": [(50,92)]
        },

        "4-4-2": {

            "GK": [(50,8)],

            "LB": [(18,25)],
            "CB": [(40,22), (60,22)],
            "RB": [(82,25)],

            "CM": [(32,50), (68,50)],
            "CDM": [(50,42)],

            "LW": [(20,62)],
            "RW": [(80,62)],

            "ST": [(40,88), (60,88)]
        },

        "4-2-3-1": {

            "GK": [(50,8)],

            "LB": [(18,25)],
            "CB": [(40,22), (60,22)],
            "RB": [(82,25)],

            "CDM": [(40,42), (60,42)],

            "CAM": [(50,62)],

            "LW": [(22,74)],
            "RW": [(78,74)],

            "ST": [(50,90)]
        },

        "3-5-2": {

            "GK": [(50,8)],

            "CB": [(30,22), (50,22), (70,22)],

            "RB": [(82,45)],

            "CDM": [(50,40)],

            "CM": [(35,55), (65,55)],

            "CAM": [(50,68)],

            "ST": [(40,88), (60,88)]
        }
    }

    posisi_map = FORMASI_POSISI.get(formasi_nama, {})

    # =====================================================
    # WARNA POSISI
    # =====================================================

    warna_posisi = {

        "GK":"#00c3ff",

        "CB":"#1e90ff",

        "LB":"#ff3b3b",

        "RB":"#9b59b6",

        "CDM":"#f39c12",

        "CM":"#2ecc71",

        "CAM":"#f1c40f",

        "LW":"#e67e22",

        "RW":"#95a5a6",

        "ST":"#ff4757"
    }

    counter = {}

    for slot, nama, rating, harga in best_lineup:

        idx = counter.get(slot, 0)

        posisi_list = posisi_map.get(slot, [(50,50)])

        x, y = posisi_list[
            min(idx, len(posisi_list)-1)
        ]

        warna = warna_posisi.get(slot, "white")

        # Shadow
        ax.scatter(
            x,
            y,
            s=3200,
            color="black",
            alpha=0.25,
            zorder=1
        )

        # Circle pemain
        ax.scatter(
            x,
            y,
            s=2600,
            color=warna,
            edgecolors="white",
            linewidths=2.5,
            zorder=2
        )

        nama_pendek = nama.split()[-1]

        # Nama pemain
        ax.text(
            x,
            y + 2,
            nama_pendek,
            ha="center",
            va="center",
            fontsize=11,
            color="white",
            weight="bold",
            zorder=3
        )

        # Rating
        ax.text(
            x,
            y - 2,
            f"{rating}",
            ha="center",
            va="center",
            fontsize=14,
            color="white",
            weight="bold",
            zorder=3
        )

        # Posisi
        ax.text(
            x,
            y - 7,
            slot,
            ha="center",
            va="center",
            fontsize=8,
            color="white",
            zorder=3
        )

        counter[slot] = idx + 1

    # =====================================================
    # FINAL DISPLAY
    # =====================================================

    ax.set_xlim(0,100)
    ax.set_ylim(0,100)

    ax.axis("off")

    st.pyplot(fig)

# =========================================================
# UI
# =========================================================

st.title("⚽ Optimasi Starting XI")
st.markdown("### Branch and Bound Algorithm")

uploaded_file = st.file_uploader(
    "Upload Dataset CSV",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.subheader("📋 Dataset Pemain")

    st.dataframe(df)

    st.sidebar.header("⚙ Pengaturan")

    formasi_nama = st.sidebar.selectbox(
        "Pilih Formasi",
        list(FORMASI_TERSEDIA.keys())
    )

    budget_juta = st.sidebar.number_input(
        "Budget (Juta Euro)",
        min_value=1,
        value=1000
    )

    budget = budget_juta * 1_000_000

    if st.button("🚀 Cari Starting XI Optimal"):

        with st.spinner("Menjalankan Branch and Bound..."):

            best_rating, best_lineup, statistik = branch_and_bound(
                df,
                FORMASI_TERSEDIA[formasi_nama],
                budget
            )

        if not best_lineup:

            st.error("Tidak ditemukan solusi.")

        else:

            st.success("Optimasi selesai!")

            hasil_df = pd.DataFrame(
                best_lineup,
                columns=[
                    "Slot",
                    "Nama",
                    "Rating",
                    "Harga"
                ]
            )

            hasil_df["Harga"] = hasil_df["Harga"] / 1_000_000

            st.subheader("🏆 Starting XI Optimal")

            st.dataframe(hasil_df)

            total_harga = hasil_df["Harga"].sum()

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Total Rating",
                int(best_rating)
            )

            col2.metric(
                "Total Harga",
                f"€{total_harga:.1f}M"
            )

            col3.metric(
                "Sisa Budget",
                f"€{budget_juta-total_harga:.1f}M"
            )

            st.subheader("📊 Statistik Branch and Bound")

            st.write(statistik)

            st.subheader("🏟 Visualisasi Formasi")

            gambar_formasi(best_lineup, formasi_nama)