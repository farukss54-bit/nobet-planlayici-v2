# 🏥 Nöbet Planlayıcı v2

> Hastane acil servisleri için akıllı nöbet çizelgesi optimizasyon sistemi

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io/)
[![OR-Tools](https://img.shields.io/badge/OR--Tools-9.15-brightgreen.svg)](https://developers.google.com/optimization)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Proje Özeti

**Nöbet Planlayıcı v2**, hastane acil servislerinde aylık nöbet çizelgelerini otomatik olarak oluşturan bir Python web uygulamasıdır. Google OR-Tools CP-SAT kısıt programlama çözücüsü kullanarak karmaşık personel kısıtlarını, izinleri, birlikte/ayrı çalışma kurallarını ve vardiya kısıtlarını optimize eder.

### ✨ Temel Özellikler

- 🎯 **Akıllı Optimizasyon**: CP-SAT constraint solver ile optimal çizelge üretimi
- 👥 **Esnek Personel Yönetimi**: Kıdem grupları, alan yetkinlikleri, vardiya kısıtları
- 📅 **Çoklu Mod Desteği**: Tek alan, çoklu alan, vardiya bazlı planlama
- 🔒 **Kısıt Yönetimi**: Birlikte/ayrı tutma kuralları, izin yönetimi, tatil dengesi
- 📊 **Gelişmiş Raporlama**: CSV/Excel export, istatistikler, çözüm analizi
- 🧪 **Test Edilen**: 144 pytest test case'i ile doğrulanmış
- 🎨 **Modern UI**: Streamlit tabanlı kullanıcı dostu arayüz

## 🛠️ Teknoloji Yığını

| Teknoloji | Kullanım Alanı |
|-----------|----------------|
| **Python 3.10+** | Ana programlama dili |
| **Streamlit** | Web tabanlı kullanıcı arayüzü |
| **Google OR-Tools** | CP-SAT constraint programming solver |
| **pandas** | Veri işleme ve tablo operasyonları |
| **openpyxl** | Excel export |
| **pytest** | Unit ve integration testleri |

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Python 3.10 veya üzeri
- pip paket yöneticisi

### Kurulum

```bash
# Depoyu klonlayın
git clone https://github.com/farukss54-bit/nobet-planlayici-v2.git
cd nobet-planlayici-v2

# Sanal ortam oluşturun (önerilir)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı çalıştırın
streamlit run app.py
```

Uygulama otomatik olarak tarayıcınızda `http://localhost:8501` adresinde açılacaktır.

## 📖 Kullanım

### 1. Personel Tanımlama
- **Kişiler** sekmesinden personel ekleyin
- Kişi bazlı hedef nöbet sayıları belirleyin
- Otomatik hedef hesaplama özelliğini kullanın

### 2. Kıdem ve Alan Yönetimi
- **Kıdem** sekmesinden kıdem grupları oluşturun
- **Alanlar** sekmesinden çalışma alanlarını tanımlayın
- Alan yetkinliklerini ve kıdem kurallarını ayarlayın

### 3. Vardiya ve Kısıtlar
- **Vardiyalar** sekmesinden vardiya tiplerini ekleyin
- **İzinler** sekmesinden izin günlerini işaretleyin
- **Eşleşmeler** sekmesinden birlikte/ayrı tutma kurallarını belirleyin

### 4. Çizelge Oluşturma
- **Çözüm** sekmesine gidin
- "Nöbeti Oluştur" butonuna tıklayın
- Sonucu tablo, CSV veya Excel olarak indirin

## 📁 Proje Yapısı

```
nobet-planlayici-v2/
├── app.py                      # Ana Streamlit uygulaması
├── solver.py                   # CP-SAT solver ve optimizasyon motoru
├── models.py                   # Veri modelleri (dataclass'lar)
├── config.py                   # Solver konfigürasyonu ve ağırlıklar
├── storage.py                  # JSON tabanlı kalıcılık katmanı
├── utils.py                    # Yardımcı fonksiyonlar
├── scenarios.py                # Test senaryoları ve veri üretimi
├── streamlit_integration.py   # Demo modu entegrasyonu
├── tabs/                       # UI sekme modülleri
│   ├── personel_tab.py
│   ├── kidem_tab.py
│   ├── alanlar_tab.py
│   ├── vardiyalar_tab.py
│   ├── izinler_tab.py
│   ├── eslesmeler_tab.py
│   └── cozum_tab.py
├── tests/                      # Pytest test suite
│   ├── test_solver_properties.py
│   ├── test_baseline.py
│   └── test_g*.py             # Faz bazlı testler
├── docs/                       # Teknik dökümanlar
├── requirements.txt            # Python bağımlılıkları
└── README.md                   # Bu dosya
```

## 🧪 Test

Proje, 144 pytest test case'i içeren kapsamlı bir test suite'ine sahiptir:

```bash
# Tüm testleri çalıştır
pytest

# Hızlı testler (yavaş testleri atla)
pytest -m "not yavas"

# Detaylı çıktı ile
pytest -v

# Belirli bir test dosyası
pytest tests/test_solver_properties.py
```

## 🎯 Algoritmik Yaklaşım

### Kısıt Programlama (CP-SAT)

Proje, Google OR-Tools CP-SAT solver kullanarak nöbet çizelgesi optimizasyonunu gerçekleştirir:

#### Hard Constraints (Kesin Kurallar)
- ✅ Ardışık gün yasağı
- ✅ İzin günleri kısıtı
- ✅ Alan yetkinliği kontrolü
- ✅ Vardiya uyumluluk kuralları
- ✅ Minimum personel gereksinimleri

#### Soft Constraints (Tercih Edilen Kurallar)
- 📊 Hedef nöbet sayısına yakınlık
- 🔄 Hafta sonu ve tatil dengesi
- 🤝 Birlikte/ayrı tutma tercihleri
- ⚖️ Çalışma saati dengesi

### Optimizasyon Hedefi

Solver, soft constraint'lerin ağırlıklı toplamını minimize ederek en adil ve dengeli çizelgeyi bulmaya çalışır:

```python
minimize: Σ (hedef_sapması + hafta_sonu_dengesizliği + 
             tatil_dengesizliği + ayrı_tutma_cezası + ...)
```

## 📊 Performans

- **Ortalama Çözüm Süresi**: 5-30 saniye (18 personel, 31 gün, 2 alan, 3 vardiya)
- **Başarı Oranı**: %95+ (feasible senaryolarda)
- **Determinizm**: Aynı girdi → Aynı çıktı (sabit seed ile)
- **Ölçeklenebilirlik**: 50+ personel, çoklu alan/vardiya desteği

## 🔧 Geliştirme

### Kod Stili
- Tüm kod yorumları ve docstring'ler Türkçe
- Değişken isimleri snake_case
- Dataclass'lar JSON serialization destekli
- Type hints kullanımı

### Katkıda Bulunma
1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'feat: Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📝 Faz Geçmişi

Proje, iteratif faz metodolojisi ile geliştirilmiştir:

- **Faz 0-1**: Solver çekirdeği sertleştirme (soft hedefler, günaşırı düzeltmesi)
- **Faz 2**: UI dürüstlük katmanı (girdi doğrulama, hata görünürlüğü)

Detaylı faz dökümanları `docs/` dizininde mevcuttur.

## 🎓 Öğrenilen Dersler

Bu proje geliştirilirken:
- ✅ Karmaşık constraint programming problemleri
- ✅ CP-SAT solver optimizasyonu ve tuning
- ✅ Streamlit ile interaktif web uygulamaları
- ✅ Property-based testing ve solver verification
- ✅ JSON tabanlı veri persistence
- ✅ Kullanıcı deneyimi odaklı tasarım

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 👤 Geliştirici

**Faruk Saraç**
- 📧 Email: farukss54@gmail.com
- 💼 GitHub: [@farukss54-bit](https://github.com/farukss54-bit)

## 🙏 Teşekkürler

- Google OR-Tools ekibine constraint solver için
- Streamlit topluluğuna harika framework için
- Tüm test kullanıcılarına geri bildirimler için

---

<div align="center">
  <sub>⭐ Projeyi beğendiyseniz yıldız vermeyi unutmayın!</sub>
</div>
