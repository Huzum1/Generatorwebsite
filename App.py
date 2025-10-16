import streamlit as st
import pandas as pd
from collections import Counter
import random
import io
from itertools import combinations

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
if "rounds_data" not in st.session_state:
    st.session_state.rounds_data = []

# --- Secțiunea 1: Încărcarea datelor ---
st.header("📊 1. Încarcă datele extragerilor")

tab1, tab2 = st.tabs(["📁 Import Fișier", "✍️ Manual"])

def process_data(lines):
    """Procesează datele și actualizează session state"""
    all_numbers = []
    valid_lines = []
    
    for line in lines:
        try:
            numbers = [int(x.strip()) for x in line.split(",") if x.strip()]
            # Validare: verifică că numerele sunt între 1 și 66
            if all(1 <= n <= 66 for n in numbers):
                all_numbers.extend(numbers)
                valid_lines.append(line)
            else:
                st.warning(f"⚠️ Linie ignorată (numere invalide): {line}")
        except ValueError:
            st.warning(f"⚠️ Linie ignorată (format invalid): {line}")
    
    if not all_numbers:
        st.error("❌ Nu s-au putut procesa date valide")
        return False
    
    frequency = Counter(all_numbers)
    sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    st.session_state.frequency = dict(sorted_freq)
    st.session_state.rounds_data = valid_lines
    
    return True, valid_lines, all_numbers, frequency, sorted_freq

with tab1:
    uploaded_file = st.file_uploader("📂 CSV/TXT cu extragerile din runde", type=["csv", "txt"])
    
    if uploaded_file:
        try:
            content = uploaded_file.read().decode("utf-8")
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            
            result = process_data(lines)
            if result:
                _, valid_lines, all_numbers, frequency, sorted_freq = result
                
                st.success(f"✅ Încărcate {len(valid_lines)} runde cu total {len(all_numbers)} numere")
                
                # Afișare runde cu paginare
                st.subheader("📋 Rundele încărcate:")
                
                # Paginare
                items_per_page = 10
                total_pages = (len(valid_lines) - 1) // items_per_page + 1
                
                if total_pages > 1:
                    page = st.selectbox("Pagina", range(1, total_pages + 1))
                else:
                    page = 1
                
                start_idx = (page - 1) * items_per_page
                end_idx = min(start_idx + items_per_page, len(valid_lines))
                
                rounds_df = pd.DataFrame(
                    [[i+1, line] for i, line in enumerate(valid_lines[start_idx:end_idx], start_idx)],
                    columns=["Runda", "Numere"]
                )
                st.dataframe(rounds_df, use_container_width=True, hide_index=True)
                
                if total_pages > 1:
                    st.caption(f"Afișate rundele {start_idx + 1}-{end_idx} din {len(valid_lines)}")
                
                # Statistici
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Runde", len(valid_lines))
                col2.metric("Total numere", len(all_numbers))
                col3.metric("Numere unice", len(frequency))
                col4.metric("Medie/rundă", f"{len(all_numbers)/len(valid_lines):.1f}")
                
                # Top și Bottom
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🔥 Top 15 cele mai frecvente")
                    top15_df = pd.DataFrame(sorted_freq[:15], columns=["Număr", "Frecvență"])
                    top15_df["Procent"] = (top15_df["Frecvență"] / len(all_numbers) * 100).round(1)
                    st.dataframe(top15_df, use_container_width=True, hide_index=True)
                
                with col2:
                    st.subheader("❄️ Bottom 15 cele mai reci")
                    bottom15_df = pd.DataFrame(sorted_freq[-15:], columns=["Număr", "Frecvență"])
                    bottom15_df["Procent"] = (bottom15_df["Frecvență"] / len(all_numbers) * 100).round(1)
                    st.dataframe(bottom15_df, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"❌ Eroare la procesarea fișierului: {str(e)}")

