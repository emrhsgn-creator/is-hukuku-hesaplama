import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

# --- VERİ SETİ (GÜNCEL) ---
ASGARI_UCRET_TABLOSU = {
    2026: 25000.00, 2025: 20002.12, 2024: 17002.12, 
    2023: 13414.50, 2022: 6471.00, 2021: 3577.50, 2020: 2943.00, 2019: 2558.40
}
KIDEM_TAVANI_TABLOSU = {
    2026: 60000.00, 2025: 50000.00, 2024: 41828.42, 
    2023: 23489.83, 2022: 15371.40, 2021: 8284.51, 2020: 7117.17
}

def format_tl(value):
    return "{:,.2f} TL".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

def kesinti_hesapla(brut, tip="standart"):
    dv = brut * 0.00759
    if tip == "kıdem":
        return {"brut": brut, "dv": dv, "gv": 0.0, "sgk": 0.0, "issizlik": 0.0, "toplam": dv, "net": brut - dv}
    
    sgk = brut * 0.14
    issizlik = brut * 0.01
    gv = (brut - (sgk + issizlik)) * 0.15 
    toplam = dv + sgk + gv + issizlik
    return {"brut": brut, "dv": dv, "gv": gv, "sgk": sgk, "issizlik": issizlik, "toplam": toplam, "net": brut - toplam}

st.set_page_config(page_title="Bilirkişi Raporu Pro", layout="wide")
st.markdown("<h2 style='text-align: center;'>⚖️ İşçilik Alacakları Bilirkişi Raporu</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Giriş Parametreleri")
    isim = st.text_input("İşçinin Adı Soyadı", "Onur Erol")
    g_tarih = st.date_input("İşe Giriş Tarihi", datetime(2020, 1, 15))
    c_tarih = st.date_input("İşten Çıkış Tarihi", datetime(2021, 7, 26))
    son_brut = st.number_input("Brüt Ücret (TL)", value=5595.11)
    yemek_ucreti = st.number_input("Yemek Ücreti (Aylık Brüt)", value=350.0)
    fm_saat = st.number_input("Haftalık Fazla Mesai Saati", value=12.0)
    izin_gun = st.number_input("Kalan İzin Günü", value=14)
    ubgt_yillik = st.number_input("Yıllık Çalışılan UBGT Günü", value=5)

