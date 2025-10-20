import streamlit as st
import pandas as pd
from collections import Counter
import random
import itertools
import numpy as np 

st.set_page_config(page_title="Generator Variante Keno Avansat", page_icon="🎯", layout="wide")

st.title("🎯 Generator Variante Keno Avansat & Ultra-Eficient")

st.markdown("""
Analiză statistică multi-nivel (frecvență, perechi, istoric) pentru a genera variante loto
cu eficiență sporită. **Toate filtrele de calitate au fost eliminate** pentru a permite generarea maximă.
""")

# --- Session State Initialization ---
if "variants" not in st.session_state:
    st.session_state.variants = []
if "top_numbers" not in st.session_state:
    st.session_state.top_numbers = []
if "frequency" not in st.session_state:
    st.session_state.frequency = {}
if "historic_rounds" not in st.session_state:
    st.session_state.historic_rounds = []
if "max_number" not in st.session_state:
    st.session_state.max_number = 80
if "pair_frequency" not in st.session_state:
    st.session_state.pair_frequency = {}
if "selected_strategies" not in st.session_state:
    st.session_state.selected_strategies = []
if "history_depth" not in st.session_state: 
    st.session_state.history_depth = 50
if "avg_reps" not in st.session_state:
    st.session_state.avg_reps = 0
if "generation_ran" not in st.session_state: 
    st.session_state.generation_ran = False 
if "process_ran" not in st.session_state:
    st.session_state.process_ran = False
if "top_stats_count" not in st.session_state: 
    st.session_state.top_stats_count = 10 

# --- Funcții de suport ---
def analyze_pairs_triplets(rounds, k_size):
    pair_counts = Counter()
    triplet_counts = Counter()
    for round_nums in rounds:
        sorted_nums = sorted(round_nums)
        for pair in itertools.combinations(sorted_nums, 2):
            pair_counts[tuple(sorted(pair))] += 1
        if k_size >= 3:
             for triplet in itertools.combinations(sorted_nums, 3):
                triplet_counts[tuple(sorted(triplet))] += 1
    sorted_pairs = dict(sorted(pair_counts.items(), key=lambda x: x[1], reverse=True))
    sorted_triplets = dict(sorted(triplet_counts.items(), key=lambda x: x[1], reverse=True))
    return sorted_pairs, sorted_triplets

def analyze_cold_streak(rounds, max_num):
    cold_streak = {}
    all_nums = set(range(1, max_num + 1))
    for num in all_nums:
        age = 0
        for round_nums in reversed(rounds):
            if num in round_nums: break
            age += 1
        cold_streak[num] = age
    return dict(sorted(cold_streak.items(), key=lambda x: x[1], reverse=True))

def analyze_repetitions(rounds):
    repetitions = []
    if len(rounds) < 2: return 0
    for i in range(1, len(rounds)):
        prev_round = set(rounds[i-1])
        current_round = set(rounds[i])
        repetitions.append(len(prev_round.intersection(current_round)))
    if not repetitions: return 0
    return round(np.median(repetitions))

def proceseaza_runde(lines, variant_size):
    all_numbers = []
    rounds_data = []
    for line in lines:
        try:
            numbers = [int(x.strip()) for x in line.split(",") if x.strip()]
            if any(n > st.session_state.max_number or n < 1 for n in numbers):
                st.error(f"Eroare: Runda conține numere în afara intervalului 1 la {st.session_state.max_number}.")
                return None, None, None
            if numbers:
                all_numbers.extend(numbers)
                rounds_data.append(numbers)
        except ValueError:
            st.error(f"Eroare la procesarea liniei: '{line}'. Asigură-te că sunt doar numere întregi valide separate prin virgulă.")
            return None, None, None
    if not rounds_data: return None, None, None

    frequency = Counter(all_numbers)
    sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    st.session_state.frequency = dict(sorted_freq)
    st.session_state.historic_rounds = rounds_data
    st.session_state.pair_frequency, st.session_state.triplet_frequency = analyze_pairs_triplets(rounds_data, variant_size)
    st.session_state.avg_reps = analyze_repetitions(rounds_data)
    return frequency, sorted_freq, all_numbers

