"""
Solver invariant'larını doğrulayan property-based testler.

Refactor sonrası sessiz regresyonları yakalamak için güvenlik ağı.
"""

import pytest
from solver import NobetSolver, gelismis_teshis, SolverInput, SolverConfig, VardiyaTanimi


# =============================================================================
# SONUÇ NORMALIZE EDİCİ HELPER'LAR
# =============================================================================

def kisinin_nobet_gunleri(sonuc: dict, isim: str) -> set:
    """Her modda çalışan normalize edici: kişinin nöbet tuttuğu günleri döndürür."""
    gunler = set()
    for gun, deger in sonuc.items():
        if isinstance(deger, list):
            # Basit mod: {gun: ["Dr. A", "Dr. B"]}
            if isim in deger:
                gunler.add(gun)
        elif isinstance(deger, dict):
            # Alan veya vardiya modu
            for alt_key, alt_deger in deger.items():
                if isinstance(alt_deger, list):
                    # Çoklu alan veya vardiya: {gun: {"Yesil": ["Dr. A"]}}
                    if isim in alt_deger:
                        gunler.add(gun)
                elif isinstance(alt_deger, dict):
                    # Alan + vardiya: {gun: {"Yesil": {"Sabah": ["Dr. A"]}}}
                    for vardiya, kisiler in alt_deger.items():
                        if isim in kisiler:
                            gunler.add(gun)
    return gunler


def gun_toplam_atama(sonuc: dict, gun: int) -> int:
    """Belirli bir gün toplam kaç atama var (tüm slotlar)."""
    deger = sonuc.get(gun)
    if deger is None:
        return 0
    if isinstance(deger, list):
        return len(deger)
    if isinstance(deger, dict):
        toplam = 0
        for alt_deger in deger.values():
            if isinstance(alt_deger, list):
                toplam += len(alt_deger)
            elif isinstance(alt_deger, dict):
                for kisiler in alt_deger.values():
                    toplam += len(kisiler)
        return toplam
    return 0


# =============================================================================
# PROPERTY TESTLERİ
# =============================================================================

class TestKisiGunTekAtama:
    """
    Kişi başı günlük atama limiti.
    - Nöbet modu (test_easy): blanket ardışık gün yasağı da bu sınırın bir sonucudur.
    - Vardiya modu (test_normal): her kişi her günde en fazla 1 vardiyada atanabilir.
    """

    def test_easy(self, easy_input):
        solver = NobetSolver(easy_input)
        sonuc = solver.coz()
        for p in easy_input.personeller:
            gunler = sorted(kisinin_nobet_gunleri(sonuc, p))
            for i in range(len(gunler) - 1):
                assert gunler[i + 1] - gunler[i] > 1, (
                    f"{p}: ardışık nöbet günleri {gunler[i]} ve {gunler[i + 1]}"
                )

    def test_normal(self, normal_input):
        # Vardiya modunda blanket ardışık yasak kalktı;
        # yerine zaman-bazlı dinlenme kuralı geldi.
        # Bu test, yerine geçen güçlü invariant'ı doğrular:
        # her kişi her günde en fazla 1 atama alabilir (hard constraint).
        solver = NobetSolver(normal_input)
        sonuc = solver.coz()
        for p in normal_input.personeller:
            for g in range(1, 31):
                gun_data = sonuc.get(g, {})
                atama_sayisi = 0
                for alan_data in gun_data.values():
                    for vardiya_kisiler in alan_data.values():
                        if p in vardiya_kisiler:
                            atama_sayisi += 1
                assert atama_sayisi <= 1, (
                    f"{p}: Gün {g}'de {atama_sayisi} atama — günde max 1 atama kuralı ihlal"
                )


