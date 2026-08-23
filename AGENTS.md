# AGENTS.md — Nöbet Planlayıcı v2

> Bu dosya, projeye yeni başlayan AI kodlama ajanları için hazırlanmıştır. Proje hakkında ön bilgi olmadan çalışabilmeniz için gerekli tüm bağlam burada özetlenmiştir.
>
> **Önemli:** Bu repo'da iki farklı UI mimarisi bulunur. Hangi branch'te çalıştığınızı önce kontrol edin.

---

## Branch'ler ve Mimariler

Proje iki aktif branch üzerinde ilerliyor:

| Branch | UI Mimarisi | Durum |
|--------|-------------|-------|
| `main` | 7 sekme (Kişiler, Kıdem, Alanlar, Vardiyalar, İzinler, Eşleşmeler, Çözüm) | Eski, istikrarlı |
| `feature/ui-adim1` | Dashboard + 4 adımlı sihirbaz (Ekip → İzinler → Kurallar → Çizelge) + Kurum Ayarları | Yeni, devam ediyor |

Hangi branch'te olduğunuzu anlamak için:

```bash
git branch        # * ile işaretli aktif branch
```

- `app.py` 7 sekme çağrısı içeriyorsa → `main` branch'indesiniz.
- `app.py` sayfa navigasyonu (`Dashboard`, `Yeni Plan`, `Kurum Ayarları`) içeriyorsa → `feature/ui-adim1` branch'indesiniz.
- `design.py` ve `pages/` dizini varsa → `feature/ui-adim1` branch'indesiniz.

**Genel kural:** Backend dosyaları (`models.py`, `solver.py`, `config.py`, `storage.py`, `utils.py`) her iki branch'te de ortaktır. Sadece arayüz katmanı değişir.

---

## feature/ui-adim1 Branch — Yeni Dashboard + Sihirbaz UI

### Genel Bakış

Bu branch'te uygulama, `docs/DESIGN.md` spesifikasyonuna göre yeniden tasarlanıyor:

- **Dashboard**: Mevcut/oluşturulmamış/geçmiş aylık plan kartları.
- **Yeni Plan**: 4 adımlı sihirbaz akışı.
  1. Ekip
  2. İzinler
  3. Kurallar
  4. Çizelge
- **Kurum Ayarları**: Alan, vardiya, kıdem grubu tanımları.

Teknoloji yığını değişmemiştir: Streamlit + pandas + openpyxl + OR-Tools CP-SAT.

### Kod Organizasyonu

| Dosya | Satır | Sorumluluk |
|-------|-------|------------|
| `app.py` | 119 | Ana Streamlit girişi. Sayfa navigasyonu (`Dashboard`, `Yeni Plan`, `Kurum Ayarları`) ve session state başlatma. |
| `design.py` | 319 | UI/UX bileşenleri: `inject_css()`, `render_stepper()`, `render_card()`, `render_badge()`, renk sabitleri. |
| `pages/dashboard.py` | 148 | Dashboard ekranı. Mock plan kartları ve "Yeni Plan" CTA. |
| `pages/plan_ekip.py` | — | Adım 1: Ekip tanımlama. **Henüz implemente edilmedi.** |
| `pages/plan_izinler.py` | — | Adım 2: İzin ve tercih girişi. **Henüz implemente edilmedi.** |
| `pages/plan_kurallar.py` | — | Adım 3: Kesin kurallar ve tercihler. **Henüz implemente edilmedi.** |
| `pages/plan_cizelge.py` | — | Adım 4: Solver sonuç ekranı. **Henüz implemente edilmedi.** |
| `pages/settings.py` | — | Kurum ayarları ekranı. **Henüz implemente edilmedi.** |
| `models.py` | 428 | Ortak backend: `@dataclass` veri modelleri. |
| `solver.py` | 1125 | Ortak backend: `NobetSolver` CP-SAT modeli. |
| `config.py` | 87 | Ortak backend: solver ağırlıkları ve parametreleri. |
| `storage.py` | 268 | Ortak backend: JSON dosya tabanlı kalıcılık. |
| `utils.py` | 293 | Ortak backend: tarih, parse, otomatik hedef hesaplama. |
| `tests/` | — | Property-based solver testleri. |

