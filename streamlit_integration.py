"""
streamlit_integration.py - Senin App'in için Streamlit Entegrasyonu

Bu modül, üretilen sentetik veriyi doğrudan senin session_state
anahtarlarına enjekte eder.

Kullanım:
    from streamlit_integration import get_demo_sidebar
    
    # Sidebar'a ekle (tek satır)
    get_demo_sidebar()
    
    # Artık st.session_state.personel_list, izin_map, vs. dolu
"""

import streamlit as st
from typing import Optional, Dict, Any
import json

from scenarios import (
    ScenarioGenerator,
    generate_quick_scenario,
    describe_scenario,
    save_scenario,
    load_scenario,
    HazirSenaryolar,
    ZORLUK_PROFILLERI
)


def inject_scenario_to_session_state(data: Dict[str, Any]) -> None:
    """
    Senaryo verisini doğrudan senin session_state anahtarlarına yazar.
    
    Bu fonksiyon çağrıldıktan sonra:
        st.session_state.personel_list          -> List[str]
        st.session_state.personel_targets       -> Dict[str, int]
        st.session_state.weekday_block_map      -> Dict[str, List[str]]
        st.session_state.want_pairs_list        -> List[{"a", "b", "min"}]
        st.session_state.no_pairs_list          -> List[{"a", "b"}]
        st.session_state.soft_no_pairs_list     -> List[{"a", "b"}]
        st.session_state.izin_map               -> Dict[str, Set[int]]
        st.session_state.prefer_map             -> Dict[str, Set[int]]
        st.session_state.manuel_tatiller        -> str
        st.session_state.alanlar                -> List[dict]
        st.session_state.alan_modu_aktif        -> bool
        st.session_state.alan_bazli_denklik     -> bool
        st.session_state.personel_alan_yetkinlikleri -> Dict[str, List[str]]
        st.session_state.kidem_gruplari         -> List[dict]
        st.session_state.personel_kidem_gruplari -> Dict[str, str]
        st.session_state.vardiya_tipleri        -> List[dict]
        st.session_state.personel_vardiya_kisitlari -> Dict[str, List[str]]
    
    Args:
        data: ScenarioGenerator.generate() çıktısı
    """
    # === YIL/AY ===
    meta = data.get("_meta", {})
    if "yil" in meta:
        st.session_state.yil = meta["yil"]
    if "ay" in meta:
        st.session_state.ay = meta["ay"]
    
    # === VARSAYILAN HEDEF ===
    if "varsayilan_hedef" in data:
        # 0-31 arasına sınırla (UI limiti)
        hedef = data["varsayilan_hedef"]
        st.session_state.varsayilan_hedef = max(0, min(31, hedef))
    
    # === ZORUNLU ANAHTARLAR ===
    st.session_state.personel_list = data["personel_list"]
    st.session_state.personel_sayisi = len(data["personel_list"])  # UI sync için
    st.session_state.personel_targets = data.get("personel_targets", {})
    st.session_state.weekday_block_map = data.get("weekday_block_map", {})
    
    # === ÇİFT TERCİHLERİ ===
    st.session_state.want_pairs_list = data.get("want_pairs_list", [])
    st.session_state.no_pairs_list = data.get("no_pairs_list", [])
    st.session_state.soft_no_pairs_list = data.get("soft_no_pairs_list", [])
    
    # === AY'A ÖZEL ===
    st.session_state.izin_map = data.get("izin_map", {})
    st.session_state.prefer_map = data.get("prefer_map", {})
    st.session_state.manuel_tatiller = data.get("manuel_tatiller", "")
    
    # === OPSİYONEL MODLAR ===
    alanlar = data.get("alanlar", [])
    st.session_state.alanlar = alanlar
    st.session_state.alan_modu_aktif = len(alanlar) > 0  # Auto-enable if areas exist
    st.session_state.alan_bazli_denklik = data.get("alan_bazli_denklik", False)
    st.session_state.personel_alan_yetkinlikleri = data.get("personel_alan_yetkinlikleri", {})
    
    st.session_state.kidem_gruplari = data.get("kidem_gruplari", [])
    st.session_state.personel_kidem_gruplari = data.get("personel_kidem_gruplari", {})
    
    st.session_state.vardiya_tipleri = data.get("vardiya_tipleri", [])
    st.session_state.personel_vardiya_kisitlari = data.get("personel_vardiya_kisitlari", {})
    
    # === DEMO MODU FLAG'LERİ ===
    st.session_state._demo_aktif = True
    st.session_state._demo_meta = data.get("_meta", {})
    st.session_state.initialized = True  # init_session_state'in çalışmasını engelle
    
    # Debug: Inject edilen değerleri meta'ya ekle
    st.session_state._demo_meta["injected_personel_count"] = len(data["personel_list"])
    st.session_state._demo_meta["injected_alan_count"] = len(data.get("alanlar", []))
    st.session_state._demo_meta["injected_vardiya_count"] = len(data.get("vardiya_tipleri", []))


