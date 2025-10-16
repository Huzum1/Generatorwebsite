import streamlit as st
import pandas as pd
from collections import Counter
import random
import io

st.set_page_config(page_title="Generator Variante Loterie", page_icon="🎰", layout="wide")

st.title("🎰 Generator Variante Loterie 12/66 (configurabil - 3/3, 4/4, 5/5, etc.)")

st.markdown("""
Analizează frecvența numerelor, elimină cele reci, extrage top numere 
și generează variante unice cu strategii multiple și dimensiune variabilă (ex: 3/3, 4/4, 5/5).
""")

# --- Session State ---
if "variants" not in st.session_state:
    st.session_state.variants = []
if "top_numbers" not in st.session_state:
    st.session_state.top_numbers = []
if "frequency" not in st.session_state:
    st.session_state.frequency = {}

# --- Secțiunea 1: Încărcarea datelor ---
st.header("📊 1. Încarcă datele extragerilor")

tab1, tab2 = st.tabs(["📁 Import Fișier", "✍️ Manual"])

with tab1:
    uploaded_file = st.file_uploader("📂 CSV/TXT cu extragerile din runde", type=["csv", "txt"])
    
    if uploaded_file:
        try:
            content = uploaded_file.read().decode("utf-8")
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            all_numbers = []
            for line in lines:
                numbers = [int(x.strip()) for x in line.split(",")]
                all_numbers.extend(numbers)
            frequency = Counter(all_numbers)
            sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
            st.session_state.frequency = dict(sorted_freq)
            st.success(f"✅ Încărcate {len(lines)} runde cu total {len(all_numbers)} numere")
            rounds_df = pd.DataFrame([[i+1, line] for i, line in enumerate(lines)], columns=["Runda", "Numere"])
            st.dataframe(rounds_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"❌ Eroare: {str(e)}")

with tab2:
    st.subheader("✍️ Adaugă rundele manual")
    manual_input = st.text_area("Introduce rundele (o rună pe linie, numere separate cu virgulă)")
    
    if st.button("✅ Procesează rundele"):
        if manual_input.strip():
            try:
                lines = [line.strip() for line in manual_input.split("\n") if line.strip()]
                all_numbers = []
                for line in lines:
                    numbers = [int(x.strip()) for x in line.split(",")]
                    all_numbers.extend(numbers)
                frequency = Counter(all_numbers)
                sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
                st.session_state.frequency = dict(sorted_freq)
                st.success(f"✅ Procesate {len(lines)} runde cu total {len(all_numbers)} numere")
            except Exception as e:
                st.error(f"❌ Eroare: {str(e)}")
        else:
            st.warning("⚠️ Te rugăm să adaugi cel puțin o rună")

# --- Secțiunea 2: Configurare filtre ---
st.header("⚙️ 2. Configurare filtre")

col1, col2 = st.columns(2)

with col1:
    exclude_mode = st.radio("Exclude numere:", ["❌ Nu exclude", "🔢 Auto (cele mai reci)", "✍️ Manual"], horizontal=True)
    exclude_numbers = set()
    if exclude_mode == "🔢 Auto (cele mai reci)":
        cold_count = st.selectbox("Câte numere reci să excluzi:", [0, 5, 10, 15, 20], index=0)
        if st.session_state.frequency and cold_count > 0:
            sorted_freq = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
            exclude_numbers = set([x[0] for x in sorted_freq[-cold_count:]])
            st.info(f"Excluse automat: {sorted(exclude_numbers)}")
    elif exclude_mode == "✍️ Manual":
        manual = st.text_input("Numere de exclus (separate cu virgulă):")
        if manual.strip():
            try:
                exclude_numbers = set([int(x.strip()) for x in manual.split(",")])
                st.info(f"Excluse manual: {sorted(exclude_numbers)}")
            except:
                st.error("Format invalid")

with col2:
    top_count = st.slider("Câte numere din top folosești:", 10, 66, 50, step=1)
    if st.session_state.frequency:
        sorted_freq = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
        top_numbers = [x[0] for x in sorted_freq[:top_count] if x[0] not in exclude_numbers]
        st.session_state.top_numbers = top_numbers
        st.success(f"{len(top_numbers)} numere disponibile pentru generare")

# --- Secțiunea 3: Strategii de generare ---
st.header("🎲 3. Strategii de generare")

strategy = st.selectbox(
    "Alege strategia:",
    [
        "🎯 Standard (aleator)",
        "🔥 Hot Numbers (3 din top 10 + rest aleator)",
        "❄️ Cold-Hot Hybrid (jumătate top + jumătate rest)",
        "🔥❄️ Premium Hybrid (3 din top 25 + rest)",
        "⚡ Hybrid Ultra Sonic (2 din top 35 + 2 din 19–66)",
        "🎯 Ultra 3+1 (3 din top 34 + 1 din rest)",
        "🎪 Mix Strategy (combinație din toate)"
    ]
)

# 🔢 Selectează câte numere are o variantă
numere_pe_varianta = st.slider("Numere per variantă (ex: 3/3, 4/4, 5/5)", 3, 7, 4, step=1)