if st.button("HESAPLA VE DETAYLI RAPORU OLUŞTUR", type="primary"):
    # --- TEMEL VERİLER ---
    delta = relativedelta(c_tarih, g_tarih)
    yil, ay, gun = delta.years, delta.months, delta.days
    toplam_gun = (c_tarih - g_tarih).days
    giydirilmis_brut = son_brut + yemek_ucreti
    tavan = KIDEM_TAVANI_TABLOSU.get(c_tarih.year, 41828.42)
    esas_kidem = min(giydirilmis_brut, tavan)
    d_asgari_cikis = ASGARI_UCRET_TABLOSU.get(c_tarih.year, 3577.50)
    maas_orani = son_brut / d_asgari_cikis
    ihbar_hafta = 2 if toplam_gun < 180 else 4 if toplam_gun < 540 else 6 if toplam_gun < 1080 else 8

    # --- 3. ÜCRET TESPİTİ ---
    st.markdown("### 3. Hesaplamalarda Kullanılacak Ücret Miktarları İle İlgili Tespit")
    ucret_tablo = [
        ["Brüt Ücret", format_tl(son_brut)],
        ["Yemek Ücreti", format_tl(yemek_ucreti)],
        ["Giydirilmiş Brüt Ücret", format_tl(giydirilmis_brut)],
        ["Kıdem Tazminatı Tavan Tutarı", format_tl(tavan)],
        ["Kıdem Tazminatına Esas Ücret", format_tl(esas_kidem)],
        ["İhbar Tazminatına Esas Ücret", format_tl(son_brut)],
        ["Dönem Asgari Ücret (" + str(c_tarih.year) + ")", format_tl(d_asgari_cikis)],
        ["Brüt Ücretin Asgari Ücrete Oranı", "{:.5f}".format(maas_orani).replace(".", ",")]
    ]
    st.table(pd.DataFrame(ucret_tablo, columns=["Kalem", "Miktar"]))

    # --- 4. KIDEM VE İHBAR ---
    st.markdown("### 4. Kıdem ve İhbar Tazminatının Hesaplanması")
    st.caption(f"Hizmet Süresi: {yil} Yıl {ay} Ay {gun} Gün")
    
    b_kidem = (esas_kidem * yil) + (esas_kidem / 12 * ay) + (esas_kidem / 365 * gun)
    k_res = kesinti_hesapla(b_kidem, "kıdem")
    st.markdown("**Kıdem Tazminatı Hesabı:**")
    st.table(pd.DataFrame([
        [format_tl(esas_kidem), "x", f"{yil} Yıl", "=", format_tl(esas_kidem * yil)],
        [f"{format_tl(esas_kidem)} / 12", "x", f"{ay} Ay", "=", format_tl(esas_kidem/12*ay)],
        [f"{format_tl(esas_kidem)} / 365", "x", f"{gun} Gün", "=", format_tl(esas_kidem/365*gun)],
        ["**TOPLAM BRÜT**", "", "", "", f"**{format_tl(b_kidem)}**"],
        ["Damga Vergisi (Binde 7,59)", "", "", "=", format_tl(k_res['dv'])],
        ["**NET KIDEM**", "", "", "", f"**{format_tl(k_res['net'])}**"]
    ]))

    b_ihbar = (son_brut / 30) * 7 * ihbar_hafta
    i_res = kesinti_hesapla(b_ihbar)
    st.markdown(f"**İhbar Tazminatı Hesabı ({ihbar_hafta} Hafta):**")
    st.table(pd.DataFrame([
        [f"{format_tl(son_brut)} / 30", "x", f"7 Gün x {ihbar_hafta} Hafta", "=", format_tl(b_ihbar)],
        ["Gelir Vergisi (%15)", "", "", "=", format_tl(i_res['gv'])],
        ["Damga Vergisi (Binde 7,59)", "", "", "=", format_tl(i_res['dv'])],
        ["**NET İHBAR**", "", "", "", f"**{format_tl(i_res['net'])}**"]
    ]))

    # --- 5. YILLIK İZİN ---
    st.markdown("### 5. Yıllık İzin Ücretinin Hesaplanması")
    b_izin = (son_brut / 30) * izin_gun
    z_res = kesinti_hesapla(b_izin)
    st.table(pd.DataFrame([
        ["Brüt İzin Alacağı", f"{format_tl(son_brut/30)} x {izin_gun} Gün", "=", format_tl(b_izin)],
        ["SGK Primi (%14)", "", "=", format_tl(z_res['sgk'])],
        ["İşsizlik Sigortası (%1)", "", "=", format_tl(z_res['issizlik'])],
        ["Gelir Vergisi (%15)", "", "=", format_tl(z_res['gv'])],
        ["Damga Vergisi (Binde 7,59)", "", "=", format_tl(z_res['dv'])],
        ["**NET YILLIK İZİN**", "", "=", f"**{format_tl(z_res['net'])}**"]
    ]))

    # --- 6. FAZLA MESAİ ---
    st.markdown("### 6. Fazla Mesai Ücretinin Hesaplanması")
    fm_brut, ubgt_brut = 0, 0
    fm_rows, ubgt_rows = [], []
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_maas = ASGARI_UCRET_TABLOSU.get(y, 25000.0) * maas_orani
        sz = (d_maas / 225) * 1.5
        bas = max(g_tarih, datetime(y, 1, 1).date()); bit = min(c_tarih, datetime(y, 12, 31).date())
        h_say = max(0, (bit - bas).days / 7)
        donem_fm = h_say * fm_saat * sz
        fm_brut += donem_fm
        fm_rows.append([f"{y}", f"({format_tl(d_maas)}/225)*1,5", f"{fm_saat} Saat * {h_say:.2f} Hafta", format_tl(donem_fm)])
        
        gunluk = d_maas / 30
        d_gun = ubgt_yillik * ((bit - bas).days / 365)
        donem_ubgt = d_gun * gunluk
        ubgt_brut += donem_ubgt
        ubgt_rows.append([f"{y}", f"{format_tl(d_maas)} / 30", f"{d_gun:.2f} Gün", format_tl(donem_ubgt)])
    
    st.table(pd.DataFrame(fm_rows, columns=["Dönem", "Saatlik Zamlı", "FM Süresi", "Brüt"]))
    fm_res = kesinti_hesapla(fm_brut)
    st.markdown("**Fazla Mesai Kesinti Dökümü:**")
    st.table(pd.DataFrame([
        ["SGK Primi (%14)", "=", format_tl(fm_res['sgk'])],
        ["İşsizlik Sigortası (%1)", "=", format_tl(fm_res['issizlik'])],
        ["Gelir Vergisi (%15)", "=", format_tl(fm_res['gv'])],
        ["Damga Vergisi (Binde 7,59)", "=", format_tl(fm_res['dv'])],
        ["**Net Fazla Mesai**", "=", f"**{format_tl(fm_res['net'])}**"]
    ]))

    # --- 6.1 UBGT ---
    st.markdown("### 6.1 UBGT Ücretinin Hesaplanması")
    st.table(pd.DataFrame(ubgt_rows, columns=["Dönem", "Günlük Ücret", "Gün Sayısı", "Brüt"]))
    u_res = kesinti_hesapla(ubgt_brut)
    st.markdown("**UBGT Kesinti Dökümü:**")
    st.table(pd.DataFrame([
        ["SGK Primi (%14)", "=", format_tl(u_res['sgk'])],
        ["İşsizlik Sigortası (%1)", "=", format_tl(u_res['issizlik'])],
        ["Gelir Vergisi (%15)", "=", format_tl(u_res['gv'])],
        ["Damga Vergisi (Binde 7,59)", "=", format_tl(u_res['dv'])],
        ["**Net UBGT**", "=", f"**{format_tl(u_res['net'])}**"]
    ]))

    # --- 7. SONUÇ VE İCMAL ---
    st.markdown("### 7. Sonuç ve İcmal (Özet) Tablosu")
    g_brut = b_kidem + b_ihbar + b_izin + fm_brut + ubgt_brut
    g_kes = k_res['toplam'] + i_res['toplam'] + z_res['toplam'] + fm_res['toplam'] + u_res['toplam']
    g_net = k_res['net'] + i_res['net'] + z_res['net'] + fm_res['net'] + u_res['net']
    
    icmal_data = [
        ["Kıdem Tazminatı", format_tl(b_kidem), format_tl(k_res['toplam']), format_tl(k_res['net'])],
        ["İhbar Tazminatı", format_tl(b_ihbar), format_tl(i_res['toplam']), format_tl(i_res['net'])],
        ["Yıllık İzin Ücreti", format_tl(b_izin), format_tl(z_res['toplam']), format_tl(z_res['net'])],
        ["Fazla Mesai Ücreti", format_tl(fm_brut), format_tl(fm_res['toplam']), format_tl(fm_res['net'])],
        ["UBGT Ücreti", format_tl(ubgt_brut), format_tl(u_res['toplam']), format_tl(u_res['net'])],
        ["**GENEL TOPLAM**", "**"+format_tl(g_brut)+"**", "**"+format_tl(g_kes)+"**", "**"+format_tl(g_net)+"**"]
    ]
    st.table(pd.DataFrame(icmal_data, columns=["Alacak Kalemi", "Brüt Tutar", "Kesintiler", "Net Ödenecek"]))