def clear_demo_data() -> None:
    """
    Tüm demo verisini session_state'ten temizle.
    """
    keys_to_clear = [
        # Yıl/Ay
        "yil", "ay",
        # Zorunlu
        "personel_list", "personel_targets", "weekday_block_map",
        # Çift tercihleri
        "want_pairs_list", "no_pairs_list", "soft_no_pairs_list",
        # Ay'a özel
        "izin_map", "prefer_map", "manuel_tatiller",
        # Opsiyonel modlar
        "alanlar", "alan_modu_aktif", "alan_bazli_denklik",
        "personel_alan_yetkinlikleri",
        "kidem_gruplari", "personel_kidem_gruplari",
        "vardiya_tipleri", "personel_vardiya_kisitlari",
        # Meta
        "_demo_aktif", "_demo_meta"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def is_demo_active() -> bool:
    """Demo modu aktif mi?"""
    return st.session_state.get("_demo_aktif", False)


def get_demo_meta() -> Dict[str, Any]:
    """Demo meta bilgisi (seed, difficulty, vs.)"""
    return st.session_state.get("_demo_meta", {})


# =============================================================================
# SIDEBAR BİLEŞENİ
# =============================================================================

def get_demo_sidebar() -> None:
    """
    Sidebar'a demo senaryo yükleme kontrollerini ekler.
    
    Bu fonksiyonu app.py'de şöyle çağır:
        with st.sidebar:
            get_demo_sidebar()
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧪 Demo Senaryo")
    
    # Mod seçimi
    mod = st.sidebar.radio(
        "Senaryo Kaynağı",
        ["Yeni Üret", "Hazır Senaryolar", "Dosyadan Yükle"],
        key="_demo_mod",
        horizontal=True
    )
    
    if mod == "Yeni Üret":
        _render_yeni_senaryo()
    elif mod == "Hazır Senaryolar":
        _render_hazir_senaryolar()
    else:
        _render_dosya_yukle()
    
    # Aktif senaryo bilgisi
    if is_demo_active():
        st.sidebar.markdown("---")
        meta = get_demo_meta()
        st.sidebar.success(f"✅ Demo aktif: {meta.get('difficulty', '?')}")
        st.sidebar.caption(f"Seed: `{meta.get('seed', '?')}`")
        st.sidebar.caption(f"Dönem: {meta.get('yil', '?')}-{meta.get('ay', '?'):02d}")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🗑️ Temizle", use_container_width=True):
                clear_demo_data()
                st.rerun()
        with col2:
            if st.button("📋 Detay", use_container_width=True):
                st.session_state._show_demo_detail = True


def _render_yeni_senaryo() -> None:
    """Yeni senaryo üretme kontrolleri."""
    
    # Zorluk
    zorluk = st.sidebar.selectbox(
        "Zorluk",
        list(ZORLUK_PROFILLERI.keys()),
        index=1,
        key="_demo_zorluk",
        format_func=lambda x: f"{x} - {ZORLUK_PROFILLERI[x]['aciklama'][:30]}..."
    )
    
    # Personel sayısı
    num_personel = st.sidebar.slider(
        "Personel Sayısı",
        min_value=5,
        max_value=40,
        value=15,
        key="_demo_num_personel"
    )
    
    # Yıl/Ay
    col1, col2 = st.sidebar.columns(2)
    with col1:
        yil = st.number_input("Yıl", value=2025, min_value=2020, max_value=2030, key="_demo_yil")
    with col2:
        ay = st.number_input("Ay", value=1, min_value=1, max_value=12, key="_demo_ay")
    
    # Seed
    use_seed = st.sidebar.checkbox("Özel seed kullan", key="_demo_use_seed")
    if use_seed:
        seed = st.sidebar.number_input("Seed değeri", value=42, key="_demo_seed")
    else:
        seed = None
    
    # Üret butonu
    if st.sidebar.button("🎲 Senaryo Üret", type="primary", use_container_width=True):
        data = generate_quick_scenario(
            difficulty=zorluk,
            seed=seed,
            yil=int(yil),
            ay=int(ay),
            num_personel=num_personel
        )
        inject_scenario_to_session_state(data)
        st.toast(f"✅ Senaryo üretildi! Seed: {data['_meta']['seed']}")
        st.rerun()


def _render_hazir_senaryolar() -> None:
    """Hazır test senaryoları."""
    
    senaryolar = {
        "Minimal (En basit)": "minimal",
        "Hafta Sonu Krizi": "hafta_sonu_krizi",
        "Çift Çatışması": "cift_catismasi",
        "İzin Bombardımanı (Muhtemelen çözümsüz)": "izin_bombardimani",
    }
    
    secim = st.sidebar.selectbox(
        "Hazır Senaryo",
        list(senaryolar.keys()),
        key="_demo_hazir"
    )
    
    # Açıklamalar
    aciklamalar = {
        "Minimal (En basit)": "5 kişi, minimum kısıt. Hızlı test için.",
        "Hafta Sonu Krizi": "Herkes Cts/Paz blokladı. Solver zorlanır.",
        "Çift Çatışması": "Çok sayıda uyumsuz çift. Kısıt yoğun.",
        "İzin Bombardımanı (Muhtemelen çözümsüz)": "Aşırı izin. Infeasible test.",
    }
    st.sidebar.caption(aciklamalar.get(secim, ""))
    
    if st.sidebar.button("📦 Hazır Yükle", type="primary", use_container_width=True):
        method_name = senaryolar[secim]
        method = getattr(HazirSenaryolar, method_name)
        data = method()
        inject_scenario_to_session_state(data)
        st.toast(f"✅ '{secim}' yüklendi!")
        st.rerun()


def _render_dosya_yukle() -> None:
    """JSON dosyasından yükleme."""
    
    uploaded = st.sidebar.file_uploader(
        "Senaryo JSON dosyası",
        type=["json"],
        key="_demo_upload"
    )
    
    if uploaded is not None:
        if st.sidebar.button("📂 Dosyadan Yükle", type="primary", use_container_width=True):
            try:
                content = json.load(uploaded)
                
                # izin_map ve prefer_map'i set'e çevir
                for key in ["izin_map", "prefer_map"]:
                    if key in content and isinstance(content[key], dict):
                        content[key] = {k: set(v) for k, v in content[key].items()}
                
                inject_scenario_to_session_state(content)
                st.toast("✅ Dosyadan yüklendi!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Hata: {e}")


# =============================================================================
# DETAY GÖRÜNTÜLEYICI
# =============================================================================

def render_demo_detail_modal() -> None:
    """
    Demo verisi detaylarını gösteren modal/expander.
    
    Ana sayfada şöyle kullan:
        render_demo_detail_modal()
    """
    if not st.session_state.get("_show_demo_detail", False):
        return
    
    with st.expander("📊 Demo Senaryo Detayları", expanded=True):
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Kapat", key="_close_detail"):
                st.session_state._show_demo_detail = False
                st.rerun()
        
        # Tab'lar
        tab1, tab2, tab3, tab4 = st.tabs([
            "Personel", "İzinler/Tercihler", "Çift Kuralları", "Modlar"
        ])
        
        with tab1:
            _render_personel_tab()
        
        with tab2:
            _render_izin_tab()
        
        with tab3:
            _render_cift_tab()
        
        with tab4:
            _render_mod_tab()


def _render_personel_tab():
    """Personel listesi ve hedefler."""
    personel_list = st.session_state.get("personel_list", [])
    personel_targets = st.session_state.get("personel_targets", {})
    weekday_block = st.session_state.get("weekday_block_map", {})
    
    st.write(f"**Toplam Personel:** {len(personel_list)}")
    
    # Tablo oluştur
    rows = []
    for p in personel_list:
        rows.append({
            "İsim": p,
            "Hedef Override": personel_targets.get(p, "-"),
            "Bloklu Günler": ", ".join(weekday_block.get(p, [])) or "-"
        })
    
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz personel eklenmemiş.")


def _render_izin_tab():
    """İzin ve tercih haritaları."""
    izin_map = st.session_state.get("izin_map", {})
    prefer_map = st.session_state.get("prefer_map", {})
    manuel_tatiller = st.session_state.get("manuel_tatiller", "")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**İzin Haritası**")
        toplam_izin = sum(len(v) for v in izin_map.values())
        st.caption(f"Toplam: {toplam_izin} gün, {len(izin_map)} kişi")
        
        for p, gunler in list(izin_map.items())[:10]:
            st.write(f"- {p}: {sorted(gunler)}")
        if len(izin_map) > 10:
            st.caption(f"... ve {len(izin_map) - 10} kişi daha")
    
    with col2:
        st.write("**Tercih Haritası**")
        toplam_prefer = sum(len(v) for v in prefer_map.values())
        st.caption(f"Toplam: {toplam_prefer} gün, {len(prefer_map)} kişi")
        
        for p, gunler in list(prefer_map.items())[:10]:
            st.write(f"- {p}: {sorted(gunler)}")
        if len(prefer_map) > 10:
            st.caption(f"... ve {len(prefer_map) - 10} kişi daha")
    
    st.write(f"**Manuel Tatiller:** {manuel_tatiller or '(yok)'}")


def _render_cift_tab():
    """Çift kuralları."""
    no_pairs = st.session_state.get("no_pairs_list", [])
    soft_no_pairs = st.session_state.get("soft_no_pairs_list", [])
    want_pairs = st.session_state.get("want_pairs_list", [])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**Kesin Ayrı ({len(no_pairs)})**")
        for p in no_pairs[:5]:
            st.write(f"🚫 {p['a']} ↔ {p['b']}")
        if len(no_pairs) > 5:
            st.caption(f"... +{len(no_pairs) - 5}")
    
    with col2:
        st.write(f"**Esnek Ayrı ({len(soft_no_pairs)})**")
        for p in soft_no_pairs[:5]:
            st.write(f"⚠️ {p['a']} ↔ {p['b']}")
        if len(soft_no_pairs) > 5:
            st.caption(f"... +{len(soft_no_pairs) - 5}")
    
    with col3:
        st.write(f"**Birlikte ({len(want_pairs)})**")
        for p in want_pairs[:5]:
            st.write(f"💚 {p['a']} + {p['b']} (min:{p['min']})")
        if len(want_pairs) > 5:
            st.caption(f"... +{len(want_pairs) - 5}")


def _render_mod_tab():
    """Alan/Vardiya/Kıdem modları."""
    
    # Alan modu
    st.write("### Alan Modu")
    alan_aktif = st.session_state.get("alan_modu_aktif", False)
    st.write(f"**Durum:** {'✅ Aktif' if alan_aktif else '❌ Kapalı'}")
    
    if alan_aktif:
        alanlar = st.session_state.get("alanlar", [])
        st.write(f"**Alanlar ({len(alanlar)}):**")
        for a in alanlar:
            max_k = a.get('max_kontenjan')
            max_str = f" (max: {max_k})" if max_k else ""
            st.write(f"- {a['isim']}: kontenjan={a['kontenjan']}{max_str}")
        
        denklik = st.session_state.get("alan_bazli_denklik", False)
        st.write(f"**Alan Bazlı Denklik:** {'Evet' if denklik else 'Hayır'}")
    
    st.markdown("---")
    
    # Vardiya modu
    st.write("### Vardiya Modu")
    vardiyalar = st.session_state.get("vardiya_tipleri", [])
    st.write(f"**Vardiya Sayısı:** {len(vardiyalar)}")
    for v in vardiyalar:
        st.write(f"- {v['isim']}: {v['baslangic']} - {v['bitis']}")
    
    kisitlar = st.session_state.get("personel_vardiya_kisitlari", {})
    if kisitlar:
        st.write(f"**Vardiya Kısıtlı Personel:** {len(kisitlar)}")
    
    st.markdown("---")
    
    # Kıdem
    st.write("### Kıdem Grupları")
    kidem = st.session_state.get("kidem_gruplari", [])
    for k in kidem:
        st.write(f"- {k['isim']}: varsayılan hedef={k['varsayilan_hedef']}")


# =============================================================================
# SOLVER INPUT ÖNİZLEME (Debug için)
# =============================================================================

def preview_solver_input() -> Dict[str, Any]:
    """
    Session state'teki veriyi solver input formatında önizle.
    Bu, senin SolverInput dataclass'ına dönüştürmeden önce
    ham veriyi görmek için kullanılabilir.
    """
    if not is_demo_active():
        return {}
    
    meta = get_demo_meta()
    gun_sayisi = meta.get("gun_sayisi", 30)

    return {
        "yil": meta.get("yil"),
        "ay": meta.get("ay"),
        "personeller": st.session_state.get("personel_list", []),
        "hedefler": st.session_state.get("personel_targets", {}),
        "izinler": {
            k: list(v) for k, v in st.session_state.get("izin_map", {}).items()
        },
        "tatiller": [
            int(x.strip())
            for x in st.session_state.get("manuel_tatiller", "").split(",")
            if x.strip().isdigit() and 1 <= int(x.strip()) <= gun_sayisi
        ],
        "ayri_tut": [
            (p["a"], p["b"]) for p in st.session_state.get("no_pairs_list", [])
        ],
        "birlikte_tut": [
            (p["a"], p["b"], p["min"]) for p in st.session_state.get("want_pairs_list", [])
        ],
        "esnek_ayri_tut": [
            (p["a"], p["b"]) for p in st.session_state.get("soft_no_pairs_list", [])
        ],
        "tercih_edilen": {
            k: list(v) for k, v in st.session_state.get("prefer_map", {}).items()
        },
        "alanlar": st.session_state.get("alanlar", []),
        "personel_alan_yetkinlikleri": st.session_state.get("personel_alan_yetkinlikleri", {}),
        "alan_bazli_denklik": st.session_state.get("alan_bazli_denklik", False),
        "personel_kidem_gruplari": st.session_state.get("personel_kidem_gruplari", {}),
        "vardiyalar": st.session_state.get("vardiya_tipleri", []),
        "personel_vardiya_kisitlari": st.session_state.get("personel_vardiya_kisitlari", {}),
    }


# =============================================================================
# MİNİMAL DEMO APP
# =============================================================================

def _demo_app():
    """
    Minimal test uygulaması.
    Çalıştır: streamlit run streamlit_integration.py
    """
    st.set_page_config(page_title="Senaryo Demo", layout="wide")
    
    st.title("🗓️ Roster Senaryo Demo")
    
    # Sidebar'a demo kontrollerini ekle
    get_demo_sidebar()
    
    # Ana içerik
    if is_demo_active():
        st.success("✅ Demo verisi yüklü!")
        
        # Detay modal
        render_demo_detail_modal()
        
        # Özet
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Personel", len(st.session_state.get("personel_list", [])))
        with col2:
            izin_toplam = sum(len(v) for v in st.session_state.get("izin_map", {}).values())
            st.metric("Toplam İzin Günü", izin_toplam)
        with col3:
            kisit_toplam = (
                len(st.session_state.get("no_pairs_list", [])) +
                len(st.session_state.get("soft_no_pairs_list", []))
            )
            st.metric("Çift Kısıtları", kisit_toplam)
        
        # Solver input preview
        with st.expander("🔧 Solver Input Preview (Debug)"):
            preview = preview_solver_input()
            st.json(preview)
    else:
        st.info("👈 Sol panelden bir demo senaryo yükleyin.")


if __name__ == "__main__":
    _demo_app()
