"""
pages/plan_ekip.py — Plan Akışı Adım 1: Ekip Yapılandırması

Bu sayfa, aylık plan oluşturma akışının ilk adımıdır.
Kullanıcı personel listesini görür, hedefleri düzenler ve otomatik hesaplama yapabilir.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List

from design import render_stepper, render_card, render_badge
from models import Ayarlar, KidemGrubu
from storage import ayarlari_yukle_veya_varsayilan
from utils import hesapla_otomatik_hedef, ay_gun_sayisi


# Ay isimleri
AY_ISIMLERI = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}


def _init_plan_ekip() -> None:
    """Session state'i başlatır"""
    # Ay bilgisi
    if "plan_yil" not in st.session_state:
        today = datetime.now()
        st.session_state.plan_yil = today.year
        st.session_state.plan_ay = today.month

    # Ayarları yükle
    if "ayarlar" not in st.session_state:
        st.session_state.ayarlar = ayarlari_yukle_veya_varsayilan()

        # Eğer ayarlar boşsa mock ayarlar oluştur
        if not st.session_state.ayarlar.kidem_gruplari:
            st.session_state.ayarlar = _create_mock_ayarlar()

    # Personel listesi - ilk yükleme
    if "plan_personel" not in st.session_state:
        if st.session_state.ayarlar.personeller:
            # Storage'dan yükle
            st.session_state.plan_personel = [
                {
                    "isim": p.isim,
                    "kidem_grubu": p.kidem_grubu or "",
                    "hedef_nobet": p.hedef_nobet or st.session_state.ayarlar.varsayilan_hedef,
                    "calisabilir_alanlar": p.calisabilir_alanlar,
                    "calisabilir_vardiyalar": p.calisabilir_vardiyalar,
                    "not": ""
                }
                for p in st.session_state.ayarlar.personeller
            ]
        else:
            # Mock veri oluştur
            st.session_state.plan_personel = _create_mock_personel()


def _create_mock_ayarlar() -> Ayarlar:
    """Demo için mock ayarlar oluşturur"""
    from models import Alan, VardiyaTipi

    return Ayarlar(
        kidem_gruplari=[
            KidemGrubu("Kidemli", "#1565c0", 8),
            KidemGrubu("Orta", "#6b5bd2", 10),
            KidemGrubu("Yeni", "#c2185b", 12)
        ],
        alanlar=[
            Alan("Yeşil Alan", gunluk_kontenjan=2, renk="#4caf50"),
            Alan("Sarı Alan", gunluk_kontenjan=1, renk="#ff9800"),
            Alan("Kırmızı Alan", gunluk_kontenjan=1, renk="#f44336")
        ],
        vardiya_tipleri=[
            VardiyaTipi("Gündüz 8s", "08:00", "16:00", "#FFA500"),
            VardiyaTipi("Akşam 8s", "16:00", "00:00", "#9C27B0"),
            VardiyaTipi("Gece 8s", "00:00", "08:00", "#3F51B5")
        ],
        varsayilan_hedef=8
    )


def _create_mock_personel() -> List[Dict]:
    """Demo için mock personel listesi oluşturur"""
    return [
        {
            "isim": "Dr. Ayşe Yılmaz",
            "kidem_grubu": "Kidemli",
            "hedef_nobet": 8,
            "calisabilir_alanlar": [],
            "calisabilir_vardiyalar": [],
            "not": ""
        },
        {
            "isim": "Dr. Mehmet Demir",
            "kidem_grubu": "Orta",
            "hedef_nobet": 10,
            "calisabilir_alanlar": [],
            "calisabilir_vardiyalar": [],
            "not": ""
        },
        {
            "isim": "Dr. Zeynep Kaya",
            "kidem_grubu": "Yeni",
            "hedef_nobet": 12,
            "calisabilir_alanlar": [],
            "calisabilir_vardiyalar": [],
            "not": ""
        },
        {
            "isim": "Dr. Ahmet Öz",
            "kidem_grubu": "Orta",
            "hedef_nobet": 10,
            "calisabilir_alanlar": [],
            "calisabilir_vardiyalar": [],
            "not": ""
        }
    ]


