"""
Faz sonu - gercek_senaryo_01 resmi baseline fikstoru.

gercek_senaryo_01_EKSIKLER.md'de "G0.2 baseline setine eklenmeli" notu
verilmisti; bu dosya o notu yerine getirir. Senaryo Faz 0-1 oncesi
INFEASIBLE'di (bkz. EKSIKLER.md); G1.1 (gunasiri vardiyadan cikar) +
G1.3 (soft hedef) + G1.4 (kontenjan granularitesi) sonrasi FEASIBLE'a
donustugu burada dogrulanir.

NOT (onemli): Bu senaryonun config'i pin_search_workers=False (8 thread,
uretimdeki gibi). pin_search_workers=True (tek thread) 60s butcesinde
HICBIR cozum bulamiyor - senaryo tek threade cok buyuk. 8 threadli
paralel aramada CP-SAT DETERMINISTIK DEGIL: ayni girdiyle art arda
kosularda toplam_hedef_sapmasi 0-16 arasinda degisti (status hep
FEASIBLE, sure hep ~60-61s sabit). Bu yuzden asagidaki tavan testi SIKI
bir denge olcutu degil, KABA bir regresyon tripwire'i (gozlenen en
kotu deger + genis marj) - amac ince ayarlamayi degil, "status
INFEASIBLE'a geri dondu" veya "sapma capisizca patladi" gibi gercek
regresyonlari yakalamak.
"""
import json
import time
from pathlib import Path

import pytest

from solver import NobetSolver, SolverInput, SolverConfig, AlanTanimi, VardiyaTanimi

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "gercek_senaryo_01.json"


def _fikstur_yukle() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _girdi_olustur(input_dict: dict) -> SolverInput:
    d = input_dict
    return SolverInput(
        yil=d["yil"], ay=d["ay"],
        personeller=d["personeller"],
        hedefler=d.get("hedefler", {}),
        vardiya_hedefleri=d.get("vardiya_hedefleri", {}),
        izinler={k: set(v) for k, v in d.get("izinler", {}).items()},
        tatiller=set(d.get("tatiller", [])),
        ayri_tut=[tuple(x) for x in d.get("ayri_tut", [])],
        birlikte_tut=[tuple(x) for x in d.get("birlikte_tut", [])],
        esnek_ayri_tut=[tuple(x) for x in d.get("esnek_ayri_tut", [])],
        tercih_edilen={k: set(v) for k, v in d.get("tercih_edilen", {}).items()},
        alanlar=[AlanTanimi(**a) for a in d.get("alanlar", [])],
        personel_alan_yetkinlikleri=d.get("personel_alan_yetkinlikleri", {}),
        personel_kidem_gruplari=d.get("personel_kidem_gruplari", {}),
        vardiyalar=[VardiyaTanimi(**v) for v in d.get("vardiyalar", [])],
        personel_vardiya_kisitlari=d.get("personel_vardiya_kisitlari", {}),
        config=SolverConfig(**d.get("config", {})),
    )


@pytest.mark.yavas
def test_gercek_senaryo_01_regresyon():
    """gercek_senaryo_01: FEASIBLE kalmali, hedef sapmasi capsizca buyumemeli."""
    fikstur = _fikstur_yukle()
    girdi = _girdi_olustur(fikstur["input"])
    tavan = fikstur["toplam_sapma_tavani"]

    solver = NobetSolver(girdi)
    t0 = time.time()
    try:
        sonuc = solver.coz()
    except ValueError as e:
        pytest.fail(f"gercek_senaryo_01 INFEASIBLE/ValueError uretti (regresyon): {e}")
    sure_olcum = time.time() - t0

    print(
        f"\n[gercek_senaryo_01] status={solver.cozum_meta['status']} "
        f"sure_rapor={solver.cozum_meta['sure_saniye']:.2f}s sure_olcum={sure_olcum:.2f}s"
    )

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE"), (
        f"beklenmeyen status: {solver.cozum_meta['status']}"
    )

    sayim = {p: 0 for p in girdi.personeller}
    for _gun, gun_sonuc in sonuc.items():
        for _alan, vardiyalar in gun_sonuc.items():
            for _vardiya, kisiler in vardiyalar.items():
                for k in kisiler:
                    sayim[k] += 1

    toplam_sapma = sum(abs(sayim[p] - girdi.hedefler.get(p, 0)) for p in girdi.personeller)
    print(f"[gercek_senaryo_01] toplam_hedef_sapmasi={toplam_sapma} (tavan={tavan})")

    assert toplam_sapma <= tavan, (
        f"toplam hedef sapmasi {toplam_sapma}, regresyon tavanini ({tavan}) asti"
    )
