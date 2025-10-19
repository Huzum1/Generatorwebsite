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

# --- Funcții Avansate de Analiză ---

def analyze_pairs(rounds, max_num):
    """Calculeaza frecventa perechilor extrase impreuna."""
    pair_counts = Counter()
    for round_nums in rounds:
        sorted_nums = sorted(round_nums)
        # Folosim combinations pentru a gasi toate perechile
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
    
    # Pre-validare și curățare
    for line in lines:
        try:
            numbers = [int(x.strip()) for x in line.split(",") if x.strip()]
            
            # Validare: Numerele nu trebuie sa depaseasca MAX_NUMBER
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

    # Analiza Frecvenței Standard
    frequency = Counter(all_numbers)
    sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    st.session_state.frequency = dict(sorted_freq)
    st.session_state.historic_rounds = rounds_data

    # Analize Avansate
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
        min_value=3,
        max_value=min(20, st.session_state.max_number), 
        value=5,
        step=1
    )

with col_num:
    num_variants = st.number_input("Câte variante unice să generezi?", 10, 10000, 1000, 10)

strategy = st.selectbox(
    "Alege strategia:",
    [
        "🎯 1. Standard (numere aleatoare din Top N)",
        "🔥 2. Hot Numbers (3 din top 10 + rest aleatoriu)",
        "❄️ 3. Cold-Hot Hybrid (jumătate top 20, jumătate rest)",
        "⚡ 4. Frecvență Ponderată (fără duplicări)",
        "🥇 5. Perechi de Aur (Bazat pe Top Perechi)",
        "🔄 6. Par-Impar Echilibrat (~50/50)",
        "🗺️ 7. Câmpuri de Forță (Minimum 3 Cadrane)",
        "🕰️ 8. Aproape de Întoarcere (Include numere 'în vârstă')", # CORECTAT AICI
        "⛓️ 9. Numere Consecutive (Asigură o pereche)",
        "⭐ 10. Frecvență & Vecinătate",
        "💡 11. Restantierul (Cold Booster)",
        "⚖️ 12. Somă Medie (Selecție Ponderată pe Suma Optimă)",
        "🧬 13. Adâncimea Istoriei (Aderență la ultimele 50 de runde)",
        "🧪 14. Mix Strategy (Combinație aleatorie a strategiilor)",
    ]
)

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
            # Daca ponderea e zero, revenim la random.sample pe ce a ramas
            sample.extend(random.sample(available, k - len(sample)))
            break
            
        chosen = random.choices(available, weights=current_weights, k=1)[0]
        sample.append(chosen)

        # Scoatem elementul ales si refacem listele
        idx = available.index(chosen)
        available.pop(idx)
        current_weights.pop(idx)
        
    return sample

