if st.button("🚀 Generează variante"):
    if not st.session_state.top_numbers:
        st.error("❌ Încarcă datele și configurează filtrele")
    else:
        top_nums = st.session_state.top_numbers
        
        variants = set()

        # --- Strategie specială: Premium Hybrid ---
        if strategy == "🔥❄️ Premium Hybrid (toate posibilele 3+1 din top 25/rest)":
            from itertools import combinations
            top25 = top_nums[:25]
            rest = top_nums[25:]
            
            if len(top25) >= 3 and len(rest) >= 1:
                all_combos = []
                for three in combinations(top25, 3):
                    for one in rest:
                        variant = tuple(sorted(list(three) + [one]))
                        all_combos.append(variant)
                
                # Dacă numărul cerut e mai mic decât totalul, alegem aleator exact atâtea
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
