"""
G2.1 - UI on kontrolunu Faz 1 davranisiyla hizala (AppTest).

Faz 2 protokolu geregi UI degisikliklerinde MUMKUNSE AppTest kullanilir.
Ortak kurulum (session_state, storage izolasyonu) icin bkz. _apptest_helpers.py.
"""
import pytest

from tests._apptest_helpers import apptest_calistir, nobet_olustur_butonu


@pytest.mark.yavas
def test_hedef_tabanin_altinda_uyari_ve_cozum_calisir(tmp_path, monkeypatch):
    """
    3 kişi, hedef=2 (toplam 6); vardiya minimum_staffing=3, 30 gün ->
    zorunlu taban = 90. Toplam hedef << taban.
    G1.3 öncesi bu durum st.error + st.stop() ile ENGELLENİYORDU.
    G2.1 sonrası: solver ÇALIŞIR, çözüm gösterilir, uyarı görünür.
    """
    at = apptest_calistir(tmp_path, monkeypatch, {})
    nobet_olustur_butonu(at).click().run(timeout=60)
    assert not at.exception, f"Çözüm sırasında hata: {[str(e) for e in at.exception]}"

    warning_texts = " ".join(w.value for w in at.warning)
    assert "zorunlu doluluk tabanının" in warning_texts
    assert "90" in warning_texts

    success_texts = " ".join(s.value for s in at.success)
    assert "Çözüm bulundu" in success_texts


@pytest.mark.yavas
def test_hedef_aralikta_uyari_yok(tmp_path, monkeypatch):
    """Toplam hedef taban-tavan aralığındaysa hiçbir staffing uyarısı çıkmamalı."""
    at = apptest_calistir(tmp_path, monkeypatch, {
        "varsayilan_hedef": 30,  # 3 kisi x 30 = 90 = tam taban
    })
    nobet_olustur_butonu(at).click().run(timeout=60)
    assert not at.exception, f"Çözüm sırasında hata: {[str(e) for e in at.exception]}"

    warning_texts = " ".join(w.value for w in at.warning)
    assert "zorunlu doluluk tabanının" not in warning_texts
    assert "teorik doluluk tavanının" not in warning_texts
