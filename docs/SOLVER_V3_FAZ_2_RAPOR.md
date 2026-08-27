# SOLVER V3 — FAZ 2 RAPORU: Dürüstlük Katmanı

**Branch:** `feature/solver-v3-faz2` (`feature/solver-v3` üzerinden dallandı)
**Kapsam:** G2.1 – G2.10 (10 görev, 10 commit)
**Durum:** Tamamlandı — Faz Sonu Kontrol Listesi geçildi

---

## Özet

Faz 2, solver'ın ürettiği planları **değiştirmeden**, sistemin kullanıcıya karşı dürüstlüğünü artırdı: hatalar artık görünür, girdiler doğrulanıyor, sonuçlar eksiksiz raporlanıyor. Ana tema Faz 0-1'in kazanımlarını (soft hedefler, doğru kontenjan granülaritesi, günaşırı düzeltmesi) UI'a bağlamak ve UI'nin bu kazanımlarla çelişen eski varsayımlarını (hard hedef dönemine ait "İmkânsız" kontrolleri, sessiz kayıt hataları, sessiz veri bozulmaları) temizlemekti.

**Sonuç:** 10 görevin tamamı tamamlandı, tam test suite'i 143 test (142 hızlı + 1 yavaş `@pytest.mark.yavas`) ile **regresyonsuz** geçiyor. "Dokunma" listesindeki hiçbir solver kısıt/objective fonksiyonuna, `utils.py`/`config.py`/`scenarios.py`'ye veya baseline fikstür beklentilerine dokunulmadı.

---

## G2.1 — UI ön kontrolünü Faz 1 davranışıyla hizala

**Sorun:** `tabs/cozum_tab.py`'deki "toplam_hedef < gereken_toplam → İmkânsız + st.stop()" bloğu iki nedenden yanlıştı: (a) G1.3'ten beri hedefler soft, bu girdiler artık çözülebilir; (b) "gereken" `gunluk_kontenjan × vardiya` ile hesaplanıyordu, oysa hard gereksinim `minimum_staffing`'e bağlı ve yalnızca `vardiya_modu + enforce_minimum_staffing=True` iken geçerli.

**Çözüm:** Yeni saf fonksiyon `_staffing_taban_tavan(alanlar, vardiyalar, gun_sayisi, enforce_minimum_staffing)` — solver'ın hard staffing filtresiyle (alan.vardiya_tipleri kombinasyon kontrolü, `max(alan.min, vardiya.min)`) birebir aynı mantıkla hard taban ve teorik tavanı hesaplıyor. `st.stop()` kaldırıldı; aralık dışı girdilerde `st.warning` ile bilgilendirme yapılıyor, çözüm engellenmiyor.

**Bulgu (ÖNERİ):** `AlanTanimi.minimum_staffing`, vardiya modu kapalıyken solver'da hiç enforce edilmiyor (hard staffing bloğu yalnızca `vardiya_modu`'na bağlı) — modelleme borcu, Faz 3+ girdisi.

**Testler:** 8 unit (`test_g2_1_staffing_taban_tavan.py`) + 2 AppTest (`test_g2_1_apptest.py`). Commit: `2e24f4d`.

---

## G2.2 — Hata sınıflarını ayır: bilinçli red ≠ çökme

**Sorun:** Tek `except Exception` bloğu G1.2'nin bilinçli `ValueError`'ını, solver `INFEASIBLE`'ini ve gerçek kod hatalarını (TypeError vb.) aynı "Çözüm bulunamadı" mesajına düşürüyordu; kod hatalarında bile teşhis çalışıp kullanıcıyı yanlış yöne yönlendiriyordu.

**Çözüm:** Üç ayrı yol:
1. `except ValueError` → "Girdi kuralları çözümü engelliyor" + mesaj, ardından teşhis çalışır (kural sorunu).
2. Aynı yolda `solver.cozum_meta["status"]` varsa (solver INFEASIBLE verdiyse) başlıkta gösterilir.
3. `except Exception` → "Beklenmedik uygulama hatası" + `st.exception` (traceback). **Teşhis çalıştırılmaz.**

**Testler:** 2 AppTest (`test_g2_2_apptest.py`) — hedef>max → yol 1; `solver.coz()` monkeypatch ile TypeError → yol 3. Commit: `bd89545`.

---

## G2.3 — Çözüm karnesi: status, süre, uyarılar

