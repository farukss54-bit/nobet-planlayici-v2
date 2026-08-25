"""
G1.5 - hesapla_otomatik_hedef taşma kırpması ve entegrasyon testleri.
"""
import random

import pytest

from utils import hesapla_otomatik_hedef, ay_gun_sayisi
from solver import NobetSolver, SolverInput, SolverConfig


def _rastgele_senaryo(seed):
    rnd = random.Random(seed)
    gun_sayisi = rnd.randint(14, 31)
    num_personel = rnd.randint(3, 8)
    personeller = [f"P{i}" for i in range(1, num_personel + 1)]

    num_alan = rnd.randint(0, 3)
    alanlar = [{"kontenjan": rnd.randint(1, 3)} for _ in range(num_alan)]

    num_vardiya = rnd.randint(0, 3)
    vardiyalar = [{"isim": f"V{i}"} for i in range(num_vardiya)]

    izin_map = {}
    for p in personeller:
        izin_sayisi = rnd.randint(0, min(5, gun_sayisi - 1))
        izin_map[p] = rnd.sample(range(1, gun_sayisi + 1), izin_sayisi)

    return gun_sayisi, alanlar, vardiyalar, personeller, izin_map


def _toplam_slot(gun_sayisi, alanlar, vardiyalar):
    alan_kontenjan = sum(a.get("kontenjan", 1) for a in alanlar) if alanlar else 1
    vardiya_sayisi = len(vardiyalar) if vardiyalar else 1
    return gun_sayisi * alan_kontenjan * vardiya_sayisi


@pytest.mark.parametrize("seed", range(30))
def test_toplam_hedef_slotu_asmaz(seed):
    """Üretilen hedeflerin toplamı hiçbir rastgele küçük senaryoda toplam_slot'u aşmaz."""
    gun_sayisi, alanlar, vardiyalar, personeller, izin_map = _rastgele_senaryo(seed)

    hedefler = hesapla_otomatik_hedef(
        gun_sayisi, alanlar, vardiyalar, personeller, izin_map
    )

    toplam_slot = _toplam_slot(gun_sayisi, alanlar, vardiyalar)
    assert sum(hedefler.values()) <= toplam_slot, (
        f"seed={seed}: toplam hedef {sum(hedefler.values())} > toplam_slot {toplam_slot}"
    )


def test_nobet_modu_hicbir_hedef_11i_asmaz():
    """Nöbet modu, 31 gün, izinsiz: max_gunasiri=1 varsayılanıyla hiçbir hedef 11'i aşmaz."""
    for num_personel in (1, 2, 5, 10):
        personeller = [f"P{i}" for i in range(1, num_personel + 1)]
        hedefler = hesapla_otomatik_hedef(
            gun_sayisi=31,
            alanlar=[],
            vardiyalar=[],
            personeller=personeller,
            izin_map={},
        )
        for p, hedef in hedefler.items():
            assert hedef <= 11, f"{p}: hedef={hedef} > 11 (31 gün, izinsiz, nöbet modu üst sınırı)"


def test_kirpma_determinizmi():
    """Aynı girdi -> aynı çıktı (kırpma sırası deterministik)."""
    gun_sayisi, alanlar, vardiyalar, personeller, izin_map = _rastgele_senaryo(seed=7)

    sonuc1 = hesapla_otomatik_hedef(gun_sayisi, alanlar, vardiyalar, personeller, izin_map)
    sonuc2 = hesapla_otomatik_hedef(gun_sayisi, alanlar, vardiyalar, personeller, izin_map)

    assert sonuc1 == sonuc2


@pytest.mark.parametrize("seed", range(10))
def test_entegrasyon_otomatik_hedef_infeasible_olmamali(seed):
    """
    Basit mod (alan/vardiya çakışması olmayan) rastgele küçük senaryolarda:
    otomatik hedef -> solver INFEASIBLE/ValueError ÜRETMEMELİ.
    (G1.3 sonrası hedefler soft olduğundan, bu test kontenjan/staffing
    çakışması olmayan girdilerle sınırlı — basit mod, alan/vardiya yok.)
    """
    rnd = random.Random(seed)
    yil, ay = 2025, rnd.randint(1, 12)
    gun_sayisi = ay_gun_sayisi(yil, ay)
    num_personel = rnd.randint(2, 6)
    personeller = [f"P{i}" for i in range(1, num_personel + 1)]
    izin_map = {}
    for p in personeller:
        izin_sayisi = rnd.randint(0, min(5, gun_sayisi - 1))
        izin_map[p] = rnd.sample(range(1, gun_sayisi + 1), izin_sayisi)

    hedefler = hesapla_otomatik_hedef(
        gun_sayisi, alanlar=[], vardiyalar=[], personeller=personeller, izin_map=izin_map
    )

    izinler = {p: set(gunler) for p, gunler in izin_map.items()}
    config = SolverConfig(
        pin_search_workers=True,
        max_sure_saniye=10.0,
    )
    inp = SolverInput(
        yil=yil, ay=ay,
        personeller=personeller,
        hedefler=hedefler,
        izinler=izinler,
        config=config,
    )
    try:
        solver = NobetSolver(inp)
        solver.coz()
    except ValueError as e:
        pytest.fail(f"seed={seed}: otomatik hedef INFEASIBLE/ValueError üretti: {e}")
