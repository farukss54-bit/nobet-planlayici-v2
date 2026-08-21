"""
pages/plan_izinler.py — Plan Akışı Adım 2: İzinler ve Tercihler

Bu sayfa, aylık plan oluşturma akışının ikinci adımıdır.
Kullanıcı her personel için izin günleri, tercih günleri ve bloklu hafta günlerini girer.
Ay şeridi ile görsel geri bildirim sağlanır.
"""

import streamlit as st
from typing import Dict, List, Set
from datetime import datetime

from design import render_stepper, render_card, render_badge
from utils import gun_parse, ay_gun_sayisi, resmi_tatiller, hafta_gunu


# Ay isimleri
AY_ISIMLERI = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}


def _init_plan_izinler() -> None:
    """Session state'i başlatır, izin/tercih dict'lerini kurar"""
    # İzin dict'leri
    if "plan_izinler" not in st.session_state:
        st.session_state.plan_izinler = {}

    if "plan_tercihler" not in st.session_state:
        st.session_state.plan_tercihler = {}

    if "plan_bloklu_gunler" not in st.session_state:
        st.session_state.plan_bloklu_gunler = {}

    if "plan_manuel_tatiller" not in st.session_state:
        st.session_state.plan_manuel_tatiller = []

    # Her personel için default değer oluştur
    for p in st.session_state.plan_personel:
        isim = p["isim"]
        st.session_state.plan_izinler.setdefault(isim, [])
        st.session_state.plan_tercihler.setdefault(isim, [])
        st.session_state.plan_bloklu_gunler.setdefault(isim, [])


def _render_ay_seridi(
    personel_isim: str,
    yil: int,
    ay: int,
    gun_sayisi: int,
    izinler: Set[int],
    tercihler: Set[int]
) -> None:
    """31 günlük ay şeridini 7 hafta × 7 gün grid olarak render eder

    Args:
        personel_isim: Personel adı
        yil: Plan yılı
        ay: Plan ayı
        gun_sayisi: Ayın gün sayısı
        izinler: İzinli günler seti
        tercihler: Tercih edilen günler seti
    """
    max_hafta = (gun_sayisi + 6) // 7  # 5-6 hafta

    st.markdown("<div style='margin-top: 12px; margin-bottom: 8px;'>", unsafe_allow_html=True)

    for hafta_idx in range(max_hafta):
        cols = st.columns(7)

        for gun_idx in range(7):
            gun = hafta_idx * 7 + gun_idx + 1

            with cols[gun_idx]:
                if gun > gun_sayisi:
                    # Ayın bittiği boş kareler
                    st.markdown(
                        '<div style="width:30px;height:30px;"></div>',
                        unsafe_allow_html=True
                    )
                else:
                    # Renk belirleme
                    if gun in izinler:
                        bg_color = "#ff6b6b"  # Kırmızı
                        text_color = "#ffffff"
                    elif gun in tercihler:
                        bg_color = "#4dabf7"  # Açık mavi
                        text_color = "#ffffff"
                    else:
                        bg_color = "#e8e5e0"  # Açık gri (border rengi)
                        text_color = "#1a1a2e"  # Koyu metin

                    # 30×30 kare
                    st.markdown(
                        f'<div style="'
                        f'width:30px;'
                        f'height:30px;'
                        f'background:{bg_color};'
                        f'color:{text_color};'
                        f'border-radius:4px;'
                        f'display:flex;'
                        f'align-items:center;'
                        f'justify-content:center;'
                        f'font-family:monospace;'
                        f'font-size:11px;'
                        f'font-weight:600;'
                        f'">{gun}</div>',
                        unsafe_allow_html=True
                    )

    st.markdown("</div>", unsafe_allow_html=True)