**Sorun:** G0.1'in `cozum_meta`'sı ve G1.3'ün `solver.uyarilar`'ı UI'da hiç gösterilmiyordu; "Çözüm bulundu!" mesajı OPTIMAL ile süre limitine takılmış FEASIBLE'ı ayırt etmiyordu.

**Çözüm:** Yeni `_toplam_sayim_cikar` (mod-bağımsız kişi başı sayım) ve `_cozum_karnesi_goster` (Durum/Süre/Toplam Hedef Sapması metrikleri + FEASIBLE bilgi notu + uyarı bloğu) fonksiyonları, her 4 modda `st.success` sonrasına eklendi. Eksik olan 3 moda "Fark" sütunu eklendi.

**Ortam bulgusu + düzeltmesi:** `AppTest.from_function`, bu depoda `AppTest.from_file(app.py)` sonrası çağrıldığında çöküyordu — kök neden: Streamlit'in `PagesManager.uses_pages_directory` bayrağı süreç-geneli/kalıcı, ve `app.py`'nin yanında boş bir `pages/` dizini var. Düzeltme test tarafında: `tests/_apptest_helpers.py::from_function_izole` her çağrıdan önce bayrağı `False`'a sabitliyor (`pages/`'a dokunulmadı).

**Testler:** 4 AppTest (`test_g2_3_cozum_karnesi.py`). Commit: `73ee57f`.

---

## G2.4 — Boş slot: ayrıştır ve bağır

**Sorun:** Dolması gerekirken boş kalan slot ile "geçersiz kombinasyon" aynı "-" olarak görünüyordu; kayıtlı plana boş slot hiç yazılmıyordu.

**Çözüm:**
- `solver.py::_coz_ve_sonuc_al`: vardiya modundaki `if kisiler:` filtresi kaldırıldı — geçerli kombinasyonlar boş liste olarak da yazılıyor, geçersizler hâlâ hiç yazılmıyor.
- `tabs/cozum_tab.py`: yeni `_hucre_degeri` üç durumu ayırıyor (isimler / `"⚠ BOŞ"` / `"—"`). Boş slot sayısı > 0 ise `st.error` (enforce_minimum_staffing=True iken ekstra "bug işareti" notu). Excel'de boş slot hücresine kırmızı dolgu + "BOŞ" metni.

**Testler:** 5 test (2 solver-seviyesi + 1 unit + 2 AppTest, `test_g2_4_bos_slot.py`). **Kullanıcı tarafından Excel çıktısı manuel doğrulandı.** Commit: `ad942e6`.

---

## G2.5 — Kayıt hatalarını görünür yap

**Sorun:** Tüm storage hataları `print()` ile basılıyordu — Streamlit kullanıcısı asla görmüyordu. `personel_tab`/`cozum_tab` kayıt fonksiyonlarının dönüşünü kontrol etmiyordu. Bozuk plan dosyaları listeden sessizce kayboluyordu.

**Çözüm:**
- `storage.py`: `print` → `logging` (`exc_info=True`), imza/dönüş sözleşmeleri değişmedi. `kayitli_planlari_listele` artık bozuk dosyayı `{"dosya":..., "bozuk": True}` ile listede tutuyor.
- `tabs/sidebar.py`: bozuk kayıt "⚠ bozuk dosya (...)" gösteriliyor.
- `tabs/personel_tab.py`: 3 `ayarlari_kaydet` çağrısının hepsi dönüş kontrolü kazandı (`st.rerun()` öncesi olan, hata mesajını `session_state` üzerinden bir sonraki çalışmaya taşıyor).
- `tabs/cozum_tab.py`: `aylik_plani_kaydet` dönüşü kontrol ediliyor; başarısızlıkta çözüm yine de gösteriliyor.

**Testler:** 3 test (`test_g2_5_kayit_hatalari.py`). Commit: `bd9a279`.

---

## G2.6 — Girdi kimlik doğrulaması (çözüm kapısı)

**Sorun:** Doğrulanmayan kimlikler sessiz veri bozulması yaratıyordu: boş/yinelenen personel adı, `kidem_kurallari`'nda tanımsız/üyesiz grup, yetkinlik/kısıt listelerinde tanımsız alan/vardiya.

