"""
Faz 2 - AppTest ortak yardimcilari (G2.1'den itibaren birden fazla test
dosyasinda kullanilir).

app.py TUM sekmeleri (st.tabs bir layout'tur, kosullu render degildir)
tek script calismasinda render eder; bu yuzden session_state, HER
sekmenin ihtiyac duydugu anahtarlarla ONCEDEN doldurulmali (personel_list/
yil/ay/weekday_block_map/want_pairs_list/no_pairs_list/soft_no_pairs_list
dogrudan `[...]` ile okunuyor -> ZORUNLU, digerleri `.get(...,default)`
ile guvenli ama senaryo-ozel degerler icin yine de acikca set edilmeli).

Disk yan etkilerinden izole etmek icin `storage` modulunun dosya
yollarini gecici bir dizine yonlendirmek CAGIRAN TARAFIN sorumlulugundadir
(bkz. apptest_calistir).
"""
from pathlib import Path

from streamlit.runtime.pages_manager import PagesManager
from streamlit.testing.v1 import AppTest

import storage

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def from_function_izole(fn, monkeypatch, **kwargs) -> AppTest:
    """
    AppTest.from_function icin izolasyon sarmalayicisi.

    Streamlit'in PagesManager.uses_pages_directory bayragi surec-geneli,
    tembel-baslatilan (None -> True/False) ve KALICI: ilk AppTest calismasi
    ana script'in yaninda bir `pages/` dizini gorurse (bu depoda app.py'nin
    yaninda BOS bir `pages/` dizini var) bayragi True'ya kilitler. Sonraki
    TUM AppTest.from_function/from_string cagrilari - kendi gecici script'i
    icin hicbir pages/ dizini olmasa bile - bu kalinti True yuzunden
    _mpa_v1 (cok sayfali uygulama) yoluna sapar ve sentetik ana sayfa icin
    "basligi bos" hatasi firlatir. Bu fonksiyon her cagridan once bayragi
    False'a sabitler (monkeypatch teardown'da otomatik geri alinir).
    """
    monkeypatch.setattr(PagesManager, "uses_pages_directory", False)
    at = AppTest.from_function(fn, **kwargs)
    at.run()
    return at


def temel_session_state(overrides: dict) -> dict:
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


def apptest_calistir(tmp_path, monkeypatch, overrides: dict) -> AppTest:
    """storage dosya yollarini tmp_path'e yonlendirir, session_state'i
    doldurur ve app.py'yi ilk kez calistirir."""
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(storage, "SCHEDULES_DIR", tmp_path / "schedules")

    at = AppTest.from_file(APP_PATH)
    for k, v in temel_session_state(overrides).items():
        at.session_state[k] = v
    at.run(timeout=30)
    assert not at.exception, f"Uygulama hata fırlattı: {[str(e) for e in at.exception]}"
    return at


def nobet_olustur_butonu(at: AppTest):
    for b in at.button:
        if b.label == "🚀 Nöbeti Oluştur":
            return b
    raise AssertionError("'Nöbeti Oluştur' butonu bulunamadı")
