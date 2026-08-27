"""
G2.6 - Girdi kimlik dogrulamasi (cozum kapisi).

_girdi_dogrula saf bir fonksiyondur (Streamlit'e bagimli degil): sessiz
veri bozulmasina yol acan girdileri HATA (cozumu durdurur), zararsiz ama
bilgilendirilmesi gereken durumlari UYARI (cozum devam eder) olarak
ayirir.
"""
import pytest

import storage
from solver import SolverInput, AlanTanimi, VardiyaTanimi
from tabs.cozum_tab import _girdi_dogrula
from tests._apptest_helpers import from_function_izole


def _temel_girdi(**kwargs):
    varsayilan = dict(
        yil=2025, ay=6,
        personeller=["Ahmet", "Mehmet"],
        hedefler={"Ahmet": 10, "Mehmet": 10},
    )
    varsayilan.update(kwargs)
    return SolverInput(**varsayilan)


def test_temiz_girdi_hata_ve_uyari_bos():
    girdi = _temel_girdi()
    hatalar, uyarilar = _girdi_dogrula(girdi, kidem_grubu_isimleri=[])
    assert hatalar == []
    assert uyarilar == []


def test_yinelenen_isim_hata():
    girdi = _temel_girdi(personeller=["Ahmet", "Ahmet", "Mehmet"], hedefler={"Ahmet": 10, "Mehmet": 10})
    hatalar, _ = _girdi_dogrula(girdi, kidem_grubu_isimleri=[])
    assert any("Ahmet" in h and "benzersiz" in h for h in hatalar)


def test_bos_isim_hata():
    girdi = _temel_girdi(personeller=["Ahmet", "  ", "Mehmet"], hedefler={"Ahmet": 10, "Mehmet": 10})
    hatalar, _ = _girdi_dogrula(girdi, kidem_grubu_isimleri=[])
    assert any("Boş" in h for h in hatalar)


def test_kidem_kurali_tanimsiz_grup_hata():
    alanlar = [AlanTanimi(isim="Kirmizi", kidem_kurallari={"K9": {"min": 1}})]
    girdi = _temel_girdi(alanlar=alanlar)
    hatalar, _ = _girdi_dogrula(girdi, kidem_grubu_isimleri=["K1", "K2"])
    assert any("K9" in h and "tanımsız" in h for h in hatalar)


def test_kidem_kurali_uyesiz_grup_hata():
    alanlar = [AlanTanimi(isim="Kirmizi", kidem_kurallari={"K1": {"min": 1}})]
    girdi = _temel_girdi(
        alanlar=alanlar,
        personel_kidem_gruplari={"Ahmet": "K2", "Mehmet": "K2"},  # K1'de kimse yok
    )
    hatalar, _ = _girdi_dogrula(girdi, kidem_grubu_isimleri=["K1", "K2"])
    assert any("K1" in h and "üye hiç kimse yok" in h for h in hatalar)


def test_kidem_kurali_min_sifir_kontrol_edilmez():
    alanlar = [AlanTanimi(isim="Kirmizi", kidem_kurallari={"K9": {"min": 0}})]
    girdi = _temel_girdi(alanlar=alanlar)
    hatalar, _ = _girdi_dogrula(girdi, kidem_grubu_isimleri=["K1"])
    assert hatalar == []


def test_personel_tanimsiz_kidem_grubu_uyari():
    girdi = _temel_girdi(personel_kidem_gruplari={"Ahmet": "K9"})
    hatalar, uyarilar = _girdi_dogrula(girdi, kidem_grubu_isimleri=["K1", "K2"])
    assert hatalar == []
    assert any("K9" in u for u in uyarilar)


def test_yetkinlik_tanimsiz_alan_uyari():
    alanlar = [AlanTanimi(isim="Kirmizi")]
    girdi = _temel_girdi(
        alanlar=alanlar,
        personel_alan_yetkinlikleri={"Ahmet": ["Kirmizi", "Sari"]},
    )
    _, uyarilar = _girdi_dogrula(girdi, kidem_grubu_isimleri=[])
    assert any("Sari" in u for u in uyarilar)


def test_kisit_tanimsiz_vardiya_uyari():
    vardiyalar = [VardiyaTanimi("V1")]
    girdi = _temel_girdi(
        vardiyalar=vardiyalar,
        personel_vardiya_kisitlari={"Ahmet": ["V1", "V9"]},
    )
    _, uyarilar = _girdi_dogrula(girdi, kidem_grubu_isimleri=[])
    assert any("V9" in u for u in uyarilar)


