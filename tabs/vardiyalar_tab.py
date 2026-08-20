"""
Vardiyalar sekmesi — Vardiya tipi tanımları ve eşleştirmeler.
"""

import streamlit as st
from models import VardiyaTipi, HAZIR_VARDIYALAR


def render_vardiyalar_tab():
    st.subheader("⏰ Vardiya Tipleri")

    st.info("""
    **Vardiya Sistemi**: Farklı süreli vardiyalar tanımlayabilirsiniz (8s, 12s, 24s vs.).
    Her alan için hangi vardiyaların geçerli olduğunu belirleyebilirsiniz.
    """)

    # ====== HAZIR ŞABLONLAR ======
    st.markdown("### 📋 Hazır Şablonlar")
    st.caption("Sık kullanılan vardiya tiplerini ekleyin:")

    mevcut_vardiyalar = st.session_state.get("vardiya_tipleri", [])
    mevcut_isimler = [v["isim"] for v in mevcut_vardiyalar]

    # Şablonları grid olarak göster
    cols = st.columns(4)
    for i, sablon in enumerate(HAZIR_VARDIYALAR):
        with cols[i % 4]:
            zaten_var = sablon.isim in mevcut_isimler
            if st.button(
                f"{'✓ ' if zaten_var else '+'} {sablon.isim}",
                key=f"sablon_{i}",
                disabled=zaten_var,
                use_container_width=True
            ):
                st.session_state.setdefault("vardiya_tipleri", []).append({
                    "isim": sablon.isim,
                    "baslangic": sablon.baslangic,
                    "bitis": sablon.bitis,
                    "renk": sablon.renk
                })
                st.rerun()

    st.divider()

    # ====== ÖZEL VARDİYA EKLE ======
    st.markdown("### ➕ Özel Vardiya Ekle")

    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        yeni_vardiya_isim = st.text_input("Vardiya adı", placeholder="Örn: Özel Gece", key="yeni_vardiya_isim")
    with col2:
        yeni_baslangic = st.time_input("Başlangıç", value=None, key="yeni_vardiya_bas")
    with col3:
        yeni_bitis = st.time_input("Bitiş", value=None, key="yeni_vardiya_bit")
    with col4:
        yeni_vardiya_min_staff = st.number_input(
            "Günlük Min. Kişi",
            min_value=1, max_value=50, value=1,
            key="yeni_vardiya_min_staff",
            help="Bu vardiyada HER GÜN en az kaç kişi nöbet tutmalı? Örn: 1"
        )
    with col5:
        yeni_vardiya_renk = st.color_picker("Renk", value="#2196F3", key="yeni_vardiya_renk")

    if st.button("➕ Vardiya Ekle", key="vardiya_ekle_btn"):
        if yeni_vardiya_isim.strip() and yeni_baslangic and yeni_bitis:
            if yeni_vardiya_isim.strip() not in mevcut_isimler:
                st.session_state.setdefault("vardiya_tipleri", []).append({
                    "isim": yeni_vardiya_isim.strip(),
                    "baslangic": yeni_baslangic.strftime("%H:%M"),
                    "bitis": yeni_bitis.strftime("%H:%M"),
                    "minimum_staffing": yeni_vardiya_min_staff,
                    "renk": yeni_vardiya_renk
                })
                st.rerun()
            else:
                st.error("Bu isimde bir vardiya zaten var!")
        else:
            st.error("Tüm alanları doldurun!")

    st.divider()

    # ====== MEVCUT VARDİYALAR ======
    st.markdown("### 📋 Aktif Vardiyalar")

    if not mevcut_vardiyalar:
        st.caption("Henüz vardiya tanımlanmamış. Yukarıdan şablon seçin veya özel vardiya ekleyin.")
    else:
        for i, v in enumerate(mevcut_vardiyalar):
            # Saat hesapla
            try:
                vt = VardiyaTipi(v["isim"], v["baslangic"], v["bitis"], v.get("renk", "#808080"))
                saat = vt.saat
            except:
                saat = "?"

            col1, col2, col3, col4, col5 = st.columns([4, 2, 1, 1, 1])

            with col1:
                st.markdown(
                    f"<span style='color:{v.get('renk', '#808080')}'>●</span> **{v['isim']}**",
                    unsafe_allow_html=True
                )
            with col2:
                st.caption(f"{v['baslangic']} → {v['bitis']} ({saat}s)")
            with col3:
                current_min_staff = v.get("minimum_staffing", 1)
                yeni_min_staff = st.number_input(
                    "Günlük Min. Kişi",
                    min_value=1, max_value=50,
                    value=current_min_staff,
                    key=f"vardiya_min_staff_{i}",
                    label_visibility="collapsed"
                )
                if yeni_min_staff != current_min_staff:
                    st.session_state["vardiya_tipleri"][i]["minimum_staffing"] = yeni_min_staff
            with col4:
                yeni_renk = st.color_picker(
                    "Renk",
                    value=v.get("renk", "#808080"),
                    key=f"vardiya_renk_{i}",
                    label_visibility="collapsed"
                )
                if yeni_renk != v.get("renk"):
                    st.session_state["vardiya_tipleri"][i]["renk"] = yeni_renk
            with col5:
                if st.button("🗑️", key=f"vardiya_sil_{i}"):
                    st.session_state["vardiya_tipleri"].pop(i)
                    st.rerun()

    st.divider()

    # ====== ALAN-VARDİYA EŞLEŞTİRME ======
    st.markdown("### 🏢 Alan-Vardiya Eşleştirmesi")
    st.caption("Her alan için hangi vardiyaların geçerli olduğunu seçin.")

    alanlar = st.session_state.get("alanlar", [])
    vardiya_isimleri = [v["isim"] for v in mevcut_vardiyalar]

    if not alanlar:
        st.info("Önce Alanlar sekmesinde çoklu alan modunu aktifleştirin ve alan ekleyin.")
    elif not mevcut_vardiyalar:
        st.info("Önce yukarıdan vardiya tipleri ekleyin.")
    else:
        for i, alan in enumerate(alanlar):
            mevcut_vardiya_atamalari = alan.get("vardiya_tipleri", [])

            secilen = st.multiselect(
                f"📍 {alan['isim']}",
                options=vardiya_isimleri,
                default=[v for v in mevcut_vardiya_atamalari if v in vardiya_isimleri],
                key=f"alan_vardiya_{i}",
                placeholder="Tüm vardiyalar"
            )

            st.session_state["alanlar"][i]["vardiya_tipleri"] = secilen

    st.divider()

    # ====== PERSONEL VARDİYA KISITLARI ======
    st.markdown("### 👤 Personel Vardiya Kısıtları")
    st.caption("Bazı personeller sadece belirli vardiyalarda çalışabilir.")

    personeller = st.session_state.get("personel_list", [])

    if not personeller:
        st.info("Önce Kişiler sekmesinde personel ekleyin.")
    elif not mevcut_vardiyalar:
        st.info("Önce yukarıdan vardiya tipleri ekleyin.")
    else:
        personel_vardiya_kisitlari = st.session_state.get("personel_vardiya_kisitlari", {})

        with st.expander("Vardiya kısıtları düzenle", expanded=False):
            for p in personeller:
                mevcut = personel_vardiya_kisitlari.get(p, [])

                secilen = st.multiselect(
                    f"{p}",
                    options=vardiya_isimleri,
                    default=[v for v in mevcut if v in vardiya_isimleri],
                    key=f"personel_vardiya_{p}",
                    placeholder="Tüm vardiyalar"
                )

                if secilen:
                    st.session_state.setdefault("personel_vardiya_kisitlari", {})[p] = secilen
                elif p in st.session_state.get("personel_vardiya_kisitlari", {}):
                    del st.session_state["personel_vardiya_kisitlari"][p]

    st.divider()

    # ====== SAAT DENGESİ AYARI ======
    st.markdown("### ⚖️ Denge Ayarları")

    saat_denge = st.checkbox(
        "Saat bazlı denge",
        value=st.session_state.get("saat_bazli_denge", True),
        help="Açık: Toplam çalışma saati dengeli dağıtılır. Kapalı: Vardiya sayısı dengeli dağıtılır."
    )
    st.session_state["saat_bazli_denge"] = saat_denge

    st.divider()

    # ====== MİNİMUM STAFFING AYARI ======
    st.markdown("### 🚨 Minimum Personel Kuralı")

    enforce_staffing = st.checkbox(
        "Her vardiyada minimum 1 personel zorunlu (Hard Constraint)",
        value=st.session_state.get("enforce_minimum_staffing", True),
        help="✅ Açık: Her vardiyada mutlaka en az 1 kişi olmalı. Çözüm bulunamazsa hangi vardiya boş kalacağını gösterir.\n"
             "❌ Kapalı: Boş vardiyalara izin verir ama yüksek ceza puanı uygular. Acil durumlar için esnek çözüm sağlar."
    )
    st.session_state["enforce_minimum_staffing"] = enforce_staffing

    if not enforce_staffing:
        st.warning("⚠️ **Dikkat:** Bu ayar kapalıysa bazı vardiyalar boş kalabilir!")