def weighted_sample_unique(population, weights, k):
    sample = []
    available = list(population)
    current_weights = list(weights)

    for _ in range(k):
        if len(available) == 0: break
        if sum(current_weights) <= 0:
            sample.extend(random.sample(available, k - len(sample)))
            break
            
        chosen = random.choices(available, weights=current_weights, k=1)[0]
        sample.append(chosen)

        idx = available.index(chosen)
        available.pop(idx)
        current_weights.pop(idx)
        
    return sample

def is_valid_variant(variant, max_num):
    variant_size = len(variant)
    variant_set = set(variant)
    if len(variant_set) != variant_size: 
        return False
    return True


# --- Functie pentru generarea variantei pe baza strategiei (Logica) ---
def generate_variant_by_strategy(strategy_key, top_nums, variant_size, exclude_numbers, max_num, cold_data, top_pairs, top_triplets, cold_candidates, historic_rounds, avg_reps, use_triplets):
    if len(top_nums) < variant_size: return []
    
    all_numbers_with_freq = st.session_state.frequency
    sorted_freq_keys = list(st.session_state.frequency.keys())
    
    # ------------------------------------------------------------------
    # --- LOGICA NOUĂ: Stratificată (Top 15/20/25 + Rest) ---
    # ------------------------------------------------------------------
    if strategy_key == "stratified_mix":
        if variant_size != 4:
            # Dacă mărimea nu e 4, revenim la tragere simplă ponderată
            strategy_key = "weighted_frequency"
        
        elif len(sorted_freq_keys) < 25:
             # Nu sunt suficiente numere unice în istoric pentru a defini straturile
             strategy_key = "weighted_frequency"

        else:
            variant = []
            
            # Definirea straturilor exclusive
            pool_15 = set(sorted_freq_keys[:15])                           # Top 1 - 15
            pool_16_20 = set(sorted_freq_keys[15:20])                     # Locurile 16 - 20
            pool_21_25 = set(sorted_freq_keys[20:25])                     # Locurile 21 - 25
            
            # Restul: Numerele disponibile în Top N, care NU sunt în Top 25
            all_top_n_set = set(top_nums)
            pool_rest = all_top_n_set - (pool_15 | pool_16_20 | pool_21_25)
            
            # Verificare minimă a pool-urilor necesare
            if not pool_15 or not pool_16_20 or not pool_21_25 or not pool_rest:
                 st.warning("Setul de numere 'Top N' sau frecvența nu permit crearea celor 4 straturi distincte. Se folosește tragere ponderată.")
                 strategy_key = "weighted_frequency"
            else:
                # Extragem câte un număr din fiecare strat distinct (pentru a garanta diversitatea)
                
                # Locul 1: Top 15 (Selectează din cel mai fierbinte strat)
                num1 = random.choice(list(pool_15))
                variant.append(num1)
                
                # Locul 2: Top 16-20 (Selectează din stratul fierbinte secundar)
                # Notă: Trebuie să ne asigurăm că nu este același număr, dar pool-urile sunt deja exclusive (pool_15 nu e in pool_16_20)
                num2 = random.choice(list(pool_16_20))
                variant.append(num2)
                
                # Locul 3: Top 21-25 (Selectează din stratul median)
                num3 = random.choice(list(pool_21_25))
                variant.append(num3)
                
                # Locul 4: Restul (Selectează din cele mai reci/medii rămase)
                num4 = random.choice(list(pool_rest))
                variant.append(num4)
                
                # Am extras 4 numere din 4 seturi disjuncte, deci sunt automat unice.
                return list(set(variant))
    
    # ------------------------------------------------------------------
    # --- LOGICA GENERALĂ (Standard, Ponderată și Alte Strategii) ---
    # ------------------------------------------------------------------
    
    # 1. Standard (Ponderare Uniformă - Trage aleatoriu, ignorând frecvența)
    if strategy_key == "standard":
        variant = random.sample(top_nums, variant_size)
        
    # 2. Ponderată (inclusiv cazul în care "stratified_mix" a eșuat)
    else:
        general_weights = [all_numbers_with_freq.get(n, 1) for n in top_nums]
        if not general_weights or sum(general_weights) <= 0:
            variant = random.sample(top_nums, variant_size)
        else:
            variant = weighted_sample_unique(top_nums, general_weights, variant_size)
            
    return list(set(variant)) 


# --- Secțiunea 1: Configurare & Încarcare date (Neschimbată) ---
st.header("1. Configurare Loterie & Încărcare Date")

col_max, col_size, col_round = st.columns(3)

