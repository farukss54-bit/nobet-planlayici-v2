# SOLVER V3 — FAZ 2: Dürüstlük Katmanı (Sessiz Başarısızlıkların Sonu)

**Durum:** Onaylandı — uygulamaya hazır
**Ön koşul:** Faz 0-1 tamamlanmış ve main'e merge edilmiş olmalı; bu faz o HEAD'den dallanır.
**Kapsam:** `tabs/cozum_tab.py`, `tabs/personel_tab.py`, `tabs/eslesmeler_tab.py`, `tabs/izinler_tab.py`, `storage.py`, `models.py`, `solver.py` (YALNIZCA `gelismis_teshis`/`teshis_ozeti`), `app.py` (yalnızca G2.10 default hizalama)
**Kapsam DIŞI (bu fazda DOKUNMA):** `solver.py` kısıt/objective fonksiyonları (`_hedef_*`, `_gunasiri_*`, `_vardiya_*`, `_alan_*`, `_hafta_*`, `_iki_gun_*`, `_kidem_*`, eşleşme kısıtları), `utils.py` hesap fonksiyonları, `config.py` ağırlıkları, `tests/fixtures/` beklenen durumları, `scenarios.py`

**FAZ İLKESİ:** Bu faz solver'ın ürettiği planları DEĞİŞTİRMEZ. Tüm baseline
fikstürleri faz sonunda aynı statü ve benzer sapma değerleriyle geçmelidir.
Değişen tek şey: sistemin kullanıcıya karşı dürüstlüğü — hatalar görünür,
girdiler doğrulanır, sonuçlar eksiksiz raporlanır.

---

## AGENT ÇALIŞMA PROTOKOLÜ

Faz 0-1 protokolü aynen geçerlidir (sıralı görevler, görev başına commit +
rapor, test zayıflatma yasağı, kapsam dışına çıkmama, Türkçe konvansiyon,
tanımsız iyileştirme = ÖNERİ olarak rapora). Ek kurallar:

1. UI değişikliklerinde MÜMKÜNSE `streamlit.testing.v1.AppTest` ile otomatik
   test yaz. AppTest'in kaldıramadığı akışlar (dosya indirme, file_uploader,
   çok adımlı etkileşim) için raporda MANUEL TEST DİREKTİFİ ver.
2. UI metinleri: teknik jargon yok. "INFEASIBLE" yerine "çözüm bulunamadı",
   "constraint" yerine "kural". Solver status'ü gösterirken parantezde teknik
   değer kalabilir: örn. "En iyi çözüm (OPTIMAL)".
3. Her görev sonunda baseline suite koş: statü değişimi = BLOKE, dur.

### Rapor formatı: Faz 0-1 ile aynı.

---

## ARKA PLAN

Kod incelemesi, sistemin birçok noktada kullanıcıya sessiz kaldığını veya
yanlış bilgi verdiğini gösterdi. Ana tema: **kullanıcının girdiği şey ile
solver'a giden şey arasındaki farklar görünmez.** Bu faz o farkları ya
kapatır ya görünür kılar. İkinci tema: **Faz 0-1'in kazanımları UI'a
bağlanmadı** — status/uyarılar gösterilmiyor ve bir UI ön kontrolü artık
Faz 1 davranışıyla çelişip çözülebilir girdileri engelliyor.

---

## G2.1 — UI ön kontrolünü Faz 1 davranışıyla hizala (YANLIŞ ENGELLEYİCİ)

**Dosya:** `tabs/cozum_tab.py` ~172-180