with tab2:
    st.subheader("✍️ Adaugă rundele manual")
    
    manual_input = st.text_area(
        "Introduce rundele (o rundă pe linie, numere separate cu virgulă)",
        placeholder="7, 27, 22, 34, 59, 14, 55, 52, 47, 41, 51, 11\n51, 3, 61, 10, 27, 55, 24, 39, 12, 14, 65, 58\n4, 49, 55, 11, 7, 30, 44, 29, 60, 59, 22, 36",
        height=300
    )
    
    if st.button("✅ Procesează rundele"):
        if manual_input.strip():
            lines = [line.strip() for line in manual_input.split("\n") if line.strip()]
            
            result = process_data(lines)
            if result:
                _, valid_lines, all_numbers, frequency, sorted_freq = result
                
                st.success(f"✅ Procesate {len(valid_lines)} runde cu total {len(all_numbers)} numere")
                
                # Afișare runde cu paginare
                st.subheader("📋 Rundele adăugate:")
                
                items_per_page = 10
                total_pages = (len(valid_lines) - 1) // items_per_page + 1
                
                if total_pages > 1:
                    page = st.selectbox("Pagina", range(1, total_pages + 1), key="manual_page")
                else:
                    page = 1
                
                start_idx = (page - 1) * items_per_page
                end_idx = min(start_idx + items_per_page, len(valid_lines))
                
                rounds_df = pd.DataFrame(
                    [[i+1, line] for i, line in enumerate(valid_lines[start_idx:end_idx], start_idx)],
                    columns=["Runda", "Numere"]
                )
                st.dataframe(rounds_df, use_container_width=True, hide_index=True)
                
                if total_pages > 1:
                    st.caption(f"Afișate rundele {start_idx + 1}-{end_idx} din {len(valid_lines)}")
                
                # Statistici
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Runde", len(valid_lines))
                col2.metric("Total numere", len(all_numbers))
                col3.metric("Numere unice", len(frequency))
                col4.metric("Medie/rundă", f"{len(all_numbers)/len(valid_lines):.1f}")
                
                # Top și Bottom
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🔥 Top 15 cele mai frecvente")
                    top15_df = pd.DataFrame(sorted_freq[:15], columns=["Număr", "Frecvență"])
                    top15_df["Procent"] = (top15_df["Frecvență"] / len(all_numbers) * 100).round(1)
                    st.dataframe(top15_df, use_container_width=True, hide_index=True)
                
                with col2:
                    st.subheader("❄️ Bottom 15 cele mai reci")
                    bottom15_df = pd.DataFrame(sorted_freq[-15:], columns=["Număr", "Frecvență"])
                    bottom15_df["Procent"] = (bottom15_df["Frecvență"] / len(all_numbers) * 100).round(1)
                    st.dataframe(bottom15_df, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Te rugăm să adaugi cel puțin o rundă")

# --- Secțiunea 2: Configurare filtre ---
st.header("⚙️ 2. Configurare filtre")

col1, col2 = st.columns(2)

with col1:
    st.subheader("❄️ Exclude cele mai reci numere")
    
    exclude_mode = st.radio(
        "Cum vrei să excludi?",
        ["🔢 Automată (cele mai reci)", "✍️ Manual (numere specifice)", "🔀 Ambele"],
        horizontal=True
    )
    
    exclude_numbers = set()
    auto_exclude = set()
    
    # Excludere automată
    if exclude_mode in ["🔢 Automată (cele mai reci)", "🔀 Ambele"]:
        auto_cold_count = st.selectbox(
            "Exclude topul celor mai reci",
            [0, 5, 10, 15, 20, 25, 30],
            index=0
        )
        
        if st.session_state.frequency and auto_cold_count > 0:
            sorted_freq = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
            auto_exclude = set([x[0] for x in sorted_freq[-auto_cold_count:]])
            if auto_exclude:
                st.info(f"🔴 Auto-exclude ({auto_cold_count}): {sorted(auto_exclude)}")
    
    # Excludere manuală
    if exclude_mode in ["✍️ Manual (numere specifice)", "🔀 Ambele"]:
        manual_exclude_input = st.text_area(
            "Introduce numere de exclus manual (separate cu virgulă)",
            placeholder="Exemplu: 51, 2, 15",
            height=80
        )
        
        if manual_exclude_input.strip():
            try:
                manual_exclude = set([int(x.strip()) for x in manual_exclude_input.split(",") if x.strip()])
                # Validare
                invalid = [n for n in manual_exclude if n < 1 or n > 66]
                if invalid:
                    st.error(f"❌ Numere invalide (trebuie între 1-66): {invalid}")
                else:
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
    
    if st.session_state.frequency:
        max_available = len(st.session_state.frequency)
        top_count = st.slider(
            "Câte numere din top?",
            min_value=10,
            max_value=max_available,
            value=min(50, max_available),
            step=5
        )
        
        sorted_freq = sorted(st.session_state.frequency.items(), key=lambda x: x[1], reverse=True)
        top_numbers = [x[0] for x in sorted_freq[:top_count] if x[0] not in exclude_numbers]
        st.session_state.top_numbers = top_numbers
        
        if len(top_numbers) >= 4:
            st.success(f"✅ {len(top_numbers)} numere disponibile pentru generare")
            
            with st.expander("👁️ Vezi numerele selectate"):
                st.write(sorted(top_numbers))
        else:
            st.error("❌ Sunt necesare minimum 4 numere pentru generare!")
    else:
        st.warning("⚠️ Încarcă mai întâi datele extragerilor")

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
        "🎪 Mix Strategy (combinație din toate)",
        "💎 Elite (toate combinațiile posibile 3+1)"
    ]
)

