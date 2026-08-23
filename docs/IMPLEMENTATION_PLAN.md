# Nöbet Planlayıcı v2 — Streamlit Implementasyon Planı

Bu plan, DESIGN.md spesifikasyonunu Streamlit koduna adım adım dökmek için kullanılır.
Her adım bir dosya/dosya grubu hedefler. Kimi Code CLI ile çalışırken bu planı takip edin.

---

## Ön Hazırlık

### 1. Dosyaları Proje Klasörüne Koy
```
nobet-planlayici-v2/
├── docs/
│   ├── DESIGN.md              ← Bu dosyalar
│   └── IMPLEMENTATION_PLAN.md ←
├── backend/                     ← Mevcut solver kodları (dokunma)
│   ├── models.py
│   ├── solver.py
│   └── ...
├── app.py                       ← YENİ — ana giriş
├── design.py                    ← YENİ — CSS + ortak bileşenler
└── pages/                       ← YENİ — alt sayfalar
```

### 2. Kimi Code CLI Prompt Şablonu
Her adımda Kimi Code CLI'ya şunu söyleyin:

> "docs/DESIGN.md ve docs/IMPLEMENTATION_PLAN.md'yi oku. Şimdi [ADIM_X] yapıyoruz. 
> Mevcut backend kodunu (backend/models.py, backend/solver.py) bozmadan, 
> sadece arayüz katmanını yaz. design.py'deki CSS injection'ı kullan."

---

## Adım 1: Temel Altyapı (design.py + app.py iskeleti)

**Hedef:** CSS injection ve ortak bileşenlerin hazır olması.

**Yapılacaklar:**
- `design.py` oluştur:
  - `inject_css()` fonksiyonu: DESIGN.md Bölüm 6'daki CSS'yi enjekte eder
  - `render_stepper(step, total)` fonksiyonu: Stepper HTML'i döner
  - `render_card(title, content)` fonksiyonu: Kart wrapper
  - `render_badge(text, color_class)` fonksiyonu: Kıdem badge'leri
  - Renk sabitleri: `COLORS = {...}` dict
- `app.py` oluştur:
  - `st.set_page_config` (wide, collapsed sidebar)
  - `inject_css()` çağrısı
  - Üst navigasyon: Dashboard / Yeni Plan / Kurum Ayarları (st.tabs veya st.radio)
  - `st.session_state.page` yönetimi

**Kimi Code CLI Prompt:**
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md oku.
Adım 1: design.py ve app.py iskeletini oluştur.
design.py'de CSS injection, stepper renderer, card renderer, badge renderer olsun.
app.py'de sayfa navigasyonu (Dashboard/Yeni Plan/Kurum Ayarları) ve session_state yönetimi olsun.
Backend dosyalarına dokunma.
```

---

## Adım 2: Dashboard Ekranı

**Hedef:** Kullanıcı açılışta plan kartlarını görsün.

**Yapılacaklar:**
- `pages/dashboard.py` oluştur:
  - `show_dashboard()` fonksiyonu
  - 3 sütunlu grid: Hazır / Oluşturulmadı / Geçmiş plan kartları
  - Her kart: st.container + CSS card class + içerik
  - Kart aksiyon butonları: "İncele", "Excel", "Plan Oluştur"
  - Alt CTA: "Yeni Plan Oluştur" dashed card
  - `st.session_state` ile sayfa geçişi: Yeni Plan'a tıklayınca `page = "plan"`, `step = 0`

**Veri Kaynağı:**
- Şimdilik mock data (hardcoded dict listesi).
- İleride backend'den plan geçmişi çekilecek.

**Kimi Code CLI Prompt:**
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md oku.
Adım 2: pages/dashboard.py oluştur.
3 sütunlu plan kartları (Hazır/Oluşturulmadı/Geçmiş).
Her kart: ay adı, personel sayısı, alan/vardiya sayısı, ihlal, çözüm süresi.
Butonlar: İncele, Excel, Plan Oluştur.
Alt kısımda büyük "Yeni Plan Oluştur" CTA.
design.py'deki card ve badge fonksiyonlarını kullan.
```

---

## Adım 3: Adım 1 — Ekip (plan_ekip.py)

**Hedef:** Personel listesi, kıdem, hedef, alan/vardiya seçimi.