class TestIzinGunleri:
    """İzinli günde atama yok."""

    def test_easy(self, easy_input):
        solver = NobetSolver(easy_input)
        sonuc = solver.coz()
        for p in easy_input.personeller:
            nobet_gunleri = kisinin_nobet_gunleri(sonuc, p)
            izinler = easy_input.izinler.get(p, set())
            kesisim = nobet_gunleri & izinler
            assert not kesisim, (
                f"{p}: izinli günlerde nöbet atanmış {kesisim}"
            )

    def test_normal(self, normal_input):
        solver = NobetSolver(normal_input)
        sonuc = solver.coz()
        for p in normal_input.personeller:
            nobet_gunleri = kisinin_nobet_gunleri(sonuc, p)
            izinler = normal_input.izinler.get(p, set())
            kesisim = nobet_gunleri & izinler
            assert not kesisim, (
                f"{p}: izinli günlerde nöbet atanmış {kesisim}"
            )


class TestNoPairs:
    """Kesin ayrı tutma: iki kişi asla aynı gün nöbet tutamaz."""

    def test_easy(self, easy_input):
        solver = NobetSolver(easy_input)
        sonuc = solver.coz()
        for (a, b) in easy_input.ayri_tut:
            a_gunler = kisinin_nobet_gunleri(sonuc, a)
            b_gunler = kisinin_nobet_gunleri(sonuc, b)
            kesisim = a_gunler & b_gunler
            assert not kesisim, (
                f"Ayrı tutma ihlali: {a} ve {b} aynı günlerde {kesisim}"
            )

    def test_normal(self, normal_input):
        solver = NobetSolver(normal_input)
        sonuc = solver.coz()
        for (a, b) in normal_input.ayri_tut:
            a_gunler = kisinin_nobet_gunleri(sonuc, a)
            b_gunler = kisinin_nobet_gunleri(sonuc, b)
            kesisim = a_gunler & b_gunler
            assert not kesisim, (
                f"Ayrı tutma ihlali: {a} ve {b} aynı günlerde {kesisim}"
            )



class TestHedefSapmasi:
    """Kişi başı toplam nöbet sayısı hedefin makul bandında (±2)."""

    def test_easy(self, easy_input):
        solver = NobetSolver(easy_input)
        sonuc = solver.coz()
        for p in easy_input.personeller:
            nobet_sayisi = len(kisinin_nobet_gunleri(sonuc, p))
            hedef = easy_input.hedefler.get(p, 0)
            if hedef > 0:
                assert abs(nobet_sayisi - hedef) <= 2, (
                    f"{p}: nobet={nobet_sayisi}, hedef={hedef}, sapma={abs(nobet_sayisi - hedef)}"
                )

    def test_normal(self, normal_input):
        solver = NobetSolver(normal_input)
        sonuc = solver.coz()
        for p in normal_input.personeller:
            nobet_sayisi = len(kisinin_nobet_gunleri(sonuc, p))
            hedef = normal_input.hedefler.get(p, 0)
            if hedef > 0:
                assert abs(nobet_sayisi - hedef) <= 2, (
                    f"{p}: nobet={nobet_sayisi}, hedef={hedef}, sapma={abs(nobet_sayisi - hedef)}"
                )


