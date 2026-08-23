"""
G0.1 - Solver status ve meta bilgisi testleri
"""
import pytest
from solver import NobetSolver, SolverInput, SolverConfig


def test_cozulebilir_senaryo_meta_bilgisi():
    """Çözülebilir küçük senaryo → meta bilgisi doğru doldurulmalı"""
    input_data = SolverInput(
        yil=2025,
        ay=1,
        personeller=["Ahmet", "Mehmet", "Ayşe"],
        hedefler={"Ahmet": 10, "Mehmet": 10, "Ayşe": 11},
        config=SolverConfig()
    )

    solver = NobetSolver(input_data)
    sonuc = solver.coz()

    # Meta bilgisi doldurulmuş olmalı
    assert solver.cozum_meta is not None
    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    assert solver.cozum_meta["sure_saniye"] > 0
    assert solver.cozum_meta["objective"] is not None
    assert isinstance(solver.cozum_meta["optimal"], bool)


def test_cozumsuz_senaryo_meta_bilgisi():
    """Çözümsüz senaryo → ValueError yükselir VE meta bilgisi doldurulur"""
    # INFEASIBLE senaryo: birlikte_tut ile çelişen hedefler
    # Ahmet ve Mehmet 10 gün birlikte olmalı, ama Mehmet'in hedefi 1 → INFEASIBLE
    input_data = SolverInput(
        yil=2025,
        ay=1,
        personeller=["Ahmet", "Mehmet"],
        hedefler={"Ahmet": 10, "Mehmet": 1},
        birlikte_tut=[("Ahmet", "Mehmet", 10)]  # 10 gün birlikte ama Mehmet hedefi 1
    )

    solver = NobetSolver(input_data)

    with pytest.raises(ValueError, match="Çözüm bulunamadı"):
        solver.coz()

    # Meta bilgisi INFEASIBLE durumunda bile doldurulmuş olmalı
    assert solver.cozum_meta is not None
    assert solver.cozum_meta["status"] == "INFEASIBLE"
    assert solver.cozum_meta["objective"] is None
    assert solver.cozum_meta["optimal"] is False


def test_mevcut_testler_etkilenmez():
    """Mevcut dönüş yapısı değişmemiş olmalı"""
    input_data = SolverInput(
        yil=2025,
        ay=1,
        personeller=["Ali", "Veli", "Can"],
        hedefler={"Ali": 10, "Veli": 10, "Can": 11},
        config=SolverConfig()
    )

    solver = NobetSolver(input_data)
    sonuc = solver.coz()

    # Dönüş tipi Dict
    assert isinstance(sonuc, dict)
    # Günler 1'den başlar
    assert 1 in sonuc
    # Her gün kişi listesi içerir
    assert isinstance(sonuc[1], list)