### Veri Akışı

```
Kullanıcı Girdisi (Streamlit pages/)
    ↓
st.session_state (page, plan_step, personel, izinler, kurallar, sonuc, kurum)
    ↓
models.Ayarlar + models.AylikPlan
    ↓
storage.py (settings.json, schedules/YYYY_MM.json)
    ↓
NobetSolver (solver.py)
    ↓
CP-SAT Model → Çözüm
    ↓
Excel / CSV / Tablo (pages/plan_cizelge.py)
```

### Session State Contract'ı (Hedef)

`docs/IMPLEMENTATION_PLAN.md` Adım 8'de öngörülen yapı:

```python
{
    "page": "dashboard",        # dashboard | plan | settings
    "plan_step": 0,            # 0-3 (Ekip, İzinler, Kurallar, Çizelge)
    "personel": [],            # Liste[dict] — kişi, kıdem, hedef, alanlar, vardiyalar
    "izinler": {},             # {isim: {"izin": [], "tercih": [], "bloklu": []}}
    "kurallar": {},            # {kural: değer / ağırlık}
    "sonuc": None,             # Solver sonucu
    "kurum": {}                # {"alanlar": [], "vardiyalar": [], "kidem_gruplari": []}
}
```

**Not:** Bu contract henüz tam oturmuş değildir. `pages/` dosyaları yazılırken `streamlit_integration.py` ve `scenarios.py`'deki eski contract ile uyumlu hale getirilmelidir.

### Implementasyon Durumu

`docs/IMPLEMENTATION_PLAN.md` adımlarına göre:

| Adım | Hedeflenen Dosya | Durum | Not |
|------|------------------|-------|-----|
| 1 | `design.py`, `app.py` iskeleti | ✅ Tamam | CSS injection, stepper, navigasyon hazır. |
| 2 | `pages/dashboard.py` | ✅ Tamam | Mock veriyle Dashboard ekranı çalışıyor. |
| 3 | `pages/plan_ekip.py` | ⬜ Yok | Yazılacak. |
| 4 | `pages/plan_izinler.py` | ⬜ Yok | Yazılacak. |
| 5 | `pages/plan_kurallar.py` | ⬜ Yok | Yazılacak. |
| 6 | `pages/plan_cizelge.py` | ⬜ Yok | Solver entegrasyonu burada yapılacak. |
| 7 | `pages/settings.py` | ⬜ Yok | Yazılacak. |
| 8 | `app.py` finalize | ⬜ Kısmi | Sayfa yönlendirme var, alt sayfalar henüz placeholder. |
| 9 | Excel export + hata kontrolü | ⬜ Yok | `plan_cizelge.py`'ye eklenecek. |

### UI/UX Tasarım Referansı

Yeni arayüzün detaylı tasarımı ve implementasyon planı şu dosyalarda:

- `docs/DESIGN.md` — Renk paleti, kart/badges/stepper bileşenleri, ekran haritası, Streamlit bileşen eşlemesi.
- `docs/IMPLEMENTATION_PLAN.md` — Adım adım implementasyon talimatları ve Kimi Code CLI prompt şablonları.

---

## main Branch — Legacy Tab UI

### Genel Bakış

`main` branch'inde uygulama 7 sekmeden oluşur. Her sekme `tabs/` altındaki bir modül tarafından çizilir. Bu mimari `feature/ui-adim1`'de değiştirilmektedir.

### Kod Organizasyonu

