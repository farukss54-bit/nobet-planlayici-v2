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


def personel_referanslarini_temizle(session_state, eski_isim: str, yeni_isim: str = None):
    """
    Personel ismi değiştiğinde veya silindiğinde session state'teki
    ilişkili dict'leri günceller.

    Args:
        session_state: Streamlit session state veya benzeri dict
        eski_isim: Eski personel ismi
        yeni_isim: Yeni personel ismi (None ise silme işlemi)
    """
    # Key bazlı dict'ler (key = personel ismi)
    key_dictler = [
        "personel_targets", "weekday_block_map", "izin_map",
        "prefer_map", "personel_alan_yetkinlikleri",
        "personel_kidem_gruplari", "personel_vardiya_kisitlari"
    ]

    for dict_key in key_dictler:
        d = session_state.get(dict_key)
        if not isinstance(d, dict):
            continue
        if eski_isim not in d:
            continue
        if yeni_isim is None:
            d.pop(eski_isim, None)
        else:
            d[yeni_isim] = d.pop(eski_isim)

    # Value bazlı list/dict'ler (eşleşme tercihleri)
    eslesme_listeleri = ["want_pairs_list", "no_pairs_list", "soft_no_pairs_list"]

    for list_key in eslesme_listeleri:
        lst = session_state.get(list_key)
        if not isinstance(lst, list):
            continue

        for item in lst:
            if not isinstance(item, dict):
                continue
            if item.get("a") == eski_isim:
                item["a"] = yeni_isim
            if item.get("b") == eski_isim:
                item["b"] = yeni_isim

        # Silme durumunda None olanları temizle
        if yeni_isim is None:
            session_state[list_key] = [
                item for item in lst
                if item.get("a") is not None and item.get("b") is not None
            ]


def yetim_personel_temizligi_yap(session_state, personel_listesi: list):
    """
    Mevcut personel listesinde olmayan isimleri tüm dict'lerden temizler.

    Args:
        session_state: Streamlit session state veya benzeri dict
        personel_listesi: Geçerli personel isimleri listesi
    """
    mevcut_isimler = set(personel_listesi)

    # Key bazlı dict'ler
    key_dictler = [
        "personel_targets", "weekday_block_map", "izin_map",
        "prefer_map", "personel_alan_yetkinlikleri",
        "personel_kidem_gruplari", "personel_vardiya_kisitlari"
    ]

    for dict_key in key_dictler:
        d = session_state.get(dict_key)
        if not isinstance(d, dict):
            continue
        for isim in list(d.keys()):
            if isim not in mevcut_isimler:
                d.pop(isim, None)

    # Value bazlı eşleşme listeleri
    eslesme_listeleri = ["want_pairs_list", "no_pairs_list", "soft_no_pairs_list"]

    for list_key in eslesme_listeleri:
        lst = session_state.get(list_key)
        if not isinstance(lst, list):
            continue
        session_state[list_key] = [
            item for item in lst
            if item.get("a") in mevcut_isimler and item.get("b") in mevcut_isimler
        ]


def hesapla_otomatik_hedef(
    gun_sayisi: int,
    alanlar: list,
    vardiyalar: list,
    personeller: list,
    izin_map: dict,
    ardisik_yasak: bool = True
) -> dict:
    """
    Toplam nöbet ihtiyacını müsait personel sayısına bölerek
    herkes eşit paylaşsa düşecek nöbet sayısını hesaplar.

    Args:
        gun_sayisi: Ayın gün sayısı
        alanlar: Alan tanımları listesi (dict listesi)
        vardiyalar: Vardiya tipi listesi (dict listesi)
        personeller: Personel isimleri listesi
        izin_map: {isim: [izinli_gunler]} formatında izinler
        ardisik_yasak: Ardışık gün yasağı var mı

    Returns:
        {isim: hedef_nobet} formatında dictionary
    """
    if not personeller:
        return {}

    # Toplam slot = gün × alan_kontenjan × vardiya_sayisi
    if alanlar:
        alan_kontenjan = sum(a.get("kontenjan", 1) for a in alanlar)
    else:
        alan_kontenjan = 1

    vardiya_sayisi = len(vardiyalar) if vardiyalar else 1
    toplam_slot = gun_sayisi * alan_kontenjan * vardiya_sayisi

    # Kişi başı düşen nöbet (yuvarla)
    kisi_basi = max(1, round(toplam_slot / len(personeller)))

    sonuc = {}
    for p in personeller:
        izin_gun = len(izin_map.get(p, []))
        musait_gun = max(0, gun_sayisi - izin_gun)

        if ardisik_yasak:
            max_mumkun = (musait_gun + 1) // 2
        else:
            max_mumkun = musait_gun

        # İzinli kişi hiç müsait değilse 0 ver
        if max_mumkun <= 0:
            sonuc[p] = 0
        else:
            sonuc[p] = min(kisi_basi, max_mumkun)

    return sonuc
