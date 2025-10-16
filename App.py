import streamlit as st
import pandas as pd
from collections import Counter
import random
import io
from itertools import combinations

st.set_page_config(page_title="Generator Variante Loterie", page_icon="🎰", layout="wide")

st.title("🎰 Generator Variante Loterie 12/66 (4/4, 5/5 etc.)")

st.markdown("""
Analizează frecvența numerelor, elimină cele reci, extrage top numere 
și generează variante unice cu strategii multiple și mărimi flexibile (3/3, 4/4, 5/5).
""")

# --- Session State ---
if "variants" not in st.session_state:
    st.session_state.variants = []
if "top_numbers" not in st.session_state:
    st.session_state.top_numbers = []
if "frequency" not in st.session_state:
    st.session_state.frequency = {}

# --- Secțiunea 1: Încărcare date ---
st.header("📊 1. Încarcă datele extragerilor")

tab1, tab2 = st.tabs(["📁 Import Fișier", "✍️ Manual"])

def proceseaza_runde(lines):
    all_numbers = []
    for line in lines:
        numbers = [int(x.strip()) for x in line.split(",") if x.strip()]
        all_numbers.extend(numbers)
    frequency = Counter(all_numbers)
    sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    st.session_state.frequency = dict(sorted_freq)
    return frequency, sorted_freq, all_numbers