| Dosya | Satır | Sorumluluk |
|-------|-------|------------|
| `app.py` | 349 | Ana Streamlit uygulaması. 7 sekmenin çağrılması, session state başlatma, sidebar. |
| `models.py` | 428 | Veri modelleri: `Ayarlar`, `Personel`, `Alan`, `KidemGrubu`, `VardiyaTipi`, `EslesmeTercihi`, `AylikPlan`. |
| `solver.py` | 1022 | `NobetSolver` sınıfı ve CP-SAT modeli. |
| `config.py` | 77 | Solver ağırlıkları, zaman aşımı, işçi sayısı, determinizm parametreleri. |
| `storage.py` | 218 | JSON dosya tabanlı kalıcılık. |
| `utils.py` | 273 | Tarih hesaplamaları, parse, otomatik hedef, session state temizlik. |
| `scenarios.py` | 1128 | Sentetik test verisi üretimi. |
| `streamlit_integration.py` | 564 | Demo modu entegrasyonu. |
| `tabs/personel_tab.py` | 136 | 👥 Kişiler sekmesi |
| `tabs/kidem_tab.py` | 205 | 🎖️ Kıdem sekmesi |
| `tabs/alanlar_tab.py` | 222 | 🏢 Alanlar sekmesi |
| `tabs/vardiyalar_tab.py` | 212 | ⏰ Vardiyalar sekmesi |
| `tabs/izinler_tab.py` | 94 | 🏖️ İzinler sekmesi |
| `tabs/eslesmeler_tab.py` | 181 | 👫 Eşleşmeler sekmesi |
| `tabs/cozum_tab.py` | 580 | ✅ Çözüm sekmesi |
| `tabs/sidebar.py` | 81 | Yan panel (kayıt/yükleme) |
| `tabs/utils.py` | 5 | Sekmeler arası ortak yardımcılar |

### Veri Akışı

```
Kullanıcı Girdisi (Streamlit UI)
    ↓
st.session_state
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
CSV / Excel / Tablo
```

### UI Sekme Yapısı

1. **👥 Kişiler** — Personel listesi, kişi bazlı hedef nöbet sayıları, yıl/ay seçimi, otomatik hedef hesaplama.
2. **🎖️ Kıdem** — Kıdem grupları, gruplara personel atama, grup hedefleri ve vardiya bazlı hedefler.
3. **🏢 Alanlar** — Çoklu çalışma alanı tanımı, alan yetkinlikleri, kıdem kuralları.
4. **⏰ Vardiyalar** — Vardiya tipi tanımları, personel vardiya kısıtları.
5. **🏖️ İzinler** — Günlük izin seçimi, hafta günü bloklama, tercih edilen günler, resmi/manuel tatiller.
6. **👫 Eşleşmeler** — Birlikte tutma, kesin ayrı tutma, esnek ayrı tutma kuralları.
7. **✅ Çözüm** — Solver çalıştırma, sonuç tablosu, istatistikler, CSV/Excel indirme.

---

## Ortak Backend (Her İki Branch)

### Teknoloji Yığını

| Bileşen | Kullanım Alanı |
|---------|----------------|
| Python 3.10+ | Ana dil |
| Streamlit >= 1.28.0 | Web tabanlı kullanıcı arayüzü |
| pandas >= 2.0.0 | Tablo işlemleri, CSV dönüşümü |
| openpyxl >= 3.1.0 | Excel (.xlsx) dışa aktarımı |
| ortools == 9.15.6755 | CP-SAT kısıt programlama çözücüsü (sürüm sabitlenmiştir) |
| holidays >= 0.35 | Türkiye resmi tatilleri tespiti |
| pytest >= 7.0.0 | Property-based solver testleri |

**Not:** `pyproject.toml`, `setup.py` vb. yoktur. Tek bağımlılık tanımı `requirements.txt`'dedir.

### Veri Modelleri

`models.py` dosyasındaki ana modeller:

- `Personel`: isim, hedef_nobet, hedef_saat, bloklu_gunler, calisabilir_alanlar, alan_hedefleri, kidem_grubu, calisabilir_vardiyalar.
- `Alan`: isim, gunluk_kontenjan, max_kontenjan, renk, aktif, minimum_staffing, kidem_kurallari, vardiya_tipleri.
- `KidemGrubu`: isim, renk, varsayilan_hedef, vardiya_hedefleri.
- `VardiyaTipi`: isim, baslangic, bitis, renk, minimum_staffing; `saat` property'si vardiya süresini hesaplar.
- `EslesmeTercihi`: personel_a, personel_b, min_birlikte, zorunlu.
- `Ayarlar`: Tüm kalıcı ayarlar. Yeni eklenen alanlar: `minimum_dinlenme_saati` (varsayılan 12), `max_ardisik_calisma_gunu` (varsayılan 5).
- `AylikPlan`: Ay'a özel izinler, tercihler, manuel tatiller, hedef override ve sonuç.

Her modelde `to_dict()` ve `from_dict()` metodları bulunur.

### Kısıt Türleri

#### Hard Constraints (Kesin Kurallar)

- **Hedef nöbet sayıları:** Her personel toplam hedefi kadar nöbet tutar.
- **Ardışık yasak:** Aynı kişi arka arkaya iki gün nöbet tutamaz (nöbet modunda).
- **Günaşırı limit:** Kişi başına ayda maksimum `max_gunasiri` tane 1-gün aralıklı nöbet.
- **İzin günleri:** İzinli günde nöbet atanamaz.
- **Ayrı tutma (no_pairs):** İki kişi aynı gün nöbet tutamaz.
- **Minimum staffing:** Her vardiyada (her alanda) en az `minimum_staffing` kişi; `enforce_minimum_staffing` açıksa hard, kapalıysa soft.
- **Alan yetkinliği:** Personel sadece yetkin olduğu alanlarda çalışabilir.
- **Vardiya kısıtları:** Personel sadece izin verilen vardiyalarda çalışabilir.
- **Alan-vardiya eşleşmesi:** Bir alanda sadece tanımlı vardiya tipleri çalışabilir.
- **Kıdem kuralları:** Alan bazlı her kıdem grubundan min/max personel sayısı.
- **Vardiya dinlenme kuralı:** Vardiya modunda, iki atama arası `minimum_dinlenme_saati` kadar dinlenme zorunluluğu.

#### Soft Constraints (Tercih Edilen Kurallar)

- **Hafta sonu dengesi:** Cuma/Cumartesi/Pazar nöbetlerini eşit dağıtma.
- **Tatil dengesi:** Resmi tatil nöbetlerini eşit dağıtma.
- **2 gün boşluk tercihi:** Nöbetler arasında en az 2 gün boşluk.
- **Esnek ayrı tutma:** Mümkünse kaçınılması istenen çiftler.
- **Tercih edilen günler:** Personelin belirli günleri tercih etmesi.
- **Alan bazlı denklik:** Her kişinin her alandan benzer sayıda nöbet tutması.
- **Saat bazlı denge:** Toplam çalışma saatinin dengeli dağıtılması.
- **Günlük denge:** Günlük nöbet sayısı dengesizliğini minimize etme.
- **Alan kontenjan sapması:** Her alanın günlük hedef kontenjanına yakın olması.
- **Max ardışık çalışma günü (soft):** Vardiya modunda peş peşe çalışma günü limitini aşan atamalara ceza.

### Veri Saklama

```
data/
├── settings.json          # Kalıcı ayarlar
└── schedules/
    ├── 2025_01.json       # Ocak 2025 çizelgesi
    ├── 2025_02.json       # Şubat 2025 çizelgesi
    └── ...
```

- `Ayarlar` aydan aya değişmeyen veriyi temsil eder.
- `AylikPlan` ay özel veriyi temsil eder.
- Her ikisi de `to_dict()` / `from_dict()` ile JSON'a dönüştürülür.

### Test Stratejisi

