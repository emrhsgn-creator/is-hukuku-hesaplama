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

# Görseldeki gibi başlık
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
    # TEMEL PARAMETRELER
    delta = relativedelta(c_tarih, g_tarih)
    yil, ay, gun = delta.years, delta.months, delta.days
    giydirilmis_brut = son_brut + yemek_ucreti
    tavan_tutari = KIDEM_TAVANI_TABLOSU.get(c_tarih.year, 41828.42)
    esas_kidem_ucret = min(giydirilmis_brut, tavan_tutari)
    donem_asgari = ASGARI_UCRET_TABLOSU.get(c_tarih.year, 25000.0)
    maas_orani = son_brut / ASGARI_UCRET_TABLOSU.get(c_tarih.year, 3577.50)

    # --- BÖLÜM 3: ÜCRET TESPİTİ ---
    st.markdown("### 3. Hesaplamalarda Kullanılacak Ücret Miktarları İle İlgili Tespit")
    ucret_data = [
        ["Brüt Ücret", format_tl(son_brut)],
        ["Yemek Ücreti", format_tl(yemek_ucreti)],
        ["Giydirilmiş Brüt Ücret", format_tl(giydirilmis_brut)],
        ["Kıdem Tazminatı Tavan Tutarı", format_tl(tavan_tutari)],
        ["Kıdem Tazminatına Esas Ücret", format_tl(esas_kidem_ucret)],
        ["İhbar Tazminatına Esas Ücret", format_tl(son_brut)],
        ["Dönem Asgari Ücret (" + str(c_tarih.year) + ")", format_tl(donem_asgari)],
        ["Brüt Ücretin Asgari Ücrete Oranı", "{:.5f}".format(maas_orani).replace(".", ",")]
    ]
    st.table(pd.DataFrame(ucret_data, columns=["Kalem", "Miktar"]))

    # --- BÖLÜM 4: KIDEM VE İHBAR ---
    st.markdown("### 4. Kıdem ve İhbar Tazminatının Hesaplanması")
    st.caption(f"Hizmet Süresi: {g_tarih.strftime('%d/%m/%Y')} - {c_tarih.strftime('%d/%m/%Y')} ({yil} Yıl {ay} Ay {gun} Gün)")
    
    # Kıdem Alt Kıvrımları
    kidem_yil_tutar = esas_kidem_ucret * yil
    kidem_ay_tutar = (esas_kidem_ucret / 12) * ay
    kidem_gun_tutar = (esas_kidem_ucret / 365) * gun
    toplam_brut_kidem = kidem_yil_tutar + kidem_ay_tutar + kidem_gun_tutar
    dv_kidem = toplam_brut_kidem * 0.00759
    net_kidem = toplam_brut_kidem - dv_kidem

    st.markdown("**Kıdem Tazminatı:**")
    kidem_tablo = [
        [format_tl(esas_kidem_ucret), "x", f"{yil} Yıl", "=", format_tl(kidem_yil_tutar)],
        [f"{format_tl(esas_kidem_ucret)} / 12", "x", f"{ay} Ay", "=", format_tl(kidem_ay_tutar)],
        [f"{format_tl(esas_kidem_ucret)} / 365", "x", f"{gun} Gün", "=", format_tl(kidem_gun_tutar)],
        ["**TOPLAM**", "", "", "", f"**{format_tl(toplam_brut_kidem)}**"],
        ["Damga Vergisi", "Binde 7,59", "", "", format_tl(dv_kidem)],
        ["**Net Kıdem Tazminatı**", "", "", "", f"**{format_tl(net_kidem)}**"]
    ]
    st.table(pd.DataFrame(kidem_tablo))

    # İhbar Alt Kıvrımları
    hafta = 2 if (c_tarih-g_tarih).days < 180 else 4 if (c_tarih-g_tarih).days < 540 else 6 if (c_tarih-g_tarih).days < 1080 else 8
    brut_ihbar = (son_brut / 30) * 7 * hafta
    gv_ihbar = (brut_ihbar - (brut_ihbar * 0.15)) * 0.15 # Basit GV mantığı
    dv_ihbar = brut_ihbar * 0.00759
    net_ihbar = brut_ihbar - (gv_ihbar + dv_ihbar)

    st.markdown("**İhbar Tazminatı:**")
    st.caption(f"4857 Sayılı Yasanın 17. maddesi uyarınca ihbar öneli {hafta} haftadır.")
    ihbar_tablo = [
        [f"{format_tl(son_brut)} / 30", "x", "7 Gün", f"x {hafta} Hafta =", format_tl(brut_ihbar)],
        ["Gelir Vergisi", "%15", "", "=", format_tl(gv_ihbar)],
        ["Damga Vergisi", "Binde 7,59", "", "=", format_tl(dv_ihbar)],
        ["**Net İhbar Tazminatı**", "", "", "=", f"**{format_tl(net_ihbar)}**"]
    ]
    st.table(pd.DataFrame(ihbar_tablo))

    # --- BÖLÜM 5: YILLIK İZİN ---
    st.markdown("### 5. Yıllık İzin Süresinin Tespiti ve Ücretinin Hesaplanması")
    st.caption(f"İşçinin 1 tam yıllık kıdemine karşılık hak kazandığı yıllık izin süresi {izin_gun} gündür.")
    brut_izin = (son_brut / 30) * izin_gun
    sgk_izin = brut_izin * 0.15
    gv_izin = (brut_izin - sgk_izin) * 0.15
    dv_izin = brut_izin * 0.00759
    net_izin = brut_izin - (sgk_izin + gv_izin + dv_izin)

    izin_tablo = [
        ["Brüt Ücret", "Günlük Brüt Ücret", "Gün Sayısı", "Brüt İzin Alacağı"],
        [f"{format_tl(son_brut)} / 30", format_tl(son_brut/30), f"x {izin_gun}", format_tl(brut_izin)],
        ["SGK Primi", "%15", "=", format_tl(sgk_izin)],
        ["Gelir Vergisi", "%15", "=", format_tl(gv_izin)],
        ["Damga Vergisi", "Binde 7,59", "=", format_tl(dv_izin)],
        ["**Net Alacak**", "", "=", f"**{format_tl(net_izin)}**"]
    ]
    st.table(pd.DataFrame(izin_tablo))

    # --- BÖLÜM 6: FAZLA MESAİ VE UBGT ---
    st.markdown("### 6. Fazla Mesai ve Genel Tatil Sürelerinin Tespiti ve Ücretinin Hesaplanması")
    st.caption(f"(Not: Brüt ücretin ilgili yıllardaki asgari ücrete oranı ({maas_orani:.5f}) kullanılarak geçmiş yıl ücretleri bulunmuştur.)")
    
    fm_toplam_brut = 0
    fm_rows = []
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_asgari = ASGARI_UCRET_TABLOSU.get(y, 25000.0)
        saatlik_zamli = (d_asgari * maas_orani / 225) * 1.5
        
        bas = max(g_tarih, datetime(y, 1, 1).date())
        bit = min(c_tarih, datetime(y, 12, 31).date())
        hafta_say = max(0, (bit - bas).days / 7)
        donem_brut = hafta_say * fm_saat * saatlik_zamli
        fm_toplam_brut += donem_brut
        
        formül = f"{format_tl(d_asgari)} x {maas_orani:.4f} / 225 x 1,5"
        fm_rows.append([f"{bas.strftime('%d/%m/%Y')}-{bit.strftime('%d/%m/%Y')}", formül, f"= {format_tl(saatlik_zamli)}"])

    st.markdown("**Fazla Mesai Ücreti**")
    st.table(pd.DataFrame(fm_rows, columns=["Çalışma Dönemi", "Saatlik Zamlı Ücret Hesabı", "Sonuç"]))
    
    sgk_fm = fm_toplam_brut * 0.15
    gv_fm = (fm_toplam_brut - sgk_fm) * 0.15
    dv_fm = fm_toplam_brut * 0.00759
    net_fm = fm_toplam_brut - (sgk_fm + gv_fm + dv_fm)

    fm_ozet = [
        ["Brüt Fazla Mesai Ücreti", format_tl(fm_toplam_brut)],
        ["SGK Kesintisi", "%15 Üzerinden"],
        ["Gelir Vergisi", "%15 Üzerinden (Kademeli varsayımıyla)"],
        ["Damga Vergisi", "Binde 7,59"],
        ["**Net Fazla Mesai Ücreti Alacağı**", f"**{format_tl(net_fm)}**"]
    ]
    st.table(pd.DataFrame(fm_ozet))