**Yapılacaklar:**
- `pages/plan_ekip.py` oluştur:
  - `show_plan_ekip()` fonksiyonu
  - Stepper render (step=1, total=4)
  - `st.data_editor` ile personel tablosu:
    - Kolonlar: İsim, Kıdem (selectbox), Hedef (number), Alanlar (multiselect), Vardiyalar (multiselect), Not
  - Alt: "+ Kişi Ekle" butonu (yeni boş satır ekler)
  - "Hedefleri Otomatik Hesapla" butonu (kıdem grubunun ortalamasını dağıtır)
  - Alt grid (2 sütun):
    - Sol: Birlikte/Ayrı tutulacak kişiler listesi (compact)
    - Sağ: Kıdem grupları özet (renkli dot + sayı + hedef)
  - "İzinlere Geç →" butonu (session_state.step = 2)

**Veri Kaynağı:**
- Kurum Ayarları'ndan personel listesi ve kıdem grupları.
- Şimdilik mock data, sonra backend entegrasyonu.

**Kimi Code CLI Prompt:**
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md oku.
Adım 3: pages/plan_ekip.py oluştur.
st.data_editor ile personel tablosu: İsim, Kıdem (dropdown), Hedef (sayı), 
Alanlar (multiselect), Vardiyalar (multiselect), Not.
"+ Kişi Ekle" butonu yeni satır eklesin.
"Hedefleri Otomatik Hesapla" butonu kıdem ortalamasını dağıtsın.
Alt kısımda 2 sütun: sol eşleşme kuralları listesi, sağ kıdem grupları özet.
Stepper göster (1/4).
```

---

## Adım 4: Adım 2 — İzinler (plan_izinler.py)

**Hedef:** Her personel için izin/tercih girişi + ay şeridi geri bildirimi.

**Yapılacaklar:**
- `pages/plan_izinler.py` oluştur:
  - `show_plan_izinler()` fonksiyonu
  - Stepper render (step=2, total=4)
  - Her personel için expander veya st.container (card) içinde:
    - Kişi adı + kıdem badge + hedef
    - 3 sütun: İzinli Günler (text_input), Tercih Günleri (text_input), Bloklu Gün (text_input)
    - **Ay şeridi**: 7 hafta × 7 gün = 49 kare (ayın günleri kadar). 
      - İzinli = kırmızı kare, Tercih = açık mavi kare, Boş = gri kare
      - Streamlit'te `st.columns(7)` ile hafta hafta göster
    - Alt metin: "X izinli gün · Y tercih · kalan uygun gün Z"
  - Uyarı banner: Eğer bir günde çok kişi izinliyse st.warning
  - "← Ekip" ve "Kurallara Geç →" butonları

**Önemli Not:**
- 31 sütunlu tek satır yerine 7 hafta × 7 gün grid daha sağlıklı.
- Her hafta bir `st.container` + `st.columns(7)` ile gösterilir.

**Kimi Code CLI Prompt:**
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md oku.
Adım 4: pages/plan_izinler.py oluştur.
Her personel için bir card içinde:
- İzinli Günler (text_input), Tercih Günleri (text_input), Bloklu Gün (text_input)
- Altında hafta-hafta 7x7 kare şerit. İzinli=kırmızı, Tercih=açık mavi, Boş=gri.
- st.columns(7) ile hafta satırları oluştur.
- Eğer bir günde N kişi izinliyse st.warning banner.
- Stepper (2/4) + Geri/İleri butonları.
```

---

## Adım 5: Adım 3 — Kurallar (plan_kurallar.py)

**Hedef:** Kesin kurallar (toggle) + Tercihler (segmented) + Hazır profiller.

**Yapılacaklar:**
- `pages/plan_kurallar.py` oluştur:
  - `show_plan_kurallar()` fonksiyonu
  - Stepper render (step=3, total=4)
  - 2 sütunlu layout:
    - **Sol — Kesin Kurallar** (st.container card):
      - Arka arkaya iki gün nöbet olmaz → `st.toggle`
      - Günaşırı nöbet sınırı → `st.segmented_control` (1/2/3) veya `st.radio` horizontal
      - Her vardiyada en az 1 kişi → `st.toggle`
      - İki nöbet arası en az 12 saat → `st.segmented_control` (8/12/24)
      - Her kuralın altında 1 satır açıklama (st.caption)
    - **Sağ — Tercihler** (st.container card):
      - Hafta sonu dengesi → Az/Orta/Çok
      - Resmi tatiller → Az/Orta/Çok
      - Nöbetler arası 2 gün boşluk → Az/Orta/Çok
      - Tercih edilen günler → Az/Orta/Çok
      - Çalışma saati dengesi → Az/Orta/Çok
      - Her tercihin altında 1 satır açıklama
  - Alt: Hazır profil butonları: "Dengeli" (aktif), "Adalet odaklı", "Dinlenme odaklı"
    - Tıklayınca tercih segmentlerini otomatik ayarlar
  - Bilgi banner: "Şu anki kurallarla X kişi Y nöbeti karşılıyor..."
  - "← İzinler" ve "Çizelgeyi Oluştur" butonları