class TestVardiyaDinlenmeKurali:
    """Vardiya modunda zaman-bazlı dinlenme kuralı."""

    def test_sabit_vardiya_duzemi_feasible(self):
        """Aynı vardiyada ardışık günler mümkün olmalı (dinlenme yeterliyse)."""
        config = SolverConfig(
            pin_search_workers=True,
            max_sure_saniye=10.0,
            enforce_minimum_staffing=False,
            minimum_dinlenme_saati=8,
            max_ardisik_calisma_gunu=0,
        )
        inp = SolverInput(
            yil=2025, ay=6,
            personeller=['A', 'B', 'C', 'D', 'E'],
            hedefler={'A': 6, 'B': 6, 'C': 6, 'D': 6, 'E': 6},
            izinler={},
            vardiyalar=[VardiyaTanimi('Akşam', '16:00', '24:00')],
            config=config,
        )
        solver = NobetSolver(inp)
        sonuc = solver.coz()

        # En az bir kişide ardışık günler olmalı
        ardisik_var = False
        for p in inp.personeller:
            gunler = sorted(kisinin_nobet_gunleri(sonuc, p))
            for i in range(len(gunler) - 1):
                if gunler[i + 1] - gunler[i] == 1:
                    ardisik_var = True
                    break
            if ardisik_var:
                break
        assert ardisik_var, "Aynı vardiyada ardışık günler mümkün olmalı"

    def test_yetersiz_dinlenme_yasak(self):
        """Yetersiz dinlenmeli geçiş (Gece→Gece, min 25s) yasaklanmalı."""
        config = SolverConfig(
            pin_search_workers=True,
            max_sure_saniye=10.0,
            enforce_minimum_staffing=False,
            minimum_dinlenme_saati=25,
        )
        inp = SolverInput(
            yil=2025, ay=6,
            personeller=['A'],
            hedefler={'A': 2},
            izinler={'A': {g for g in range(3, 31)}},
            vardiyalar=[VardiyaTanimi('Gece', '00:00', '08:00')],
            personel_vardiya_kisitlari={'A': ['Gece']},
            config=config,
        )
        solver = NobetSolver(inp)
        with pytest.raises(ValueError):
            solver.coz()

    def test_gercekci_sinir_aksam_gunduz_yasak(self):
        """
        Varsayılan 12 saatlik dinlenme limitiyle:
        Akşam (16–24) → Gündüz (08–16) geçişi 8 saat dinlenme verir;
        bu yetersiz olduğu için ardışık atama yasaklanmalı.
        """
        config = SolverConfig(
            pin_search_workers=True,
            max_sure_saniye=10.0,
            enforce_minimum_staffing=False,
            minimum_dinlenme_saati=12,
        )
        inp = SolverInput(
            yil=2025, ay=6,
            personeller=['A'],
            hedefler={'A': 2},
            izinler={'A': {g for g in range(3, 31)}},
            vardiyalar=[
                VardiyaTanimi('Akşam', '16:00', '24:00'),
                VardiyaTanimi('Gündüz', '08:00', '16:00'),
            ],
            personel_vardiya_kisitlari={'A': ['Akşam', 'Gündüz']},
            config=config,
        )
        solver = NobetSolver(inp)
        sonuc = solver.coz()

        # Kişinin hangi gün hangi vardiyada çalıştığını topla
        kisi_vardiya_gun = {}
        for g in range(1, 3):
            gun_data = sonuc.get(g, {})
            for vardiya, kisiler in gun_data.items():
                if 'A' in kisiler:
                    kisi_vardiya_gun.setdefault(vardiya, set()).add(g)

        # Akşam→Gündüz yasaklı geçiş kontrolü
        aksam_gunler = kisi_vardiya_gun.get('Akşam', set())
        gunduz_gunler = kisi_vardiya_gun.get('Gündüz', set())
        for g in aksam_gunler:
            assert (g + 1) not in gunduz_gunler, (
                f"Akşam→Gündüz yasaklı geçiş: gün {g} Akşam, gün {g+1} Gündüz"
            )


class TestOncekiAyKuyrugu:
    """Önceki ayın son günü ile bu ayın 1. günü arası ardışık/dinlenme kısıtları."""

    def test_nobet_modu_onceki_gun_yasak(self):
        """Önceki ayın son gününde nöbet tutan kişi, bu ayın 1. gününe atanmamalı."""
        config = SolverConfig(
            pin_search_workers=True,
            max_sure_saniye=10.0,
            enforce_minimum_staffing=False,
        )
        inp = SolverInput(
            yil=2025, ay=6,
            personeller=['A', 'B'],
            hedefler={'A': 1, 'B': 1},
            izinler={},
            onceki_ay_kuyrugu={'A': {-1: ['Nöbet']}},
            config=config,
        )
        solver = NobetSolver(inp)
        sonuc = solver.coz()
        a_gunler = kisinin_nobet_gunleri(sonuc, 'A')
        assert 1 not in a_gunler, (
            "A önceki ayın son gününde çalışmış, bu ayın 1. gününe atanmamalı"
        )

    def test_vardiya_modu_dinlenme_yasak(self):
        """Önceki ay Akşam→bu ay Sabah (8 saat dinlenme) yasaklanmalı."""
        config = SolverConfig(
            pin_search_workers=True,
            max_sure_saniye=10.0,
            enforce_minimum_staffing=False,
            minimum_dinlenme_saati=12,
        )
        inp = SolverInput(
            yil=2025, ay=6,
            personeller=['A', 'B'],
            hedefler={'A': 1, 'B': 1},
            izinler={},
            vardiyalar=[
                VardiyaTanimi('Akşam', '16:00', '24:00'),
                VardiyaTanimi('Sabah', '08:00', '16:00'),
            ],
            onceki_ay_kuyrugu={'A': {-1: ['Akşam']}},
            config=config,
        )
        solver = NobetSolver(inp)
        sonuc = solver.coz()
        gun_data = sonuc.get(1, {})
        sabah_kisiler = gun_data.get('Sabah', [])
        assert 'A' not in sabah_kisiler, (
            "A Akşam→Sabah yasaklı geçiş: 8 saat dinlenme < 12 saat limit"
        )


