"""
Nöbet Planlayıcı - Merkezi Konfigürasyon

Bu dosya, solver'ın soft/hard constraint ağırlıklarını ve
temel solver parametrelerini merkezi olarak tutar.
Değerleri değiştirip uygulamayı yeniden başlatabilirsiniz.
"""

# =============================================================================
# SOLVER PERFORMANS PARAMETRELERİ
# =============================================================================

# CP-SAT çözücünün maksimum çalışma süresi (saniye)
# Daha karmaşık problemlerde artırılabilir
max_sure_saniye = 60.0

# Paralel arama işçi sayısı (CPU çekirdek sayısına göre ayarlanabilir)
thread_sayisi = 8

# =============================================================================
# HARD CONSTRAINT SABİTLERİ (Limit ve eşik değerler)
# =============================================================================

# Kişi başına aylık maksimum günaşırı nöbet sayısı
# Günaşırı = 1 gün arayla nöbet (örn: Pazartesi ve Çarşamba)
max_gunasiri_per_kisi = 1

# =============================================================================
# SOFT CONSTRAINT AĞIRLIKLARI (Penalty / Reward)
# =============================================================================
# Yüksek değer = daha katı denge, düşük değer = daha gevşek denge
# Ağırlıkların göreceli büyüklüğü önemlidir, mutlak değeri değil

# --- Minimum Staffing ---
# Boş vardiyaya uygulanan ceza (çok yüksek tutulmalı)
w_vardiya_min_kontenjan = 50000

# --- Alan & Kontenjan Dengesi ---
# Alan hedef kontenjanından sapma cezası
w_alan_kontenjan_sapma = 10000
# Günlük nöbet sayısı dengesizliği cezası
w_gunluk_denge = 5000
# Her personelin farklı alanlarda benzer sayıda nöbet tutması cezası
w_alan_denklik = 800

# --- Saat Dengesi ---
# Toplam çalışma saati dengesizliği cezası
w_saat_denge = 3000

# --- Hafta Sonu & Tatil Dengesi ---
# Cuma nöbetlerinin adil dağıtımı cezası
w_cuma = 1000
# Cumartesi nöbetlerinin adil dağıtımı cezası
w_cumartesi = 1000
# Pazar nöbetlerinin adil dağıtımı cezası
w_pazar = 1000
# Resmi tatil nöbetlerinin adil dağıtımı cezası
w_tatil = 200

# --- Boşluk & Ardışık Tercihler ---
# 1 gün arayla iki nöbet (günaşırı) durumunda uygulanan ceza
# NOT: Bu bir SOFT constraint; hard limiti max_gunasiri_per_kisi kontrol eder
w_iki_gun_bosluk = 300

# --- Eşleşme Kuralları ---
# Birlikte çalışması istenen çiftler için ödül ağırlığı (negatif ceza = ödül)
w_birlikte_odul = 30
# Esnek ayrı tutma kuralı ihlali cezası
w_esnek_ayri = 800
# Personelin tercih ettiği günde nöbet tutması ödül ağırlığı
w_tercih = 2
