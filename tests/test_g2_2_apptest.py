"""
G2.2 - Hata sınıflarını ayır: bilinçli red != çökme.

tabs/cozum_tab.py'de tek `except Exception` yolu üçe ayrıldı:
1. ValueError (G1.2 pre-solve doğrulaması VEYA solver INFEASIBLE) ->
   "Girdi kuralları çözümü engelliyor" + teşhis çalışır.
2. (aynı ValueError yolu) solver.cozum_meta["status"] varsa mesajda kullanılır.
3. Diğer her şey (TypeError, KeyError, ...) -> "Beklenmedik uygulama hatası"
   + st.exception(traceback). TEŞHİS ÇALIŞTIRILMAZ.
"""
import pytest

import solver as solver_modul
from tests._apptest_helpers import apptest_calistir, nobet_olustur_butonu


@pytest.mark.yavas
def test_deger_hatasi_girdi_kurali_teshis_calisir(tmp_path, monkeypatch):
    """Hedef > kişisel maksimum (G1.2 pre-solve ValueError) -> yol 1: teşhis çalışır."""
    at = apptest_calistir(tmp_path, monkeypatch, {
        "personel_list": ["Ahmet"],
        "personel_targets": {"Ahmet": 31},  # personel_tab widget ust siniri 31
        "ardisik_yasak": True,
        "gunasiri_limit_aktif": True,
        "max_gunasiri": 1,
        "vardiya_tipleri": [],
    })
    nobet_olustur_butonu(at).click().run(timeout=30)
    assert not at.exception, f"Beklenmeyen üst seviye hata: {[str(e) for e in at.exception]}"

    error_texts = " ".join(e.value for e in at.error)
    assert "Girdi kuralları çözümü engelliyor" in error_texts

    warning_texts = " ".join(w.value for w in at.warning)
    assert "Tespit Edilen Sorunlar" in warning_texts


@pytest.mark.yavas
def test_kod_hatasi_teshis_calismaz(tmp_path, monkeypatch):
    """solver.coz() TypeError fırlatırsa -> yol 3: traceback görünür, teşhis YOK."""
    def _bozuk_coz(self):
        raise TypeError("Kasıtlı kod hatası (test)")

    monkeypatch.setattr(solver_modul.NobetSolver, "coz", _bozuk_coz)

    at = apptest_calistir(tmp_path, monkeypatch, {})
    nobet_olustur_butonu(at).click().run(timeout=30)

    error_texts = " ".join(e.value for e in at.error)
    assert "Beklenmedik uygulama hatası" in error_texts

    warning_texts = " ".join(w.value for w in at.warning)
    assert "Tespit Edilen Sorunlar" not in warning_texts

    assert len(at.exception) >= 1
    assert "Kasıtlı kod hatası" in str(at.exception[0].value)
