import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

# --- VERİ SETİ ---
ASGARI_UCRET_TABLOSU = {
    2026: 25000.00, 2025: 20002.12, 2024: 17002.12, 
    2023: 13414.50, 2022: 6471.00, 2021: 3577.50, 2020: 2943.00, 2019: 2558.40
}
KIDEM_TAVANI_TABLOSU = {
    2026: 60000.00, 2025: 50000.00, 2024: 41828.42, 
    2023: 23489.83, 2022: 15371.40, 2021: 8284.51, 2020: 7117.17
}

def kesinti_ayrintisi(brut_tutar, tip="standart"):
    dv = brut_tutar * 0.00759
    if tip == "kıdem":
        return {"brut": brut_tutar, "dv": dv, "gv": 0.0, "sgk": 0.0, "net": brut_tutar - dv}
    sgk = brut_tutar * 0.15
    gv = (brut_tutar - sgk) * 0.15
    return {"brut": brut_tutar, "dv": dv, "gv": gv, "sgk": sgk, "net": brut_tutar - (dv + gv + sgk)}

st.set_page_config(page_title="Hukuk Robotu PRO", layout="wide")
st.title("⚖️ Detaylı İşçilik Alacakları Bilirkişi Raporu")

with st.sidebar:
    st.header("Giriş Parametreleri")
    isim = st.text_input("İşçinin Adı Soyadı", "Onur Erol")
    g_tarih = st.date_input("İşe Giriş Tarihi", datetime(2020, 1, 15))
    c_tarih = st.date_input("İşten Çıkış Tarihi", datetime(2021, 7, 26))
    son_brut = st.number_input("Son Brüt Ücret (TL)", value=5595.11)
    yan_hak = st.number_input("Aylık Giydirilmiş Ek Haklar (Brüt TL)", value=350.0)
    fm_saat = st.number_input("Haftalık Fazla Mesai Saati", value=12.0)
    izin_gun = st.number_input("Kalan Yıllık İzin Günü", value=14)
    ubgt_yillik = st.number_input("Yıllık Çalışılan UBGT Günü", value=5)