with tab1:
    uploaded_file = st.file_uploader("📂 CSV/TXT cu extragerile din runde", type=["csv", "txt"])
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        frequency, sorted_freq, all_numbers = proceseaza_runde(lines)

        st.success(f"✅ Încărcate {len(lines)} runde cu total {len(all_numbers)} numere")
        rounds_df = pd.DataFrame([[i+1, line] for i, line in enumerate(lines)], columns=["Runda", "Numere"])
        st.dataframe(rounds_df, use_container_width=True, hide_index=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Runde", len(lines))
        col2.metric("Total numere", len(all_numbers))
        col3.metric("Numere unice", len(frequency))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔥 Top 15 cele mai frecvente")
            st.dataframe(pd.DataFrame(sorted_freq[:15], columns=["Număr", "Frecvență"]), use_container_width=True)
        with col2:
            st.subheader("❄️ Bottom 15 cele mai reci")
            st.dataframe(pd.DataFrame(sorted_freq[-15:], columns=["Număr", "Frecvență"]), use_container_width=True)

with tab2:
    st.subheader("✍️ Adaugă rundele manual")
    manual_input = st.text_area(
        "Introduce rundele (o rună pe linie, numere separate cu virgulă)",
        height=300
    )
    if st.button("✅ Procesează rundele"):
        if manual_input.strip():
            lines = [line.strip() for line in manual_input.split("\n") if line.strip()]
            frequency, sorted_freq, all_numbers = proceseaza_runde(lines)
            st.success(f"✅ Procesate {len(lines)} runde cu total {len(all_numbers)} numere")
        else:
            st.warning("⚠️ Te rugăm să adaugi cel puțin o rundă")

# --- Secțiunea 2: Configurare filtre ---
st.header("⚙️ 2. Configurare filtre")

col1, col2 = st.columns(2)

with col1:
    st.subheader("❄️ Exclude cele mai reci numere")
    exclude_mode = st.radio(
        "Cum vrei să excludi?",
        ["🔢 Automata (cele mai reci)", "✍️ Manual (numere specifice)", "🔀 Ambele"],
        horizontal=True
    )
    exclude_numbers = set()
    auto_exclude = set()

    if exclude_mode in ["🔢 Automata (cele mai reci)", "🔀 Ambele"]:
        auto_cold_count = st.selectbox("Exclude topul celor mai reci", [0, 5, 10, 15, 20], index=0)
        if st.session_state.frequency and auto_cold_count > 0:
            sorted_freq = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
            auto_exclude = set([x[0] for x in sorted_freq[-auto_cold_count:]])
            st.info(f"🔴 Auto-exclude ({auto_cold_count}): {sorted(auto_exclude)}")

    if exclude_mode in ["✍️ Manual (numere specifice)", "🔀 Ambele"]:
        manual_exclude_input = st.text_area("Introduce numere de exclus manual (separate cu virgulă)", height=80)
        if manual_exclude_input.strip():
            manual_exclude = set([int(x.strip()) for x in manual_exclude_input.split(",")])
            exclude_numbers.update(manual_exclude)
            st.info(f"✋ Manual exclude: {sorted(manual_exclude)}")

    exclude_numbers.update(auto_exclude)
    if exclude_numbers:
        st.success(f"📌 Total excluse: {len(exclude_numbers)} numere: {sorted(exclude_numbers)}")

with col2:
    st.subheader("🔥 Numere pentru generare (top numere)")
    top_count = st.slider("Câte numere din top?", 10, 66, 50, 1)
    if st.session_state.frequency:
        sorted_freq = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
        top_numbers = [x[0] for x in sorted_freq[:top_count] if x[0] not in exclude_numbers]
        st.session_state.top_numbers = top_numbers
        st.success(f"✅ {len(top_numbers)} numere disponibile")

# --- Secțiunea 3: Strategii de generare ---
st.header("🎲 3. Strategii de generare")

col1, col2 = st.columns(2)

with col1:
    variant_size = st.selectbox(
        "Alege mărimea variantei (ex: 4/4, 5/5, 3/3)",
        [3, 4, 5],
        index=1,
        help="Selectează câte numere vrei în fiecare variantă"
    )

with col2:
    strategy = st.selectbox(
        "Alege strategia:",
        [
            "🎯 Standard (numere aleatoare)",
            "🔥 Hot Numbers (3 din top 10 + rest aleatoriu)",
            "❄️ Cold-Hot Hybrid (jumătate top, jumătate rest)",
            "🔥❄️ Premium Hybrid (3 din top 25 + rest)",
            "🌀 Random Pairs (perechi aleatoare)",
            "⚡ Frecvență Ponderată (proporțional cu frecvența)",
            "🎪 Mix Strategy (combinație din toate)",
            "🚀 Hybrid Ultra Sonic (2 din top 35 + 2 din 19-66)",
            "💎 Top34 + 1 Rest (3 din top34 + 1 rest)"
        ]
    )

num_variants = st.number_input("Câte variante?", 100, 5000, 1000, 100)

if st.button("🚀 Generează variante"):
    if not st.session_state.top_numbers:
        st.error("❌ Încarcă datele și configurează filtrele")
    else:
        top_nums = st.session_state.top_numbers
        variants = set()
        max_attempts = num_variants * 50
        attempts = 0

        while len(variants) < num_variants and attempts < max_attempts:
            attempts += 1
            random.shuffle(top_nums)

            if strategy == "🎯 Standard (numere aleatoare)":
                variant = random.sample(top_nums, variant_size)

            elif strategy == "🔥 Hot Numbers (3 din top 10 + rest aleatoriu)":
                top10 = top_nums[:10]; rest = top_nums[10:]
                variant = random.sample(top10, min(3, variant_size)) + random.sample(rest, max(variant_size-3, 0))

            elif strategy == "❄️ Cold-Hot Hybrid (jumătate top, jumătate rest)":
                half = variant_size // 2
                top20 = top_nums[:20]; rest = top_nums[20:]
                variant = random.sample(top20, min(half, len(top20))) + random.sample(rest, variant_size - half)

            elif strategy == "🔥❄️ Premium Hybrid (3 din top 25 + rest)":
                top25 = top_nums[:25]; rest = top_nums[25:]
                variant = random.sample(top25, min(3, variant_size)) + random.sample(rest, max(variant_size-3, 0))

            elif strategy == "🌀 Random Pairs (perechi aleatoare)":
                variant = random.sample(top_nums, variant_size)

            elif strategy == "⚡ Frecvență Ponderată (proporțional cu frecvența)":
                weights = [st.session_state.frequency.get(n, 1) for n in top_nums]
                variant = random.choices(top_nums, weights=weights, k=variant_size)

            elif strategy == "🚀 Hybrid Ultra Sonic (2 din top 35 + 2 din 19-66)":
                top35 = top_nums[:35]; rest = top_nums[18:]
                variant = random.sample(top35, min(2, variant_size)) + random.sample(rest, variant_size - 2)

            elif strategy == "💎 Top34 + 1 Rest (3 din top34 + 1 rest)":
                top34 = top_nums[:34]; rest = top_nums[34:]
                variant = random.sample(top34, min(3, variant_size)) + random.sample(rest, max(variant_size-3, 0))

            else:  # Mix Strategy
                choice = random.randint(1, 5)
                if choice == 1:
                    variant = random.sample(top_nums, variant_size)
                elif choice == 2:
                    top10 = top_nums[:10]; rest = top_nums[10:]
                    variant = random.sample(top10, 3) + random.sample(rest, variant_size - 3)
                elif choice == 3:
                    top20 = top_nums[:20]; rest = top_nums[20:]
                    variant = random.sample(top20, 2) + random.sample(rest, variant_size - 2)
                else:
                    top25 = top_nums[:25]; rest = top_nums[25:]
                    variant = random.sample(top25, 3) + random.sample(rest, variant_size - 3)

            # 🔀 Amestec complet aleatoriu
            random.shuffle(variant)
            variants.add(tuple(variant))

        st.session_state.variants = sorted(list(variants))
        st.success(f"✅ Generate {len(st.session_state.variants)} variante unice ({variant_size}/{variant_size}) în {attempts} încercări")

# --- Secțiunea 4: Preview & Export ---
if st.session_state.variants:
    st.header("📋 4. Preview și Export")
    preview_count = st.slider("Câte variante să afișez?", 5, 50, 20)
    preview_df = pd.DataFrame(
        [[i+1, " ".join(map(str, v))] for i, v in enumerate(st.session_state.variants[:preview_count])],
        columns=["ID", "Combinație"]
    )
    st.dataframe(preview_df, use_container_width=True, hide_index=True)

    txt_output = "\n".join([f"{i+1}, {' '.join(map(str, v))}" for i, v in enumerate(st.session_state.variants)])
    st.download_button("⬇️ Descarcă variante (TXT)", txt_output, "variante.txt", "text/plain")