**Backend Eşleme:**
- Az/Orta/Çok → backend'deki sayısal ağırlıklara (w_cuma, w_iki_gun_bosluk vb.) map edilecek.
- Şimdilik session_state içinde dict olarak tut, solver entegrasyonu sonraki adımda.

**Kimi Code CLI Prompt:**
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md oku.
Adım 5: pages/plan_kurallar.py oluştur.
2 sütun: sol Kesin Kurallar (toggle + segmented), sağ Tercihler (segmented Az/Orta/Çok).
Her kural/tercih altında 1 satır açıklama (st.caption).
Alt kısımda hazır profil butonları: Dengeli, Adalet odaklı, Dinlenme odaklı.
Bilgi banner: "Şu anki kurallarla X kişi Y nöbeti karşılıyor..."
Stepper (3/4) + Geri/Çizelgeyi Oluştur butonları.
```

---

## Adım 6: Adım 4 — Çizelge (plan_cizelge.py)

**Hedef:** Solver sonucunu göster: metric kartları, takvim, bar chart, uyarılar.

**Yapılacaklar:**
- `pages/plan_cizelge.py` oluştur:
  - `show_plan_cizelge()` fonksiyonu
  - Stepper render (step=4, total=4) — son adım
  - Başarı banner: Yeşil tik + "Çizelge Oluşturuldu" + özet metin
  - 4 metric kart: Toplam Nöbet, İhlal, Hedef Sapması, Esnek İhlal
    - `st.columns(4)` + custom card CSS
    - Metric bar (progress çubuğu) her kartın altında
  - 2 sütun:
    - **Sol — Haftalık Takvim** (st.container):
      - 7 sütun grid (Pzt-Sal-Çar-Per-Cum-Cts-Paz)
      - Her hücre: gün numarası + gün adı + nöbetçi listesi
      - Nöbetçi: renkli dot (kıdem rengine göre) + kısa isim
      - Hafta sonları farklı arka plan (CSS class)
    - **Sağ — Kişi Başı Dağılım** (st.container):
      - `st.bar_chart` veya `matplotlib` bar chart
      - Her bar = kişi, yükseklik = nöbet sayısı
      - Hedef çizgisi (horizontal line) göster
  - Uyarı banner'ları (st.warning): "Hafta sonu dağılımı eşit değil..."
  - Bilgi banner'ı (st.success): "Ardışık gün yasağı · ihlal yok..."
  - Aksiyon butonları: "Kuralları Değiştir", "Excel İndir", "Dashboard'a Dön"

**Backend Entegrasyonu:**
- Bu adımda backend solver'ı çağır.
- `backend/solver.py`'den `solve()` fonksiyonunu çağır, sonuçları al.
- Sonuçları session_state'e kaydet.

**Kimi Code CLI Prompt:**
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md oku.
@backend/solver.py @backend/models.py oku.
Adım 6: pages/plan_cizelge.py oluştur.
Başarı banner + 4 metric kart (Toplam Nöbet, İhlal, Hedef Sapması, Esnek İhlal).
Sol: Haftalık takvim grid (7 sütun). Her gün: numara, gün adı, nöbetçi listesi (renkli dot + kısa isim).
Sağ: Kişi başı dağılım bar chart (matplotlib veya st.bar_chart). Hedef çizgisi göster.
Uyarı ve bilgi banner'ları.
"Kuralları Değiştir", "Excel İndir", "Dashboard'a Dön" butonları.
Backend solver'ı çağır, sonuçları göster.
```

---

## Adım 7: Kurum Ayarları (settings.py)

**Hedef:** Alan, vardiya, kıdem tanımları. Aylık akışın dışında.

