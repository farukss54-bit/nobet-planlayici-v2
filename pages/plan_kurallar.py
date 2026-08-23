"""
pages/plan_kurallar.py — Plan Akışı Adım 3: Kurallar ve Tercihler

Bu sayfa, aylık plan oluşturma akışının üçüncü adımıdır.
Sol sütunda kesin kurallar (toggle/segmented), sağ sütunda tercihler (Az/Orta/Çok),
altta hazır profiller ve kapasite banner'ı bulunur.
"""

import streamlit as st
from typing import Dict

from design import render_stepper, render_card
from utils import ay_gun_sayisi


def _init_plan_kurallar() -> None:
    """Session state'i başlatır, varsayılan kuralları yükler"""
    # Kesin Kurallar
    if "kural_ardisik_yasak" not in st.session_state:
        st.session_state.kural_ardisik_yasak = True

    if "kural_gunasiri_limit" not in st.session_state:
        st.session_state.kural_gunasiri_limit = 2

    if "kural_min_kisi_vardiya" not in st.session_state:
        st.session_state.kural_min_kisi_vardiya = True

    if "kural_min_dinlenme_saat" not in st.session_state:
        st.session_state.kural_min_dinlenme_saat = 12

    # Tercihler
    if "tercih_hafta_sonu" not in st.session_state:
        st.session_state.tercih_hafta_sonu = "Orta"

    if "tercih_tatil" not in st.session_state:
        st.session_state.tercih_tatil = "Orta"

    if "tercih_iki_gun_bosluk" not in st.session_state:
        st.session_state.tercih_iki_gun_bosluk = "Orta"

    if "tercih_istekler" not in st.session_state:
        st.session_state.tercih_istekler = "Orta"

    if "tercih_saat_dengesi" not in st.session_state:
        st.session_state.tercih_saat_dengesi = "Orta"

    # Profil seçimi için flag (widget'lardan önce işlenir)
    if "profil_degisim_flag" not in st.session_state:
        st.session_state.profil_degisim_flag = None

    # Aktif profil
    if "aktif_profil" not in st.session_state:
        st.session_state.aktif_profil = "Dengeli"

    # Profil değişimi varsa widget'lar render edilmeden önce uygula
    if st.session_state.profil_degisim_flag is not None:
        profil = st.session_state.profil_degisim_flag

        if profil == "Dengeli":
            st.session_state.tercih_hafta_sonu = "Orta"
            st.session_state.tercih_tatil = "Orta"
            st.session_state.tercih_iki_gun_bosluk = "Orta"
            st.session_state.tercih_istekler = "Orta"
            st.session_state.tercih_saat_dengesi = "Orta"
        elif profil == "Adalet odaklı":
            st.session_state.tercih_hafta_sonu = "Çok"
            st.session_state.tercih_tatil = "Çok"
            st.session_state.tercih_iki_gun_bosluk = "Az"
            st.session_state.tercih_istekler = "Az"
            st.session_state.tercih_saat_dengesi = "Çok"
        elif profil == "Dinlenme odaklı":
            st.session_state.tercih_hafta_sonu = "Az"
            st.session_state.tercih_tatil = "Az"
            st.session_state.tercih_iki_gun_bosluk = "Çok"
            st.session_state.tercih_istekler = "Çok"
            st.session_state.tercih_saat_dengesi = "Orta"

        st.session_state.aktif_profil = profil
        st.session_state.profil_degisim_flag = None  # Flag'i temizle


def _render_kesin_kurallar() -> None:
    """Sol sütun - Kesin Kurallar widget'ları"""
    # 1. Arka arkaya iki gün nöbet olmaz
    st.toggle(
        "Arka arkaya iki gün nöbet olmaz",
        key="kural_ardisik_yasak"
    )
    st.caption("Personel art arda iki gün nöbet tutamaz (hard constraint)")

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # 2. Günaşırı nöbet sınırı
    st.segmented_control(
        "Günaşırı nöbet sınırı",
        options=[1, 2, 3],
        default=st.session_state.kural_gunasiri_limit,
        key="kural_gunasiri_limit"
    )
    st.caption("Bir hafta içinde en fazla X kez günaşırı nöbet")

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # 3. Her vardiyada en az 1 kişi
    st.toggle(
        "Her vardiyada en az 1 kişi",
        key="kural_min_kisi_vardiya"
    )
    st.caption("Hiçbir vardiya boş kalmaz (hard constraint)")

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # 4. İki nöbet arası dinlenme
    st.segmented_control(
        "En az dinlenme (saat)",
        options=[8, 12, 24],
        default=st.session_state.kural_min_dinlenme_saat,
        key="kural_min_dinlenme_saat"
    )
    st.caption("İki nöbet arasında en az X saat boşluk olmalı")