def _render_personel_table() -> None:
    """Düzenlenebilir personel tablosu render eder"""
    # Kıdem grubu seçenekleri
    kidem_options = [kg.isim for kg in st.session_state.ayarlar.kidem_gruplari]

    # Alan seçenekleri
    alan_options = [a.isim for a in st.session_state.ayarlar.alanlar if a.aktif]

    # Vardiya seçenekleri
    vardiya_options = [v.isim for v in st.session_state.ayarlar.vardiya_tipleri]

    column_config = {
        "isim": st.column_config.TextColumn(
            "İsim",
            required=True,
            max_chars=50,
            help="Personel adı"
        ),
        "kidem_grubu": st.column_config.SelectboxColumn(
            "Kıdem",
            options=kidem_options if kidem_options else ["Atanmamış"],
            required=False,
            help="Kıdem grubu seçin"
        ),
        "hedef_nobet": st.column_config.NumberColumn(
            "Hedef",
            min_value=0,
            max_value=31,
            step=1,
            default=st.session_state.ayarlar.varsayilan_hedef,
            help="Bu ay hedeflenen nöbet sayısı"
        ),
        "calisabilir_alanlar": st.column_config.ListColumn(
            "Alanlar",
            help="Çalışabileceği alanlar (boş = tümü)"
        ),
        "calisabilir_vardiyalar": st.column_config.ListColumn(
            "Vardiyalar",
            help="Çalışabileceği vardiyalar (boş = tümü)"
        ),
        "not": st.column_config.TextColumn(
            "Not",
            max_chars=100,
            help="Ek bilgiler"
        )
    }

    # DataFrame oluştur
    df_data = pd.DataFrame(st.session_state.plan_personel)

    # Eğer liste boşsa, boş bir satır ekle
    if df_data.empty:
        df_data = pd.DataFrame([{
            "isim": "",
            "kidem_grubu": "",
            "hedef_nobet": st.session_state.ayarlar.varsayilan_hedef,
            "calisabilir_alanlar": [],
            "calisabilir_vardiyalar": [],
            "not": ""
        }])

    # Data editor
    edited_df = st.data_editor(
        df_data,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="personel_editor"
    )

    # Session state'i güncelle (boş satırları filtrele)
    new_personel = edited_df.to_dict('records')
    st.session_state.plan_personel = [
        p for p in new_personel
        if p.get("isim", "").strip() != ""
    ]


def _hedefleri_otomatik_hesapla() -> None:
    """Hedefleri otomatik hesaplar ve personel listesini günceller"""
    yil = st.session_state.plan_yil
    ay = st.session_state.plan_ay
    gun_sayisi = ay_gun_sayisi(yil, ay)

    # Veri hazırlığı
    alanlar = [{"kontenjan": a.gunluk_kontenjan} for a in st.session_state.ayarlar.alanlar]
    if not alanlar:
        alanlar = [{"kontenjan": 1}]  # Varsayılan

    vardiyalar = st.session_state.ayarlar.vardiya_tipleri
    personel_isimleri = [p["isim"] for p in st.session_state.plan_personel]
    izin_map = {}  # İlk adımda izin bilgisi yok

    # Hesapla
    hedefler = hesapla_otomatik_hedef(
        gun_sayisi,
        alanlar,
        vardiyalar,
        personel_isimleri,
        izin_map,
        st.session_state.ayarlar.ardisik_yasak
    )

    # Hedefleri güncelle
    for p in st.session_state.plan_personel:
        if p["isim"] in hedefler:
            p["hedef_nobet"] = hedefler[p["isim"]]


