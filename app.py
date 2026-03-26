import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

# --- VERİ SETİ (2026 Verileri Dahil Tahmini/Güncel) ---
ASGARI_UCRET_TABLOSU = {
    2026: 25000.00, 2025: 20002.12, 2024: 17002.12, 
    2023: 13414.50, 2022: 6471.00, 2021: 3577.50, 2020: 2943.00
}
KIDEM_TAVANI_TABLOSU = {
    2026: 60000.00, 2025: 50000.00, 2024: 41828.42, 
    2023: 23489.83, 2022: 15371.40, 2021: 8284.51, 2020: 7117.17
}

# --- YARDIMCI HESAPLAMA FONKSİYONLARI ---
def net_hesapla(brut, tip="standart"):
    dv = brut * 0.00759
    if tip == "kıdem":
        return {"brut": brut, "dv": dv, "gv": 0, "sgk": 0, "net": brut - dv}
    
    sgk = brut * 0.15  # %14 SGK + %1 İşsizlik
    gv = (brut - sgk) * 0.15 # Gelir Vergisi (Basitleştirilmiş %15)
    return {"brut": brut, "dv": dv, "gv": gv, "sgk": sgk, "net": brut - (dv + gv + sgk)}

# --- ANA UYGULAMA ---
st.set_page_config(page_title="Hukuk Robotu", layout="wide")
st.title("⚖️ Profesyonel İşçilik Alacakları Hesaplama Robotu")

with st.sidebar:
    st.header("Giriş Parametreleri")
    isim = st.text_input("İşçinin Adı Soyadı", "Onur Erol")
    g_tarih = st.date_input("İşe Giriş Tarihi", datetime(2020, 1, 15))
    c_tarih = st.date_input("İşten Çıkış Tarihi", datetime(2024, 7, 26))
    son_brut = st.number_input("Son Brüt Ücret (TL)", value=30000.0)
    yan_hak = st.number_input("Aylık Giydirilmiş Ek Haklar (Brüt TL)", value=500.0)
    fm_saat = st.number_input("Haftalık Fazla Mesai Saati", value=10.0)
    izin_gun = st.number_input("Kalan Yıllık İzin Günü", value=14)
    ubgt_gun = st.number_input("Yıllık Ortalama Çalışılan UBGT Gün Sayısı", value=5)

