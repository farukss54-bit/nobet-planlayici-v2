"""
G1.3 - _hedef_nobet_sayilari yeniden yazımı testleri.

Hedef eşitliği hard'dan soft'a döner (AddAbsEquality + w_hedef_sapma),
hedef=0 artık "yasak" anlamına gelmez, hedefsiz kişi sessizce kilitlenmez.
"""
import pytest
from solver import NobetSolver, SolverInput, SolverConfig, VardiyaTanimi


def _gunler(sonuc, isim, gun_araligi):
    return [g for g in gun_araligi if isim in sonuc.get(g, [])]


def test_hedef_tam_tutturur_cakismasiz():
    """Hedef 15, çakışma yok, tolerans 0 -> optimal çözüm hedefi tam tutturur."""
    config = SolverConfig(
        ardisik_yasak=False,
        gunasiri_limit_aktif=False,
        pin_search_workers=True,
        max_sure_saniye=10.0,
    )
    inp = SolverInput(
        yil=2025, ay=1,
        personeller=["Ahmet"],
        hedefler={"Ahmet": 15},
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()
    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(_gunler(sonuc, "Ahmet", range(1, 32))) == 15


def test_hedef_hafif_cakisma_feasible_eski_infeasible():
    """
    İki kişi ayrı_tut ile hiç aynı gün çalışamıyor (kombine kapasite <= 31).
    İkisinin hedefi de 20 -> toplam 40 > 31: tam eşitlikte INFEASIBLE olurdu.
    Soft hedefle FEASIBLE olmalı (sapma var ama çözüm çıkıyor).
    """
    config = SolverConfig(
        ardisik_yasak=False,
        gunasiri_limit_aktif=False,
        pin_search_workers=True,
        max_sure_saniye=15.0,
    )
    inp = SolverInput(
        yil=2025, ay=1,
        personeller=["Ahmet", "Mehmet"],
        hedefler={"Ahmet": 20, "Mehmet": 20},
        ayri_tut=[("Ahmet", "Mehmet")],
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()  # ValueError fırlatmamalı

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    ahmet_gun = len(_gunler(sonuc, "Ahmet", range(1, 32)))
    mehmet_gun = len(_gunler(sonuc, "Mehmet", range(1, 32)))
    assert ahmet_gun + mehmet_gun <= 31
    assert ahmet_gun < 20 or mehmet_gun < 20  # kombine kapasite yetersiz, biri sapar


def test_hedef_tolerans_araligi_cezasiz():
    """Tolerans=2, hedef=17 -> kombine kapasite (31) her iki kişiyi de 15-19 bandında tutar."""
    config = SolverConfig(
        ardisik_yasak=False,
        gunasiri_limit_aktif=False,
        hedef_tolerans=2,
        pin_search_workers=True,
        max_sure_saniye=15.0,
    )
    inp = SolverInput(
        yil=2025, ay=1,
        personeller=["Ahmet", "Mehmet"],
        hedefler={"Ahmet": 17, "Mehmet": 17},
        ayri_tut=[("Ahmet", "Mehmet")],
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    ahmet_gun = len(_gunler(sonuc, "Ahmet", range(1, 32)))
    mehmet_gun = len(_gunler(sonuc, "Mehmet", range(1, 32)))
    assert 15 <= ahmet_gun <= 19
    assert 15 <= mehmet_gun <= 19


def test_vardiya_hedefi_sifir_hard_kilit_degil():
    """
    Ahmet '8s' vardiyasında hedef=0 ama minimum_staffing'i dolduracak tek kişi o.
    Eski kodda hedef=0 -> x==0 hard kilidi, minimum staffing ile çakışıp INFEASIBLE
    üretirdi. Yeni kodda hedef=0 sadece soft baskı; FEASIBLE olmalı.
    """
    config = SolverConfig(
        ardisik_yasak=False,
        gunasiri_limit_aktif=False,
        enforce_minimum_staffing=True,
        pin_search_workers=True,
        max_sure_saniye=15.0,
    )
    inp = SolverInput(
        yil=2025, ay=2,
        personeller=["Ahmet"],
        hedefler={},
        vardiya_hedefleri={"Ahmet": {"8s": 0}},
        vardiyalar=[VardiyaTanimi("8s", "08:00", "16:00", minimum_staffing=1)],
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    ahmet_atama = sum(
        1 for g in range(1, 29)
        if "Ahmet" in sonuc.get(g, {}).get("8s", [])
    )
    assert ahmet_atama > 0, "Minimum staffing'i dolduracak tek kişi hedef=0 diye hiç atanmadı"


def test_vardiya_kisitlari_hala_hard():
    """
    personel_vardiya_kisitlari dışındaki vardiyaya asla atanmaz — hedef sapması
    soft olsa da (büyük ceza pahasına) bu hard kısıt aşılamaz.
    """
    config = SolverConfig(
        ardisik_yasak=False,
        gunasiri_limit_aktif=False,
        enforce_minimum_staffing=False,
        pin_search_workers=True,
        max_sure_saniye=15.0,
    )
    inp = SolverInput(
        yil=2025, ay=2,
        personeller=["Ahmet", "Mehmet"],
        hedefler={},
        vardiya_hedefleri={"Ahmet": {"8s": 10, "16s": 0}},
        vardiyalar=[
            VardiyaTanimi("8s", "08:00", "16:00", minimum_staffing=0),
            VardiyaTanimi("16s", "16:00", "24:00", minimum_staffing=0),
        ],
        personel_vardiya_kisitlari={"Ahmet": ["16s"]},
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()

    assert solver.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")
    for g in range(1, 29):
        assert "Ahmet" not in sonuc.get(g, {}).get("8s", []), (
            f"Ahmet, kısıtlı olmadığı '8s' vardiyasına gün {g}'de atanmış"
        )


def test_hedefsiz_kisi_serbest_ve_uyari():
    """Hedefler sözlüğünde olmayan kişi hiç kısıtlanmaz; atama alabilir ve uyarılar listesine eklenir."""
    config = SolverConfig(
        ardisik_yasak=False,
        gunasiri_limit_aktif=False,
        pin_search_workers=True,
        max_sure_saniye=10.0,
    )
    inp = SolverInput(
        yil=2025, ay=1,
        personeller=["Ahmet", "Veli"],
        hedefler={"Ahmet": 5},  # Veli hedeflerde YOK
        tercih_edilen={"Veli": {1, 2, 3}},
        config=config,
    )
    solver = NobetSolver(inp)
    sonuc = solver.coz()

    assert any("Veli" in u and "hedef" in u for u in solver.uyarilar), (
        f"Veli için uyarı bulunamadı: {solver.uyarilar}"
    )
    assert len(_gunler(sonuc, "Veli", (1, 2, 3))) > 0, (
        "Hedefsiz kişi tercih edilen günlere bile atanamadı — sessizce kilitlenmiş olabilir"
    )
