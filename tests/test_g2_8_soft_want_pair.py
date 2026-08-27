"""
G2.8 - Soft want-pair girilebilir olsun.

"Minimum birlikte gun" min_value=1 idi - UI'dan soft (zorunlu olmayan)
birlikte-calisma tercihi girmek IMKANSIZDI; her want-pair hard doguyordu
(solver semantigi: min_k=0 -> yalnizca odul; min_k>0 -> hard alt sinir).
min_value=0 yapildi, varsayilan 0; liste gosteriminde min:0 icin
"tercih", min>0 icin "zorunlu >=N" etiketi eklendi.
"""
from tests._apptest_helpers import from_function_izole


def _eslesmeler_tab_render_bos():
    import streamlit as st

    # st.rerun() (Ekle butonu) ayni sarmalayiciyi YENIDEN calistirir; bu
    # yuzden kurulum yalnizca ILK calismada yapilir (aksi halde her
    # rerun'da want_pairs_list sifirlanip eklenen kayit kaybolur).
    if "_test_init" not in st.session_state:
        st.session_state["_test_init"] = True
        st.session_state["personel_list"] = ["Ahmet", "Mehmet"]
        st.session_state["want_pairs_list"] = []
        st.session_state["no_pairs_list"] = []
        st.session_state["soft_no_pairs_list"] = []
        st.session_state["ardisik_yasak"] = True
        st.session_state["gunasiri_limit_aktif"] = True
        st.session_state["max_gunasiri"] = 1
        st.session_state["hafta_sonu_dengesi"] = True
        st.session_state["w_cuma"] = 1000
        st.session_state["w_cumartesi"] = 1000
        st.session_state["w_pazar"] = 1000
        st.session_state["tatil_dengesi"] = True
        st.session_state["iki_gun_bosluk_aktif"] = True
        st.session_state["w_gap3"] = 300

    from tabs.eslesmeler_tab import render_eslesmeler_tab
    render_eslesmeler_tab()


def test_min_0_ciftle_tercih_etiketi_ve_kalici_kayit(monkeypatch):
    at = from_function_izole(_eslesmeler_tab_render_bos, monkeypatch, default_timeout=30)
    assert not at.exception

    # Varsayilan min degeri artik 0 olmali
    min_kutusu = next(n for n in at.number_input if n.key == "wp_min")
    assert min_kutusu.value == 0

    ekle_butonu = next(b for b in at.button if b.key == "wp_add")
    ekle_butonu.click().run()
    assert not at.exception

    assert at.session_state["want_pairs_list"] == [{"a": "Ahmet", "b": "Mehmet", "min": 0}]

    markdown_texts = " ".join(m.value for m in at.markdown)
    assert "tercih" in markdown_texts
    assert "zorunlu" not in markdown_texts


def _eslesmeler_tab_render_mevcut_kayitli():
    import streamlit as st

    st.session_state["personel_list"] = ["Ahmet", "Mehmet", "Zeynep"]
    st.session_state["want_pairs_list"] = [{"a": "Ahmet", "b": "Mehmet", "min": 3}]
    st.session_state["no_pairs_list"] = []
    st.session_state["soft_no_pairs_list"] = []
    st.session_state["ardisik_yasak"] = True
    st.session_state["gunasiri_limit_aktif"] = True
    st.session_state["max_gunasiri"] = 1
    st.session_state["hafta_sonu_dengesi"] = True
    st.session_state["w_cuma"] = 1000
    st.session_state["w_cumartesi"] = 1000
    st.session_state["w_pazar"] = 1000
    st.session_state["tatil_dengesi"] = True
    st.session_state["iki_gun_bosluk_aktif"] = True
    st.session_state["w_gap3"] = 300

    from tabs.eslesmeler_tab import render_eslesmeler_tab
    render_eslesmeler_tab()


def test_mevcut_kayitli_min_1_ustu_cift_geriye_uyumlu_yuklenir(monkeypatch):
    """Mevcut kayıtlı ayarlarda min>=1 çiftler aynen yüklenir (geriye uyumluluk)."""
    at = from_function_izole(_eslesmeler_tab_render_mevcut_kayitli, monkeypatch, default_timeout=30)
    assert not at.exception

    assert at.session_state["want_pairs_list"] == [{"a": "Ahmet", "b": "Mehmet", "min": 3}]

    markdown_texts = " ".join(m.value for m in at.markdown)
    assert "zorunlu ≥3" in markdown_texts


class _SahteSolver:
    son_birlikte_tut = None

    def __init__(self, solver_input):
        _SahteSolver.son_birlikte_tut = list(solver_input.birlikte_tut)
        self.cozum_meta = {"status": "OPTIMAL", "sure_saniye": 0.01, "objective": 0.0, "optimal": True}
        self.uyarilar = []

    def coz(self):
        return {1: []}


def _cozum_tab_calistir_soft_want_pair():
    import streamlit as st

    st.session_state["yil"] = 2025
    st.session_state["ay"] = 6
    st.session_state["personel_list"] = ["Ahmet", "Mehmet"]
    st.session_state["varsayilan_hedef"] = 7
    st.session_state["personel_targets"] = {}
    st.session_state["otomatik_hedef"] = False
    st.session_state["izin_map"] = {}
    st.session_state["prefer_map"] = {}
    st.session_state["manuel_tatiller"] = ""
    st.session_state["weekday_block_map"] = {}
    st.session_state["no_pairs_list"] = []
    st.session_state["want_pairs_list"] = [{"a": "Ahmet", "b": "Mehmet", "min": 0}]
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


def test_solver_girdisinde_birlikte_tut_uclusunde_sifir(monkeypatch):
    import tabs.cozum_tab as cozum_tab_modul

    _SahteSolver.son_birlikte_tut = None
    monkeypatch.setattr(cozum_tab_modul, "NobetSolver", _SahteSolver)

    at = from_function_izole(_cozum_tab_calistir_soft_want_pair, monkeypatch, default_timeout=30)
    assert not at.exception, f"Beklenmeyen hata: {[str(e) for e in at.exception]}"

    assert _SahteSolver.son_birlikte_tut == [("Ahmet", "Mehmet", 0)]