with col_max:
    st.session_state.max_number = st.number_input(
        "Numărul maxim al loteriei (ex: 80, 90)",
        min_value=1,
        value=80,
        step=1
    )
with col_size:
    variant_size = st.slider(
        "📏 Alege mărimea variantei (k/k, ex: 5/5, 8/8)",
        min_value=1, 
        max_value=9, 
        value=4, 
        step=1
    )
    if variant_size < 2:
        st.error("Mărimea variantei trebuie să fie de minim 2 pentru strategiile avansate.")
with col_round:
    st.info(f"Domeniul de lucru: **1 la {st.session_state.max_number}**")


tab1, tab2 = st.tabs(["📁 Import Fișier", "✍️ Manual"])

uploaded_file = None
manual_input = ""
lines = []

with tab1:
    uploaded_file = st.file_uploader("📂 CSV/TXT cu extragerile din runde", type=["csv", "txt"])
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        lines = [line.strip() for line in content.split("\n") if line.strip()]

with tab2:
    st.subheader("✍️ Adaugă rundele manual")
    manual_input = st.text_area("Introduce rundele (o rundă pe linie, numere separate cu virgulă)", height=300, 
                                help=f"Exemplu: 1,12,25,30,44,51,68,79")

if st.button("✅ Procesează rundele și rulează analiza"):
    if uploaded_file and lines:
        results = proceseaza_runde(lines, variant_size)
    elif manual_input.strip():
        lines = [line.strip() for line in manual_input.split("\n") if line.strip()]
        results = proceseaza_runde(lines, variant_size)
    else:
        st.warning("⚠️ Te rugăm să încarci sau să introduci datele.")
        results = None

    if results is not None:
        frequency, sorted_freq, all_numbers = results
        st.session_state.process_ran = True 
        st.success(f"✅ Analiză completă pe **{len(st.session_state.historic_rounds)}** runde.")
        st.info(f"Repetiții mediane runda N-1: **{st.session_state.avg_reps}**")


st.markdown("---")

# --- Secțiunea 2: Configurare filtre (Neschimbată) ---
st.header("2. Configurare Filtre (Rece & Cald)")

col1, col2 = st.columns(2)
exclude_numbers = set()

with col1:
    st.subheader("❄️ Exclude numere")
    exclude_mode = st.radio("Cum vrei să excluzi?", ["🔢 Exclude cele mai reci", "✍️ Manual", "🔀 Ambele"], horizontal=True)
    auto_exclude = set()

    if exclude_mode in ["🔢 Exclude cele mai reci", "🔀 Ambele"]:
        auto_cold_count = st.selectbox("Exclude topul celor mai reci N numere", [0, 5, 10, 15, 20, 30], index=0)
        if st.session_state.frequency and auto_cold_count > 0:
            sorted_freq_items = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
            auto_exclude = set([x[0] for x in sorted_freq_items[-auto_cold_count:]])
            st.info(f"🔴 Auto-exclude: {sorted(auto_exclude)}")

    if exclude_mode in ["✍️ Manual", "🔀 Ambele"]:
        manual_exclude_input = st.text_area("Introduce numere de exclus manual (separate cu virgulă)", height=80)
        if manual_exclude_input.strip():
            try:
                manual_exclude = set([int(x.strip()) for x in manual_exclude_input.split(",") if x.strip()])
                exclude_numbers.update(manual_exclude)
                st.info(f"✋ Manual exclude: {sorted(manual_exclude)}")
            except ValueError:
                 st.error("Te rugăm să introduci numere întregi valide separate prin virgulă.")
                 
    exclude_numbers.update(auto_exclude)
    if exclude_numbers:
        st.success(f"📌 Total excluse: **{len(exclude_numbers)}** numere.")

with col2:
    st.subheader("🔥 Numere pentru generare (Top N Frecvență)")
    top_count = st.slider("Câte numere fierbinți să păstrezi?", 10, st.session_state.max_number, min(st.session_state.max_number, 50), 1)
    
    if st.session_state.frequency:
        sorted_freq_items = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
        top_numbers = [x[0] for x in sorted_freq_items if x[0] not in exclude_numbers][:top_count]
        st.session_state.top_numbers = top_numbers
        st.success(f"✅ **{len(top_numbers)}** numere disponibile pentru generare.")
        
        cold_data = analyze_cold_streak(st.session_state.historic_rounds, st.session_state.max_number)
        cold_candidates_info = [(num, age) for num, age in cold_data.items() if num not in top_numbers and num not in exclude_numbers]
        if cold_candidates_info:
            st.markdown(f"**Cei mai reci (disponibili):** {', '.join([f'{n}({a}r)' for n, a in cold_candidates_info[:5]])}")

