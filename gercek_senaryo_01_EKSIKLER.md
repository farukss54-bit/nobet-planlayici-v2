# gercek_senaryo_01 — İfade Edilemeyen Kurallar ve Modelleme Kararları

Senaryonun istediği ama mevcut solver şemasının İFADE EDEMEDİĞİ kurallar.
Bunlar fikstürde YOK veya yaklaşık kodlandı; düzeltme DENENMEDİ (talimat gereği).
Her madde ilgili faz/görevle etiketli.

## İfade edilemeyenler

1. **"Sarıda her gün en az 1 K1 VEYA K2"** — birleşim kardinalitesi
   (`sum(x, p ∈ K1∪K2) ≥ 1`) desteklenmiyor. Kodlanmadı; Sarı'da hiçbir
   kıdem kuralı yok. → Faz 5 (kıdem birleşim kuralları)

2. **"Kırmızıda en az 1 K2 VEYA K3"** — aynı sebep. Kodlanmadı; Kırmızı'da
   yalnızca `K1 min 1` var. → Faz 5

3. **Günaşırı: K1-K2 için ayda max 2, K3-K4 serbest** — kişi/grup bazlı
   günaşırı limiti yok, limit global. Yaklaşım: global `max_gunasiri=2`.
   Yan etki: K3-K4 gereğinden kısıtlı (K4 hedef 11, günaşırı-2 teorik
   tavanı da 11 → kasıtlı stres noktası). Ek sorun: G1.1 sonrası günaşırı
   limiti vardiya modunda TAMAMEN devre dışı → K1-K2 kuralı o zaman da
   ifade edilemeyecek. → Faz 5 (grup bazlı günaşırı, vardiya modu
   semantiğiyle birlikte yeniden tasarım)

4. **Hafta sonu dengesi kıdem grubu İÇİNDE** — denge global min-max.
   8 hedefli K1 ile 11 hedefli K4 aynı kefede → kaçınılmaz sabit ceza,
   grup içi adalet ölçülmüyor. → Faz 3 (denge tasarımı) + Faz 5 (grup bazlı)

5. **K1 alan önceliği: "önce Kırmızı, gerekirse Sarı"** — soft alan
   önceliği yok. Yalnızca hard yasak kodlanabildi (K1 ve K2: Yeşil yok).
   → Faz 5 (alan öncelik puanı)

## Yaklaşık kodlananlar / modelleme borçları

6. **"Ardışık gün herkese yasak" + "24s sonrası ≥1 gün dinlenme"** —
   vardiya modunda doğrudan anahtar yok. `minimum_dinlenme_saati=17` ile
   sağlandı: bu vardiya saatleriyle tüm ertesi-gün dinlenmeleri 0/8/16
   saat olduğundan 17 hepsini yasaklar. KIRILGAN: vardiya saatleri
   değişirse kural sessizce delinir. → Faz 2'ye not (doğrulama:
   "ardışık yasak" niyetini dinlenme saatinden türetme, açık anahtar)

7. **16s/8s mesailer için yapay `MesaiDestek` alanı** — mesailer alan
   gerektirmiyor ama 4D model her atamaya alan istiyor. `staffing=0,
   kontenjan=0` yapay alan eklendi. `gunluk_kontenjan=0` mesai
   atamalarına anlamsız sapma cezası üretir (G1.4 sonrası vardiya
   granülaritesinde de sürer). → "Alansız vardiya" kavramı yok — Faz 5
   adayı olarak not

8. **"Kırmızıda 1 adet K1"** — `min 1` olarak yorumlandı (max yok).
   "TAM 1" kastedildiyse `{"min": 1, "max": 1}` yapılmalı. AÇIK SORU.

9. **want_pair'ler `min_k=0`** — mevcut şemada `min_k>0` hard zorunluluk
   demek (Belge 3 bulgu #3); tercih niyeti için 0 verildi → yalnızca
   `w_birlikte_odul=30` ödülü. Bu ağırlık pratikte görünmez (w_tercih=2
   sorunuyla aynı sınıf). → Faz 3 (ağırlık normalizasyonu)

## Beklenen davranış

- **Bugünkü solver:** INFEASIBLE. Muhtemel başat sebepler: günaşırı
  limitinin (2) vardiya moduna sızıp ardışık blokları/K4'ün 11 hedefini
  boğması + hedef tam eşitliği. Teşhisin bunları YAKALAYAMAMASI
  bekleniyor ("belirgin sorun tespit edilemedi") — bu da başlı başına
  bulgu (teşhis kör noktası).
- **Faz 0-1 sonrası:** FEASIBLE + minimal hedef sapması bekleniyor.
  G1.1 (günaşırı vardiyadan çıkar) + G1.3 (soft hedef) + G1.4 (kontenjan
  granülaritesi) üçlüsü bu senaryonun ana düğümlerini çözüyor.
- **EKLENDİ:** Fikstür `tests/fixtures/gercek_senaryo_01.json` olarak
  resmi baseline setine eklendi, `beklenen_durum: FEASIBLE` (Faz 0-1
  sonrası doğrulandı). Test: `tests/test_baseline_gercek_senaryo_01.py`
  (`@pytest.mark.yavas`, ~60s). Not: senaryonun config'i 8 thread
  (pin_search_workers=False) kullandığından CP-SAT paralel araması
  deterministik değil — toplam hedef sapması ölçümü art arda koşularda
  0-16 arasında değişti (status hep FEASIBLE). Bu yüzden test sıkı bir
  denge ölçütü değil, gözlenen en kötü değer + geniş marjla kurulmuş
  kaba bir regresyon tripwire'ı (`toplam_sapma_tavani: 25`) kullanıyor.

## Çalıştırma

```
python calistir_senaryo_01.py            # varsayılan: gercek_senaryo_01.json
python calistir_senaryo_01.py <dosya>    # başka fikstür
```
