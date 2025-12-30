"""
Nöbet Planlayıcı - Yardımcı Fonksiyonlar

Tarih hesaplamaları, metin parse işlemleri ve diğer utility fonksiyonlar.
"""

from datetime import datetime
from typing import Set, Dict, List
import holidays


def ay_gun_sayisi(yil: int, ay: int) -> int:
    """Verilen ay için gün sayısını hesaplar"""
    if ay == 12:
        return (datetime(yil + 1, 1, 1) - datetime(yil, 12, 1)).days
    return (datetime(yil, ay + 1, 1) - datetime(yil, ay, 1)).days


def gun_parse(text: str, max_gun: int) -> Set[int]:
    """
    Gün numaralarını parse eder.
    
    Desteklenen formatlar:
    - Tekil: "1, 5, 12"
    - Aralık: "1-5, 12"
    - Karışık: "1-3, 7, 15-20"
    
    Args:
        text: Parse edilecek metin
        max_gun: Ayın maksimum gün sayısı
        
    Returns:
        Gün numaraları seti
    """
    if not text or not text.strip():
        return set()
    
    sonuc = set()
    parcalar = [p.strip() for p in text.split(',') if p.strip()]
    
    for parca in parcalar:
        if '-' in parca:
            try:
                baslangic, bitis = parca.split('-', 1)
                baslangic = int(baslangic.strip())
                bitis = int(bitis.strip())
                if baslangic > bitis:
                    baslangic, bitis = bitis, baslangic
                for gun in range(baslangic, bitis + 1):
                    if 1 <= gun <= max_gun:
                        sonuc.add(gun)
            except ValueError:
                pass
        else:
            try:
                gun = int(parca)
                if 1 <= gun <= max_gun:
                    sonuc.add(gun)
            except ValueError:
                pass
    
    return sonuc


def resmi_tatiller(yil: int, ay: int) -> Dict[int, str]:
    """
    Türkiye'deki resmi tatilleri döndürür.
    
    Args:
        yil: Yıl
        ay: Ay
        
    Returns:
        {gün: tatil_adı} formatında dictionary
    """
    try:
        tr_holidays = holidays.Turkey(years=yil)
        return {
            tarih.day: isim 
            for tarih, isim in tr_holidays.items() 
            if tarih.month == ay
        }
    except Exception:
        return {}


def hafta_gunu(yil: int, ay: int, gun: int) -> int:
    """
    Verilen tarihin haftanın kaçıncı günü olduğunu döndürür.
    0 = Pazartesi, 6 = Pazar
    """
    return datetime(yil, ay, gun).weekday()


def hafta_gunu_adi(weekday: int) -> str:
    """Hafta günü numarasından Türkçe isim döndürür"""
    gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    return gunler[weekday]


def hafta_gunu_numarasi(gun_adi: str) -> int:
    """Türkçe gün adından numara döndürür"""
    gunler = {
        "Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3,
        "Cuma": 4, "Cumartesi": 5, "Pazar": 6
    }
    return gunler.get(gun_adi, -1)


def gunleri_weekday_ile_filtrele(yil: int, ay: int, weekday: int) -> List[int]:
    """Belirli bir hafta gününe denk gelen tüm günleri döndürür"""
    gun_sayisi = ay_gun_sayisi(yil, ay)
    return [
        gun for gun in range(1, gun_sayisi + 1)
        if hafta_gunu(yil, ay, gun) == weekday
    ]


def tum_hafta_gunleri() -> List[str]:
    """Tüm hafta günlerinin listesini döndürür"""
    return ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def tarih_formatla(yil: int, ay: int, gun: int) -> str:
    """Tarihi DD/MM/YYYY formatında döndürür"""
    return f"{gun:02d}/{ay:02d}/{yil}"
