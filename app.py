"""
Nöbet Planlayıcı - Ana Uygulama

Streamlit tabanlı kullanıcı arayüzü.
"""

import streamlit as st

# Yerel modüller
from models import Ayarlar, Personel, EslesmeTercihi, Alan, KidemGrubu, VardiyaTipi
from storage import ayarlari_yukle_veya_varsayilan
from streamlit_integration import (
    get_demo_sidebar,
    render_demo_detail_modal,
    is_demo_active,
    get_demo_meta
)

# Sekme render modülleri
from tabs.personel_tab import render_personel_tab
from tabs.kidem_tab import render_kidem_tab
from tabs.alanlar_tab import render_alanlar_tab
from tabs.vardiyalar_tab import render_vardiyalar_tab
from tabs.izinler_tab import render_izinler_tab
from tabs.eslesmeler_tab import render_eslesmeler_tab
from tabs.cozum_tab import render_cozum_tab
from tabs.sidebar import render_sidebar


# =============================================================================
# SAYFA AYARLARI
# =============================================================================

st.set_page_config(page_title="Nöbet Planlayıcı", layout="wide")
st.title("🏥 Acil Servis Nöbet Planlayıcı")

# Demo modu aktifse detaylı özet göster
if is_demo_active():
    meta = get_demo_meta()

    with st.expander(f"🧪 **Demo Modu Aktif** - {meta.get('difficulty', '?')} | Seed: {meta.get('seed', '?')}", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("👥 Personel", len(st.session_state.get('personel_list', [])))

        with col2:
            izin_toplam = sum(len(v) for v in st.session_state.get('izin_map', {}).values())
            st.metric("🏖️ Toplam İzin", izin_toplam)

        with col3:
            kisit_toplam = (
                len(st.session_state.get('no_pairs_list', [])) +
                len(st.session_state.get('soft_no_pairs_list', []))
            )
            st.metric("🚫 Çift Kısıtları", kisit_toplam)

        with col4:
            alan_sayisi = len(st.session_state.get('alanlar', []))
            vardiya_sayisi = len(st.session_state.get('vardiya_tipleri', []))
            st.metric("🏢/⏰ Alan/Vardiya", f"{alan_sayisi}/{vardiya_sayisi}")

        # Kapasite/Hedef hesapla ve göster
        alanlar = st.session_state.get('alanlar', [])
        vardiyalar = st.session_state.get('vardiya_tipleri', [])
        gun_sayisi = meta.get('gun_sayisi', 30)

        if alanlar:
            toplam_kontenjan = sum(a.get('kontenjan', 1) for a in alanlar)
        else:
            toplam_kontenjan = 1

        if vardiyalar:
            gunluk_slot = toplam_kontenjan * len(vardiyalar)
        else:
            gunluk_slot = toplam_kontenjan

        demo_kapasite = gunluk_slot * gun_sayisi

        st.caption(f"📅 Dönem: {meta.get('yil', '?')}-{meta.get('ay', '?'):02d} | 📊 Demo Kapasite: {demo_kapasite} | ✅ Çözüm sekmesine git")

# Demo detay modalı
render_demo_detail_modal()


# =============================================================================
# SESSION STATE BAŞLATMA
# =============================================================================

def init_session_state():
    """Session state'i başlat veya kayıtlı ayarları yükle"""

    # Demo modu aktifse ASLA kayıtlı dosyadan yükleme - demo verisi kullanılacak
    if st.session_state.get("_demo_aktif", False):
        # Demo verisi zaten session_state'te, sadece initialized flag'i set et
        st.session_state["initialized"] = True
        return

    if "initialized" not in st.session_state:
        # Kayıtlı ayarları yükle
        ayarlar = ayarlari_yukle_veya_varsayilan()

        # Personel listesi
        if ayarlar.personeller:
            st.session_state["personel_list"] = [p.isim for p in ayarlar.personeller]
            st.session_state["personel_targets"] = {
                p.isim: p.hedef_nobet
                for p in ayarlar.personeller
                if p.hedef_nobet is not None
            }
            st.session_state["weekday_block_map"] = {
                p.isim: p.bloklu_gunler
                for p in ayarlar.personeller
            }
        else:
            st.session_state["personel_list"] = [
                "Dr. Ahmet", "Dr. Ayşe", "Dr. Mehmet", "Dr. Fatma",
                "Dr. Ali", "Dr. Zeynep", "Dr. Can", "Dr. Elif", "Dr. Burak"
            ]
            st.session_state["personel_targets"] = {}
            st.session_state["weekday_block_map"] = {}

        st.session_state["personel_sayisi"] = len(st.session_state["personel_list"])

        # Eşleşme kuralları
        st.session_state["want_pairs_list"] = [
            {"a": e.personel_a, "b": e.personel_b, "min": e.min_birlikte}
            for e in ayarlar.birlikte_tutma
        ]
        st.session_state["no_pairs_list"] = [
            {"a": e.personel_a, "b": e.personel_b}
            for e in ayarlar.ayri_tutma
        ]
        st.session_state["soft_no_pairs_list"] = [
            {"a": e.personel_a, "b": e.personel_b}
            for e in ayarlar.esnek_ayri_tutma
        ]

        # Ağırlıklar
        st.session_state["varsayilan_hedef"] = ayarlar.varsayilan_hedef

        # Tarih (varsayılan: gelecek ay)
        from datetime import datetime
        bugun = datetime.now()
        if bugun.month == 12:
            st.session_state["yil"] = bugun.year + 1
            st.session_state["ay"] = 1
        else:
            st.session_state["yil"] = bugun.year
            st.session_state["ay"] = bugun.month + 1

        # Ay'a özel veriler
        st.session_state["izin_map"] = {}
        st.session_state["prefer_map"] = {}
        st.session_state["manuel_tatiller"] = ""

        # Aşama 1: Alanlar
        st.session_state["alanlar"] = [
            {"isim": a.isim, "kontenjan": a.gunluk_kontenjan, "max_kontenjan": a.max_kontenjan, "minimum_staffing": a.minimum_staffing, "renk": a.renk}
            for a in ayarlar.alanlar
        ] if ayarlar.alanlar else []
        st.session_state["alan_modu_aktif"] = len(st.session_state["alanlar"]) > 0
        st.session_state["alan_bazli_denklik"] = ayarlar.alan_bazli_denklik

        # Personel alan yetkinlikleri
        st.session_state["personel_alan_yetkinlikleri"] = {
            p.isim: p.calisabilir_alanlar
            for p in ayarlar.personeller
            if p.calisabilir_alanlar
        }

        # Kıdem grupları
        st.session_state["kidem_gruplari"] = [
            {"isim": k.isim, "renk": k.renk, "varsayilan_hedef": k.varsayilan_hedef}
            for k in ayarlar.kidem_gruplari
        ] if ayarlar.kidem_gruplari else []

        st.session_state["personel_kidem_gruplari"] = {
            p.isim: p.kidem_grubu
            for p in ayarlar.personeller
            if p.kidem_grubu
        }

        # Vardiya tipleri
        st.session_state["vardiya_tipleri"] = [
            {"isim": v.isim, "baslangic": v.baslangic, "bitis": v.bitis, "minimum_staffing": v.minimum_staffing, "renk": v.renk}
            for v in ayarlar.vardiya_tipleri
        ] if ayarlar.vardiya_tipleri else []

        st.session_state["personel_vardiya_kisitlari"] = {
            p.isim: p.calisabilir_vardiyalar
            for p in ayarlar.personeller
            if p.calisabilir_vardiyalar
        }

        st.session_state["saat_bazli_denge"] = ayarlar.saat_bazli_denge

        # Kural ayarları
        st.session_state["ardisik_yasak"] = ayarlar.ardisik_yasak
        st.session_state["gunasiri_limit_aktif"] = ayarlar.gunasiri_limit_aktif
        st.session_state["max_gunasiri"] = ayarlar.max_gunasiri
        st.session_state["enforce_minimum_staffing"] = ayarlar.enforce_minimum_staffing
        st.session_state["hafta_sonu_dengesi"] = ayarlar.hafta_sonu_dengesi
        st.session_state["w_cuma"] = ayarlar.w_cuma
        st.session_state["w_cumartesi"] = ayarlar.w_cumartesi
        st.session_state["w_pazar"] = ayarlar.w_pazar
        st.session_state["tatil_dengesi"] = ayarlar.tatil_dengesi
        st.session_state["iki_gun_bosluk_aktif"] = ayarlar.iki_gun_bosluk_aktif
        st.session_state["w_gap3"] = ayarlar.iki_gun_bosluk_tercihi

        st.session_state["initialized"] = True


def session_to_ayarlar() -> Ayarlar:
    """Session state'ten Ayarlar nesnesi oluşturur"""
    personeller = []
    for isim in st.session_state.get("personel_list", []):
        personeller.append(Personel(
            isim=isim,
            hedef_nobet=st.session_state.get("personel_targets", {}).get(isim),
            bloklu_gunler=st.session_state.get("weekday_block_map", {}).get(isim, []),
            calisabilir_alanlar=st.session_state.get("personel_alan_yetkinlikleri", {}).get(isim, []),
            kidem_grubu=st.session_state.get("personel_kidem_gruplari", {}).get(isim),
            calisabilir_vardiyalar=st.session_state.get("personel_vardiya_kisitlari", {}).get(isim, [])
        ))

    birlikte_tutma = [
        EslesmeTercihi(
            personel_a=item["a"],
            personel_b=item["b"],
            min_birlikte=item.get("min", 0)
        )
        for item in st.session_state.get("want_pairs_list", [])
    ]

    ayri_tutma = [
        EslesmeTercihi(personel_a=item["a"], personel_b=item["b"])
        for item in st.session_state.get("no_pairs_list", [])
    ]

    esnek_ayri_tutma = [
        EslesmeTercihi(personel_a=item["a"], personel_b=item["b"], zorunlu=False)
        for item in st.session_state.get("soft_no_pairs_list", [])
    ]

    # Alanlar
    alanlar = [
        Alan(
            isim=a["isim"],
            gunluk_kontenjan=a.get("kontenjan", 1),
            max_kontenjan=a.get("max_kontenjan"),
            minimum_staffing=a.get("minimum_staffing", 1),
            renk=a.get("renk", "#808080"),
            kidem_kurallari=a.get("kidem_kurallari", {})
        )
        for a in st.session_state.get("alanlar", [])
    ]

    # Kıdem grupları
    kidem_gruplari = [
        KidemGrubu(
            isim=k["isim"],
            renk=k.get("renk", "#808080"),
            varsayilan_hedef=k.get("varsayilan_hedef")
        )
        for k in st.session_state.get("kidem_gruplari", [])
    ]

    # Vardiya tipleri
    vardiya_tipleri = [
        VardiyaTipi(
            isim=v["isim"],
            baslangic=v.get("baslangic", "08:00"),
            bitis=v.get("bitis", "16:00"),
            minimum_staffing=v.get("minimum_staffing", 1),
            renk=v.get("renk", "#808080")
        )
        for v in st.session_state.get("vardiya_tipleri", [])
    ]

    return Ayarlar(
        personeller=personeller,
        varsayilan_hedef=st.session_state.get("varsayilan_hedef", 7),
        alanlar=alanlar,
        alan_bazli_denklik=st.session_state.get("alan_bazli_denklik", True),
        kidem_gruplari=kidem_gruplari,
        vardiya_tipleri=vardiya_tipleri,
        saat_bazli_denge=st.session_state.get("saat_bazli_denge", True),
        birlikte_tutma=birlikte_tutma,
        ayri_tutma=ayri_tutma,
        esnek_ayri_tutma=esnek_ayri_tutma,
        # Kural ayarları
        ardisik_yasak=st.session_state.get("ardisik_yasak", True),
        gunasiri_limit_aktif=st.session_state.get("gunasiri_limit_aktif", True),
        max_gunasiri=st.session_state.get("max_gunasiri", 1),
        enforce_minimum_staffing=st.session_state.get("enforce_minimum_staffing", True),
        hafta_sonu_dengesi=st.session_state.get("hafta_sonu_dengesi", True),
        w_cuma=st.session_state.get("w_cuma", 1000),
        w_cumartesi=st.session_state.get("w_cumartesi", 1000),
        w_pazar=st.session_state.get("w_pazar", 1000),
        tatil_dengesi=st.session_state.get("tatil_dengesi", True),
        iki_gun_bosluk_aktif=st.session_state.get("iki_gun_bosluk_aktif", True),
        iki_gun_bosluk_tercihi=st.session_state.get("w_gap3", 300)
    )


init_session_state()


# =============================================================================
# SIDEBAR
# =============================================================================

render_sidebar(session_to_ayarlar)


# =============================================================================
# ANA SEKMELER
# =============================================================================

tabs = st.tabs(["👥 Kişiler", "🎖️ Kıdem", "🏢 Alanlar", "⏰ Vardiyalar", "🏖️ İzinler", "👫 Eşleşmeler", "✅ Çözüm"])


with tabs[0]:
    render_personel_tab()

with tabs[1]:
    render_kidem_tab()

with tabs[2]:
    render_alanlar_tab()

with tabs[3]:
    render_vardiyalar_tab()

with tabs[4]:
    render_izinler_tab()

with tabs[5]:
    render_eslesmeler_tab()

with tabs[6]:
    render_cozum_tab()
