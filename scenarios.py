"""
scenarios.py - Senin Roster App'in için Sentetik Veri Üretici

Bu modül, solver'ını test etmek için gerçekçi sahte veri üretir.
Üretilen veriler doğrudan senin session_state contract'ına uyumludur.

Kullanım:
    from scenarios import ScenarioGenerator, generate_quick_scenario
    
    # Seed ile tekrarlanabilir senaryo üret
    gen = ScenarioGenerator(seed=42)
    data = gen.generate(difficulty="normal", yil=2025, ay=2, num_personel=15)
    
    # data artık senin app'inin beklediği formatta bir dict
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Tuple
from datetime import date
import calendar
import json

from utils import kisinin_max_atama


# =============================================================================
# TÜRKÇE GÜN ADLARI (Senin app'inin kullandığı format)
# =============================================================================

GUN_ADLARI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

# weekday() -> 0=Pazartesi, 6=Pazar ile eşleşiyor


# =============================================================================
# İSİM ÜRETİCİ
# =============================================================================

class IsimUretici:
    """Gerçekçi Türkçe isimler üretir."""
    
    ISIMLER = [
        "Ahmet", "Mehmet", "Mustafa", "Ali", "Hüseyin", "Hasan", "İbrahim", "Ömer",
        "Fatma", "Ayşe", "Emine", "Hatice", "Zeynep", "Elif", "Merve", "Büşra",
        "Yusuf", "Emre", "Burak", "Murat", "Serkan", "Kemal", "Oğuz", "Cem",
        "Seda", "Deniz", "Esra", "Gül", "Pınar", "Derya", "Sibel", "Canan",
        "Tolga", "Barış", "Onur", "Kaan", "Arda", "Berk", "Efe", "Can",
        "Nur", "Gamze", "Özge", "Aslı", "Burcu", "Ebru", "İrem", "Melis"
    ]
    
    SOYISIMLER = [
        "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Yıldırım", "Öztürk",
        "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara",
        "Koç", "Kurt", "Özkan", "Şimşek", "Polat", "Korkmaz", "Özgür", "Erdoğan",
        "Acar", "Aksoy", "Aktaş", "Güneş", "Güler", "Tekin", "Şen", "Özen"
    ]
    
    def __init__(self, rng: random.Random):
        self.rng = rng
        self._kullanilan = set()
    
    def uret(self) -> str:
        """Benzersiz tam isim üret."""
        for _ in range(100):
            isim = self.rng.choice(self.ISIMLER)
            soyisim = self.rng.choice(self.SOYISIMLER)
            tam_isim = f"{isim} {soyisim}"
            if tam_isim not in self._kullanilan:
                self._kullanilan.add(tam_isim)
                return tam_isim
        # Fallback: numara ekle
        return f"{isim} {soyisim} {self.rng.randint(1, 99)}"


# =============================================================================
# ZORLUK PROFİLLERİ
# =============================================================================

ZORLUK_PROFILLERI = {
    "easy": {
        "aciklama": "Bol personel, az izin, gevşek kısıtlar",
        "personel_carpani": 1.4,
        "izin_min": 1,
        "izin_max": 3,
        "prefer_min": 0,
        "prefer_max": 2,
        "no_pairs_oran": 0.02,
        "soft_no_pairs_oran": 0.03,
        "want_pairs_sayi": 1,
        "weekday_block_oran": 0.05,
        "alan_aktif": False,
        "vardiya_aktif": False,
    },
    "normal": {
        "aciklama": "Gerçekçi personel/kısıt dengesi",
        "personel_carpani": 1.2,
        "izin_min": 2,
        "izin_max": 5,
        "prefer_min": 0,
        "prefer_max": 3,
        "no_pairs_oran": 0.04,
        "soft_no_pairs_oran": 0.05,
        "want_pairs_sayi": 2,
        "weekday_block_oran": 0.10,
        "alan_aktif": True,
        "vardiya_aktif": True,
    },
    "tight": {
        "aciklama": "Sıkı personel, çok izin, güçlü kısıtlar",
        "personel_carpani": 1.0,
        "izin_min": 3,
        "izin_max": 6,
        "prefer_min": 1,
        "prefer_max": 4,
        "no_pairs_oran": 0.07,
        "soft_no_pairs_oran": 0.08,
        "want_pairs_sayi": 3,
        "weekday_block_oran": 0.15,
        "alan_aktif": True,
        "vardiya_aktif": True,
    },
    "nightmare": {
        "aciklama": "Aşırı kısıtlar - çözümsüz olabilir!",
        "personel_carpani": 0.85,
        "izin_min": 4,
        "izin_max": 8,
        "prefer_min": 2,
        "prefer_max": 5,
        "no_pairs_oran": 0.12,
        "soft_no_pairs_oran": 0.10,
        "want_pairs_sayi": 4,
        "weekday_block_oran": 0.25,
        "alan_aktif": True,
        "vardiya_aktif": True,
    },
}


# =============================================================================
# RENK PALETİ
# =============================================================================

RENKLER = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
    "#F8B500", "#00CED1", "#FF69B4", "#32CD32", "#FFD700"
]


# =============================================================================
# ANA SENARYO ÜRETİCİ
# =============================================================================

class ScenarioGenerator:
    """
    Senin app'inin session_state contract'ına uygun sentetik veri üretir.
    
    Üretilen dict doğrudan inject_scenario_to_session_state() ile kullanılabilir.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: Tekrarlanabilirlik için random seed. None ise rastgele.
        """
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.rng = random.Random(self.seed)
        self.isim_uretici = IsimUretici(self.rng)
    
    def generate(
        self,
        difficulty: str = "normal",
        yil: int = 2025,
        ay: int = 1,
        num_personel: int = 15
    ) -> Dict[str, Any]:
        """
        Tam bir senaryo üret.
        
        Args:
            difficulty: "easy", "normal", "tight", "nightmare"
            yil: Çizelge yılı
            ay: Çizelge ayı (1-12)
            num_personel: Baz personel sayısı
            
        Returns:
            Senin session_state anahtarlarına uygun dict
        """
        if difficulty not in ZORLUK_PROFILLERI:
            raise ValueError(f"Bilinmeyen zorluk: {difficulty}. "
                           f"Seçenekler: {list(ZORLUK_PROFILLERI.keys())}")
        
        profil = ZORLUK_PROFILLERI[difficulty]
        
        # Personel sayısını zorluğa göre ayarla
        adjusted_count = max(5, int(num_personel * profil["personel_carpani"]))
        
        # Ayın gün sayısı
        _, gun_sayisi = calendar.monthrange(yil, ay)
        
        # Her bileşeni üret
        personel_list = self._uret_personel_list(adjusted_count)
        
        personel_targets = self._uret_personel_targets(
            personel_list, gun_sayisi, profil
        )
        
        weekday_block_map = self._uret_weekday_block_map(
            personel_list, profil
        )
        
        izin_map = self._uret_izin_map(
            personel_list, gun_sayisi, profil
        )
        
        prefer_map = self._uret_prefer_map(
            personel_list, gun_sayisi, izin_map, profil
        )
        
        no_pairs_list, soft_no_pairs_list = self._uret_no_pairs(
            personel_list, profil
        )
        
        manuel_tatiller = self._uret_manuel_tatiller(yil, ay, gun_sayisi)
        
        # Alan ve vardiya modları
        if profil["alan_aktif"]:
            alanlar = self._uret_alanlar_sinirli(len(personel_list), gun_sayisi, profil.get("vardiya_aktif", False))
            personel_alan_yetkinlikleri = self._uret_alan_yetkinlikleri(
                personel_list, alanlar
            )
            alan_modu_aktif = True
            alan_bazli_denklik = self.rng.choice([True, False])
        else:
            alanlar = []
            personel_alan_yetkinlikleri = {}
            alan_modu_aktif = False
            alan_bazli_denklik = False
        
        if profil["vardiya_aktif"]:
            vardiya_tipleri = self._uret_vardiya_tipleri()
            personel_vardiya_kisitlari = self._uret_vardiya_kisitlari(
                personel_list, vardiya_tipleri
            )
        else:
            vardiya_tipleri = []
            personel_vardiya_kisitlari = {}
        
        # Toplam kapasiteyi hesapla
        if alanlar:
            toplam_kontenjan = sum(a.get("kontenjan", 1) for a in alanlar)
        else:
            toplam_kontenjan = 1
        
        if vardiya_tipleri:
            gunluk_slot = toplam_kontenjan * len(vardiya_tipleri)
        else:
            gunluk_slot = toplam_kontenjan
        
        toplam_kapasite = gunluk_slot * gun_sayisi
        
        # Kişi başı ORTALAMA hedef (kapasiteyi tam karşılayacak şekilde)
        kisi_basi_ortalama = toplam_kapasite / len(personel_list)
        
        # Kıdem gruplarını oluştur - toplam hedef kapasiteyi aşmayacak şekilde
        kidem_gruplari, personel_kidem_gruplari = self._uret_kidem_dengeli(
            personel_list, vardiya_tipleri, kisi_basi_ortalama, toplam_kapasite
        )
        
        # Varsayılan hedefi kıdem gruplarından hesapla (max 25 ile sınırla)
        if kidem_gruplari:
            varsayilan_hedef = min(25, int(sum(g.get("varsayilan_hedef", 8) for g in kidem_gruplari) / len(kidem_gruplari)))
        else:
            varsayilan_hedef = min(25, int(kisi_basi_ortalama))
        
        want_pairs_list = self._uret_want_pairs(
            personel_list, no_pairs_list, soft_no_pairs_list, profil,
            personel_targets, varsayilan_hedef
        )
        
        return {
            # === ZORUNLU ANAHTARLAR ===
            "personel_list": personel_list,
            "personel_targets": personel_targets,
            "weekday_block_map": weekday_block_map,
            "varsayilan_hedef": varsayilan_hedef,
            
            # === ÇİFT TERCİHLERİ ===
            "want_pairs_list": want_pairs_list,
            "no_pairs_list": no_pairs_list,
            "soft_no_pairs_list": soft_no_pairs_list,
            
            # === AY'A ÖZEL ===
            "izin_map": izin_map,
            "prefer_map": prefer_map,
            "manuel_tatiller": manuel_tatiller,
            
            # === OPSİYONEL MODLAR ===
            "alanlar": alanlar,
            "alan_modu_aktif": alan_modu_aktif,
            "alan_bazli_denklik": alan_bazli_denklik,
            "personel_alan_yetkinlikleri": personel_alan_yetkinlikleri,
            
            "kidem_gruplari": kidem_gruplari,
            "personel_kidem_gruplari": personel_kidem_gruplari,
            
            "vardiya_tipleri": vardiya_tipleri,
            "personel_vardiya_kisitlari": personel_vardiya_kisitlari,
            
            # === META BİLGİ (app kullanmaz ama debug için) ===
            "_meta": {
                "seed": self.seed,
                "difficulty": difficulty,
                "aciklama": profil["aciklama"],
                "yil": yil,
                "ay": ay,
                "gun_sayisi": gun_sayisi,
            }
        }
    
    # -------------------------------------------------------------------------
    # YARDIMCI ÜRETİCİ METODLAR
    # -------------------------------------------------------------------------
    
    def _uret_personel_list(self, count: int) -> List[str]:
        """Personel isim listesi üret."""
        return [self.isim_uretici.uret() for _ in range(count)]
    
    def _uret_personel_targets(
        self,
        personel_list: List[str],
        gun_sayisi: int,
        profil: dict
    ) -> Dict[str, int]:
        """
        Kişi başı hedef nöbet sayısı (opsiyonel override).
        Çoğu kişi için boş bırakılır (solver default kullanır).
        Sadece bazı kişilere özel hedef verilir.
        """
        targets = {}
        vardiya_modu = profil.get("vardiya_aktif", False)

        # %20 kişiye özel hedef ver
        for personel in personel_list:
            if self.rng.random() < 0.20:
                # Ortalama hedef: ayın günü / personel sayısı civarı
                ortalama = gun_sayisi // max(1, len(personel_list) // 3)
                hedef = self.rng.randint(
                    max(1, ortalama - 2),
                    ortalama + 2
                )
                # Max mümkün ile kırp (izinler henüz belli değil, conservative)
                max_mumkun = kisinin_max_atama(gun_sayisi, vardiya_modu, ardisik_yasak=True)
                hedef = min(hedef, max_mumkun)
                if hedef > 0:
                    targets[personel] = hedef

        return targets
    
    def _uret_weekday_block_map(
        self,
        personel_list: List[str],
        profil: dict
    ) -> Dict[str, List[str]]:
        """
        Kişinin çalışamadığı hafta günleri.
        Örn: {"Ahmet Yılmaz": ["Cts", "Paz"]}
        """
        block_map = {}
        oran = profil["weekday_block_oran"]
        
        for personel in personel_list:
            if self.rng.random() < oran:
                # 1-2 gün blokla
                blok_sayisi = self.rng.randint(1, 2)
                blok_gunler = self.rng.sample(GUN_ADLARI, blok_sayisi)
                block_map[personel] = blok_gunler
        
        return block_map
    
    def _uret_izin_map(
        self,
        personel_list: List[str],
        gun_sayisi: int,
        profil: dict
    ) -> Dict[str, Set[int]]:
        """
        Kişinin izinli olduğu gün numaraları.
        Örn: {"Ahmet Yılmaz": {1, 15, 16}}
        """
        izin_map = {}
        
        for personel in personel_list:
            izin_sayisi = self.rng.randint(
                profil["izin_min"],
                profil["izin_max"]
            )
            
            if izin_sayisi > 0:
                # Ardışık izin bloğu oluşturma şansı (%40)
                if self.rng.random() < 0.4 and izin_sayisi >= 2:
                    # Ardışık blok
                    blok_uzunlugu = min(izin_sayisi, self.rng.randint(2, 4))
                    baslangic = self.rng.randint(1, gun_sayisi - blok_uzunlugu + 1)
                    gunler = set(range(baslangic, baslangic + blok_uzunlugu))
                    
                    # Kalan izinleri rastgele ekle
                    kalan = izin_sayisi - blok_uzunlugu
                    if kalan > 0:
                        mevcut = set(range(1, gun_sayisi + 1)) - gunler
                        ekstra = self.rng.sample(list(mevcut), min(kalan, len(mevcut)))
                        gunler.update(ekstra)
                else:
                    # Tamamen rastgele
                    gunler = set(self.rng.sample(
                        range(1, gun_sayisi + 1),
                        min(izin_sayisi, gun_sayisi)
                    ))
                
                izin_map[personel] = gunler
        
        return izin_map
    
    def _uret_prefer_map(
        self,
        personel_list: List[str],
        gun_sayisi: int,
        izin_map: Dict[str, Set[int]],
        profil: dict
    ) -> Dict[str, Set[int]]:
        """
        Kişinin tercih ettiği günler (çalışmak istediği).
        İzinli günlerle çakışmaz.
        """
        prefer_map = {}
        
        for personel in personel_list:
            izinli_gunler = izin_map.get(personel, set())
            mumkun_gunler = set(range(1, gun_sayisi + 1)) - izinli_gunler
            
            if not mumkun_gunler:
                continue
            
            tercih_sayisi = self.rng.randint(
                profil["prefer_min"],
                profil["prefer_max"]
            )
            
            if tercih_sayisi > 0:
                tercih_gunler = set(self.rng.sample(
                    list(mumkun_gunler),
                    min(tercih_sayisi, len(mumkun_gunler))
                ))
                if tercih_gunler:
                    prefer_map[personel] = tercih_gunler
        
        return prefer_map
    
    def _uret_no_pairs(
        self,
        personel_list: List[str],
        profil: dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Birlikte çalışmaması gereken çiftler.
        no_pairs_list: Kesin yasak
        soft_no_pairs_list: Mümkünse kaçınılsın
        """
        n = len(personel_list)
        toplam_cift = n * (n - 1) // 2
        
        # Hard no-pairs
        no_count = max(0, int(toplam_cift * profil["no_pairs_oran"]))
        no_pairs_list = []
        kullanilan_ciftler = set()
        
        for _ in range(no_count):
            a, b = self.rng.sample(personel_list, 2)
            cift = tuple(sorted([a, b]))
            if cift not in kullanilan_ciftler:
                kullanilan_ciftler.add(cift)
                no_pairs_list.append({"a": a, "b": b})
        
        # Soft no-pairs (hard olanlarla çakışmaz)
        soft_count = max(0, int(toplam_cift * profil["soft_no_pairs_oran"]))
        soft_no_pairs_list = []
        
        for _ in range(soft_count):
            a, b = self.rng.sample(personel_list, 2)
            cift = tuple(sorted([a, b]))
            if cift not in kullanilan_ciftler:
                kullanilan_ciftler.add(cift)
                soft_no_pairs_list.append({"a": a, "b": b})
        
        return no_pairs_list, soft_no_pairs_list
    
    def _uret_want_pairs(
        self,
        personel_list: List[str],
        no_pairs_list: List[Dict],
        soft_no_pairs_list: List[Dict],
        profil: dict,
        personel_targets: Dict[str, int],
        varsayilan_hedef: int
    ) -> List[Dict]:
        """
        Birlikte çalışması istenen çiftler.
        no_pairs ile çakışmaz.
        min değeri her iki kişinin hedefine sığacak şekilde kırpılır.
        """
        # Yasaklı çiftleri set'e çevir
        yasakli = set()
        for p in no_pairs_list + soft_no_pairs_list:
            yasakli.add(tuple(sorted([p["a"], p["b"]])))
        
        want_count = profil["want_pairs_sayi"]
        want_pairs_list = []
        
        for _ in range(want_count):
            for _ in range(20):  # Max deneme
                a, b = self.rng.sample(personel_list, 2)
                cift = tuple(sorted([a, b]))
                if cift not in yasakli:
                    yasakli.add(cift)  # Tekrar seçilmesin
                    hedef_a = personel_targets.get(a, varsayilan_hedef)
                    hedef_b = personel_targets.get(b, varsayilan_hedef)
                    min_k = self.rng.randint(2, 4)
                    min_k = min(min_k, hedef_a, hedef_b)
                    if min_k > 0:
                        want_pairs_list.append({
                            "a": a,
                            "b": b,
                            "min": min_k
                        })
                    break
        
        return want_pairs_list
    
    def _uret_manuel_tatiller(
        self,
        yil: int,
        ay: int,
        gun_sayisi: int
    ) -> str:
        """
        Manuel tatil günleri string formatında.
        Örn: "1, 23" veya ""
        """
        # Ayın ilk günü ve bazı resmi tatil benzerleri
        tatiller = []
        
        # Yılbaşı
        if ay == 1:
            tatiller.append(1)
        
        # 23 Nisan
        if ay == 4:
            tatiller.append(23)
        
        # 19 Mayıs
        if ay == 5:
            tatiller.append(19)
        
        # 30 Ağustos
        if ay == 8:
            tatiller.append(30)
        
        # 29 Ekim
        if ay == 10:
            tatiller.append(29)
        
        # %30 ihtimalle rastgele 1-2 ek tatil
        if self.rng.random() < 0.3:
            mevcut = set(range(1, gun_sayisi + 1)) - set(tatiller)
            ekstra = self.rng.randint(1, 2)
            ek_tatiller = self.rng.sample(list(mevcut), min(ekstra, len(mevcut)))
            tatiller.extend(ek_tatiller)
        
        tatiller.sort()
        return ", ".join(str(g) for g in tatiller)
    
    def _uret_alanlar_sinirli(self, personel_sayisi: int, gun_sayisi: int, vardiya_aktif: bool = False) -> List[Dict]:
        """
        Çalışma alanları üret - personel sayısına göre kapasite sınırlı.
        """
        alan_isimleri = ["Acil", "Yoğun Bakım", "Poliklinik", "Ameliyathane", "Servis"]
        secilen = self.rng.sample(alan_isimleri, self.rng.randint(2, 3))

        # Kişi başı max atama (moda göre)
        if vardiya_aktif:
            kisi_basi_max = gun_sayisi
        else:
            kisi_basi_max = 15  # ardışık yasak nedeniyle yaklaşık ~15

        max_aylik_nobet = personel_sayisi * kisi_basi_max
        max_gunluk_slot = max_aylik_nobet // gun_sayisi
        max_kontenjan_per_vardiya = max(1, max_gunluk_slot // 3)  # 3 vardiya varsayımı
        
        alanlar = []
        toplam_kontenjan = 0
        
        for i, isim in enumerate(secilen):
            # Kalan kapasiteye göre kontenjan belirle
            kalan = max(1, max_kontenjan_per_vardiya - toplam_kontenjan)
            kontenjan = self.rng.randint(1, min(2, kalan))
            toplam_kontenjan += kontenjan
            
            alanlar.append({
                "isim": isim,
                "kontenjan": kontenjan,
                "max_kontenjan": kontenjan + 1 if self.rng.random() < 0.3 else None,
                "renk": RENKLER[i % len(RENKLER)],
                "vardiya_tipleri": []
            })
            
            # Toplam kontenjan sınırına ulaştıysa dur
            if toplam_kontenjan >= max_kontenjan_per_vardiya:
                break
        
        return alanlar
    
    def _uret_alanlar(self) -> List[Dict]:
        """
        Çalışma alanları üret.
        """
        alan_isimleri = ["Acil", "Yoğun Bakım", "Poliklinik", "Ameliyathane", "Servis"]
        secilen = self.rng.sample(alan_isimleri, self.rng.randint(2, 4))
        
        alanlar = []
        for i, isim in enumerate(secilen):
            kontenjan = self.rng.randint(1, 3)
            alanlar.append({
                "isim": isim,
                "kontenjan": kontenjan,
                "max_kontenjan": kontenjan + self.rng.randint(0, 2) if self.rng.random() < 0.5 else None,
                "renk": RENKLER[i % len(RENKLER)],
                "vardiya_tipleri": []  # Boş = tüm vardiyalar geçerli
            })
        
        return alanlar
    
    def _uret_alan_yetkinlikleri(
        self,
        personel_list: List[str],
        alanlar: List[Dict]
    ) -> Dict[str, List[str]]:
        """
        Her personelin hangi alanlarda çalışabileceği.
        """
        alan_isimleri = [a["isim"] for a in alanlar]
        yetkinlikler = {}
        
        for personel in personel_list:
            # Her kişi en az 1, en fazla tüm alanlarda çalışabilir
            kac_alan = self.rng.randint(1, len(alan_isimleri))
            yetkinlikler[personel] = self.rng.sample(alan_isimleri, kac_alan)
        
        return yetkinlikler
    
    def _uret_vardiya_tipleri(self) -> List[Dict]:
        """
        Vardiya tipleri üret.
        """
        return [
            {
                "isim": "Sabah",
                "baslangic": "08:00",
                "bitis": "16:00",
                "renk": "#4CAF50"
            },
            {
                "isim": "Akşam",
                "baslangic": "16:00",
                "bitis": "24:00",
                "renk": "#2196F3"
            },
            {
                "isim": "Gece",
                "baslangic": "00:00",
                "bitis": "08:00",
                "renk": "#9C27B0"
            }
        ]
    
    def _uret_vardiya_kisitlari(
        self,
        personel_list: List[str],
        vardiya_tipleri: List[Dict]
    ) -> Dict[str, List[str]]:
        """
        Personelin yapamayacağı vardiya tipleri.
        Örn: {"Ahmet Yılmaz": ["Gece"]}
        """
        kisitlar = {}
        vardiya_isimleri = [v["isim"] for v in vardiya_tipleri]
        
        # %20 personele vardiya kısıtı
        for personel in personel_list:
            if self.rng.random() < 0.20:
                # Genellikle gece vardiyası kısıtı
                if self.rng.random() < 0.7:
                    kisitlar[personel] = ["Gece"]
                else:
                    kisitlar[personel] = [self.rng.choice(vardiya_isimleri)]
        
        return kisitlar
    
    def _uret_kidem_dengeli(
        self,
        personel_list: List[str],
        vardiya_tipleri: List[Dict],
        kisi_basi_ortalama: float,
        toplam_kapasite: int
    ) -> Tuple[List[Dict], Dict[str, str]]:
        """
        Kıdem grupları - toplam hedef kapasiteyi aşmayacak şekilde dengeli.
        """
        n = len(personel_list)
        
        # Önce personeli kıdem gruplarına ata
        personel_kidem = {}
        for personel in personel_list:
            roll = self.rng.random()
            if roll < 0.20:
                personel_kidem[personel] = "Kıdemli"
            elif roll < 0.70:
                personel_kidem[personel] = "Orta"
            else:
                personel_kidem[personel] = "Yeni"
        
        # Grup başına kişi sayısı
        n_kidemli = sum(1 for k in personel_kidem.values() if k == "Kıdemli")
        n_orta = sum(1 for k in personel_kidem.values() if k == "Orta")
        n_yeni = sum(1 for k in personel_kidem.values() if k == "Yeni")
        
        # Kapasiteyi aşmayan temel hedef
        base_hedef = max(1, toplam_kapasite // n)
        
        kidemli_hedef = max(1, base_hedef - 2)
        orta_hedef = base_hedef
        yeni_hedef = base_hedef + 2
        
        # Hedefleri sınırla (makul aralıkta)
        kidemli_hedef = max(1, min(25, kidemli_hedef))
        orta_hedef = max(1, min(25, orta_hedef))
        yeni_hedef = max(1, min(25, yeni_hedef))
        
        # Toplam hedef fiilen kapasiteyi aşıyor mu kontrol et; aşıyorsa oransal küçült
        toplam_hedef_hesap = n_kidemli * kidemli_hedef + n_orta * orta_hedef + n_yeni * yeni_hedef
        if toplam_hedef_hesap > toplam_kapasite and toplam_kapasite > 0:
            oran = toplam_kapasite / toplam_hedef_hesap
            kidemli_hedef = max(1, int(kidemli_hedef * oran))
            orta_hedef = max(1, int(orta_hedef * oran))
            yeni_hedef = max(1, int(yeni_hedef * oran))
            # Kalan farkı düşür (yuvarlama hatası olabilir)
            while (n_kidemli * kidemli_hedef + n_orta * orta_hedef + n_yeni * yeni_hedef) > toplam_kapasite:
                if yeni_hedef > 1:
                    yeni_hedef -= 1
                elif orta_hedef > 1:
                    orta_hedef -= 1
                elif kidemli_hedef > 1:
                    kidemli_hedef -= 1
                else:
                    break
        
        if vardiya_tipleri and len(vardiya_tipleri) > 0:
            kidem_gruplari = [
                {
                    "isim": "Kıdemli",
                    "renk": "#FFD700",
                    "varsayilan_hedef": kidemli_hedef,
                    "vardiya_hedefleri": self._dagiit_vardiya_hedefleri(vardiya_tipleri, kidemli_hedef)
                },
                {
                    "isim": "Orta",
                    "renk": "#C0C0C0",
                    "varsayilan_hedef": orta_hedef,
                    "vardiya_hedefleri": self._dagiit_vardiya_hedefleri(vardiya_tipleri, orta_hedef)
                },
                {
                    "isim": "Yeni",
                    "renk": "#CD7F32",
                    "varsayilan_hedef": yeni_hedef,
                    "vardiya_hedefleri": self._dagiit_vardiya_hedefleri(vardiya_tipleri, yeni_hedef)
                },
            ]
        else:
            kidem_gruplari = [
                {"isim": "Kıdemli", "renk": "#FFD700", "varsayilan_hedef": kidemli_hedef},
                {"isim": "Orta", "renk": "#C0C0C0", "varsayilan_hedef": orta_hedef},
                {"isim": "Yeni", "renk": "#CD7F32", "varsayilan_hedef": yeni_hedef},
            ]
        
        return kidem_gruplari, personel_kidem
    
    def _uret_kidem_kapasiteli(
        self,
        personel_list: List[str],
        vardiya_tipleri: List[Dict],
        kisi_basi_hedef: int
    ) -> Tuple[List[Dict], Dict[str, str]]:
        """
        Kıdem grupları ve personel atamaları - kapasiteye göre hedefler.
        """
        # Hedefleri kişi başı hedefe göre ayarla
        kidemli_hedef = max(kisi_basi_hedef - 2, 1)
        orta_hedef = kisi_basi_hedef
        yeni_hedef = kisi_basi_hedef + 2
        
        if vardiya_tipleri and len(vardiya_tipleri) > 0:
            kidem_gruplari = [
                {
                    "isim": "Kıdemli",
                    "renk": "#FFD700",
                    "varsayilan_hedef": kidemli_hedef,
                    "vardiya_hedefleri": self._dagiit_vardiya_hedefleri(vardiya_tipleri, kidemli_hedef)
                },
                {
                    "isim": "Orta",
                    "renk": "#C0C0C0",
                    "varsayilan_hedef": orta_hedef,
                    "vardiya_hedefleri": self._dagiit_vardiya_hedefleri(vardiya_tipleri, orta_hedef)
                },
                {
                    "isim": "Yeni",
                    "renk": "#CD7F32",
                    "varsayilan_hedef": yeni_hedef,
                    "vardiya_hedefleri": self._dagiit_vardiya_hedefleri(vardiya_tipleri, yeni_hedef)
                },
            ]
        else:
            kidem_gruplari = [
                {"isim": "Kıdemli", "renk": "#FFD700", "varsayilan_hedef": kidemli_hedef},
                {"isim": "Orta", "renk": "#C0C0C0", "varsayilan_hedef": orta_hedef},
                {"isim": "Yeni", "renk": "#CD7F32", "varsayilan_hedef": yeni_hedef},
            ]
        
        personel_kidem = {}
        
        for personel in personel_list:
            roll = self.rng.random()
            if roll < 0.20:
                personel_kidem[personel] = "Kıdemli"
            elif roll < 0.70:
                personel_kidem[personel] = "Orta"
            else:
                personel_kidem[personel] = "Yeni"
        
        return kidem_gruplari, personel_kidem
    
    def _uret_kidem(
        self,
        personel_list: List[str],
        vardiya_tipleri: List[Dict] = None
    ) -> Tuple[List[Dict], Dict[str, str]]:
        """
        Kıdem grupları ve personel atamaları.
        Vardiya tipleri varsa, vardiya bazlı hedefler de üretir.
        """
        # Temel kıdem grupları
        if vardiya_tipleri and len(vardiya_tipleri) > 0:
            # Vardiya bazlı hedefler
            vardiya_isimleri = [v["isim"] for v in vardiya_tipleri]
            
            # Kıdemliler daha az, yeniler daha çok nöbet
            kidem_gruplari = [
                {
                    "isim": "Kıdemli",
                    "renk": "#FFD700",
                    "varsayilan_hedef": 6,
                    "vardiya_hedefleri": self._dagiit_vardiya_hedefleri(vardiya_tipleri, 6)
                },
                {
                    "isim": "Orta",
                    "renk": "#C0C0C0",
                    "varsayilan_hedef": 8,
                    "vardiya_hedefleri": self._dagiit_vardiya_hedefleri(vardiya_tipleri, 8)
                },
                {
                    "isim": "Yeni",
                    "renk": "#CD7F32",
                    "varsayilan_hedef": 10,
                    "vardiya_hedefleri": self._dagiit_vardiya_hedefleri(vardiya_tipleri, 10)
                },
            ]
        else:
            # Eski mod - sadece toplam hedef
            kidem_gruplari = [
                {"isim": "Kıdemli", "renk": "#FFD700", "varsayilan_hedef": 8},
                {"isim": "Orta", "renk": "#C0C0C0", "varsayilan_hedef": 10},
                {"isim": "Yeni", "renk": "#CD7F32", "varsayilan_hedef": 12},
            ]
        
        personel_kidem = {}
        
        for personel in personel_list:
            # Dağılım: %20 Kıdemli, %50 Orta, %30 Yeni
            roll = self.rng.random()
            if roll < 0.20:
                personel_kidem[personel] = "Kıdemli"
            elif roll < 0.70:
                personel_kidem[personel] = "Orta"
            else:
                personel_kidem[personel] = "Yeni"
        
        return kidem_gruplari, personel_kidem
    
    def _dagiit_vardiya_hedefleri(
        self,
        vardiya_tipleri: List[Dict],
        toplam_hedef: int
    ) -> Dict[str, int]:
        """
        Toplam hedefi vardiyalara dağıtır.
        Uzun vardiyalara (24s, 16s) öncelik verir.
        """
        if not vardiya_tipleri:
            return {}
        
        # Vardiya sürelerini hesapla
        vardiya_sureleri = {}
        for v in vardiya_tipleri:
            baslangic = v.get("baslangic", "08:00")
            bitis = v.get("bitis", "08:00")
            
            b_saat = int(baslangic.split(":")[0])
            s_saat = int(bitis.split(":")[0])
            
            if s_saat <= b_saat:
                sure = (24 - b_saat) + s_saat
            else:
                sure = s_saat - b_saat
            
            vardiya_sureleri[v["isim"]] = sure
        
        # Uzun vardiyaları önceliklendir
        sirali = sorted(vardiya_sureleri.items(), key=lambda x: -x[1])
        
        hedefler = {}
        kalan = toplam_hedef
        
        for i, (vardiya_isim, sure) in enumerate(sirali):
            if i == len(sirali) - 1:
                # Son vardiya - kalanı al
                hedefler[vardiya_isim] = max(0, kalan)
            else:
                # Rastgele dağıt (uzun vardiyalara daha fazla)
                if sure >= 16:
                    min_pay = int(kalan * 0.4)
                    max_pay = int(kalan * 0.8)
                    pay = self.rng.randint(min_pay, max(min_pay, max_pay))
                elif sure >= 12:
                    min_pay = int(kalan * 0.2)
                    max_pay = int(kalan * 0.5)
                    pay = self.rng.randint(min_pay, max(min_pay, max_pay))
                else:
                    pay = self.rng.randint(0, max(0, int(kalan * 0.3)))

                hedefler[vardiya_isim] = min(pay, kalan)
                kalan -= hedefler[vardiya_isim]
        
        return hedefler


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def generate_quick_scenario(
    difficulty: str = "normal",
    seed: Optional[int] = None,
    yil: int = 2025,
    ay: int = 1,
    num_personel: int = 15
) -> Dict[str, Any]:
    """
    Tek satırda senaryo üret.
    
    Örnek:
        data = generate_quick_scenario("tight", seed=42, ay=3)
    """
    gen = ScenarioGenerator(seed=seed)
    return gen.generate(
        difficulty=difficulty,
        yil=yil,
        ay=ay,
        num_personel=num_personel
    )


def save_scenario(data: Dict[str, Any], filepath: str) -> None:
    """
    Senaryoyu JSON dosyasına kaydet.
    Set'ler list'e çevrilir.
    """
    def convert(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=convert)
    print(f"Senaryo kaydedildi: {filepath}")


def load_scenario(filepath: str) -> Dict[str, Any]:
    """
    JSON dosyasından senaryo yükle.
    List'ler tekrar Set'e çevrilir (izin_map, prefer_map için).
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # izin_map ve prefer_map'teki list'leri set'e çevir
    for key in ["izin_map", "prefer_map"]:
        if key in data and isinstance(data[key], dict):
            data[key] = {k: set(v) for k, v in data[key].items()}
    
    return data


def describe_scenario(data: Dict[str, Any]) -> str:
    """
    Senaryo özeti oluştur.
    """
    meta = data.get("_meta", {})
    
    personel_sayisi = len(data.get("personel_list", []))
    
    # İzin istatistikleri
    izin_map = data.get("izin_map", {})
    toplam_izin = sum(len(v) for v in izin_map.values())
    ort_izin = toplam_izin / personel_sayisi if personel_sayisi else 0
    
    # Prefer istatistikleri
    prefer_map = data.get("prefer_map", {})
    toplam_prefer = sum(len(v) for v in prefer_map.values())
    
    lines = [
        "=" * 50,
        "SENARYO ÖZETİ",
        "=" * 50,
        f"Zorluk: {meta.get('difficulty', '?')}",
        f"Açıklama: {meta.get('aciklama', '?')}",
        f"Seed: {meta.get('seed', '?')}",
        f"Dönem: {meta.get('yil', '?')}-{meta.get('ay', '?'):02d}",
        "",
        "--- Personel ---",
        f"Toplam: {personel_sayisi}",
        f"Hedef override: {len(data.get('personel_targets', {}))} kişi",
        f"Hafta günü bloğu: {len(data.get('weekday_block_map', {}))} kişi",
        "",
        "--- Kısıtlar ---",
        f"Toplam izin günü: {toplam_izin} (ort: {ort_izin:.1f}/kişi)",
        f"Tercih edilen gün: {toplam_prefer}",
        f"Kesin ayrı tut: {len(data.get('no_pairs_list', []))} çift",
        f"Esnek ayrı tut: {len(data.get('soft_no_pairs_list', []))} çift",
        f"Birlikte tut: {len(data.get('want_pairs_list', []))} çift",
        "",
        "--- Modlar ---",
        f"Alan modu: {'Aktif' if data.get('alan_modu_aktif') else 'Kapalı'}",
        f"Alanlar: {len(data.get('alanlar', []))}",
        f"Vardiyalar: {len(data.get('vardiya_tipleri', []))}",
        f"Kıdem grupları: {len(data.get('kidem_gruplari', []))}",
    ]
    
    return "\n".join(lines)


# =============================================================================
# HAZIR SENARYOLAR (Spesifik test case'ler için)
# =============================================================================

class HazirSenaryolar:
    """
    Önceden tanımlı test senaryoları.
    """
    
    @staticmethod
    def minimal(seed: int = 100) -> Dict[str, Any]:
        """En küçük çözülebilir senaryo."""
        return generate_quick_scenario("easy", seed=seed, num_personel=5)
    
    @staticmethod
    def hafta_sonu_krizi(seed: int = 200) -> Dict[str, Any]:
        """Herkes hafta sonu izin istiyor."""
        gen = ScenarioGenerator(seed=seed)
        data = gen.generate("tight", num_personel=12)
        
        # Herkese Cts-Paz bloğu ekle
        for personel in data["personel_list"]:
            if personel not in data["weekday_block_map"]:
                data["weekday_block_map"][personel] = []
            bloklanan = data["weekday_block_map"][personel]
            if "Cts" not in bloklanan:
                bloklanan.append("Cts")
            if "Paz" not in bloklanan:
                bloklanan.append("Paz")
        
        data["_meta"]["aciklama"] = "Hafta sonu krizi - herkes Cts/Paz blokladı"
        return data
    
    @staticmethod
    def cift_catismasi(seed: int = 300) -> Dict[str, Any]:
        """Çok fazla uyumsuz çift."""
        gen = ScenarioGenerator(seed=seed)
        data = gen.generate("normal", num_personel=15)
        
        # Extra no_pairs ekle
        personel = data["personel_list"]
        mevcut = {tuple(sorted([p["a"], p["b"]])) for p in data["no_pairs_list"]}
        
        for _ in range(10):
            a, b = gen.rng.sample(personel, 2)
            cift = tuple(sorted([a, b]))
            if cift not in mevcut:
                mevcut.add(cift)
                data["no_pairs_list"].append({"a": a, "b": b})
        
        data["_meta"]["aciklama"] = "Çift çatışması - çok sayıda uyumsuz çift"
        return data
    
    @staticmethod
    def izin_bombardimani(seed: int = 400) -> Dict[str, Any]:
        """Aşırı izin talebi."""
        gen = ScenarioGenerator(seed=seed)
        data = gen.generate("nightmare", num_personel=10)
        
        # Her kişiye 2-3 gün daha izin ekle
        gun_sayisi = data["_meta"]["gun_sayisi"]
        for personel in data["personel_list"]:
            mevcut = data["izin_map"].get(personel, set())
            bos_gunler = set(range(1, gun_sayisi + 1)) - mevcut
            if bos_gunler:
                ekstra = gen.rng.randint(2, 3)
                yeni = set(gen.rng.sample(list(bos_gunler), min(ekstra, len(bos_gunler))))
                data["izin_map"][personel] = mevcut | yeni
        
        data["_meta"]["aciklama"] = "İzin bombardımanı - aşırı izin talebi, muhtemelen çözümsüz"
        return data


# =============================================================================
# DOĞRUDAN ÇALIŞTIRMA
# =============================================================================

if __name__ == "__main__":
    print("🗓️ SENARYO ÜRETİCİ DEMO")
    print("=" * 50)
    
    # Normal senaryo üret
    data = generate_quick_scenario("normal", seed=42, ay=2)
    print(describe_scenario(data))
    
    print("\n" + "=" * 50)
    print("Örnek Personel (ilk 5):")
    for p in data["personel_list"][:5]:
        print(f"  - {p}")
    
    print("\n" + "=" * 50)
    print("Örnek İzinler (ilk 3 kişi):")
    for p, gunler in list(data["izin_map"].items())[:3]:
        print(f"  {p}: {sorted(gunler)}")