**Yapılacaklar:**
- `pages/settings.py` oluştur:
  - `show_settings()` fonksiyonu
  - 3 sekme veya 3 kart: Alanlar / Vardiyalar / Kıdem Grupları
  - **Alanlar**: `st.data_editor` ile tablo — İsim, Renk (color_picker), Kontenjan (min-max), Min Personel, Vardiyalar (multiselect), Kıdem Kuralı
  - **Vardiyalar**: Kartlar halinde — İsim, Başlangıç Saati, Bitiş Saati, Süre (otomatik), Min Personel
  - **Kıdem Grupları**: Tablo — İsim, Renk, Hedef Nöbet
  - "Kaydet" butonu — JSON veya pickle olarak kaydet
  - "Aya Dön" butonu

**Kimi Code CLI Prompt:**
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md oku.
Adım 7: pages/settings.py oluştur.
3 bölüm: Alanlar (data_editor tablo), Vardiyalar (kartlar), Kıdem Grupları (tablo).
Her alan/vardiya/kıdem için renk seçici (color_picker).
Kaydet butonu JSON olarak kaydetsin.
```

---

## Adım 8: Navigasyon ve State Yönetimi (app.py finalize)

**Hedef:** Tüm sayfalar birbirine bağlı, akışlı çalışsın.

**Yapılacaklar:**
- `app.py` güncelle:
  - `st.session_state` yapısı:
    ```python
    {
        "page": "dashboard",  # dashboard | plan | settings
        "plan_step": 0,      # 0-3 (Ekip, İzinler, Kurallar, Çizelge)
        "personel": [],      # Liste
        "izinler": {},       # {isim: {izin: [], tercih: [], bloklu: []}}
        "kurallar": {},      # {kural: değer}
        "sonuc": None,       # Solver sonucu
        "kurum": {}          # Alanlar, vardiyalar, kıdemler
    }
    ```
  - Sayfa yönlendirme mantığı:
    - `page == "dashboard"` → `pages.dashboard.show()`
    - `page == "plan"` → `plan_step`'e göre ilgili sayfa
    - `page == "settings"` → `pages.settings.show()`
  - `st.rerun()` kullanımını minimize et. Sadece sayfa değişiminde.

**Kimi Code CLI Prompt:**
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md oku.
Adım 8: app.py'yi finalize et.
Tüm sayfaları (dashboard, plan_ekip, plan_izinler, plan_kurallar, plan_cizelge, settings) 
app.py'de birleştir. session_state yapısını kur: page, plan_step, personel, izinler, kurallar, sonuc, kurum.
Sayfa geçişleri akıcı olsun, st.rerun() sadece gerekli yerlerde.
```

---

## Adım 9: Excel Export ve Son Dokunuşlar

**Hedef:** Çizelge sonucunu Excel'e aktar. Hata kontrolü.

**Yapılacaklar:**
- `pages/plan_cizelge.py`'ye Excel export fonksiyonu ekle:
  - `openpyxl` veya `xlsxwriter` ile .xlsx oluştur
  - Sayfa 1: Takvim görünümü (günler sütun, personeller satır)
  - Sayfa 2: Kişi başı özet
  - `st.download_button` ile indirme
- Hata kontrolü:
  - Solver çözüm bulamazsa: st.error + "Hangi kuralı gevşetmelisiniz?" önerileri
  - Boş personel listesi: st.warning + "Önce Kurum Ayarları'ndan personel ekleyin"

**Kimi Code CLI Prompt:**
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md oku.
Adım 9: Excel export fonksiyonu ekle (plan_cizelge.py'ye).
openpyxl ile .xlsx oluştur: Sayfa 1 takvim, Sayfa 2 özet.
Solver hatası durumunda kullanıcıya hangi kuralı gevşetmesi gerektiğini öneren mesaj göster.
```

---

## Kimi Code CLI Kullanım İpuçları

### Dosya Referans Verme
Kimi Code CLI'da dosya referans vermek için:
```
@docs/DESIGN.md oku ve Bölüm 4.2'deki İzinler ekranını implemente et.
```

### Çoklu Dosya
```
@docs/DESIGN.md @docs/IMPLEMENTATION_PLAN.md @design.py oku. 
Şimdi plan_izinler.py'deki ay şeridini hafta-hafta 7x7 grid olarak değiştir.
```

### Mevcut Kodu Bozmadan
```
Mevcut backend/ klasöründeki dosyalara dokunma. Sadece arayüz katmanını değiştir.
```

### Geri Alma
Kimi Code CLI değişiklikleri git commit ile yapar. Eğer bir adım hatalı giderse:
```
/git log
/git revert HEAD
```

---

*Bu plan, DESIGN.md spesifikasyonunun kod karşılığıdır. Her adım bağımsız çalışabilir.*
