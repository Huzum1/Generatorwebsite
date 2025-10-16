import streamlit as st
import pandas as pd
from collections import Counter
import random
import io

st.set_page_config(page_title="Generator Variante Loterie", page_icon="🎰", layout="wide")

st.title("🎰 Generator Variante Loterie 12/66 (4/4)")

st.markdown("""
Analizează frecvența numerelor, elimină cele reci, extrage top numere 
și generează variante unice cu strategii multiple.
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
            
            # Afișare runde
            st.subheader("📋 Rundele încărcate:")
            rounds_df = pd.DataFrame([[i+1, line] for i, line in enumerate(lines)], columns=["Runda", "Numere"])
            st.dataframe(rounds_df, use_container_width=True, hide_index=True)
            
            # Statistici
            col1, col2, col3 = st.columns(3)
            col1.metric("Runde", len(lines))
            col2.metric("Total numere", len(all_numbers))
            col3.metric("Numere unice", len(frequency))
            
            # Top și Bottom
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔥 Top 15 cele mai frecvente")
                top15_df = pd.DataFrame(sorted_freq[:15], columns=["Număr", "Frecvență"])
                st.dataframe(top15_df, use_container_width=True)
            
            with col2:
                st.subheader("❄️ Bottom 15 cele mai reci")
                bottom15_df = pd.DataFrame(sorted_freq[-15:], columns=["Număr", "Frecvență"])
                st.dataframe(bottom15_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Eroare: {str(e)}")

with tab2:
    st.subheader("✍️ Adaugă rundele manual")
    
    manual_input = st.text_area(
        "Introduce rundele (o rună pe linie, numere separate cu virgulă)",
        placeholder="7, 27, 22, 34, 59, 14, 55, 52, 47, 41, 51, 11\n51, 3, 61, 10, 27, 55, 24, 39, 12, 14, 65, 58\n4, 49, 55, 11, 7, 30, 44, 29, 60, 59, 22, 36",
        height=300
    )
    
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
                
                # Afișare runde
                st.subheader("📋 Rundele adăugate:")
                rounds_df = pd.DataFrame([[i+1, line] for i, line in enumerate(lines)], columns=["Runda", "Numere"])
                st.dataframe(rounds_df, use_container_width=True, hide_index=True)
                
                # Statistici
                col1, col2, col3 = st.columns(3)
                col1.metric("Runde", len(lines))
                col2.metric("Total numere", len(all_numbers))
                col3.metric("Numere unice", len(frequency))
                
                # Top și Bottom
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🔥 Top 15 cele mai frecvente")
                    top15_df = pd.DataFrame(sorted_freq[:15], columns=["Număr", "Frecvență"])
                    st.dataframe(top15_df, use_container_width=True)
                
                with col2:
                    st.subheader("❄️ Bottom 15 cele mai reci")
                    bottom15_df = pd.DataFrame(sorted_freq[-15:], columns=["Număr", "Frecvență"])
                    st.dataframe(bottom15_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Eroare: {str(e)}")
        else:
            st.warning("⚠️ Te rugăm să adaugi cel puțin o rună")

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
    
    # Excludere automata
    if exclude_mode in ["🔢 Automata (cele mai reci)", "🔀 Ambele"]:
        auto_cold_count = st.selectbox(
            "Exclude topul celor mai reci",
            [0, 5, 10, 15, 20],
            index=0
        )
        
        if st.session_state.frequency and auto_cold_count > 0:
            sorted_freq = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
            auto_exclude = set([x[0] for x in sorted_freq[-auto_cold_count:]])
            if auto_exclude:
                st.info(f"🔴 Auto-exclude ({auto_cold_count}): {sorted(auto_exclude)}")
    
    # Excludere manuala
    if exclude_mode in ["✍️ Manual (numere specifice)", "🔀 Ambele"]:
        manual_exclude_input = st.text_area(
            "Introduce numere de exclus manual (separate cu virgulă)",
            placeholder="Exemplu: 51, 2, 15",
            height=80
        )
        
        if manual_exclude_input.strip():
            try:
                manual_exclude = set([int(x.strip()) for x in manual_exclude_input.split(",")])
                if manual_exclude:
                    st.info(f"✋ Manual exclude: {sorted(manual_exclude)}")
                exclude_numbers.update(manual_exclude)
            except:
                st.error("❌ Format invalid pentru numere de exclus")
    
    exclude_numbers.update(auto_exclude)
    
    if exclude_numbers:
        st.success(f"📌 Total excluse: {len(exclude_numbers)} numere: {sorted(exclude_numbers)}")

with col2:
    st.subheader("🔥 Numere pentru generare (top numere)")
    top_count = st.slider(
        "Câte numere din top?",
        min_value=10,
        max_value=66,
        value=50,
        step=1
    )
    
    if st.session_state.frequency:
        sorted_freq = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
        top_numbers = [x[0] for x in sorted_freq[:top_count] if x[0] not in exclude_numbers]
        st.session_state.top_numbers = top_numbers
        st.success(f"✅ {len(top_numbers)} numere disponibile")
        st.write("Numere:", sorted(top_numbers))

# --- Secțiunea 3: Strategii de generare ---
st.header("🎲 3. Strategii de generare")

strategy = st.radio(
    "Alege strategia:",
    [
        "🎯 Standard (4 numere aleatoare)",
        "🔥 Hot Numbers (3 din top 10 + 1 din rest)",
        "❄️ Cold-Hot Hybrid (2 din top 20 + 2 din 21-50)",
        "🔥❄️ Premium Hybrid (3 din top 25 + 1 din rest)",
        "🌀 Random Pairs (2 perechi aleatoare)",
        "⚡ Frecvență Ponderată (numere cu mai multă frecvență)",
        "🎪 Mix Strategy (combinație din toate)"
    ]
)

num_variants = st.number_input(
    "Câte variante?",
    min_value=100,
    max_value=5000,
    value=1000,
    step=100
)

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
            
            if strategy == "🎯 Standard (4 numere aleatoare)":
                variant = tuple(sorted(random.sample(top_nums, 4)))
            
            elif strategy == "🔥 Hot Numbers (3 din top 10 + 1 din rest)":
                top10 = top_nums[:10]
                rest = top_nums[10:]
                if len(rest) > 0:
                    three = random.sample(top10, min(3, len(top10)))
                    one = random.sample(rest, 1)
                    variant = tuple(sorted(three + one))
                else:
                    variant = tuple(sorted(random.sample(top_nums, 4)))
            
            elif strategy == "❄️ Cold-Hot Hybrid (2 din top 20 + 2 din 21-50)":
                top20 = top_nums[:20]
                rest = top_nums[20:]
                if len(rest) >= 2:
                    two_hot = random.sample(top20, min(2, len(top20)))
                    two_cold = random.sample(rest, min(2, len(rest)))
                    variant = tuple(sorted(two_hot + two_cold))
                else:
                    variant = tuple(sorted(random.sample(top_nums, 4)))
            
            elif strategy == "🔥❄️ Premium Hybrid (3 din top 25 + 1 din rest)":
                top25 = top_nums[:25]
                rest = top_nums[25:]
                if len(rest) > 0:
                    three = random.sample(top25, min(3, len(top25)))
                    one = random.sample(rest, 1)
                    variant = tuple(sorted(three + one))
                else:
                    variant = tuple(sorted(random.sample(top_nums, 4)))
            
            elif strategy == "🌀 Random Pairs (2 perechi aleatoare)":
                if len(top_nums) >= 4:
                    pair1 = random.sample(top_nums, 2)
                    pair2 = random.sample(top_nums, 2)
                    variant = tuple(sorted(pair1 + pair2))
                else:
                    variant = tuple(sorted(random.sample(top_nums, 4)))
            
            elif strategy == "⚡ Frecvență Ponderată (numere cu mai multă frecvență)":
                weights = [st.session_state.frequency.get(n, 1) for n in top_nums]
                variant = tuple(sorted(random.choices(top_nums, weights=weights, k=4)))
            
            elif strategy == "🎪 Mix Strategy (combinație din toate)":
                choice = random.randint(1, 6)
                if choice == 1:
                    variant = tuple(sorted(random.sample(top_nums, 4)))
                elif choice == 2:
                    top10 = top_nums[:10]
                    rest = top_nums[10:]
                    variant = tuple(sorted(random.sample(top10, 3) + random.sample(rest, 1))) if len(rest) > 0 else tuple(sorted(random.sample(top_nums, 4)))
                elif choice == 3:
                    top20 = top_nums[:20]
                    rest = top_nums[20:]
                    variant = tuple(sorted(random.sample(top20, 2) + random.sample(rest, 2))) if len(rest) >= 2 else tuple(sorted(random.sample(top_nums, 4)))
                elif choice == 4:
                    variant = tuple(sorted(random.sample(top_nums, 2) + random.sample(top_nums, 2)))
                elif choice == 5:
                    weights = [st.session_state.frequency.get(n, 1) for n in top_nums]
                    variant = tuple(sorted(random.choices(top_nums, weights=weights, k=4)))
                else:
                    top25 = top_nums[:25]
                    rest = top_nums[25:]
                    variant = tuple(sorted(random.sample(top25, 3) + random.sample(rest, 1))) if len(rest) > 0 else tuple(sorted(random.sample(top_nums, 4)))
            
            variants.add(variant)
        
        st.session_state.variants = sorted(list(variants))
        st.success(f"✅ Generate {len(st.session_state.variants)} variante unice în {attempts} încercări")
        st.info(f"📊 Strategie: {strategy}")

# --- Secțiunea 4: Preview și Export ---
if st.session_state.variants:
    st.header("📋 4. Preview și Export")
    
    preview_count = st.slider("Câte variante să afișez?", 5, 50, 20)
    
    st.subheader(f"Preview (primele {preview_count})")
    preview_df = pd.DataFrame(
        [[i+1, " ".join(map(str, v))] for i, v in enumerate(st.session_state.variants[:preview_count])],
        columns=["ID", "Combinație"]
    )
    st.dataframe(preview_df, use_container_width=True, hide_index=True)
    
    # Export TXT
    txt_output = ""
    for i, variant in enumerate(st.session_state.variants, 1):
        txt_output += f"{i}, {' '.join(map(str, variant))}\n"
    
    st.download_button(
        label="⬇️ Descarcă variante (TXT)",
        data=txt_output,
        file_name="variante.txt",
        mime="text/plain"
    )
    
    st.info(f"✅ Total variante generate: {len(st.session_state.variants)}")
