"""
G2.7 - Hedef girisinde sessiz donusumleri bitir.

Sorun A: Kisisel hedef varsayilana ESITSE siliniyordu -> kullanici bilincli
7 girdi, sistem "girilmemis" sayip otomatik/kidem zincirine dusuruyordu.
Cozum: personel_tab.py'ye "Oto" checkbox eklendi; isaretli DEGILSE deger
- varsayilana esit olsa bile - personel_targets'a yazilir.

Sorun B: Kisisel hedefi olan kisi, kidem grubunun vardiya kirilimini
sessizce kaybediyordu. Cozum: cozum_tab.py bu durumu tespit edip
st.info listesiyle gorunur kiliyor (kirilim yine de uygulanmiyor -
davranis icat edilmiyor, yalnizca gorunurluk).
"""
from tests._apptest_helpers import from_function_izole


def _personel_tab_render():
    # NOT: ASCII-only kaynak metin gerekiyor (AppTest.from_function ortam
    # kisitlamasi - bkz. test_g2_6_girdi_dogrula.py'deki not).
    import streamlit as st

    st.session_state["yil"] = 2025
    st.session_state["ay"] = 6
    st.session_state["personel_list"] = ["Ahmet"]
    st.session_state["personel_sayisi"] = 1
    st.session_state["varsayilan_hedef"] = 7
    st.session_state["personel_targets"] = {}
    st.session_state["otomatik_hedef"] = False

    from tabs.personel_tab import render_personel_tab
    render_personel_tab(session_to_ayarlar_func=None)


def test_oto_kapali_ve_varsayilana_esit_deger_kalici_yazilir(monkeypatch):
    at = from_function_izole(_personel_tab_render, monkeypatch, default_timeout=30)
    assert not at.exception

    oto_kutusu = next(c for c in at.checkbox if c.key == "oto_hedef_0")
    assert oto_kutusu.value is True  # kisisel kayit yokken varsayilan: isaretli

    oto_kutusu.set_value(False).run()
    assert not at.exception

    hedef_kutusu = next(n for n in at.number_input if n.key == "target_0")
    hedef_kutusu.set_value(7).run()
    assert not at.exception

    assert at.session_state["personel_targets"].get("Ahmet") == 7


def _personel_tab_render_iki_kisi():
    import streamlit as st

    st.session_state["yil"] = 2025
    st.session_state["ay"] = 6
    st.session_state["personel_list"] = ["Ahmet", "Mehmet"]
    st.session_state["personel_sayisi"] = 2
    st.session_state["varsayilan_hedef"] = 7
    st.session_state["personel_targets"] = {}
    st.session_state["otomatik_hedef"] = False

    from tabs.personel_tab import render_personel_tab
    render_personel_tab(session_to_ayarlar_func=None)


def test_varsayilan_hedef_degisince_bildirim_gorunur(monkeypatch):
    at = from_function_izole(_personel_tab_render_iki_kisi, monkeypatch, default_timeout=30)
    assert not at.exception

    varsayilan_kutusu = next(n for n in at.number_input if n.key == "varsayilan_hedef_input")
    varsayilan_kutusu.set_value(10).run()
    assert not at.exception

    info_texts = " ".join(i.value for i in at.info)
    assert "Varsayılan hedef değişti" in info_texts
    assert "2 kişinin hedefi güncellendi" in info_texts


class _SahteSolver:
    """NobetSolver yerine gecen, gercek CP-SAT cozumu yapmayan casus."""
    son_hedefler = None

    def __init__(self, solver_input):
        self._solver_input = solver_input
        _SahteSolver.son_hedefler = dict(solver_input.hedefler)
        self.cozum_meta = {"status": "OPTIMAL", "sure_saniye": 0.01, "objective": 0.0, "optimal": True}
        self.uyarilar = []

    def coz(self):
        alanlar = self._solver_input.alanlar
        vardiyalar = self._solver_input.vardiyalar
        if alanlar and vardiyalar:
            return {1: {a.isim: {v.isim: [] for v in vardiyalar} for a in alanlar}}
        elif vardiyalar:
            return {1: {v.isim: [] for v in vardiyalar}}
        elif alanlar:
            return {1: {a.isim: [] for a in alanlar}}
        return {1: []}


