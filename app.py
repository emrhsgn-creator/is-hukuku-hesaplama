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

def kesinti_ayrintisi(brut, tip="standart"):
    dv = brut * 0.00759
    if tip == "kıdem":
        return {"dv": dv, "gv": 0.0, "sgk": 0.0, "net": brut - dv}
    sgk = brut * 0.15
    gv = (brut - sgk) * 0.15 # %15 gelir vergisi
    return {"dv": dv, "gv": gv, "sgk": sgk, "net": brut - (dv + gv + sgk)}

st.set_page_config(page_title="Hukuk Robotu PRO", layout="wide")
st.title("⚖️ Detaylı İşçilik Alacakları Bilirkişi Raporu")

with st.sidebar:
    st.header("Giriş Parametreleri")
    isim = st.text_input("İşçinin Adı Soyadı", "Onur Erol")
    g_tarih = st.date_input("İşe Giriş Tarihi", datetime(2020, 1, 15))
    c_tarih = st.date_input("İşten Çıkış Tarihi", datetime(2024, 7, 26))
    son_brut = st.number_input("Son Brüt Ücret (TL)", value=30000.0)
    yan_hak = st.number_input("Aylık Giydirilmiş Ek Haklar (Brüt TL)", value=500.0)
    fm_saat = st.number_input("Haftalık Fazla Mesai Saati", value=12.0)
    izin_gun = st.number_input("Kalan Yıllık İzin Günü", value=14)
    ubgt_yillik = st.number_input("Yıllık Çalışılan UBGT Günü", value=5)

if st.button("DETAYLI RAPORU OLUŞTUR", type="primary"):
    delta = relativedelta(c_tarih, g_tarih)
    yil, ay, gun = delta.years, delta.months, delta.days
    maas_katsayisi = son_brut / ASGARI_UCRET_TABLOSU.get(c_tarih.year, 25000.0)

    # 1. KIDEM, İHBAR, İZİN (Statik Hesaplar)
    giydirilmis = son_brut + yan_hak
    tavan = KIDEM_TAVANI_TABLOSU.get(c_tarih.year, 41828.42)
    esas_kıdem = min(giydirilmis, tavan)
    brut_kidem = (esas_kıdem * yil) + (esas_kıdem / 12 * ay) + (esas_kıdem / 365 * gun)
    k_res = kesinti_ayrintisi(brut_kidem, "kıdem")

    hafta = 2 if (c_tarih-g_tarih).days < 180 else 4 if (c_tarih-g_tarih).days < 540 else 6 if (c_tarih-g_tarih).days < 1080 else 8
    brut_ihbar = (son_brut / 30) * (hafta * 7)
    i_res = kesinti_ayrintisi(brut_ihbar)
    z_res = kesinti_ayrintisi((son_brut / 30) * izin_gun)

    # 2. FAZLA MESAİ DÖNEMSEL DÖKÜM (Alt Kademeler)
    fm_rows = []
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_asgari = ASGARI_UCRET_TABLOSU.get(y, 25000.0)
        d_brut = d_asgari * maas_katsayisi
        saatlik = (d_brut / 225) * 1.5
        
        # O yıl kaç hafta çalışıldı?
        baslangic = max(g_tarih, datetime(y, 1, 1).date())
        bitis = min(c_tarih, datetime(y, 12, 31).date())
        hafta_sayisi = ((bitis - baslangic).days / 7)
        
        toplam_saat = hafta_sayisi * fm_saat
        b_tutar = toplam_saat * saatlik
        n_tutar = kesinti_ayrintisi(b_tutar)["net"]
        
        fm_rows.append({
            "Dönem": f"{y}",
            "Maaş (Brüt)": f"{d_brut:,.2f}",
            "Saatlik Ücret": f"{saatlik:,.2f}",
            "Haftalık FM": f"{fm_saat}",
            "Toplam Saat": f"{toplam_saat:,.2f}",
            "Brüt Tutar": b_tutar,
            "Net Tutar": n_tutar
        })

    # 3. UBGT DÖNEMSEL DÖKÜM
    ubgt_rows = []
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_asgari = ASGARI_UCRET_TABLOSU.get(y, 25000.0)
        d_brut = d_asgari * maas_katsayisi
        gunluk = d_brut / 30
        
        # Yıl içindeki gün oranı
        baslangic = max(g_tarih, datetime(y, 1, 1).date())
        bitis = min(c_tarih, datetime(y, 12, 31).date())
        yil_orani = (bitis - baslangic).days / 365
        donem_gun = ubgt_yillik * yil_orani
        
        b_tutar = donem_gun * gunluk
        n_tutar = kesinti_ayrintisi(b_tutar)["net"]
        
        ubgt_rows.append({
            "Dönem": f"{y}",
            "Günlük Ücret": f"{gunluk:,.2f}",
            "Gün Sayısı": f"{donem_gun:,.2f}",
            "Brüt Tutar": b_tutar,
            "Net Tutar": n_tutar
        })

    # --- EKRAN ÇIKTISI ---
    st.header("1. BİLGİLER VE SÜRE HESABI")
    st.markdown(f"**Hizmet Süresi:** {yil} Yıl {ay} Ay {gun} Gün")
    
    st.header("2. KIDEM VE İHBAR HESABI")
    st.table(pd.DataFrame([
        {"Alacak": "Kıdem Tazminatı", "Brüt": f"{k_res['brut']:,.2f}", "DV (%0.759)": f"{k_res['dv']:,.2f}", "Net": f"{k_res['net']:,.2f}"},
        {"Alacak": "İhbar Tazminatı", "Brüt": f"{i_res['brut']:,.2f}", "Kesintiler": f"{i_res['gv']+i_res['sgk']+i_res['dv']:,.2f}", "Net": f"{i_res['net']:,.2f}"}
    ]))

    st.header("3. FAZLA MESAİ DÖNEMSEL HESAP TABLOSU")
    df_fm = pd.DataFrame(fm_rows)
    st.table(df_fm)
    st.write(f"**Toplam FM Brüt:** {sum(df_fm['Brüt Tutar']):,.2f} TL | **Toplam FM Net:** {sum(df_fm['Net Tutar']):,.2f} TL")

    st.header("4. UBGT DÖNEMSEL HESAP TABLOSU")
    df_ubgt = pd.DataFrame(ubgt_rows)
    st.table(df_ubgt)
    st.write(f"**Toplam UBGT Brüt:** {sum(df_ubgt['Brüt Tutar']):,.2f} TL | **Toplam UBGT Net:** {sum(df_ubgt['Net Tutar']):,.2f} TL")

    st.header("5. SONUÇ İCMAL TABLOSU")
    toplam_brut = k_res['brut'] + i_res['brut'] + z_res['brut'] + sum(df_fm['Brüt Tutar']) + sum(df_ubgt['Brüt Tutar'])
    toplam_net = k_res['net'] + i_res['net'] + z_res['net'] + sum(df_fm['Net Tutar']) + sum(df_ubgt['Net Tutar'])
    
    st.success(f"### GENEL TOPLAM NET: {toplam_net:,.2f} TL")
