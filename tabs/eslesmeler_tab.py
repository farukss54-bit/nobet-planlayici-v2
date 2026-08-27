"""
Eşleşmeler sekmesi — Birlikte/ayrı tutma kuralları ve gelişmiş kısıtlar.
"""

import streamlit as st
from config import w_cuma, w_cumartesi, w_pazar, w_iki_gun_bosluk


def render_eslesmeler_tab():
    st.subheader("👫 Eşleşme Tercihleri")

    personeller = st.session_state.get("personel_list", [])

    if not personeller:
        st.warning("Önce Kişiler sekmesinde personel listesini girin.")
    elif len(personeller) < 2:
        st.warning("Çift tanımlamak için en az 2 personel gerekli.")
    else:
        colA, colB = st.columns(2)

        with colA:
            st.markdown("### ✅ Birlikte Tutsun")
            a = st.selectbox("Personel A", options=personeller, key="wp_a")
            b_options = [p for p in personeller if p != a]
            b = st.selectbox("Personel B", options=b_options, key="wp_b")
            min_k = st.number_input(
                "Minimum birlikte gün",
                min_value=0, max_value=31, value=0, key="wp_min",
                help="0 = tercih (mümkünse birlikte, zorunlu değil); "
                     "1+ = en az bu kadar gün birlikte ZORUNLU"
            )

            if st.button("➕ Ekle", key="wp_add"):
                aa, bb = sorted([a, b])
                exists = any(
                    item["a"] == aa and item["b"] == bb
                    for item in st.session_state["want_pairs_list"]
                )
                if not exists:
                    st.session_state["want_pairs_list"].append({"a": aa, "b": bb, "min": int(min_k)})
                    st.rerun()

        with colB:
            st.markdown("### ❌ Asla Birlikte Tutmasın")
            na = st.selectbox("Personel A ", options=personeller, key="np_a")
            nb_options = [p for p in personeller if p != na]
            nb = st.selectbox("Personel B ", options=nb_options, key="np_b")

            if st.button("➕ Ekle", key="np_add"):
                aa, bb = sorted([na, nb])
                exists = any(
                    item["a"] == aa and item["b"] == bb
                    for item in st.session_state["no_pairs_list"]
                )
                if not exists:
                    st.session_state["no_pairs_list"].append({"a": aa, "b": bb})
                    st.rerun()

        st.divider()
        st.markdown("### Mevcut Tanımlar")

        colL, colR = st.columns(2)

        with colL:
            st.markdown("**Birlikte tutulacaklar:**")
            if not st.session_state["want_pairs_list"]:
                st.caption("Henüz yok.")
            else:
                for i, item in enumerate(st.session_state["want_pairs_list"]):
                    c1, c2 = st.columns([6, 2])
                    etiket = "tercih" if item["min"] <= 0 else f"zorunlu ≥{item['min']}"
                    c1.write(f"• {item['a']} ↔ {item['b']} ({etiket})")
                    if c2.button("Sil", key=f"wp_del_{i}"):
                        st.session_state["want_pairs_list"].pop(i)
                        st.rerun()

        with colR:
            st.markdown("**Ayrı tutulacaklar:**")
            if not st.session_state["no_pairs_list"]:
                st.caption("Henüz yok.")
            else:
                for i, item in enumerate(st.session_state["no_pairs_list"]):
                    c1, c2 = st.columns([6, 2])
                    c1.write(f"• {item['a']} × {item['b']}")
                    if c2.button("Sil", key=f"np_del_{i}"):
                        st.session_state["no_pairs_list"].pop(i)
                        st.rerun()

        # Gelişmiş ayarlar
        with st.expander("⚙️ Gelişmiş Ayarlar"):
            st.markdown("#### ☁️ Esnek Ayrı Tutma (Soft)")
            sna = st.selectbox("Personel A", options=personeller, key="snp_a")
            snb_options = [p for p in personeller if p != sna]
            snb = st.selectbox("Personel B", options=snb_options, key="snp_b")

            if st.button("➕ Esnek kural ekle"):
                aa, bb = sorted([sna, snb])
                exists = any(
                    item["a"] == aa and item["b"] == bb
                    for item in st.session_state["soft_no_pairs_list"]
                )
                if not exists:
                    st.session_state["soft_no_pairs_list"].append({"a": aa, "b": bb})
                    st.rerun()

            for i, item in enumerate(st.session_state["soft_no_pairs_list"]):
                c1, c2 = st.columns([8, 2])
                c1.write(f"☁️ {item['a']} - {item['b']}")
                if c2.button("Sil", key=f"snp_del_{i}"):
                    st.session_state["soft_no_pairs_list"].pop(i)
                    st.rerun()

            st.divider()

            # === KURAL AYARLARI ===
            st.markdown("#### 📋 Nöbet Kuralları")

            # Ardışık gün yasağı
            st.session_state["ardisik_yasak"] = st.checkbox(
                "Ardışık gün yasağı",
                value=st.session_state.get("ardisik_yasak", True),
                help="Aynı kişi arka arkaya iki gün nöbet tutamaz"
            )

            # Günaşırı limiti
            col1, col2 = st.columns([1, 2])
            with col1:
                st.session_state["gunasiri_limit_aktif"] = st.checkbox(
                    "Günaşırı limit",
                    value=st.session_state.get("gunasiri_limit_aktif", True),
                    help="1 gün arayla nöbet sayısını sınırla"
                )
            with col2:
                if st.session_state.get("gunasiri_limit_aktif", True):
                    st.session_state["max_gunasiri"] = st.number_input(
                        "Maksimum günaşırı nöbet (kişi başı/ay)",
                        min_value=1, max_value=15,
                        value=st.session_state.get("max_gunasiri", 1),
                        help="0 = sınırsız"
                    )

            st.divider()
            st.markdown("#### ⚖️ Denge Kuralları")

            # Hafta sonu dengesi
            st.session_state["hafta_sonu_dengesi"] = st.checkbox(
                "Hafta sonu dengesi",
                value=st.session_state.get("hafta_sonu_dengesi", True),
                help="Cuma, Cumartesi, Pazar nöbetlerini dengeli dağıt"
            )

            if st.session_state.get("hafta_sonu_dengesi", True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.session_state["w_cuma"] = st.slider("Cuma ağırlığı", 0, 2000,
                        st.session_state.get("w_cuma", w_cuma))
                with col2:
                    st.session_state["w_cumartesi"] = st.slider("Cumartesi ağırlığı", 0, 2000,
                        st.session_state.get("w_cumartesi", w_cumartesi))
                with col3:
                    st.session_state["w_pazar"] = st.slider("Pazar ağırlığı", 0, 2000,
                        st.session_state.get("w_pazar", w_pazar))

            # Tatil dengesi
            st.session_state["tatil_dengesi"] = st.checkbox(
                "Tatil dengesi",
                value=st.session_state.get("tatil_dengesi", True),
                help="Resmi tatil nöbetlerini dengeli dağıt"
            )

            st.divider()
            st.markdown("#### 🎯 Tercihler")

            # 2 gün boşluk tercihi
            col1, col2 = st.columns([1, 2])
            with col1:
                st.session_state["iki_gun_bosluk_aktif"] = st.checkbox(
                    "2 gün boşluk tercihi",
                    value=st.session_state.get("iki_gun_bosluk_aktif", True),
                    help="Nöbetler arası en az 2 gün boşluk tercih edilir"
                )
            with col2:
                if st.session_state.get("iki_gun_bosluk_aktif", True):
                    st.session_state["w_gap3"] = st.slider(
                        "Tercih ağırlığı",
                        0, 2000, st.session_state.get("w_gap3", w_iki_gun_bosluk)
                    )
