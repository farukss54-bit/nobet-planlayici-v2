"""
Nöbet Planlayıcı - Optimizasyon Motoru (Solver)

Google OR-Tools CP-SAT solver kullanarak nöbet çizelgesi oluşturur.

v2.6 - Vardiya desteği:
- 4 boyutlu değişken: x[personel, gün, alan, vardiya]
- Saat bazlı denge
- Vardiya-personel kısıtları
- Alan-vardiya eşleştirmesi
"""

from ortools.sat.python import cp_model
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field

from utils import ay_gun_sayisi, gunleri_weekday_ile_filtrele


@dataclass
class VardiyaTanimi:
    """Bir vardiya tipi tanımı"""
    isim: str
    baslangic: str = "08:00"
    bitis: str = "16:00"
    
    @property
    def saat(self) -> int:
        """Vardiya süresini saat olarak hesaplar"""
        b_saat, b_dk = map(int, self.baslangic.split(":"))
        s_saat, s_dk = map(int, self.bitis.split(":"))
        
        baslangic_dk = b_saat * 60 + b_dk
        bitis_dk = s_saat * 60 + s_dk
        
        if bitis_dk <= baslangic_dk:
            bitis_dk += 24 * 60
        
        return (bitis_dk - baslangic_dk) // 60


@dataclass
class AlanTanimi:
    """Bir alan/lokasyon tanımı"""
    isim: str
    gunluk_kontenjan: int = 1
    max_kontenjan: int = None
    kidem_kurallari: Dict[str, Dict[str, int]] = field(default_factory=dict)
    vardiya_tipleri: List[str] = field(default_factory=list)


@dataclass
class SolverConfig:
    """Solver için konfigürasyon parametreleri"""

    min_kisi_per_gun: int = 1
    ardisik_yasak: bool = True
    gunasiri_limit_aktif: bool = True
    max_gunasiri_per_kisi: int = 1

    # Minimum staffing enforcement
    enforce_minimum_staffing: bool = True  # Hard constraint if True, soft if False
    w_vardiya_min_kontenjan: int = 50000  # Penalty for empty shifts when soft (very high)

    w_alan_kontenjan_sapma: int = 10000
    w_gunluk_denge: int = 5000
    w_saat_denge: int = 3000

    hafta_sonu_dengesi_aktif: bool = True
    w_cuma: int = 1000
    w_cumartesi: int = 1000
    w_pazar: int = 1000

    tatil_dengesi_aktif: bool = True
    w_tatil: int = 200

    iki_gun_bosluk_aktif: bool = True
    w_iki_gun_bosluk: int = 300

    w_birlikte_odul: int = 30
    w_esnek_ayri: int = 800
    w_tercih: int = 2
    w_alan_denklik: int = 800

    saat_bazli_denge: bool = True

    max_sure_saniye: float = 60.0
    thread_sayisi: int = 8


@dataclass
class SolverInput:
    """Solver'a gönderilecek tüm veriler"""
    yil: int
    ay: int
    personeller: List[str]
    hedefler: Dict[str, int]  # Toplam nöbet hedefi (eski mod veya fallback)
    hedefler_saat: Dict[str, int] = field(default_factory=dict)
    vardiya_hedefleri: Dict[str, Dict[str, int]] = field(default_factory=dict)  # {kisi: {vardiya: hedef}}
    izinler: Dict[str, Set[int]] = field(default_factory=dict)
    tatiller: Set[int] = field(default_factory=set)
    
    ayri_tut: List[Tuple[str, str]] = field(default_factory=list)
    birlikte_tut: List[Tuple[str, str, int]] = field(default_factory=list)
    esnek_ayri_tut: List[Tuple[str, str]] = field(default_factory=list)
    tercih_edilen: Dict[str, Set[int]] = field(default_factory=dict)
    
    alanlar: List[AlanTanimi] = field(default_factory=list)
    personel_alan_yetkinlikleri: Dict[str, List[str]] = field(default_factory=dict)
    alan_bazli_denklik: bool = True
    
    personel_kidem_gruplari: Dict[str, str] = field(default_factory=dict)
    
    vardiyalar: List[VardiyaTanimi] = field(default_factory=list)
    personel_vardiya_kisitlari: Dict[str, List[str]] = field(default_factory=dict)
    
    config: SolverConfig = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = SolverConfig()
    
    @property
    def coklu_alan_modu(self) -> bool:
        return len(self.alanlar) > 0
    
    @property
    def vardiya_modu(self) -> bool:
        return len(self.vardiyalar) > 0


