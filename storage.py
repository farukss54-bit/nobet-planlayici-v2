"""
Nöbet Planlayıcı - Veri Saklama

Ayarları ve aylık planları JSON dosyalarına kaydeder/yükler.
"""

import json
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from models import Ayarlar, AylikPlan


# Varsayılan veri dizini
DATA_DIR = Path(__file__).parent / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
SCHEDULES_DIR = DATA_DIR / "schedules"


def veri_dizinini_hazirla():
    """Gerekli dizinleri oluşturur"""
    DATA_DIR.mkdir(exist_ok=True)
    SCHEDULES_DIR.mkdir(exist_ok=True)


def ayarlari_kaydet(ayarlar: Ayarlar) -> bool:
    """
    Ayarları JSON dosyasına kaydeder.
    
    Args:
        ayarlar: Kaydedilecek Ayarlar nesnesi
        
    Returns:
        Başarılı ise True
    """
    try:
        veri_dizinini_hazirla()
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(ayarlar.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ayarlar kaydedilemedi: {e}")
        return False


def ayarlari_yukle() -> Optional[Ayarlar]:
    """
    Kaydedilmiş ayarları yükler.
    
    Returns:
        Ayarlar nesnesi veya dosya yoksa None
    """
    try:
        if not SETTINGS_FILE.exists():
            return None
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Ayarlar.from_dict(data)
    except Exception as e:
        print(f"Ayarlar yüklenemedi: {e}")
        return None


def ayarlari_yukle_veya_varsayilan() -> Ayarlar:
    """Ayarları yükler, yoksa varsayılan döndürür"""
    ayarlar = ayarlari_yukle()
    if ayarlar is None:
        ayarlar = Ayarlar()
    return ayarlar


def aylik_plani_kaydet(plan: AylikPlan) -> bool:
    """
    Aylık planı JSON dosyasına kaydeder.
    
    Args:
        plan: Kaydedilecek AylikPlan nesnesi
        
    Returns:
        Başarılı ise True
    """
    try:
        veri_dizinini_hazirla()
        dosya_yolu = SCHEDULES_DIR / plan.dosya_adi
        
        # Kaydetmeden önce tarihi güncelle
        if plan.sonuc is not None and plan.olusturma_tarihi is None:
            plan.olusturma_tarihi = datetime.now().isoformat()
        
        with open(dosya_yolu, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Plan kaydedilemedi: {e}")
        return False


def aylik_plani_yukle(yil: int, ay: int) -> Optional[AylikPlan]:
    """
    Belirli bir ay için kaydedilmiş planı yükler.
    
    Args:
        yil: Yıl
        ay: Ay
        
    Returns:
        AylikPlan nesnesi veya dosya yoksa None
    """
    try:
        dosya_adi = f"{yil}_{ay:02d}.json"
        dosya_yolu = SCHEDULES_DIR / dosya_adi
        
        if not dosya_yolu.exists():
            return None
            
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return AylikPlan.from_dict(data)
    except Exception as e:
        print(f"Plan yüklenemedi: {e}")
        return None


def aylik_plani_yukle_veya_yeni(yil: int, ay: int) -> AylikPlan:
    """Planı yükler, yoksa yeni oluşturur"""
    plan = aylik_plani_yukle(yil, ay)
    if plan is None:
        plan = AylikPlan(yil=yil, ay=ay)
    return plan


def kayitli_planlari_listele() -> List[dict]:
    """
    Kaydedilmiş tüm planların listesini döndürür.
    
    Returns:
        [{"yil": 2025, "ay": 1, "dosya": "2025_01.json", "tarih": "..."}, ...]
    """
    try:
        veri_dizinini_hazirla()
        planlar = []
        
        for dosya in SCHEDULES_DIR.glob("*.json"):
            try:
                with open(dosya, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                planlar.append({
                    "yil": data.get("yil"),
                    "ay": data.get("ay"),
                    "dosya": dosya.name,
                    "olusturma_tarihi": data.get("olusturma_tarihi"),
                    "sonuc_var": data.get("sonuc") is not None
                })
            except Exception:
                continue
        
        # Tarihe göre sırala (en yeni önce)
        planlar.sort(key=lambda x: (x["yil"], x["ay"]), reverse=True)
        return planlar
    except Exception as e:
        print(f"Plan listesi alınamadı: {e}")
        return []


def plani_sil(yil: int, ay: int) -> bool:
    """
    Belirli bir ayın planını siler.
    
    Args:
        yil: Yıl
        ay: Ay
        
    Returns:
        Başarılı ise True
    """
    try:
        dosya_adi = f"{yil}_{ay:02d}.json"
        dosya_yolu = SCHEDULES_DIR / dosya_adi
        
        if dosya_yolu.exists():
            dosya_yolu.unlink()
            return True
        return False
    except Exception as e:
        print(f"Plan silinemedi: {e}")
        return False


def ayarlari_json_olarak_export(ayarlar: Ayarlar) -> str:
    """Ayarları JSON string olarak döndürür (indirme için)"""
    return json.dumps(ayarlar.to_dict(), ensure_ascii=False, indent=2)


def ayarlari_json_dan_import(json_str: str) -> Optional[Ayarlar]:
    """JSON string'den ayarları yükler (yükleme için)"""
    try:
        data = json.loads(json_str)
        return Ayarlar.from_dict(data)
    except Exception as e:
        print(f"JSON import hatası: {e}")
        return None


def plani_json_olarak_export(plan: AylikPlan) -> str:
    """Planı JSON string olarak döndürür"""
    return json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)


def plani_json_dan_import(json_str: str) -> Optional[AylikPlan]:
    """JSON string'den planı yükler"""
    try:
        data = json.loads(json_str)
        return AylikPlan.from_dict(data)
    except Exception as e:
        print(f"JSON import hatası: {e}")
        return None
