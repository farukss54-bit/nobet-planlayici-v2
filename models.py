"""
Nöbet Planlayıcı - Veri Modelleri

Bu modül uygulamada kullanılan temel veri yapılarını tanımlar.
Dataclass kullanımı sayesinde:
- Tip güvenliği sağlanır
- JSON dönüşümü kolay olur
- Kod okunabilirliği artar
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from datetime import datetime


@dataclass
class VardiyaTipi:
    """
    Bir vardiya tipini temsil eder.
    Örnek: 08-16 Gündüz, 16-08 Gece, 08-08 Tam Gün vs.
    """
    isim: str
    baslangic: str = "08:00"  # "HH:MM" formatında
    bitis: str = "16:00"      # "HH:MM" formatında
    renk: str = "#808080"
    
    @property
    def saat(self) -> int:
        """Vardiya süresini saat olarak hesaplar"""
        try:
            b_saat, b_dk = map(int, self.baslangic.split(":"))
            s_saat, s_dk = map(int, self.bitis.split(":"))

            baslangic_dk = b_saat * 60 + b_dk
            bitis_dk = s_saat * 60 + s_dk

            # Gece geçişi varsa (örn: 16:00 - 08:00)
            if bitis_dk <= baslangic_dk:
                bitis_dk += 24 * 60

            return (bitis_dk - baslangic_dk) // 60
        except (ValueError, AttributeError):
            # Fallback to default 8-hour shift if parsing fails
            return 8
    
    def to_dict(self) -> dict:
        return {
            "isim": self.isim,
            "baslangic": self.baslangic,
            "bitis": self.bitis,
            "renk": self.renk
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "VardiyaTipi":
        return cls(
            isim=data["isim"],
            baslangic=data.get("baslangic", "08:00"),
            bitis=data.get("bitis", "16:00"),
            renk=data.get("renk", "#808080")
        )


# Hazır vardiya şablonları
HAZIR_VARDIYALAR = [
    VardiyaTipi("Gündüz 8s", "08:00", "16:00", "#FFA500"),
    VardiyaTipi("Akşam 8s", "16:00", "24:00", "#9C27B0"),
    VardiyaTipi("Gece 8s", "00:00", "08:00", "#3F51B5"),
    VardiyaTipi("Tam Gün 24s", "08:00", "08:00", "#4CAF50"),
    VardiyaTipi("Uzun Gece 16s", "16:00", "08:00", "#607D8B"),
    VardiyaTipi("Uzun Gündüz 12s", "08:00", "20:00", "#FF9800"),
    VardiyaTipi("Gece 12s", "20:00", "08:00", "#673AB7"),
]


@dataclass
class KidemGrubu:
    """
    Kullanıcı tanımlı kıdem/seviye grubu.
    Örnek: Asistan, Uzman, Profesör veya Junior, Senior vs.
    
    Vardiya hedefleri: {"24s": 8, "16s": 1} gibi
    Eğer vardiya_hedefleri boşsa, varsayilan_hedef kullanılır (eski mod uyumu)
    """
    isim: str
    renk: str = "#808080"
    varsayilan_hedef: int = None  # Vardiya yoksa veya tanımlı değilse kullanılır
    vardiya_hedefleri: Dict[str, int] = field(default_factory=dict)  # {"Tam Gün 24s": 8, "Uzun Gece 16s": 1}
    
    def toplam_nobet(self) -> int:
        """Toplam nöbet sayısı"""
        if self.vardiya_hedefleri:
            return sum(self.vardiya_hedefleri.values())
        return self.varsayilan_hedef or 0
    
    def toplam_saat(self, vardiya_saatleri: Dict[str, int]) -> int:
        """Toplam çalışma saati"""
        if self.vardiya_hedefleri:
            return sum(
                sayi * vardiya_saatleri.get(vardiya, 24)
                for vardiya, sayi in self.vardiya_hedefleri.items()
            )
        return (self.varsayilan_hedef or 0) * 24
    
    def to_dict(self) -> dict:
        return {
            "isim": self.isim,
            "renk": self.renk,
            "varsayilan_hedef": self.varsayilan_hedef,
            "vardiya_hedefleri": self.vardiya_hedefleri
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "KidemGrubu":
        return cls(
            isim=data["isim"],
            renk=data.get("renk", "#808080"),
            varsayilan_hedef=data.get("varsayilan_hedef"),
            vardiya_hedefleri=data.get("vardiya_hedefleri", {})
        )


@dataclass
class Alan:
    """
    Bir çalışma alanını/lokasyonu temsil eder.
    Örnek: Yeşil Alan, Sarı Alan, Kırmızı Alan, Resüsitasyon, Travma vs.
    """
    isim: str
    gunluk_kontenjan: int = 1  # Bu alana günde kaç kişi atanmalı (hedef/minimum) - vardiya başına
    max_kontenjan: int = None  # Maksimum kişi sayısı (None = sınırsız) - vardiya başına
    renk: str = "#808080"      # UI'da gösterim için (hex renk kodu)
    aktif: bool = True         # Devre dışı bırakılabilir
    
    # Aşama 2: Kıdem kuralları - her gruptan günde min/max kaç kişi
    kidem_kurallari: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Aşama 3: Bu alanda geçerli vardiya tipleri (boş = tüm vardiyalar)
    vardiya_tipleri: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "isim": self.isim,
            "gunluk_kontenjan": self.gunluk_kontenjan,
            "max_kontenjan": self.max_kontenjan,
            "renk": self.renk,
            "aktif": self.aktif,
            "kidem_kurallari": self.kidem_kurallari,
            "vardiya_tipleri": self.vardiya_tipleri
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Alan":
        return cls(
            isim=data["isim"],
            gunluk_kontenjan=data.get("gunluk_kontenjan", 1),
            max_kontenjan=data.get("max_kontenjan"),
            renk=data.get("renk", "#808080"),
            aktif=data.get("aktif", True),
            kidem_kurallari=data.get("kidem_kurallari", {}),
            vardiya_tipleri=data.get("vardiya_tipleri", [])
        )


@dataclass
class Personel:
    """Tek bir personeli temsil eder"""
    isim: str
    hedef_nobet: Optional[int] = None  # None ise varsayılan kullanılır (nöbet sayısı)
    hedef_saat: Optional[int] = None   # None ise hedef_nobet * ortalama vardiya saati
    bloklu_gunler: List[str] = field(default_factory=list)  # ["Pazartesi", "Cuma"]
    
    # Aşama 1: Alan yetkinlikleri
    calisabilir_alanlar: List[str] = field(default_factory=list)  # Boşsa tüm alanlarda çalışabilir
    alan_hedefleri: Dict[str, int] = field(default_factory=dict)  # {"Kırmızı": 2, "Yeşil": 5}
    
    # Aşama 2: Kıdem grubu
    kidem_grubu: Optional[str] = None  # None ise atanmamış
    
    # Aşama 3: Vardiya kısıtları (boş = tüm vardiyalarda çalışabilir)
    calisabilir_vardiyalar: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "isim": self.isim,
            "hedef_nobet": self.hedef_nobet,
            "hedef_saat": self.hedef_saat,
            "bloklu_gunler": self.bloklu_gunler,
            "calisabilir_alanlar": self.calisabilir_alanlar,
            "alan_hedefleri": self.alan_hedefleri,
            "kidem_grubu": self.kidem_grubu,
            "calisabilir_vardiyalar": self.calisabilir_vardiyalar
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Personel":
        return cls(
            isim=data["isim"],
            hedef_nobet=data.get("hedef_nobet"),
            hedef_saat=data.get("hedef_saat"),
            bloklu_gunler=data.get("bloklu_gunler", []),
            calisabilir_alanlar=data.get("calisabilir_alanlar", []),
            alan_hedefleri=data.get("alan_hedefleri", {}),
            kidem_grubu=data.get("kidem_grubu"),
            calisabilir_vardiyalar=data.get("calisabilir_vardiyalar", [])
        )


@dataclass
class EslesmeTercihi:
    """İki personel arasındaki eşleşme tercihi"""
    personel_a: str
    personel_b: str
    min_birlikte: int = 0  # 0 ise sadece "birlikte olmasın" anlamına gelir
    zorunlu: bool = True   # False ise soft constraint
    
    def to_dict(self) -> dict:
        return {
            "personel_a": self.personel_a,
            "personel_b": self.personel_b,
            "min_birlikte": self.min_birlikte,
            "zorunlu": self.zorunlu
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EslesmeTercihi":
        return cls(
            personel_a=data["personel_a"],
            personel_b=data["personel_b"],
            min_birlikte=data.get("min_birlikte", 0),
            zorunlu=data.get("zorunlu", True)
        )


@dataclass
class Ayarlar:
    """
    Uygulamanın kalıcı ayarları - aydan aya değişmeyen şeyler.
    Bu dosya kaydedilir ve her açılışta yüklenir.
    """
    personeller: List[Personel] = field(default_factory=list)
    varsayilan_hedef: int = 7
    
    # Aşama 1: Alanlar
    alanlar: List[Alan] = field(default_factory=list)
    alan_bazli_denklik: bool = True  # Aynı kişi her alandan benzer sayıda tutsun
    
    # Aşama 2: Kıdem grupları
    kidem_gruplari: List[KidemGrubu] = field(default_factory=list)
    
    # Aşama 3: Vardiya tipleri
    vardiya_tipleri: List[VardiyaTipi] = field(default_factory=list)
    saat_bazli_denge: bool = True  # Toplam saat dengesi önemli mi
    
    # Eşleşme tercihleri
    birlikte_tutma: List[EslesmeTercihi] = field(default_factory=list)  # want_pairs
    ayri_tutma: List[EslesmeTercihi] = field(default_factory=list)      # no_pairs  
    esnek_ayri_tutma: List[EslesmeTercihi] = field(default_factory=list)  # soft_no_pairs
    
    # === KURAL AYARLARI ===
    # Hard constraints
    ardisik_yasak: bool = True
    gunasiri_limit_aktif: bool = True
    max_gunasiri: int = 1
    enforce_minimum_staffing: bool = True  # Minimum staffing is hard constraint if True

    # Soft constraints - hafta sonu
    hafta_sonu_dengesi: bool = True
    w_cuma: int = 1000
    w_cumartesi: int = 1000
    w_pazar: int = 1000
    
    # Soft constraints - tatil
    tatil_dengesi: bool = True
    
    # Soft constraints - boşluk tercihi
    iki_gun_bosluk_aktif: bool = True
    iki_gun_bosluk_tercihi: int = 300
    
    def to_dict(self) -> dict:
        return {
            "personeller": [p.to_dict() for p in self.personeller],
            "varsayilan_hedef": self.varsayilan_hedef,
            "alanlar": [a.to_dict() for a in self.alanlar],
            "alan_bazli_denklik": self.alan_bazli_denklik,
            "kidem_gruplari": [k.to_dict() for k in self.kidem_gruplari],
            "vardiya_tipleri": [v.to_dict() for v in self.vardiya_tipleri],
            "saat_bazli_denge": self.saat_bazli_denge,
            "birlikte_tutma": [e.to_dict() for e in self.birlikte_tutma],
            "ayri_tutma": [e.to_dict() for e in self.ayri_tutma],
            "esnek_ayri_tutma": [e.to_dict() for e in self.esnek_ayri_tutma],
            # Kural ayarları
            "ardisik_yasak": self.ardisik_yasak,
            "gunasiri_limit_aktif": self.gunasiri_limit_aktif,
            "max_gunasiri": self.max_gunasiri,
            "enforce_minimum_staffing": self.enforce_minimum_staffing,
            "hafta_sonu_dengesi": self.hafta_sonu_dengesi,
            "w_cuma": self.w_cuma,
            "w_cumartesi": self.w_cumartesi,
            "w_pazar": self.w_pazar,
            "tatil_dengesi": self.tatil_dengesi,
            "iki_gun_bosluk_aktif": self.iki_gun_bosluk_aktif,
            "iki_gun_bosluk_tercihi": self.iki_gun_bosluk_tercihi
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Ayarlar":
        return cls(
            personeller=[Personel.from_dict(p) for p in data.get("personeller", [])],
            varsayilan_hedef=data.get("varsayilan_hedef", 7),
            alanlar=[Alan.from_dict(a) for a in data.get("alanlar", [])],
            alan_bazli_denklik=data.get("alan_bazli_denklik", True),
            kidem_gruplari=[KidemGrubu.from_dict(k) for k in data.get("kidem_gruplari", [])],
            vardiya_tipleri=[VardiyaTipi.from_dict(v) for v in data.get("vardiya_tipleri", [])],
            saat_bazli_denge=data.get("saat_bazli_denge", True),
            birlikte_tutma=[EslesmeTercihi.from_dict(e) for e in data.get("birlikte_tutma", [])],
            ayri_tutma=[EslesmeTercihi.from_dict(e) for e in data.get("ayri_tutma", [])],
            esnek_ayri_tutma=[EslesmeTercihi.from_dict(e) for e in data.get("esnek_ayri_tutma", [])],
            # Kural ayarları
            ardisik_yasak=data.get("ardisik_yasak", True),
            gunasiri_limit_aktif=data.get("gunasiri_limit_aktif", True),
            max_gunasiri=data.get("max_gunasiri", 1),
            enforce_minimum_staffing=data.get("enforce_minimum_staffing", True),
            hafta_sonu_dengesi=data.get("hafta_sonu_dengesi", True),
            w_cuma=data.get("w_cuma", 1000),
            w_cumartesi=data.get("w_cumartesi", 1000),
            w_pazar=data.get("w_pazar", 1000),
            tatil_dengesi=data.get("tatil_dengesi", True),
            iki_gun_bosluk_aktif=data.get("iki_gun_bosluk_aktif", True),
            iki_gun_bosluk_tercihi=data.get("iki_gun_bosluk_tercihi", 300)
        )
    
    def personel_isimleri(self) -> List[str]:
        """Personel isimlerinin listesini döndürür"""
        return [p.isim for p in self.personeller]
    
    def kidem_grubu_isimleri(self) -> List[str]:
        """Kıdem grubu isimlerinin listesini döndürür"""
        return [k.isim for k in self.kidem_gruplari]
    
    def vardiya_isimleri(self) -> List[str]:
        """Vardiya tipi isimlerinin listesini döndürür"""
        return [v.isim for v in self.vardiya_tipleri]
    
    def alan_isimleri(self) -> List[str]:
        """Aktif alan isimlerinin listesini döndürür"""
        return [a.isim for a in self.alanlar if a.aktif]
    
    def toplam_gunluk_kontenjan(self) -> int:
        """Tüm alanların günlük toplam kontenjanı"""
        return sum(a.gunluk_kontenjan for a in self.alanlar if a.aktif)


@dataclass 
class AylikPlan:
    """
    Bir aya ait tüm veriler - izinler, tercihler ve sonuç.
    Her ay için ayrı dosya olarak kaydedilir.
    """
    yil: int
    ay: int
    
    # Ay'a özel girdiler
    izinler: Dict[str, List[int]] = field(default_factory=dict)  # {"Dr. A": [5, 6, 7]}
    tercih_edilen_gunler: Dict[str, List[int]] = field(default_factory=dict)
    manuel_tatiller: List[int] = field(default_factory=list)
    
    # Kişi bazlı hedef override (ay'a özel)
    hedef_override: Dict[str, int] = field(default_factory=dict)
    
    # Sonuç - iki format destekleniyor:
    # Eski format (tek alan): {1: ["Dr. A", "Dr. B"], 2: [...]}
    # Yeni format (çoklu alan): {1: {"Yeşil": ["Dr. A"], "Kırmızı": ["Dr. B"]}, ...}
    sonuc: Optional[Dict] = None
    sonuc_alanlı: bool = False  # True ise yeni format kullanılıyor
    
    olusturma_tarihi: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "yil": self.yil,
            "ay": self.ay,
            "izinler": self.izinler,
            "tercih_edilen_gunler": self.tercih_edilen_gunler,
            "manuel_tatiller": self.manuel_tatiller,
            "hedef_override": self.hedef_override,
            "sonuc": self.sonuc,
            "sonuc_alanlı": self.sonuc_alanlı,
            "olusturma_tarihi": self.olusturma_tarihi
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AylikPlan":
        return cls(
            yil=data["yil"],
            ay=data["ay"],
            izinler=data.get("izinler", {}),
            tercih_edilen_gunler=data.get("tercih_edilen_gunler", {}),
            manuel_tatiller=data.get("manuel_tatiller", []),
            hedef_override=data.get("hedef_override", {}),
            sonuc=data.get("sonuc"),
            sonuc_alanlı=data.get("sonuc_alanlı", False),
            olusturma_tarihi=data.get("olusturma_tarihi")
        )
    
    @property
    def dosya_adi(self) -> str:
        """Bu plan için dosya adını döndürür"""
        return f"{self.yil}_{self.ay:02d}.json"