| Dosya | Amaç |
|-------|------|
| `tests/conftest.py` | `easy_input`, `normal_input`, `nightmare_input` fixture'ları. |
| `tests/_helpers.py` | `ScenarioGenerator` çıktısını `SolverInput`'a dönüştürür. |
| `tests/test_solver_properties.py` | Solver invariant'larını doğrular. |

Ek yöntemler:
- Sentetik senaryolar (`scenarios.py`)
- Demo modu (Streamlit UI)
- Manuel UI testi
- `solver.py` içindeki `gelismis_teshis()` ile çözüm bulunamama analizi

---

## Eski / Kullanılmayan Kod

`feature/ui-adim1` branch'inde aşağıdaki dosyalar hâlâ repo'da durur ama yeni arayüz tarafından kullanılmaz:

- `tabs/`: Eski 7 sekme UI'sı. `feature/ui-adim1`'de hiçbir yerden import edilmez.
- `streamlit_integration.py`: Demo modu entegrasyonu. Eski session state contract'ına göre çalışır; yeni `pages/` mimarisine uyarlanması gerekir.
- `scenarios.py`: Sentetik test verisi üretimi. `ScenarioGenerator` çıktısı eski session state anahtarlarına göre düzenlenmiştir.
- `nobet-planlayici/`: Eski versiyon/backup alt dizini. Aktif geliştirme dışıdır.

---

## Çalıştırma Komutları

```bash
# Sanal ortam oluştur
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
pytest
pytest tests/test_solver_properties.py
pytest -v
```

---

## Kodlama Stili ve Kurallar

- **Dil:** Tüm kod yorumları, docstring'ler ve UI metinleri **Türkçe**'dir.
- **Docstring formatı:** Üç tırnaklı açıklama satırları modül/sınıf/fonksiyon başlarında kullanılır.
- **Veri modelleri:** `dataclasses` kullanılır. Her modelde `to_dict()` ve `from_dict()` olmalıdır.
- **Streamlit session state:** UI durumu `st.session_state` sözlüğünde tutulur. Anahtar isimleri snake_case Türkçe'dir.
- **Solver ağırlıkları:** `w_` öneki ile belirtilen penalty/reward değerleri `config.py` ve `SolverConfig` içindedir.
- **Determinizm:** `config.random_seed` ve `SolverConfig.pin_search_workers=True` ile aynı girdi aynı çizelgeyi üretir.
- **Backend dokunulmazlığı:** `feature/ui-adim1`'de yalnızca `app.py`, `design.py`, `pages/` dosyaları değiştirilir; `models.py`, `solver.py`, `config.py`, `storage.py`, `utils.py` korunur.

### Döndürülen Sonuç Formatları

- Tek alan: `{gun: ["Dr. A", "Dr. B"]}`
- Çoklu alan: `{gun: {"Yeşil": ["Dr. A"], "Kırmızı": ["Dr. B"]}}`
- Vardiya: `{gun: {"Sabah": ["Dr. A"], "Gece": ["Dr. B"]}}`
- Alan + Vardiya: `{gun: {"Yeşil": {"Sabah": ["Dr. A"]}}}`

---

## Sık Kullanılan Session State Anahtarları

### `main` Branch (Eski Tab UI)

