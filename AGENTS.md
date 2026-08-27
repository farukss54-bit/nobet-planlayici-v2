# AGENTS.md — Nöbet Planlayıcı v2

> Bu dosya, projeye yeni başlayan AI kodlama ajanları için hazırlanmıştır. Proje hakkında ön bilgi olmadan çalışabilmeniz için gerekli tüm bağlam burada özetlenmiştir.

---

## Proje Genel Bakış

**Nöbet Planlayıcı v2**, hastane acil servisleri için aylık nöbet çizelgesi oluşturan bir Python web uygulamasıdır. Google OR-Tools CP-SAT çözücüsü kullanarak personel kısıtlarını, izinleri, birlikte/ayrı tutma kurallarını, çalışma alanı ve vardiya kısıtlarını optimize eder.

> **Güncel durum:** `feature/solver-v3` dalında iki resmi faz tamamlandı — **Faz 0-1** (solver çekirdeği sertleştirmesi: soft hedefler, günaşırı düzeltmesi, kontenjan granülaritesi — `docs/SOLVER_V3_FAZ_0-1.md`) ve **Faz 2** (UI dürüstlük katmanı: girdi doğrulama, hata görünürlüğü, boş-slot ayrıştırma — `docs/SOLVER_V3_FAZ_2.md`, özet `docs/SOLVER_V3_FAZ_2_RAPOR.md`). Bu belgeler, aşağıdaki bazı bölümlerin (Kısıt Türleri, Test Stratejisi) **neden** böyle olduğunu açıklayan tarihçedir — çelişki gördüğünüzde onlara bakın.

Uygulamanın ana işlevleri:
- Personel, kıdem grubu, çalışma alanı ve vardiya tipi tanımlama
- Kişi bazlı hedef nöbet sayısı ve vardiya bazlı hedefler belirleme
- İzin, tercih ve hafta günü bloklama girme
- Birlikte tutma (want_pairs), kesin ayrı tutma (no_pairs), esnek ayrı tutma (soft_no_pairs) kuralları
- Çoklu çalışma alanı ve vardiya desteği
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
| ortools == 9.15.6755 | CP-SAT kısıt programlama çözücüsü (sürüm sabitlenmiştir) |
| holidays >= 0.35 | Türkiye resmi tatilleri tespiti |
| pytest >= 7.0.0 | Property-based solver testleri |

**Not:** Bu projenin `pyproject.toml`, `setup.py` veya benzeri bir yapılandırma dosyası yoktur. Tek bağımlılık tanımı `requirements.txt`'dedir.

---

## Kod Organizasyonu ve Modüller

| Dosya | Satır | Sorumluluk |
|-------|-------|------------|
| `app.py` | 346 | Ana Streamlit uygulaması. Sayfa yapılandırması, session state başlatma, sekmelerin çağrılması ve sidebar'ı bir araya getirir. |
| `models.py` | 448 | `@dataclass` ile tanımlı veri modelleri: `Ayarlar`, `Personel`, `Alan`, `KidemGrubu`, `VardiyaTipi`, `EslesmeTercihi`, `AylikPlan`. JSON serileştirme/ters-serileştirme metodları içerir. |
| `solver.py` | 1262 | `NobetSolver` sınıfı ve CP-SAT modeli. Hard/soft kısıtlar, hedef dengeleme, teşhis sistemi (`gelismis_teshis`/`teshis_ozeti`). |
| `config.py` | 97 | Solver ağırlıkları, zaman aşımı, işçi sayısı ve determinizm parametrelerinin merkezi konfigürasyonu. |
| `storage.py` | 275 | JSON dosya tabanlı kalıcılık. `data/settings.json` ve `data/schedules/YYYY_MM.json` dosyalarını yönetir. Hatalar `logging` ile raporlanır (bkz. Faz 2 / G2.5). |
| `utils.py` | 364 | Tarih hesaplamaları (`ay_gun_sayisi`), Türkçe gün adları, tatil parse, aralık parse (`gun_parse`), otomatik hedef hesaplama (taşma kırpmalı, bkz. Faz 0-1 / G1.5) ve session state temizlik fonksiyonları. |
| `scenarios.py` | 1164 | Sentetik test verisi üretimi. `ScenarioGenerator` ile zorluk seviyelerine göre (`easy`/`normal`/`tight`/`nightmare`) demo senaryolar oluşturur; `HazirSenaryolar` sabit test senaryoları sunar. |
| `streamlit_integration.py` | 564 | Demo modu entegrasyonu. `inject_scenario_to_session_state()` ile senaryoları uygulamaya enjekte eder, sidebar kontrolleri ve detay modalı sunar. |
| `tabs/` | - | UI'nın her sekmesi ayrı bir modüle ayrılmıştır. |
| `tests/` | - | Pytest tabanlı solver + AppTest testleri (144 test, bkz. Test Stratejisi). |

