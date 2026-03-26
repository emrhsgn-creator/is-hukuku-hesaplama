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

if st.button("HESAPLA VE RAPORU OLUŞTUR", type="primary"):
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
        ["Kıdem Tazminatına Esas Ücret", format_tl(esas_kidem_ucret)],
        ["İhbar Tazminatına Esas Ücret", format_tl(son_brut)],
        ["Brüt Ücretin Asgari Ücrete Oranı", "{:.5f}".format(maas_orani).replace(".", ",")]
    ]
    st.table(pd.DataFrame(ucret_data, columns=["Kalem", "Miktar"]))

    # --- 4. KIDEM VE İHBAR ---
    st.markdown("### 4. Kıdem ve İhbar Tazminatının Hesaplanması")
    st.caption(f"Hizmet Süresi: {g_tarih.strftime('%d/%m/%Y')} - {c_tarih.strftime('%d/%m/%Y')} ({yil} Yıl {ay} Ay {gun} Gün)")
    
    # Kıdem
    k_y = esas_kidem_ucret * yil
    k_a = (esas_kidem_ucret / 12) * ay
    k_g = (esas_kidem_ucret / 365) * gun
    t_b_k = k_y + k_a + k_g
    dv_k = t_b_k * 0.00759
    
    st.markdown("**Kıdem Tazminatı:**")
    st.table(pd.DataFrame([
        [format_tl(esas_kidem_ucret), "x", f"{yil} Yıl", "=", format_tl(k_y)],
        [f"{format_tl(esas_kidem_ucret)} / 12", "x", f"{ay} Ay", "=", format_tl(k_a)],
        [f"{format_tl(esas_kidem_ucret)} / 365", "x", f"{gun} Gün", "=", format_tl(k_g)],
        ["**TOPLAM BRÜT**", "", "", "", format_tl(t_b_k)],
        ["Damga Vergisi", "Binde 7,59", "", "=", format_tl(dv_k)],
        ["**NET KIDEM**", "", "", "", f"**{format_tl(t_b_k - dv_k)}**"]
    ]))

    # İhbar
    hafta = 2 if (c_tarih-g_tarih).days < 180 else 4 if (c_tarih-g_tarih).days < 540 else 6 if (c_tarih-g_tarih).days < 1080 else 8
    b_ihbar = (son_brut / 30) * 7 * hafta
    gv_ihbar = b_ihbar * 0.15
    dv_ihbar = b_ihbar * 0.00759
    
    st.markdown("**İhbar Tazminatı:**")
    st.table(pd.DataFrame([
        [f"{format_tl(son_brut)} / 30", "x", "7 Gün", f"x {hafta} Hafta =", format_tl(b_ihbar)],
        ["Gelir Vergisi", "%15", "", "=", format_tl(gv_ihbar)],
        ["Damga Vergisi", "Binde 7,59", "", "=", format_tl(dv_ihbar)],
        ["**NET İHBAR**", "", "", "", f"**{format_tl(b_ihbar - gv_ihbar - dv_ihbar)}**"]
    ]))

    # --- 5. YILLIK İZİN ---
    st.markdown("### 5. Yıllık İzin Ücretinin Hesaplanması")
    b_izin = (son_brut / 30) * izin_gun
    sgk_i = b_izin * 0.15
    gv_i = (b_izin - sgk_i) * 0.15
    dv_i = b_izin * 0.00759
    
    st.table(pd.DataFrame([
        ["Brüt Ücret / 30", "Günlük Brüt", "Gün Sayısı", "Brüt İzin Alacağı"],
        [f"{format_tl(son_brut)} / 30", format_tl(son_brut/30), f"x {izin_gun}", format_tl(b_izin)],
        ["Kesintiler", "SGK %15 + GV %15 + DV", "", "=", format_tl(sgk_i + gv_i + dv_i)],
        ["**NET İZİN**", "", "", "=", f"**{format_tl(b_izin - sgk_i - gv_i - dv_i)}**"]
    ]))

    # --- 6. FAZLA MESAİ VE UBGT ---
    st.markdown("### 6. Fazla Mesai ve Genel Tatil Sürelerinin Tespiti ve Ücretinin Hesaplanması")
    
    # FAZLA MESAİ DETAYLI TABLO
    st.markdown("**Fazla Mesai Ücreti Hesap Tablosu:**")
    fm_rows = []
    total_fm_brut = 0
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_asgari = ASGARI_UCRET_TABLOSU.get(y, 25000.0)
        saatlik = (d_asgari * maas_orani / 225) * 1.5
        bas = max(g_tarih, datetime(y, 1, 1).date())
        bit = min(c_tarih, datetime(y, 12, 31).date())
        h_say = max(0, (bit - bas).days / 7)
        toplam_saat = h_say * fm_saat
        d_brut = toplam_saat * saatlik
        total_fm_brut += d_brut
        
        fm_rows.append([
            f"{bas.strftime('%d/%m/%Y')}-{bit.strftime('%d/%m/%Y')}",
            f"{format_tl(saatlik)} x {toplam_saat:.2f} Saat",
            format_tl(d_brut)
        ])
    
    st.table(pd.DataFrame(fm_rows, columns=["Dönem", "Saatlik Ücret x Toplam Saat", "Dönem Brüt"]))
    
    sgk_fm = total_fm_brut * 0.15
    gv_fm = (total_fm_brut - sgk_fm) * 0.15
    dv_fm = total_fm_brut * 0.00759
    
    st.table(pd.DataFrame([
        ["**Brüt Fazla Mesai Toplamı**", format_tl(total_fm_brut)],
        ["Yasal Kesintiler (SGK+GV+DV)", format_tl(sgk_fm + gv_fm + dv_fm)],
        ["**NET FAZLA MESAİ ALACAĞI**", f"**{format_tl(total_fm_brut - sgk_fm - gv_fm - dv_fm)}**"]
    ]))

    # UBGT DETAYLI TABLO (EKLEDİM)
    st.markdown("**UBGT (Genel Tatil) Ücreti Hesap Tablosu:**")
    ubgt_rows = []
    total_ubgt_brut = 0
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_asgari = ASGARI_UCRET_TABLOSU.get(y, 25000.0)
        gunluk = (d_asgari * maas_orani / 30)
        bas = max(g_tarih, datetime(y, 1, 1).date())
        bit = min(c_tarih, datetime(y, 12, 31).date())
        yil_orani = (bit - bas).days / 365
        d_gun = ubgt_yillik * yil_orani
        d_brut = d_gun * gunluk
        total_ubgt_brut += d_brut
        
        ubgt_rows.append([
            f"{y} Yılı",
            f"{format_tl(gunluk)} x {d_gun:.2f} Gün",
            format_tl(d_brut)
        ])

    st.table(pd.DataFrame(ubgt_rows, columns=["Dönem", "Günlük Ücret x Gün Sayısı", "Dönem Brüt"]))

    sgk_u = total_ubgt_brut * 0.15
    gv_u = (total_ubgt_brut - sgk_u) * 0.15
    dv_u = total_ubgt_brut * 0.00759

    st.table(pd.DataFrame([
        ["**Brüt UBGT Toplamı**", format_tl(total_ubgt_brut)],
        ["Yasal Kesintiler (SGK+GV+DV)", format_tl(sgk_u + gv_u + dv_u)],
        ["**NET UBGT ALACAĞI**", f"**{format_tl(total_ubgt_brut - sgk_u - gv_u - dv_u)}**"]
    ]))