**Çözüm:** Yeni saf fonksiyon `_girdi_dogrula(solver_input, kidem_grubu_isimleri) -> (hatalar, uyarilar)`. **HATA** (durdurur): boş/whitespace isim, yinelenen isim, tanımsız/üyesiz kıdem kuralı (min>0). **UYARI** (devam eder): tanımsız kıdem grubu, tanımsız yetkinlik/kısıt, izin/hedef'te olmayan isim. `personel_tab.py`'de anlık satır uyarısı eklendi.

**Önemli bulgu (ÖNERİ):** Yinelenen personel adıyla **tam uygulama** çalıştırıldığında çözüm kapısına hiç ulaşılamıyor — `izinler_tab.py`/`vardiyalar_tab.py` kişi başına isme bağlı widget key'leri kullanıyor (`key=f"izin_{p}"` vb.), iki aynı isimli personel `StreamlitDuplicateElementKey` ile **tüm uygulamayı** çözüm kapısından çok daha önce çökertiyor. Bu yüzden testler tam `app.py` yerine izole `_cozum_olustur`/`render_personel_tab` çağrısı üzerinden kuruldu.

**Testler:** 12 test (10 unit + 2 AppTest, `test_g2_6_girdi_dogrula.py`). Commit: `877abdc`.

---

## G2.7 — Hedef girişinde sessiz dönüşümleri bitir

**Sorun A:** Kişisel hedef varsayılana eşitse siliniyordu → kullanıcı bilinçli 7 girdi, sistem "girilmemiş" sayıp otomatik/kıdem zincirine düşürüyordu.
**Sorun B:** Kişisel hedefi olan kişi, kıdem grubunun vardiya kırılımını sessizce kaybediyordu.

**Çözüm:**
- `tabs/personel_tab.py`: her satıra **"Oto" checkbox** eklendi (varsayılan: kişisel kayıt yoksa işaretli). İşaretli değilse değer — varsayılana eşit olsa bile — kalıcı yazılıyor. Eski "değer==varsayılan → sil" mantığı tamamen kaldırıldı.
- `tabs/cozum_tab.py`: kişisel hedefin grup vardiya kırılımını ezdiği durum tespit edilip çözümden önce `st.info` ile gösteriliyor (kırılım yine uygulanmıyor — yalnızca görünürlük).
- Varsayılan hedef toplu güncellemesi artık `st.info` ile bildiriliyor.

**Testler:** 4 AppTest (izole route + sahte `NobetSolver` casusu ile `SolverInput.hedefler` doğrudan doğrulandı, `test_g2_7_hedef_sessiz_donusumler.py`). Commit: `cc030e5`.

---

## G2.8 — Soft want-pair girilebilir olsun

**Sorun:** "Minimum birlikte gün" `min_value=1` idi — UI'dan soft (zorunlu olmayan) birlikte-çalışma tercihi girmek imkânsızdı; her want-pair hard doğuyordu (solver semantiği zaten `min_k=0` → yalnızca ödül destekliyordu).

**Çözüm:** `tabs/eslesmeler_tab.py`'de `min_value=0`, varsayılan 0, yardım metni eklendi. Liste gösteriminde `min:0` için "tercih", `min>0` için "zorunlu ≥N" etiketi. **Solver'a dokunulmadı.**

**Testler:** 3 AppTest (`test_g2_8_soft_want_pair.py`) — min=0 kalıcılığı, geriye uyumluluk (min≥1 aynen yüklenir), sahte solver ile `birlikte_tut` üçlüsünde 0 doğrulandı. Commit: `0fad689`.

---

## G2.9 — Teşhis false-positive temizliği

**Sorun:** `gelismis_teshis` iki yönde yanıltıyordu: (a) saf nöbet modunda `toplam_kapasite = gun_sayisi` ("günde 1 kişi" varsayımı, modelde yok) — çözülebilir girdilere "İmkânsız!" diyordu; (b) `enforce_minimum_staffing` bayrağına bakıyordu ama staffing kısıtı yalnızca vardiya modunda kuruluyor.