def _hesapla_kalan_uygun_gun(
    personel_isim: str,
    gun_sayisi: int,
    izinler: Set[int],
    tercihler: Set[int],
    bloklu_gunler: List[str],
    yil: int,
    ay: int
) -> int:
    """Personelin çalışabileceği gün sayısını hesaplar

    Returns:
        Kalan uygun gün sayısı (izinler ve bloklu günler düşüldükten sonra)
    """
    # Bloklu hafta günlerini gün numaralarına dönüştür
    bloklu_gun_numaralari = set()

    hafta_gun_map = {
        "Pazartesi": 0,
        "Salı": 1,
        "Çarşamba": 2,
        "Perşembe": 3,
        "Cuma": 4,
        "Cumartesi": 5,
        "Pazar": 6
    }

    for gun in range(1, gun_sayisi + 1):
        gun_hafta_idx = hafta_gunu(yil, ay, gun)  # 0=Pzt, 6=Paz

        for bloklu_gun_adi in bloklu_gunler:
            if bloklu_gun_adi in hafta_gun_map:
                if hafta_gun_map[bloklu_gun_adi] == gun_hafta_idx:
                    bloklu_gun_numaralari.add(gun)

    # Toplam bloklu gün sayısı
    tum_bloklu = izinler | bloklu_gun_numaralari

    kalan = gun_sayisi - len(tum_bloklu)
    return max(0, kalan)


def _check_cakisma_uyarilari(
    gun_sayisi: int,
    personeller: List[Dict],
    izinler_map: Dict[str, List[int]]
) -> List[str]:
    """Her gün için izinli kişi sayısını kontrol eder

    Args:
        gun_sayisi: Ayın gün sayısı
        personeller: Personel listesi
        izinler_map: {isim: [gun1, gun2, ...]}

    Returns:
        Uyarı mesajları listesi
    """
    uyarilar = []
    toplam_personel = len(personeller)

    if toplam_personel == 0:
        return uyarilar

    for gun in range(1, gun_sayisi + 1):
        izinli_sayisi = sum(
            1 for p in personeller
            if gun in izinler_map.get(p["isim"], [])
        )

        if izinli_sayisi > 0:
            oran = izinli_sayisi / toplam_personel

            # %40 eşiği
            if oran >= 0.4:
                ay_adi = AY_ISIMLERI[st.session_state.plan_ay]
                uyarilar.append(
                    f"{gun} {ay_adi} tarihinde {izinli_sayisi} kişi izinli — "
                    f"o gün kadro darlaşıyor"
                )

    return uyarilar


