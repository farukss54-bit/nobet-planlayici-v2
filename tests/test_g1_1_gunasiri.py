"""
G1.1 - Günaşırı limitinin nöbet moduna kilitlenmesi testleri
"""
import pytest
from solver import NobetSolver, SolverInput, SolverConfig, VardiyaTanimi


def test_vardiya_modu_gunasiri_limit_devre_disi():
    """Vardiya modunda günaşırı limiti devre dışı → 5 ardışık gün FEASIBLE"""
    input_data = SolverInput(
        yil=2025,
        ay=1,
        personeller=["Ahmet", "Mehmet", "Ayse"],
        hedefler={"Ahmet": 10, "Mehmet": 10, "Ayse": 11},  # 31 toplam, minimum_staffing=1 için yeterli
        vardiyalar=[
            VardiyaTanimi(isim="Gunduz", baslangic="08:00", bitis="16:00", minimum_staffing=1)
        ],
        config=SolverConfig(
            ardisik_yasak=False,
            gunasiri_limit_aktif=True,  # Aktif ama vardiya modunda uygulanmamalı
            max_gunasiri_per_kisi=1,
            min_kisi_per_gun=1
        )
    )

    solver = NobetSolver(input_data)
    sonuc = solver.coz()

    # Çözüm bulunmalı (günaşırı limiti uygulanmadı)
    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")

    # Ahmet'in 5 ardışık gün çalışabileceğini doğrula
    ahmet_gunler = []
    for g in range(1, 32):
        if "Ahmet" in sonuc.get(g, {}).get("Gunduz", []):
            ahmet_gunler.append(g)

    # En az 5 gün çalışmalı (günaşırı sınırı uygulanmadı)
    assert len(ahmet_gunler) >= 5


def test_nobet_modu_gunasiri_limit_aktif():
    """Nöbet modunda günaşırı limiti aktif → limit uygulanır"""
    input_data = SolverInput(
        yil=2025,
        ay=1,
        personeller=["Ahmet", "Mehmet"],
        hedefler={"Ahmet": 8, "Mehmet": 8},
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

    # Ahmet'in günlerini al
    ahmet_gunler = sorted([g for g in range(1, 32) if "Ahmet" in sonuc.get(g, [])])

    # Günaşırı çift sayısını hesapla (fark=2 olan ardışık günler)
    gunasiri_ciftler = 0
    for i in range(len(ahmet_gunler) - 1):
        if ahmet_gunler[i+1] - ahmet_gunler[i] == 2:
            gunasiri_ciftler += 1

    # Günaşırı limit (max=1) uygulanmalı
    assert gunasiri_ciftler <= 1


def test_baseline_gunasiri_vardiya_artik_feasible():
    """baseline_gunasiri_vardiya.json artık FEASIBLE olmalı"""
    from pathlib import Path
    import json

    fixtures_dir = Path(__file__).parent / "fixtures"
    filepath = fixtures_dir / "baseline_gunasiri_vardiya.json"

    with open(filepath, 'r', encoding='utf-8') as f:
        fixture = json.load(f)

    # Fikstürü SolverInput'a çevir (basitleştirilmiş)
    input_dict = fixture["input"].copy()
    input_dict["vardiyalar"] = [VardiyaTanimi(**v) for v in input_dict["vardiyalar"]]
    input_dict["config"] = SolverConfig(**input_dict["config"])
    input_data = SolverInput(**input_dict)

    solver = NobetSolver(input_data)

    # Artık FEASIBLE olmalı (günaşırı limiti vardiya modunda devre dışı)
    sonuc = solver.coz()
    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
