"""
G2.1 - UI on kontrolunu Faz 1 davranisiyla hizala (AppTest).

Faz 2 protokolu geregi UI degisikliklerinde MUMKUNSE AppTest kullanilir.
Bu dosya gercek `app.py`yi (tum sekmeleriyle) calistirir; disk yan
etkilerinden izole etmek icin storage modulunun dosya yollarini gecici
bir dizine yonlendirir (aksi halde gercek data/settings.json'a dokunurdu).

app.py TUM sekmeleri (st.tabs bir layout'tur, kosullu render degildir)
tek script calismasinda render ettigi icin session_state, HER sekmenin
ihtiyac duydugu anahtarlarla ONCEDEN doldurulur (bkz. arastirma notu:
personel_list/yil/ay/weekday_block_map/want_pairs_list/no_pairs_list/
soft_no_pairs_list dogrudan `[...]` ile okunuyor -> ZORUNLU).
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import storage

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def _temel_session_state(overrides: dict) -> dict:
    taban = {
        "initialized": True,
        "personel_list": ["Ahmet", "Mehmet", "Ayşe"],
        "personel_sayisi": 3,
        "personel_targets": {},
        "weekday_block_map": {},
        "want_pairs_list": [],
        "no_pairs_list": [],
        "soft_no_pairs_list": [],
        "varsayilan_hedef": 2,
        "yil": 2025,
        "ay": 6,
        "izin_map": {},
        "prefer_map": {},
        "manuel_tatiller": "",
        "alanlar": [],
        "alan_modu_aktif": False,
        "alan_bazli_denklik": True,
        "personel_alan_yetkinlikleri": {},
        "kidem_gruplari": [],
        "personel_kidem_gruplari": {},
        "vardiya_tipleri": [
            {"isim": "Gunduz", "baslangic": "08:00", "bitis": "16:00", "minimum_staffing": 3},
        ],
        "personel_vardiya_kisitlari": {},
        "saat_bazli_denge": True,
        "ardisik_yasak": False,
        "gunasiri_limit_aktif": False,
        "max_gunasiri": 1,
        "enforce_minimum_staffing": True,
        "hafta_sonu_dengesi": False,
        "w_cuma": 1000,
        "w_cumartesi": 1000,
        "w_pazar": 1000,
        "tatil_dengesi": False,
        "iki_gun_bosluk_aktif": False,
        "w_gap3": 300,
        "otomatik_hedef": False,
    }
    taban.update(overrides)
    return taban


def _calistir(tmp_path, monkeypatch, overrides: dict) -> AppTest:
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(storage, "SCHEDULES_DIR", tmp_path / "schedules")

    at = AppTest.from_file(APP_PATH)
    for k, v in _temel_session_state(overrides).items():
        at.session_state[k] = v
    at.run(timeout=30)
    assert not at.exception, f"Uygulama hata fırlattı: {[str(e) for e in at.exception]}"
    return at


def _nobet_olustur_butonu(at: AppTest):
    for b in at.button:
        if b.label == "🚀 Nöbeti Oluştur":
            return b
    raise AssertionError("'Nöbeti Oluştur' butonu bulunamadı")


@pytest.mark.yavas
def test_hedef_tabanin_altinda_uyari_ve_cozum_calisir(tmp_path, monkeypatch):
    """
    3 kişi, hedef=2 (toplam 6); vardiya minimum_staffing=3, 30 gün ->
    zorunlu taban = 90. Toplam hedef << taban.
    G1.3 öncesi bu durum st.error + st.stop() ile ENGELLENİYORDU.
    G2.1 sonrası: solver ÇALIŞIR, çözüm gösterilir, uyarı görünür.
    """
    at = _calistir(tmp_path, monkeypatch, {})
    _nobet_olustur_butonu(at).click().run(timeout=60)
    assert not at.exception, f"Çözüm sırasında hata: {[str(e) for e in at.exception]}"

    warning_texts = " ".join(w.value for w in at.warning)
    assert "zorunlu doluluk tabanının" in warning_texts
    assert "90" in warning_texts

    success_texts = " ".join(s.value for s in at.success)
    assert "Çözüm bulundu" in success_texts


@pytest.mark.yavas
def test_hedef_aralikta_uyari_yok(tmp_path, monkeypatch):
    """Toplam hedef taban-tavan aralığındaysa hiçbir staffing uyarısı çıkmamalı."""
    at = _calistir(tmp_path, monkeypatch, {
        "varsayilan_hedef": 30,  # 3 kisi x 30 = 90 = tam taban
    })
    _nobet_olustur_butonu(at).click().run(timeout=60)
    assert not at.exception, f"Çözüm sırasında hata: {[str(e) for e in at.exception]}"

    warning_texts = " ".join(w.value for w in at.warning)
    assert "zorunlu doluluk tabanının" not in warning_texts
    assert "teorik doluluk tavanının" not in warning_texts