def test_izin_ve_hedef_tanimsiz_personel_uyari():
    girdi = _temel_girdi(izinler={"Zeynep": {1, 2}}, hedefler={"Ahmet": 10, "Mehmet": 10, "Kaan": 5})
    _, uyarilar = _girdi_dogrula(girdi, kidem_grubu_isimleri=[])
    assert any("Zeynep" in u for u in uyarilar)
    assert any("Kaan" in u for u in uyarilar)


def _cozum_tab_yinelenen_isimle_calistir():
    # NOT: bu fonksiyonun kendi kaynak metni ASCII olmali (AppTest.from_function
    # bu ortamda kaynak metni platform kodekiyle yazip utf-8 olarak geri okuyor;
    # Turkce karakter UnicodeDecodeError firlatiyor - dogrulanmis ortam kisitlamasi).
    # app.py'nin TAMAMI yerine sadece cozum_tab'i izole calistiriyoruz: tam app
    # akisinda personel_list'te yinelenen isim, izinler_tab/vardiyalar_tab gibi
    # DIGER sekmelerde per-kisi key'li widget'lari (key=f"izin_{p}") coktan
    # StreamlitDuplicateElementKey ile cokertiyor - bu G2.6'nin konusu olmayan,
    # ayri bir on-kosul sorunu (ayri bulgu olarak raporlandi).
    import streamlit as st

    st.session_state["yil"] = 2025
    st.session_state["ay"] = 6
    st.session_state["personel_list"] = ["Ahmet", "Ahmet", "Mehmet"]
    st.session_state["varsayilan_hedef"] = 10
    st.session_state["personel_targets"] = {}
    st.session_state["otomatik_hedef"] = False
    st.session_state["izin_map"] = {}
    st.session_state["prefer_map"] = {}
    st.session_state["manuel_tatiller"] = ""
    st.session_state["weekday_block_map"] = {}
    st.session_state["no_pairs_list"] = []
    st.session_state["want_pairs_list"] = []
    st.session_state["soft_no_pairs_list"] = []
    st.session_state["alan_modu_aktif"] = False
    st.session_state["alanlar"] = []
    st.session_state["vardiya_tipleri"] = []
    st.session_state["personel_alan_yetkinlikleri"] = {}
    st.session_state["personel_vardiya_kisitlari"] = {}
    st.session_state["personel_kidem_gruplari"] = {}
    st.session_state["kidem_gruplari"] = []
    st.session_state["ardisik_yasak"] = False
    st.session_state["gunasiri_limit_aktif"] = False
    st.session_state["enforce_minimum_staffing"] = True
    st.session_state["hafta_sonu_dengesi"] = False
    st.session_state["tatil_dengesi"] = False
    st.session_state["iki_gun_bosluk_aktif"] = False
    st.session_state["saat_bazli_denge"] = True

    from tabs.cozum_tab import _cozum_olustur
    _cozum_olustur()


@pytest.mark.yavas
def test_ui_yinelenen_isimle_cozum_kapisi_durdurur(tmp_path, monkeypatch):
    """Yinelenen personel adıyla çözüm çalıştırılırsa -> hata mesajı, solver hiç çalışmaz."""
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(storage, "SCHEDULES_DIR", tmp_path / "schedules")

    at = from_function_izole(_cozum_tab_yinelenen_isimle_calistir, monkeypatch, default_timeout=30)
    assert not at.exception, f"Beklenmeyen üst seviye hata: {[str(e) for e in at.exception]}"

    error_texts = " ".join(e.value for e in at.error)
    assert "Girdi doğrulaması başarısız" in error_texts
    assert "benzersiz" in error_texts

    assert len(at.dataframe) == 0
    success_texts = " ".join(s.value for s in at.success)
    assert "Çözüm bulundu" not in success_texts


def _personel_tab_yinelenen_isimle_calistir():
    # NOT: ASCII-only kaynak metin gerekiyor, bkz. yukaridaki fonksiyondaki not.
    import streamlit as st

    st.session_state["yil"] = 2025
    st.session_state["ay"] = 6
    st.session_state["personel_list"] = ["Ahmet", "Ahmet", "Mehmet"]
    st.session_state["personel_sayisi"] = 3
    st.session_state["varsayilan_hedef"] = 10
    st.session_state["personel_targets"] = {}
    st.session_state["otomatik_hedef"] = False

    from tabs.personel_tab import render_personel_tab
    render_personel_tab(session_to_ayarlar_func=None)


def test_personel_tab_yinelenen_isim_aninda_uyarilir(monkeypatch):
    at = from_function_izole(_personel_tab_yinelenen_isimle_calistir, monkeypatch, default_timeout=30)
    assert not at.exception, f"Beklenmeyen üst seviye hata: {[str(e) for e in at.exception]}"

    warning_texts = " ".join(w.value for w in at.warning)
    assert "'Ahmet' başka bir satırda da var" in warning_texts
