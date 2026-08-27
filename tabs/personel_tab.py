"""
Kişiler sekmesi — Personel listesi ve hedef nöbet sayıları.
"""

import streamlit as st

from storage import ayarlari_kaydet
from utils import personel_referanslarini_temizle, hesapla_otomatik_hedef, ay_gun_sayisi


KAYIT_HATASI_MESAJI = "Kaydedilemedi — değişiklikler kalıcı olmayabilir"


def render_personel_tab(session_to_ayarlar_func=None):
    st.subheader("👥 Kişiler ve Hedefler")
    degisiklik_yapildi = False

    # st.rerun() sonrası gosterilmesi gereken kayit hatasi (rerun oncesi
    # st.error cagrisi rerun ile birlikte kaybolur, bu yuzden session_state
    # uzerinden bir sonraki calismaya tasinir).
    bekleyen_hata = st.session_state.pop("_kayit_hata_mesaji", None)
    if bekleyen_hata:
        st.error(bekleyen_hata)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("Yıl", min_value=2020, max_value=2100, step=1, key="yil")
    with col2:
        st.number_input("Ay", min_value=1, max_value=12, step=1, key="ay")
    with col3:
        # Widget key'ini hesaplama key'inden ayır
        # (Streamlit'te widget key'ine doğrudan atama yasak)
        current_hedef = st.session_state.get("varsayilan_hedef", 7)
        clamped_hedef = max(0, min(31, current_hedef))
        varsayilan_input = st.number_input(
            "Varsayılan hedef nöbet",
            min_value=0, max_value=31, step=1,
            value=clamped_hedef,
            key="varsayilan_hedef_input"
        )
        st.session_state["varsayilan_hedef"] = varsayilan_input

        # Varsayılan hedef değişmişse mevcut tüm personelleri senkronize et
        onceki = st.session_state.get("_varsayilan_hedef_onceki", varsayilan_input)
        if onceki != varsayilan_input and st.session_state.get("personel_list"):
            personel_sayisi_guncellenen = len(st.session_state["personel_list"])
            for p in st.session_state["personel_list"]:
                st.session_state.setdefault("personel_targets", {})[p] = varsayilan_input
            degisiklik_yapildi = True
            st.info(f"Varsayılan hedef değişti — {personel_sayisi_guncellenen} kişinin hedefi güncellendi.")
        st.session_state["_varsayilan_hedef_onceki"] = varsayilan_input

    # Otomatik hedef hesaplama kontrolü
    otomatik_aktif = st.toggle(
        "🧮 Otomatik hedef hesaplama",
        value=st.session_state.get("otomatik_hedef", True),
        key="otomatik_hedef_toggle",
        help="Açıkken solver, kişisel hedef girilmemiş personeller için otomatik hesaplanan değeri kullanır."
    )
    if otomatik_aktif != st.session_state.get("otomatik_hedef", True):
        st.session_state["otomatik_hedef"] = otomatik_aktif
        if session_to_ayarlar_func is not None:
            if not ayarlari_kaydet(session_to_ayarlar_func()):
                st.error(KAYIT_HATASI_MESAJI)

    st.divider()

    # Personel sayısı
    personel_sayisi = st.number_input(
        "Kaç personel var?",
        min_value=0, max_value=50,
        value=st.session_state.get("personel_sayisi", 0),
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

        # Silinen personellerin referanslarını temizle
        for p in removed:
            personel_referanslarini_temizle(st.session_state, p)
            degisiklik_yapildi = True

    st.session_state["personel_sayisi"] = personel_sayisi

    # Otomatik hesaplama butonu
    if st.session_state.get("otomatik_hedef", True):
        btn_col1, btn_col2 = st.columns([1, 3])
        with btn_col1:
            if st.button("🧮 Hedefleri Otomatik Hesapla", use_container_width=True):
                yil = int(st.session_state.get("yil", 2024))
                ay = int(st.session_state.get("ay", 1))
                gun_sayisi = ay_gun_sayisi(yil, ay)
                alanlar = st.session_state.get("alanlar", [])
                vardiyalar = st.session_state.get("vardiya_tipleri", [])
                izin_map = st.session_state.get("izin_map", {})
                personeller = st.session_state.get("personel_list", [])
                ardisik = st.session_state.get("ardisik_yasak", True)

                otomatik_hedefler = hesapla_otomatik_hedef(
                    gun_sayisi, alanlar, vardiyalar, personeller, izin_map, ardisik
                )

                st.session_state["personel_targets"] = otomatik_hedefler
                if otomatik_hedefler:
                    ort_hedef = round(sum(otomatik_hedefler.values()) / len(otomatik_hedefler))
                    st.session_state["varsayilan_hedef"] = max(1, ort_hedef)
                    degisiklik_yapildi = True

                if session_to_ayarlar_func is not None:
                    if not ayarlari_kaydet(session_to_ayarlar_func()):
                        st.session_state["_kayit_hata_mesaji"] = KAYIT_HATASI_MESAJI
                st.rerun()
        with btn_col2:
            st.caption("💡 Butona basınca herkese 'toplam ihtiyaç ÷ personel' formülüyle eşit nöbet dağıtılır. Sonra dilediğiniz kişiyi elle değiştirebilirsiniz.")

    st.caption("Her personelin adını ve hedef nöbet sayısını girin:")

    default_target = st.session_state.get("varsayilan_hedef", 7)

    for i in range(personel_sayisi):
        cols = st.columns([3, 1, 1])
        with cols[0]:
            eski_isim = st.session_state["personel_list"][i]
            yeni_isim = st.text_input(
                f"{i+1}. Personel",
                value=st.session_state["personel_list"][i],
                key=f"personel_name_{i}"
            )
            st.session_state["personel_list"][i] = yeni_isim
            if eski_isim != yeni_isim:
                personel_referanslarini_temizle(st.session_state, eski_isim, yeni_isim)
                degisiklik_yapildi = True

            # Anlik uyari (kaydetmeyi engellemez - cozum kapisi G2.6'da durdurur)
            if not yeni_isim.strip():
                st.warning("⚠ Boş isim")
            elif st.session_state["personel_list"].count(yeni_isim) > 1:
                st.warning(f"⚠ '{yeni_isim}' başka bir satırda da var")
        with cols[1]:
            p_name = st.session_state["personel_list"][i]
            kisisel_kayit_var = p_name in st.session_state.get("personel_targets", {})
            oto = st.checkbox(
                "Oto",
                value=not kisisel_kayit_var,
                key=f"oto_hedef_{i}",
                help="İşaretliyse bu kişi otomatik/kıdem hedef zincirini kullanır. "
                     "İşareti kaldırırsanız girdiğiniz değer — varsayılana eşit olsa bile — kalıcı olur."
            )
        with cols[2]:
            current_target = st.session_state.get("personel_targets", {}).get(p_name, default_target)
            new_target = st.number_input(
                "Hedef",
                min_value=0, max_value=31,
                value=int(current_target),
                step=1,
                key=f"target_{i}",
                disabled=oto
            )
            if oto:
                st.session_state.get("personel_targets", {}).pop(p_name, None)
            else:
                # Deger varsayilana esit olsa BILE kaydedilir - "Oto" isaretini
                # kaldirmak bilincli bir tercihtir, sessizce geri alinmaz.
                st.session_state.setdefault("personel_targets", {})[p_name] = new_target

    # Değişiklik varsa ayarları otomatik kaydet
    if degisiklik_yapildi and session_to_ayarlar_func is not None:
        if not ayarlari_kaydet(session_to_ayarlar_func()):
            st.error(KAYIT_HATASI_MESAJI)
