"""
G0.2 - Baseline test fikstürleri
Mevcut solver davranışını sabitler. Sonraki görevlerde beklenen durumlar güncellenecek.
"""
import json
import pytest
from pathlib import Path
from solver import NobetSolver, SolverInput, SolverConfig, VardiyaTanimi, AlanTanimi


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> dict:
    """JSON fikstürü yükler"""
    filepath = FIXTURES_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def fixture_to_solver_input(fixture_data: dict) -> SolverInput:
    """Fikstür verisini SolverInput'a dönüştürür"""
    input_dict = fixture_data["input"].copy()

    # Vardiyalar varsa VardiyaTanimi nesnelerine çevir
    if "vardiyalar" in input_dict:
        input_dict["vardiyalar"] = [
            VardiyaTanimi(**v) for v in input_dict["vardiyalar"]
        ]

    # Alanlar varsa AlanTanimi nesnelerine çevir
    if "alanlar" in input_dict:
        input_dict["alanlar"] = [
            AlanTanimi(**a) for a in input_dict["alanlar"]
        ]

    # Config varsa SolverConfig nesnesine çevir
    if "config" in input_dict:
        input_dict["config"] = SolverConfig(**input_dict["config"])

    # İzinler set'e çevir
    if "izinler" in input_dict:
        input_dict["izinler"] = {
            k: set(v) for k, v in input_dict["izinler"].items()
        }

    # Tatiller set'e çevir
    if "tatiller" in input_dict:
        input_dict["tatiller"] = set(input_dict["tatiller"])

    return SolverInput(**input_dict)


@pytest.mark.parametrize("fixture_name", [
    "baseline_gunasiri_vardiya.json",
    "baseline_hedef_12.json",
    "baseline_hedef_esitlik.json",
])
def test_baseline_fixture(fixture_name):
    """Baseline fikstürlerini test eder, beklenen durumu doğrular"""
    fixture = load_fixture(fixture_name)

    print(f"\n{'='*60}")
    print(f"Fikstür: {fixture['name']}")
    print(f"Açıklama: {fixture['description']}")
    print(f"Beklenen: {fixture['beklenen_durum']}")

    input_data = fixture_to_solver_input(fixture)
    solver = NobetSolver(input_data)

    beklenen = fixture["beklenen_durum"]

    if beklenen == "INFEASIBLE":
        with pytest.raises(ValueError, match="Çözüm bulunamadı"):
            solver.coz()

        # Meta bilgisi kontrol
        assert solver.cozum_meta is not None
        assert solver.cozum_meta["status"] == "INFEASIBLE"
        print(f"[OK] INFEASIBLE dogrulandı (sure: {solver.cozum_meta['sure_saniye']:.2f}s)")

    elif beklenen == "FEASIBLE":
        sonuc = solver.coz()
        assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
        print(f"[OK] FEASIBLE dogrulandı (sure: {solver.cozum_meta['sure_saniye']:.2f}s)")

    elif beklenen == "ValueError":
        # Çözüm öncesi ValueError (örn: hedef > max_mumkun)
        with pytest.raises(ValueError):
            solver.coz()
        print(f"[OK] ValueError dogrulandı (pre-solve)")

    else:
        pytest.fail(f"Geçersiz beklenen_durum: {beklenen}")

    print(f"{'='*60}")


def test_fixtures_directory_exists():
    """Fixtures dizini var mı?"""
    assert FIXTURES_DIR.exists(), f"Fixtures dizini bulunamadı: {FIXTURES_DIR}"
    assert FIXTURES_DIR.is_dir(), f"Fixtures bir dizin değil: {FIXTURES_DIR}"


def test_all_fixtures_loadable():
    """Tüm fikstürler yüklenebiliyor mu?"""
    fixture_files = list(FIXTURES_DIR.glob("*.json"))
    assert len(fixture_files) >= 3, "En az 3 baseline fikstürü olmalı"

    for filepath in fixture_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert "name" in data
        assert "beklenen_durum" in data
        assert "input" in data
