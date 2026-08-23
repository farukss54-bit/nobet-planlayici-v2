"""
G1.2 - kisinin_max_atama günaşırı-farkında formül testleri
"""
import pytest
from utils import kisinin_max_atama
from solver import NobetSolver, SolverInput, SolverConfig


def test_kisinin_max_atama_gunasiri_limit_1():
    """31 gün, max_gunasiri=1 → max 11 atama"""
    assert kisinin_max_atama(31, False, True, 31, True, 1) == 11


def test_kisinin_max_atama_gunasiri_limit_2():
    """31 gün, max_gunasiri=2 → max 11 atama (formül: (31-1+2)//3+1 = 11)"""
    # Formül: (takvim - 1 + max_gunasiri) // 3 + 1 = (31-1+2)//3+1 = 32//3+1 = 10+1 = 11
    assert kisinin_max_atama(31, False, True, 31, True, 2) == 11


def test_kisinin_max_atama_geriye_uyumlu():
    """Eski API çağrıları hala çalışmalı (geriye uyumluluk)"""
    assert kisinin_max_atama(31, False, True) == 16


def test_kisinin_max_atama_vardiya_modu_etkisiz():
    """Vardiya modunda günaşırı limit etkisiz"""
    assert kisinin_max_atama(31, True, True, 31, True, 1) == 31


def test_kisinin_max_atama_gunasiri_limit_devre_disi():
    """Günaşırı limit devre dışıysa eski formül çalışır"""
    assert kisinin_max_atama(31, False, True, 31, False, 1) == 16


def test_kisinin_max_atama_28_gun():
    """28 gün (Şubat), max_gunasiri=1 → max 10 atama"""
    result = kisinin_max_atama(28, False, True, 28, True, 1)
    expected = (28 - 1 + 1) // 3 + 1  # (28 - 1 + 1) // 3 + 1 = 10
    assert result == expected


def test_kisinin_max_atama_izinli_kisi():
    """İzinli kişi: musait=20, takvim=31, max_gunasiri=1"""
    # Ardışık sınır: (20 + 1) // 2 = 10
    # Günaşırı sınır: (31 - 1 + 1) // 3 + 1 = 11
    # Min: 10
    assert kisinin_max_atama(20, False, True, 31, True, 1) == 10


def test_entegrasyon_hedef_12_raises_valueerror():
    """Nöbet modu, 31 gün, hedef=12 → ValueError (max=11)"""
    input_data = SolverInput(
        yil=2025,
        ay=1,
        personeller=["Ahmet"],
        hedefler={"Ahmet": 12},
        config=SolverConfig(
            ardisik_yasak=True,
            gunasiri_limit_aktif=True,
            max_gunasiri_per_kisi=1
        )
    )

    with pytest.raises(ValueError) as exc_info:
        solver = NobetSolver(input_data)

    # Hata mesajında hem hedef (12) hem de maksimum (11) geçmeli
    error_msg = str(exc_info.value)
    assert "12" in error_msg or "hedef" in error_msg.lower()
    assert "11" in error_msg or "maksimum" in error_msg.lower()


def test_entegrasyon_hedef_11_feasible():
    """Nöbet modu, 31 gün, hedef=11 → FEASIBLE (tam limitte)"""
    input_data = SolverInput(
        yil=2025,
        ay=1,
        personeller=["Ahmet", "Mehmet"],
        hedefler={"Ahmet": 11, "Mehmet": 11},
        config=SolverConfig(
            ardisik_yasak=True,
            gunasiri_limit_aktif=True,
            max_gunasiri_per_kisi=1,
            min_kisi_per_gun=1
        )
    )

    solver = NobetSolver(input_data)
    sonuc = solver.coz()

    # Çözüm bulunmalı
    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")

    # Ahmet tam 11 gün çalışmalı
    ahmet_gunler = [g for g in range(1, 32) if "Ahmet" in sonuc.get(g, [])]
    assert len(ahmet_gunler) == 11
