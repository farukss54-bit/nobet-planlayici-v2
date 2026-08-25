# SOLVER V3 — FAZ 0-1: Ölçüm Zemini + Kritik Model Bugları

**Durum:** Onaylandı — uygulamaya hazır
**Kapsam:** `solver.py`, `utils.py`, `config.py`, `tests/`
**Kapsam DIŞI (bu fazda DOKUNMA):** `app.py`, `tabs/`, `storage.py`, `scenarios.py`, `models.py`, UI davranışı, senaryo JSON şeması

---

## AGENT ÇALIŞMA PROTOKOLÜ

1. Görevleri **sırayla** yap: G0.1 → G0.2 → G1.1 → G1.2 → G1.3 → G1.4 → G1.5. Sırayı değiştirme, görevleri birleştirme.
2. Her görev **ayrı commit**. Commit mesajı: `[G1.2] kisinin_max_atama: gunasiri-farkinda formul`.
3. Her görev sonunda **rapor** yaz (aşağıdaki format). Rapor yazmadan sonraki göreve geçme.
4. Her görev sonunda: o görevin kabul testleri + `pytest` tüm suite + baseline suite (G0.2 sonrası) çalıştır. Kırmızı test varsa sonraki göreve geçme; düzelt veya raporda "BLOKE" olarak işaretle ve dur.
5. Bir kabul testini geçirmek için **testin kendisini zayıflatma** (assert silme, tolerans genişletme, skip ekleme yasak). Test yanlışsa raporda gerekçesiyle öner, onay bekle.
6. "Dokunma" listesindeki dosyalarda değişiklik gerekirse: yapma, raporda gerekçesiyle belirt ve dur.
7. Kod, yorum, hata mesajları, test isimleri: **Türkçe** (mevcut proje konvansiyonu).
8. Bu dosyada tanımlanmayan bir iyileştirme fark edersen: yapma, rapora "ÖNERİ" olarak ekle.

### Rapor formatı (her görev için)

```
## RAPOR [görev no]
- Yapılan: (2-4 cümle)
- Değişen dosyalar ve satırlar:
- Eklenen testler:
- Test sonucu: X geçti / Y kaldı (kalan varsa neden)
- Baseline etkisi: (hangi fikstürlerin durumu değişti)
- MANUEL TEST DİREKTİFİ: (kullanıcının Streamlit arayüzünde elle
  doğrulaması gereken bir şey varsa adım adım yaz; yoksa "yok")
- ÖNERİ / BLOKE: (varsa)
```

---

## ARKA PLAN — NEDEN BU DEĞİŞİKLİKLER

Bu faz, vardiya modunun "neredeyse her zaman infeasible" olmasının kod
incelemesiyle tespit edilmiş kök nedenlerini hedefler:

1. **Günaşırı limiti vardiya moduna sızıyor** ve 4+ ardışık çalışma
   gününü gizlice yasaklıyor (G1.1).
2. **Doğrulama fonksiyonu `kisinin_max_atama` günaşırı limitini
   bilmiyor**: 31 gün için 16 diyor, gerçek üst sınır 11. 12-16 arası
   hedefler doğrulamadan geçip açıklanamaz INFEASIBLE üretiyor (G1.2).
3. **Hedef kısıtı tam eşitlik** (`toplam == hedef`): en küçük çakışmada
   plan hiç çıkmıyor. Ayrıca hedef=0 "yasak" anlamına geliyor ve hedefi
   girilmemiş kişi sessizce sıfıra kilitleniyor (G1.3).
4. **Soft kontenjan kısıtı yanlış granülaritede**: hard staffing vardiya
   başına (DOĞRU — kapsama semantiği), soft kontenjan gün toplamına
   bakıyor ve kaçınılmaz sabit ceza üretiyor; `max_kontenjan` gün
   seviyesinde tavan olduğu için garantili INFEASIBLE senaryoları var (G1.4).

**Semantik karar (kullanıcı onaylı):** `minimum_staffing` = "o alanda
HER VARDİYADA bulunması gereken minimum kişi" (kapsama semantiği).
Hard staffing kısıtı bu haliyle DOĞRUDUR, değiştirilmeyecek.

---