class NobetSolver:
    """CP-SAT tabanlı nöbet çizelgesi optimizasyonu."""
    
    def __init__(self, input_data: SolverInput):
        self.input = input_data
        self.gun_sayisi = ay_gun_sayisi(input_data.yil, input_data.ay)
        self.n_personel = len(input_data.personeller)
        self.name_to_idx = {name: i for i, name in enumerate(input_data.personeller)}
        
        self.alan_isimleri = [a.isim for a in input_data.alanlar]
        self.alan_to_idx = {a.isim: i for i, a in enumerate(input_data.alanlar)}
        self.n_alan = max(len(input_data.alanlar), 1)
        
        self.vardiya_isimleri = [v.isim for v in input_data.vardiyalar]
        self.vardiya_to_idx = {v.isim: i for i, v in enumerate(input_data.vardiyalar)}
        self.n_vardiya = max(len(input_data.vardiyalar), 1)
        
        self.vardiya_saatleri = {v.isim: v.saat for v in input_data.vardiyalar}
        
        self.model = cp_model.CpModel()
        self.x = {}
        self.objective_terms = []
    
    def coz(self) -> Dict:
        self._degiskenleri_olustur()
        self._hard_constraints_ekle()
        self._soft_constraints_ekle()
        return self._coz_ve_sonuc_al()
    
    def _degiskenleri_olustur(self):
        for p in range(self.n_personel):
            for g in range(1, self.gun_sayisi + 1):
                for a in range(self.n_alan):
                    for v in range(self.n_vardiya):
                        self.x[p, g, a, v] = self.model.NewBoolVar(f"x_{p}_{g}_{a}_{v}")
    
    def _hard_constraints_ekle(self):
        self._hedef_nobet_sayilari()
        self._izin_gunleri()
        self._kisi_gun_tek_atama()

        if self.input.coklu_alan_modu:
            self._alan_yetkinlikleri()
            self._kidem_kurallari()

        if self.input.vardiya_modu:
            self._vardiya_kisitlari()
            self._alan_vardiya_eslesmesi()
            # Minimum staffing: Hard constraint if enforce_minimum_staffing is True
            if self.input.config.enforce_minimum_staffing:
                self._vardiya_minimum_kontenjan_hard()

        if self.input.config.ardisik_yasak:
            self._ardisik_gun_yasagi()

        if self.input.config.gunasiri_limit_aktif and self.input.config.max_gunasiri_per_kisi > 0:
            self._gunasiri_limiti()

        self._ayri_tutma_kurallari()
    
    def _soft_constraints_ekle(self):
        if self.input.coklu_alan_modu:
            self._alan_kontenjan_soft()
            self._gunluk_alan_dengesi()
            if self.input.alan_bazli_denklik:
                self._alan_bazli_denklik()
        else:
            self._gunluk_kisi_dengesi()

        # Minimum staffing: Soft constraint if enforce_minimum_staffing is False
        if self.input.vardiya_modu and not self.input.config.enforce_minimum_staffing:
            self._vardiya_minimum_kontenjan_soft()

        if self.input.config.saat_bazli_denge and self.input.vardiya_modu:
            self._saat_bazli_denge()

        if self.input.config.hafta_sonu_dengesi_aktif:
            self._hafta_sonu_adaleti()

        if self.input.config.iki_gun_bosluk_aktif:
            self._iki_gun_bosluk_tercihi()

        self._birlikte_tutma_kurallari()
        self._esnek_ayri_tutma_kurallari()
        self._tercih_edilen_gunler()

        self.model.Minimize(sum(self.objective_terms))
    
    def _hedef_nobet_sayilari(self):
        """
        Her personel için hedef sayıda nöbet tutmalı.
        - Vardiya hedefleri tanımlıysa: her vardiya için ayrı hedef
        - Değilse: toplam nöbet hedefi (eski mod)
        """
        for p_idx, isim in enumerate(self.input.personeller):
            # Calculate max possible shifts for this person
            musait_gunler = [g for g in range(1, self.gun_sayisi + 1)
                           if g not in self.input.izinler.get(isim, set())]
            musait_gun_sayisi = len(musait_gunler)

            if self.input.config.ardisik_yasak:
                max_mumkun = (musait_gun_sayisi + 1) // 2
            else:
                max_mumkun = musait_gun_sayisi

            # Vardiya bazlı hedef var mı?
            vardiya_hedef = self.input.vardiya_hedefleri.get(isim, {})

            if vardiya_hedef and self.input.vardiya_modu:
                # VARDIYA BAZLI HEDEF MODU
                toplam_vardiya_hedef = sum(vardiya_hedef.values())
                if toplam_vardiya_hedef > max_mumkun:
                    raise ValueError(f"{isim}: Toplam vardiya hedefi ({toplam_vardiya_hedef}) > maksimum mümkün ({max_mumkun})")

                for v_idx, vardiya in enumerate(self.input.vardiyalar):
                    hedef = vardiya_hedef.get(vardiya.isim, 0)
                    if hedef > 0:
                        if hedef > max_mumkun:
                            raise ValueError(f"{isim}: {vardiya.isim} hedefi ({hedef}) > maksimum mümkün ({max_mumkun})")
                        # Bu kişinin bu vardiyadan tutması gereken nöbet sayısı
                        toplam = sum(self.x[p_idx, g, a, v_idx]
                                    for g in range(1, self.gun_sayisi + 1)
                                    for a in range(self.n_alan))
                        self.model.Add(toplam == hedef)
                    elif hedef == 0:
                        # Bu vardiyada çalışmamalı (hedef 0 ise)
                        for g in range(1, self.gun_sayisi + 1):
                            for a in range(self.n_alan):
                                self.model.Add(self.x[p_idx, g, a, v_idx] == 0)
            else:
                # ESKİ MOD - toplam nöbet hedefi
                hedef = self.input.hedefler.get(isim, 0)
                if hedef > max_mumkun:
                    raise ValueError(f"{isim}: Hedef ({hedef}) > maksimum mümkün ({max_mumkun})")
                toplam = sum(self.x[p_idx, g, a, v]
                            for g in range(1, self.gun_sayisi + 1)
                            for a in range(self.n_alan)
                            for v in range(self.n_vardiya))
                self.model.Add(toplam == hedef)
    
    def _izin_gunleri(self):
        for p_idx, isim in enumerate(self.input.personeller):
            for gun in self.input.izinler.get(isim, set()):
                if 1 <= gun <= self.gun_sayisi:
                    for a in range(self.n_alan):
                        for v in range(self.n_vardiya):
                            self.model.Add(self.x[p_idx, gun, a, v] == 0)
    
    def _kisi_gun_tek_atama(self):
        for p in range(self.n_personel):
            for g in range(1, self.gun_sayisi + 1):
                self.model.Add(sum(self.x[p, g, a, v] 
                                  for a in range(self.n_alan) 
                                  for v in range(self.n_vardiya)) <= 1)
    
    def _alan_yetkinlikleri(self):
        for p_idx, isim in enumerate(self.input.personeller):
            yetkin = self.input.personel_alan_yetkinlikleri.get(isim, [])
            if not yetkin:
                continue
            for a_idx, alan in enumerate(self.input.alanlar):
                if alan.isim not in yetkin:
                    for g in range(1, self.gun_sayisi + 1):
                        for v in range(self.n_vardiya):
                            self.model.Add(self.x[p_idx, g, a_idx, v] == 0)
    
    def _vardiya_kisitlari(self):
        for p_idx, isim in enumerate(self.input.personeller):
            kisitlar = self.input.personel_vardiya_kisitlari.get(isim, [])
            if not kisitlar:
                continue
            for v_idx, vardiya in enumerate(self.input.vardiyalar):
                if vardiya.isim not in kisitlar:
                    for g in range(1, self.gun_sayisi + 1):
                        for a in range(self.n_alan):
                            self.model.Add(self.x[p_idx, g, a, v_idx] == 0)
    
    def _alan_vardiya_eslesmesi(self):
        for a_idx, alan in enumerate(self.input.alanlar):
            gecerli = alan.vardiya_tipleri
            if not gecerli:
                continue
            for v_idx, vardiya in enumerate(self.input.vardiyalar):
                if vardiya.isim not in gecerli:
                    for p in range(self.n_personel):
                        for g in range(1, self.gun_sayisi + 1):
                            self.model.Add(self.x[p, g, a_idx, v_idx] == 0)
    
    def _vardiya_minimum_kontenjan_hard(self):
        """Her vardiyada (her alanda) günde en az 1 kişi olmalı - HARD CONSTRAINT"""
        for g in range(1, self.gun_sayisi + 1):
            for a in range(self.n_alan):
                for v in range(self.n_vardiya):
                    # Bu alan-vardiya kombinasyonu geçerli mi kontrol et
                    if self.input.coklu_alan_modu:
                        alan = self.input.alanlar[a]
                        vardiya = self.input.vardiyalar[v]
                        # Alan için vardiya kısıtı varsa ve bu vardiya listede yoksa atla
                        if alan.vardiya_tipleri and vardiya.isim not in alan.vardiya_tipleri:
                            continue

                    # Bu gün/alan/vardiya için en az 1 kişi
                    toplam = sum(self.x[p, g, a, v] for p in range(self.n_personel))
                    self.model.Add(toplam >= 1)

    def _vardiya_minimum_kontenjan_soft(self):
        """Her vardiyada (her alanda) günde en az 1 kişi olmalı - SOFT CONSTRAINT"""
        w = self.input.config.w_vardiya_min_kontenjan
        for g in range(1, self.gun_sayisi + 1):
            for a in range(self.n_alan):
                for v in range(self.n_vardiya):
                    # Bu alan-vardiya kombinasyonu geçerli mi kontrol et
                    if self.input.coklu_alan_modu:
                        alan = self.input.alanlar[a]
                        vardiya = self.input.vardiyalar[v]
                        # Alan için vardiya kısıtı varsa ve bu vardiya listede yoksa atla
                        if alan.vardiya_tipleri and vardiya.isim not in alan.vardiya_tipleri:
                            continue

                    # Soft penalty for empty slots
                    bos = self.model.NewBoolVar(f"bos_{g}_{a}_{v}")
                    toplam = sum(self.x[p, g, a, v] for p in range(self.n_personel))
                    # bos = 1 if toplam == 0 (empty shift)
                    self.model.Add(bos == (toplam == 0))
                    self.objective_terms.append(bos * w)
    
    def _kidem_kurallari(self):
        for a_idx, alan in enumerate(self.input.alanlar):
            if not alan.kidem_kurallari:
                continue
            for grup_isim, kurallar in alan.kidem_kurallari.items():
                min_k = kurallar.get("min", 0)
                max_k = kurallar.get("max")
                
                grup_idx = [p for p, isim in enumerate(self.input.personeller)
                           if self.input.personel_kidem_gruplari.get(isim) == grup_isim]
                if not grup_idx:
                    continue
                
                for g in range(1, self.gun_sayisi + 1):
                    toplam = sum(self.x[p, g, a_idx, v] 
                                for p in grup_idx for v in range(self.n_vardiya))
                    if min_k > 0:
                        self.model.Add(toplam >= min_k)
                    if max_k and max_k > 0:
                        self.model.Add(toplam <= max_k)
    
    def _ardisik_gun_yasagi(self):
        for p in range(self.n_personel):
            for g in range(1, self.gun_sayisi):
                bugun = sum(self.x[p, g, a, v] for a in range(self.n_alan) for v in range(self.n_vardiya))
                yarin = sum(self.x[p, g+1, a, v] for a in range(self.n_alan) for v in range(self.n_vardiya))
                self.model.Add(bugun + yarin <= 1)
    
    def _gunasiri_limiti(self):
        max_ga = self.input.config.max_gunasiri_per_kisi
        for p in range(self.n_personel):
            ga_list = []
            for g in range(1, self.gun_sayisi - 1):
                b = self.model.NewBoolVar(f"ga_{p}_{g}")
                g1 = sum(self.x[p, g, a, v] for a in range(self.n_alan) for v in range(self.n_vardiya))
                g3 = sum(self.x[p, g+2, a, v] for a in range(self.n_alan) for v in range(self.n_vardiya))
                self.model.Add(b <= g1)
                self.model.Add(b <= g3)
                self.model.Add(b >= g1 + g3 - 1)
                ga_list.append(b)
            if ga_list:
                self.model.Add(sum(ga_list) <= max_ga)
    
    def _ayri_tutma_kurallari(self):
        for (a, b) in self.input.ayri_tut:
            if a not in self.name_to_idx or b not in self.name_to_idx:
                continue
            pa, pb = self.name_to_idx[a], self.name_to_idx[b]
            for g in range(1, self.gun_sayisi + 1):
                ta = sum(self.x[pa, g, al, v] for al in range(self.n_alan) for v in range(self.n_vardiya))
                tb = sum(self.x[pb, g, al, v] for al in range(self.n_alan) for v in range(self.n_vardiya))
                self.model.Add(ta + tb <= 1)
    
    def _alan_kontenjan_soft(self):
        w = self.input.config.w_alan_kontenjan_sapma
        for a_idx, alan in enumerate(self.input.alanlar):
            hedef = alan.gunluk_kontenjan
            max_k = alan.max_kontenjan
            
            for g in range(1, self.gun_sayisi + 1):
                toplam = sum(self.x[p, g, a_idx, v] 
                            for p in range(self.n_personel) for v in range(self.n_vardiya))
                
                if max_k and max_k > 0:
                    self.model.Add(toplam <= max_k)
                
                sapma_pos = self.model.NewIntVar(0, self.n_personel, f"sp_{a_idx}_{g}")
                sapma_neg = self.model.NewIntVar(0, self.n_personel, f"sn_{a_idx}_{g}")
                self.model.Add(toplam - hedef == sapma_pos - sapma_neg)
                self.objective_terms.append(sapma_pos * w)
                self.objective_terms.append(sapma_neg * w)
    
    def _gunluk_alan_dengesi(self):
        w = self.input.config.w_gunluk_denge
        for a_idx in range(self.n_alan):
            topl = []
            for g in range(1, self.gun_sayisi + 1):
                t = self.model.NewIntVar(0, self.n_personel * self.n_vardiya, f"gad_{a_idx}_{g}")
                self.model.Add(t == sum(self.x[p, g, a_idx, v] 
                                       for p in range(self.n_personel) for v in range(self.n_vardiya)))
                topl.append(t)
            if len(topl) > 1:
                mn = self.model.NewIntVar(0, self.n_personel * self.n_vardiya, f"gad_mn_{a_idx}")
                mx = self.model.NewIntVar(0, self.n_personel * self.n_vardiya, f"gad_mx_{a_idx}")
                self.model.AddMinEquality(mn, topl)
                self.model.AddMaxEquality(mx, topl)
                fark = self.model.NewIntVar(0, self.n_personel * self.n_vardiya, f"gad_f_{a_idx}")
                self.model.Add(fark == mx - mn)
                self.objective_terms.append(fark * w)
    
    def _gunluk_kisi_dengesi(self):
        w = self.input.config.w_gunluk_denge
        topl = []
        for g in range(1, self.gun_sayisi + 1):
            t = self.model.NewIntVar(0, self.n_personel * self.n_vardiya, f"gkd_{g}")
            self.model.Add(t == sum(self.x[p, g, 0, v] 
                                   for p in range(self.n_personel) for v in range(self.n_vardiya)))
            topl.append(t)
        if len(topl) > 1:
            mn = self.model.NewIntVar(0, self.n_personel * self.n_vardiya, "gkd_mn")
            mx = self.model.NewIntVar(0, self.n_personel * self.n_vardiya, "gkd_mx")
            self.model.AddMinEquality(mn, topl)
            self.model.AddMaxEquality(mx, topl)
            fark = self.model.NewIntVar(0, self.n_personel * self.n_vardiya, "gkd_f")
            self.model.Add(fark == mx - mn)
            self.objective_terms.append(fark * w)
    
    def _saat_bazli_denge(self):
        w = self.input.config.w_saat_denge
        max_saat = self.gun_sayisi * 24
        saatler = []
        for p in range(self.n_personel):
            s = self.model.NewIntVar(0, max_saat, f"saat_{p}")
            toplam = []
            for g in range(1, self.gun_sayisi + 1):
                for a in range(self.n_alan):
                    for v_idx, vrd in enumerate(self.input.vardiyalar):
                        saat = self.vardiya_saatleri.get(vrd.isim, 24)
                        toplam.append(self.x[p, g, a, v_idx] * saat)
            self.model.Add(s == sum(toplam))
            saatler.append(s)
        if len(saatler) > 1:
            mn = self.model.NewIntVar(0, max_saat, "saat_mn")
            mx = self.model.NewIntVar(0, max_saat, "saat_mx")
            self.model.AddMinEquality(mn, saatler)
            self.model.AddMaxEquality(mx, saatler)
            fark = self.model.NewIntVar(0, max_saat, "saat_f")
            self.model.Add(fark == mx - mn)
            self.objective_terms.append(fark * w)
    
    def _alan_bazli_denklik(self):
        w = self.input.config.w_alan_denklik
        for a_idx in range(self.n_alan):
            sayimlar = []
            for p in range(self.n_personel):
                s = self.model.NewIntVar(0, self.gun_sayisi * self.n_vardiya, f"abd_{a_idx}_{p}")
                self.model.Add(s == sum(self.x[p, g, a_idx, v] 
                                       for g in range(1, self.gun_sayisi + 1) for v in range(self.n_vardiya)))
                sayimlar.append(s)
            if len(sayimlar) > 1:
                mn = self.model.NewIntVar(0, self.gun_sayisi * self.n_vardiya, f"abd_mn_{a_idx}")
                mx = self.model.NewIntVar(0, self.gun_sayisi * self.n_vardiya, f"abd_mx_{a_idx}")
                self.model.AddMinEquality(mn, sayimlar)
                self.model.AddMaxEquality(mx, sayimlar)
                fark = self.model.NewIntVar(0, self.gun_sayisi * self.n_vardiya, f"abd_f_{a_idx}")
                self.model.Add(fark == mx - mn)
                self.objective_terms.append(fark * w)
    
    def _hafta_sonu_adaleti(self):
        yil, ay = self.input.yil, self.input.ay
        if self.input.config.w_cuma > 0:
            self._adalet_ekle(gunleri_weekday_ile_filtrele(yil, ay, 4), self.input.config.w_cuma, "cuma")
        if self.input.config.w_cumartesi > 0:
            self._adalet_ekle(gunleri_weekday_ile_filtrele(yil, ay, 5), self.input.config.w_cumartesi, "cts")
        if self.input.config.w_pazar > 0:
            self._adalet_ekle(gunleri_weekday_ile_filtrele(yil, ay, 6), self.input.config.w_pazar, "paz")
        if self.input.config.tatil_dengesi_aktif and self.input.config.w_tatil > 0:
            self._adalet_ekle(list(self.input.tatiller), self.input.config.w_tatil, "tatil")
    
    def _adalet_ekle(self, gunler: List[int], agirlik: int, tag: str):
        if not gunler:
            return
        sayimlar = []
        for p in range(self.n_personel):
            s = self.model.NewIntVar(0, len(gunler) * self.n_alan * self.n_vardiya, f"{tag}_{p}")
            self.model.Add(s == sum(self.x[p, g, a, v] 
                                   for g in gunler for a in range(self.n_alan) for v in range(self.n_vardiya)))
            sayimlar.append(s)
        if len(sayimlar) > 1:
            ub = len(gunler) * self.n_alan * self.n_vardiya
            mn = self.model.NewIntVar(0, ub, f"{tag}_mn")
            mx = self.model.NewIntVar(0, ub, f"{tag}_mx")
            self.model.AddMinEquality(mn, sayimlar)
            self.model.AddMaxEquality(mx, sayimlar)
            fark = self.model.NewIntVar(0, ub, f"{tag}_f")
            self.model.Add(fark == mx - mn)
            self.objective_terms.append(fark * agirlik)
    
    def _iki_gun_bosluk_tercihi(self):
        w = self.input.config.w_iki_gun_bosluk
        for p in range(self.n_personel):
            for g in range(1, self.gun_sayisi - 1):
                ceza = self.model.NewBoolVar(f"bos_{p}_{g}")
                g1 = sum(self.x[p, g, a, v] for a in range(self.n_alan) for v in range(self.n_vardiya))
                g3 = sum(self.x[p, g+2, a, v] for a in range(self.n_alan) for v in range(self.n_vardiya))
                self.model.Add(ceza >= g1 + g3 - 1)
                self.objective_terms.append(ceza * w)
    
    def _birlikte_tutma_kurallari(self):
        for (a, b, min_k) in self.input.birlikte_tut:
            if a not in self.name_to_idx or b not in self.name_to_idx:
                continue
            pa, pb = self.name_to_idx[a], self.name_to_idx[b]
            birlikte = []
            for g in range(1, self.gun_sayisi + 1):
                t = self.model.NewBoolVar(f"bir_{pa}_{pb}_{g}")
                ca = sum(self.x[pa, g, al, v] for al in range(self.n_alan) for v in range(self.n_vardiya))
                cb = sum(self.x[pb, g, al, v] for al in range(self.n_alan) for v in range(self.n_vardiya))
                self.model.Add(t <= ca)
                self.model.Add(t <= cb)
                self.model.Add(t >= ca + cb - 1)
                birlikte.append(t)
            if birlikte:
                toplam = self.model.NewIntVar(0, self.gun_sayisi, f"bir_t_{pa}_{pb}")
                self.model.Add(toplam == sum(birlikte))
                self.model.Add(toplam >= min_k)
                self.objective_terms.append(toplam * (-self.input.config.w_birlikte_odul))
    
    def _esnek_ayri_tutma_kurallari(self):
        w = self.input.config.w_esnek_ayri
        for (a, b) in self.input.esnek_ayri_tut:
            if a not in self.name_to_idx or b not in self.name_to_idx:
                continue
            pa, pb = self.name_to_idx[a], self.name_to_idx[b]
            for g in range(1, self.gun_sayisi + 1):
                t = self.model.NewBoolVar(f"esn_{pa}_{pb}_{g}")
                ca = sum(self.x[pa, g, al, v] for al in range(self.n_alan) for v in range(self.n_vardiya))
                cb = sum(self.x[pb, g, al, v] for al in range(self.n_alan) for v in range(self.n_vardiya))
                self.model.Add(t >= ca + cb - 1)
                self.objective_terms.append(t * w)
    
    def _tercih_edilen_gunler(self):
        w = self.input.config.w_tercih
        for p_idx, isim in enumerate(self.input.personeller):
            for g in self.input.tercih_edilen.get(isim, set()):
                if 1 <= g <= self.gun_sayisi:
                    for a in range(self.n_alan):
                        for v in range(self.n_vardiya):
                            self.objective_terms.append(self.x[p_idx, g, a, v] * (-w))
    
    def _coz_ve_sonuc_al(self) -> Dict:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.input.config.max_sure_saniye
        solver.parameters.num_search_workers = self.input.config.thread_sayisi
        
        status = solver.Solve(self.model)
        
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise ValueError("Çözüm bulunamadı (kısıtlar fazla sıkı olabilir).")
        
        if self.input.vardiya_modu and self.input.coklu_alan_modu:
            sonuc = {}
            for g in range(1, self.gun_sayisi + 1):
                sonuc[g] = {}
                for a_idx, alan in enumerate(self.input.alanlar):
                    sonuc[g][alan.isim] = {}
                    for v_idx, vardiya in enumerate(self.input.vardiyalar):
                        kisiler = [isim for p_idx, isim in enumerate(self.input.personeller)
                                  if solver.Value(self.x[p_idx, g, a_idx, v_idx]) == 1]
                        if kisiler:
                            sonuc[g][alan.isim][vardiya.isim] = kisiler
            return sonuc
        
        elif self.input.vardiya_modu:
            sonuc = {}
            for g in range(1, self.gun_sayisi + 1):
                sonuc[g] = {}
                for v_idx, vardiya in enumerate(self.input.vardiyalar):
                    kisiler = [isim for p_idx, isim in enumerate(self.input.personeller)
                              if solver.Value(self.x[p_idx, g, 0, v_idx]) == 1]
                    if kisiler:
                        sonuc[g][vardiya.isim] = kisiler
            return sonuc
        
        elif self.input.coklu_alan_modu:
            sonuc = {}
            for g in range(1, self.gun_sayisi + 1):
                sonuc[g] = {}
                for a_idx, alan in enumerate(self.input.alanlar):
                    sonuc[g][alan.isim] = [isim for p_idx, isim in enumerate(self.input.personeller)
                                          if solver.Value(self.x[p_idx, g, a_idx, 0]) == 1]
            return sonuc
        
        else:
            sonuc = {}
            for g in range(1, self.gun_sayisi + 1):
                sonuc[g] = [isim for p_idx, isim in enumerate(self.input.personeller)
                           if solver.Value(self.x[p_idx, g, 0, 0]) == 1]
            return sonuc