# --- Generare Logică Principală ---
if st.button("🚀 Generează variante și aplică filtrele de calitate"):
    if not st.session_state.top_numbers:
        st.error("❌ Încarcă datele și configurează filtrele în Secțiunile 1 & 2.")
    elif variant_size > len(st.session_state.top_numbers):
        st.error(f"❌ Mărimea variantei ({variant_size}) este mai mare decât numerele disponibile ({len(st.session_state.top_numbers)}). Ajustează.")
    else:
        top_nums = st.session_state.top_numbers
        variants = set()
        max_attempts = num_variants * 50
        attempts = 0
        
        # Date pentru strategii avansate
        max_num = st.session_state.max_number
        q1, q3 = st.session_state.sum_range
        historic_rounds_set = [set(r) for r in st.session_state.historic_rounds]
        
        # Cold Candidates (pentru Restantierul)
        cold_data = analyze_cold_streak(st.session_state.historic_rounds, max_num)
        cold_candidates = [num for num, age in cold_data.items() if num not in top_nums and num not in exclude_numbers]
        
        # Perechi de aur
        top_pairs = list(st.session_state.pair_frequency.keys())[:100] # Top 100 de perechi
        
        # Cadrane (pentru strategia 7)
        q_size = max_num // 4
        quadrants = [
            set(range(1, q_size + 1)),
            set(range(q_size + 1, q_size * 2 + 1)),
            set(range(q_size * 2 + 1, q_size * 3 + 1)),
            set(range(q_size * 3 + 1, max_num + 1))
        ]
        
        while len(variants) < num_variants and attempts < max_attempts:
            attempts += 1
            variant = []
            
            # --- 3.1. Logica de Generare Specifică Strategiei ---
            
            # --- Strategii Existente (1-5) ---
            if strategy == "🎯 1. Standard (numere aleatoare din Top N)":
                variant = random.sample(top_nums, variant_size)

            elif strategy == "🔥 2. Hot Numbers (3 din top 10 + rest aleatoriu)":
                top10 = top_nums[:10]; rest = top_nums[10:]
                variant = random.sample(top10, min(3, variant_size)) + random.sample(rest, max(variant_size-3, 0))

            elif strategy == "❄️ 3. Cold-Hot Hybrid (jumătate top 20, jumătate rest)":
                half = variant_size // 2
                top20 = top_nums[:20]; rest = top_nums[20:]
                variant = random.sample(top20, min(half, len(top20))) + random.sample(rest, variant_size - half)

            elif strategy == "⚡ 4. Frecvență Ponderată (fără duplicări)":
                weights = [st.session_state.frequency.get(n, 1) for n in top_nums]
                variant = weighted_sample_unique(top_nums, weights, variant_size)

            elif strategy == "🥇 5. Perechi de Aur (Bazat pe Top Perechi)":
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
                    variant = random.sample(top_nums, variant_size) # Fallback

            # --- Strategii Noi (6-14) ---
            elif strategy == "🔄 6. Par-Impar Echilibrat (~50/50)":
                num_par = variant_size // 2
                num_impar = variant_size - num_par
                par_nums = [n for n in top_nums if n % 2 == 0]
                impar_nums = [n for n in top_nums if n % 2 != 0]
                
                # Asiguram ca numerele sunt unice si avem destule
                variant_set = set(random.sample(par_nums, min(num_par, len(par_nums))))
                variant_set.update(random.sample(impar_nums, min(num_impar, len(impar_nums))))
                variant = list(variant_set)

            elif strategy == "🗺️ 7. Câmpuri de Forță (Minimum 3 Cadrane)":
                variant_set = set()
                
                # Asigura min 3 cadrane (sau cate putem)
                num_quads = min(random.randint(3, 4), variant_size, len(quadrants))
                chosen_quadrants = random.sample(quadrants, num_quads)
                
                for q in chosen_quadrants:
                    available_in_q = list(q.intersection(set(top_nums)))
                    if available_in_q and len(variant_set) < variant_size:
                        # Ia un singur numar din fiecare cadran ales
                        variant_set.add(random.choice([n for n in available_in_q if n not in variant_set]))
                        
                # Completeaza restul aleatoriu din top_nums
                num_left = variant_size - len(variant_set)
                if num_left > 0:
                    available_rest = [n for n in top_nums if n not in variant_set]
                    variant_set.update(random.sample(available_rest, min(num_left, len(available_rest))))
                variant = list(variant_set)

            elif strategy == "🕰️ 8. Aproape de Întoarcere (Include numere 'în vârstă')":
                # Include 1-2 numere din cele mai reci care au o varsta (nu sunt cele mai rare, dar nu au iesit recent)
                cold_age_candidates = [num for num, age in cold_data.items() if age > 5 and num not in top_nums and num not in exclude_numbers]
                
                num_cold_include = min(random.randint(1, 2), variant_size, len(cold_age_candidates))
                
                cold_part = random.sample(cold_age_candidates, num_cold_include)
                
                num_hot = variant_size - len(cold_part)
                available_hot = [n for n in top_nums if n not in cold_part]
                hot_part = random.sample(available_hot, min(num_hot, len(available_hot)))
                
                variant = cold_part + hot_part

            elif strategy == "⛓️ 9. Numere Consecutive (Asigură o pereche)":
                # Gasim o pereche consecutiva valida in top_nums
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
                     variant = random.sample(top_nums, variant_size) # Fallback standard

            elif strategy == "⭐ 10. Frecvență & Vecinătate":
                # Alege primul număr din Top 5 Hot
                top5 = top_nums[:5]
                start_num = random.choice(top5)
                variant_set = {start_num}
                
                # Defineste vecinatatea (N-1, N+1) pentru top 15
                top15 = top_nums[:15]
                neighbors = set()
                for n in top15:
                    if n - 1 >= 1 and n - 1 not in exclude_numbers: neighbors.add(n - 1)
                    if n + 1 <= max_num and n + 1 not in exclude_numbers: neighbors.add(n + 1)
                
                # Combina numerele hot ramase cu vecinii
                combined_pool = list(set(top_nums[1:]).union(neighbors) - variant_set)
                
                num_left = variant_size - 1
                variant_set.update(random.sample(combined_pool, min(num_left, len(combined_pool))))
                variant = list(variant_set)
                
            elif strategy == "💡 11. Restantierul (Cold Booster)":
                # Asigura includerea a 1-2 numere care au fost excluse de filtrul de "rece" (dar nu interzise manual)
                
                num_cold_include = min(random.randint(1, 2), variant_size, len(cold_candidates))
                cold_part = random.sample(cold_candidates, num_cold_include)
                
                num_hot = variant_size - len(cold_part)
                available_hot = [n for n in top_nums if n not in cold_part]
                hot_part = random.sample(available_hot, min(num_hot, len(available_hot)))
                
                variant = cold_part + hot_part
                
            elif strategy == "⚖️ 12. Somă Medie (Selecție Ponderată pe Suma Optimă)":
                # Incearca sa genereze o varianta cu o suma apropiata de media optima (Q25+Q75)/2
                target_sum = (q1 + q3) / 2
                best_variant = []
                best_sum_diff = float('inf')
                
                # Ruleaza o selectie aleatoare, dar cu ponderi (standard) si pastreaza ce e mai aproape de suma tinta
                for _ in range(10): # 10 sub-incercari
                    weights = [st.session_state.frequency.get(n, 1) for n in top_nums]
                    temp_variant = weighted_sample_unique(top_nums, weights, variant_size)
                    current_sum = sum(temp_variant)
                    current_diff = abs(current_sum - target_sum)
                    
                    if current_diff < best_sum_diff and len(temp_variant) == variant_size:
                        best_sum_diff = current_diff
                        best_variant = temp_variant
                        
                variant = best_variant if best_variant and len(best_variant) == variant_size else random.sample(top_nums, variant_size)
                
            elif strategy == "🧬 13. Adâncimea Istoriei (Aderență la ultimele 50 de runde)":
                
                num_common = min(random.randint(3, 4), variant_size) # Numar de numere comune tinta
                
                if st.session_state.historic_rounds:
                    # Alege o runda "parent" din ultimele 50 (sau cat avem)
                    parent_round = random.choice(st.session_state.historic_rounds[-min(50, len(st.session_state.historic_rounds)):])
                    
                    # Pastreaza num_common numere din runda parent
                    hot_parent_intersection = [n for n in parent_round if n in top_nums]
                    
                    parent_part = random.sample(hot_parent_intersection, min(num_common, len(hot_parent_intersection)))
                    variant_set = set(parent_part)
                    
                    # Completeaza restul din top_nums
                    num_left = variant_size - len(variant_set)
                    available_rest = [n for n in top_nums if n not in variant_set]
                    
                    variant_set.update(random.sample(available_rest, min(num_left, len(available_rest))))
                    variant = list(variant_set)
                else:
                    variant = random.sample(top_nums, variant_size) # Fallback standard

            else:  # 🧪 14. Mix Strategy (Combinație aleatorie)
                # Alege aleatoriu între strategiile 1, 2, 4, 6, 9
                mix_choices = [
                    lambda: random.sample(top_nums, variant_size), # 1. Standard
                    lambda: random.sample(top_nums[:10], min(3, variant_size)) + random.sample(top_nums[10:], max(variant_size-3, 0)), # 2. Hot
                    lambda: weighted_sample_unique(top_nums, [st.session_state.frequency.get(n, 1) for n in top_nums], variant_size), # 4. Ponderata
                    lambda: [n for n in random.sample([n for n in top_nums if n % 2 == 0], variant_size // 2) + random.sample([n for n in top_nums if n % 2 != 0], variant_size - (variant_size // 2))], # 6. Par/Impar
                ]
                variant = random.choice(mix_choices)()
            
            # --- 3.2. Filtre de Calitate (Se aplică TOATE variantelor generate) ---

            # Filtru 1: Unicitate și mărime
            if len(set(variant)) != variant_size:
                continue

            # Filtru 2: Filtru de Somă (Sum Filter)
            if not (q1 <= sum(variant) <= q3):
                continue 
            
            # Filtru 3: Verificare de Aderență la Istoric (Nearness to History)
            # Asiguram ca varianta are minim 2 numere comune cu ultimele 10 runde
            if st.session_state.historic_rounds:
                is_close_to_history = False
                last_10_rounds = historic_rounds_set[-min(10, len(historic_rounds_set)):]
                for hist_round in last_10_rounds:
                    if len(set(variant).intersection(hist_round)) >= 2:
                        is_close_to_history = True
                        break
                if not is_close_to_history:
                    continue 

            final_variant = tuple(sorted(variant))
            variants.add(final_variant)

        st.session_state.variants = list(variants)
        random.shuffle(st.session_state.variants)

        st.success(f"✅ Generate **{len(st.session_state.variants)}** variante UNICE ({variant_size}/{variant_size}) în {attempts} încercări.")
        if len(st.session_state.variants) < num_variants:
             st.warning(f"⚠️ Nu s-au putut genera {num_variants} variante unice după aplicarea filtrelor de calitate. Au rămas {len(st.session_state.variants)}.")

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
        # Verifică aderența la Suma Optimă
        avg_sum = sum(sum(v) for v in st.session_state.variants) / len(st.session_state.variants)
        st.info(f"Suma medie a variantelor generate: **{avg_sum:.2f}** (Optim: {st.session_state.sum_range[0]}-{st.session_state.sum_range[1]})")

    
    preview_count = st.slider("Câte variante să afișez (Preview)?", 5, min(50, len(st.session_state.variants)), 20)
    preview_df = pd.DataFrame(
        [[i+1, " ".join(map(str, v))] for i, v in enumerate(st.session_state.variants[:preview_count])],
        columns=["ID", "Combinație"]
    )
    st.dataframe(preview_df, use_container_width=True, hide_index=True)

    txt_output = "\n".join([",".join(map(str, v)) for v in st.session_state.variants])
    st.download_button("⬇️ Descarcă variante (CSV/TXT)", txt_output, "variante_generate.txt", "text/plain")
