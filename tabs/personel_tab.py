"""
Kişiler sekmesi — Personel listesi ve hedef nöbet sayıları.
"""

import streamlit as st


def render_personel_tab():
    st.subheader("👥 Kişiler ve Hedefler")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("Yıl", min_value=2020, max_value=2100, step=1, key="yil")
    with col2:
        st.number_input("Ay", min_value=1, max_value=12, step=1, key="ay")
    with col3:
        # Değeri 0-31 arasına sınırla
        current_hedef = st.session_state.get("varsayilan_hedef", 7)
        clamped_hedef = max(0, min(31, current_hedef))
        if current_hedef != clamped_hedef:
            st.session_state["varsayilan_hedef"] = clamped_hedef
        st.number_input(
            "Varsayılan hedef nöbet",
            min_value=0, max_value=31, step=1,
            key="varsayilan_hedef"
        )

    st.divider()

    # Personel sayısı
    personel_sayisi = st.number_input(
        "Kaç personel var?",
        min_value=1, max_value=50,
        value=st.session_state.get("personel_sayisi", 9),
        step=1,
        key="personel_sayisi_input"
    )

    # Listeyi güncelle
    current_list = st.session_state["personel_list"]
    if len(current_list) < personel_sayisi:
        for i in range(len(current_list), personel_sayisi):
            current_list.append(f"Personel {i+1}")
    elif len(current_list) > personel_sayisi:
        removed = current_list[personel_sayisi:]
        st.session_state["personel_list"] = current_list[:personel_sayisi]

        # Clean up associated data for removed personnel
        for p in removed:
            for key in ["personel_targets", "weekday_block_map", "izin_map",
                       "prefer_map", "personel_alan_yetkinlikleri",
                       "personel_kidem_gruplari", "personel_vardiya_kisitlari"]:
                if key in st.session_state and p in st.session_state[key]:
                    del st.session_state[key][p]

    st.session_state["personel_sayisi"] = personel_sayisi

    st.caption("Her personelin adını ve hedef nöbet sayısını girin:")

    default_target = st.session_state.get("varsayilan_hedef", 7)

    for i in range(personel_sayisi):
        cols = st.columns([3, 1])
        with cols[0]:
            st.session_state["personel_list"][i] = st.text_input(
                f"{i+1}. Personel",
                value=st.session_state["personel_list"][i],
                key=f"personel_name_{i}"
            )
        with cols[1]:
            p_name = st.session_state["personel_list"][i]
            current_target = st.session_state.get("personel_targets", {}).get(p_name, default_target)
            new_target = st.number_input(
                "Hedef",
                min_value=0, max_value=31,
                value=int(current_target),
                step=1,
                key=f"target_{i}"
            )
            if new_target != default_target:
                st.session_state.setdefault("personel_targets", {})[p_name] = new_target
            elif p_name in st.session_state.get("personel_targets", {}):
                st.session_state["personel_targets"].pop(p_name, None)
