"""
G2.3 - Cozum karnesi: status, sure, uyarilar.

Not (onemli): AppTest.from_function bu ortamda wrapper fonksiyonun
KAYNAK METNINI gecici bir dosyaya yazip utf-8 olarak geri okuyor;
yazma adimi platform varsayilan kodekini kullandigindan, wrapper
fonksiyonun kendi govdesinde (docstring/yorum/literal) Turkce karakter
olursa UnicodeDecodeError firlatiyor (dogrulandi - ortam kisitlamasi).
Bu yuzden asagidaki `_render_*` yardimci fonksiyonlari BILEREK ASCII
tutulmustur; gercek `_cozum_karnesi_goster` (tabs/cozum_tab.py, normal
import ile yuklenir) Turkce metinlerini oldugu gibi kullanmaya devam
eder ve test assertion'lari o gercek Turkce metinlere karsi calisir.
"""
import pytest

from tests._apptest_helpers import apptest_calistir, from_function_izole, nobet_olustur_butonu


@pytest.mark.yavas
def test_cozulebilir_senaryoda_karne_metrikleri_render_edilir(tmp_path, monkeypatch):
    """Durum/Süre/Toplam Hedef Sapması metrikleri gerçek çözüm akışında görünür."""
    at = apptest_calistir(tmp_path, monkeypatch, {
        "varsayilan_hedef": 30,  # tam taban -> OPTIMAL/FEASIBLE beklenir
    })
    nobet_olustur_butonu(at).click().run(timeout=60)
    assert not at.exception, f"Çözüm sırasında hata: {[str(e) for e in at.exception]}"

    metric_labels = {m.label for m in at.metric}
    assert "Durum" in metric_labels
    assert "Süre" in metric_labels
    assert "Toplam Hedef Sapması" in metric_labels

    durum_metric = next(m for m in at.metric if m.label == "Durum")
    assert "OPTIMAL" in durum_metric.value or "FEASIBLE" in durum_metric.value


def _render_karne_uyarili():
    from tabs.cozum_tab import _cozum_karnesi_goster

    class FakeSolver:
        cozum_meta = {"status": "OPTIMAL", "sure_saniye": 3.4}
        uyarilar = ["test kisisi: hedef girilmemis, serbest birakildi"]

    _cozum_karnesi_goster(FakeSolver(), toplam_sapma=2)


def test_uyarilar_varsa_gosterilir(monkeypatch):
    """solver.uyarilar doluysa uyarı bloğu render edilir (G1.3 kazanımı UI'a bağlandı)."""
    at = from_function_izole(_render_karne_uyarili, monkeypatch)
    assert not at.exception

    warning_texts = " ".join(w.value for w in at.warning)
    assert "test kisisi" in warning_texts


def _render_karne_uyarisiz_optimal():
    from tabs.cozum_tab import _cozum_karnesi_goster

    class FakeSolver:
        cozum_meta = {"status": "OPTIMAL", "sure_saniye": 3.4}
        uyarilar = []

    _cozum_karnesi_goster(FakeSolver(), toplam_sapma=0)


def test_uyarilar_yoksa_ve_optimal_ise_bilgi_notu_yok(monkeypatch):
    at = from_function_izole(_render_karne_uyarisiz_optimal, monkeypatch)
    assert not at.exception
    assert len(at.warning) == 0
    assert len(at.info) == 0


def _render_karne_feasible():
    from tabs.cozum_tab import _cozum_karnesi_goster

    class FakeSolver:
        cozum_meta = {"status": "FEASIBLE", "sure_saniye": 60.1}
        uyarilar = []

    _cozum_karnesi_goster(FakeSolver(), toplam_sapma=5)


def test_feasible_ise_sure_limiti_bilgi_notu_gorunur(monkeypatch):
    """FEASIBLE (OPTIMAL değil) durumunda süre limiti bilgilendirmesi görünmeli."""
    at = from_function_izole(_render_karne_feasible, monkeypatch)
    assert not at.exception

    info_texts = " ".join(i.value for i in at.info)
    assert "Süre limiti" in info_texts

    durum_metric = next(m for m in at.metric if m.label == "Durum")
    assert "FEASIBLE" in durum_metric.value
