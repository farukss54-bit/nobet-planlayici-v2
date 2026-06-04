# AGENTS.md — Nöbet Planlayıcı v2

> Bu dosya, projeye yeni başlayan AI kodlama ajanları için hazırlanmıştır. Proje hakkında ön bilgi olmadan çalışabilmeniz için gerekli tüm bağlam burada özetlenmiştir.

---

## Proje Genel Bakış

**Nöbet Planlayıcı v2**, hastane acil servisleri için aylık nöbet çizelgesi oluşturan bir Python web uygulamasıdır. Google OR-Tools CP-SAT çözücüsü kullanarak personel kısıtlarını, izinleri, birlikte/ayrı tutma kurallarını ve vardiya dengelemeyi optimize eder.

Uygulamanın ana işlevleri:
- Personel, kıdem grubu, çalışma alanı ve vardiya tipi tanımlama
- İzin, tercih ve hafta günü bloklama girme
- Birlikte/ayrı tutma çift kısıtları
- Aylık nöbet çizelgesi üretme (optimizasyon)
- Excel ve CSV olarak dışa aktarma

---

## Teknoloji Yığını (Technology Stack)

| Bileşen | Kullanım Alanı |
|---------|----------------|
| Python 3.10+ | Ana dil |
| Streamlit >= 1.28.0 | Web tabanlı kullanıcı arayüzü |
| pandas >= 2.0.0 | Tablo işlemleri, CSV dönüşümü |
| openpyxl >= 3.1.0 | Excel (.xlsx) dışa aktarımı |
| ortools >= 9.7.0 | CP-SAT kısıt programlama çözücüsü |
| holidays >= 0.35 | Türkiye resmi tatilleri tespiti |

**Not:** Bu projenin `pyproject.toml`, `setup.py` veya benzeri bir yapılandırma dosyası yoktur. Tek bağımlılık tanımı `requirements.txt`'dedir.

---

## Kod Organizasyonu ve Modüller

| Dosya | Satır | Sorumluluk |
|-------|-------|------------|
| `app.py` | ~1900 | Ana Streamlit uygulaması. Tüm UI sekmeleri, session state yönetimi, solver çağrısı ve sonuç sunumu buradadır. |
| `models.py` | ~410 | `@dataclass` ile tanımlı veri modelleri: `Ayarlar`, `Personel`, `Alan`, `KidemGrubu`, `VardiyaTipi`, `EslesmeTercihi`, `AylikPlan`. JSON serileştirme/ters-serileştirme metodları içerir. |
| `solver.py` | ~990 | `NobetSolver` sınıfı ve CP-SAT modeli. Hard/soft kısıtlar, hedef dengeleme, teşhis sistemi (`gelismis_teshis`). |
| `storage.py` | ~220 | JSON dosya tabanlı kalıcılık. `data/settings.json` ve `data/schedules/YYYY_MM.json` dosyalarını yönetir. |
| `utils.py` | ~130 | Tarih hesaplamaları (`ay_gun_sayisi`), Türkçe gün adları, tatil parse, aralık parse (`gun_parse`). |
| `scenarios.py` | ~1130 | Sentetik test verisi üretimi. `ScenarioGenerator` ile zorluk seviyelerine göre (easy/normal/tight/nightmare) demo senaryolar oluşturur. |
| `streamlit_integration.py` | ~560 | Demo modu entegrasyonu. `inject_scenario_to_session_state` ile senaryoları uygulamaya enjekte eder, sidebar kontrolleri sunar. |

### Veri Akışı

```
Kullanıcı Girdisi (Streamlit UI)
    ↓
st.session_state (Streamlit oturum durumu)
    ↓
session_to_ayarlar() / SolverInput (app.py)
    ↓
NobetSolver (solver.py)
    ↓
CP-SAT Model → Çözüm
    ↓
AylikPlan + storage.py (JSON)
    ↓
CSV / Excel / Tablo (UI'da gösterim)
```

---

## Çalıştırma Komutları

```bash
# Sanal ortam oluştur (önerilir)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
streamlit run app.py
```

Varsayılan olarak `http://localhost:8501` adresinde açılır.

---

## UI Sekme Yapısı

`app.py` içinde 7 sekme bulunur:

1. **👥 Kişiler** — Personel listesi, hedef nöbet sayıları, yıl/ay seçimi
2. **🎖️ Kıdem** — Kıdem grupları (örn: Asistan/Uzman/Profesör), gruplara personel atama, vardiya bazlı hedefler
3. **🏢 Alanlar** — Çoklu çalışma alanı tanımı (örn: Yeşil/Sarı/Kırmızı alan), alan yetkinlikleri, kıdem kuralları
4. **⏰ Vardiyalar** — Vardiya tipi tanımları (8s/12s/16s/24s), alan-vardiya eşleştirme, personel vardiya kısıtları
5. **🏖️ İzinler** — Günlük izin seçimi, hafta günü bloklama, tercih edilen günler, resmi tatiller
6. **👫 Eşleşmeler** — Birlikte tutma (want_pairs), kesin ayrı tutma (no_pairs), esnek ayrı tutma (soft_no_pairs)
7. **✅ Çözüm** — Solver çalıştırma, sonuç tablosu, istatistikler, CSV/Excel indirme

