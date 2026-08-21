import streamlit as st

"""
design.py — Nöbet Planlayıcı v2 UI/UX bileşenleri ve stil enjeksiyonu.

Bu modül, DESIGN.md spesifikasyonundaki renk paleti, kart yapısı,
badge'ler ve stepper bileşenlerini merkezi olarak sunar.
"""

COLORS = {
    "bg": "#f5f3f0",
    "surface": "#ffffff",
    "surface_hover": "#faf9f7",
    "border": "#e8e5e0",
    "text_primary": "#1a1a2e",
    "text_secondary": "#6b6b7b",
    "text_tertiary": "#9a9aa8",
    "accent": "#0d7c8a",
    "accent_light": "#e6f4f5",
    "success": "#2e7d32",
    "warning": "#ed6c02",
    "danger": "#c62828",
    "kidis": {
        "kidemli": "#1565c0",
        "orta": "#6b5bd2",
        "yeni": "#c2185b",
    },
    "alan": {
        "yesil": "#4caf50",
        "sari": "#ff9800",
        "kirmizi": "#f44336",
    },
}


def inject_css() -> None:
    """
    Uygulama genelinde kullanılan CSS kurallarını Streamlit'e enjekte eder.
    DESIGN.md Bölüm 6'daki şablonu temel alır.
    """
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #f5f3f0;
            }

            .main .block-container {
                padding: 2rem 3rem;
                max-width: 1200px;
            }

            /* Kart yapısı */
            .card {
                background: #ffffff;
                border: 1px solid #e8e5e0;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 16px;
            }
            .card-title {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 14px;
                font-weight: 600;
                color: #1a1a2e;
                margin-bottom: 12px;
            }
            .card-subtitle {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 11px;
                font-weight: 400;
                color: #6b6b7b;
                margin-top: -8px;
                margin-bottom: 12px;
            }
            .card-content {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
                color: #1a1a2e;
            }

            /* Badge'ler */
            .badge {
                display: inline-flex;
                align-items: center;
                padding: 2px 10px;
                border-radius: 20px;
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 11px;
                font-weight: 500;
                line-height: 1.4;
            }
            .badge-kidemli {
                background: #e3f2fd;
                color: #1565c0;
            }
            .badge-orta {
                background: #ede7f6;
                color: #6b5bd2;
            }
            .badge-yeni {
                background: #f8bbd0;
                color: #c2185b;
            }
            .badge-alan-yesil {
                background: #e8f5e9;
                color: #2e7d32;
            }
            .badge-alan-sari {
                background: #fff3e0;
                color: #ed6c02;
            }
            .badge-alan-kirmizi {
                background: #ffebee;
                color: #c62828;
            }
            .badge-success {
                background: #e8f5e9;
                color: #2e7d32;
            }
            .badge-warning {
                background: #fff3e0;
                color: #ed6c02;
            }
            .badge-muted {
                background: #f5f5f5;
                color: #6b6b7b;
            }

            /* Dashboard CTA kartı */
            .card-cta {
                background: #ffffff;
                border: 2px dashed #e8e5e0;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 16px;
                text-align: center;
            }
            .card-cta:hover {
                border-color: #0d7c8a;
                background: #e6f4f5;
            }

            /* Adım şeridi */
            .stepper {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 24px;
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            .step {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .step-circle {
                width: 28px;
                height: 28px;
                border-radius: 50%;
                border: 2px solid #e8e5e0;
                background: #ffffff;
                color: #6b6b7b;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 11px;
                font-weight: 600;
                flex-shrink: 0;
            }
            .step-circle.done {
                background: #2e7d32;
                border-color: #2e7d32;
                color: #ffffff;
            }
            .step-circle.active {
                background: #1a1a2e;
                border-color: #1a1a2e;
                color: #ffffff;
            }
            .step-label {
                font-size: 12px;
                font-weight: 500;
                color: #6b6b7b;
            }
            .step-label.active {
                color: #1a1a2e;
                font-weight: 600;
            }
            .step-label.done {
                color: #2e7d32;
            }
            .step-line {
                flex-grow: 0;
                width: 24px;
                height: 2px;
                background: #e8e5e0;
                margin: 0 4px;
            }
            .step-line.done {
                background: #2e7d32;
            }

            /* Sayfa başlığı */
            .page-header {
                margin-bottom: 24px;
            }
            .page-header h1 {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 16px;
                font-weight: 600;
                color: #1a1a2e;
                margin: 0 0 4px 0;
            }
            .page-header p {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 12px;
                color: #6b6b7b;
                margin: 0;
            }

            /* Streamlit metin renkleri (kontrast düzeltmesi) */
            .stMarkdown, .stMarkdown p {
                color: #1a1a2e !important;
            }
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
                color: #1a1a2e !important;
            }
            [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
                color: #6b6b7b !important;
            }

            /* Radio butonları (navigasyon) - tüm iç elementler */
            .stRadio,
            .stRadio *,
            .stRadio label,
            .stRadio [role="radiogroup"] label,
            .stRadio [data-baseweb="radio"] > div,
            .stRadio [data-baseweb="radio"] label,
            .stRadio div[role="radiogroup"] label p,
            .stRadio p {
                color: #1a1a2e !important;
            }
            .stRadio label {
                font-weight: 500 !important;
            }

            /* Subheader'lar */
            [data-testid="stHeadingWithActionElements"],
            .stHeadingContainer h1,
            .stHeadingContainer h2,
            .stHeadingContainer h3 {
                color: #1a1a2e !important;
            }

            /* Streamlit widget override'ları */
            .stDataFrame th {
                background: #faf9f7 !important;
                font-family: monospace !important;
                font-size: 10px !important;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: #9a9aa8 !important;
            }
            .stTextInput input,
            .stNumberInput input {
                border-radius: 6px !important;
                border: 1px solid #e8e5e0 !important;
            }
            .stButton button[kind="primary"] {
                background: #1a1a2e !important;
                color: #ffffff !important;
                border-radius: 10px !important;
            }
            .stButton button[kind="secondary"] {
                background: #ffffff !important;
                color: #1a1a2e !important;
                border: 1px solid #e8e5e0 !important;
                border-radius: 10px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_stepper(aktif_adim: int, toplam_adim: int) -> str:
    """
    Yatay adım şeridi HTML'i döndürür.

    Parametreler:
        aktif_adim: 1'den başlayan, şu anki adım numarası.
        toplam_adim: Toplam adım sayısı.

    Adım isimleri: Ekip → İzinler → Kurallar → Çizelge.
    """
    adim_isimleri = ["Ekip", "İzinler", "Kurallar", "Çizelge"]
    html_parcalari = ['<div class="stepper">']

    for i in range(1, toplam_adim + 1):
        isim = adim_isimleri[i - 1] if i <= len(adim_isimleri) else f"Adım {i}"

        if i < aktif_adim:
            durum = "done"
            icerik = "✓"
        elif i == aktif_adim:
            durum = "active"
            icerik = str(i)
        else:
            durum = ""
            icerik = str(i)

        html_parcalari.append(
            f'<div class="step">'
            f'<div class="step-circle {durum}">{icerik}</div>'
            f'<span class="step-label {durum}">{isim}</span>'
            f'</div>'
        )

        if i < toplam_adim:
            cizgi_durum = "done" if i < aktif_adim else ""
            html_parcalari.append(f'<div class="step-line {cizgi_durum}"></div>')

    html_parcalari.append("</div>")
    return "".join(html_parcalari)


def render_card(baslik: str | None, icerik: str) -> str:
    """
    Beyaz kart kutusu içinde HTML içeriği döndürür.

    Parametreler:
        baslik: Kart üstünde gösterilecek başlık. None ise başlık kısmı oluşturulmaz.
        icerik: Kart gövdesinde gösterilecek HTML içeriği.
    """
    baslik_html = f'<div class="card-title">{baslik}</div>' if baslik else ""
    return (
        f'<div class="card">'
        f'{baslik_html}'
        f'<div class="card-content">{icerik}</div>'
        f'</div>'
    )


def render_badge(metin: str, badge_sinifi: str) -> str:
    """
    Renkli badge HTML'i döndürür.

    Parametreler:
        metin: Badge içindeki metin.
        badge_sinifi: CSS class adı; örn. "badge-kidemli", "badge-orta", "badge-yeni".
    """
    return f'<span class="badge {badge_sinifi}">{metin}</span>'