**Sorun:** `toplam_hedef < gereken_toplam` → "İmkânsız" + `st.stop()`.
İki hata: (a) G1.3'ten beri hedefler soft — bu girdiler artık ÇÖZÜLEBİLİR,
kontrol solver'ı hiç çalıştırmadan reddediyor; (b) "gereken" `gunluk_kontenjan
× vardiya` ile hesaplanıyor, oysa hard gereksinim `minimum_staffing`.

**Değişiklik:**
- `st.stop()` kaldırılır. Kontrol bilgilendirmeye dönüşür:
  - Hard taban: `sum( max(alan.minimum_staffing, vardiya.minimum_staffing,
    alan.vardiya_tipleri'ne göre geçerli kombinasyonlar için) )` × gün.
    Hesap, solver'daki hard staffing döngüsüyle AYNI kombinasyon filtresini
    kullanmalı (geçersiz alan-vardiya çiftleri sayılmaz).
  - `toplam_hedef < hard_taban` → `st.warning`: "Toplam hedef (X), zorunlu
    doluluk tabanının (Y) altında. Plan yine üretilir; kişilere hedeflerinden
    fazla nöbet düşecek ve sapmalar raporlanacak."
  - `toplam_hedef > teorik_tavan` (max_kontenjan toplamı × gün, tavan
    tanımlıysa) → `st.warning` benzer dille (kişiler hedeflerinin altında
    kalacak).
  - Aralıktaysa mesaj yok.
- `st.stop()` yalnızca yapısal eksiklerde kalır (personel listesi boş).

**Kabul testleri:**
- AppTest: hedef toplamı tabanın altında bir senaryoda "Nöbeti Oluştur" →
  solver ÇALIŞIR, çözüm gösterilir, warning görünür.
- Baseline fikstürleri statü değiştirmez.

---

## G2.2 — Hata sınıflarını ayır: bilinçli red ≠ çökme

**Dosya:** `tabs/cozum_tab.py` ~261-319

**Sorun:** `except Exception` her şeyi "Çözüm bulunamadı" sayıyor: G1.2'nin
bilinçli ValueError'ı, gerçek INFEASIBLE ve kod hataları (TypeError vb.) aynı
mesaja düşüyor; kod hatalarında bile teşhis koşup kullanıcıyı yanıltıyor.

**Değişiklik — üç ayrı yol:**
1. `except ValueError as e` → "Girdi kuralları çözümü engelliyor" başlığı,
   `str(e)` mesajı büyük/okunur göster, ARDINDAN teşhis çalıştır.
2. Solver INFEASIBLE (ValueError "Çözüm bulunamadı" mesajı — mevcut raise) →
   aynı ValueError yolunda kalır; `solver.cozum_meta["status"]` varsa
   mesajda kullan.
3. `except Exception as e` (geri kalan her şey) → "Beklenmedik uygulama
   hatası" + `st.exception(e)` (traceback görünür). TEŞHİS ÇALIŞTIRILMAZ.
   Kullanıcıya "bu bir kural sorunu değil, hata raporu iletebilirsiniz" notu.

**Kabul testleri:**
- AppTest/unit: hedef>max girdisi → yol 1 mesajı + teşhis bölümü var.
- Kasıtlı bozuk girdi ile (test için monkeypatch, örn. solver.coz'a
  TypeError fırlattır) → yol 3: traceback görünür, teşhis başlığı YOK.

---

## G2.3 — Çözüm karnesi: status, süre, uyarılar

**Dosya:** `tabs/cozum_tab.py` (başarı yolu, ~321 sonrası)

**Sorun:** G0.1'in `cozum_meta`sı ve G1.3'ün `solver.uyarilar`ı UI'da hiç
gösterilmiyor. "🎉 Çözüm bulundu!" mesajı OPTIMAL ile 60 saniyeye takılmış
FEASIBLE'ı ayırt etmiyor — baseline ölçümlerinde bu fark toplam sapmayı
0↔16 arasında değiştiriyor.

**Değişiklik:**
- Başarı mesajının hemen altına üç `st.metric` satırı: Durum ("En iyi çözüm
  (OPTIMAL)" / "Geçerli çözüm — süre limitine takıldı (FEASIBLE)"), Süre
  (sn), Toplam hedef sapması (istatistik tablosundan hesaplanır:
  Σ|gerçekleşen−hedef|).
- FEASIBLE ise `st.info`: "Süre limiti içinde en iyi bulunan plan bu;
  sapmalar süre artırılarak azalabilir."
- `solver.uyarilar` boş değilse `st.warning` bloğunda madde madde göster.
- Mevcut istatistik tablolarına "Fark" sütunu zaten tek-alan modunda var;
  DİĞER üç modda da eklensin (Gerçekleşen − Hedef).

**Kabul testleri:**
- AppTest: çözülebilir senaryo → Durum/Süre metrikleri render edildi.
- Hedefi girilmemiş personel içeren senaryo (personel_targets'tan silinmiş,
  otomatik hedef kapalı) → uyarı bloğu görünür.

---

## G2.4 — Boş slot: ayrıştır ve bağır

**Dosyalar:** `solver.py::_coz_ve_sonuc_al` (~740-741 `if kisiler:` filtresi),
`tabs/cozum_tab.py` (dört mod gösterimi + Excel)

**Sorun:** Dolması gerekirken boş kalan slot ile "bu kombinasyon zaten
geçersiz" aynı "-" olarak görünüyor; kayıtlı plana boş slot hiç yazılmıyor.
Soft staffing modunda boş kalan gece vardiyası fark edilmeden yayınlanabilir.

**Değişiklik:**
1. `solver.py`: `if kisiler:` filtresi kaldırılır — GEÇERLİ tüm alan-vardiya
   kombinasyonları (vardiya_tipleri filtresine uyanlar) sonuçta boş liste
   olarak da yer alır. Geçersiz kombinasyonlar yazılMAZ.
   - Tüketici güvenliği: `onceki_ay_son_gun_atamalari` boş listelerde no-op
     (döngü boş) — güvenli, değişiklik gerekmez. UI `get(..., [])` zaten
     tolere ediyor. `AylikPlan.sonuc`a boş listeler de kaydedilir (bilgi
     kaybı biter).
2. `cozum_tab.py`: hücre değeri üretilirken üç durum ayrılır:
   - Kişi var → isimler
   - Anahtar var + liste boş → `"⚠ BOŞ"`
   - Anahtar yok (geçersiz kombinasyon) → `"—"`
3. Boş slot sayısı > 0 ise tablo üstünde `st.error`: "X slot boş kaldı —
   plan bu haliyle yayınlanmamalı." (enforce_minimum_staffing=False iken
   olası; True iken görülmesi bug işaretidir, mesajda belirt.)
4. Excel: boş slot hücresine kırmızı dolgu + "BOŞ" metni.

**Kabul testleri:**
- Unit: soft staffing + kasıtlı dar kapasiteli mini senaryo → sonuç dict'inde
  boş listeli anahtar VAR; UI satırında "⚠ BOŞ"; sayaç mesajı render edildi.
- Hard staffing çözülebilir senaryo → hiç "⚠ BOŞ" yok; geçersiz kombinasyon
  hücresi "—".
- Baseline fikstürleri statü/sapma değiştirmez (yalnızca sonuç dict'i
  genişledi — testler kişi listelerini okuduğundan etkilenmemeli; etkilenen
  test varsa sebebiyle raporla, ZAYIFLATMA).

---

## G2.5 — Kayıt hatalarını görünür yap

**Dosyalar:** `storage.py`, `tabs/personel_tab.py`, `tabs/cozum_tab.py`

**Sorun:** Tüm storage hataları `print()` — Streamlit kullanıcısı asla
görmez. `personel_tab` `ayarlari_kaydet` dönüşünü kontrol etmiyor;
`cozum_tab` `aylik_plani_kaydet` dönüşünü kontrol etmiyor. Bozuk plan
dosyaları listeden sessizce kaybolur.

**Değişiklik:**
1. `storage.py`: `print` → `logging` (modül logger'ı). Fonksiyon imzaları
   ve dönüş sözleşmeleri DEĞİŞMEZ (bool/None aynen).
2. `kayitli_planlari_listele`: parse edilemeyen dosyayı atlamak yerine
   listeye `{"dosya": ..., "bozuk": True}` kaydı ekler; `sidebar.py`
   bozuk kaydı "⚠ bozuk dosya" olarak gösterir.
3. Çağıran taraf: `personel_tab`'daki iki `ayarlari_kaydet` çağrısı ve
   `cozum_tab`'daki `aylik_plani_kaydet` dönüş kontrolü + başarısızlıkta
   `st.error("Kaydedilemedi — değişiklikler kalıcı olmayabilir")`.

**Kabul testleri:**
- Unit (storage): yazılamaz dizin (monkeypatch/chmod) → False döner, log
  kaydı düşer.
- Unit: bozuk JSON'lu plan dosyası → listede `bozuk: True` ile yer alır.
- AppTest: kaydetme başarısız monkeypatch'i ile personel değişikliği →
  ekranda hata mesajı.

---

## G2.6 — Girdi kimlik doğrulaması (çözüm kapısı)

**Dosyalar:** `tabs/cozum_tab.py` (solver çağrısı ÖNCESİ yeni fonksiyon
`_girdi_dogrula(...)`), `tabs/personel_tab.py` (anlık uyarılar)

**Sorun:** Doğrulanmayan kimlikler sessiz veri bozulması yaratıyor:
boş personel adı; iki personele aynı isim (tüm dict'ler isim anahtarlı —
izin/hedef/yetkinlik sessizce birleşir); `personel_kidem_gruplari`nda
tanımsız grup adı (solver `continue` ile atlar); alan `kidem_kurallari`nda
tanımsız grup; yetkinlik/kısıt listelerinde tanımsız alan/vardiya adı.

**Değişiklik:**
1. `_girdi_dogrula(solver_input, kidem_grubu_isimleri) -> (hatalar, uyarilar)`
   saf fonksiyon (test edilebilir, Streamlit'e bağımlı değil):
   - HATA (çözümü durdurur): boş/whitespace personel adı; yinelenen personel
     adı; kidem_kurallari'nda hiçbir personelin üye olmadığı VEYA tanımsız
     grup adı (min>0 iken — kural fiilen sağlanamaz/uygulanamaz).
   - UYARI (devam eder, gösterilir): personelin kıdem grubu tanımsız;
     yetkinlik/kısıt listesinde tanımsız alan veya vardiya adı; izin/hedef
     dict'lerinde listede olmayan personel anahtarı.
2. `cozum_tab`: solver kurulumundan önce çağır; hatalar `st.error` + dur,
   uyarılar `st.warning` + devam.
3. `personel_tab`: isim girişinde anlık kontrol — boş veya çakışan isimde
   satır yanında `st.warning` işareti (kaydetmeyi engellemez, çözüm kapısı
   G2.6.1'de zaten durduracak).

**Kabul testleri (saf fonksiyon, AppTest gerekmez):**
- Yinelenen isim → hatalar listesinde; tanımsız kıdem grubu (kidem_kurallari,
  min=1) → hata; personelde tanımsız grup → uyarı; temiz girdi → ikisi de boş.
- AppTest: yinelenen isimli senaryoda "Nöbeti Oluştur" → hata mesajı, solver
  çalışmadı.

---

## G2.7 — Hedef girişinde sessiz dönüşümleri bitir

**Dosyalar:** `tabs/personel_tab.py` (~132-136), `tabs/cozum_tab.py` (~84-106)

**Sorun A:** Kişisel hedef varsayılana EŞİTSE siliniyor → kullanıcı bilinçli
7 girdi, sistem "girilmemiş" sayıp otomatik/kıdem zincirine düşürüyor.
**Sorun B:** `elif` zinciri: kişisel hedef girilen kişi, kıdem grubunun
vardiya kırılımını ({"24s": 8, "16s": 1}) sessizce kaybediyor.

**Değişiklik:**
1. Personel satırına "Oto" checkbox eklenir (default: kişisel kayıt yoksa
   işaretli). İşaretliyse `personel_targets`'tan silinir (otomatik/kıdem
   zinciri çalışır); işaretli DEĞİLSE girilen değer — varsayılana eşit olsa
   bile — `personel_targets`'a yazılır. "Değer==default → sil" mantığı
   tamamen kaldırılır.
2. `cozum_tab` hedef zinciri: kişisel hedef VARSA ve kişinin grubunun
   vardiya kırılımı da varsa, kırılım YOK sayılır AMA sessiz değil:
   çözüm öncesi `st.info` listesi — "Şu kişilerde kişisel hedef, grup
   vardiya kırılımının önüne geçti: ...". (Kırılımı ölçekleme YOK — bu
   fazda davranış icat edilmez, yalnızca görünür kılınır.)
3. Varsayılan hedef değişince tüm hedeflerin toplu güncellenmesi (satır
   ~33-38) korunur ama `st.toast/info` ile bildirilir: "Varsayılan hedef
   değişti — N kişinin hedefi güncellendi."

**Kabul testleri:**
- AppTest: default 7 iken Oto kapalı + 7 girilir → `personel_targets`'ta 7
  kalır; çözümde otomatik hedef bu kişiye uygulanmaz.
- Unit: kişisel hedefli + grup kırılımlı kişi → `vardiya_hedefleri`ne
  girmez ve bilgi listesinde adı geçer.

---

## G2.8 — Soft want-pair girilebilir olsun

**Dosya:** `tabs/eslesmeler_tab.py` ~26

**Sorun:** "Minimum birlikte gün" `min_value=1` — UI'dan soft (zorunlu
olmayan) birlikte-çalışma tercihi girmek İMKÂNSIZ; her want-pair hard
doğuyor. (Solver semantiği: min_k=0 → yalnızca ödül; min_k>0 → hard alt
sınır. Solver DEĞİŞMEZ.)

**Değişiklik:**
- `min_value=0`, varsayılan 0. Yardım metni: "0 = tercih (mümkünse birlikte,
  zorunlu değil); 1+ = en az bu kadar gün birlikte ZORUNLU".
- Liste gösteriminde (satır ~66) min:0 için "tercih", min>0 için
  "zorunlu ≥N" etiketi.

**Kabul testleri:**
- AppTest: min=0 çift eklenir → listede "tercih" etiketi; solver girdisinde
  `birlikte_tut` üçlüsünde 0.
- Mevcut kayıtlı ayarlarda min≥1 çiftler aynen yüklenir (geriye uyumluluk).

---

## G2.9 — Teşhis false-positive temizliği

**Dosya:** `solver.py` → YALNIZCA `gelismis_teshis` / `teshis_ozeti`

**Sorun:** Teşhis iki yönde yanıltıyor. (a) Saf nöbet modunda
`toplam_kapasite = gun_sayisi` (günde 1 kişi varsayımı) — modelde böyle bir
hard kısıt yok; `sum(hedef) > gun_sayisi` olan çözülebilir girdilere
"İmkansız!" diyor. (b) `enforce_minimum_staffing` bayrağına bakıp hata
basıyor ama staffing kısıtı yalnızca vardiya modunda kurulur.

**Değişiklik:**
1. Saf nöbet modu kapasite hesabı: günde-1 varsayımı kaldırılır; kapasite
   üst sınırı `Σ kisinin_max_atama(...)` (kişi bazlı, G1.2 formülüyle) olur;
   "toplam hedef > kişisel maksimumlar toplamı" gerçek imkânsızlık olarak
   kalır.
2. Staffing kontrolleri `vardiyalar is not None` (vardiya modu) şartına
   bağlanır.
3. G1.3 sonrası dil düzeltmesi: hedef kaynaklı bulgular "İmkansız" değil
   "hedefler sapacak" dilinde raporlanır (hedefler artık soft) — yalnızca
   hard sınır ihlalleri (kişisel max, staffing tabanı) "imkânsız" kalır.
4. Hiç bulgu yoksa `teshis_ozeti` dürüst kapanış: "Bilinen desenlerde sorun
   bulunamadı; teşhis kapsamı sınırlıdır — kısıt etkileşimleri Faz 3
   teşhisiyle adreslenecek."

**Kabul testleri:**
- Unit: nöbet modu, 5 kişi × hedef 10, 31 gün (günde ~1.6 kişi) → teşhis
  "İmkansız" ÜRETMEZ.
- Unit: nöbet modu + enforce_minimum_staffing=True → staffing hatası YOK.
- Vardiya modu regresyonu: mevcut teşhis testleri yeşil.
- `gercek_senaryo_01` INFEASIBLE'a zorlanmış varyantında (örn. hedefleri
  kişisel max üstüne çek) teşhis en az bir GERÇEK bulgu üretir.

