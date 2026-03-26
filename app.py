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

def format_tl(value):
    return "{:,.2f} TL".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

def kesinti_hesapla(brut, tip="standart"):
    dv = brut * 0.00759
    if tip == "kıdem":
        return {"dv": dv, "gv": 0.0, "sgk": 0.0, "net": brut - dv}
    sgk = brut * 0.15 # %14 + %1
    gv = (brut - sgk) * 0.15 # %15 gelir vergisi (basit usul)
    return {"dv": dv, "gv": gv, "sgk": sgk, "net": brut - (dv + gv + sgk)}

st.set_page_config(page_title="Bilirkişi Raporu Hazırlığı", layout="centered")
st.markdown("<h2 style='text-align: center;'>İşçilik Alacakları Bilirkişi Raporu Hazırlığı</h2>", unsafe_allow_html=True)

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
    # PARAMETRELER
    delta = relativedelta(c_tarih, g_tarih)
    yil, ay, gun = delta.years, delta.months, delta.days
    giydirilmis_brut = son_brut + yemek_ucreti
    tavan_tutari = KIDEM_TAVANI_TABLOSU.get(c_tarih.year, 41828.42)
    esas_kidem_ucret = min(giydirilmis_brut, tavan_tutari)
    maas_orani = son_brut / ASGARI_UCRET_TABLOSU.get(c_tarih.year, 3577.50)

    # --- 3. ÜCRET TESPİTİ ---
    st.markdown("### 3. Hesaplamalarda Kullanılacak Ücret Miktarları İle İlgili Tespit")
    ucret_data = [
        ["Brüt Ücret", format_tl(son_brut)],
        ["Yemek Ücreti", format_tl(yemek_ucreti)],
        ["Giydirilmiş Brüt Ücret", format_tl(giydirilmis_brut)],
        ["Kıdem Tazminatı Tavan Tutarı", format_tl(tavan_tutari)],
        ["Kıdem Tazminatına Esas Ücret", format_tl(esas_kidem_ucret)],
        ["İhbar Tazminatına Esas Ücret", format_tl(son_brut)],
        ["Brüt Ücretin Asgari Ücrete Oranı", "{:.5f}".format(maas_orani).replace(".", ",")]
    ]
    st.table(pd.DataFrame(ucret_data, columns=["Kalem", "Miktar"]))

    # --- 4. KIDEM VE İHBAR ---
    st.markdown("### 4. Kıdem ve İhbar Tazminatının Hesaplanması")
    st.caption(f"Hizmet Süresi: {yil} Yıl {ay} Ay {gun} Gün")
    
    k_yil = esas_kidem_ucret * yil
    k_ay = (esas_kidem_ucret / 12) * ay
    k_gun = (esas_kidem_ucret / 365) * gun
    b_kidem = k_yil + k_ay + k_gun
    k_res = kesinti_hesapla(b_kidem, "kıdem")

    st.markdown("**Kıdem Tazminatı Hesabı:**")
    st.table(pd.DataFrame([
        [format_tl(esas_kidem_ucret), "x", f"{yil} Yıl", "=", format_tl(k_yil)],
        [f"{format_tl(esas_kidem_ucret)} / 12", "x", f"{ay} Ay", "=", format_tl(k_ay)],
        [f"{format_tl(esas_kidem_ucret)} / 365", "x", f"{gun} Gün", "=", format_tl(k_gun)],
        ["**TOPLAM BRÜT**", "", "", "", f"**{format_tl(b_kidem)}**"],
        ["Damga Vergisi", "Binde 7,59", "", "=", format_tl(k_res['dv'])],
        ["**NET KIDEM**", "", "", "=", f"**{format_tl(k_res['net'])}**"]
    ]))

    hafta = 2 if (c_tarih-g_tarih).days < 180 else 4 if (c_tarih-g_tarih).days < 540 else 6 if (c_tarih-g_tarih).days < 1080 else 8
    b_ihbar = (son_brut / 30) * 7 * hafta
    i_res = kesinti_hesapla(b_ihbar)
    st.markdown(f"**İhbar Tazminatı Hesabı ({hafta} Hafta):**")
    st.table(pd.DataFrame([
        [f"{format_tl(son_brut)} / 30", "x", "7 Gün", f"x {hafta} Hafta =", format_tl(b_ihbar)],
        ["Kesintiler (GV+DV)", "Toplam", "", "=", format_tl(i_res['gv']+i_res['dv']+i_res['sgk'])],
        ["**NET İHBAR**", "", "", "=", f"**{format_tl(i_res['net'])}**"]
    ]))

    # --- 5. YILLIK İZİN ---
    st.markdown("### 5. Yıllık İzin Ücretinin Hesaplanması")
    b_izin = (son_brut / 30) * izin_gun
    z_res = kesinti_hesapla(b_izin)
    st.table(pd.DataFrame([
        ["Günlük Brüt", "Gün Sayısı", "Brüt Alacak", "Kesintiler", "Net Alacak"],
        [format_tl(son_brut/30), f"x {izin_gun}", format_tl(b_izin), format_tl(z_res['gv']+z_res['sgk']+z_res['dv']), format_tl(z_res['net'])]
    ]))

    # --- 6. FAZLA MESAİ VE UBGT ---
    st.markdown("### 6. Fazla Mesai ve UBGT Hesabı")
    fm_brut_total, ubgt_brut_total = 0, 0
    fm_rows = []
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_asgari = ASGARI_UCRET_TABLOSU.get(y, 25000.0)
        saatlik = (d_asgari * maas_orani / 225) * 1.5
        h_sayisi = max(0, (min(c_tarih, datetime(y, 12, 31).date()) - max(g_tarih, datetime(y, 1, 1).date())).days / 7)
        b_fm = h_sayisi * fm_saat * saatlik
        fm_brut_total += b_fm
        fm_rows.append([f"{y} Dönemi", f"{format_tl(d_asgari)} x {maas_orani:.4f} / 225 x 1,5", format_tl(saatlik), format_tl(b_fm)])
    
    st.table(pd.DataFrame(fm_rows, columns=["Dönem", "Saatlik Hesaplama", "Saatlik Zamlı", "Brüt Tutar"]))
    fm_res = kesinti_hesapla(fm_brut_total)
    
    # UBGT (Basit Yıllık Hesap)
    ubgt_brut_total = (son_brut / 30) * ubgt_yillik * yil
    u_res = kesinti_hesapla(ubgt_brut_total)

    # --- 7. SONUÇ VE İCMAL TABLOSU ---
    st.markdown("### 7. Sonuç ve İcmal (Özet) Tablosu")
    st.write("Hesaplanan tüm alacak kalemlerinin brüt ve net dökümü aşağıdadır:")
    
    icmal_data = [
        ["Kıdem Tazminatı", format_tl(b_kidem), format_tl(k_res['dv']), format_tl(k_res['net'])],
        ["İhbar Tazminatı", format_tl(b_ihbar), format_tl(i_res['gv']+i_res['dv']+i_res['sgk']), format_tl(i_res['net'])],
        ["Yıllık İzin Ücreti", format_tl(b_izin), format_tl(z_res['gv']+z_res['dv']+z_res['sgk']), format_tl(z_res['net'])],
        ["Fazla Mesai Ücreti", format_tl(fm_brut_total), format_tl(fm_res['gv']+fm_res['dv']+fm_res['sgk']), format_tl(fm_res['net'])],
        ["UBGT Ücreti", format_tl(ubgt_brut_total), format_tl(u_res['gv']+u_res['dv']+u_res['sgk']), format_tl(u_res['net'])],
        ["**GENEL TOPLAM**", "**" + format_tl(b_kidem+b_ihbar+b_izin+fm_brut_total+ubgt_brut_total) + "**", "-", "**" + format_tl(k_res['net']+i_res['net']+z_res['net']+fm_res['net']+u_res['net']) + "**"]
    ]
    
    df_icmal = pd.DataFrame(icmal_data, columns=["Alacak Kalemi", "Brüt Tutar", "Kesintiler Toplamı", "Net Ödenecek"])
    st.table(df_icmal)
    
    st.success(f"**Rapor Sonucu:** Davacıya ödenmesi gereken toplam net tutar **{format_tl(k_res['net']+i_res['net']+z_res['net']+fm_res['net']+u_res['net'])}** olarak hesaplanmıştır.")
