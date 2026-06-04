"""
Alanlar sekmesi — Çoklu çalışma alanı tanımları ve yetkinlikler.
"""

import streamlit as st


def render_alanlar_tab():
    st.subheader("🏢 Çalışma Alanları")

    st.info("""
    **Çoklu Alan Modu**: Farklı çalışma alanları tanımlayabilirsiniz (örn: Yeşil, Sarı, Kırmızı alan).
    Her alana günlük kontenjan belirlenir ve sistem otomatik olarak dağılımı yapar.

    Alan tanımlamazsanız, mevcut tek-alan modu kullanılır.
    """)

    # Alan modu toggle
    alan_modu = st.checkbox(
        "Çoklu alan modunu aktifleştir",
        value=st.session_state.get("alan_modu_aktif", False),
        key="alan_modu_checkbox"
    )
    st.session_state["alan_modu_aktif"] = alan_modu

    if alan_modu:
        st.divider()

        # Yeni alan ekleme
        st.markdown("### ➕ Alan Ekle")
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

        with col1:
            yeni_alan_isim = st.text_input("Alan adı", placeholder="Örn: Kırmızı Alan", key="yeni_alan_isim")
        with col2:
            yeni_alan_kontenjan = st.number_input("Hedef", min_value=1, max_value=10, value=1, key="yeni_alan_kont", help="Günlük hedef kişi sayısı")
        with col3:
            yeni_alan_max = st.number_input("Max", min_value=1, max_value=15, value=3, key="yeni_alan_max", help="Günlük maksimum kişi sayısı")
        with col4:
            yeni_alan_min_staff = st.number_input("Min Pers.", min_value=1, max_value=10, value=1, key="yeni_alan_min_staff", help="Her vardiyada en az kaç kişi")
        with col5:
            yeni_alan_renk = st.color_picker("Renk", value="#FF6B6B", key="yeni_alan_renk")

        if st.button("➕ Alan Ekle", key="alan_ekle_btn"):
            if yeni_alan_isim.strip():
                mevcut_isimler = [a["isim"] for a in st.session_state.get("alanlar", [])]
                if yeni_alan_isim.strip() not in mevcut_isimler:
                    st.session_state.setdefault("alanlar", []).append({
                        "isim": yeni_alan_isim.strip(),
                        "kontenjan": yeni_alan_kontenjan,
                        "max_kontenjan": yeni_alan_max,
                        "minimum_staffing": yeni_alan_min_staff,
                        "renk": yeni_alan_renk
                    })
                    st.rerun()
                else:
                    st.error("Bu isimde bir alan zaten var!")
            else:
                st.error("Alan adı boş olamaz!")

        st.divider()

        # Mevcut alanlar
        st.markdown("### 📋 Mevcut Alanlar")

        alanlar = st.session_state.get("alanlar", [])

        if not alanlar:
            st.caption("Henüz alan tanımlanmamış.")
        else:
            toplam_kontenjan = sum(a.get("kontenjan", 1) for a in alanlar)
            # max_kontenjan None olabilir, None check yapıyoruz
            toplam_max = sum(
                (a.get("max_kontenjan") if a.get("max_kontenjan") is not None
                 else a.get("kontenjan", 1) + 2)
                for a in alanlar
            )
            st.caption(f"Toplam günlük: Hedef **{toplam_kontenjan}** / Max **{toplam_max}** kişi")

            # Başlık satırı
            hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([3, 1, 1, 1, 1])
            with hcol2:
                st.caption("Hedef")
            with hcol3:
                st.caption("Max")
            with hcol4:
                st.caption("Min Pers.")

            for i, alan in enumerate(alanlar):
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

                with col1:
                    st.markdown(f"<span style='color:{alan.get('renk', '#808080')}'>●</span> **{alan['isim']}**", unsafe_allow_html=True)
                with col2:
                    # Hedef kontenjan değiştirme
                    yeni_kont = st.number_input(
                        "Hedef",
                        min_value=1, max_value=10,
                        value=alan.get("kontenjan", 1),
                        key=f"alan_kont_{i}",
                        label_visibility="collapsed"
                    )
                    if yeni_kont != alan.get("kontenjan", 1):
                        st.session_state["alanlar"][i]["kontenjan"] = yeni_kont
                with col3:
                    # Max kontenjan değiştirme
                    current_max = alan.get("max_kontenjan", alan.get("kontenjan", 1) + 2)
                    yeni_max = st.number_input(
                        "Max",
                        min_value=yeni_kont, max_value=15,
                        value=current_max,
                        key=f"alan_max_{i}",
                        label_visibility="collapsed"
                    )
                    if yeni_max != current_max:
                        st.session_state["alanlar"][i]["max_kontenjan"] = yeni_max
                with col4:
                    # Minimum staffing değiştirme
                    current_min_staff = alan.get("minimum_staffing", 1)
                    yeni_min_staff = st.number_input(
                        "Min Pers.",
                        min_value=1, max_value=10,
                        value=current_min_staff,
                        key=f"alan_min_staff_{i}",
                        label_visibility="collapsed"
                    )
                    if yeni_min_staff != current_min_staff:
                        st.session_state["alanlar"][i]["minimum_staffing"] = yeni_min_staff
                with col5:
                    if st.button("🗑️", key=f"alan_sil_{i}"):
                        st.session_state["alanlar"].pop(i)
                        st.rerun()

        st.divider()

        # Alan bazlı denklik ayarı
        st.markdown("### ⚖️ Denklik Ayarları")
        alan_denklik = st.checkbox(
            "Alan bazlı denklik sağla",
            value=st.session_state.get("alan_bazli_denklik", True),
            help="Her kişi her alandan benzer sayıda nöbet tutar"
        )
        st.session_state["alan_bazli_denklik"] = alan_denklik

        st.divider()

        # Personel alan yetkinlikleri
        st.markdown("### 👤 Personel Alan Yetkinlikleri")
        st.caption("Boş bırakılan personeller tüm alanlarda çalışabilir.")

        personeller = st.session_state.get("personel_list", [])
        alan_isimleri = [a["isim"] for a in alanlar]

        if personeller and alan_isimleri:
            for p in personeller:
                mevcut_yetkinlikler = st.session_state.get("personel_alan_yetkinlikleri", {}).get(p, [])

                secilen = st.multiselect(
                    f"{p}",
                    options=alan_isimleri,
                    default=[y for y in mevcut_yetkinlikler if y in alan_isimleri],
                    key=f"yetkinlik_{p}",
                    placeholder="Tüm alanlar"
                )

                if secilen:
                    st.session_state.setdefault("personel_alan_yetkinlikleri", {})[p] = secilen
                elif p in st.session_state.get("personel_alan_yetkinlikleri", {}):
                    st.session_state["personel_alan_yetkinlikleri"].pop(p, None)

        # ====== KIDEM KURALLARI ======
        st.divider()
        st.markdown("### 🎖️ Alan-Kıdem Kuralları")
        st.caption("Her alan için kıdem gruplarından günde min/max kaç kişi olacağını belirleyin.")

        kidem_gruplari = st.session_state.get("kidem_gruplari", [])
        grup_isimleri = [g["isim"] for g in kidem_gruplari]

        if not kidem_gruplari:
            st.info("Önce Kıdem sekmesinde kıdem grupları tanımlayın.")
        elif alanlar:
            for i, alan in enumerate(alanlar):
                with st.expander(f"📍 {alan['isim']} - Kıdem Kuralları", expanded=False):
                    mevcut_kurallar = alan.get("kidem_kurallari", {})

                    for grup in grup_isimleri:
                        cols = st.columns([3, 1, 1])

                        with cols[0]:
                            st.markdown(f"**{grup}**")

                        with cols[1]:
                            mevcut_min = mevcut_kurallar.get(grup, {}).get("min", 0)
                            yeni_min = st.number_input(
                                f"Min",
                                min_value=0, max_value=10,
                                value=mevcut_min,
                                key=f"kidem_min_{i}_{grup}",
                                help=f"Günde en az kaç {grup}"
                            )

                        with cols[2]:
                            mevcut_max = mevcut_kurallar.get(grup, {}).get("max", 0)
                            yeni_max = st.number_input(
                                f"Max",
                                min_value=0, max_value=10,
                                value=mevcut_max,
                                key=f"kidem_max_{i}_{grup}",
                                help=f"Günde en fazla kaç {grup} (0=sınırsız)"
                            )

                        # Kuralları güncelle
                        if yeni_min > 0 or yeni_max > 0:
                            st.session_state["alanlar"][i].setdefault("kidem_kurallari", {})[grup] = {
                                "min": yeni_min,
                                "max": yeni_max if yeni_max > 0 else None
                            }
                        elif grup in st.session_state["alanlar"][i].get("kidem_kurallari", {}):
                            del st.session_state["alanlar"][i]["kidem_kurallari"][grup]
    else:
        # Alan modu kapalı - bilgi göster
        st.caption("Çoklu alan modu kapalı. Tek alan (eski mod) kullanılacak.")
