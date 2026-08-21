import streamlit as st

from design import inject_css, render_stepper

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


def _render_dashboard_placeholder() -> None:
    """Dashboard ekranı için yer tutucu (Adım 2'de doldurulacak)."""
    st.markdown("## Dashboard")
    st.info("Dashboard ekranı buraya eklenecek (Adım 2).")

    _, cta_col, _ = st.columns([2, 1, 2])
    with cta_col:
        if st.button(
            "Yeni Plan Oluştur",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.page = "plan"
            st.session_state.plan_step = 0
            st.rerun()


def _render_plan_placeholder() -> None:
    """Yeni Plan akışı için yer tutucu (Adım 3-6'da doldurulacak)."""
    st.markdown(
        render_stepper(st.session_state.plan_step + 1, 4),
        unsafe_allow_html=True,
    )
    st.info("Plan akışı buraya eklenecek (Adım 3-6).")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Dashboard'a Dön", type="secondary"):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("İleri →"):
            st.session_state.plan_step = min(st.session_state.plan_step + 1, 3)
            st.rerun()


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
        _render_dashboard_placeholder()
    elif st.session_state.page == "plan":
        _render_plan_placeholder()
    elif st.session_state.page == "settings":
        _render_settings_placeholder()
    else:
        # Bilinmeyen sayfa durumunda dashboard'a dön
        st.session_state.page = "dashboard"
        st.rerun()


if __name__ == "__main__":
    main()