### Sekme Modülleri (`tabs/`)

| Dosya | Satır | Sekme |
|-------|-------|-------|
| `tabs/personel_tab.py` | 178 | 👥 Kişiler |
| `tabs/kidem_tab.py` | 205 | 🎖️ Kıdem |
| `tabs/alanlar_tab.py` | 222 | 🏢 Alanlar |
| `tabs/vardiyalar_tab.py` | 222 | ⏰ Vardiyalar |
| `tabs/izinler_tab.py` | 127 | 🏖️ İzinler |
| `tabs/eslesmeler_tab.py` | 187 | 👫 Eşleşmeler |
| `tabs/cozum_tab.py` | 881 | ✅ Çözüm (Faz 2'de önemli ölçüde büyüdü: girdi doğrulama, çözüm karnesi, boş-slot ayrıştırma) |
| `tabs/sidebar.py` | 84 | Yan panel (kayıt/yükleme) |
| `tabs/utils.py` | 5 | Sekmeler arası ortak yardımcılar |

### Veri Akışı

```
Kullanıcı Girdisi (Streamlit UI)
    ↓
st.session_state (Streamlit oturum durumu)
    ↓
session_to_ayarlar() (app.py) → Ayarlar modeli
    ↓
tabs/cozum_tab.py → SolverInput
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

### Test Komutları

```bash
# Tüm pytest testlerini çalıştır (144 test, ~4 dk — AppTest'ler dahil)
pytest

# En yavaş 10 testi (uzun CP-SAT çözümü / tam AppTest.from_file) atla (~3 dk)
pytest -m "not yavas"

# Belirli test dosyası
pytest tests/test_solver_properties.py

# Detaylı çıktı ile
pytest -v
```

---

## UI Sekme Yapısı

`app.py` içinde 7 sekme bulunur:

1. **👥 Kişiler** — Personel listesi, kişi bazlı hedef nöbet sayıları, yıl/ay seçimi, otomatik hedef hesaplama
2. **🎖️ Kıdem** — Kıdem grupları (örn: Kıdemli/Orta/Yeni), gruplara personel atama, grup hedefleri ve vardiya bazlı hedefler
3. **🏢 Alanlar** — Çoklu çalışma alanı tanımı (örn: Acil/Yoğun Bakım/Poliklinik), alan yetkinlikleri, kıdem kuralları
4. **⏰ Vardiyalar** — Vardiya tipi tanımları (başlangıç/bitiş saati), personel vardiya kısıtları
5. **🏖️ İzinler** — Günlük izin seçimi, hafta günü bloklama, tercih edilen günler, resmi/manuel tatiller
6. **👫 Eşleşmeler** — Birlikte tutma (`want_pairs_list`), kesin ayrı tutma (`no_pairs_list`), esnek ayrı tutma (`soft_no_pairs_list`)
7. **✅ Çözüm** — Solver çalıştırma, sonuç tablosu, istatistikler, CSV/Excel indirme

---

## Kısıt Türleri (Constraints)

> **Önemli (Faz 0-1, G1.3):** Hedef nöbet sayıları artık **hard değil soft**tur — bkz. aşağıdaki soft liste. Hedefi hiç girilmemiş kişi serbest bırakılır (`solver.uyarilar`'a not düşülür). Bu ayrımı bilmeden `solver.py`'ye dokunmayın; `docs/SOLVER_V3_FAZ_0-1.md` (G1.3) ve `docs/SOLVER_V3_FAZ_2_RAPOR.md` (G2.9) geçmişini okuyun.

### Hard Constraints (Kesin Kurallar)
- **Ardışık yasak:** Aynı kişi arka arkaya iki gün nöbet tutamaz
- **Günaşırı limit:** Kişi başına ayda maksimum `max_gunasiri` tane 1-gün aralıklı nöbet. **Yalnızca nöbet modunda (vardiyasız) uygulanır** — vardiya modunda G1.1'den beri devre dışıdır (vardiya saatleri zaten dinlenmeyi kapsar).
- **İzin günleri:** İzinli günde nöbet atanamaz; hafta günü bloklamalar izinlere dönüştürülür
- **Ayrı tutma (no_pairs):** İki kişi aynı gün nöbet tutamaz
- **Minimum staffing:** Her vardiyada (her alanda) en az `minimum_staffing` kişi; `enforce_minimum_staffing` açıksa hard, kapalıysa soft. **Yalnızca vardiya modunda (`vardiyalar` doluyken) kurulur** — vardiyasız modlarda (nöbet modu veya yalnız alan modu) bu bayrağın modelde HİÇBİR etkisi yoktur; `AlanTanimi.minimum_staffing` o durumda kullanılmaz (bilinen modelleme borcu, bkz. Faz 2 G2.1 ÖNERİ).
- **Alan yetkinliği:** Personel sadece yetkin olduğu alanlarda çalışabilir
- **Vardiya kısıtları:** Personel sadece izin verilen vardiyalarda çalışabilir
- **Alan-vardiya eşleşmesi:** Bir alanda sadece tanımlı vardiya tipleri çalışabilir
- **Kıdem kuralları:** Alan bazlı her kıdem grubundan min personel sayısı (min>0 iken)
- **Alan max kontenjan:** `max_kontenjan` tanımlıysa o alan/vardiya kombinasyonu için gün başına hard üst sınır (G1.4)
- **Kişisel maksimum:** `kisinin_max_atama(...)` (G1.2 formülü) — bir kişinin hedefi bu değeri aşarsa `NobetSolver.__init__` `ValueError` fırlatır (pre-solve doğrulama)

### Soft Constraints (Tercih Edilen Kurallar)
- **Hedef nöbet sayıları (G1.3):** Her personel `Σ|gerçekleşen − hedef|` cezasıyla (`w_hedef_sapma`) hedefine yaklaştırılır; vardiya bazlı hedef varsa her vardiya için ayrı. Hard eşitlik DEĞİLDİR.
- **Alan kontenjan sapması (G1.4):** Vardiya modunda **vardiya başına** (eskiden gün başına) `gunluk_kontenjan` hedefine yakınlık cezası
- **Hafta sonu dengesi:** Cuma/Cumartesi/Pazar nöbetlerini eşit dağıtma
- **Tatil dengesi:** Resmi tatil nöbetlerini eşit dağıtma
- **2 gün boşluk tercihi:** Nöbetler arasında en az 2 gün boşluk (soft ceza)
- **Esnek ayrı tutma:** Mümkünse kaçınılması istenen çiftler
- **Birlikte tutma (want_pairs):** `min_k=0` ise yalnızca ödül (soft tercih); `min_k>0` ise hard alt sınır (G2.8'den beri UI'dan `min=0` girilebilir)
- **Tercih edilen günler:** Personelin belirli günleri tercih etmesi (ödül)
- **Alan bazlı denklik:** Her kişinin her alandan benzer sayıda nöbet tutması
- **Saat bazlı denge:** Toplam çalışma saatinin dengeli dağıtılması
- **Günlük denge:** Günlük nöbet sayısı dengesizliğini minimize etme

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

- `Ayarlar` sınıfı aydan aya değişmeyen veriyi temsil eder.
- `AylikPlan` sınıfı ay özel veriyi (izinler, tercihler, sonuç) temsil eder.
- Her iki model de `to_dict()` / `from_dict()` ile JSON'a dönüştürülür.
- Ayarlar "Kaydet" butonu ile manuel kaydedilir; uygulama açılışında otomatik yüklenir.

---

## Senaryo / Demo Modu

`streamlit_integration.py` üzerinden entegre edilmiş demo modu bulunur:
- Sidebar'dan `🧪 Demo Senaryo` bölümüne erişilir.
- 4 zorluk seviyesi: `easy`, `normal`, `tight`, `nightmare`.
- Seed ile tekrarlanabilir sentetik veri üretimi.
- Hazır senaryolar: `Minimal`, `Hafta Sonu Krizi`, `Çift Çatışması`, `İzin Bombardımanı` (`HazirSenaryolar` sınıfı).
- JSON dosyasından senaryo yükleme imkanı.
- Demo modu aktifken `_demo_aktif` flag'i `True` olur ve kayıtlı dosyadan otomatik yükleme engellenir.

---

## Test Stratejisi

Proje **pytest** ile 144 testlik bir suite içerir (143 passed + 1 skipped; Faz 0-1'de 86, Faz 2'de 57 test eklendi). `pytest.ini` bir `yavas` marker'ı tanımlar (gerçek CP-SAT çözümü/tam `AppTest.from_file` gerektiren en yavaş 10 test); `pytest -m "not yavas"` bu 10'u atlar ama kalan 133 test hâlâ birçok gerçek (kısa) CP-SAT çözümü içerdiğinden süre çok kısalmaz (~tam suite 250s → filtrelenmiş ~182s).

| Dosya | Amaç |
|-------|------|
| `tests/conftest.py` | `easy_input`, `normal_input`, `nightmare_input` fixture'ları (`ScenarioGenerator` + `_helpers.scenario_to_solver_input`). |
| `tests/_helpers.py` | `ScenarioGenerator` çıktısını `SolverInput`'a dönüştürür; test verisinde vardiyalar kapalı tutulur. |
| `tests/_apptest_helpers.py` | UI testleri için ortak AppTest kurulumu: `apptest_calistir` (gerçek `app.py`'yi `storage` dosya yollarını `tmp_path`'e yönlendirerek çalıştırır), `from_function_izole` (tek bir tab fonksiyonunu izole çalıştırır, `PagesManager.uses_pages_directory` bug'ını bypass eder — bkz. aşağıdaki "AppTest Gotcha'ları"). |
| `tests/test_solver_properties.py` | Solver invariant'larını doğrular: ardışık yasak, izin günleri, no_pairs, hedef sapması, determinizm, nightmare infeasible raporlama. |
| `tests/test_baseline.py` + `tests/fixtures/*.json` | Solver'ın bilinen (INFEASIBLE/FEASIBLE/ValueError) davranışını sabitleyen 3+1 baseline fikstürü (`gercek_senaryo_01` gerçek bir vakanın kurgusallaştırılmış hali, `tests/test_baseline_gercek_senaryo_01.py`'de `@pytest.mark.yavas` regresyon tavanıyla test edilir). |
| `tests/test_g0_1_*` … `tests/test_g2_10_*` | Faz 0-1 (G0.1-G1.5) ve Faz 2 (G2.1-G2.10) görev bazlı testler — her dosya bir faz görevine karşılık gelir, bkz. `docs/SOLVER_V3_FAZ_0-1.md` / `docs/SOLVER_V3_FAZ_2.md` / `docs/SOLVER_V3_FAZ_2_RAPOR.md`. |

### AppTest Gotcha'ları (bu ortamda doğrulanmış)

UI kodunu (`tabs/*.py`) test ederken `streamlit.testing.v1.AppTest` kullanılıyor. İki ortam kısıtlaması tespit edildi:

1. **`PagesManager.uses_pages_directory` kalıcılığı:** Depo kökünde boş bir `pages/` dizini var. İlk `AppTest.from_file("app.py")` çağrısı bu süreç-geneli bayrağı `True`'ya kilitler; sonraki `AppTest.from_function`/`from_string` çağrıları (kendi `pages/` dizinleri olmasa bile) yanlışlıkla çok-sayfalı-uygulama moduna sapıp çöker. Çözüm: `from_function_izole` her çağrıdan önce bayrağı `monkeypatch` ile `False`'a sabitler.
2. **`AppTest.from_function` kaynak-kodek uyumsuzluğu:** Sarmalayıcı fonksiyonun kaynak metni geçici bir dosyaya platform kodekiyle yazılıp UTF-8 olarak geri okunuyor; fonksiyonun **kendi gövdesinde** Türkçe karakter (ü, ı, ş, ğ, ç, ö) olursa `UnicodeDecodeError` fırlıyor. Kural: `from_function`'a verilen sarmalayıcı fonksiyonların kaynağı ASCII kalmalı (çağırdıkları gerçek modül kodu — örn. `tabs/cozum_tab.py` — normal import edildiğinden bu kısıtlamaya tabi değil). Ayrıca bu fonksiyonlar dış closure değişkenlerine erişemez (yalnızca kendi kaynağı exec edilir) — parametre + `AppTest.from_function(fn, args=(...))` kullanın.

Ayrıca:
- **Gerçek `app.py` her sekmeyi render eder:** `st.tabs()` bir layout'tur, koşullu render değildir — `AppTest.from_file("app.py").run()` TÜM sekmelerin kodunu çalıştırır. `session_state`'i her sekmenin ihtiyaç duyduğu anahtarlarla önceden doldurun (`apptest_calistir`'deki varsayılan şablona bakın).
- **İsme bağlı widget key'leri kırılgan:** `izinler_tab.py`/`vardiyalar_tab.py` kişi başına `key=f"izin_{p}"` gibi isme bağlı key kullanıyor; iki aynı isimli personel `StreamlitDuplicateElementKey` ile TÜM uygulamayı çökertir (bkz. Faz 2 G2.6 ÖNERİ). Bu senaryoları test ederken tam `app.py` yerine `from_function_izole` ile ilgili tab fonksiyonunu izole çalıştırın.
- **Sentetik solver casusu:** Gerçek CP-SAT çözümünden kaçınmak isteyen testler (örn. G2.7, G2.8) `tabs.cozum_tab.NobetSolver`'ı `monkeypatch` ile sahte bir sınıfa değiştirip `SolverInput`'u yakalıyor — hızlı ve deterministik.

Diğer test yöntemleri:
- **Demo modu:** Streamlit UI üzerinden farklı zorluklarda senaryolar çalıştırılır.
- **Teşhis sistemi:** `solver.py` içindeki `gelismis_teshis()`/`teshis_ozeti()` çözüm bulunamadığında olası nedenleri raporlar (G2.9'da false-positive'leri temizlendi).

---

## Kodlama Stili ve Kurallar

- **Dil:** Tüm kod yorumları, docstring'ler ve UI metinleri **Türkçe**'dir. Yeni kod yazarken Türkçe devam edilmelidir.
- **Docstring formatı:** Üç tırnaklı açıklama satırları modül/sınıf/fonksiyon başlarında kullanılır.
- **Veri modelleri:** `dataclasses` kullanılır. Her modelde `to_dict()` ve `from_dict()` olmalıdır.
- **Streamlit session state:** UI durumu `st.session_state` sözlüğünde tutulur. Anahtar isimleri snake_case Türkçe'dir.
- **Solver ağırlıkları:** `w_` öneki ile belirtilen penalty/reward değerleri `config.py` ve `SolverConfig` içindedir.
- **Determinizm:** `config.random_seed` ve `SolverConfig.pin_search_workers=True` ile aynı girdi aynı çizelgeyi üretir. Aynı `ortools` sürümü için garantilidir; `requirements.txt`'te sürüm sabitlenmiştir.
- **Döndürülen sonuç formatları:**
  - Tek alan: `{gun: ["Dr. A", "Dr. B"]}`
  - Çoklu alan: `{gun: {"Yeşil": ["Dr. A"], "Kırmızı": ["Dr. B"]}}`
  - Vardiya: `{gun: {"Sabah": ["Dr. A"], "Gece": ["Dr. B"]}}`
  - Alan + Vardiya: `{gun: {"Yeşil": {"Sabah": ["Dr. A"]}}}`
  - **Boş slot ayrımı (G2.4):** Vardiya modunda `_coz_ve_sonuc_al` artık GEÇERLİ her alan-vardiya kombinasyonunu — kimse atanmasa bile boş liste `[]` olarak — sonuca yazar; yalnızca GEÇERSİZ kombinasyonlar (alan.vardiya_tipleri filtresine uymayanlar) hiç yazılmaz. UI (`tabs/cozum_tab.py::_hucre_degeri`) bu farkı ayırt eder: anahtar var + liste boş → `"⚠ BOŞ"`, anahtar yok → `"—"`.

---

## Güvenlik ve Dikkat Edilecekler

- **Dosya sistemi:** Uygulama yerel dosya sistemi üzerinde `data/` dizini oluşturur ve JSON okur/yazar. Başka dizinlere erişim yoktur. `storage.py`'deki tüm hatalar `logging` ile raporlanır ve çağıran taraf (`personel_tab.py`/`cozum_tab.py`) dönüş değerini kontrol edip `st.error` gösterir (G2.5) — artık sessiz `print()` yok. Bozuk plan dosyaları listeden kaybolmaz, `{"bozuk": True}` ile işaretlenip sidebar'da "⚠ bozuk dosya" olarak gösterilir.
- **Depo kökünde boş bir `pages/` dizini var** (takip edilmiyor, gerçek bir amacı yok görünüyor). Streamlit multipage-app tespiti bunu görünce `PagesManager.uses_pages_directory`'i kalıcı olarak `True`'ya kilitliyor ve bazı `AppTest` senaryolarını bozabiliyor (bkz. Test Stratejisi → AppTest Gotcha'ları). Silmeden önce kullanıcıya danışın.
- **Kullanıcı girdisi:** Streamlit UI üzerinden gelen metin girdileri `gun_parse()` ile sayıya dönüştürülür; temel hata kontrolü yapılır. SQL injection gibi bir risk yoktur (veritabanı kullanılmaz).
- **Dosya yükleme:** JSON import özelliği sadece `Ayarlar.from_dict()` ile sınırlıdır; zararlı kod çalıştırma riski düşüktür ancak JSON içeriği doğrulanmamaktadır.
- **Bellek:** Büyük personel listelerinde (50+ kişi, çoklu alan + vardiya) CP-SAT modeli büyüyebilir. Solver zaman aşımı `config.max_sure_saniye = 60.0` ile sınırlıdır; karmaşık problemlerde artırılabilir.
- **Ağırlıklar:** `config.py` içindeki soft constraint ağırlıkları birbiriyle göreceli olarak ayarlanmalıdır; mutlak değerler değil, göreceli büyüklükler önemlidir.

---

## Sık Kullanılan Session State Anahtarları

| Anahtar | Tür | Açıklama |
|---------|-----|----------|
| `personel_list` | `List[str]` | Personel isimleri |
| `personel_targets` | `Dict[str, int]` | Kişi bazlı hedef nöbet sayısı override |
| `personel_sayisi` | `int` | UI'da gösterilen personel sayısı |
| `izin_map` | `Dict[str, Set[int]]` | Kişi başı izinli gün numaraları |
| `prefer_map` | `Dict[str, Set[int]]` | Tercih edilen günler |
| `weekday_block_map` | `Dict[str, List[str]]` | Bloklu hafta günleri adları ("Pazartesi", "Cuma", vb.) |
| `manuel_tatiller` | `str` | Virgülle ayrılmış manuel tatil günleri |
| `alanlar` | `List[dict]` | Alan tanımları (isim, kontenjan, max_kontenjan, renk, minimum_staffing, kidem_kurallari, vardiya_tipleri) |
| `alan_modu_aktif` | `bool` | Çoklu alan modu açık mı |
| `alan_bazli_denklik` | `bool` | Her alanda benzer sayıda nöbet tutma hedefi |
| `personel_alan_yetkinlikleri` | `Dict[str, List[str]]` | Kişi → çalışabileceği alanlar |
| `kidem_gruplari` | `List[dict]` | Kıdem grup tanımları (isim, renk, varsayilan_hedef, vardiya_hedefleri) |
| `personel_kidem_gruplari` | `Dict[str, str]` | Kişi → grup eşlemesi |
| `vardiya_tipleri` | `List[dict]` | Vardiya tanımları (isim, baslangic, bitis, renk, minimum_staffing) |
| `personel_vardiya_kisitlari` | `Dict[str, List[str]]` | Kişinin çalışabileceği vardiyalar (boş = tümü) |
| `no_pairs_list` | `List[dict]` | Kesin ayrı tutulacak çiftler (`{"a": ..., "b": ...}`) |
| `want_pairs_list` | `List[dict]` | Birlikte tutulacak çiftler (`{"a": ..., "b": ..., "min": ...}`) |
| `soft_no_pairs_list` | `List[dict]` | Esnek ayrı tutulacak çiftler (`{"a": ..., "b": ...}`) |
| `varsayilan_hedef` | `int` | Genel varsayılan nöbet hedefi (0-31 arası) |
| `otomatik_hedef` | `bool` | Otomatik hedef hesaplama aktif mi |
| `ardisik_yasak` | `bool` | Ardışık gün yasağı |
| `gunasiri_limit_aktif` | `bool` | Günaşırı limit aktif mi |
| `max_gunasiri` | `int` | Maksimum günaşırı nöbet sayısı |
| `enforce_minimum_staffing` | `bool` | Minimum personel zorunlu mu (hard/soft) |
| `hafta_sonu_dengesi` | `bool` | Hafta sonu dengesi aktif |
| `saat_bazli_denge` | `bool` | Saat bazlı denge aktif |
| `iki_gun_bosluk_aktif` | `bool` | 2 gün boşluk tercihi aktif |
| `w_cuma` / `w_cumartesi` / `w_pazar` | `int` | Hafta sonu denge ağırlıkları |
| `w_gap3` | `int` | 2 gün boşluk ceza ağırlığı |
| `tatil_dengesi` | `bool` | Tatil dengesi aktif |
| `random_seed` | `int` | CP-SAT deterministik çözüm için sabit tohum (varsayılan 42) |
| `pin_search_workers` | `bool` | True ise paralel arama tek işçiye düşer (reproducibility) |
| `_demo_aktif` | `bool` | Demo modu aktif mi |
| `_demo_meta` | `dict` | Demo meta bilgisi (seed, difficulty, yıl, ay) |

---

## Önemli Notlar Ajanlar İçin

1. **Yeni model alanı eklerken** `models.py` içinde ilgili dataclass'a ekledikten sonra `to_dict()` ve `from_dict()` metodlarını da güncelleyin.
2. **Streamlit UI state değişikliği** yaptıktan sonra `app.py` içinde `session_to_ayarlar()` ve `init_session_state()` fonksiyonlarını da senkronize edin.
3. **Solver'a yeni kısıt eklerken** `solver.py` içinde `_hard_constraints_ekle()` veya `_soft_constraints_ekle()` zincirine ekleyin. Soft constraint'ler `objective_terms`'e ağırlık ekler; ağırlıkları `config.py`'den alın.
4. **Yeni sekme eklerken** `app.py`'deki `tabs = st.tabs([...])` listesini ve `with tabs[N]:` bloklarını güncelleyin; ilgili render fonksiyonunu `tabs/` altına ekleyin.
5. **Demo senaryosu güncellerken** `scenarios.py`'deki `ScenarioGenerator.generate()` çıktı dict'ine yeni anahtarlar ekleyin ve `streamlit_integration.py`'deki `inject_scenario_to_session_state()` ile session state'e yazın.
6. **Test verisi değişikliği** yaparsanız `tests/_helpers.py` içindeki `scenario_to_solver_input()` dönüşümünü de güncelleyin; test fixture'ları bu helper'a bağımlıdır.
7. **Otomatik hedef hesaplama** `utils.hesapla_otomatik_hedef()` ve `tabs/cozum_tab.py` içindeki hedef öncelik zinciri (kişisel > otomatik > kıdem > varsayılan) ile çalışır; değişiklik yaparken iki yeri de tutarlı tutun. `tabs/personel_tab.py`'deki **"Oto" checkbox'ı** (G2.7) bu zincirin UI tarafındaki anahtarıdır: işaretliyse `personel_targets`'tan silinir (zincir çalışır), işaretli değilse değer — varsayılana eşit olsa bile — kalıcı yazılır. Kişisel hedefi olan kişi, kıdem grubunun vardiya kırılımını sessizce KAYBEDER (davranış kasıtlı, yalnızca `st.info` ile bildirilir — bkz. Faz 2 G2.7).
8. **Faz bazlı çalışma protokolü:** Bu proje şu ana kadar iki resmi faz tamamladı — `docs/SOLVER_V3_FAZ_0-1.md` (solver çekirdeği: soft hedefler, günaşırı düzeltmesi, kontenjan granülaritesi) ve `docs/SOLVER_V3_FAZ_2.md` (UI dürüstlük katmanı, özet: `docs/SOLVER_V3_FAZ_2_RAPOR.md`). Her ikisi de katı bir protokol izledi: görevler sırayla, görev başına ayrı commit + Türkçe RAPOR, testi asla zayıflatma (assert gevşetme/silme yasak), "dokunma" listesindeki dosya/fonksiyonlara dokunmama. Faz 3+ planlanırsa aynı disiplini bekleyin; yeni bir faz dokümanı varsa önce onu okuyun.
9. **Çözüm kapısı (G2.6):** `tabs/cozum_tab.py::_girdi_dogrula` solver kurulumundan ÖNCE çalışır ve hard hatalarda (`boş/yinelenen isim`, tanımsız/üyesiz kıdem kuralı) `st.stop()` ile durur. Yeni bir girdi kimliği kuralı eklerken bu fonksiyonu güncelleyin, solver'ın kendisini değil.
10. **UI'da isme bağlı widget key'i kullanmayın:** `izinler_tab.py`/`vardiyalar_tab.py`'deki `key=f"izin_{p}"` gibi desenler, iki personel aynı isme sahip olduğunda `StreamlitDuplicateElementKey` ile TÜM uygulamayı çökertir (bilinen sorun, düzeltilmedi — bkz. Faz 2 G2.6 ÖNERİ). Yeni kişi-bazlı widget eklerken index bazlı key (`key=f"...{i}"`) tercih edin.
11. **Test yazarken hız için** `pytest -m "not yavas"` kullanın; gerçek CP-SAT çözümü veya tam `AppTest.from_file("app.py")` gerektiren testleri `@pytest.mark.yavas` ile işaretleyin (bkz. Test Stratejisi'ndeki AppTest Gotcha'ları).