if st.button("DETAYLI RAPORU OLUŞTUR", type="primary"):
    # 1. TEMEL SÜRE HESAPLARI
    delta = relativedelta(c_tarih, g_tarih)
    yil, ay, gun = delta.years, delta.months, delta.days
    maas_katsayisi = son_brut / ASGARI_UCRET_TABLOSU.get(c_tarih.year, 25000.0)

    # 2. KIDEM, İHBAR, İZİN
    giydirilmis = son_brut + yan_hak
    tavan = KIDEM_TAVANI_TABLOSU.get(c_tarih.year, 41828.42)
    esas_kıdem = min(giydirilmis, tavan)
    brut_kidem = (esas_kıdem * yil) + (esas_kıdem / 12 * ay) + (esas_kıdem / 365 * gun)
    k_res = kesinti_ayrintisi(brut_kidem, "kıdem")

    hafta = 2 if (c_tarih-g_tarih).days < 180 else 4 if (c_tarih-g_tarih).days < 540 else 6 if (c_tarih-g_tarih).days < 1080 else 8
    brut_ihbar = (son_brut / 30) * (hafta * 7)
    i_res = kesinti_ayrintisi(brut_ihbar)
    
    brut_izin = (son_brut / 30) * izin_gun
    z_res = kesinti_ayrintisi(brut_izin)

    # 3. FAZLA MESAİ DÖNEMSEL DÖKÜM
    fm_rows = []
    total_fm_brut = 0
    total_fm_net = 0
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_asgari = ASGARI_UCRET_TABLOSU.get(y, 25000.0)
        d_brut = d_asgari * maas_katsayisi
        saatlik = (d_brut / 225) * 1.5
        
        bas = max(g_tarih, datetime(y, 1, 1).date())
        bit = min(c_tarih, datetime(y, 12, 31).date())
        h_sayisi = max(0, (bit - bas).days / 7)
        
        b_tutar = h_sayisi * fm_saat * saatlik
        res = kesinti_ayrintisi(b_tutar)
        
        total_fm_brut += b_tutar
        total_fm_net += res['net']
        
        fm_rows.append({
            "Dönem": f"{y}",
            "Maaş (Brüt)": f"{d_brut:,.2f}",
            "Saatlik": f"{saatlik:,.2f}",
            "Hafta": f"{h_sayisi:.2f}",
            "Brüt Toplam": b_tutar,
            "Net": res['net']
        })

    # 4. UBGT DÖNEMSEL DÖKÜM
    ubgt_rows = []
    total_ubgt_brut = 0
    total_ubgt_net = 0
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_asgari = ASGARI_UCRET_TABLOSU.get(y, 25000.0)
        d_brut = d_asgari * maas_katsayisi
        gunluk = d_brut / 30
        
        bas = max(g_tarih, datetime(y, 1, 1).date())
        bit = min(c_tarih, datetime(y, 12, 31).date())
        yil_orani = (bit - bas).days / 365
        d_gun = ubgt_yillik * yil_orani
        
        b_tutar = d_gun * gunluk
        res = kesinti_ayrintisi(b_tutar)
        
        total_ubgt_brut += b_tutar
        total_ubgt_net += res['net']
        
        ubgt_rows.append({
            "Dönem": f"{y}",
            "Günlük": f"{gunluk:,.2f}",
            "Gün Sayısı": f"{d_gun:.2f}",
            "Brüt Toplam": b_tutar,
            "Net": res['net']
        })

    # --- GÖRSEL ÇIKTILAR ---
    st.header("1. BİLGİLER VE SÜRE HESABI")
    st.markdown(f"**Hizmet Süresi:** {yil} Yıl {ay} Ay {gun} Gün")
    
    st.header("2. KIDEM VE İHBAR HESABI")
    st.table(pd.DataFrame([
        {"Alacak": "Kıdem Tazminatı", "Brüt": f"{k_res['brut']:,.2f}", "Vergi": f"{k_res['dv']:,.2f}", "Net": f"{k_res['net']:,.2f}"},
        {"Alacak": "İhbar Tazminatı", "Brüt": f"{i_res['brut']:,.2f}", "Vergi": f"{i_res['gv']+i_res['dv']+i_res['sgk']:,.2f}", "Net": f"{i_res['net']:,.2f}"},
        {"Alacak": "Yıllık İzin Ücreti", "Brüt": f"{z_res['brut']:,.2f}", "Vergi": f"{z_res['gv']+z_res['dv']+z_res['sgk']:,.2f}", "Net": f"{z_res['net']:,.2f}"}
    ]))

    st.header("3. FAZLA MESAİ DÖNEMSEL HESAP TABLOSU")
    df_fm = pd.DataFrame(fm_rows)
    # Görüntüleme için formatla
    df_fm_disp = df_fm.copy()
    df_fm_disp["Brüt Toplam"] = df_fm_disp["Brüt Toplam"].map("{:,.2f}".format)
    df_fm_disp["Net"] = df_fm_disp["Net"].map("{:,.2f}".format)
    st.table(df_fm_disp)
    st.info(f"Fazla Mesai Toplam Net: {total_fm_net:,.2f} TL")

    st.header("4. UBGT DÖNEMSEL HESAP TABLOSU")
    df_ubgt = pd.DataFrame(ubgt_rows)
    # Görüntüleme için formatla
    df_ubgt_disp = df_ubgt.copy()
    df_ubgt_disp["Brüt Toplam"] = df_ubgt_disp["Brüt Toplam"].map("{:,.2f}".format)
    df_ubgt_disp["Net"] = df_ubgt_disp["Net"].map("{:,.2f}".format)
    st.table(df_ubgt_disp)
    st.info(f"UBGT Toplam Net: {total_ubgt_net:,.2f} TL")

    st.header("5. SONUÇ İCMAL TABLOSU")
    icmal_net = k_res['net'] + i_res['net'] + z_res['net'] + total_fm_net + total_ubgt_net
    icmal_brut = k_res['brut'] + i_res['brut'] + z_res['brut'] + total_fm_brut + total_ubgt_brut
    
    st.table(pd.DataFrame([
        {"Alacak Kalemi": "Kıdem Tazminatı", "Net Tutar": f"{k_res['net']:,.2f} TL"},
        {"Alacak Kalemi": "İhbar Tazminatı", "Net Tutar": f"{i_res['net']:,.2f} TL"},
        {"Alacak Kalemi": "Yıllık İzin Ücreti", "Net Tutar": f"{z_res['net']:,.2f} TL"},
        {"Alacak Kalemi": "Fazla Mesai Ücreti", "Net Tutar": f"{total_fm_net:,.2f} TL"},
        {"Alacak Kalemi": "UBGT Ücreti", "Net Tutar": f"{total_ubgt_net:,.2f} TL"},
        {"Alacak Kalemi": "GENEL TOPLAM", "Net Tutar": f"**{icmal_net:,.2f} TL**"}
    ]))
    st.success(f"### ÖDENECEK TOPLAM NET: {icmal_net:,.2f} TL")
