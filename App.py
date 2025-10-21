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
if "triplet_frequency" not in st.session_state:
    st.session_state.triplet_frequency = {}
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
            if num in round_nums: 
                break
            age += 1
        cold_streak[num] = age
    return dict(sorted(cold_streak.items(), key=lambda x: x[1], reverse=True))

def analyze_repetitions(rounds):
    repetitions = []
    if len(rounds) < 2: 
        return 0
    for i in range(1, len(rounds)):
        prev_round = set(rounds[i-1])
        current_round = set(rounds[i])
        repetitions.append(len(prev_round.intersection(current_round)))
    if not repetitions: 
        return 0
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
    if not rounds_data: 
        return None, None, None

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
        if len(available) == 0: 
            break
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
    variant_set = set(variant)
    if len(variant_set) != len(variant): 
        return False
    return True


# --- Functie pentru generarea variantei pe baza strategiei (Logica Completa) ---
def generate_variant_by_strategy(strategy_key, top_nums, variant_size, exclude_numbers, max_num, cold_data, top_pairs, top_triplets, cold_candidates, historic_rounds, avg_reps, use_triplets):
    if len(top_nums) < variant_size: 
        return []
    
    all_numbers_with_freq = st.session_state.frequency
    sorted_freq_keys = list(st.session_state.frequency.keys())
    variant = []
    
    # Strategy: Standard (Uniform Random)
    if strategy_key == "standard":
        variant = random.sample(top_nums, variant_size)
    
    # Strategy: Weighted Frequency
    elif strategy_key == "weighted_frequency":
        weights = [all_numbers_with_freq.get(n, 1) for n in top_nums]
        variant = weighted_sample_unique(top_nums, weights, variant_size)
    
    # Strategy: Hot Numbers (3 from top 10 + rest weighted)
    elif strategy_key == "hot_numbers":
        hot_pool = top_nums[:min(10, len(top_nums))]
        num_hot = min(3, variant_size, len(hot_pool))
        variant.extend(random.sample(hot_pool, num_hot))
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in variant]
            if rest_pool:
                weights = [all_numbers_with_freq.get(n, 1) for n in rest_pool]
                variant.extend(weighted_sample_unique(rest_pool, weights, remaining))
    
    # Strategy: Cold-Hot Hybrid
    elif strategy_key == "cold_hot_hybrid":
        num_hot = variant_size // 2
        num_cold = variant_size - num_hot
        
        hot_pool = top_nums[:len(top_nums)//2]
        cold_pool = [n for n in top_nums if n not in hot_pool]
        
        if hot_pool:
            variant.extend(random.sample(hot_pool, min(num_hot, len(hot_pool))))
        if cold_pool and num_cold > 0:
            variant.extend(random.sample(cold_pool, min(num_cold, len(cold_pool))))
    
    # Strategy: Golden Pairs/Triplets
    elif strategy_key == "golden_pairs":
        base_used = set()
        if use_triplets and top_triplets and variant_size >= 3:
            top_combo = list(top_triplets.keys())[0] if top_triplets else None
            if top_combo:
                variant.extend(top_combo)
                base_used.update(top_combo)
        elif top_pairs:
            top_pair = list(top_pairs.keys())[0] if top_pairs else None
            if top_pair:
                variant.extend(top_pair)
                base_used.update(top_pair)
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in base_used]
            if rest_pool:
                variant.extend(random.sample(rest_pool, min(remaining, len(rest_pool))))
    
    # Strategy: Parity Balance
    elif strategy_key == "parity_balance":
        even_nums = [n for n in top_nums if n % 2 == 0]
        odd_nums = [n for n in top_nums if n % 2 == 1]
        
        num_even = variant_size // 2
        num_odd = variant_size - num_even
        
        if even_nums:
            variant.extend(random.sample(even_nums, min(num_even, len(even_nums))))
        if odd_nums:
            variant.extend(random.sample(odd_nums, min(num_odd, len(odd_nums))))
    
    # Strategy: Quadrant Force
    elif strategy_key == "quadrant_force":
        q1 = [n for n in top_nums if n <= max_num // 4]
        q2 = [n for n in top_nums if max_num // 4 < n <= max_num // 2]
        q3 = [n for n in top_nums if max_num // 2 < n <= 3 * max_num // 4]
        q4 = [n for n in top_nums if n > 3 * max_num // 4]
        
        quadrants = [q for q in [q1, q2, q3, q4] if q]
        nums_per_quad = max(1, variant_size // len(quadrants)) if quadrants else 1
        
        for q in quadrants:
            if len(variant) < variant_size and q:
                variant.extend(random.sample(q, min(nums_per_quad, len(q), variant_size - len(variant))))
    
    # Strategy: Return Age
    elif strategy_key == "return_age":
        aged_nums = sorted(cold_data.items(), key=lambda x: x[1], reverse=True)
        aged_pool = [n for n, age in aged_nums if n in top_nums and age > 5][:variant_size]
        
        if aged_pool:
            num_aged = min(variant_size // 2, len(aged_pool))
            variant.extend(random.sample(aged_pool, num_aged))
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in variant]
            if rest_pool:
                variant.extend(random.sample(rest_pool, min(remaining, len(rest_pool))))
    
    # Strategy: Consecutive Pair
    elif strategy_key == "consecutive_pair":
        consecutive_found = False
        for i, n in enumerate(top_nums[:-1]):
            if top_nums[i+1] == n + 1:
                variant.extend([n, n+1])
                consecutive_found = True
                break
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in variant]
            if rest_pool:
                variant.extend(random.sample(rest_pool, min(remaining, len(rest_pool))))
    
    # Strategy: Frequency Neighbors
    elif strategy_key == "frequency_neighbors":
        if sorted_freq_keys:
            seed = random.choice(sorted_freq_keys[:20])
            variant.append(seed)
            
            neighbors = [n for n in top_nums if abs(n - seed) <= 5 and n != seed]
            if neighbors:
                num_neighbors = min(variant_size // 2, len(neighbors))
                variant.extend(random.sample(neighbors, num_neighbors))
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in variant]
            if rest_pool:
                variant.extend(random.sample(rest_pool, min(remaining, len(rest_pool))))
    
    # Strategy: Cold Booster
    elif strategy_key == "cold_booster":
        if cold_candidates:
            num_cold = min(variant_size // 3, len(cold_candidates))
            variant.extend(random.sample(cold_candidates, num_cold))
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in variant]
            if rest_pool:
                variant.extend(random.sample(rest_pool, min(remaining, len(rest_pool))))
    
    # Strategy: Average Sum Weighted
    elif strategy_key == "average_sum_weighted":
        target_sum = (max_num * variant_size) // 2
        weights = [1.0 / (1 + abs(n - target_sum / variant_size)) for n in top_nums]
        variant = weighted_sample_unique(top_nums, weights, variant_size)
    
    # Strategy: History Adherence
    elif strategy_key == "history_adherence":
        recent_rounds = historic_rounds[-st.session_state.history_depth:] if historic_rounds else []
        recent_nums = []
        for r in recent_rounds:
            recent_nums.extend(r)
        recent_freq = Counter(recent_nums)
        
        pool_with_recent = [n for n in top_nums if n in recent_freq]
        if pool_with_recent:
            weights = [recent_freq.get(n, 1) for n in pool_with_recent]
            variant = weighted_sample_unique(pool_with_recent, weights, min(variant_size, len(pool_with_recent)))
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in variant]
            if rest_pool:
                variant.extend(random.sample(rest_pool, min(remaining, len(rest_pool))))
    
    # Strategy: Mix Strategy
    elif strategy_key == "mix_strategy":
        available_strategies = ["hot_numbers", "cold_hot_hybrid", "weighted_frequency", "parity_balance"]
        chosen_strat = random.choice(available_strategies)
        return generate_variant_by_strategy(chosen_strat, top_nums, variant_size, exclude_numbers, max_num, cold_data, top_pairs, top_triplets, cold_candidates, historic_rounds, avg_reps, use_triplets)
    
    # Strategy: Hot/Cold Ratio 70/30
    elif strategy_key == "hot_cold_ratio":
        num_hot = int(variant_size * 0.7)
        num_cold = variant_size - num_hot
        
        hot_pool = top_nums[:len(top_nums)//2]
        cold_pool = [n for n in top_nums if n not in hot_pool]
        
        if hot_pool:
            variant.extend(random.sample(hot_pool, min(num_hot, len(hot_pool))))
        if cold_pool and num_cold > 0:
            variant.extend(random.sample(cold_pool, min(num_cold, len(cold_pool))))
    
    # Strategy: Low Numbers Gravitation
    elif strategy_key == "low_numbers_gravitation":
        low_pool = [n for n in top_nums if n <= max_num // 3]
        num_low = min(variant_size // 2, len(low_pool))
        
        if low_pool:
            variant.extend(random.sample(low_pool, num_low))
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in variant]
            if rest_pool:
                variant.extend(random.sample(rest_pool, min(remaining, len(rest_pool))))
    
    # Strategy: Quadrant Mirroring
    elif strategy_key == "quadrant_mirroring":
        if historic_rounds:
            last_round = historic_rounds[-1]
            last_quadrants = []
            for n in last_round:
                if n <= max_num // 4:
                    last_quadrants.append(1)
                elif n <= max_num // 2:
                    last_quadrants.append(2)
                elif n <= 3 * max_num // 4:
                    last_quadrants.append(3)
                else:
                    last_quadrants.append(4)
            
            for q in set(last_quadrants):
                if q == 1:
                    pool = [n for n in top_nums if n <= max_num // 4 and n not in variant]
                elif q == 2:
                    pool = [n for n in top_nums if max_num // 4 < n <= max_num // 2 and n not in variant]
                elif q == 3:
                    pool = [n for n in top_nums if max_num // 2 < n <= 3 * max_num // 4 and n not in variant]
                else:
                    pool = [n for n in top_nums if n > 3 * max_num // 4 and n not in variant]
                
                if pool and len(variant) < variant_size:
                    variant.append(random.choice(pool))
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in variant]
            if rest_pool:
                variant.extend(random.sample(rest_pool, min(remaining, len(rest_pool))))
    
    # Strategy: Forced Repetitions
    elif strategy_key == "forced_repetitions":
        if historic_rounds and avg_reps > 0:
            last_round = set(historic_rounds[-1])
            repeat_pool = [n for n in last_round if n in top_nums]
            
            num_repeat = min(avg_reps, len(repeat_pool), variant_size)
            if repeat_pool:
                variant.extend(random.sample(repeat_pool, num_repeat))
        
        remaining = variant_size - len(variant)
        if remaining > 0:
            rest_pool = [n for n in top_nums if n not in variant]
            if rest_pool:
                variant.extend(random.sample(rest_pool, min(remaining, len(rest_pool))))
    
    # Strategy: Stratified Mix (doar pentru 4/4)
    elif strategy_key == "stratified_mix":
        if variant_size != 4 or len(sorted_freq_keys) < 25:
            weights = [all_numbers_with_freq.get(n, 1) for n in top_nums]
            variant = weighted_sample_unique(top_nums, weights, variant_size)
        else:
            pool_15 = set(sorted_freq_keys[:15])
            pool_16_20 = set(sorted_freq_keys[15:20])
            pool_21_25 = set(sorted_freq_keys[20:25])
            all_top_n_set = set(top_nums)
            pool_rest = all_top_n_set - (pool_15 | pool_16_20 | pool_21_25)
            
            if pool_15 and pool_16_20 and pool_21_25 and pool_rest:
                variant.append(random.choice(list(pool_15)))
                variant.append(random.choice(list(pool_16_20)))
                variant.append(random.choice(list(pool_21_25)))
                variant.append(random.choice(list(pool_rest)))
            else:
                weights = [all_numbers_with_freq.get(n, 1) for n in top_nums]
                variant = weighted_sample_unique(top_nums, weights, variant_size)
    
    # Default fallback
    else:
        variant = random.sample(top_nums, variant_size)
    
    # Ensure unique and correct size
    variant = list(set(variant))
    if len(variant) < variant_size:
        rest_pool = [n for n in top_nums if n not in variant]
        if rest_pool:
            variant.extend(random.sample(rest_pool, min(variant_size - len(variant), len(rest_pool))))
    
    return variant[:variant_size]


# --- Secțiunea 1: Configurare & Încarcare date ---
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

# --- Secțiunea 2: Configurare filtre ---
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
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
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
                    
                    if num_generated % 50 == 0:
                        progress = min(num_generated / num_variants, 1.0)
                        progress_bar.progress(progress)
                        status_text.text(f"Generare: {num_generated}/{num_variants} variante ({attempts} încercări)")

        progress_bar.progress(1.0)
        status_text.text(f"Finalizat: {num_generated}/{num_variants} variante")
        
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

# --- Secțiunea 4: Preview & Export ---

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


    # BUTONUL DE DESCARCARE
    st.download_button("⬇️ Descarcă variantele (TXT)", txt_output, "variante_generate_eficient.txt", "text/plain")
    
    # Statistici suplimentare
    if st.session_state.variants:
        st.markdown("---")
        st.subheader("📊 Analiză Detaliată")
        
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            sums = [sum(v) for v in st.session_state.variants]
            st.metric("Suma medie", f"{np.mean(sums):.1f}")
            st.metric("Suma min/max", f"{min(sums)} / {max(sums)}")
        
        with col_stats2:
            even_counts = [sum(1 for n in v if n % 2 == 0) for v in st.session_state.variants]
            st.metric("Medie numere pare", f"{np.mean(even_counts):.1f}")
            st.metric("Medie numere impare", f"{variant_size - np.mean(even_counts):.1f}")
        
        with col_stats3:
            ranges = [max(v) - min(v) for v in st.session_state.variants]
            st.metric("Range mediu", f"{np.mean(ranges):.1f}")
            st.metric("Range min/max", f"{min(ranges)} / {max(ranges)}")
        
        # Analiză distribuție pe cadrane
        st.markdown("### 🗺️ Distribuție pe Cadrane")
        quadrant_dist = {1: 0, 2: 0, 3: 0, 4: 0}
        for v in st.session_state.variants:
            for n in v:
                if n <= max_num // 4:
                    quadrant_dist[1] += 1
                elif n <= max_num // 2:
                    quadrant_dist[2] += 1
                elif n <= 3 * max_num // 4:
                    quadrant_dist[3] += 1
                else:
                    quadrant_dist[4] += 1
        
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        total_nums = sum(quadrant_dist.values())
        
        with col_q1:
            pct = (quadrant_dist[1] / total_nums * 100) if total_nums > 0 else 0
            st.metric(f"Q1 (1-{max_num//4})", f"{quadrant_dist[1]}", f"{pct:.1f}%")
        with col_q2:
            pct = (quadrant_dist[2] / total_nums * 100) if total_nums > 0 else 0
            st.metric(f"Q2 ({max_num//4+1}-{max_num//2})", f"{quadrant_dist[2]}", f"{pct:.1f}%")
        with col_q3:
            pct = (quadrant_dist[3] / total_nums * 100) if total_nums > 0 else 0
            st.metric(f"Q3 ({max_num//2+1}-{3*max_num//4})", f"{quadrant_dist[3]}", f"{pct:.1f}%")
        with col_q4:
            pct = (quadrant_dist[4] / total_nums * 100) if total_nums > 0 else 0
            st.metric(f"Q4 ({3*max_num//4+1}-{max_num})", f"{quadrant_dist[4]}", f"{pct:.1f}%")
        
        # Grafic vizualizare frecvență numere generate
        st.markdown("### 📊 Frecvența Numerelor Generate")
        
        freq_df = pd.DataFrame(
            sorted(generated_freq.items(), key=lambda x: x[1], reverse=True)[:30],
            columns=["Număr", "Frecvență"]
        )
        
        import plotly.express as px
        fig = px.bar(
            freq_df, 
            x="Număr", 
            y="Frecvență",
            title=f"Top 30 Numere Cel Mai Frecvent Generate",
            color="Frecvență",
            color_continuous_scale="viridis"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Analiză consecutive
        st.markdown("### ⛓️ Analiză Perechi Consecutive")
        consecutive_count = 0
        for v in st.session_state.variants:
            sorted_v = sorted(v)
            for i in range(len(sorted_v) - 1):
                if sorted_v[i+1] == sorted_v[i] + 1:
                    consecutive_count += 1
                    break
        
        consecutive_pct = (consecutive_count / len(st.session_state.variants) * 100)
        st.info(f"**{consecutive_count}** variante ({consecutive_pct:.1f}%) conțin cel puțin o pereche consecutivă")
        
        # Analiză perechi populare
        st.markdown("### 🥇 Top Perechi în Variante Generate")
        gen_pairs = Counter()
        for v in st.session_state.variants:
            sorted_v = sorted(v)
            for pair in itertools.combinations(sorted_v, 2):
                gen_pairs[pair] += 1
        
        top_gen_pairs = gen_pairs.most_common(15)
        if top_gen_pairs:
            pairs_text = ", ".join([f"({p[0]},{p[1]}): {cnt}x" for p, cnt in top_gen_pairs])
            st.info(f"**Top 15 perechi:** {pairs_text}")
        
        # Comparație cu istoricul
        if st.session_state.pair_frequency:
            st.markdown("### 🔍 Comparație cu Istoricul")
            
            hist_top_pairs = list(st.session_state.pair_frequency.keys())[:10]
            gen_top_pairs = [p for p, _ in top_gen_pairs[:10]]
            
            overlap = len(set(hist_top_pairs) & set(gen_top_pairs))
            st.info(f"**{overlap}/10** din perechile cele mai frecvente din istoric apar și în top 10 generate")
        
        # Opțiuni export avansate
        st.markdown("---")
        st.subheader("📤 Opțiuni Export Avansate")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            # Export CSV cu detalii
            csv_data = []
            for i, v in enumerate(st.session_state.variants):
                sorted_v = sorted(v)
                csv_data.append({
                    "ID": i+1,
                    "Varianta": " ".join(map(str, sorted_v)),
                    "Suma": sum(v),
                    "Pare": sum(1 for n in v if n % 2 == 0),
                    "Impare": sum(1 for n in v if n % 2 == 1),
                    "Range": max(v) - min(v),
                    "Min": min(v),
                    "Max": max(v)
                })
            
            csv_df = pd.DataFrame(csv_data)
            csv_output = csv_df.to_csv(index=False)
            
            st.download_button(
                "⬇️ Descarcă CSV cu Statistici",
                csv_output,
                "variante_cu_statistici.csv",
                "text/csv"
            )
        
        with col_exp2:
            # Export doar numere (fără ID)
            simple_export = "\n".join([" ".join(map(str, sorted(v))) for v in st.session_state.variants])
            
            st.download_button(
                "⬇️ Descarcă Doar Numere",
                simple_export,
                "variante_simple.txt",
                "text/plain"
            )
        
        # Filtru variante după criterii
        st.markdown("---")
        st.subheader("🔎 Filtru Variante După Criterii")
        
        with st.expander("Aplică filtre personalizate"):
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                suma_min = st.number_input("Suma minimă", 0, max_num * variant_size, 0)
                suma_max = st.number_input("Suma maximă", 0, max_num * variant_size, max_num * variant_size)
            
            with col_f2:
                pare_min = st.number_input("Număr minim de pare", 0, variant_size, 0)
                pare_max = st.number_input("Număr maxim de pare", 0, variant_size, variant_size)
            
            with col_f3:
                range_min = st.number_input("Range minim", 0, max_num, 0)
                range_max = st.number_input("Range maxim", 0, max_num, max_num)
            
            if st.button("🔍 Aplică Filtre"):
                filtered_variants = []
                for v in st.session_state.variants:
                    suma = sum(v)
                    pare = sum(1 for n in v if n % 2 == 0)
                    rng = max(v) - min(v)
                    
                    if (suma_min <= suma <= suma_max and 
                        pare_min <= pare <= pare_max and 
                        range_min <= rng <= range_max):
                        filtered_variants.append(v)
                
                if filtered_variants:
                    st.success(f"✅ {len(filtered_variants)} variante îndeplinesc criteriile")
                    
                    # Export variante filtrate
                    filtered_export = "\n".join([
                        f"{i+1}, {' '.join(map(str, sorted(v)))}" 
                        for i, v in enumerate(filtered_variants)
                    ])
                    
                    st.download_button(
                        "⬇️ Descarcă Variante Filtrate",
                        filtered_export,
                        "variante_filtrate.txt",
                        "text/plain",
                        key="filtered_download"
                    )
                    
                    # Preview filtrate
                    preview_filtered = min(10, len(filtered_variants))
                    st.text(f"Preview primele {preview_filtered} variante filtrate:")
                    for i, v in enumerate(filtered_variants[:preview_filtered]):
                        st.text(f"{i+1}. {' '.join(map(str, sorted(v)))}")
                else:
                    st.warning("⚠️ Nicio variantă nu îndeplinește criteriile selectate")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>🎯 Generator Variante Keno Avansat</strong></p>
    <p>Analiză statistică multi-nivel | 19 strategii disponibile | Export flexibil</p>
    <p style='font-size: 0.8em;'>Folosește acest tool în mod responsabil. Rezultatele sunt generate statistic și nu garantează câștiguri.</p>
</div>
""", unsafe_allow_html=True)