def _render_tercihler() -> None:
    """Sağ sütun - Tercihler widget'ları"""
    tercihler = [
        ("Hafta sonu dengesi", "tercih_hafta_sonu", "Herkes benzer sayıda Cts/Paz nöbeti tutsun"),
        ("Resmi tatiller", "tercih_tatil", "Bayram/tatil günlerinde adil dağılım"),
        ("Nöbetler arası boşluk", "tercih_iki_gun_bosluk", "İki nöbet arasında 2 gün boş bırakmaya çalış"),
        ("İstekler", "tercih_istekler", "Personelin tercih ettiği günlere öncelik ver"),
        ("Saat dengesi", "tercih_saat_dengesi", "Herkes benzer toplam saat çalışsın")
    ]

    for idx, (label, key, aciklama) in enumerate(tercihler):
        st.segmented_control(
            label,
            options=["Az", "Orta", "Çok"],
            default=st.session_state.get(key, "Orta"),
            key=key
        )
        st.caption(aciklama)

        if idx < len(tercihler) - 1:
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)


def _render_profil_butonlari() -> None:
    """Hazır profil butonları render eder"""
    st.caption("Hızlı başlangıç için bir profil seçin, sonra manuel ayarlayabilirsiniz.")

    col1, col2, col3 = st.columns(3)

    aktif = st.session_state.get("aktif_profil", "Dengeli")

    with col1:
        if st.button(
            "Dengeli (Önerilen)",
            type="primary" if aktif == "Dengeli" else "secondary",
            use_container_width=True,
            key="btn_dengeli"
        ):
            st.session_state.profil_degisim_flag = "Dengeli"
            st.rerun()

    with col2:
        if st.button(
            "Adalet Odaklı",
            type="primary" if aktif == "Adalet odaklı" else "secondary",
            use_container_width=True,
            key="btn_adalet"
        ):
            st.session_state.profil_degisim_flag = "Adalet odaklı"
            st.rerun()

    with col3:
        if st.button(
            "Dinlenme Odaklı",
            type="primary" if aktif == "Dinlenme odaklı" else "secondary",
            use_container_width=True,
            key="btn_dinlenme"
        ):
            st.session_state.profil_degisim_flag = "Dinlenme odaklı"
            st.rerun()


def _hesapla_kapasite_banner() -> str:
    """Kapasite bilgi banner'ı HTML olarak döndürür"""
    gun_sayisi = ay_gun_sayisi(st.session_state.plan_yil, st.session_state.plan_ay)
    toplam_personel = len(st.session_state.plan_personel)

    # Alan kontenjanı toplamı
    alan_kontenjan = sum(
        a.gunluk_kontenjan
        for a in st.session_state.ayarlar.alanlar
        if a.aktif
    )
    if alan_kontenjan == 0:
        alan_kontenjan = 1  # Fallback

    # Vardiya sayısı
    vardiya_sayisi = len(st.session_state.ayarlar.vardiya_tipleri)
    if vardiya_sayisi == 0:
        vardiya_sayisi = 1  # Fallback

    # Toplam nöbet ihtiyacı
    toplam_ihtiyac = gun_sayisi * alan_kontenjan * vardiya_sayisi

    # Kişi başı ortalama
    if toplam_personel > 0:
        kisi_basi = toplam_ihtiyac / toplam_personel
        banner_text = (
            f'📊 <strong>Mevcut Kapasite:</strong> '
            f'{toplam_personel} kişi ile {gun_sayisi} günlük planda '
            f'~{kisi_basi:.0f} nöbet/kişi bekleniyor.'
        )
    else:
        banner_text = '⚠️ <strong>Uyarı:</strong> Personel eklenmemiş, kapasite hesaplanamıyor.'

    return (
        f'<div style="background:#e6f4f5; padding:12px; border-radius:6px; '
        f'margin-top:20px; font-family:system-ui; font-size:13px;">'
        f'{banner_text}'
        f'</div>'
    )


def _render_navigation() -> None:
    """Geri/İleri navigasyon butonları"""
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← İzinler", type="secondary", use_container_width=True):
            st.session_state.plan_step = 1
            st.rerun()

    with col3:
        if st.button("Çizelgeyi Oluştur →", type="primary", use_container_width=True):
            st.session_state.plan_step = 3
            st.rerun()


def show_plan_kurallar() -> None:
    """Ana giriş noktası - Kurallar ve Tercihler sayfası"""
    _init_plan_kurallar()

    # STEPPER
    st.markdown(render_stepper(3, 4), unsafe_allow_html=True)

    # BAŞLIK
    st.markdown("## Kurallar ve Tercihler")
    st.caption("Kesin kurallar mutlaka uygulanır, tercihler solver'a rehberlik eder.")
    st.markdown("<br>", unsafe_allow_html=True)

    # 2 SÜTUN: Kesin Kurallar + Tercihler
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔒 Kesin Kurallar")
        _render_kesin_kurallar()

    with col2:
        st.subheader("⚖️ Tercihler")
        _render_tercihler()

    # HAZIR PROFİLLER
    st.markdown("---")
    st.markdown("### Hazır Profiller")
    _render_profil_butonlari()

    # KAPASİTE BANNER
    st.markdown(_hesapla_kapasite_banner(), unsafe_allow_html=True)

    # NAVİGASYON
    _render_navigation()