class TestNightmareInfeasible:
    """
    Nightmare profili aşırı kısıtlıdır ve genellikle infeasible olur.
    Bu durum ValueError ile raporlanmalı; sessiz başarısızlık olmamalı.
    Exception yakalandığında gelismis_teshis en az bir error döndürmeli.
    """

    def test_nightmare_raises_or_reports(self, nightmare_input):
        try:
            solver = NobetSolver(nightmare_input)
            solver.coz()
            # Eğer buraya gelindiyse feasible çıktı — seed'e bağlı, skip et
            pytest.skip("Nightmare senaryosu bu seed ile feasible çıktı")
        except ValueError:
            pass  # Beklenen durum

        # Teshis çağır ve error seviyesi sonuçlar olduğunu kontrol et
        alanlar = nightmare_input.alanlar if nightmare_input.alanlar else None
        vardiyalar = nightmare_input.vardiyalar if nightmare_input.vardiyalar else None

        kidem_kurallari = {}
        if alanlar:
            for a in nightmare_input.alanlar:
                if a.kidem_kurallari:
                    kidem_kurallari[a.isim] = a.kidem_kurallari

        teshisler = gelismis_teshis(
            yil=nightmare_input.yil,
            ay=nightmare_input.ay,
            personeller=nightmare_input.personeller,
            hedefler=nightmare_input.hedefler,
            vardiya_hedefleri=nightmare_input.vardiya_hedefleri,
            izinler=nightmare_input.izinler,
            tatiller=nightmare_input.tatiller,
            birlikte_tut=nightmare_input.birlikte_tut,
            ayri_tut=nightmare_input.ayri_tut,
            alanlar=alanlar,
            vardiyalar=vardiyalar,
            personel_alan_yetkinlikleri=nightmare_input.personel_alan_yetkinlikleri,
            personel_vardiya_kisitlari=nightmare_input.personel_vardiya_kisitlari,
            personel_kidem_gruplari=nightmare_input.personel_kidem_gruplari,
            kidem_kurallari=kidem_kurallari or None,
            ardisik_yasak=nightmare_input.config.ardisik_yasak,
            enforce_minimum_staffing=nightmare_input.config.enforce_minimum_staffing,
        )

        # En az bir anlamlı teşhis sonucu olmalı ('belirsiz' dışında)
        anlamli = [t for t in teshisler if t.tip != "belirsiz"]
        assert anlamli, (
            "Nightmare infeasible oldu ama gelismis_teshis anlamlı sorun bulamadı"
        )


class TestDeterminizm:
    """T1.1: Aynı girdi aynı çıktı (pin_search_workers=True ile CI-flake-proof)."""

    def test_t1_1_same_input_same_output(self, easy_input):
        # easy_input zaten pin_search_workers=True ile oluşturuldu
        sonuc1 = NobetSolver(easy_input).coz()
        sonuc2 = NobetSolver(easy_input).coz()
        assert sonuc1 == sonuc2, "Aynı girdi farklı çıktı üretti — determinizm bozuk"
