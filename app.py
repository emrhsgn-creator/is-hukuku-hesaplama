import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- VERİ SETİ (Robotun Hafızası) ---
# Buraya güncel veriler eklenebilir. 
ASGARI_UCRET_TABLOSU = {
    2026: 25000.00, # Temsili, güncelleyebiliriz
    2025: 20000.00, # Temsili
    2024: 17002.12,
    2023: 13414.50, # Temmuz sonrası
    2022: 6471.00,
    2021: 3577.50
}

KIDEM_TAVANI_TABLOSU = {
    2026: 60000.00, # Temsili
    2025: 50000.00, # Temsili
    2024: 41828.42,
    2023: 23489.83
}

# --- HESAPLAMA FONKSİYONLARI ---
def vergi_kes(brut, tip="standart"):
    dv = brut * 0.00759
    if tip == "kıdem":
        return dv, 0, 0, brut - dv
    
    sgk = brut * 0.14
    issizlik = brut * 0.01
    matrah = brut - (sgk + issizlik)
    gv = matrah * 0.15 # Basitleştirilmiş %15 (Kademeli istenirse genişletilebilir)
    
    net = brut - (sgk + issizlik + gv + dv)
    return dv, gv, (sgk + issizlik), net

def hesapla(ad, giris, cikis, son_brut, yan_hak, fm_saat, izin_gun):
    # 1. Süre Hesabı
    delta = relativedelta(cikis, giris)
    toplam_gun = (cikis - giris).days
    yil = delta.years
    ay = delta.months
    gun = delta.days

    # 2. Kıdem Tazminatı
    giydirilmis = son_brut + yan_hak
    tavan = KIDEM_TAVANI_TABLOSU.get(cikis.year, 41828.42)
    hesaba_esas_kıdem = min(giydirilmis, tavan)
    
    brut_kidem = (hesaba_esas_kıdem * yil) + (hesaba_esas_kıdem / 12 * ay) + (hesaba_esas_kıdem / 365 * gun)
    dv_k, _, _, net_kidem = vergi_kes(brut_kidem, "kıdem")

    # 3. İhbar Tazminatı
    if toplam_gun < 180: hafta = 2
    elif toplam_gun < 540: hafta = 4
    elif toplam_gun < 1080: hafta = 6
    else: hafta = 8
    
    ihbar_gun = hafta * 7
    brut_ihbar = (son_brut / 30) * ihbar_gun
    dv_i, gv_i, _, net_ihbar = vergi_kes(brut_ihbar)

    # 4. Yıllık İzin
    brut_izin = (son_brut / 30) * izin_gun
    dv_z, gv_z, sgk_z, net_izin = vergi_kes(brut_izin)

    return {
        "sure": f"{yil} Yıl {ay} Ay {gun} Gün",
        "kidem": {"brut": brut_kidem, "net": net_kidem, "dv": dv_k},
        "ihbar": {"brut": brut_ihbar, "net": net_ihbar, "gv": gv_i, "dv": dv_i, "gun": ihbar_gun},
        "izin": {"brut": brut_izin, "net": net_izin, "sgk": sgk_z, "gv": gv_z, "dv": dv_z}
    }

# --- STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="İşçilik Robotu", layout="wide")
st.title("🤖 İşçilik Alacakları Hesaplama Robotu (AI Değil)")

with st.form("hesap_formu"):
    c1, c2 = st.columns(2)
    with c1:
        isim = st.text_input("İşçinin Adı Soyadı")
        g_tarih = st.date_input("İşe Giriş", value=datetime(2020,1,1))
        c_tarih = st.date_input("İşten Çıkış", value=datetime(2023,12,31))
    with c2:
        brut = st.number_input("Son Brüt Maaş", min_value=0.0)
        yan = st.number_input("Ek Brüt Haklar (Yol/Yemek vb.)", min_value=0.0)
        izin = st.number_input("Kalan İzin Günü", min_value=0)
    
    submit = st.form_submit_button("HESAPLA")

if submit:
    res = hesapla(isim, g_tarih, c_tarih, brut, yan, 0, izin)
    
    st.subheader(f"📋 Bilirkişi Rapor Özeti: {isim}")
    st.info(f"Toplam Çalışma Süresi: {res['sure']}")

    # Tablo Gösterimi
    st.markdown("### 1. Kıdem Tazminatı")
    st.table({
        "Açıklama": ["Brüt Tutar", "Damga Vergisi (%0.759)", "NET ÖDENECEK"],
        "Tutar (TL)": [f"{res['kidem']['brut']:,.2f}", f"{res['kidem']['dv']:,.2f}", f"{res['kidem']['net']:,.2f}"]
    })

    st.markdown("### 2. İhbar Tazminatı")
    st.table({
        "Açıklama": [f"İhbar Süresi ({res['ihbar']['gun']} Gün)", "Gelir Vergisi (%15)", "Damga Vergisi", "NET ÖDENECEK"],
        "Tutar (TL)": [f"{res['ihbar']['brut']:,.2f}", f"{res['ihbar']['gv']:,.2f}", f"{res['ihbar']['dv']:,.2f}", f"{res['ihbar']['net']:,.2f}"]
    })

    st.markdown("### 3. Yıllık İzin Ücreti")
    st.table({
        "Açıklama": ["Brüt İzin Ücreti", "SGK Kesintisi (%15)", "Gelir Vergisi (%15)", "Damga Vergisi", "NET ÖDENECEK"],
        "Tutar (TL)": [f"{res['izin']['brut']:,.2f}", f"{res['izin']['sgk']:,.2f}", f"{res['izin']['gv']:,.2f}", f"{res['izin']['dv']:,.2f}", f"{res['izin']['net']:,.2f}"]
    })