def _render_hesaplama_butonu() -> None:
    """Otomatik hesaplama butonu render eder"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "⚡ Hedefleri Otomatik Hesapla",
            use_container_width=True,
            help="Kıdem grupları ve vardiya tiplerine göre hedefleri otomatik hesaplar"
        ):
            _hedefleri_otomatik_hesapla()
            st.success("✓ Hedefler otomatik hesaplandı!")
            st.rerun()


def _render_eslesmeler_html() -> str:
    """Eşleşme kurallarını HTML olarak döndürür (read-only)"""
    ayarlar = st.session_state.ayarlar
    parts = []

    # Birlikte tutulacaklar
    if ayarlar.birlikte_tutma:
        parts.append('<p style="font-weight: 600; color: #2e7d32; margin-bottom: 8px;">Birlikte Tutulacaklar</p>')
        for e in ayarlar.birlikte_tutma:
            parts.append(f'<div style="margin-left: 12px; margin-bottom: 4px;">• {e.personel_a} ↔ {e.personel_b}</div>')

    # Ayrı tutulacaklar
    if ayarlar.ayri_tutma:
        parts.append('<p style="font-weight: 600; color: #c62828; margin-top: 12px; margin-bottom: 8px;">Ayrı Tutulacaklar</p>')
        for e in ayarlar.ayri_tutma:
            parts.append(f'<div style="margin-left: 12px; margin-bottom: 4px;">• {e.personel_a} ⊗ {e.personel_b}</div>')

    # Esnek ayrı tutma
    if ayarlar.esnek_ayri_tutma:
        parts.append('<p style="font-weight: 600; color: #ed6c02; margin-top: 12px; margin-bottom: 8px;">Esnek Ayrı Tutma</p>')
        for e in ayarlar.esnek_ayri_tutma:
            parts.append(f'<div style="margin-left: 12px; margin-bottom: 4px;">• {e.personel_a} ~ {e.personel_b}</div>')

    if not parts:
        parts.append('<p style="color: #9a9aa8; font-style: italic;">Tanımlı kural yok</p>')
        parts.append('<p style="color: #6b6b7b; font-size: 12px; margin-top: 8px;">Kurum Ayarlarından eşleşme kuralları ekleyebilirsiniz.</p>')

    return "".join(parts)


def _render_kidem_ozet_html() -> str:
    """Kıdem grupları özetini HTML olarak döndürür"""
    # Kıdem başına personel sayısını hesapla
    kidem_counts: Dict[str, int] = {}
    for p in st.session_state.plan_personel:
        kg = p.get("kidem_grubu", "")
        if kg:
            kidem_counts[kg] = kidem_counts.get(kg, 0) + 1
        else:
            kidem_counts["Atanmamış"] = kidem_counts.get("Atanmamış", 0) + 1

    parts = []

    # Her kıdem grubu için
    for kg in st.session_state.ayarlar.kidem_gruplari:
        count = kidem_counts.get(kg.isim, 0)

        # Badge class belirleme
        kg_lower = kg.isim.lower()
        if kg_lower in ["kidemli", "orta", "yeni"]:
            badge_class = f"badge-{kg_lower}"
        else:
            badge_class = "badge"

        badge_html = render_badge(kg.isim, badge_class)
        parts.append(
            f'<div style="margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">'
            f'{badge_html}'
            f'<span style="font-family: monospace; font-weight: 600; font-size: 14px;">{count}</span>'
            f'<span style="color: #6b6b7b; font-size: 12px;">kişi</span>'
            f'</div>'
        )

    # Atanmamış personel varsa göster
    if "Atanmamış" in kidem_counts and kidem_counts["Atanmamış"] > 0:
        count = kidem_counts["Atanmamış"]
        parts.append(
            f'<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e8e5e0; color: #9a9aa8;">'
            f'<span style="font-family: monospace; font-weight: 600;">{count}</span> kişi kıdem grubu atanmamış'
            f'</div>'
        )

    if not parts:
        parts.append('<p style="color: #9a9aa8; font-style: italic;">Henüz personel eklenmemiş</p>')

    return "".join(parts)


def _render_bottom_section() -> None:
    """2 sütunlu alt grid: Eşleşmeler + Kıdem Özeti"""
    st.markdown("### Ek Bilgiler")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            render_card("Eşleşme Kuralları", _render_eslesmeler_html()),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            render_card("Kıdem Grupları", _render_kidem_ozet_html()),
            unsafe_allow_html=True
        )


def _render_navigation() -> None:
    """Geri/İleri navigasyon butonlarını render eder"""
    st.markdown("<br>", unsafe_allow_html=True)  # Boşluk

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Dashboard'a Dön", type="secondary", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    with col3:
        can_proceed = len(st.session_state.plan_personel) > 0

        if st.button(
            "İzinlere Geç →",
            type="primary",
            use_container_width=True,
            disabled=not can_proceed
        ):
            st.session_state.plan_step = 1
            st.rerun()

    # Uyarı mesajı
    if not can_proceed:
        st.warning("⚠️ Devam etmek için en az bir personel ekleyin.")


def show_plan_ekip() -> None:
    """Ekip yapılandırma sayfasını render eder (ana giriş noktası)"""
    _init_plan_ekip()

    # Stepper (1/4)
    st.markdown(render_stepper(1, 4), unsafe_allow_html=True)

    # Başlık
    st.markdown("## Ekip Yapılandırması")
    ay_text = f"{AY_ISIMLERI[st.session_state.plan_ay]} {st.session_state.plan_yil}"
    st.caption(f"Personel listesi, kıdem grupları ve hedefler · {ay_text}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Personel tablosu
    st.markdown("### Personel Listesi")
    st.caption("Satır eklemek için tablonun altındaki '+' butonunu kullanın. Satır silmek için sol taraftaki checkbox'ları seçin.")
    _render_personel_table()

    # Otomatik hesaplama butonu
    _render_hesaplama_butonu()

    st.markdown("<br>", unsafe_allow_html=True)

    # Alt grid: Eşleşmeler + Kıdem özeti
    _render_bottom_section()

    # Navigasyon
    _render_navigation()
