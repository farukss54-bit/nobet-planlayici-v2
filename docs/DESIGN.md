# Nöbet Planlayıcı v2 — UI/UX Tasarım Spesifikasyonu

## 1. Tasarım Dili Prensipleri

### 1.1 Kart-Merkezli Bilgi Yapısı
- Her bilgi parçası bir `card` (kutu) içinde sunulur.
- Kart = bir düşünce birimi. Kullanıcı bir bakışta kartın sınırlarını ve içeriğini anlar.
- Kartlar arasında tutarlı `padding` (20px) ve `border-radius` (10px) kullanılır.

### 1.2 Sessiz Vurgu (Restrained Accent)
- Renk sadece iki amaçla kullanılır:
  1. **Eylem gerektiren durumlar** (başarı, uyarı, hata)
  2. **Kimlik kodlaması** (kıdem grupları, alanlar)
- Bilgi taşıma görevi nötr gri tonlara aittir. Beyaz arka plan üzerinde `#1a1a2e` metin, `#6b6b7b` ikincil metin.

### 1.3 Monospace Ritmi
- Tüm sayılar, gün numaraları, saatler, kodlar **monospace** fontta (SF Mono, Monaco, Cascadia Code).
- Metin ve etiketler **sans-serif** (system-ui, Segoe UI, Roboto).
- Bu ayrım kullanıcının sayısal veriyi hızlı taramasını sağlar.

### 1.4 Adım Şeridi (Stepper)
- "Yeni Plan" akışında 4 adım vardır: Ekip → İzinler → Kurallar → Çizelge.
- Kullanıcı her zaman hangi adımda olduğunu ve ne kaldığını görür.
- Tamamlanan adımlar yeşil tik (`✓`), aktif adım dolu daire, bekleyen adım boş daire.

### 1.5 Geri Bildirim Döngüsü
- Her kullanıcı eylemi anında görsel karşılık alır.
- Örnek: İzin günü yazıldığında altındaki ay şeridi anında boyanır.
- Örnek: Kural seçildiğinde etiket rengi değişir.

### 1.6 Kesin / Tercih Ayrımı
- **Kesin kurallar**: Toggle switch (`st.toggle`). Açık/kapalı. Kapalıyken çizelge yine üretilir.
- **Tercihler**: Segmented control (`Az / Orta / Çok`). Mümkün olduğunca sağlanır; sağlanamazsa çizelge yine üretilir.

---

## 2. Renk Paleti

```css
:root {
  --bg: #f5f3f0;              /* Ana arka plan — sıcak nötr gri */
  --surface: #ffffff;          /* Kart arka planı */
  --surface-hover: #faf9f7;    /* Hover durumu */
  --border: #e8e5e0;          /* Kart/sınırlar */

  --text-primary: #1a1a2e;    /* Başlıklar, ana metin */
  --text-secondary: #6b6b7b;   /* Açıklamalar, ikincil */
  --text-tertiary: #9a9aa8;    /* Yer tutucular, gölge metin */

  --accent: #0d7c8a;           /* Tek vurgu rengi (teal/cyan) */
  --accent-light: #e6f4f5;     /* Açık vurgu arka planı */

  --success: #2e7d32;          /* Başarı, tamamlanmış adım */
  --warning: #ed6c02;          /* Uyarı, dikkat edilecekler */
  --danger: #c62828;           /* Hata, izinli gün, kesin ayrı */

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
}
```

### Kıdem Grubu Renkleri (Kimlik)
- Kıdemli: `#1565c0` (Mavi)
- Orta: `#6b5bd2` (Mor)
- Yeni: `#c2185b` (Pembe/Kırmızı)

### Alan Renkleri (Kimlik)
- Yeşil Alan: `#4caf50`
- Sarı Alan: `#ff9800`
- Kırmızı Alan: `#f44336`

---

## 3. Tipografi

| Eleman | Font | Boyut | Ağırlık | Renk |
|--------|------|-------|---------|------|
| Sayfa başlığı | sans-serif | 16px | 600 | `#1a1a2e` |
| Kart başlığı | sans-serif | 14px | 600 | `#1a1a2e` |
| Kart alt metni | sans-serif | 11px | 400 | `#6b6b7b` |
| Tablo başlığı | monospace | 10px | 600 | `#9a9aa8` |
| Tablo hücresi | sans-serif | 12-13px | 400-500 | `#1a1a2e` |
| Sayısal veri | monospace | 12-13px | 600 | `#1a1a2e` |
| Badge | sans-serif | 11px | 500 | grup rengine göre |
| Stepper adım | sans-serif | 12px | 500 | `#6b6b7b` / `#1a1a2e` |