## G0.1 — Solver status ve meta bilgisi

**Dosya:** `solver.py` → `_coz_ve_sonuc_al` (~satır 717-729)

**Değişiklik:**
- `solver.Solve(...)` sonrası, dönüş yapısına DOKUNMADAN instance'a meta ekle:

```python
self.cozum_meta = {
    "status": solver.StatusName(status),
    "sure_saniye": solver.WallTime(),
    "objective": solver.ObjectiveValue() if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
    "optimal": status == cp_model.OPTIMAL,
}
```

- INFEASIBLE/UNKNOWN durumunda meta, ValueError raise edilmeden ÖNCE doldurulmalı.
- Mevcut dict dönüş tipi ve yapısı AYNEN korunur. UI bağlantısı bu fazın işi değil.

**Kabul testleri:**
- Çözülebilir küçük senaryo → `solver_instance.cozum_meta["status"] in ("OPTIMAL", "FEASIBLE")`, `sure_saniye > 0`.
- Çözümsüz senaryo → ValueError yükselir VE `cozum_meta["status"] == "INFEASIBLE"`.
- Mevcut tüm testler değişmeden yeşil.

---

## G0.2 — Baseline test fikstürleri

**Dosya:** yeni `tests/fixtures/` + `tests/test_baseline.py`

**Değişiklik:**
- `SolverInput`'u doğrudan kuran JSON fikstür formatı tanımla
  (senaryo şemasından BAĞIMSIZ — `scenarios.py` kullanma).
- Her fikstürde: girdi + `beklenen_durum` alanı (`"FEASIBLE"` / `"INFEASIBLE"`).
- `test_baseline.py`: her fikstürü yükle, çöz, durumu doğrula, süreyi logla.
- Kod incelemesindeki bulguları temsil eden 3 sentetik fikstürü sen oluştur:
  - `baseline_gunasiri_vardiya.json`: vardiya modu, 4 ardışık gün gerektiren
    girdi → bugünkü beklenen: `INFEASIBLE` (G1.1 sonrası `FEASIBLE` olacak)
  - `baseline_hedef_12.json`: nöbet modu, 31 gün, izinsiz, hedef=12 →
    bugünkü beklenen: `INFEASIBLE` (G1.2 sonrası çözüm öncesi ValueError olacak)
  - `baseline_hedef_esitlik.json`: hafif hedef çakışması → bugünkü beklenen:
    `INFEASIBLE` (G1.3 sonrası `FEASIBLE` olacak)
- Fikstürler MEVCUT davranışı sabitler (bugün yeşil olmalı). Sonraki
  görevlerde beklenen durumlar güncellenecek — her güncelleme o görevin
  commit'inde ve raporunda belirtilmeli.

**MANUEL TEST DİREKTİFİ (rapora yaz):** Kullanıcıdan, gerçekte patlamış
2-3 senaryonun girdilerini fikstür formatında eklemesini iste; format
örneğini raporda göster.

**Kabul testi:** `pytest tests/test_baseline.py` yeşil, süreler logda.

---

## G1.1 — Günaşırı limitini nöbet moduna kilitle

**Dosya:** `solver.py` ~satır 222, `config.py` (yorum)

**Değişiklik:**

```python
# ESKİ:
if self.input.config.gunasiri_limit_aktif and self.input.config.max_gunasiri_per_kisi > 0:
# YENİ:
if (not self.input.vardiya_modu
        and self.input.config.gunasiri_limit_aktif
        and self.input.config.max_gunasiri_per_kisi > 0):
```

- `config.py`'da `max_gunasiri_per_kisi` yorumuna ekle:
  "YALNIZCA nöbet modunda uygulanır. Vardiya modunda dinlenme
  kuralları (`minimum_dinlenme_saati`, `max_ardisik_calisma_gunu`) geçerlidir."
- `_iki_gun_bosluk_tercihi` (soft, ~246) BU FAZDA DEĞİŞMEZ.

**Gerekçe:** `_gunasiri_limiti` gün g ve g+2'nin ikisinde de atama olan
çiftleri sayar. Vardiya modunda ardışık günler serbest olduğundan, ardışık
çalışma bloğu İÇİNDEKİ günler de fark-2 çifti oluşturur: 4 ardışık gün =
2 çift > limit(1) → kategorik INFEASIBLE. Bu, `max_ardisik_calisma_gunu=5`
soft limitini ulaşılamaz kılıyordu.