def _render_personel_kart(personel: Dict, yil: int, ay: int, gun_sayisi: int) -> None:
    """Tek bir personel için kart render eder

    Args:
        personel: {"isim": "Dr. A", "kidem_grubu": "Kidemli", "hedef_nobet": 8, ...}
        yil: Plan yılı
        ay: Plan ayı
        gun_sayisi: Ayın gün sayısı
    """
    with st.container():
        # BAŞLIK: İsim + Badge + Hedef
        col1, col2 = st.columns([3, 1])

        with col1:
            isim = personel["isim"]
            kidem = personel.get("kidem_grubu", "")

            if kidem:
                kg_lower = kidem.lower()
                if kg_lower in ["kidemli", "orta", "yeni"]:
                    badge_class = f"badge-{kg_lower}"
                else:
                    badge_class = "badge"

                badge_html = render_badge(kidem, badge_class)
                st.markdown(
                    f'<h4 style="margin:0;">{isim} {badge_html}</h4>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f'<h4 style="margin:0;">{isim}</h4>', unsafe_allow_html=True)

        with col2:
            hedef = personel.get("hedef_nobet", 0)
            st.markdown(
                f'<p style="text-align:right; color:#6b6b7b; margin:0;">Hedef: {hedef}</p>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # 3 SÜTUN INPUT
        col1, col2, col3 = st.columns(3)

        with col1:
            mevcut_izinler = st.session_state.plan_izinler.get(isim, [])
            izin_input = st.text_input(
                "İzinli Günler",
                value=",".join(map(str, mevcut_izinler)) if mevcut_izinler else "",
                placeholder="5-9, 14, 22",
                key=f"izin_{isim}",
                help="Örnek: 5-9, 14, 22"
            )
            izinler = gun_parse(izin_input, gun_sayisi)
            st.session_state.plan_izinler[isim] = sorted(izinler)

            if izinler:
                st.caption(f"✓ {len(izinler)} gün")

        with col2:
            mevcut_tercihler = st.session_state.plan_tercihler.get(isim, [])
            tercih_input = st.text_input(
                "Tercih Günleri",
                value=",".join(map(str, mevcut_tercihler)) if mevcut_tercihler else "",
                placeholder="10, 15, 20",
                key=f"tercih_{isim}",
                help="Tercih edilen nöbet günleri (soft constraint)"
            )
            tercihler = gun_parse(tercih_input, gun_sayisi)
            st.session_state.plan_tercihler[isim] = sorted(tercihler)

            if tercihler:
                st.caption(f"✓ {len(tercihler)} gün")

        with col3:
            bloklu = st.multiselect(
                "Bloklu Hafta Günleri",
                ["Pazartesi", "Salı", "Çarşamba", "Perşembe",
                 "Cuma", "Cumartesi", "Pazar"],
                default=st.session_state.plan_bloklu_gunler.get(isim, []),
                key=f"bloklu_{isim}",
                help="Her hafta bu günlerde nöbet tutamaz"
            )
            st.session_state.plan_bloklu_gunler[isim] = bloklu

        # AY ŞERİDİ
        _render_ay_seridi(
            isim,
            yil,
            ay,
            gun_sayisi,
            set(izinler),
            set(tercihler)
        )

        # ALT METİN (istatistikler)
        kalan = _hesapla_kalan_uygun_gun(
            isim,
            gun_sayisi,
            set(izinler),
            set(tercihler),
            bloklu,
            yil,
            ay
        )

        st.caption(
            f"{len(izinler)} izinli gün · {len(tercihler)} tercih · "
            f"kalan uygun gün {kalan}"
        )

        st.markdown("---")


def _render_manuel_tatiller(yil: int, ay: int, gun_sayisi: int) -> None:
    """Otomatik resmi tatiller + manuel tatil girişi bölümünü render eder

    Args:
        yil: Plan yılı
        ay: Plan ayı
        gun_sayisi: Ayın gün sayısı
    """
    st.divider()
    st.subheader("🎌 Resmi Tatiller")

    # Otomatik tatiller
    auto_holidays = resmi_tatiller(yil, ay)

    if auto_holidays:
        st.success("✓ Otomatik tespit edilen tatiller:")
        for gun, isim in sorted(auto_holidays.items()):
            st.write(f"  • {gun}. gün - {isim}")
    else:
        st.info("Bu ay resmi tatil bulunmuyor.")

    # Manuel input
    st.caption("İdari izin veya ekstra tatil günü varsa ekleyin:")

    mevcut_manuel = st.session_state.plan_manuel_tatiller
    manuel_input = st.text_input(
        "Manuel tatil günleri",
        value=",".join(map(str, mevcut_manuel)) if mevcut_manuel else "",
        placeholder="15, 16",
        key="manuel_tatiller_input",
        help="Tüm personel için geçerli ekstra tatil günleri"
    )

    manuel_gunler = gun_parse(manuel_input, gun_sayisi)
    st.session_state.plan_manuel_tatiller = sorted(manuel_gunler)

    if manuel_gunler:
        st.caption(f"✓ Eklenecek: {sorted(manuel_gunler)}")


def _render_navigation() -> None:
    """Geri/İleri navigasyon butonlarını render eder"""
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Ekip", type="secondary", use_container_width=True):
            st.session_state.plan_step = 0
            st.rerun()

    with col3:
        if st.button(
            "Kurallara Geç →",
            type="primary",
            use_container_width=True
        ):
            st.session_state.plan_step = 2
            st.rerun()


def show_plan_izinler() -> None:
    """Ana giriş noktası - tüm bileşenleri birleştirir"""
    _init_plan_izinler()

    # Stepper (2/4)
    st.markdown(render_stepper(2, 4), unsafe_allow_html=True)

    # Başlık
    ay_text = f"{AY_ISIMLERI[st.session_state.plan_ay]} {st.session_state.plan_yil}"
    st.markdown(f"## İzinler ve Tercihler · {ay_text}")
    st.caption("Gün numaralarını virgülle, aralıkları tire ile yaz. Örnek: 5-9, 14, 22.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ÇAKIŞMA UYARILARI
    gun_sayisi = ay_gun_sayisi(st.session_state.plan_yil, st.session_state.plan_ay)
    uyarilar = _check_cakisma_uyarilari(
        gun_sayisi,
        st.session_state.plan_personel,
        st.session_state.plan_izinler
    )

    if uyarilar:
        for uyari in uyarilar:
            st.warning(f"⚠️ {uyari}")

    # PERSONEL KARTLARI
    for personel in st.session_state.plan_personel:
        _render_personel_kart(
            personel,
            st.session_state.plan_yil,
            st.session_state.plan_ay,
            gun_sayisi
        )

    # MANUEL TATİLLER
    _render_manuel_tatiller(
        st.session_state.plan_yil,
        st.session_state.plan_ay,
        gun_sayisi
    )

    # NAVİGASYON
    _render_navigation()