---

## 4. Ekran Haritası

### 4.1 Dashboard (Ana Sayfa)
- **Sol üst**: Logo + "Nöbet Planlama Merkezi" + "Acil Servis Vardiya Optimizasyonu"
- **Sağ üst**: Aktif ay pill (örn: "Ağustos 2026")
- **Navigasyon**: Dashboard | Yeni Plan | Kurum Ayarları
- **İçerik**:
  - 3 sütunlu plan kartları: Hazır / Oluşturulmadı / Geçmiş
  - Her kart: Ay adı, personel/alan/vardiya özet, ihlal sayısı, çözüm süresi
  - Kart aksiyonları: İncele / Excel / Plan Oluştur
  - Alt kısım: "Yeni Plan Oluştur" CTA (büyük, dashed border)

### 4.2 Yeni Plan — Stepper Akışı

#### Adım 1: Ekip
- **Tablo**: Kişi | Kıdem | Hedef | Çalışabildiği Alanlar | Vardiyalar | Not
- **Satır**: Avatar (baş harfler) + İsim + Badge (kıdem) + Sayı input + Metin
- **Alt**: "+ Kişi Ekle" (dashed), "Hedefleri Otomatik Hesapla"
- **Alt grid**: Sol — Birlikte/Ayrı tutulacak kişiler listesi. Sağ — Kıdem grupları özet.

#### Adım 2: İzinler
- **Başlık**: "İzinler ve Tercihler · Ağustos 2026"
- **Açıklama**: "Gün numaralarını virgülle, aralıkları tire ile yaz. Örnek: 5-9, 14, 22."
- **Kişi kartları** (accordion gibi ama tek sayfa):
  - Kişi adı + kıdem badge + hedef
  - 3 sütun: İzinli Günler (input) | Tercih Ettiği Günler (input) | Bloklu Gün (input)
  - **Ay şeridi**: 31 küçük kare. İzinli = kırmızı, Tercih = açık mavi, Boş = gri
  - Alt metin: "5 izinli gün · 3 tercih · kalan uygun gün 23"
- **Uyarı banner**: "7 Ağustos'ta 4 kişi izinli — o gün kadro darlaşıyor"

#### Adım 3: Kurallar
- **İki sütun**:
  - **Sol — Kesin Kurallar**:
    - Arka arkaya iki gün nöbet olmaz → Toggle
    - Günaşırı nöbet sınırı → Segmented (1 / 2 / 3)
    - Her vardiyada en az 1 kişi → Toggle
    - İki nöbet arası en az 12 saat → Segmented (8 / 12 / 24)
  - **Sağ — Tercihler**:
    - Hafta sonu dengesi → Az / Orta / Çok
    - Resmi tatiller → Az / Orta / Çok
    - Nöbetler arası 2 gün boşluk → Az / Orta / Çok
    - Tercih edilen günler → Az / Orta / Çok
    - Çalışma saati dengesi → Az / Orta / Çok
- **Alt**: "Hazır profil: Dengeli · Adalet odaklı · Dinlenme odaklı"
- **Bilgi banner**: "Şu anki kurallarla 10 kişi 93 nöbeti karşılıyor..."

#### Adım 4: Çizelge (Sonuç)
- **Başarı banner**: Yeşil tik + "Çizelge Oluşturuldu" + özet metin
- **Metric kartları** (4 sütun): Toplam Nöbet | İhlal | Hedef Sapması | Esnek İhlal
- **İki sütun**:
  - Sol: Haftalık takvim görünümü (7 sütun grid). Her gün: numara + gün adı + nöbetçi listesi (renkli nokta + kısa isim)
  - Sağ: Kişi başı dağılım bar chart (hedef çizgisi ile)
- **Uyarılar**: Sarı banner'lar ("Hafta sonu dağılımı eşit değil...")
- **Bilgi**: Yeşil banner ("Ardışık gün yasağı · ihlal yok...")
- **Aksiyon**: "Kuralları Değiştir", "Excel İndir", "Dashboard'a Dön"

### 4.3 Kurum Ayarları
- **Navigasyon**: Dashboard | Yeni Plan | Kurum Ayarları (aktif)
- **İçerik**:
  - Alanlar kartı: Renk noktası + Alan adı + Kontenjan + Min personel + Vardiyalar
  - Vardiyalar kartı: Renk noktası + Vardiya adı + Saat aralığı + Süre + Min personel
  - Kıdem grupları kartı: Renk noktası + Grup adı + Hedef nöbet

---

## 5. Streamlit Bileşen Eşlemesi