---

## Kısıt Türleri (Constraints)

### Hard Constraints (Kesin Kurallar)
- **Ardışık yasak:** Aynı kişi arka arkaya iki gün nöbet tutamaz
- **Günaşırı limit:** Kişi başına ayda maksimum X tane 1-gün aralıklı nöbet
- **İzin günleri:** İzinli günde nöbet atanamaz
- **Ayri tutma (no_pairs):** İki kişi aynı gün nöbet tutamaz
- **Minimum staffing:** Her vardiyada en az 1 kişi (opsiyonel olarak hard veya soft)
- **Alan yetkinliği:** Personel sadece yetkin olduğu alanlarda çalışabilir
- **Vardiya kısıtları:** Personel sadece izin verilen vardiyalarda çalışabilir

### Soft Constraints (Tercih Edilen Kurallar)
- **Hafta sonu dengesi:** Cuma/Cumartesi/Pazar nöbetlerini eşit dağıtma
- **Tatil dengesi:** Resmi tatil nöbetlerini eşit dağıtma
- **2 gün boşluk tercihi:** Nöbetler arasında en az 2 gün boşluk
- **Esnek ayrı tutma:** Mümkünse kaçınılması istenen çiftler
- **Tercih edilen günler:** Personelin belirli günleri tercih etmesi
- **Alan bazlı denklik:** Her kişinin her alandan benzer sayıda nöbet tutması
- **Saat bazlı denge:** Toplam çalışma saatinin dengeli dağıtılması

---

## Veri Saklama (Persistence)

Uygulama çalışma dizininde `data/` klasörü oluşturur:

```
data/
├── settings.json          # Kalıcı ayarlar (personel, alanlar, vardiyalar, kurallar)
└── schedules/
    ├── 2025_01.json       # Ocak 2025 çizelgesi
    ├── 2025_02.json       # Şubat 2025 çizelgesi
    └── ...
```

- `Ayarlar` sınıfı aydan aya değişmeyen veriyi temsil eder
- `AylikPlan` sınıfı ay özel veriyi (izinler, tercihler, sonuç) temsil eder
- Her iki model de `to_dict()` / `from_dict()` ile JSON'a dönüştürülür
- Ayarlar "Kaydet" butonu ile manuel kaydedilir; yükleme otomatik yapılır

---

## Senaryo / Demo Modu

`streamlit_integration.py` üzerinden entegre edilmiş demo modu bulunur:
- Sidebar'dan `🧪 Demo Senaryo` bölümüne erişilir
- 4 zorluk seviyesi: `easy`, `normal`, `tight`, `nightmare`
- Seed ile tekrarlanabilir sentetik veri üretimi
- Hazır senaryolar: Minimal, Hafta Sonu Krizi, Çift Çatışması, İzin Bombardımanı
- JSON dosyasından senaryo yükleme imkanı

Demo modu aktifken `_demo_aktif` flag'i `True` olur ve kayıtlı dosyadan otomatik yükleme engellenir.

---

## Kodlama Stili ve Kurallar

- **Dil:** Tüm kod yorumları, docstring'ler ve UI metinleri **Türkçe**'dir. Yeni kod yazarken Türkçe devam edilmelidir.
- **Docstring formatı:** Üç tırnaklı açıklama satırları modül/sınıf/fonksiyon başlarında kullanılır.
- **Veri modelleri:** `dataclasses` kullanılır. Her modelde `to_dict()` ve `from_dict()` olmalıdır.
- **Streamlit session state:** UI durumu `st.session_state` sözlüğünde tutulur. Anahtar isimleri snake_case Türkçe'dir.
- **Solver ağırlıkları:** `w_` öneki ile belirtilen penalty/reward değerleri `SolverConfig` içindedir.
- **Döndürülen sonuç formatları:**
  - Tek alan: `{gun: ["Dr. A", "Dr. B"]}`
  - Çoklu alan: `{gun: {"Yeşil": ["Dr. A"], "Kırmızı": ["Dr. B"]}}`
  - Vardiya: `{gun: {"Sabah": ["Dr. A"], "Gece": ["Dr. B"]}}`
  - Alan + Vardiya: `{gun: {"Yeşil": {"Sabah": ["Dr. A"]}}}`

---

## Test Stratejisi

Projede **formal bir test çerçevesi (pytest, unittest vb.) yoktur.** Testler şu şekilde yapılır:

1. **Sentetik senaryolar:** `scenarios.py` ile üretilen veriler solver'a beslenir
2. **Demo modu:** Streamlit UI üzerinden farklı zorluklarda senaryolar çalıştırılır
3. **Manuel UI testi:** Farklı sekme kombinasyonları ile çözüm üretilip sonuçlar kontrol edilir
4. **Teşhis sistemi:** `solver.py` içindeki `gelismis_teshis()` çözüm bulunamadığında olası nedenleri raporlar

Yeni özellik eklerken:
- `scenarios.py`'ye uygun zorluk parametreleri eklenmeli
- `streamlit_integration.py`'deki session state anahtarları güncellenmeli
- `models.py`'deki `Ayarlar.to_dict()` / `from_dict()` güncellenmeli

---

## Güvenlik ve Dikkat Edilecekler

- **Dosya sistemi:** Uygulama yerel dosya sistemi üzerinde `data/` dizini oluşturur ve JSON okur/yazar. Başka dizinlere erişim yoktur.
- **Kullanıcı girdisi:** Streamlit UI üzerinden gelen metin girdileri `gun_parse()` ile sayıya dönüştürülür; temel hata kontrolü yapılır. SQL injection gibi bir risk yoktur (veritabanı kullanılmaz).
- **Dosya yükleme:** JSON import özelliği sadece `Ayarlar.from_dict()` ile sınırlıdır; zararlı kod çalıştırma riski düşüktür ancak JSON içeriği doğrulanmamaktadır.
- **Bellek:** Büyük personel listelerinde (50+ kişi, çoklu alan + vardiya) CP-SAT modeli büyüyebilir. Solver zaman aşımı `SolverConfig.max_sure_saniye = 60.0` ile sınırlıdır.

---

## Sık Kullanılan Session State Anahtarları

| Anahtar | Tür | Açıklama |
|---------|-----|----------|
| `personel_list` | `List[str]` | Personel isimleri |
| `personel_targets` | `Dict[str, int]` | Kişi bazlı hedef nöbet sayısı |
| `izin_map` | `Dict[str, Set[int]]` | Kişi başı izinli gün numaraları |
| `prefer_map` | `Dict[str, List[int]]` | Tercih edilen günler |
| `weekday_block_map` | `Dict[str, List[str]]` | Bloklu hafta günleri adları |
| `alanlar` | `List[dict]` | Alan tanımları (isim, kontenjan, renk) |
| `alan_modu_aktif` | `bool` | Çoklu alan modu açık mı |
| `kidem_gruplari` | `List[dict]` | Kıdem grup tanımları |
| `personel_kidem_gruplari` | `Dict[str, str]` | Kişi → grup eşlemesi |
| `vardiya_tipleri` | `List[dict]` | Vardiya tanımları (isim, baslangic, bitis, renk) |
| `personel_vardiya_kisitlari` | `Dict[str, List[str]]` | Kişinin çalışabileceği vardiyalar |
| `no_pairs_list` | `List[dict]` | Kesin ayrı tutulacak çiftler |
| `want_pairs_list` | `List[dict]` | Birlikte tutulacak çiftler (min gün ile) |
| `soft_no_pairs_list` | `List[dict]` | Esnek ayrı tutulacak çiftler |
| `varsayilan_hedef` | `int` | Genel varsayılan nöbet hedefi |
| `ardisik_yasak` | `bool` | Ardışık gün yasağı |
| `gunasiri_limit_aktif` | `bool` | Günaşırı limit aktif mi |
| `max_gunasiri` | `int` | Maksimum günaşırı nöbet sayısı |
| `enforce_minimum_staffing` | `bool` | Minimum personel zorunlu mu |
| `hafta_sonu_dengesi` | `bool` | Hafta sonu dengesi aktif |
| `saat_bazli_denge` | `bool` | Saat bazlı denge aktif |
| `iki_gun_bosluk_aktif` | `bool` | 2 gün boşluk tercihi aktif |

---

## Önemli Notlar Ajanlar İçin

1. **Yeni model alanı eklerken** `models.py` içinde ilgili dataclass'a ekledikten sonra `to_dict()` ve `from_dict()` metodlarını da güncelleyin.
2. **Streamlit UI state değişikliği** yaptıktan sonra `app.py` içinde `session_to_ayarlar()` ve `init_session_state()` fonksiyonlarını da senkronize edin.
3. **Solver'a yeni kısıt eklerken** `solver.py` içinde `_hard_constraints_ekle()` veya `_soft_constraints_ekle()` zincirine ekleyin. Soft constraint'ler `objective_terms`'e ağırlık ekler.
4. **Yeni sekme eklerken** `app.py`'deki `tabs = st.tabs([...])` listesini ve `with tabs[N]:` bloklarını güncelleyin.
5. **Demo senaryosu güncellerken** `scenarios.py`'deki `ScenarioGenerator.generate()` çıktı dict'ine yeni anahtarlar ekleyin ve `streamlit_integration.py`'deki `inject_scenario_to_session_state()` ile session state'e yazın.
