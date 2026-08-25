"""
G1.4 - Soft kontenjan ve max tavanını vardiya granülaritesine indirme testleri.
"""
from solver import NobetSolver, SolverInput, SolverConfig, AlanTanimi, VardiyaTanimi


def _vardiya_sayisi(sonuc, gun, alan, vardiya):
    return len(sonuc.get(gun, {}).get(alan, {}).get(vardiya, []))


def test_kontenjan_vardiya_basina_sifir_ceza():
    """
    3 vardiyalı alan, gunluk_kontenjan=1, her vardiya min 1, hedefler uyumlu.
    Eski (gün toplamı) granülaritede: her gün 3 kişi zorunlu ama hedef 1 ->
    kaçınılmaz 2×w_alan_kontenjan_sapma ceza. Yeni (vardiya başına)
    granülaritede: optimal çözümde her vardiya slotu tam 1 kişi, ceza 0.
    """
    personeller = [f"P{i}" for i in range(1, 7)]
    hedefler = {p: 15 for p in personeller}  # 30 gun * 3 vardiya / 6 kisi = 15
    alanlar = [AlanTanimi(isim="Alan1", gunluk_kontenjan=1, minimum_staffing=1)]
    vardiyalar = [VardiyaTanimi("V1"), VardiyaTanimi("V2"), VardiyaTanimi("V3")]

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
        hedefler=hedefler,
        alanlar=alanlar,
        vardiyalar=vardiyalar,
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    for g in range(1, 31):
        for v in ("V1", "V2", "V3"):
            n = _vardiya_sayisi(sonuc, g, "Alan1", v)
            assert n == 1, f"gün {g}, {v}: kontenjan hedefi (1) tutturulamadı, n={n}"


def test_max_kontenjan_vardiya_basina_feasible():
    """
    max_kontenjan=2, 3 vardiya × min 1. Eski (gün toplamı) tavanda:
    gün tavanı 2 < gereken 3 -> kategorik INFEASIBLE. Yeni (vardiya başına)
    tavanda: her vardiya slotu bağımsız <=2 kısıtlı, FEASIBLE olmalı.
    """
    personeller = [f"P{i}" for i in range(1, 8)]
    hedefler = {p: 12 for p in personeller}
    alanlar = [AlanTanimi(isim="Alan1", gunluk_kontenjan=1, max_kontenjan=2, minimum_staffing=1)]
    vardiyalar = [VardiyaTanimi("V1"), VardiyaTanimi("V2"), VardiyaTanimi("V3")]

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
        hedefler=hedefler,
        alanlar=alanlar,
        vardiyalar=vardiyalar,
        config=config,
    )
    solver = NobetSolver(inp)  # ValueError fırlatmamalı (eski hali burada infeasible verirdi)
    sonuc = solver.coz()

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    for g in range(1, 31):
        for v in ("V1", "V2", "V3"):
            n = _vardiya_sayisi(sonuc, g, "Alan1", v)
            assert 1 <= n <= 2, f"gün {g}, {v}: kontenjan tavanı/minimumu ihlal edildi, n={n}"


def test_nobet_modu_kontenjan_degismedi():
    """Vardiyasız (nöbet modu) alan kontenjanı eski (gün, alan) granülaritesiyle birebir aynı davranmalı."""
    personeller = ["A", "B", "C", "D"]
    hedefler = {"A": 8, "B": 8, "C": 7, "D": 7}  # toplam=30=gun_sayisi*gunluk_kontenjan
    alanlar = [AlanTanimi(isim="Alan1", gunluk_kontenjan=1, minimum_staffing=1)]

    config = SolverConfig(
        ardisik_yasak=False,
        gunasiri_limit_aktif=False,
        enforce_minimum_staffing=True,
        pin_search_workers=True,
        max_sure_saniye=15.0,
    )
    inp = SolverInput(
        yil=2025, ay=6,
        personeller=personeller,
        hedefler=hedefler,
        alanlar=alanlar,
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    for g in range(1, 31):
        toplam = len(sonuc.get(g, {}).get("Alan1", []))
        assert toplam == 1, f"gün {g}: nöbet modunda kontenjan hedefi (1) tutturulamadı, toplam={toplam}"