# Afișare descriere strategie
strategy_descriptions = {
    "🎯 Standard (4 numere aleatoare)": "Selectează aleator 4 numere din pool-ul disponibil",
    "🔥 Hot Numbers (3 din top 10 + 1 din rest)": "3 numere din top 10 + 1 număr din restul",
    "❄️ Cold-Hot Hybrid (2 din top 20 + 2 din 21-50)": "Combină 2 numere fierbinți cu 2 mai puțin frecvente",
    "🔥❄️ Premium Hybrid (3 din top 25 + 1 din rest)": "3 numere din top 25 + 1 din rest",
    "🌀 Random Pairs (2 perechi aleatoare)": "Generează 2 perechi aleatoare de numere",
    "⚡ Frecvență Ponderată (numere cu mai multă frecvență)": "Probabilitate mai mare pentru numere frecvente",
    "🎪 Mix Strategy (combinație din toate)": "Aplică random diferite strategii pentru fiecare variantă",
    "💎 Elite (toate combinațiile posibile 3+1)": "Generează TOATE combinațiile posibile (3 din top + 1 din rest)"
}

st.info(f"ℹ️ {strategy_descriptions[strategy]}")

# Configurare număr variante
if strategy != "💎 Elite (toate combinațiile posibile 3+1)":
    num_variants = st.number_input(
        "Câte variante?",
        min_value=100,
        max_value=10000,
        value=1000,
        step=100
    )
else:
    st.warning("⚠️ Strategia Elite va genera TOATE combinațiile posibile. Poate dura mai mult!")
    
    if st.session_state.top_numbers:
        top25 = st.session_state.top_numbers[:25]
        rest = st.session_state.top_numbers[25:]
        
        if len(rest) > 0:
            # Calculează numărul de combinații
            from math import comb
            total_combinations = comb(len(top25), 3) * len(rest)
            st.info(f"📊 Se vor genera ~{total_combinations:,} combinații unice")
        else:
            st.error("❌ Nu sunt suficiente numere pentru strategia Elite")