**Kabul testleri:**
- Vardiya modu, 5 ardışık gün atamayı gerektiren fikstür → FEASIBLE.
- `baseline_gunasiri_vardiya.json` beklenen durumu `FEASIBLE` yap → yeşil.
- Nöbet modu: mevcut günaşırı testleri (varsa) + yeni test: 31 günde
  1,3,5 günlerine atama zorlanırsa INFEASIBLE (limit hâlâ çalışıyor).

---

## G1.2 — `kisinin_max_atama` günaşırı-farkında formül

**Dosyalar:** `utils.py` (fonksiyon), çağıranlar: `solver.py` ~267 ve ~829,
`utils.py::hesapla_otomatik_hedef`

**Değişiklik — geriye uyumlu imza genişletmesi:**

```python
def kisinin_max_atama(
    musait_gun_sayisi: int,
    vardiya_modu: bool,
    ardisik_yasak: bool = True,
    takvim_gun_sayisi: int = None,
    gunasiri_limit_aktif: bool = False,
    max_gunasiri: int = 1,
) -> int:
```

- Nöbet modu + ardışık yasak + günaşırı limiti aktif + `takvim_gun_sayisi` verili:

```python
sinir_ardisik = (musait_gun_sayisi + 1) // 2
sinir_gunasiri = (takvim_gun_sayisi - 1 + max_gunasiri) // 3 + 1
return min(sinir_ardisik, sinir_gunasiri)
```

- Diğer tüm durumlarda mevcut davranış AYNEN korunur.
- Docstring'e türetme yazılsın: ardışık yasak → atamalar arası gün farkı ≥ 2;
  günaşırı limiti → fark tam 2 olan çiftlerden en fazla `max_gunasiri` adet;
  n atamanın gerektirdiği açıklık `1 + 2k + 3(n-1-k)` ≤ takvim günü
  (k = kullanılan günaşırı ≤ max_gunasiri). 31 gün, max=1 → 11.
  Bu bir ÜST SINIRDIR; izin günlerinin yerleşimi gerçek maksimumu daha da
  düşürebilir (mevcut formül için de geçerliydi, sözleşme değişmiyor).

**Çağıran güncellemeleri:**
- `solver.py::_hedef_nobet_sayilari` (~267): yeni parametreleri
  `self.gun_sayisi` ve `self.input.config`'ten geçir.