if st.button("HESAPLA VE BİLİRKİŞİ RAPORU OLUŞTUR", type="primary"):
    # 1. SÜRE VE KATSAYI HESABI
    delta = relativedelta(c_tarih, g_tarih)
    toplam_gun_farki = (c_tarih - g_tarih).days
    yil, ay, gun = delta.years, delta.months, delta.days
    
    guncel_asgari = ASGARI_UCRET_TABLOSU.get(c_tarih.year, 25000.0)
    maas_katsayisi = son_brut / guncel_asgari

    # 2. KIDEM VE İHBAR
    giydirilmis = son_brut + yan_hak
    tavan = KIDEM_TAVANI_TABLOSU.get(c_tarih.year, 41828.42)
    hesaba_esas_kıdem = min(giydirilmis, tavan)
    brut_kidem = (hesaba_esas_kıdem * yil) + (hesaba_esas_kıdem / 12 * ay) + (hesaba_esas_kıdem / 365 * gun)
    k_res = net_hesapla(brut_kidem, "kıdem")

    if toplam_gun_farki < 180: hafta = 2
    elif toplam_gun_farki < 540: hafta = 4
    elif toplam_gun_farki < 1080: hafta = 6
    else: hafta = 8
    brut_ihbar = (son_brut / 30) * (hafta * 7)
    i_res = net_hesapla(brut_ihbar)

    # 3. YILLIK İZİN
    z_res = net_hesapla((son_brut / 30) * izin_gun)

    # 4. DÖNEMSEL HESAPLAR (FM & UBGT)
    fm_list, ubgt_list = [], []
    for y in range(g_tarih.year, c_tarih.year + 1):
        donem_asgari = ASGARI_UCRET_TABLOSU.get(y, guncel_asgari)
        donem_brut = donem_asgari * maas_katsayisi
        saatlik = (donem_brut / 225) * 1.5
        gunluk = donem_brut / 30
        
        # Basitçe o yıl kaç hafta çalışıldığını bulalım (giriş/çıkış yıllarına göre)
        hafta_sayisi = 52
        if y == g_tarih.year: hafta_sayisi = (12 - g_tarih.month) * 4.3
        if y == c_tarih.year: hafta_sayisi = c_tarih.month * 4.3
        
        brut_fm_donem = fm_saat * hafta_sayisi * saatlik
        brut_ubgt_donem = ubgt_gun * gunluk
        
        fm_list.append(net_hesapla(brut_fm_donem))
        ubgt_list.append(net_hesapla(brut_ubgt_donem))

    total_fm_brut = sum(item['brut'] for item in fm_list)
    total_fm_net = sum(item['net'] for item in fm_list)
    total_ubgt_brut = sum(item['brut'] for item in ubgt_list)
    total_ubgt_net = sum(item['net'] for item in ubgt_list)

    # --- RAPOR ÇIKTISI (Birebir Prompt Formatı) ---
    st.markdown("---")
    st.header("BİLİRKİŞİ RAPORU HESAPLAMA TABLOLARI")

    st.subheader("1. BİLGİLER VE SÜRE HESABI")
    st.table({
        "Bilgi": ["Davacı", "Giriş Tarihi", "Çıkış Tarihi", "Hizmet Süresi", "Son Brüt", "Giydirilmiş Brüt", "Kıdem Tavanı"],
        "Detay": [isim, g_tarih, c_tarih, f"{yil} Yıl {ay} Ay {gun} Gün", f"{son_brut:,.2f} TL", f"{giydirilmis:,.2f} TL", f"{tavan:,.2f} TL"]
    })

    st.subheader("2. KIDEM TAZMİNATI HESABI")
    st.markdown(f"""
    | Hesap Kalemi | Süre / Çarpan | Tutar (TL) |
    | :--- | :--- | :--- |
    | Esas Ücret (Tavan Sınırıyla) | 1 Aylık | {hesaba_esas_kıdem:,.2f} |
    | **Brüt Kıdem Tazminatı** | Toplam | **{k_res['brut']:,.2f}** |
    | Damga Vergisi (%0.759) | Kesinti | {k_res['dv']:,.2f} |
    | **NET KIDEM TAZMİNATI** | | **{k_res['net']:,.2f} TL** |
    """)

    st.subheader("3. İHBAR TAZMİNATI HESABI")
    st.markdown(f"""
    | Hesap Kalemi | Detay | Tutar (TL) |
    | :--- | :--- | :--- |
    | İhbar Süresi | {hafta} Hafta | {brut_ihbar:,.2f} |
    | Yasal Kesintiler (GV+DV) | %15.759 | {i_res['gv']+i_res['dv']:,.2f} |
    | **NET İHBAR TAZMİNATI** | | **{i_res['net']:,.2f} TL** |
    """)

    st.subheader("4. YILLIK İZİN ÜCRETİ HESABI")
    st.markdown(f"""
    | Hesap Kalemi | Detay | Tutar (TL) |
    | :--- | :--- | :--- |
    | Bakiye İzin | {izin_gun} Gün | {z_res['brut']:,.2f} |
    | Kesintiler (SGK+GV+DV) | Toplam | {z_res['sgk']+z_res['gv']+z_res['dv']:,.2f} |
    | **NET YILLIK İZİN ÜCRETİ** | | **{z_res['net']:,.2f} TL** |
    """)

    st.subheader("5. FAZLA ÇALIŞMA (MESAİ) VE UBGT ÖZETİ")
    st.write("Yıllara sâri asgari ücret katsayısı ve artış oranları baz alınarak hesaplanmıştır.")
    st.markdown(f"""
    | Alacak Kalemi | Toplam Brüt (TL) | Toplam Net (TL) |
    | :--- | :--- | :--- |
    | Fazla Mesai Ücreti | {total_fm_brut:,.2f} | {total_fm_net:,.2f} |
    | UBGT Ücreti | {total_ubgt_brut:,.2f} | {total_ubgt_net:,.2f} |
    """)

    st.subheader("6. SONUÇ VE İCMAL (ÖZET) TABLOSU")
    genel_brut = k_res['brut'] + i_res['brut'] + z_res['brut'] + total_fm_brut + total_ubgt_brut
    genel_net = k_res['net'] + i_res['net'] + z_res['net'] + total_fm_net + total_ubgt_net
    
    st.markdown(f"""
    | Alacak Kalemi | Brüt Tutar (TL) | Net Ödenecek (TL) |
    | :--- | :--- | :--- |
    | Kıdem Tazminatı | {k_res['brut']:,.2f} | {k_res['net']:,.2f} |
    | İhbar Tazminatı | {i_res['brut']:,.2f} | {i_res['net']:,.2f} |
    | Yıllık İzin Ücreti | {z_res['brut']:,.2f} | {z_res['net']:,.2f} |
    | Fazla Mesai Ücreti | {total_fm_brut:,.2f} | {total_fm_net:,.2f} |
    | UBGT Ücreti | {total_ubgt_brut:,.2f} | {total_ubgt_net:,.2f} |
    | **GENEL TOPLAM** | **{genel_brut:,.2f}** | **{genel_net:,.2f} TL** |
    """)
