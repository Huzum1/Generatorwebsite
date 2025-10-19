import streamlit as st
import pandas as pd
from collections import Counter
import random
import itertools

st.set_page_config(page_title="Generator Variante Keno Avansat", page_icon="🎯", layout="wide")

st.title("🎯 Generator Variante Keno Avansat & Flexibil")

st.markdown("""
Analiză statistică multi-nivel (frecvență, perechi, sumă, istoric) pentru a genera variante loto
cu eficiență sporită, adaptabilă oricărui Keno (ex: 20/80, 20/90).
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


# --- Funcții Avansate de Analiză ---

def analyze_pairs(rounds, max_num):
    """Calculeaza frecventa perechilor extrase impreuna."""
    pair_counts = Counter()
    for round_nums in rounds:
        sorted_nums = sorted(round_nums)
        for pair in itertools.combinations(sorted_nums, 2):
            pair_counts[tuple(sorted(pair))] += 1
    
    sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_pairs)

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


def proceseaza_runde(lines):
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
            st.error(f"Eroare la procesarea liniei: '{line}'. Asigură-te că sunt doar numere întregi separate prin virgulă.")
            return None, None, None
            
    if not rounds_data:
         return None, None, None

    frequency = Counter(all_numbers)
    sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    st.session_state.frequency = dict(sorted_freq)
    st.session_state.historic_rounds = rounds_data

    st.session_state.pair_frequency = analyze_pairs(rounds_data, st.session_state.max_number)
    st.session_state.sum_range = analyze_sum(rounds_data)

    return frequency, sorted_freq, all_numbers

# --- Secțiunea 1: Configurare & Încarcare date ---
st.header("1. Configurare Loterie & Încărcare Date")

col_max, col_round = st.columns(2)
with col_max:
    st.session_state.max_number = st.number_input(
        "Numărul maxim al loteriei (ex: 80, 90)",
        min_value=1,
        value=80,
        step=1
    )
with col_round:
    st.info(f"Domeniul de lucru stabilit: **1 la {st.session_state.max_number}**")


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
        results = proceseaza_runde(lines)
    elif manual_input.strip():
        lines = [line.strip() for line in manual_input.split("\n") if line.strip()]
        results = proceseaza_runde(lines)
    else:
        st.warning("⚠️ Te rugăm să încarci sau să introduci datele.")
        results = None

    if results is not None:
        frequency, sorted_freq, all_numbers = results
        st.success(f"✅ Analiză completă pe **{len(st.session_state.historic_rounds)}** runde.")
        rounds_df = pd.DataFrame([[i+1, ",".join(map(str, r))] for i, r in enumerate(st.session_state.historic_rounds)], columns=["Runda", "Numere"])
        st.dataframe(rounds_df, use_container_width=True, hide_index=True)
        st.info(f"Suma optimă a variantelor (Q25-Q75) este între: **{st.session_state.sum_range[0]}** și **{st.session_state.sum_range[1]}**")

st.markdown("---")

# --- Secțiunea 2: Configurare filtre ---
st.header("2. Configurare Filtre (Rece & Cald)")

col1, col2 = st.columns(2)
exclude_numbers = set()

with col1:
    st.subheader("❄️ Exclude cele mai reci numere")
    exclude_mode = st.radio("Cum vrei să excluzi?", ["🔢 Automata", "✍️ Manual", "🔀 Ambele"], horizontal=True)
    auto_exclude = set()

    if exclude_mode in ["🔢 Automata", "🔀 Ambele"]:
        auto_cold_count = st.selectbox("Exclude topul celor mai reci N numere", [0, 5, 10, 15, 20, 30], index=0)
        if st.session_state.frequency and auto_cold_count > 0:
            sorted_freq_items = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
            # Excludem de la coada listei de frecventa (cele mai rare)
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
    min_top_count = st.session_state.max_number // 2 if st.session_state.max_number <= 20 else 20
    top_count = st.slider("Câte numere fierbinți să păstrezi?", 10, st.session_state.max_number, min(st.session_state.max_number, 50), 1)
    
    if st.session_state.frequency:
        sorted_freq_items = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
        # Filtram top_count, excludem numerele "reci" si numerele excluse manual
        top_numbers = [x[0] for x in sorted_freq_items if x[0] not in exclude_numbers][:top_count]
        st.session_state.top_numbers = top_numbers
        st.success(f"✅ **{len(top_numbers)}** numere disponibile pentru generare.")
        
        # Analiza de varsta (pentru afisare)
        cold_data = analyze_cold_streak(st.session_state.historic_rounds, st.session_state.max_number)
        cold_candidates_info = [(num, age) for num, age in cold_data.items() if num not in top_numbers and num not in exclude_numbers]
        if cold_candidates_info:
            st.markdown(f"**Cei mai reci (disponibili):** {', '.join([f'{n}({a}r)' for n, a in cold_candidates_info[:5]])}")

st.markdown("---")

# --- Secțiunea 3: Strategii de generare ---
st.header("3. Strategii de Generare Avansată")

col_size, col_num = st.columns(2)

with col_size:
    variant_size = st.slider(
        "📏 Alege mărimea variantei (k/k, ex: 5/5, 8/8)",
        min_value=1, 
        max_value=9, 
        value=5,
        step=1
    )

with col_num:
    num_variants = st.number_input("Câte variante unice să generezi?", 10, 10000, 1000, 10)

# Lista completa de strategii
ALL_STRATEGIES = {
    "🎯 Standard (numere aleatoare din Top N)": "standard",
    "🔥 Hot Numbers (3 din top 10 + rest aleatoriu)": "hot_numbers",
    "❄️ Cold-Hot Hybrid (jumătate top 20, jumătate rest)": "cold_hot_hybrid",
    "⚡ Frecvență Ponderată (fără duplicări)": "weighted_frequency",
    "🥇 Perechi de Aur (Bazat pe Top Perechi)": "golden_pairs",
    "🔄 Par-Impar Echilibrat (~50/50)": "parity_balance",
    "🗺️ Câmpuri de Forță (Minimum 3 Cadrane)": "quadrant_force",
    "🕰️ Aproape de Întoarcere (Include numere 'în vârstă')": "return_age",
    "⛓️ Numere Consecutive (Asigură o pereche)": "consecutive_pair",
    "⭐ Frecvență & Vecinătate": "frequency_neighbors",
    "💡 Restantierul (Cold Booster)": "cold_booster",
    "⚖️ Somă Medie (Selecție Ponderată pe Suma Optimă)": "average_sum_weighted",
    "🧬 Adâncimea Istoriei (Aderență la ultimele 50 de runde)": "history_adherence",
    "🧪 Mix Strategy (Combinație aleatorie a strategiilor)": "mix_strategy",
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
            sample.extend(random.sample(available, k - len(sample)))
            break
            
        chosen = random.choices(available, weights=current_weights, k=1)[0]
        sample.append(chosen)

        idx = available.index(chosen)
        available.pop(idx)
        current_weights.pop(idx)
        
    return sample

# --- Functie pentru generarea variantei pe baza strategiei (logica detaliata) ---
def generate_variant_by_strategy(strategy_key, top_nums, variant_size, exclude_numbers, max_num, q1, q3, historic_rounds_set, cold_data, top_pairs, quadrants, cold_candidates):
    
    # Asigură-te că avem suficiente numere pentru generare
    if len(top_nums) < variant_size:
        available_fallback = [n for n in range(1, max_num + 1) if n not in exclude_numbers]
        if len(available_fallback) >= variant_size:
             return random.sample(available_fallback, variant_size)
        return []

    variant = []

    if strategy_key == "standard":
        variant = random.sample(top_nums, variant_size)

    elif strategy_key == "hot_numbers":
        top10 = top_nums[:min(10, len(top_nums))]
        rest = top_nums[10:]
        num_hot = min(3, variant_size, len(top10))
        num_rest = variant_size - num_hot
        
        num_rest = min(num_rest, len(rest))
        
        if num_hot + num_rest < variant_size:
             return random.sample(top_nums, variant_size)
        
        variant = random.sample(top10, num_hot) + random.sample(rest, num_rest)
        
    elif strategy_key == "cold_hot_hybrid":
        half = variant_size // 2
        top20 = top_nums[:min(20, len(top_nums))]; 
        rest = top_nums[min(20, len(top_nums)):]
        
        num_top20 = min(half, len(top20))
        num_rest = variant_size - num_top20
        num_rest = min(num_rest, len(rest))
        
        if num_top20 + num_rest < variant_size:
             return random.sample(top_nums, variant_size)
             
        variant = random.sample(top20, num_top20) + random.sample(rest, num_rest)

    elif strategy_key == "weighted_frequency":
        weights = [st.session_state.frequency.get(n, 1) for n in top_nums]
        variant = weighted_sample_unique(top_nums, weights, variant_size)

    elif strategy_key == "golden_pairs":
        if top_pairs:
            num_pairs = min(random.randint(1, 2), variant_size // 2)
            chosen_pairs = random.sample(top_pairs, num_pairs)
            variant_set = set()
            for pair in chosen_pairs:
                variant_set.update(pair)
                
            num_left = variant_size - len(variant_set)
            if num_left > 0:
                available_rest = [n for n in top_nums if n not in variant_set]
                variant_set.update(random.sample(available_rest, min(num_left, len(available_rest))))
            variant = list(variant_set)
        else:
            variant = random.sample(top_nums, variant_size)

    elif strategy_key == "parity_balance":
        num_par = variant_size // 2
        num_impar = variant_size - num_par
        par_nums = [n for n in top_nums if n % 2 == 0]
        impar_nums = [n for n in top_nums if n % 2 != 0]
        
        variant_set = set(random.sample(par_nums, min(num_par, len(par_nums))))
        remaining = variant_size - len(variant_set)
        if remaining > 0:
            remaining_pool = [n for n in impar_nums if n not in variant_set] + [n for n in par_nums if n not in variant_set]
            variant_set.update(random.sample(remaining_pool, min(remaining, len(remaining_pool))))
        variant = list(variant_set)

    elif strategy_key == "quadrant_force":
        variant_set = set()
        num_quads = min(random.randint(3, 4), variant_size, len(quadrants))
        chosen_quadrants = random.sample(quadrants, num_quads)
        
        for q in chosen_quadrants:
            available_in_q = list(q.intersection(set(top_nums)))
            if available_in_q and len(variant_set) < variant_size:
                variant_set.add(random.choice([n for n in available_in_q if n not in variant_set]))
                
        num_left = variant_size - len(variant_set)
        if num_left > 0:
            available_rest = [n for n in top_nums if n not in variant_set]
            variant_set.update(random.sample(available_rest, min(num_left, len(available_rest))))
        variant = list(variant_set)

    elif strategy_key == "return_age":
        cold_age_candidates = [num for num, age in cold_data.items() if age > 5 and num not in top_nums and num not in exclude_numbers]
        
        num_cold_include = min(random.randint(1, 2), variant_size, len(cold_age_candidates))
        cold_part = random.sample(cold_age_candidates, num_cold_include)
        
        num_hot = variant_size - len(cold_part)
        available_hot = [n for n in top_nums if n not in cold_part]
        hot_part = random.sample(available_hot, min(num_hot, len(available_hot)))
        
        variant = cold_part + hot_part

    elif strategy_key == "consecutive_pair":
        consecutive_pair = None
        random.shuffle(top_nums)
        for n in top_nums:
            if n + 1 in top_nums:
                consecutive_pair = (n, n+1)
                break
        
        if consecutive_pair and variant_size >= 2:
            variant_set = set(consecutive_pair)
            num_left = variant_size - 2
            available_rest = [n for n in top_nums if n not in variant_set]
            variant_set.update(random.sample(available_rest, min(num_left, len(available_rest))))
            variant = list(variant_set)
        else:
             variant = random.sample(top_nums, variant_size)

    elif strategy_key == "frequency_neighbors":
        top5 = top_nums[:min(5, len(top_nums))]
        if not top5: return random.sample(top_nums, variant_size)
        start_num = random.choice(top5)
        variant_set = {start_num}
        
        top15 = top_nums[:min(15, len(top_nums))]
        neighbors = set()
        for n in top15:
            if n - 1 >= 1 and n - 1 not in exclude_numbers: neighbors.add(n - 1)
            if n + 1 <= max_num and n + 1 not in exclude_numbers: neighbors.add(n + 1)
        
        combined_pool = list(set(top_nums[1:]).union(neighbors) - variant_set)
        
        num_left = variant_size - 1
        variant_set.update(random.sample(combined_pool, min(num_left, len(combined_pool))))
        variant = list(variant_set)

    elif strategy_key == "cold_booster":
        num_cold_include = min(random.randint(1, 2), variant_size, len(cold_candidates))
        cold_part = random.sample(cold_candidates, num_cold_include)
        
        num_hot = variant_size - len(cold_part)
        available_hot = [n for n in top_nums if n not in cold_part]
        hot_part = random.sample(available_hot, min(num_hot, len(available_hot)))
        
        variant = cold_part + hot_part

    elif strategy_key == "average_sum_weighted":
        target_sum = (q1 + q3) / 2
        best_variant = []
        best_sum_diff = float('inf')
        
        for _ in range(10): 
            weights = [st.session_state.frequency.get(n, 1) for n in top_nums]
            temp_variant = weighted_sample_unique(top_nums, weights, variant_size)
            current_sum = sum(temp_variant)
            current_diff = abs(current_sum - target_sum)
            
            if current_diff < best_sum_diff and len(temp_variant) == variant_size:
                best_sum_diff = current_diff
                best_variant = temp_variant
                
        variant = best_variant if best_variant and len(best_variant) == variant_size else random.sample(top_nums, variant_size)

    elif strategy_key == "history_adherence":
        num_common = min(random.randint(3, 4), variant_size)
        
        if st.session_state.historic_rounds:
            parent_round = random.choice(st.session_state.historic_rounds[-min(50, len(st.session_state.historic_rounds)):])
            hot_parent_intersection = [n for n in parent_round if n in top_nums]
            
            parent_part = random.sample(hot_parent_intersection, min(num_common, len(hot_parent_intersection)))
            variant_set = set(parent_part)
            
            num_left = variant_size - len(variant_set)
            available_rest = [n for n in top_nums if n not in variant_set]
            
            variant_set.update(random.sample(available_rest, min(num_left, len(available_rest))))
            variant = list(variant_set)
        else:
            variant = random.sample(top_nums, variant_size)

    elif strategy_key == "mix_strategy":
        mix_choices = [
            "standard", "hot_numbers", "weighted_frequency", "parity_balance", "consecutive_pair",
        ]
        strategy_to_run = random.choice(mix_choices)
        
        mixed_result = generate_variant_by_strategy(strategy_to_run, top_nums, variant_size, exclude_numbers, max_num, q1, q3, historic_rounds_set, cold_data, top_pairs, quadrants, cold_candidates)
        variant = [item for item in mixed_result if isinstance(item, int)]


    # Asigură-te că varianta are dimensiunea corectă înainte de return (final fallback)
    if len(variant) != variant_size:
        variant = random.sample(top_nums, variant_size)
        
    return variant


# --- Generare Logică Principală ---
if st.button("🚀 Generează variante"):
    if not st.session_state.top_numbers:
        st.error("❌ Încarcă datele și configurează filtrele în Secțiunile 1 & 2.")
    elif variant_size > len(st.session_state.top_numbers):
        st.error(f"❌ Mărimea variantei ({variant_size}) este mai mare decât numerele disponibile ({len(st.session_state.top_numbers)}). Te rugăm să mărești numărul de numere fierbinți în Secțiunea 2.")
    elif not st.session_state.selected_strategies:
        st.error("❌ Te rugăm să selectezi cel puțin o strategie de generare.")
    else:
        top_nums = st.session_state.top_numbers
        variants = set()
        max_attempts = num_variants * 50
        attempts = 0
        
        max_num = st.session_state.max_number
        q1, q3 = st.session_state.sum_range
        historic_rounds_set = [set(r) for r in st.session_state.historic_rounds]
        cold_data = analyze_cold_streak(st.session_state.historic_rounds, max_num)
        cold_candidates = [num for num, age in cold_data.items() if num not in top_nums and num not in exclude_numbers]
        top_pairs = list(st.session_state.pair_frequency.keys())[:100]
        q_size = max_num // 4
        quadrants = [set(range(1, q_size + 1)), set(range(q_size + 1, q_size * 2 + 1)), set(range(q_size * 2 + 1, q_size * 3 + 1)), set(range(q_size * 3 + 1, max_num + 1))]
        
        strategies_to_use = st.session_state.selected_strategies
        num_strategies = len(strategies_to_use)
        
        while len(variants) < num_variants and attempts < max_attempts:
            attempts += 1
            
            strategy_key = strategies_to_use[attempts % num_strategies]
            
            variant = generate_variant_by_strategy(
                strategy_key, 
                top_nums, 
                variant_size, 
                exclude_numbers, 
                max_num, 
                q1, q3, 
                historic_rounds_set, 
                cold_data, 
                top_pairs, 
                quadrants, 
                cold_candidates
            )
            
            # --- Filtru Unicitate (Singurul rămas) ---
            if len(set(variant)) != variant_size or not variant:
                continue 

            final_variant = tuple(sorted(variant))
            variants.add(final_variant)

        st.session_state.variants = list(variants)
        random.shuffle(st.session_state.variants)
        
        selected_strategy_labels = [k for k, v in ALL_STRATEGIES.items() if v in strategies_to_use]

        st.success(f"✅ Generate **{len(st.session_state.variants)}** variante UNICE ({variant_size}/{variant_size}) în {attempts} încercări, folosind strategiile: **{', '.join(selected_strategy_labels)}**")
        
        if len(st.session_state.variants) < num_variants:
             st.info(f"ℹ️ S-au putut genera doar **{len(st.session_state.variants)}** din {num_variants} variante unice. Cauza este numărul insuficient de combinații posibile din setul curent de numere fierbinți (Top {len(top_nums)}).")


st.markdown("---")

# --- Secțiunea 4: Preview & Export ---
if st.session_state.variants:
    st.header("4. Preview și Export")
    
    # Vizualizare statistici de baza pe variantele generate
    generated_nums = []
    for v in st.session_state.variants:
        generated_nums.extend(v)
    generated_freq = Counter(generated_nums)
    
    st.subheader(f"Statistici Variante Generate ({len(st.session_state.variants)} variante)")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
         # Afișează Top 10 cele mai folosite numere în variantele generate
        top_generated = sorted(generated_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        st.info(f"Top 10 numere folosite: {', '.join([f'{n}({f}x)' for n, f in top_generated])}")
        
    with col_g2:
        # Verifică aderența la Suma Optimă (rămâne ca statistică)
        avg_sum = sum(sum(v) for v in st.session_state.variants) / len(st.session_state.variants)
        st.info(f"Suma medie a variantelor generate: **{avg_sum:.2f}** (Optim: {st.session_state.sum_range[0]}-{st.session_state.sum_range[1]})")

    
    # Preview fix de 20 de variante (FARA SLIDER)
    preview_count = min(20, len(st.session_state.variants))
    st.subheader(f"Preview (Primele {preview_count} variante)")
    
    preview_df = pd.DataFrame(
        [[i+1, " ".join(map(str, v))] for i, v in enumerate(st.session_state.variants[:preview_count])],
        columns=["ID", "Combinație"]
    )
    st.dataframe(preview_df, use_container_width=True, hide_index=True)

    # ---------------------------------------------
    # LOGICA DE EXPORT CORECTATĂ FINAL PENTRU .TXT FĂRĂ ANTET
    # ---------------------------------------------
    
    # Creează liniile de text în formatul solicitat: ID, COMBINATIE
    export_lines = []
    for i, v in enumerate(st.session_state.variants):
        # Combinația este separată prin spațiu: 3 6 8 56
        variant_str = " ".join(map(str, sorted(v)))
        # Linia finală este: 1,3 6 8 56 (fără antet)
        export_lines.append(f"{i+1},{variant_str}")
        
    txt_output = "\n".join(export_lines)

    st.download_button("⬇️ Descarcă TOATE variantele (CSV/TXT)", txt_output, "variante_generate.csv", "text/csv")
    # Am păstrat extensia .csv deoarece formatul este cel CSV (separator virgulă)