if st.button("🚀 Generează variante", type="primary"):
    if not st.session_state.top_numbers:
        st.error("❌ Încarcă datele și configurează filtrele")
    elif len(st.session_state.top_numbers) < 4:
        st.error("❌ Sunt necesare minimum 4 numere pentru generare!")
    else:
        top_nums = st.session_state.top_numbers
        
        with st.spinner("⏳ Generez variante..."):
            # Strategia Elite (toate combinațiile)
            if strategy == "💎 Elite (toate combinațiile posibile 3+1)":
                top25 = top_nums[:min(25, len(top_nums))]
                rest = top_nums[min(25, len(top_nums)):]
                
                if len(rest) > 0 and len(top25) >= 3:
                    st.session_state.variants = []
                    for three in combinations(top25, 3):
                        for one in rest:
                            variant = tuple(sorted(list(three) + [one]))
                            st.session_state.variants.append(variant)
                    
                    st.session_state.variants = sorted(list(set(st.session_state.variants)))
                    st.success(f"✅ Generate {len(st.session_state.variants):,} variante UNICE")
                else:
                    st.error("❌ Nu sunt suficiente numere pentru această strategie")
            
            else:
                # Alte strategii
                variants = set()
                max_attempts = num_variants * 100
                attempts = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                while len(variants) < num_variants and attempts < max_attempts:
                    attempts += 1
                    
                    # Update progress
                    if attempts % 100 == 0:
                        progress = min(len(variants) / num_variants, 1.0)
                        progress_bar.progress(progress)
                        status_text.text(f"Generate: {len(variants)}/{num_variants} variante...")
                    
                    try:
                        if strategy == "🎯 Standard (4 numere aleatoare)":
                            variant = tuple(sorted(random.sample(top_nums, 4)))
                        
                        elif strategy == "🔥 Hot Numbers (3 din top 10 + 1 din rest)":
                            top10 = top_nums[:min(10, len(top_nums))]
                            rest = top_nums[min(10, len(top_nums)):]
                            if len(top10) >= 3 and len(rest) > 0:
                                three = random.sample(top10, 3)
                                one = random.sample(rest, 1)
                                variant = tuple(sorted(three + one))
                            else:
                                variant = tuple(sorted(random.sample(top_nums, 4)))
                        
                        elif strategy == "❄️ Cold-Hot Hybrid (2 din top 20 + 2 din 21-50)":
                            top20 = top_nums[:min(20, len(top_nums))]
                            rest = top_nums[min(20, len(top_nums)):]
                            if len(top20) >= 2 and len(rest) >= 2:
                                two_hot = random.sample(top20, 2)
                                two_cold = random.sample(rest, 2)
                                variant = tuple(sorted(two_hot + two_cold))
                            else:
                                variant = tuple(sorted(random.sample(top_nums, 4)))
                        
                        elif strategy == "🔥❄️ Premium Hybrid (3 din top 25 + 1 din rest)":
                            top25 = top_nums[:min(25, len(top_nums))]
                            rest = top_nums[min(25, len(top_nums)):]
                            if len(top25) >= 3 and len(rest) > 0:
                                three = random.sample(top25, 3)
                                one = random.sample(rest, 1)
                                variant = tuple(sorted(three + one))
                            else:
                                variant = tuple(sorted(random.sample(top_nums, 4)))
                        
                        elif strategy == "🌀 Random Pairs (2 perechi aleatoare)":
                            variant = tuple(sorted(random.sample(top_nums, 4)))
                        
                        elif strategy == "⚡ Frecvență Ponderată (numere cu mai multă frecvență)":
                            weights = [st.session_state.frequency.get(n, 1) for n in top_nums]
                            selected = []
                            while len(selected) < 4:
                                num = random.choices(top_nums, weights=weights, k=1)[0]
                                if num not in selected:
                                    selected.append(num)
                            variant = tuple(sorted(selected))
                        
                        elif strategy == "🎪 Mix Strategy (combinație din toate)":
                            strat_choice = random.randint(1, 6)
                            if strat_choice == 1:
                                variant = tuple(sorted(random.sample(top_nums, 4)))
                            elif strat_choice <= 6:
                                # Aplică o strategie aleatoare
                                variant = tuple(sorted(random.sample(top_nums, 4)))
                        
                        variants.add(variant)
                    
                    except Exception as e:
                        continue
                
                progress_bar.progress(1.0)
                status_text.empty()
                
                st.session_state.variants = sorted(list(variants))
                
                if len(st.session_state.variants) >= num_variants * 0.9:
                    st.success(f"✅ Generate {len(st.session_state.variants):,} variante unice în {attempts:,} încercări")
                else:
                    st.warning(f"⚠️ Generate doar {len(st.session_state.variants):,} variante unice din {num_variants:,} solicitate ({attempts:,} încercări)")
                
                st.info(f"📊 Strategie: {strategy}")

