"""
Sidebar — Veri yönetimi, kaydetme/yükleme, demo modu.
"""

import streamlit as st
from datetime import datetime

from storage import (
    ayarlari_kaydet, ayarlari_yukle_veya_varsayilan,
    kayitli_planlari_listele, ayarlari_json_olarak_export,
    ayarlari_json_dan_import
)
from streamlit_integration import get_demo_sidebar


def render_sidebar(session_to_ayarlar_func):
    """
    Sidebar render fonksiyonu.

    Args:
        session_to_ayarlar_func: app.py'deki session_to_ayarlar() fonksiyonu.
    """
    with st.sidebar:
        st.header("💾 Veri Yönetimi")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Kaydet", use_container_width=True, help="Ayarları kaydet"):
                ayarlar = session_to_ayarlar_func()
                if ayarlari_kaydet(ayarlar):
                    st.success("✓ Kaydedildi")
                else:
                    st.error("Kaydetme hatası")

        with col2:
            if st.button("🔄 Yükle", use_container_width=True, help="Kayıtlı ayarları yükle"):
                st.session_state.clear()
                st.rerun()

        st.divider()

        # JSON Export/Import
        with st.expander("📤 Dışa/İçe Aktar"):
            ayarlar = session_to_ayarlar_func()
            json_str = ayarlari_json_olarak_export(ayarlar)

            st.download_button(
                "⬇️ Ayarları İndir (JSON)",
                data=json_str,
                file_name="nobet_ayarlari.json",
                mime="application/json"
            )

            uploaded = st.file_uploader("Ayar dosyası yükle", type=["json"])
            if uploaded:
                content = uploaded.read().decode("utf-8")
                loaded = ayarlari_json_dan_import(content)
                if loaded:
                    ayarlari_kaydet(loaded)
                    st.success("Ayarlar yüklendi! Sayfayı yenileyin.")
                    if st.button("🔄 Yenile"):
                        st.session_state.clear()
                        st.rerun()

        st.divider()

        # Geçmiş planlar
        st.subheader("📅 Geçmiş Planlar")
        planlar = kayitli_planlari_listele()

        if planlar:
            for plan in planlar[:5]:  # Son 5 plan
                ay_adi = datetime(plan["yil"], plan["ay"], 1).strftime("%B %Y")
                durum = "✓" if plan["sonuc_var"] else "○"
                st.caption(f"{durum} {ay_adi}")
        else:
            st.caption("Henüz kaydedilmiş plan yok")

        # Demo Senaryo Kontrolleri
        get_demo_sidebar()