num_variants = st.number_input("Câte variante să genereze?", 100, 5000, 1000, step=100)

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

            # --- Strategie Standard ---
            if strategy == "🎯 Standard (aleator)":
                variant = tuple(sorted(random.sample(top_nums, numere_pe_varianta)))

            # --- Hot Numbers ---
            elif strategy == "🔥 Hot Numbers (3 din top 10 + rest aleator)":
                top10 = top_nums[:10]
                rest = top_nums[10:]
                n_hot = min(3, numere_pe_varianta - 1)
                n_rest = numere_pe_varianta - n_hot
                variant = tuple(sorted(random.sample(top10, n_hot) + random.sample(rest, n_rest)))

            # --- Cold-Hot Hybrid ---
            elif strategy == "❄️ Cold-Hot Hybrid (jumătate top + jumătate rest)":
                half = numere_pe_varianta // 2
                top20 = top_nums[:20]
                rest = top_nums[20:]
                variant = tuple(sorted(random.sample(top20, half) + random.sample(rest, numere_pe_varianta - half)))

            # --- Premium Hybrid ---
            elif strategy == "🔥❄️ Premium Hybrid (3 din top 25 + rest)":
                top25 = top_nums[:25]
                rest = top_nums[25:]
                n_top = min(3, numere_pe_varianta - 1)
                n_rest = numere_pe_varianta - n_top
                variant = tuple(sorted(random.sample(top25, n_top) + random.sample(rest, n_rest)))

            # --- Hybrid Ultra Sonic ---
            elif strategy == "⚡ Hybrid Ultra Sonic (2 din top 35 + 2 din 19–66)":
                top35 = top_nums[:35]
                rest = [n for n in top_nums if 19 <= n <= 66 and n not in top35]
                n_top = min(2, numere_pe_varianta - 2)
                n_rest = numere_pe_varianta - n_top
                if len(top35) >= n_top and len(rest) >= n_rest:
                    variant = tuple(sorted(random.sample(top35, n_top) + random.sample(rest, n_rest)))
                else:
                    variant = tuple(sorted(random.sample(top_nums, numere_pe_varianta)))

            # --- Ultra 3+1 ---
            elif strategy == "🎯 Ultra 3+1 (3 din top 34 + 1 din rest)":
                top34 = top_nums[:34]
                rest = [n for n in top_nums if n not in top34]
                n_top = min(3, numere_pe_varianta - 1)
                n_rest = numere_pe_varianta - n_top
                variant = tuple(sorted(random.sample(top34, n_top) + random.sample(rest, n_rest)))

            # --- Mix Strategy ---
            else:
                choice = random.randint(1, 5)
                if choice == 1:
                    variant = tuple(sorted(random.sample(top_nums, numere_pe_varianta)))
                elif choice == 2:
                    top10 = top_nums[:10]; rest = top_nums[10:]
                    variant = tuple(sorted(random.sample(top10, 3) + random.sample(rest, numere_pe_varianta - 3)))
                elif choice == 3:
                    top20 = top_nums[:20]; rest = top_nums[20:]
                    variant = tuple(sorted(random.sample(top20, numere_pe_varianta // 2) + random.sample(rest, numere_pe_varianta - numere_pe_varianta // 2)))
                elif choice == 4:
                    top25 = top_nums[:25]; rest = top_nums[25:]
                    variant = tuple(sorted(random.sample(top25, min(3, numere_pe_varianta - 1)) + random.sample(rest, numere_pe_varianta - min(3, numere_pe_varianta - 1))))
                else:
                    top35 = top_nums[:35]; rest = [n for n in top_nums if 19 <= n <= 66 and n not in top35]
                    variant = tuple(sorted(random.sample(top35, min(2, numere_pe_varianta - 2)) + random.sample(rest, numere_pe_varianta - min(2, numere_pe_varianta - 2))))

            variants.add(variant)

        final_variants = sorted(list(variants))
        random.shuffle(final_variants)
        st.session_state.variants = final_variants
        st.success(f"✅ Generate {len(final_variants)} variante ({numere_pe_varianta}/{numere_pe_varianta}) în {attempts} încercări")
        st.info(f"📊 Strategie: {strategy}")

# --- Secțiunea 4: Preview și Export ---
if st.session_state.variants:
    st.header("📋 4. Preview și Export")
    preview_count = st.slider("Câte variante să afișez?", 5, 50, 20)
    preview_df = pd.DataFrame([[i+1, " ".join(map(str, v))] for i, v in enumerate(st.session_state.variants[:preview_count])], columns=["ID", "Combinație"])
    st.dataframe(preview_df, use_container_width=True, hide_index=True)
    txt_output = "".join([f"{i+1}, {' '.join(map(str, v))}\n" for i, v in enumerate(st.session_state.variants)])
    st.download_button("⬇️ Descarcă variante (TXT)", data=txt_output, file_name="variante.txt", mime="text/plain")
    st.info(f"✅ Total variante generate: {len(st.session_state.variants)}")