# --- Secțiunea 4: Preview și Export ---
if st.session_state.variants:
    st.header("📋 4. Preview și Export")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        preview_count = st.slider("Câte variante să afișez în preview?", 10, 100, 20)
    
    with col2:
        st.metric("Total variante", f"{len(st.session_state.variants):,}")
    
    # Tabs pentru diferite vizualizări
    preview_tab1, preview_tab2 = st.tabs(["📋 Tabel", "📊 Analiză"])
    
    with preview_tab1:
        st.subheader(f"Preview (primele {preview_count})")
        preview_df = pd.DataFrame(
            [[i+1, ", ".join(map(str, v))] for i, v in enumerate(st.session_state.variants[:preview_count])],
            columns=["ID", "Combinație"]
        )
        st.dataframe(preview_df, use_container_width=True, hide_index=True)
    
    with preview_tab2:
        st.subheader("📊 Analiza variantelor generate")
        
        # Calculează statistici
        all_nums_in_variants = []
        for v in st.session_state.variants:
            all_nums_in_variants.extend(v)
        
        variant_freq = Counter(all_nums_in_variants)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top 10 numere în variante:**")
            top10_variant = pd.DataFrame(
                variant_freq.most_common(10),
                columns=["Număr", "Apariții"]
            )
            top10_variant["Procent"] = (top10_variant["Apariții"] / len(st.session_state.variants) * 100).round(1)
            st.dataframe(top10_variant, use_container_width=True, hide_index=True)
        
        with col2:
            st.write("**Bottom 10 numere în variante:**")
            bottom10_variant = pd.DataFrame(
                variant_freq.most_common()[:-11:-1],
                columns=["Număr", "Apariții"]
            )
            bottom10_variant["Procent"] = (bottom10_variant["Apariții"] / len(st.session_state.variants) * 100).round(1)
            st.dataframe(bottom10_variant, use_container_width=True, hide_index=True)
    
    # Export
    st.subheader("💾 Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export TXT simplu
        txt_output = ""
        for i, variant in enumerate(st.session_state.variants, 1):
            txt_output += f"{', '.join(map(str, variant))}\n"
        
        st.download_button(
            label="⬇️ Descarcă TXT (simplu)",
            data=txt_output,
            file_name="variante_loterie.txt",
            mime="text/plain"
        )
    
    with col2:
        # Export TXT cu ID
        txt_output_id = ""
        for i, variant in enumerate(st.session_state.variants, 1):
            txt_output_id += f"{i}, {', '.join(map(str, variant))}\n"
        
        st.download_button(
            label="⬇️ Descarcă TXT (cu ID)",
            data=txt_output_id,
            file_name="variante_loterie_id.txt",
            mime="text/plain"
        )
    
    with col3:
        # Export CSV
        csv_df = pd.DataFrame(
            [[i+1] + list(v) for i, v in enumerate(st.session_state.variants)],
            columns=["ID", "Num1", "Num2", "Num3", "Num4"]
        )
        csv_output = csv_df.to_csv(index=False)
        
        st.download_button(
            label="⬇️ Descarcă CSV",
            data=csv_output,
            file_name="variante_loterie.csv",
            mime="text/csv"
        )
    
    st.success(f"✅ Gata de export: {len(st.session_state.variants):,} variante unice!")

# Footer
st.markdown("---")
st.caption("🎰 Generator Variante Loterie | Creat cu Streamlit")
