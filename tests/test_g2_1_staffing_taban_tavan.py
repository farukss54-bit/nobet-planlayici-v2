"""
G2.1 - UI on kontrolunu Faz 1 davranisiyla hizala.

`tabs/cozum_tab.py::_staffing_taban_tavan` solver'daki hard staffing
filtresiyle (_vardiya_minimum_kontenjan_hard, _alan_kontenjan_soft'un
max_kontenjan hard-cap'i) BIREBIR AYNI kombinasyon mantigini kullanmali.
Bu testler o esitligi dogrudan (saf fonksiyon, Streamlit'e bagimli
degil) dogrular.
"""
from solver import AlanTanimi, VardiyaTanimi
from tabs.cozum_tab import _staffing_taban_tavan


def test_pure_nobet_modu_taban_ve_tavan_yok():
    """Alan yok, vardiya yok: hicbir hard staffing veya kapasite tavani kavrami yok."""
    taban, tavan = _staffing_taban_tavan([], [], gun_sayisi=30, enforce_minimum_staffing=True)
    assert taban == 0
    assert tavan is None


def test_vardiya_modu_only_taban_hesaplanir_tavan_yok():
    """Vardiya var, alan yok: taban = gun x sum(vardiya.minimum_staffing). Tavan kavrami yok."""
    vardiyalar = [
        VardiyaTanimi("Gunduz", minimum_staffing=2),
        VardiyaTanimi("Gece", minimum_staffing=1),
    ]
    taban, tavan = _staffing_taban_tavan([], vardiyalar, gun_sayisi=30, enforce_minimum_staffing=True)
    assert taban == 30 * (2 + 1)
    assert tavan is None


def test_vardiya_modu_enforce_kapali_taban_sifir():
    """enforce_minimum_staffing=False: solver'da bu artik SOFT, hard taban yok."""
    vardiyalar = [VardiyaTanimi("Gunduz", minimum_staffing=5)]
    taban, tavan = _staffing_taban_tavan([], vardiyalar, gun_sayisi=30, enforce_minimum_staffing=False)
    assert taban == 0


def test_alan_modu_only_taban_sifir_vardiya_modu_gerekir():
    """
    Alan var, vardiya yok: solver'da minimum_staffing enforcement SADECE
    vardiya_modu bloguna bagli (_hard_constraints_ekle: 'if vardiya_modu: ...
    enforce_minimum_staffing ise hard kontenjan'). Vardiya yoksa bu blok hic
    calismaz -> alan.minimum_staffing bu modda solver'da islevsiz (bilinen
    modelleme borcu, Faz 2 kapsami disi) -> UI da taban=0 demeli, aksi halde
    solver'la celisen yanlis bir uyari uretilir.
    """
    alanlar = [AlanTanimi(isim="Sari", minimum_staffing=3, max_kontenjan=5)]
    taban, tavan = _staffing_taban_tavan(alanlar, [], gun_sayisi=30, enforce_minimum_staffing=True)
    assert taban == 0
    # Teorik tavan (max_kontenjan) alan modunda vardiya'dan bagimsiz calisir
    assert tavan == 30 * 5


def test_alan_ve_vardiya_modu_gecersiz_kombinasyon_atlanir():
    """
    alan.vardiya_tipleri tanimliyken o listede olmayan vardiya kombinasyonu
    sayilmamali (solver'daki _vardiya_minimum_kontenjan_hard filtresiyle ayni).
    """
    alanlar = [
        AlanTanimi(isim="Sari", minimum_staffing=2, vardiya_tipleri=["24s"]),
    ]
    vardiyalar = [
        VardiyaTanimi("24s", minimum_staffing=1),
        VardiyaTanimi("16s", minimum_staffing=1),
    ]
    taban, _ = _staffing_taban_tavan(alanlar, vardiyalar, gun_sayisi=10, enforce_minimum_staffing=True)
    # Yalnizca (Sari, 24s) gecerli kombinasyon: max(2, 1) = 2 / gun
    assert taban == 10 * 2


def test_alan_ve_vardiya_modu_max_ile_min_karsilastirilir():
    """min_required = max(alan.minimum_staffing, vardiya.minimum_staffing)."""
    alanlar = [AlanTanimi(isim="Kirmizi", minimum_staffing=1, vardiya_tipleri=["24s"])]
    vardiyalar = [VardiyaTanimi("24s", minimum_staffing=4)]
    taban, _ = _staffing_taban_tavan(alanlar, vardiyalar, gun_sayisi=5, enforce_minimum_staffing=True)
    assert taban == 5 * 4


def test_teorik_tavan_bir_alanda_tanimsizsa_none():
    """
    Iki alandan biri max_kontenjan=None ise toplam teorik tavan hesaplanamaz
    (o alanda fiili ust sinir yok) -> None donmeli, yanlis/eksik bir tavan
    uyarisi uretilmemeli.
    """
    alanlar = [
        AlanTanimi(isim="A", max_kontenjan=3, vardiya_tipleri=["24s"]),
        AlanTanimi(isim="B", max_kontenjan=None, vardiya_tipleri=["24s"]),
    ]
    vardiyalar = [VardiyaTanimi("24s")]
    _, tavan = _staffing_taban_tavan(alanlar, vardiyalar, gun_sayisi=10, enforce_minimum_staffing=False)
    assert tavan is None


def test_teorik_tavan_tum_alanlarda_tanimliysa_toplanir():
    alanlar = [
        AlanTanimi(isim="A", max_kontenjan=3, vardiya_tipleri=["24s"]),
        AlanTanimi(isim="B", max_kontenjan=2, vardiya_tipleri=["24s"]),
    ]
    vardiyalar = [VardiyaTanimi("24s")]
    _, tavan = _staffing_taban_tavan(alanlar, vardiyalar, gun_sayisi=10, enforce_minimum_staffing=False)
    assert tavan == 10 * (3 + 2)