st.markdown("---")

# --- Secțiunea 3: Strategii de generare ---
st.header("3. Strategii de Generare Avansată")

col_num, col_depth, col_comb = st.columns(3)

with col_num:
    num_variants = st.number_input("Câte variante unice să generezi?", 10, 10000, 1000, 10)

with col_depth:
    st.session_state.history_depth = st.selectbox(
        "Adâncimea Istoriei (număr de runde analizate)",
        options=[50, 85, 100, 150],
        index=0,
        help="Câte runde recente se iau în considerare pentru strategia 'Adâncimea Istoriei'."
    )
with col_comb:
    st.markdown("##### Tip Combinație Bază")
    use_triplets = st.checkbox("Folosește Triplete (3 numere) în loc de Perechi (2 numere) pentru baza combinatorie (Dacă k >= 3)", value=False)
    
    if use_triplets and variant_size < 3:
        st.warning("⚠️ Tripletele necesită varianta de minim 3. Se vor folosi Perechi.")
        use_triplets = False


ALL_STRATEGIES = {
    "🎯 Standard (Aleatoriu Uniform)": "standard", 
    "🔥 Hot Numbers (3 din top 10 + rest ponderat)": "hot_numbers", 
    "❄️ Cold-Hot Hybrid (Mix 50/50 ponderat)": "cold_hot_hybrid", 
    "⚡ Frecvență Ponderată (Fără Repetiție)": "weighted_frequency",
    "🥇 Perechi/Triplete de Aur (Bază Combinatorie + Rest din Top N)": "golden_pairs",
    "🔄 Par-Impar Echilibrat (Generare Forțată)": "parity_balance",
    "🗺️ Câmpuri de Forță (Minimum 3 Cadrane)": "quadrant_force",
    "🕰️ Aproape de Întoarcere (Include numere 'în vârstă')": "return_age", 
    "⛓️ Numere Consecutive (Asigură o pereche)": "consecutive_pair",
    "⭐ Frecvență & Vecinătate": "frequency_neighbors",
    "💡 Restantierul (Cold Booster)": "cold_booster",
    "⚖️ Somă Medie (Selecție Ponderată pe Suma Optimă)": "average_sum_weighted", 
    "🧬 Adâncimea Istoriei (Aderență la ultimele N runde)": "history_adherence",
    "🧪 Mix Strategy (Combinație aleatorie a strategiilor)": "mix_strategy",
    "🌡️ Termometrul (Hot/Cold Ratio 70/30)": "hot_cold_ratio",
    "🧲 Atracția Vestică (Low Numbers Gravitation)": "low_numbers_gravitation",
    "📅 Repetiție Zonală (Last Round Quadrant Mirroring)": "quadrant_mirroring",
    "🔄 Aderență Forțată la Runda Precedentă (Repetiții Istorice)": "forced_repetitions",
    "📈 Stratificată (Top 15/16-20/21-25 + Rest, doar pentru 4/4)": "stratified_mix", 
}

st.subheader("☑️ Selectează Strategiile de Generare")
col_a, col_b = st.columns(2)

selected_strategies_keys = []
strategy_items = list(ALL_STRATEGIES.items())

for i, (label, key) in enumerate(strategy_items):
    target_column = col_a if i < len(strategy_items) / 2 else col_b
    with target_column:
        if st.checkbox(label, key=f"strat_{key}"):
            selected_strategies_keys.append(key)

st.session_state.selected_strategies = selected_strategies_keys