- `solver.py::gelismis_teshis` (~829): fonksiyon imzasına
  `gunasiri_limit_aktif: bool = True, max_gunasiri: int = 1` ekle
  (mevcut config default'larıyla uyumlu), içeride geçir.
- `utils.py::hesapla_otomatik_hedef`: `gun_sayisi`'nı takvim günü olarak
  geçir; `gunasiri_limit_aktif` parametresini fonksiyon imzasına ekle
  (default True), `kisinin_max_atama`'ya ilet.

**Kabul testleri:**
- `kisinin_max_atama(31, False, True, 31, True, 1) == 11`
- `kisinin_max_atama(31, False, True, 31, True, 2) == 12`
- `kisinin_max_atama(31, False, True) == 16`  (geriye uyumluluk)
- `kisinin_max_atama(31, True, True, 31, True, 1) == 31`  (vardiya modunda etkisiz)
- Entegrasyon: nöbet modu, izinsiz 31 gün, hedef=12 → solver çalışmadan
  Türkçe ValueError ("... hedef (12) > maksimum mümkün (11)").
- `baseline_hedef_12.json`: beklenen durumu "ValueError (çözüm öncesi)" yap.

---

## G1.3 — `_hedef_nobet_sayilari` yeniden yazımı

**Dosyalar:** `solver.py` ~255-306, `config.py`

**Config eklemeleri:**

```python
# Hedef sapması cezası. w_alan_kontenjan_sapma (10000) üstü,
# w_vardiya_min_kontenjan (50000) altı olmalı: hedefler denge
# terimlerini domine etmeli ama staffing'i asla ezmemeli.
w_hedef_sapma = 20000
# Cezasız hedef sapması aralığı (±). 0 = tam hedefe en yakın plan.
hedef_tolerans = 0
```

`SolverConfig` dataclass'ına iki alan da eklenir.

**Üç kural (tek fonksiyon):**

1. **Eşitlik → toleranslı soft.** Satır ~291 ve ~306'daki
   `self.model.Add(toplam == hedef)` kalkar. Yerine:

```python
sapma = self.model.NewIntVar(0, self.gun_sayisi, f"hedef_sapma_{p_idx}_{...}")
fark = self.model.NewIntVar(-self.gun_sayisi, self.gun_sayisi, f"hedef_fark_{...}")
self.model.Add(fark == toplam - hedef)
self.model.AddAbsEquality(sapma, fark)
tol = self.input.config.hedef_tolerans
if tol > 0:
    asim = self.model.NewIntVar(0, self.gun_sayisi, f"hedef_asim_{...}")
    self.model.Add(asim >= sapma - tol)
    self.objective_terms.append(asim * self.input.config.w_hedef_sapma)
else:
    self.objective_terms.append(sapma * self.input.config.w_hedef_sapma)
```

   Hem vardiya-bazlı hedef dalında hem eski (toplam) dalda uygulanır.

2. **hedef=0 ≠ yasak.** Satır ~292-296'daki `x == 0` kilit bloğu SİLİNİR.
   hedef=0 artık yalnızca "0'a yakın tut" soft baskısı üretir (1. kuralın
   doğal sonucu). "Bu vardiyada çalışamaz" ifadesinin tek mekanizması
   `personel_vardiya_kisitlari`'dır (halihazırda `_vardiya_kisitlari`
   hard kısıtı, ~334-343).

3. **Hedefsiz kişi sessiz kilitlenmesin.** Else dalında
   `isim not in self.input.hedefler` ise `== hedef(0)` kısıtı KURULMAZ;
   `self.uyarilar` listesine (yoksa `__init__`'te `self.uyarilar = []`
   olarak oluştur) `"{isim}: hedef girilmemiş, serbest bırakıldı"` eklenir.
   `hedefler`'de açıkça 0 girilmiş kişi ise soft 0 hedefi alır (kural 1).

**Ön kontroller KORUNUR:** ~280, ~285-286, ~300-301'deki
`hedef > max_mumkun` ValueError'ları kalır (G1.2 ile artık doğru
formüle dayanıyorlar).

