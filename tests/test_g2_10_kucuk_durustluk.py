"""
G2.10 - Kucuk durustluk duzeltmeleri.

1. Ayarlar.otomatik_hedef default hizalama: dataclass False vs from_dict
   True vs UI True idi - ucu de True yapildi.
2. VardiyaTipi.saat sessiz 8 fallback'i: parse hatasinda artik
   logging.warning + saat_gecerli property'si + UI'da "saat okunamadi"
   rozeti.
3. izinler_tab manuel tatil: metin bos degil ama gun_parse sonucu bossa
   uyari; kismi taniamada taninmayan parcalar ayri uyariyla listelenir
   (gun_parse imzasi degismedi - UI kendi tarama fonksiyonunu kullaniyor).
"""
import logging

from models import Ayarlar, VardiyaTipi
from tabs.izinler_tab import _tanimayan_parcalari_bul
from tests._apptest_helpers import from_function_izole


def test_otomatik_hedef_default_ve_from_dict_ayni():
    assert Ayarlar().otomatik_hedef is True
    assert Ayarlar.from_dict({}).otomatik_hedef is True
    assert Ayarlar().otomatik_hedef == Ayarlar.from_dict({}).otomatik_hedef


def test_vardiya_saat_parse_hatasinda_8_ve_loglanir_ve_gecersiz_isaretlenir(caplog):
    vt = VardiyaTipi(isim="Bozuk", baslangic="bozuk-metin", bitis="16:00")
    with caplog.at_level(logging.WARNING):
        saat = vt.saat
    assert saat == 8
    assert vt.saat_gecerli is False
    assert any("Bozuk" in r.message and "parse edilemedi" in r.message for r in caplog.records)


def test_vardiya_saat_gecerli_normal_durumda_true():
    vt = VardiyaTipi(isim="Normal", baslangic="08:00", bitis="16:00")
    assert vt.saat == 8
    assert vt.saat_gecerli is True


def test_izinler_hicbir_parca_tanimazsa_bos_liste_donmez_hepsi_atlanan():
    atlanan = _tanimayan_parcalari_bul("abc, xyz", max_gun=30)
    assert set(atlanan) == {"abc", "xyz"}


def test_izinler_kismi_tanima_yalnizca_gecersiz_parca_atlanan():
    # "15" gecerli, "99" ay disi (30 gunluk ayda), "abc" parse hatasi
    atlanan = _tanimayan_parcalari_bul("15, 99, abc", max_gun=30)
    assert set(atlanan) == {"99", "abc"}


def test_izinler_tum_parcalar_gecerliyse_atlanan_bos():
    atlanan = _tanimayan_parcalari_bul("1-5, 10", max_gun=30)
    assert atlanan == []


def _vardiyalar_tab_render_bozuk_saatle():
    import streamlit as st

    st.session_state["vardiya_tipleri"] = [
        {"isim": "Bozuk", "baslangic": "bozuk-metin", "bitis": "16:00", "minimum_staffing": 1},
        {"isim": "Normal", "baslangic": "08:00", "bitis": "16:00", "minimum_staffing": 1},
    ]
    st.session_state["alanlar"] = []
    st.session_state["personel_list"] = []
    st.session_state["personel_vardiya_kisitlari"] = {}

    from tabs.vardiyalar_tab import render_vardiyalar_tab
    render_vardiyalar_tab()


def test_ui_bozuk_saatte_rozet_gorunur_normalde_gorunmez(monkeypatch):
    at = from_function_izole(_vardiyalar_tab_render_bozuk_saatle, monkeypatch, default_timeout=30)
    assert not at.exception

    captionlar = [c.value for c in at.caption]
    rozetli = [c for c in captionlar if "⚠ saat okunamadı" in c]
    assert len(rozetli) == 1  # yalnizca "Bozuk" vardiyasi rozet almali
    normal_satiri = next(c for c in captionlar if "08:00" in c and "16:00" in c and "(8s)" in c)
    assert "⚠ saat okunamadı" not in normal_satiri


def _izinler_tab_render(metin):
    # NOT: AppTest.from_function yalnizca fonksiyonun KENDI kaynak metnini
    # (inspect.getsource) izole calistiriyor - disaridaki bir closure
    # degiskeni (metin) referans alinamaz, bu yuzden parametre olarak
    # gecirilip args=(...) ile iletilir.
    import streamlit as st

    st.session_state["personel_list"] = ["Ahmet"]
    st.session_state["yil"] = 2025
    st.session_state["ay"] = 6
    st.session_state["izin_map"] = {}
    st.session_state["weekday_block_map"] = {}
    st.session_state["prefer_map"] = {}
    st.session_state["manuel_tatiller"] = metin

    from tabs.izinler_tab import render_izinler_tab
    render_izinler_tab()


def test_ui_manuel_tatil_hicbir_gun_taninamazsa_uyari(monkeypatch):
    at = from_function_izole(_izinler_tab_render, monkeypatch, default_timeout=30, args=("abc, xyz",))
    assert not at.exception

    warning_texts = " ".join(w.value for w in at.warning)
    assert "Hiçbir gün tanınamadı" in warning_texts


def test_ui_manuel_tatil_kismi_tanimada_atlanan_parcalar_uyarisi(monkeypatch):
    at = from_function_izole(_izinler_tab_render, monkeypatch, default_timeout=30, args=("15, abc",))
    assert not at.exception

    warning_texts = " ".join(w.value for w in at.warning)
    assert "Şu parçalar atlandı" in warning_texts
    assert "abc" in warning_texts
    assert "Hiçbir gün tanınamadı" not in warning_texts