# --- Generare Logică Principală ---
if st.button("🚀 Generează variante"):
    if not st.session_state.process_ran:
        st.error("❌ Te rugăm să încarci datele și să rulezi analiza în Secțiunea 1.")
    elif not st.session_state.top_numbers:
        st.error("❌ Configurează filtrele în Secțiunea 2 (Numerele disponibile sunt 0).")
    elif variant_size > len(st.session_state.top_numbers):
        st.error(f"❌ Mărimea variantei ({variant_size}) este mai mare decât numerele disponibile ({len(st.session_state.top_numbers)}).")
    elif not st.session_state.selected_strategies:
        st.error("❌ Te rugăm să selectezi cel puțin o strategie de generare.")
    else:
        st.session_state.generation_ran = True 

        top_nums = st.session_state.top_numbers
        variants = set()
        num_generated = 0
        max_attempts = num_variants * 100
        attempts = 0
        
        max_num = st.session_state.max_number
        cold_data = analyze_cold_streak(st.session_state.historic_rounds, max_num)
        cold_candidates = [num for num, age in cold_data.items() if num not in top_nums and num not in exclude_numbers]
        top_pairs = st.session_state.pair_frequency
        top_triplets = st.session_state.triplet_frequency
        strategies_to_use = st.session_state.selected_strategies
        num_strategies = len(strategies_to_use)
        
        while num_generated < num_variants and attempts < max_attempts:
            attempts += 1
            
            strategy_key = strategies_to_use[attempts % num_strategies]
            
            variant = generate_variant_by_strategy(
                strategy_key, top_nums, variant_size, exclude_numbers, max_num, 
                cold_data, top_pairs, top_triplets, cold_candidates, 
                st.session_state.historic_rounds, st.session_state.avg_reps, use_triplets
            )
            
            if len(variant) == variant_size and is_valid_variant(variant, max_num):
                final_variant = tuple(sorted(variant))
                if final_variant not in variants:
                    variants.add(final_variant)
                    num_generated += 1

        st.session_state.variants = list(variants)
        random.shuffle(st.session_state.variants)
        
        selected_strategy_labels = [k for k, v in ALL_STRATEGIES.items() if v in strategies_to_use]

        if len(st.session_state.variants) > 0:
            st.success(f"✅ Generate **{len(st.session_state.variants)}** variante UNICE ({variant_size}/{variant_size}) din {num_variants} dorite, în {attempts} încercări, folosind strategiile: **{', '.join(selected_strategy_labels)}**")
            if len(st.session_state.variants) < num_variants:
                 st.warning(f"⚠️ **ATENȚIE**: Au fost generate doar {len(st.session_state.variants)} din {num_variants} dorite. Mărește 'Top N' din Secțiunea 2.")
        else:
             st.error(f"❌ Nu s-a putut genera nicio variantă unică. Încercări totale: {attempts}.")


st.markdown("---")

# --- Secțiunea 4: Preview & Export (Top N Selectabil) ---

if st.session_state.generation_ran: 
    st.header("4. Preview și Export")
    
    export_lines = []

    if st.session_state.variants:
        
        # Selector pentru Top N în statistică
        st.session_state.top_stats_count = st.selectbox(
            "Afișează Top N numere folosite în statistici:",
            options=[10, 15, 20, 25, 30],
            index=0
        )

        generated_nums = []
        for v in st.session_state.variants:
            generated_nums.extend(v)
        generated_freq = Counter(generated_nums)
        
        st.subheader(f"Statistici Variante Generate ({len(st.session_state.variants)} variante)")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            top_generated = sorted(generated_freq.items(), key=lambda x: x[1], reverse=True)[:st.session_state.top_stats_count]
            st.info(f"Top {st.session_state.top_stats_count} numere folosite: {', '.join([f'{n}({f}x)' for n, f in top_generated])}")
            
        with col_g2:
            st.info(f"Număr mediu de repetiții cu runda precedentă: **{st.session_state.avg_reps}**")

        
        preview_count = min(20, len(st.session_state.variants))
        st.subheader(f"Preview (Primele {preview_count} variante)")
        
        preview_data_app = []
        for i, v in enumerate(st.session_state.variants):
            variant_str_space = " ".join(map(str, sorted(v)))
            
            # FORMATUL FINAL CERUT PENTRU EXPORT: ID, spațiu Numere
            export_lines.append(f"{i+1}, {variant_str_space}")
            
            preview_data_app.append([i+1, f"{i+1}, {variant_str_space}"])
        
        
        preview_df = pd.DataFrame(
            preview_data_app[:preview_count], 
            columns=["ID", "Combinație (Format Export)"]
        )
        st.dataframe(preview_df, use_container_width=True, hide_index=True)

        
        txt_output = "\n".join(export_lines)
        
    else: 
        txt_output = ""
        st.warning("⚠️ Nu s-au generat variante valide. Fișierul exportat va fi gol.")


    # 2. BUTONUL DE DESCARCARE
    st.download_button("⬇️ Descarcă variantele (TXT)", txt_output, "variante_generate_eficient.txt", "text/plain")
