"""
Kıdem sekmesi — Kıdem grupları ve personel atamaları.
"""

import streamlit as st
from models import VardiyaTipi


def render_kidem_tab():
    st.subheader("🎖️ Kıdem Grupları")

    st.info("""
    **Kıdem Grupları**: Personeli gruplara ayırabilirsiniz (örn: Asistan, Uzman, Profesör).
    Her grup için varsayılan nöbet sayısı belirleyebilir, alan bazlı kurallar tanımlayabilirsiniz.
    """)

    # ====== GRUP TANIMLAMA ======
    st.markdown("### ➕ Grup Ekle")
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        yeni_grup_isim = st.text_input("Grup adı", placeholder="Örn: Uzman", key="yeni_grup_isim")
    with col2:
        yeni_grup_hedef = st.number_input("Hedef nöbet", min_value=0, max_value=31, value=7, key="yeni_grup_hedef", help="Bu gruptaki personelin varsayılan aylık nöbet sayısı")
    with col3:
        yeni_grup_renk = st.color_picker("Renk", value="#4CAF50", key="yeni_grup_renk")

    if st.button("➕ Grup Ekle", key="grup_ekle_btn"):
        if yeni_grup_isim.strip():
            mevcut_gruplar = st.session_state.get("kidem_gruplari", [])
            mevcut_isimler = [g["isim"] for g in mevcut_gruplar]
            if yeni_grup_isim.strip() not in mevcut_isimler:
                st.session_state.setdefault("kidem_gruplari", []).append({
                    "isim": yeni_grup_isim.strip(),
                    "renk": yeni_grup_renk,
                    "varsayilan_hedef": yeni_grup_hedef
                })
                st.rerun()
            else:
                st.error("Bu isimde bir grup zaten var!")
        else:
            st.error("Grup adı boş olamaz!")

    st.divider()

    # ====== MEVCUT GRUPLAR ======
    st.markdown("### 📋 Mevcut Gruplar")

    kidem_gruplari = st.session_state.get("kidem_gruplari", [])
    vardiyalar = st.session_state.get("vardiya_tipleri", [])

    if not kidem_gruplari:
        st.caption("Henüz kıdem grubu tanımlanmamış.")
    else:
        for i, grup in enumerate(kidem_gruplari):
            # Gruptaki kişi sayısını hesapla
            personel_gruplari = st.session_state.get("personel_kidem_gruplari", {})
            kisi_sayisi = sum(1 for g in personel_gruplari.values() if g == grup["isim"])

            with st.expander(
                f"● {grup['isim']} ({kisi_sayisi} kişi)",
                expanded=False
            ):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.markdown(
                        f"<span style='color:{grup.get('renk', '#808080')}; font-size:24px'>●</span>",
                        unsafe_allow_html=True
                    )
                    yeni_renk = st.color_picker(
                        "Renk",
                        value=grup.get("renk", "#808080"),
                        key=f"grup_renk_{i}"
                    )
                    if yeni_renk != grup.get("renk"):
                        st.session_state["kidem_gruplari"][i]["renk"] = yeni_renk

                with col3:
                    if st.button("🗑️ Grubu Sil", key=f"grup_sil_{i}"):
                        # Önce bu gruptaki personellerin atamalarını kaldır
                        personel_gruplari = st.session_state.get("personel_kidem_gruplari", {})
                        to_remove = [p for p, g in personel_gruplari.items() if g == grup["isim"]]
                        for p in to_remove:
                            del st.session_state["personel_kidem_gruplari"][p]

                        st.session_state["kidem_gruplari"].pop(i)
                        st.rerun()

                st.divider()

                # VARDIYA BAZLI HEDEF veya TOPLAM HEDEF
                if vardiyalar:
                    st.markdown("**Vardiya Bazlı Hedefler:**")

                    vardiya_hedefleri = grup.get("vardiya_hedefleri", {})
                    toplam_nobet = 0
                    toplam_saat = 0

                    # Her vardiya için hedef input
                    vcols = st.columns(min(len(vardiyalar), 4))
                    for v_idx, v in enumerate(vardiyalar):
                        with vcols[v_idx % 4]:
                            mevcut = vardiya_hedefleri.get(v["isim"], 0)
                            yeni = st.number_input(
                                f"{v['isim']}",
                                min_value=0, max_value=31,
                                value=int(mevcut),
                                key=f"grup_{i}_vardiya_{v_idx}",
                                help=f"Bu gruptan {v['isim']} vardiyasında kaç nöbet"
                            )

                            # Güncelle
                            if yeni != mevcut:
                                if "vardiya_hedefleri" not in st.session_state["kidem_gruplari"][i]:
                                    st.session_state["kidem_gruplari"][i]["vardiya_hedefleri"] = {}
                                st.session_state["kidem_gruplari"][i]["vardiya_hedefleri"][v["isim"]] = yeni

                            # Saat hesapla
                            try:
                                vt = VardiyaTipi(v["isim"], v.get("baslangic", "08:00"), v.get("bitis", "08:00"))
                                toplam_saat += yeni * vt.saat
                            except:
                                toplam_saat += yeni * 24
                            toplam_nobet += yeni

                    st.caption(f"📊 Toplam: {toplam_nobet} nöbet, {toplam_saat} saat")

                    # Eski hedefi de güncelle (uyumluluk için)
                    st.session_state["kidem_gruplari"][i]["varsayilan_hedef"] = toplam_nobet

                else:
                    # Vardiya tanımlı değilse eski mod
                    st.markdown("**Toplam Nöbet Hedefi:**")
                    mevcut_hedef = grup.get("varsayilan_hedef", 7)
                    yeni_hedef = st.number_input(
                        "Hedef nöbet sayısı",
                        min_value=0, max_value=31,
                        value=mevcut_hedef if mevcut_hedef else 7,
                        key=f"grup_hedef_{i}"
                    )
                    if yeni_hedef != mevcut_hedef:
                        st.session_state["kidem_gruplari"][i]["varsayilan_hedef"] = yeni_hedef

                    st.caption("💡 Vardiyalar sekmesinden vardiya tanımlarsanız, vardiya bazlı hedef girebilirsiniz.")

    st.divider()

    # ====== GRUPLARA PERSONEL ATAMA ======
    st.markdown("### 👤 Gruplara Personel Atama")

    personeller = st.session_state.get("personel_list", [])

    if not personeller:
        st.warning("Önce Kişiler sekmesinde personel ekleyin.")
    elif not kidem_gruplari:
        st.warning("Önce yukarıda kıdem grupları tanımlayın.")
    else:
        st.caption("Her grup için personel seçin. Bir personel sadece bir grupta olabilir.")

        personel_kidem = st.session_state.get("personel_kidem_gruplari", {})

        # Personel listesinde olmayan atamaları temizle (demo değişikliği için)
        gecersiz_atamalar = [p for p in personel_kidem.keys() if p not in personeller]
        for p in gecersiz_atamalar:
            del personel_kidem[p]

        for i, grup in enumerate(kidem_gruplari):
            grup_isim = grup["isim"]
            grup_renk = grup.get("renk", "#808080")

            # Bu grupta olan personeller (sadece mevcut personel listesinde olanlar)
            mevcut_uyeler = [p for p, g in personel_kidem.items() if g == grup_isim and p in personeller]

            # Başka gruplarda olmayan personeller (seçilebilir)
            baska_gruplarda = [p for p, g in personel_kidem.items() if g != grup_isim]
            musait_personeller = [p for p in personeller if p not in baska_gruplarda or p in mevcut_uyeler]

            # Default değerlerin options'da olduğundan emin ol
            valid_defaults = [p for p in mevcut_uyeler if p in musait_personeller]

            with st.expander(f"● {grup_isim} ({len(valid_defaults)} kişi)", expanded=len(valid_defaults) == 0):
                secilen = st.multiselect(
                    f"Personel seç",
                    options=musait_personeller,
                    default=valid_defaults,
                    key=f"grup_personel_{i}",
                    label_visibility="collapsed"
                )

                # Atamaları güncelle
                # Önce bu gruptan çıkarılanları temizle
                for p in mevcut_uyeler:
                    if p not in secilen:
                        if p in st.session_state.get("personel_kidem_gruplari", {}):
                            del st.session_state["personel_kidem_gruplari"][p]

                # Yeni eklenenler
                for p in secilen:
                    st.session_state.setdefault("personel_kidem_gruplari", {})[p] = grup_isim

        # Atanmamış personelleri göster
        atanmamis = [p for p in personeller if p not in personel_kidem]
        if atanmamis:
            st.info(f"⚠️ Atanmamış personeller ({len(atanmamis)}): {', '.join(atanmamis)}")