def _cozum_tab_calistir_kisisel_hedefli():
    import streamlit as st

    st.session_state["yil"] = 2025
    st.session_state["ay"] = 6
    st.session_state["personel_list"] = ["Ahmet"]
    st.session_state["varsayilan_hedef"] = 7
    st.session_state["personel_targets"] = {"Ahmet": 7}
    st.session_state["otomatik_hedef"] = True
    st.session_state["izin_map"] = {}
    st.session_state["prefer_map"] = {}
    st.session_state["manuel_tatiller"] = ""
    st.session_state["weekday_block_map"] = {}
    st.session_state["no_pairs_list"] = []
    st.session_state["want_pairs_list"] = []
    st.session_state["soft_no_pairs_list"] = []
    st.session_state["alan_modu_aktif"] = False
    st.session_state["alanlar"] = []
    st.session_state["vardiya_tipleri"] = []
    st.session_state["personel_alan_yetkinlikleri"] = {}
    st.session_state["personel_vardiya_kisitlari"] = {}
    st.session_state["personel_kidem_gruplari"] = {}
    st.session_state["kidem_gruplari"] = []
    st.session_state["ardisik_yasak"] = False
    st.session_state["gunasiri_limit_aktif"] = False
    st.session_state["enforce_minimum_staffing"] = True
    st.session_state["hafta_sonu_dengesi"] = False
    st.session_state["tatil_dengesi"] = False
    st.session_state["iki_gun_bosluk_aktif"] = False
    st.session_state["saat_bazli_denge"] = True

    from tabs.cozum_tab import _cozum_olustur
    _cozum_olustur()


def test_kisisel_hedef_varken_otomatik_hedef_uygulanmaz(monkeypatch):
    import tabs.cozum_tab as cozum_tab_modul

    _SahteSolver.son_hedefler = None
    monkeypatch.setattr(cozum_tab_modul, "NobetSolver", _SahteSolver)

    at = from_function_izole(_cozum_tab_calistir_kisisel_hedefli, monkeypatch, default_timeout=30)
    assert not at.exception, f"Beklenmeyen hata: {[str(e) for e in at.exception]}"

    assert _SahteSolver.son_hedefler is not None
    assert _SahteSolver.son_hedefler["Ahmet"] == 7


def test_kisisel_hedefli_grup_kirilimli_kisi_bilgi_listesinde_gecer(monkeypatch):
    """
    Birim testi: kisisel hedefi olan VE kidem grubunun vardiya kirilimi
    olan kisi -> vardiya_hedefleri'ne HIC girmez (kirilim uygulanmaz) ama
    bilgi listesinde adi gecer.

    cozum_tab.py'nin hedef zinciri ayri bir saf fonksiyon olarak
    disariya cikarilmadigi icin, gercek akisi izole calistirip
    NobetSolver'a giden SolverInput'u yakaliyoruz.
    """
    import tabs.cozum_tab as cozum_tab_modul

    _SahteSolver.son_hedefler = None
    monkeypatch.setattr(cozum_tab_modul, "NobetSolver", _SahteSolver)

    def _calistir():
        import streamlit as st

        st.session_state["yil"] = 2025
        st.session_state["ay"] = 6
        st.session_state["personel_list"] = ["Ahmet"]
        st.session_state["varsayilan_hedef"] = 7
        st.session_state["personel_targets"] = {"Ahmet": 9}
        st.session_state["otomatik_hedef"] = False
        st.session_state["izin_map"] = {}
        st.session_state["prefer_map"] = {}
        st.session_state["manuel_tatiller"] = ""
        st.session_state["weekday_block_map"] = {}
        st.session_state["no_pairs_list"] = []
        st.session_state["want_pairs_list"] = []
        st.session_state["soft_no_pairs_list"] = []
        st.session_state["alan_modu_aktif"] = False
        st.session_state["alanlar"] = []
        st.session_state["vardiya_tipleri"] = [
            {"isim": "V1", "baslangic": "08:00", "bitis": "16:00", "minimum_staffing": 0},
        ]
        st.session_state["personel_alan_yetkinlikleri"] = {}
        st.session_state["personel_vardiya_kisitlari"] = {}
        st.session_state["personel_kidem_gruplari"] = {"Ahmet": "K1"}
        st.session_state["kidem_gruplari"] = [
            {"isim": "K1", "varsayilan_hedef": 8, "vardiya_hedefleri": {"V1": 8}},
        ]
        st.session_state["ardisik_yasak"] = False
        st.session_state["gunasiri_limit_aktif"] = False
        st.session_state["enforce_minimum_staffing"] = False
        st.session_state["hafta_sonu_dengesi"] = False
        st.session_state["tatil_dengesi"] = False
        st.session_state["iki_gun_bosluk_aktif"] = False
        st.session_state["saat_bazli_denge"] = True

        from tabs.cozum_tab import _cozum_olustur
        _cozum_olustur()

    at = from_function_izole(_calistir, monkeypatch, default_timeout=30)
    assert not at.exception, f"Beklenmeyen hata: {[str(e) for e in at.exception]}"

    assert _SahteSolver.son_hedefler["Ahmet"] == 9

    info_texts = " ".join(i.value for i in at.info)
    assert "Ahmet" in info_texts
    assert "kişisel hedef" in info_texts