| Tasarım Elemanı | Streamlit Bileşeni | Notlar |
|-----------------|-------------------|--------|
| Kart | `st.container` + `st.markdown` CSS border | CSS injection gerekli |
| Tablo | `st.data_editor` | Inline düzenleme için ideal |
| Toggle | `st.toggle` | Stil CSS ile override edilebilir |
| Segmented (Az/Orta/Çok) | `st.segmented_control` (v1.44+) veya `st.radio` horizontal | |
| Metric | `st.metric` veya custom `st.columns` + `st.markdown` | Custom daha esnek |
| Stepper | `st.session_state.step` + custom HTML/progress | `st.progress` basit versiyon |
| Ay şeridi (31 gün) | `st.columns(7)` hafta hafta veya `st.columns(10)` gruplar | 31 sütun mobilde çöküş yapar |
| Takvim grid | Custom HTML `st.markdown` + CSS grid | 7 sütun güvenli |
| Bar chart | `st.bar_chart` veya `matplotlib` + `st.pyplot` | Hedef çizgisi için matplotlib |
| Banner/Alert | `st.info`, `st.warning`, `st.success` + CSS override | Renkleri palette uygun ayarla |
| Input | `st.text_input`, `st.number_input` | Border-radius CSS ile |
| Button | `st.button` | Primary/Secondary ayrımı CSS ile |

---

## 6. CSS Injection Şablonu

```python

import streamlit as st

st.set_page_config(
    page_title="Nöbet Planlayıcı",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #f5f3f0; }
    .main .block-container { padding: 2rem 3rem; max-width: 1100px; }

    .card {
        background: #ffffff;
        border: 1px solid #e8e5e0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .badge-kidem-1 {
        background: #e3f2fd;
        color: #1565c0;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 500;
    }

    .stepper { display: flex; align-items: center; gap: 8px; margin-bottom: 24px; }
    .step-circle {
        width: 28px; height: 28px; border-radius: 50%;
        border: 2px solid #e8e5e0;
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 600;
    }
    .step-circle.done { background: #2e7d32; border-color: #2e7d32; color: #fff; }
    .step-circle.active { background: #1a1a2e; border-color: #1a1a2e; color: #fff; }

    .stDataFrame th {
        background: #faf9f7 !important;
        font-family: monospace !important;
        font-size: 10px !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #9a9aa8 !important;
    }

    .stTextInput input, .stNumberInput input {
        border-radius: 6px !important;
        border: 1px solid #e8e5e0 !important;
    }

    .stButton button[kind="primary"] {
        background: #1a1a2e !important;
        color: #fff !important;
        border-radius: 10px !important;
    }
    .stButton button[kind="secondary"] {
        background: #fff !important;
        color: #1a1a2e !important;
        border: 1px solid #e8e5e0 !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

```

---

## 7. Dosya Yapısı Önerisi

```
nobet-planlayici-v2/
├── app.py                    # Ana giriş (Dashboard + Navigasyon)
├── design.py                 # CSS injection + ortak bileşenler
├── pages/
│   ├── dashboard.py          # Dashboard ekranı
│   ├── plan_ekip.py          # Adım 1: Ekip
│   ├── plan_izinler.py       # Adım 2: İzinler
│   ├── plan_kurallar.py      # Adım 3: Kurallar
│   ├── plan_cizelge.py       # Adım 4: Çizelge
│   └── settings.py           # Kurum Ayarları
├── backend/                  # Mevcut solver kodları
└── docs/
    ├── DESIGN.md             # Bu dosya
    └── IMPLEMENTATION_PLAN.md # Uygulama adımları
```

---

## 8. Kullanıcı Akışı (Happy Path)

1. Kullanıcı uygulamayı açar → Dashboard görür. "Eylül 2026 — Oluşturulmadı" kartı.
2. "Plan Oluştur" butonuna tıklar → Adım 1: Ekip. Personel listesi zaten Kurum Ayarları'ndan gelir.
3. Hedefleri kontrol eder, eksik kişi varsa ekler. "İzinlere Geç".
4. Adım 2: İzinler. Her kişi için izin/tercih günlerini yazar. Alt şerit anında boyanır.
5. "Kurallara Geç". Adım 3: Kesin kurallar zaten açık. Tercihleri "Dengeli" profille ayarlar.
6. "Çizelgeyi Oluştur". Solver çalışır. Adım 4: Sonuç.
7. Metric kartları yeşil. Takvimde her gün nöbetçiler görünür. Bar chart'ta dağılım dengeli.
8. "Excel İndir" veya "Dashboard'a Dön".

---

*Bu doküman, Streamlit implementasyonu için tek kaynak doğru (single source of truth) olarak kullanılmalıdır.*
