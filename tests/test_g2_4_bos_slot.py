"""
G2.4 - Bos slot: ayristir ve bagir.

solver.py::_coz_ve_sonuc_al artik GECERLI tum alan-vardiya kombinasyonlarini
(vardiya_tipleri filtresine uyanlari) sonucta bos liste olarak da yaziyor;
GECERSIZ kombinasyonlar hic yazilmiyor. UI bu ikisini ayirt eder:
kisi var -> isimler, anahtar var + liste bos -> "⚠ BOŞ",
anahtar yok -> "—".
"""
import pytest

from solver import NobetSolver, SolverInput, SolverConfig, AlanTanimi, VardiyaTanimi
from tabs.cozum_tab import _hucre_degeri, BOS_SLOT_ISARETI, GECERSIZ_KOMBINASYON_ISARETI
from tests._apptest_helpers import apptest_calistir, nobet_olustur_butonu


def test_solver_bos_slot_yaziliyor_1_kisi_2_vardiya():
    """
    1 kisi, gunde en fazla 1 atama (_kisi_gun_tek_atama), 2 vardiya her biri
    min 1 istiyor -> her gun ZORUNLU olarak bir vardiya bos kalir (soft
    staffing, matematiksel olarak kacinilmaz). Eski davranista bu vardiyanin
    anahtari hic yazilmazdi; artik bos liste ile yaziliyor.
    """
    vardiyalar = [VardiyaTanimi("V1", minimum_staffing=1), VardiyaTanimi("V2", minimum_staffing=1)]
    config = SolverConfig(
        ardisik_yasak=False,
        gunasiri_limit_aktif=False,
        enforce_minimum_staffing=False,
        pin_search_workers=True,
        max_sure_saniye=20.0,
    )
    inp = SolverInput(
        yil=2025, ay=6,
        personeller=["A"],
        hedefler={"A": 30},
        vardiyalar=vardiyalar,
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    for g in range(1, 31):
        gun_data = sonuc[g]
        # Her iki anahtar da HER ZAMAN mevcut (vardiya modunda alan yok,
        # kombinasyon gecersizligi kavrami burada uygulanmiyor).
        assert "V1" in gun_data and "V2" in gun_data
        # Ama en az biri zorunlu olarak bos (1 kisi, gunde max 1 atama, 2 slot)
        assert gun_data["V1"] == [] or gun_data["V2"] == []


def test_solver_gecersiz_kombinasyon_hic_yazilmaz():
    """Alan.vardiya_tipleri disindaki kombinasyon sonuc dict'inde hic yer almaz."""
    alanlar = [
        AlanTanimi(isim="Kirmizi", minimum_staffing=1, vardiya_tipleri=["V1"]),
        AlanTanimi(isim="Sari", minimum_staffing=1, vardiya_tipleri=[]),
    ]
    vardiyalar = [VardiyaTanimi("V1", minimum_staffing=1), VardiyaTanimi("V2", minimum_staffing=1)]
    personeller = [f"P{i}" for i in range(1, 5)]
    config = SolverConfig(
        ardisik_yasak=False,
        gunasiri_limit_aktif=False,
        enforce_minimum_staffing=True,
        pin_search_workers=True,
        max_sure_saniye=20.0,
    )
    inp = SolverInput(
        yil=2025, ay=6,
        personeller=personeller,
        hedefler={p: 30 for p in personeller},
        alanlar=alanlar,
        vardiyalar=vardiyalar,
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    for g in range(1, 31):
        # Kirmizi/V2 GECERSIZ kombinasyon -> hic yazilmamali
        assert "V2" not in sonuc[g]["Kirmizi"]
        # Kirmizi/V1, Sari/V1, Sari/V2 GECERLI -> her zaman yazilmali (hard
        # staffing ile bos da olamaz, doluluk garanti)
        assert sonuc[g]["Kirmizi"]["V1"] != []
        assert sonuc[g]["Sari"]["V1"] != []
        assert sonuc[g]["Sari"]["V2"] != []


def test_hucre_degeri_uc_durum():
    container = {"V1": ["Ahmet"], "V2": []}
    assert _hucre_degeri(container, "V1") == ("Ahmet", False)
    metin, bos_mu = _hucre_degeri(container, "V2")
    assert metin == BOS_SLOT_ISARETI and bos_mu is True
    metin, bos_mu = _hucre_degeri(container, "V3")
    assert metin == GECERSIZ_KOMBINASYON_ISARETI and bos_mu is False


@pytest.mark.yavas
def test_ui_soft_staffing_bos_slot_gosterilir_ve_sayilir(tmp_path, monkeypatch):
    """1 kişi + 2 vardiya (min 1'er) senaryosu -> tabloda '⚠ BOŞ' ve sayaç mesajı."""
    at = apptest_calistir(tmp_path, monkeypatch, {
        "personel_list": ["A"],
        "personel_sayisi": 1,
        "varsayilan_hedef": 30,
        "otomatik_hedef": False,
        "enforce_minimum_staffing": False,
        "vardiya_tipleri": [
            {"isim": "V1", "baslangic": "08:00", "bitis": "16:00", "minimum_staffing": 1},
            {"isim": "V2", "baslangic": "16:00", "bitis": "00:00", "minimum_staffing": 1},
        ],
    })
    nobet_olustur_butonu(at).click().run(timeout=60)
    assert not at.exception, f"Çözüm sırasında hata: {[str(e) for e in at.exception]}"

    df = at.dataframe[0].value
    hucreler = set(df["V1"].tolist()) | set(df["V2"].tolist())
    assert "⚠ BOŞ" in hucreler

    error_texts = " ".join(e.value for e in at.error)
    assert "slot boş kaldı" in error_texts


@pytest.mark.yavas
def test_ui_hard_staffing_gecersiz_kombinasyon_tire_bos_yok(tmp_path, monkeypatch):
    """
    Hard staffing + çözülebilir senaryoda hiç '⚠ BOŞ' olmamalı; alanın
    vardiya_tipleri dışındaki kombinasyon '—' görünmeli.
    """
    at = apptest_calistir(tmp_path, monkeypatch, {
        "personel_list": ["P1", "P2", "P3", "P4"],
        "varsayilan_hedef": 30,
        "otomatik_hedef": False,
        "enforce_minimum_staffing": True,
        "alan_modu_aktif": True,
        "alanlar": [
            {"isim": "Kirmizi", "kontenjan": 1, "minimum_staffing": 1, "vardiya_tipleri": ["V1"]},
            {"isim": "Sari", "kontenjan": 1, "minimum_staffing": 1, "vardiya_tipleri": []},
        ],
        "vardiya_tipleri": [
            {"isim": "V1", "baslangic": "08:00", "bitis": "16:00", "minimum_staffing": 1},
            {"isim": "V2", "baslangic": "16:00", "bitis": "00:00", "minimum_staffing": 1},
        ],
    })
    nobet_olustur_butonu(at).click().run(timeout=60)
    assert not at.exception, f"Çözüm sırasında hata: {[str(e) for e in at.exception]}"

    df = at.dataframe[0].value
    tum_hucreler = set()
    for col in df.columns:
        if "/" in col:
            tum_hucreler |= set(df[col].tolist())

    assert "⚠ BOŞ" not in tum_hucreler
    assert "—" in set(df["Kirmizi / V2"].tolist())

    error_texts = " ".join(e.value for e in at.error)
    assert "slot boş kaldı" not in error_texts
