import streamlit as st

from design import inject_css, render_stepper
from pages import dashboard

"""
app.py — Nöbet Planlayıcı v2 ana giriş noktası.

Bu dosya yalnızca üst düzey navigasyonu ve sayfa yönlendirmeyi yönetir.
Ekranların içeriği ilerleyen adımlarda pages/ altındaki modüllerden çağrılacaktır.
Backend dosyalarına dokunulmamıştır.
"""

st.set_page_config(
    page_title="Nöbet Planlayıcı",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()

SAYFA_SECENEKLERI = ["Dashboard", "Yeni Plan", "Kurum Ayarları"]
SAYFA_KEY_MAP = {
    "Dashboard": "dashboard",
    "Yeni Plan": "plan",
    "Kurum Ayarları": "settings",
}
SAYFA_LABEL_MAP = {v: k for k, v in SAYFA_KEY_MAP.items()}


def _init_session_state() -> None:
    """Uygulama oturum değişkenlerini başlatır."""
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    if "plan_step" not in st.session_state:
        st.session_state.plan_step = 0


def _nav_changed() -> None:
    """Navigasyon radio butonu değiştiğinde aktif sayfayı günceller."""
    secili_label = st.session_state.nav_radio
    yeni_sayfa = SAYFA_KEY_MAP[secili_label]

    if yeni_sayfa == "plan":
        st.session_state.plan_step = 0

    st.session_state.page = yeni_sayfa


def _render_header() -> None:
    """Üst başlık ve açıklamayı gösterir."""
    st.markdown(
        """
        <div class="page-header">
            <h1>Nöbet Planlama Merkezi</h1>
            <p>Acil Servis Vardiya Optimizasyonu</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_dummy_navigation() -> None:
    """Placeholder sayfalar için basit navigasyon"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Geri", type="secondary"):
            st.session_state.plan_step = max(0, st.session_state.plan_step - 1)
            st.rerun()
    with col3:
        if st.button("İleri →", type="primary"):
            st.session_state.plan_step = min(3, st.session_state.plan_step + 1)
            st.rerun()


def _render_plan_pages() -> None:
    """Plan akışı sayfalarını yönlendirir"""
    if st.session_state.plan_step == 0:
        from pages import plan_ekip
        plan_ekip.show_plan_ekip()
    elif st.session_state.plan_step == 1:
        from pages import plan_izinler
        plan_izinler.show_plan_izinler()
    elif st.session_state.plan_step == 2:
        st.markdown(render_stepper(3, 4), unsafe_allow_html=True)
        st.info("Kurallar sayfası henüz implemente edilmedi.")
        _render_dummy_navigation()
    elif st.session_state.plan_step == 3:
        st.markdown(render_stepper(4, 4), unsafe_allow_html=True)
        st.info("Çizelge sayfası henüz implemente edilmedi.")
        _render_dummy_navigation()


def _render_settings_placeholder() -> None:
    """Kurum ayarları ekranı için yer tutucu (Adım 7'de doldurulacak)."""
    st.markdown("## Kurum Ayarları")
    st.info("Kurum ayarları buraya eklenecek (Adım 7).")


def main() -> None:
    """Uygulama ana giriş noktası."""
    _init_session_state()
    _render_header()

    mevcut_label = SAYFA_LABEL_MAP.get(st.session_state.page, "Dashboard")

    st.radio(
        "Navigasyon",
        SAYFA_SECENEKLERI,
        index=SAYFA_SECENEKLERI.index(mevcut_label),
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio",
        on_change=_nav_changed,
    )

    if st.session_state.page == "dashboard":
        dashboard.show_dashboard()
    elif st.session_state.page == "plan":
        _render_plan_pages()
    elif st.session_state.page == "settings":
        _render_settings_placeholder()
    else:
        # Bilinmeyen sayfa durumunda dashboard'a dön
        st.session_state.page = "dashboard"
        st.rerun()


if __name__ == "__main__":
    main()