**Kabul testleri:**
- Hedef 15, tolerans 0, çakışmasız → tam 15 (soft ama optimal tam tutturur).
- Hedef 15, hafif çakışma → FEASIBLE + sapma minimal (eski: INFEASIBLE).
- Tolerans 2, hedef 15 → 13-17 arası cezasız (objective'te hedef terimi 0).
- Vardiya hedefi `{“8s”: 0}` olan kişi, 8s staffing'i başka türlü
  dolmuyorsa 8s'e atanabilir → FEASIBLE (eski: INFEASIBLE).
- `personel_vardiya_kisitlari`'nda 8s olmayan kişi 8s'e ASLA atanmaz.
- Hedefsiz kişi: atama alabilir + `solver.uyarilar` ilgili mesajı içerir.
- `baseline_hedef_esitlik.json` beklenen durumu `FEASIBLE` yap → yeşil.
- `TestVardiyaDinlenmeKurali` dahil mevcut property suite yeşil.

**MANUEL TEST DİREKTİFİ (rapora yaz):** Kullanıcı, bilinen bir gerçek
senaryoyu UI'dan çözsün; plan çıkmalı ve kişi başı nöbet sayıları
hedeflerle karşılaştırılmalı (sapma varsa hangi kişilerde olduğu not edilsin).

---

## G1.4 — Soft kontenjan ve max tavanını vardiya granülaritesine indir

**Dosya:** `solver.py::_alan_kontenjan_soft` (~540-557)

**DOKUNMA:** `_vardiya_minimum_kontenjan_hard` / `_soft` (356-397) doğru
semantiktedir (her vardiyada minimum kişi = kapsama), değiştirilmeyecek.
`AlanTanimi` değişmez, migration yoktur.

**Değişiklik:** Vardiya modunda kontenjan hedefi ve tavanı
(alan, gün) yerine (alan, gün, vardiya) başına uygulanır:

```python
def _alan_kontenjan_soft(self):
    w = self.input.config.w_alan_kontenjan_sapma
    for a_idx, alan in enumerate(self.input.alanlar):
        hedef = alan.gunluk_kontenjan
        max_k = alan.max_kontenjan
        for g in range(1, self.gun_sayisi + 1):
            for v_idx in range(self.n_vardiya):
                # Alan için geçersiz vardiyaları atla (hard'daki filtreyle aynı)
                if self.input.vardiya_modu and alan.vardiya_tipleri:
                    if self.input.vardiyalar[v_idx].isim not in alan.vardiya_tipleri:
                        continue
                toplam = sum(self.x[p, g, a_idx, v_idx] for p in range(self.n_personel))
                if max_k and max_k > 0:
                    self.model.Add(toplam <= max_k)
                sapma_pos = self.model.NewIntVar(0, self.n_personel, f"sp_{a_idx}_{g}_{v_idx}")
                sapma_neg = self.model.NewIntVar(0, self.n_personel, f"sn_{a_idx}_{g}_{v_idx}")
                self.model.Add(toplam - hedef == sapma_pos - sapma_neg)
                self.objective_terms.append(sapma_pos * w)
                self.objective_terms.append(sapma_neg * w)
```

- Nöbet modunda (`n_vardiya == 1`) davranış birebir eskisiyle aynıdır.
- `gunluk_kontenjan` / `max_kontenjan` ALAN ADLARI değişmez (yeniden
  adlandırma Faz 2'de storage ile birlikte). Docstring'e not düş:
  "vardiya modunda değerler VARDİYA BAŞINA yorumlanır".

**Kabul testleri:**
- 3 vardiyalı alan, `gunluk_kontenjan=1`, her vardiya min 1, hedefler
  uyumlu → optimal çözümde kontenjan kaynaklı ceza 0 (eski: her gün
  kaçınılmaz 2×10000).
- `max_kontenjan=2`, 3 vardiya × min 1 → FEASIBLE, her vardiyada ≤2
  (eski: gün tavanı 2 < gereken 3 → INFEASIBLE).
- Nöbet modu kontenjan testleri değişmeden yeşil.

---

## G1.5 — Otomatik hedef üreticisi düzeltmeleri

**Dosya:** `utils.py::hesapla_otomatik_hedef`

**NOT:** Kapasite çarpımı (`gün × kontenjan × vardiya_sayisi`) kapsama
semantiğiyle TUTARLIDIR, değiştirilmeyecek.

**Değişiklik:**
1. `kisinin_max_atama` çağrısı G1.2'nin yeni parametreleriyle yapılır
   (`takvim_gun_sayisi=gun_sayisi`, `gunasiri_limit_aktif` iletilir).
2. Taşma kırpması: üretilen hedeflerin toplamı `toplam_slot`'u aşıyorsa
   (round yukarı yuvarlaması), aşan miktar en yüksek hedefli kişilerden
   birer birer düşülür (deterministik sıra: hedef desc, isim asc).

**Kabul testleri:**
- `sum(hedefler) <= toplam_slot` her rastgele küçük senaryoda (property testi).
- Nöbet modu, 31 gün, izinsiz: üretilen hiçbir hedef 11'i aşmaz.
- Kırpma determinizmi: aynı girdi → aynı çıktı.
- Entegrasyon (property): rastgele küçük senaryo → otomatik hedef →
  solver → INFEASIBLE OLMAMALI (G1.3 sonrası hedefler soft olduğundan
  bu test staffing çakışması olmayan girdilerle sınırlansın).

---

## FAZ SONU KONTROL LİSTESİ

- [ ] Tüm suite + baseline yeşil
- [ ] `baseline_*.json` beklenen durumları güncel ve raporlarda gerekçeli
- [ ] "Dokunma" listesindeki dosyalarda diff YOK
- [ ] Her görev ayrı commit, rapor formatına uygun 7 rapor
- [ ] Kullanıcıya iletilecek manuel test direktifleri derlenmiş
