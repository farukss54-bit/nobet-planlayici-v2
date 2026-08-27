"""
G2.5 - Kayit hatalarini gorunur yap.

storage.py'deki tum print() cagrilari logging'e cevrildi (imza/donus
sozlesmesi degismedi); kayitli_planlari_listele artik parse edilemeyen
dosyayi atlamak yerine {"dosya":..., "bozuk": True} olarak listede
tutuyor; personel_tab.py ve cozum_tab.py artik ayarlari_kaydet/
aylik_plani_kaydet donuslerini kontrol edip basarisizlikta st.error
gosteriyor.
"""
import json
import logging

import pytest

import storage
import tabs.personel_tab as personel_tab_modul
from models import Ayarlar
from tests._apptest_helpers import apptest_calistir


def test_ayarlari_kaydet_basarisiz_ise_false_doner_ve_loglar(tmp_path, monkeypatch, caplog):
    """
    Bir dosyanin oldugu yolu dizin olarak kullanmaya calismak (mkdir
    exist_ok=True bir DOSYANIN uzerine calisamaz -> FileExistsError)
    platform bagimsiz, guvenilir bir yazma hatasi tetikler.
    """
    engel_dosya = tmp_path / "engel"
    engel_dosya.write_text("x", encoding="utf-8")
    monkeypatch.setattr(storage, "DATA_DIR", engel_dosya)
    monkeypatch.setattr(storage, "SETTINGS_FILE", engel_dosya / "settings.json")
    monkeypatch.setattr(storage, "SCHEDULES_DIR", engel_dosya / "schedules")

    with caplog.at_level(logging.ERROR):
        sonuc = storage.ayarlari_kaydet(Ayarlar())

    assert sonuc is False
    assert any("Ayarlar kaydedilemedi" in rec.message for rec in caplog.records)


def test_kayitli_planlari_listele_bozuk_dosya_govde_de_yer_alir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "SETTINGS_FILE", tmp_path / "settings.json")
    schedules = tmp_path / "schedules"
    monkeypatch.setattr(storage, "SCHEDULES_DIR", schedules)
    schedules.mkdir()

    (schedules / "bozuk.json").write_text("{ gecersiz json", encoding="utf-8")
    (schedules / "2025_06.json").write_text(
        json.dumps({"yil": 2025, "ay": 6, "sonuc": {"1": ["A"]}}), encoding="utf-8"
    )

    planlar = storage.kayitli_planlari_listele()

    bozuk = [p for p in planlar if p.get("bozuk")]
    assert len(bozuk) == 1
    assert bozuk[0]["dosya"] == "bozuk.json"

    saglam = [p for p in planlar if not p.get("bozuk")]
    assert len(saglam) == 1
    assert saglam[0]["yil"] == 2025


@pytest.mark.yavas
def test_ui_kayit_basarisiz_ise_hata_mesaji_gorunur(tmp_path, monkeypatch):
    """Personel adı değişikliği + ayarlari_kaydet başarısız -> ekranda hata mesajı."""
    monkeypatch.setattr(personel_tab_modul, "ayarlari_kaydet", lambda ayarlar: False)

    at = apptest_calistir(tmp_path, monkeypatch, {})

    isim_kutusu = next(t for t in at.text_input if t.key == "personel_name_0")
    isim_kutusu.set_value("Degistirilmis Isim").run()
    assert not at.exception, f"Beklenmeyen hata: {[str(e) for e in at.exception]}"

    error_texts = " ".join(e.value for e in at.error)
    assert "Kaydedilemedi" in error_texts
