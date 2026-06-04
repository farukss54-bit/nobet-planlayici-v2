"""
İzinler sekmesi — İzin, tercih, bloklu gün ve tatil yönetimi.
"""

import streamlit as st
from utils import (
    ay_gun_sayisi, resmi_tatiller, gun_parse,
    tum_hafta_gunleri, hafta_gunu_numarasi
)


def render_izinler_tab():
    st.subheader("🏖️ İzinler ve Tercihler")

    personeller = st.session_state.get("personel_list", [])

    if not personeller:
        st.warning("Önce Kişiler sekmesinde personel listesini girin.")
    else:
        yil = int(st.session_state["yil"])
        ay = int(st.session_state["ay"])
        gun_sayisi = ay_gun_sayisi(yil, ay)
        gun_listesi = list(range(1, gun_sayisi + 1))

        # İzin map'i hazırla
        izin_map = st.session_state.get("izin_map", {})
        izin_map = {k: v for k, v in izin_map.items() if k in personeller}
        for p in personeller:
            izin_map.setdefault(p, set())
        st.session_state["izin_map"] = izin_map

        # Her personel için izin girişi
        for p in personeller:
            with st.expander(f"📅 {p}", expanded=False):
                selected = st.multiselect(
                    "İzinli günler",
                    options=gun_listesi,
                    default=sorted(list(st.session_state["izin_map"].get(p, set()))),
                    key=f"izin_{p}"
                )
                st.session_state["izin_map"][p] = set(selected)

                # Bloklu hafta günleri
                gun_adlari = tum_hafta_gunleri()
                st.session_state["weekday_block_map"].setdefault(p, [])
                # Sadece geçerli gün adlarını default olarak al
                mevcut_bloklar = st.session_state["weekday_block_map"].get(p, [])
                valid_bloklar = [g for g in mevcut_bloklar if g in gun_adlari]
                blocked = st.multiselect(
                    "Bloklu hafta günleri (her hafta)",
                    options=gun_adlari,
                    default=valid_bloklar,
                    key=f"wblock_{p}"
                )
                st.session_state["weekday_block_map"][p] = blocked

                # Tercih edilen günler
                st.session_state.setdefault("prefer_map", {}).setdefault(p, [])
                prefer_selected = st.multiselect(
                    "Tercih edilen günler (soft)",
                    options=gun_listesi,
                    default=sorted(list(set(st.session_state["prefer_map"].get(p, [])))),
                    key=f"prefer_{p}"
                )
                st.session_state["prefer_map"][p] = sorted(prefer_selected)

        st.divider()
        toplam_izin = sum(len(v) for v in st.session_state["izin_map"].values())
        st.caption(f"✓ Toplam izin günü: {toplam_izin}")

        # Tatiller
        st.divider()
        st.subheader("🎌 Resmi Tatiller")

        auto_holidays = resmi_tatiller(yil, ay)

        if auto_holidays:
            st.success("✓ Bu ay için otomatik tespit edilen tatiller:")
            for gun, isim in sorted(auto_holidays.items()):
                st.write(f"  • {gun}. gün - {isim}")
        else:
            st.info("Bu ay resmi tatil bulunmuyor.")

        manuel_input = st.text_input(
            "Ekstra tatil günleri (örn: 15, 16)",
            value=st.session_state.get("manuel_tatiller", ""),
            key="manuel_tatiller_input"
        )
        st.session_state["manuel_tatiller"] = manuel_input

        if manuel_input.strip():
            manuel_gunler = gun_parse(manuel_input, gun_sayisi)
            if manuel_gunler:
                st.caption(f"  → Eklenecek: {sorted(manuel_gunler)}")
