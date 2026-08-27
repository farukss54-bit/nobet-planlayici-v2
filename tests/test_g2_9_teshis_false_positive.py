"""
G2.9 - Teshis false-positive temizligi.

gelismis_teshis iki yonde yaniltiyordu:
(a) Saf nobet modunda toplam_kapasite = gun_sayisi (gunde 1 kisi
    varsayimi) - modelde boyle bir hard kisit yok; cozulebilir girdilere
    "Imkansiz!" diyordu.
(b) enforce_minimum_staffing bayragina bakip hata basiyordu ama staffing
    kisiti yalnizca vardiya modunda kuruluyor (solver._hard_constraints_ekle).

Duzeltme: nobet modu kapasitesi artik kisi basi kisinin_max_atama(...)
toplamidir (gercek hard tavan); staffing hata seviyesi vardiyalar
varliğina da bagli; hedef kaynakli "Imkansiz" bulgular (hard sinir
disinda) "hedefler sapacak" diline cevrildi; bulgu yoksa durust kapanis.
"""
import json
from pathlib import Path

from solver import gelismis_teshis, teshis_ozeti, SolverInput, SolverConfig, AlanTanimi, VardiyaTanimi


def test_nobet_modu_gercekci_hedef_imkansiz_uretmez():
    """5 kisi x hedef 10, 31 gun (gunde ~1.6 kisi) -> teshis 'Imkansiz' uretmemeli."""
    personeller = [f"P{i}" for i in range(1, 6)]
    hedefler = {p: 10 for p in personeller}
    teshisler = gelismis_teshis(
        yil=2025, ay=1,  # Ocak = 31 gun
        personeller=personeller, hedefler=hedefler,
        vardiya_hedefleri={}, izinler={}, tatiller=set(),
        birlikte_tut=[], ayri_tut=[],
        ardisik_yasak=True, enforce_minimum_staffing=True,
    )
    assert not any("İmkansız" in t.mesaj or "İmkânsız" in t.mesaj for t in teshisler)
    assert not any(t.tip == "toplam_hedef_fazla" for t in teshisler)


def test_nobet_modu_enforce_true_staffing_hatasi_uretmez():
    """
    Nobet modunda (vardiyalar=[]) enforce_minimum_staffing=True olsa bile
    staffing kisitli hicbir hard hata uretilmemeli - solver bu bayragi
    yalnizca vardiya_modu'nda hard kisita cevirir.
    """
    personeller = ["A", "B"]
    hedefler = {"A": 2, "B": 2}  # kucuk hedef -> "yetersiz" dali tetiklenir
    teshisler = gelismis_teshis(
        yil=2025, ay=1,
        personeller=personeller, hedefler=hedefler,
        vardiya_hedefleri={}, izinler={}, tatiller=set(),
        birlikte_tut=[], ayri_tut=[],
        ardisik_yasak=True, enforce_minimum_staffing=True,
    )
    yetersiz = [t for t in teshisler if t.tip == "toplam_hedef_yetersiz"]
    assert yetersiz, "beklenen 'toplam_hedef_yetersiz' bulgusu tetiklenmedi"
    assert all(t.seviye == "warning" for t in yetersiz), (
        "vardiya yokken staffing asla 'error' olmamali (enforce_minimum_staffing "
        "modelde hicbir etkisi olmayan bir bayrak)"
    )


def test_vardiya_modu_gercek_staffing_acigi_hala_error():
    """Vardiya modunda enforce_minimum_staffing=True + gercek acik hala 'error' kalmali (regresyon)."""
    vardiyalar = [VardiyaTanimi("V1", minimum_staffing=1)]
    personeller = ["A"]
    hedefler = {"A": 1}  # toplam kapasiteden (31) cok dusuk
    teshisler = gelismis_teshis(
        yil=2025, ay=1,
        personeller=personeller, hedefler=hedefler,
        vardiya_hedefleri={}, izinler={}, tatiller=set(),
        birlikte_tut=[], ayri_tut=[],
        vardiyalar=vardiyalar,
        ardisik_yasak=False, enforce_minimum_staffing=True,
    )
    yetersiz = [t for t in teshisler if t.tip == "toplam_hedef_yetersiz"]
    assert yetersiz and all(t.seviye == "error" for t in yetersiz)


def test_bulgu_yoksa_durust_kapanis_metni():
    ozet = teshis_ozeti([])
    assert "teşhis kapsamı sınırlı" in ozet
    assert "İmkansız" not in ozet and "Sorun tespit edilemedi" not in ozet


GERCEK_SENARYO_PATH = Path(__file__).parent / "fixtures" / "gercek_senaryo_01.json"


def _gercek_senaryo_girdisi():
    with open(GERCEK_SENARYO_PATH, encoding="utf-8") as f:
        fikstur = json.load(f)
    d = fikstur["input"]
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


def test_gercek_senaryo_zorlanmis_infeasible_gercek_bulgu_uretir():
    """
    gercek_senaryo_01'i, bir kisinin hedefini kisisel maksimumunun cok
    ustune cekerek BILEREK infeasible yapiyoruz. Teshis en az bir
    GERCEK (tip != 'belirsiz') bulgu uretmeli.
    """
    girdi = _gercek_senaryo_girdisi()
    ilk_kisi = girdi.personeller[0]
    zorlanmis_hedefler = dict(girdi.hedefler)
    zorlanmis_hedefler[ilk_kisi] = 999

    kidem_kurallari = {a.isim: a.kidem_kurallari for a in girdi.alanlar if a.kidem_kurallari}

    teshisler = gelismis_teshis(
        yil=girdi.yil, ay=girdi.ay,
        personeller=girdi.personeller,
        hedefler=zorlanmis_hedefler,
        vardiya_hedefleri=girdi.vardiya_hedefleri,
        izinler=girdi.izinler, tatiller=girdi.tatiller,
        birlikte_tut=girdi.birlikte_tut, ayri_tut=girdi.ayri_tut,
        alanlar=girdi.alanlar, vardiyalar=girdi.vardiyalar,
        personel_alan_yetkinlikleri=girdi.personel_alan_yetkinlikleri,
        personel_vardiya_kisitlari=girdi.personel_vardiya_kisitlari,
        personel_kidem_gruplari=girdi.personel_kidem_gruplari,
        kidem_kurallari=kidem_kurallari or None,
        ardisik_yasak=girdi.config.ardisik_yasak,
        enforce_minimum_staffing=girdi.config.enforce_minimum_staffing,
        gunasiri_limit_aktif=girdi.config.gunasiri_limit_aktif,
        max_gunasiri=girdi.config.max_gunasiri_per_kisi,
    )

    anlamli = [t for t in teshisler if t.tip != "belirsiz"]
    assert anlamli, "gercek bulgu uretilmedi - teshis kor nokta"
    assert any(ilk_kisi in t.mesaj for t in anlamli)