---

## G2.10 — Küçük dürüstlük düzeltmeleri (tek commit)

**Dosyalar:** `models.py`, `tabs/izinler_tab.py`

1. `Ayarlar.otomatik_hedef` default hizalama: dataclass `False` (satır ~291)
   vs `from_dict` `True` (~349) vs UI `True`. Üçü de **True** yapılır
   (mevcut kullanıcı deneyimiyle uyumlu olan bu).
2. `VardiyaTipi.saat` sessiz 8 fallback'i: parse hatasında `logging.warning`
   + UI tarafında vardiya listesinde "⚠ saat okunamadı (8s varsayıldı)"
   rozeti (vardiyalar_tab'da gösterim varsa; yoksa yalnızca log + rapor notu).
3. `izinler_tab` manuel tatil: metin boş değil ama `gun_parse` sonucu boşsa
   `st.warning("Hiçbir gün tanınamadı — virgülle ayırın: 15, 16 veya 15-18")`;
   kısmi tanımada tanınan günler zaten gösteriliyor, tanınmayan parça varsa
   "şu parçalar atlandı: ..." uyarısı (gun_parse İMZASI DEĞİŞMEZ; atlanan
   parçalar UI tarafında yeniden taranarak bulunur).

**Kabul testleri:** her madde için 1 unit/AppTest; `Ayarlar()` ile
`Ayarlar.from_dict({})` aynı `otomatik_hedef` değerini verir.

---

## FAZ SONU KONTROL LİSTESİ

- [ ] Tüm suite + baseline yeşil; baseline statü/sapma değişimi YOK
- [ ] "Dokunma" listesi diff'siz (solver kısıt fonksiyonları, utils
      hesapları, config ağırlıkları, fikstür beklentileri)
- [ ] 10 görev, 10 commit, 10 rapor
- [ ] Manuel test direktifleri derlenmiş (özellikle G2.4 Excel çıktısı ve
      G2.7 hedef girişi akışı — AppTest kapsayamazsa)
- [ ] ÖNERİ maddeleri listelenmiş (Faz 3 girdisi olacak)
