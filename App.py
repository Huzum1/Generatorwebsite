import streamlit as st
import random
import pandas as pd
from itertools import combinations

# --- Inițializare Session State ---
def init_session_state():
    """Inițializează toate valorile în session_state"""
    if "top_numbers" not in st.session_state:
        st.session_state.top_numbers = []
    if "strategy" not in st.session_state:
        st.session_state.strategy = "🎯 Standard (4 numere aleatoare)"
    if "num_variants" not in st.session_state:
        st.session_state.num_variants = 10
    if "variants" not in st.session_state:
        st.session_state.variants = []
    if "frequency" not in st.session_state:
        st.session_state.frequency = {}
    if "rounds" not in st.session_state:
        st.session_state.rounds = []

init_session_state()

# --- Configurare pagină ---
st.set_page_config(page_title="🎲 Generator Variante Loto", layout="wide")
st.title("🎲 Generator Variante Loto")

# --- Sidebar: Upload și Configurare ---
with st.sidebar:
    st.header("⚙️ Configurare")
    
    # Upload CSV
    uploaded_file = st.file_uploader("📤 Încarcă fișierul CSV", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.frequency = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
            top_nums = sorted(st.session_state.frequency.keys(), 
                            key=lambda x: st.session_state.frequency[x], 
                            reverse=True)
            st.session_state.top_numbers = top_nums
            st.success(f"✅ Încărcat! {len(top_nums)} numere")
        except Exception as e:
            st.error(f"❌ Eroare la încărcare: {e}")
    
    st.divider()
    
    # Selectare strategie
    strategies = [
        "🎯 Standard (4 numere aleatoare)",
        "🔥 Hot Numbers (3 din top 10 + 1 din rest)",
        "❄️ Cold-Hot Hybrid (2 din top 20 + 2 din 21-50)",
        "🧬 Hybrid 3+1 (3 din top 25 + 1 din rest aleator)",
        "🌀 Random Pairs (2 perechi aleatoare)",
        "⚡ Frecvență Ponderată (numere cu mai multă frecvență)",
        "🎪 Mix Strategy (combinație din toate)",
        "🔥❄️ Premium Hybrid (toate posibile 3+1 din top 25/rest)"
    ]
    
    st.session_state.strategy = st.selectbox("🎯 Selectează Strategie", strategies)
    
    # Numărul de variante
    st.session_state.num_variants = st.number_input(
        "📊 Numărul de variante", 
        min_value=1, 
        max_value=10000, 
        value=st.session_state.num_variants
    )
    
    st.divider()
    
    # Afișare date încărcate
    if st.session_state.top_numbers:
        st.info(f"📈 Total numere: {len(st.session_state.top_numbers)}")
        if st.checkbox("📋 Vizualizează top 20"):
            top_20 = st.session_state.top_numbers[:20]
            for i, num in enumerate(top_20, 1):
                freq = st.session_state.frequency.get(num, 0)
                st.text(f"{i}. {num} - Frecvență: {freq}")

# --- Secțiunea Principală ---
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🚀 Generare Variante")
    
    # Buton Generare
    if st.button("🚀 Generează variante", use_container_width=True, key="generate_btn"):
        if not st.session_state.top_numbers:
            st.error("❌ Încarcă datele și configurează filtrele")
        else:
            top_nums = st.session_state.top_numbers
            strategy = st.session_state.strategy
            num_variants = st.session_state.num_variants
            
            variants = set()
            
            # --- Strategie specială: Premium Hybrid ---
            if strategy == "🔥❄️ Premium Hybrid (toate posibile 3+1 din top 25/rest)":
                top25 = top_nums[:25]
                rest = top_nums[25:]
                
                if len(top25) >= 3 and len(rest) >= 1:
                    all_combos = []
                    for three in combinations(top25, 3):
                        for one in rest:
                            variant = tuple(sorted(list(three) + [one]))
                            all_combos.append(variant)
                    
                    if len(all_combos) > num_variants:
                        variants = set(random.sample(all_combos, num_variants))
                    else:
                        variants = set(all_combos)
                    
                    st.session_state.variants = sorted(list(variants))
                    st.success(f"✅ Generate exact {len(st.session_state.variants)} variante (din {len(all_combos)} posibile)")
                    st.info(f"📊 Strategie: {strategy}")
                else:
                    st.error("❌ Nu sunt suficiente numere pentru Premium Hybrid")
            
            # --- Restul strategiilor ---
            else:
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
                            variant = tuple(sorted(random.sample(top10, 3) + random.sample(rest, 1)))
                        else:
                            variant = tuple(sorted(random.sample(top_nums, 4)))
                    
                    elif strategy == "❄️ Cold-Hot Hybrid (2 din top 20 + 2 din 21-50)":
                        top20 = top_nums[:20]
                        rest = top_nums[20:]
                        if len(rest) >= 2:
                            variant = tuple(sorted(random.sample(top20, 2) + random.sample(rest, 2)))
                        else:
                            variant = tuple(sorted(random.sample(top_nums, 4)))
                    
                    elif strategy == "🧬 Hybrid 3+1 (3 din top 25 + 1 din rest aleator)":
                        top25 = top_nums[:25]
                        rest = top_nums[25:]
                        if len(top25) >= 3 and len(rest) >= 1:
                            variant = tuple(sorted(random.sample(top25, 3) + random.sample(rest, 1)))
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
                        choice = random.randint(1, 7)
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
                        elif choice == 6:
                            top25 = top_nums[:25]
                            rest = top_nums[25:]
                            variant = tuple(sorted(random.sample(top25, 3) + random.sample(rest, 1))) if len(rest) > 0 else tuple(sorted(random.sample(top_nums, 4)))
                        else:
                            variant = tuple(sorted(random.sample(top_nums, 4)))
                    
                    variants.add(variant)
                
                st.session_state.variants = sorted(list(variants))
                st.success(f"✅ Generate exact {len(st.session_state.variants)} variante (din {attempts} încercări)")
                st.info(f"📊 Strategie: {strategy}")
    
    # Afișare variante
    if st.session_state.variants:
        st.divider()
        st.subheader(f"📋 {len(st.session_state.variants)} Variante Generate")
        
        # Tabel
        variants_df = pd.DataFrame(
            [(i+1, " - ".join(map(str, v))) for i, v in enumerate(st.session_state.variants)],
            columns=["#", "Numere"]
        )
        st.dataframe(variants_df, use_container_width=True, hide_index=True)
        
        # Descărcare CSV
        csv = variants_df.to_csv(index=False)
        st.download_button(
            label="📥 Descarcă CSV",
            data=csv,
            file_name="variante_loto.csv",
            mime="text/csv"
        )

with col2:
    st.header("📊 Statistici")
    
    if st.session_state.variants:
        st.metric("Total variante", len(st.session_state.variants))
        st.metric("Strategie", strategy.split("(")[0].strip())
        
        st.divider()
        
        # Frecvență numere în variante
        all_nums_in_variants = []
        for variant in st.session_state.variants:
            all_nums_in_variants.extend(variant)
        
        from collections import Counter
        num_freq = Counter(all_nums_in_variants)
        top_nums_freq = sorted(num_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        st.subheader("🔥 Top 10 Numere în Variante")
        for num, freq in top_nums_freq:
            st.text(f"{num}: {freq} apariții")

st.divider()

# --- Istoric Runde ---
st.header("📝 Istoric Runde")

col1, col2 = st.columns([3, 1])

with col1:
    if st.button("💾 Salvează runda curentă"):
        if st.session_state.variants:
            round_data = {
                "Strategie": st.session_state.strategy,
                "Variante": len(st.session_state.variants),
                "Data": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.rounds.append(round_data)
            st.success("✅ Runda salvată!")

with col2:
    if st.button("🗑️ Șterge istoric"):
        st.session_state.rounds = []
        st.info("Istoric șters")

if st.session_state.rounds:
    rounds_df = pd.DataFrame(st.session_state.rounds)
    st.dataframe(rounds_df, use_container_width=True, hide_index=True)
