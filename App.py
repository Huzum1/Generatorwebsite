import streamlit as st
import pandas as pd
from collections import Counter
import random
import itertools
import numpy as np # Adaugat pentru mediana

st.set_page_config(page_title="Generator Variante Keno Avansat", page_icon="🎯", layout="wide")

st.title("🎯 Generator Variante Keno Avansat & Ultra-Eficient")

st.markdown("""
Analiză statistică multi-nivel (frecvență, perechi, sumă, istoric) pentru a genera variante loto
cu eficiență sporită. **Toate variantele sunt filtrate strict** pentru a respecta tiparele statistice de bază (Sumă, Par/Impar, Consecutivitate).
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
if "sum_range" not in st.session_state:
    st.session_state.sum_range = (0, 1000)
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


# --- Funcții Avansate de Analiză ---

def analyze_pairs_triplets(rounds, k_size):
    """Calculeaza frecventa perechilor si tripletelor extrase impreuna."""
    pair_counts = Counter()
    triplet_counts = Counter()
    
    for round_nums in rounds:
        sorted_nums = sorted(round_nums)
        # Perechi
        for pair in itertools.combinations(sorted_nums, 2):
            pair_counts[tuple(sorted(pair))] += 1
        # Triplete (doar daca varianta k e suficient de mare)
        if k_size >= 3:
             for triplet in itertools.combinations(sorted_nums, 3):
                triplet_counts[tuple(sorted(triplet))] += 1
    
    sorted_pairs = dict(sorted(pair_counts.items(), key=lambda x: x[1], reverse=True))
    sorted_triplets = dict(sorted(triplet_counts.items(), key=lambda x: x[1], reverse=True))
    
    return sorted_pairs, sorted_triplets

def analyze_sum(rounds):
    """Calculeaza intervalul de suma cel mai frecvent (percentila 25-75)."""
    sums = [sum(r) for r in rounds]
    if not sums:
        return (0, st.session_state.max_number * 20)
    
    sums_df = pd.Series(sums)
    q25 = int(sums_df.quantile(0.25))
    q75 = int(sums_df.quantile(0.75))
    st.session_state.sum_range = (q25, q75)
    return (q25, q75)

def analyze_cold_streak(rounds, max_num):
    """Calculeaza cate runde nu a mai fost extras fiecare numar (vârsta)."""
    cold_streak = {}
    all_nums = set(range(1, max_num + 1))
    
    for num in all_nums:
        age = 0
        found = False
        for round_nums in reversed(rounds):
            if num in round_nums:
                found = True
                break
            age += 1
        cold_streak[num] = age
    
    return dict(sorted(cold_streak.items(), key=lambda x: x[1], reverse=True))

def analyze_repetitions(rounds):
    """Calculeaza media de numere care se repeta din runda N-1 in runda N."""
    repetitions = []
    if len(rounds) < 2: return 0
    
    for i in range(1, len(rounds)):
        prev_round = set(rounds[i-1])
        current_round = set(rounds[i])
        repetitions.append(len(prev_round.intersection(current_round)))
        
    if not repetitions: return 0
    return round(np.median(repetitions)) # Folosim mediana pentru a evita extremele


def proceseaza_runde(lines, variant_size):
    all_numbers = []
    rounds_data = []
    
    for line in lines:
        try:
            numbers = [int(x.strip()) for x in line.split(",") if x.strip()]
            
            if any(n > st.session_state.max_number or n < 1 for n in numbers):
                st.error(f"Eroare: Runda conține numere în afara intervalului 1 la {st.session_state.max_number}. Verificați datele de intrare.")
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
    st.session_state.sum_range = analyze_sum(rounds_data)
    st.session_state.avg_reps = analyze_repetitions(rounds_data) # NOU: Mediana Repetitii
    
    return frequency, sorted_freq, all_numbers

# --- Funcție Ajutătoare pentru Frecvență Ponderată Fără Duplicări ---
def weighted_sample_unique(population, weights, k):
    """Simulează extragerea ponderată FĂRĂ repetiție."""
    sample = []
    available = list(population)
    current_weights = list(weights)

    for _ in range(k):
        if len(available) == 0:
            break
        if sum(current_weights) <= 0:
            # Fallback for zero weights
            sample.extend(random.sample(available, k - len(sample)))
            break
            
        chosen = random.choices(available, weights=current_weights, k=1)[0]
        sample.append(chosen)

        idx = available.index(chosen)
        available.pop(idx)
        current_weights.pop(idx)
        
    return sample

# --- Funcții de Filtrare de Calitate (NOU ȘI OBLIGATORIU) ---
def is_valid_variant(variant, q1, q3, max_num):
    """Aplică toate filtrele statistice obligatorii."""
    
    variant_size = len(variant)
    variant_set = set(variant)
    
    # 1. Filtru Unicitate și Mărime
    if len(variant_set) != variant_size: return False
    
    # 2. Filtru Sumă Optimă (Q25 - Q75)
    current_sum = sum(variant)
    if not (q1 <= current_sum <= q3): return False
    
    # 3. Filtru Par-Impar Echilibrat (±1 sau ±2)
    num_par = len([n for n in variant if n % 2 == 0])
    num_impar = variant_size - num_par
    max_diff = 2 if variant_size > 5 else 1 # Toleranță mai mare la variante mari
    if abs(num_par - num_impar) > max_diff: return False
    
    # 4. Filtru Numere Consecutive (Max 3)
    consecutive_count = 0
    max_consecutive = 0
    sorted_variant = sorted(variant)
    
    for i in range(1, variant_size):
        if sorted_variant[i] == sorted_variant[i-1] + 1:
            consecutive_count += 1
            max_consecutive = max(max_consecutive, consecutive_count)
        else:
            consecutive_count = 0
    
    if max_consecutive >= 3: return False 

    # 5. Filtru Răspândire (Spread) - Opțional (activat doar pentru variante mari)
    if variant_size >= 8:
        spread = sorted_variant[-1] - sorted_variant[0]
        min_spread = max_num * 0.75 # Răspândirea trebuie să acopere cel puțin 75% din grilă
        if spread < min_spread: return False

    return True


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
        value=5,
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
                                help=f"Exemplu: 1,12,25,30,44,51,68,79 (pentru loteria de la 1 la {st.session_state.max_number})")

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
        st.success(f"✅ Analiză completă pe **{len(st.session_state.historic_rounds)}** runde.")
        st.info(f"Suma optimă (Q25-Q75): **{st.session_state.sum_range[0]}** - **{st.session_state.sum_range[1]}** | Repetiții mediane runda N-1: **{st.session_state.avg_reps}**")


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


# Lista completa de strategii
ALL_STRATEGIES = {
    "🎯 Standard (Aleatoriu Ponderat)": "standard", # Ponderat
    "🔥 Hot Numbers (3 din top 10 + rest ponderat)": "hot_numbers", # Ponderat
    "❄️ Cold-Hot Hybrid (Mix 50/50 ponderat)": "cold_hot_hybrid", # Ponderat
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
    "🔄 Aderență Forțată la Runda Precedentă (Repetiții Istorice)": "forced_repetitions", # NOU
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


# --- Functie pentru generarea variantei pe baza strategiei (logica detaliata) ---
def generate_variant_by_strategy(strategy_key, top_nums, variant_size, exclude_numbers, max_num, q1, q3, cold_data, top_pairs, top_triplets, quadrants, cold_candidates, historic_rounds, avg_reps, use_triplets):
    
    if len(top_nums) < variant_size: return []

    # Bază pentru extragerea ponderată generalizată
    general_weights = [st.session_state.frequency.get(n, 1) for n in top_nums]
    
    variant_set = set()

    # --- Strat. 1: Standard (Acum Ponderat) ---
    if strategy_key == "standard":
        variant = weighted_sample_unique(top_nums, general_weights, variant_size)
        variant_set.update(variant)

    # --- Strat. 2: Hot Numbers (Ponderat) ---
    elif strategy_key == "hot_numbers":
        top10 = top_nums[:min(10, len(top_nums))]
        top10_weights = [st.session_state.frequency.get(n, 1) for n in top10]
        rest = [n for n in top_nums if n not in top10]
        rest_weights = [st.session_state.frequency.get(n, 1) for n in rest]
        
        num_hot = min(3, variant_size, len(top10))
        num_rest = variant_size - num_hot
        
        hot_part = weighted_sample_unique(top10, top10_weights, num_hot)
        rest_part = weighted_sample_unique(rest, rest_weights, num_rest)
        variant_set.update(hot_part + rest_part)
        
    # --- Strat. 3: Cold-Hot Hybrid (Ponderat) ---
    elif strategy_key == "cold_hot_hybrid":
        half = variant_size // 2
        top20 = top_nums[:min(20, len(top_nums))]
        top20_weights = [st.session_state.frequency.get(n, 1) for n in top20]
        rest = [n for n in top_nums if n not in top20]
        rest_weights = [st.session_state.frequency.get(n, 1) for n in rest]
        
        num_top20 = min(half, len(top20))
        num_rest = variant_size - num_top20
        
        top20_part = weighted_sample_unique(top20, top20_weights, num_top20)
        rest_part = weighted_sample_unique(rest, rest_weights, num_rest)
        variant_set.update(top20_part + rest_part)

    # --- Strat. 4: Frecvență Ponderată ---
    elif strategy_key == "weighted_frequency":
        variant = weighted_sample_unique(top_nums, general_weights, variant_size)
        variant_set.update(variant)

    # --- Strat. 5: Perechi/Triplete de Aur (Logică Ponderată și Triplete) ---
    elif strategy_key == "golden_pairs":
        base_size = 3 if use_triplets and variant_size >= 3 else 2
        base_pool = top_triplets if base_size == 3 else top_pairs
        
        if not base_pool or variant_size < base_size:
            return weighted_sample_unique(top_nums, general_weights, variant_size)

        # Selecție ponderată a bazei (mai frecvente au șanse mai mari)
        base_items = list(base_pool.keys())
        base_weights = list(base_pool.values())
        
        chosen_base = random.choices(base_items, weights=base_weights, k=1)[0]
        variant_set.update(chosen_base)
        
        num_left = variant_size - len(variant_set)
        
        if num_left > 0:
            available_rest = [n for n in top_nums if n not in variant_set]
            weights_rest = [st.session_state.frequency.get(n, 1) for n in available_rest]
            variant_set.update(weighted_sample_unique(available_rest, weights_rest, num_left))
            
    # --- Strat. 6: Par-Impar Echilibrat ---
    elif strategy_key == "parity_balance":
        num_par = variant_size // 2
        num_impar = variant_size - num_par
        par_nums = [n for n in top_nums if n % 2 == 0]
        impar_nums = [n for n in top_nums if n % 2 != 0]
        
        par_weights = [st.session_state.frequency.get(n, 1) for n in par_nums]
        impar_weights = [st.session_state.frequency.get(n, 1) for n in impar_nums]

        variant_set.update(weighted_sample_unique(par_nums, par_weights, min(num_par, len(par_nums))))
        
        # Extragem din Impar (și completăm cu ce a rămas)
        remaining_impar = [n for n in impar_nums if n not in variant_set]
        weights_impar = [st.session_state.frequency.get(n, 1) for n in remaining_impar]
        variant_set.update(weighted_sample_unique(remaining_impar, weights_impar, min(num_impar, len(remaining_impar))))

        # Completare finală cu orice numere fierbinți (ar trebui să fie rar)
        if len(variant_set) < variant_size:
            remaining = variant_size - len(variant_set)
            available_pool = [n for n in top_nums if n not in variant_set]
            weights_pool = [st.session_state.frequency.get(n, 1) for n in available_pool]
            variant_set.update(weighted_sample_unique(available_pool, weights_pool, remaining))

    # --- Strat. 7: Câmpuri de Forță ---
    elif strategy_key == "quadrant_force":
        q_size = max_num // 4
        quadrant_limits = [q_size, q_size * 2, q_size * 3, max_num]
        
        # Decide câte numere să extragi din fiecare cadran (cu variație)
        target_counts = [random.randint(0, variant_size // 2 + 1) for _ in range(4)]
        
        # Normalizăm suma la variant_size (dacă e prea mare/m