| Anahtar | Tür | Açıklama |
|---------|-----|----------|
| `personel_list` | `List[str]` | Personel isimleri |
| `personel_targets` | `Dict[str, int]` | Kişi bazlı hedef nöbet sayısı override |
| `izin_map` | `Dict[str, Set[int]]` | Kişi başı izinli gün numaraları |
| `prefer_map` | `Dict[str, Set[int]]` | Tercih edilen günler |
| `weekday_block_map` | `Dict[str, List[str]]` | Bloklu hafta günleri adları |
| `manuel_tatiller` | `str` | Virgülle ayrılmış manuel tatil günleri |
| `alanlar` | `List[dict]` | Alan tanımları |
| `alan_modu_aktif` | `bool` | Çoklu alan modu |
| `alan_bazli_denklik` | `bool` | Her alanda benzer sayıda nöbet tutma hedefi |
| `personel_alan_yetkinlikleri` | `Dict[str, List[str]]` | Kişi → çalışabileceği alanlar |
| `kidem_gruplari` | `List[dict]` | Kıdem grup tanımları |
| `personel_kidem_gruplari` | `Dict[str, str]` | Kişi → grup eşlemesi |
| `vardiya_tipleri` | `List[dict]` | Vardiya tanımları |
| `personel_vardiya_kisitlari` | `Dict[str, List[str]]` | Kişinin çalışabileceği vardiyalar |
| `no_pairs_list` | `List[dict]` | Kesin ayrı tutulacak çiftler |
| `want_pairs_list` | `List[dict]` | Birlikte tutulacak çiftler |
| `soft_no_pairs_list` | `List[dict]` | Esnek ayrı tutulacak çiftler |
| `varsayilan_hedef` | `int` | Genel varsayılan nöbet hedefi |
| `otomatik_hedef` | `bool` | Otomatik hedef hesaplama aktif mi |
| `ardisik_yasak` | `bool` | Ardışık gün yasağı |
| `max_gunasiri` | `int` | Maksimum günaşırı nöbet sayısı |
| `enforce_minimum_staffing` | `bool` | Minimum personel zorunlu mu |
| `hafta_sonu_dengesi` | `bool` | Hafta sonu dengesi aktif |
| `saat_bazli_denge` | `bool` | Saat bazlı denge aktif |
| `random_seed` | `int` | CP-SAT deterministik çözüm için tohum |
| `_demo_aktif` | `bool` | Demo modu aktif mi |

### `feature/ui-adim1` Branch (Hedef Contract)

| Anahtar | Tür | Açıklama |
|---------|-----|----------|
| `page` | `str` | Aktif sayfa: `dashboard`, `plan`, `settings` |
| `plan_step` | `int` | Sihirbaz adımı: 0-3 |
| `personel` | `List[dict]` | Ekip tanımları |
| `izinler` | `Dict[str, dict]` | `{isim: {"izin": [], "tercih": [], "bloklu": []}}` |
| `kurallar` | `Dict` | Aktif kurallar ve ağırlıkları |
| `sonuc` | `Dict` veya `None` | Solver çıktısı |
| `kurum` | `Dict` | Alan, vardiya, kıdem tanımları |

---

## Önemli Notlar Ajanlar İçin

1. **Branch kontrolü yapın.** `app.py`'nin yapısına bakarak `main` mi yoksa `feature/ui-adim1` mi olduğunu hemen anlayın.
2. **Yeni UI geliştirirken** `docs/DESIGN.md` ve `docs/IMPLEMENTATION_PLAN.md`'yi önce okuyun.
3. **Backend dosyalarına** (`models.py`, `solver.py`, `config.py`, `storage.py`, `utils.py`) dokunmayın; sadece arayüz katmanını değiştirin.
4. **Yeni model alanı eklerken** `models.py` içinde ilgili dataclass'a ekledikten sonra `to_dict()` ve `from_dict()` metodlarını da güncelleyin.
5. **Streamlit UI state değişikliği** yaptıktan sonra `session_to_ayarlar()` (varsa) ve `init_session_state()` fonksiyonlarını senkronize edin.
6. **Solver'a yeni kısıt eklerken** `solver.py` içinde `_hard_constraints_ekle()` veya `_soft_constraints_ekle()` zincirine ekleyin.
7. **Demo senaryosu güncellerken** `scenarios.py` ve `streamlit_integration.py`'deki session state anahtarlarını yeni `pages/` contract'ına göre uyarlayın.
8. **Otomatik hedef hesaplama** `utils.hesapla_otomatik_hedef()` ile çalışır; yeni UI'da kişisel hedef > otomatik > kıdem > varsayılan öncelik zinciri korunmalıdır.