# =============================================================================
# GELİŞMİŞ TEŞHİS SİSTEMİ
# =============================================================================

@dataclass
class TeshisSonucu:
    """Tek bir teşhis sonucu"""
    tip: str  # "hedef_imkansiz", "kidem_eksik", "kapasite_yetersiz", "vardiya_uyumsuz", etc.
    seviye: str  # "error", "warning"
    gun: Optional[int]  # None ise genel sorun
    mesaj: str
    detay: Dict = field(default_factory=dict)


def gelismis_teshis(
    yil: int, 
    ay: int, 
    personeller: List[str], 
    hedefler: Dict[str, int],
    vardiya_hedefleri: Dict[str, Dict[str, int]],  # {kisi: {vardiya: hedef}}
    izinler: Dict[str, Set[int]], 
    tatiller: Set[int],
    birlikte_tut: List[Tuple[str, str, int]], 
    ayri_tut: List[Tuple[str, str]],
    alanlar: List[AlanTanimi] = None,
    vardiyalar: List[VardiyaTanimi] = None,
    personel_alan_yetkinlikleri: Dict[str, List[str]] = None,
    personel_vardiya_kisitlari: Dict[str, List[str]] = None,
    personel_kidem_gruplari: Dict[str, str] = None,
    kidem_kurallari: Dict[str, Dict[str, Dict[str, int]]] = None,  # {alan: {grup: {min/max}}}
    ardisik_yasak: bool = True
) -> List[TeshisSonucu]:
    """
    Çözüm bulunamadığında detaylı teşhis yapar.
    Tüm olası sorunları tespit edip raporlar.
    """
    sorunlar = []
    gun_sayisi = ay_gun_sayisi(yil, ay)
    
    personel_alan_yetkinlikleri = personel_alan_yetkinlikleri or {}
    personel_vardiya_kisitlari = personel_vardiya_kisitlari or {}
    personel_kidem_gruplari = personel_kidem_gruplari or {}
    kidem_kurallari = kidem_kurallari or {}
    alanlar = alanlar or []
    vardiyalar = vardiyalar or []
    
    # =========================================================================
    # 1. KİŞİ BAZLI HEDEF ANALİZİ
    # =========================================================================
    
    for p in personeller:
        musait_gunler = [g for g in range(1, gun_sayisi + 1) if g not in izinler.get(p, set())]
        musait_gun_sayisi = len(musait_gunler)
        
        # Ardışık yasak varsa max nöbet = (müsait+1)/2
        if ardisik_yasak:
            max_mumkun = (musait_gun_sayisi + 1) // 2
        else:
            max_mumkun = musait_gun_sayisi
        
        toplam_hedef = hedefler.get(p, 0)
        
        if toplam_hedef > max_mumkun:
            sorunlar.append(TeshisSonucu(
                tip="hedef_imkansiz",
                seviye="error",
                gun=None,
                mesaj=f"{p}: Hedef ({toplam_hedef}) > maksimum mümkün ({max_mumkun})",
                detay={
                    "personel": p,
                    "hedef": toplam_hedef,
                    "musait_gun": musait_gun_sayisi,
                    "max_mumkun": max_mumkun,
                    "ardisik_yasak": ardisik_yasak
                }
            ))
        
        # Vardiya bazlı hedef kontrolü
        if p in vardiya_hedefleri and vardiyalar:
            p_vardiya_hedef = vardiya_hedefleri[p]
            p_kisitlar = personel_vardiya_kisitlari.get(p, [])
            
            for vardiya_isim, hedef in p_vardiya_hedef.items():
                if hedef > 0 and p_kisitlar and vardiya_isim not in p_kisitlar:
                    sorunlar.append(TeshisSonucu(
                        tip="vardiya_uyumsuz",
                        seviye="error",
                        gun=None,
                        mesaj=f"{p}: {vardiya_isim} için hedef var ({hedef}) ama bu vardiyada çalışamaz",
                        detay={
                            "personel": p,
                            "vardiya": vardiya_isim,
                            "hedef": hedef,
                            "calisabilir_vardiyalar": p_kisitlar
                        }
                    ))
    
    # =========================================================================
    # 2. ALAN YETKİNLİK ANALİZİ
    # =========================================================================
    
    if alanlar:
        for p in personeller:
            yetkin_alanlar = personel_alan_yetkinlikleri.get(p, [])
            hedef = hedefler.get(p, 0)
            
            if yetkin_alanlar and hedef > 0:
                # Bu kişi sadece belirli alanlarda çalışabilir
                # O alanların toplam kapasitesi yeterli mi?
                toplam_kapasite = 0
                for alan in alanlar:
                    if alan.isim in yetkin_alanlar:
                        toplam_kapasite += alan.gunluk_kontenjan * gun_sayisi
                
                if hedef > toplam_kapasite:
                    sorunlar.append(TeshisSonucu(
                        tip="alan_kapasite_yetersiz",
                        seviye="warning",
                        gun=None,
                        mesaj=f"{p}: Hedef ({hedef}) > çalışabildiği alanların kapasitesi ({toplam_kapasite})",
                        detay={
                            "personel": p,
                            "hedef": hedef,
                            "yetkin_alanlar": yetkin_alanlar,
                            "toplam_kapasite": toplam_kapasite
                        }
                    ))
    
    # =========================================================================
    # 3. GÜNLÜK KAPASİTE ANALİZİ (Unfillable Shift Detection)
    # =========================================================================

    for gun in range(1, gun_sayisi + 1):
        musait_kisiler = [p for p in personeller if gun not in izinler.get(p, set())]

        if alanlar:
            # Çoklu alan modu
            for alan in alanlar:
                # Bu alanda çalışabilecek müsait kişiler
                alan_musait = [
                    p for p in musait_kisiler
                    if not personel_alan_yetkinlikleri.get(p) or alan.isim in personel_alan_yetkinlikleri.get(p, [])
                ]

                if len(alan_musait) < alan.gunluk_kontenjan:
                    sorunlar.append(TeshisSonucu(
                        tip="gunluk_kapasite_yetersiz",
                        seviye="error",
                        gun=gun,
                        mesaj=f"Gün {gun}, {alan.isim}: Müsait kişi ({len(alan_musait)}) < kontenjan ({alan.gunluk_kontenjan})",
                        detay={
                            "gun": gun,
                            "alan": alan.isim,
                            "musait_kisi_sayisi": len(alan_musait),
                            "musait_kisiler": alan_musait,
                            "gerekli_kontenjan": alan.gunluk_kontenjan
                        }
                    ))

                # Kıdem kuralları kontrolü
                alan_kidem = alan.kidem_kurallari
                if alan_kidem:
                    for grup_isim, kurallar in alan_kidem.items():
                        min_k = kurallar.get("min", 0)
                        if min_k > 0:
                            # Bu gruptan bu alanda çalışabilecek müsait kişiler
                            grup_musait = [
                                p for p in alan_musait
                                if personel_kidem_gruplari.get(p) == grup_isim
                            ]

                            if len(grup_musait) < min_k:
                                sorunlar.append(TeshisSonucu(
                                    tip="kidem_eksik",
                                    seviye="error",
                                    gun=gun,
                                    mesaj=f"Gün {gun}, {alan.isim}: {grup_isim} grubu min {min_k} gerekli, müsait = {len(grup_musait)}",
                                    detay={
                                        "gun": gun,
                                        "alan": alan.isim,
                                        "kidem_grubu": grup_isim,
                                        "gerekli_min": min_k,
                                        "musait_sayisi": len(grup_musait),
                                        "musait_kisiler": grup_musait
                                    }
                                ))

        # Vardiya kontrolü - detect unfillable shifts
        if vardiyalar:
            for vardiya in vardiyalar:
                # Bu vardiyada çalışabilecek müsait kişiler
                vardiya_musait = [
                    p for p in musait_kisiler
                    if not personel_vardiya_kisitlari.get(p) or vardiya.isim in personel_vardiya_kisitlari.get(p, [])
                ]

                # If there are multiple areas, check each area+vardiya combination
                if alanlar:
                    for alan in alanlar:
                        # Skip if this vardiya is not valid for this area
                        if alan.vardiya_tipleri and vardiya.isim not in alan.vardiya_tipleri:
                            continue

                        # People who can work in this area AND this shift
                        alan_vardiya_musait = [
                            p for p in vardiya_musait
                            if not personel_alan_yetkinlikleri.get(p) or alan.isim in personel_alan_yetkinlikleri.get(p, [])
                        ]

                        if len(alan_vardiya_musait) < 1:
                            sorunlar.append(TeshisSonucu(
                                tip="vardiya_alan_bos_kalacak",
                                seviye="error",
                                gun=gun,
                                mesaj=f"Gün {gun}, {alan.isim}, {vardiya.isim}: Çalışabilecek müsait kimse yok! (Minimum staffing gerekli)",
                                detay={
                                    "gun": gun,
                                    "alan": alan.isim,
                                    "vardiya": vardiya.isim,
                                    "musait_kisiler": [],
                                    "oneri": "Bu gün için izinleri azaltın veya minimum staffing ayarını soft yapın"
                                }
                            ))
                else:
                    # Single area mode
                    if len(vardiya_musait) < 1:
                        sorunlar.append(TeshisSonucu(
                            tip="vardiya_bos_kalacak",
                            seviye="error",
                            gun=gun,
                            mesaj=f"Gün {gun}, {vardiya.isim}: Çalışabilecek müsait kimse yok! (Minimum staffing gerekli)",
                            detay={
                                "gun": gun,
                                "vardiya": vardiya.isim,
                                "musait_kisiler": [],
                                "oneri": "Bu gün için izinleri azaltın veya minimum staffing ayarını soft yapın"
                            }
                        ))
    
    # =========================================================================
    # 4. TOPLAM HEDEF vs KAPASİTE ANALİZİ
    # =========================================================================
    
    toplam_hedef = sum(hedefler.values())
    
    if alanlar:
        toplam_kapasite = sum(a.gunluk_kontenjan for a in alanlar) * gun_sayisi
        if vardiyalar:
            toplam_kapasite *= len(vardiyalar)
    elif vardiyalar:
        toplam_kapasite = len(vardiyalar) * gun_sayisi
    else:
        toplam_kapasite = gun_sayisi
    
    if toplam_hedef < toplam_kapasite:
        sorunlar.append(TeshisSonucu(
            tip="toplam_hedef_yetersiz",
            seviye="warning",
            gun=None,
            mesaj=f"Toplam hedef ({toplam_hedef}) < gereken kapasite ({toplam_kapasite}) - bazı slotlar boş kalabilir",
            detay={
                "toplam_hedef": toplam_hedef,
                "toplam_kapasite": toplam_kapasite,
                "fark": toplam_kapasite - toplam_hedef
            }
        ))
    elif toplam_hedef > toplam_kapasite:
        sorunlar.append(TeshisSonucu(
            tip="toplam_hedef_fazla",
            seviye="error",
            gun=None,
            mesaj=f"Toplam hedef ({toplam_hedef}) > kapasite ({toplam_kapasite}) - İmkansız!",
            detay={
                "toplam_hedef": toplam_hedef,
                "toplam_kapasite": toplam_kapasite
            }
        ))
    
    # =========================================================================
    # 5. EŞLEŞTİRME KURALLARI ANALİZİ
    # =========================================================================
    
    for (a, b, min_k) in birlikte_tut:
        if a in personeller and b in personeller:
            ortak_gunler = [
                g for g in range(1, gun_sayisi + 1) 
                if g not in izinler.get(a, set()) and g not in izinler.get(b, set())
            ]
            max_ortak = (len(ortak_gunler) + 1) // 2 if ardisik_yasak else len(ortak_gunler)
            
            if max_ortak < min_k:
                sorunlar.append(TeshisSonucu(
                    tip="birlikte_tutma_imkansiz",
                    seviye="error",
                    gun=None,
                    mesaj=f"{a} + {b}: Min {min_k} birlikte gün gerekli, mümkün = {max_ortak}",
                    detay={
                        "personel_a": a,
                        "personel_b": b,
                        "min_birlikte": min_k,
                        "ortak_musait_gun": len(ortak_gunler),
                        "max_mumkun": max_ortak
                    }
                ))
    
    # Sonuçları öncelik sırasına göre sırala (error önce)
    sorunlar.sort(key=lambda x: (0 if x.seviye == "error" else 1, x.gun or 0))
    
    if not sorunlar:
        sorunlar.append(TeshisSonucu(
            tip="belirsiz",
            seviye="warning",
            gun=None,
            mesaj="Belirgin sorun tespit edilemedi. Kısıtlar kombinasyonu çözümsüz olabilir.",
            detay={}
        ))
    
    return sorunlar