**Çözüm (yalnızca `gelismis_teshis`/`teshis_ozeti`):**
1. Nöbet modu kapasitesi artık Σ`kisinin_max_atama(...)` (kişi bazlı, gerçek hard tavan) — bu modda "İmkânsız" hâlâ doğru kalıyor çünkü bu gerçek bir hard sınır.
2. Staffing hata seviyesi `enforce_minimum_staffing AND vardiyalar var` şartına bağlandı.
3. Alan/vardiya modlarında (G1.4'ten beri soft kapasite) aşım artık "İmkânsız" değil "hedefler sapacak" dilinde, `warning`.
4. Bulgu yoksa dürüst kapanış: *"Bilinen desenlerde sorun bulunamadı; teşhis kapsamı sınırlıdır — kısıt etkileşimleri Faz 3 teşhisiyle adreslenecek."*

**Testler:** 5 unit (`test_g2_9_teshis_false_positive.py`) — nöbet modu gerçekçi senaryo "İmkânsız" üretmiyor; vardiya modunda gerçek açık hâlâ "error" (regresyon); `gercek_senaryo_01`'i bilinçli infeasible yapan varyantta en az bir gerçek bulgu üretiliyor. Commit: `15f3092`.

---

## G2.10 — Küçük dürüstlük düzeltmeleri

Üç madde, tek commit:
1. `Ayarlar.otomatik_hedef` — dataclass/`from_dict`/UI üçü de `True`'ya hizalandı (önceden üç farklı varsayılan vardı).
2. `VardiyaTipi.saat` — parse hatasında artık `logging.warning`; yeni `saat_gecerli` property'si UI'da "⚠ saat okunamadı (8s varsayıldı)" rozetini besliyor.
3. `izinler_tab.py` manuel tatil — hiçbir gün tanınmazsa uyarı; kısmi tanımada `_tanimayan_parcalari_bul()` ile "Şu parçalar atlandı: ..." uyarısı (`gun_parse` imzası değişmedi).

**Testler:** 9 test (`test_g2_10_kucuk_durustluk.py`). Commit: `25428b3`.

---

## Faz Sonu Kontrol Listesi

| Madde | Durum |
|---|---|
| Tüm suite + baseline yeşil; statü/sapma değişimi yok | ✅ 143 passed, 1 skipped, 0 failed (229.81s) |
| "Dokunma" listesi diff'siz | ✅ `solver.py` yalnızca `_coz_ve_sonuc_al` (G2.4) + `gelismis_teshis`/`teshis_ozeti` (G2.9); `utils.py`/`config.py`/`scenarios.py`/`tests/fixtures/`/`app.py` sıfır diff |
| 10 görev, 10 commit, 10 rapor | ✅ `2e24f4d` → `25428b3` |
| Manuel test direktifleri derlenmiş | ✅ G2.4 Excel çıktısı kullanıcı tarafından doğrulandı; diğerleri AppTest ile tam kapsandı |
| ÖNERİ maddeleri listelenmiş | ✅ Aşağıda |

### ÖNERİ (Faz 3+ girdisi)

1. **(G2.1)** `AlanTanimi.minimum_staffing`, vardiya modu kapalıyken solver'da hiç enforce edilmiyor (hard staffing bloğu yalnızca `vardiya_modu`'na bağlı) — modelleme borcu.
2. **(G2.6)** Yinelenen personel adıyla tam uygulama, çözüm kapısından çok önce `izinler_tab.py`/`vardiyalar_tab.py`'deki isme bağlı widget key'leri (`key=f"izin_{p}"` vb.) yüzünden `StreamlitDuplicateElementKey` ile çöküyor — genel bir desen sorunu, isme bağlı key kullanan her sekme için geçerli.

---

## Test Envanteri (Faz 2)

| Dosya | Test sayısı |
|---|---|
| `test_g2_1_staffing_taban_tavan.py` + `test_g2_1_apptest.py` | 10 |
| `test_g2_2_apptest.py` | 2 |
| `test_g2_3_cozum_karnesi.py` | 4 |
| `test_g2_4_bos_slot.py` | 5 |
| `test_g2_5_kayit_hatalari.py` | 3 |
| `test_g2_6_girdi_dogrula.py` | 12 |
| `test_g2_7_hedef_sessiz_donusumler.py` | 4 |
| `test_g2_8_soft_want_pair.py` | 3 |
| `test_g2_9_teshis_false_positive.py` | 5 |
| `test_g2_10_kucuk_durustluk.py` | 9 |
| **Toplam (yeni, Faz 2)** | **57** |

Faz 0-1'den devralınan 86 test + Faz 2'nin 57 testi = **143 test**, tam suite'te tek bir başarısızlık olmadan yeşil.
