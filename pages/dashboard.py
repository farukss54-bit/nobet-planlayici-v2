import streamlit as st
from datetime import datetime

from design import render_badge, render_card

"""
pages/dashboard.py — Dashboard ekranı.

Kullanıcı uygulamayı açtığında mevcut, geçmiş ve oluşturulmamış plan kartlarını görür.
Veri kaynağı şimdilik mock veridir; ilerleyen adımlarda backend/storage entegrasyonu yapılacaktır.
"""

AYLAR = [
    "",
    "Ocak",
    "Şubat",
    "Mart",
    "Nisan",
    "Mayıs",
    "Haziran",
    "Temmuz",
    "Ağustos",
    "Eylül",
    "Ekim",
    "Kasım",
    "Aralık",
]

DURUM_STILI = {
    "hazır": ("badge-success", "Hazır"),
    "oluşturulmadı": ("badge-warning", "Oluşturulmadı"),
    "geçmiş": ("badge-muted", "Geçmiş"),
}

MOCK_PLANLAR = [
    {
        "ay": "Ağustos 2026",
        "durum": "oluşturulmadı",
        "personel": 12,
        "alan": 3,
        "vardiya": 2,
        "ihlal": None,
        "sure": None,
    },
    {
        "ay": "Temmuz 2026",
        "durum": "hazır",
        "personel": 12,
        "alan": 3,
        "vardiya": 2,
        "ihlal": 1,
        "sure": 4.2,
    },
    {
        "ay": "Haziran 2026",
        "durum": "geçmiş",
        "personel": 10,
        "alan": 3,
        "vardiya": 2,
        "ihlal": 0,
        "sure": 3.8,
    },
]


def _yeni_plan_baslat() -> None:
    """Yeni Plan akışının ilk adımına geçer."""
    st.session_state.page = "plan"
    st.session_state.plan_step = 0
    st.rerun()


def show_dashboard() -> None:
    """Dashboard ekranını çizer."""
    # Sağ üstte aktif ay pill'i
    ust_sutunlar = st.columns([6, 1])
    with ust_sutunlar[1]:
        simdi = datetime.now()
        ay_metni = f"{AYLAR[simdi.month]} {simdi.year}"
        st.markdown(render_badge(ay_metni, "badge-orta"), unsafe_allow_html=True)

    st.markdown("## Planlar")

    # 3 sütunlu plan kartları
    kart_sutunlari = st.columns(3)
    for indeks, plan in enumerate(MOCK_PLANLAR):
        with kart_sutunlari[indeks % 3]:
            _plan_karti_ciz(plan)

    # Alt CTA: yeni plan oluştur
    st.markdown('<div class="card-cta">', unsafe_allow_html=True)
    st.markdown("#### + Yeni Plan Oluştur")
    st.caption("Yeni bir ay için nöbet çizelgesi oluşturun")
    if st.button("Oluştur", key="cta_yeni_plan", type="primary", use_container_width=True):
        _yeni_plan_baslat()
    st.markdown("</div>", unsafe_allow_html=True)


def _plan_karti_ciz(plan: dict) -> None:
    """Tek bir plan kartını ve aksiyon butonlarını çizer."""
    badge_sinifi, badge_metni = DURUM_STILI[plan["durum"]]

    ihlal_metni = (
        f"İhlal: {plan['ihlal']}" if plan["ihlal"] is not None else "Henüz çözülmedi"
    )
    sure_metni = (
        f" · Çözüm süresi: {plan['sure']}s" if plan["sure"] is not None else ""
    )

    icerik = f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <strong>{plan["ay"]}</strong>
        {render_badge(badge_metni, badge_sinifi)}
    </div>
    <div style="color:#6b6b7b; font-size:12px; margin-bottom:8px;">
        {plan["personel"]} personel · {plan["alan"]} alan · {plan["vardiya"]} vardiya
    </div>
    <div style="color:#6b6b7b; font-size:12px;">
        {ihlal_metni}{sure_metni}
    </div>
    """

    st.markdown(render_card(None, icerik), unsafe_allow_html=True)

    # Kart aksiyonları
    olusturulmadi = plan["durum"] == "oluşturulmadı"
    b1, b2, b3 = st.columns(3)
    with b1:
        st.button(
            "İncele",
            key=f"incele_{plan['ay']}",
            disabled=olusturulmadi,
            use_container_width=True,
        )
    with b2:
        st.button(
            "Excel",
            key=f"excel_{plan['ay']}",
            disabled=olusturulmadi,
            use_container_width=True,
        )
    with b3:
        if st.button(
            "Plan Oluştur",
            key=f"olustur_{plan['ay']}",
            use_container_width=True,
        ):
            _yeni_plan_baslat()