def teshis_ozeti(teshisler: List[TeshisSonucu]) -> str:
    """Teşhis sonuçlarını okunabilir metin olarak formatlar"""
    if not teshisler:
        return "Sorun tespit edilemedi."
    
    lines = []
    errors = [t for t in teshisler if t.seviye == "error"]
    warnings = [t for t in teshisler if t.seviye == "warning"]
    
    if errors:
        lines.append(f"❌ {len(errors)} KRİTİK SORUN:")
        for t in errors[:10]:  # İlk 10 hatayı göster
            lines.append(f"  • {t.mesaj}")
    
    if warnings:
        lines.append(f"⚠️ {len(warnings)} UYARI:")
        for t in warnings[:5]:  # İlk 5 uyarıyı göster
            lines.append(f"  • {t.mesaj}")
    
    return "\n".join(lines)


# Eski fonksiyon - geriye uyumluluk için
def cozum_bulunamadi_teshis(yil, ay, personeller, hedefler, izinler, tatiller,
                            birlikte_tut, ayri_tut, alanlar=None, min_kisi_per_gun=1):
    """Eski teşhis fonksiyonu - geriye uyumluluk için"""
    teshisler = gelismis_teshis(
        yil=yil, ay=ay, personeller=personeller, hedefler=hedefler,
        vardiya_hedefleri={}, izinler=izinler, tatiller=tatiller,
        birlikte_tut=birlikte_tut, ayri_tut=ayri_tut, alanlar=alanlar
    )
    return [t.mesaj for t in teshisler]
