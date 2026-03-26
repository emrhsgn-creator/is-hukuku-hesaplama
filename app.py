import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

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
        return {"brut": brut, "dv": dv, "gv": 0.0, "sgk": 0.0, "issizlik": 0.0, "toplam": dv, "net": brut - dv}
    sgk = brut * 0.14
    issizlik = brut * 0.01
    gv = (brut - (sgk + issizlik)) * 0.15 
    toplam = dv + sgk + gv + issizlik
    return {"brut": brut, "dv": dv, "gv": gv, "sgk": sgk, "issizlik": issizlik, "toplam": toplam, "net": brut - toplam}

def create_docx(isim, sections_list):
    doc = Document()
    doc.styles['Normal'].font.name = 'Arial'
    doc.styles['Normal'].font.size = Pt(10)

    t = doc.add_heading('BİLİRKİŞİ RAPORU HESAPLAMA DÖKÜMÜ', 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Davacı: {isim}")
    doc.add_paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y')}")

    for title, df in sections_list:
        doc.add_heading(title, level=1)
        if df is not None:
            table = doc.add_table(rows=df.shape[0] + 1, cols=df.shape[1])
            table.style = 'Table Grid'
            for j in range(df.shape[1]):
                table.cell(0, j).text = str(df.columns[j])
            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    table.cell(i + 1, j).text = str(df.values[i, j])
        doc.add_paragraph("\n")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

st.set_page_config(page_title="Bilirkişi Raporu Pro", layout="wide")
st.markdown("<h2 style='text-align: center;'>⚖️ İşçilik Alacakları Bilirkişi Raporu</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Giriş Parametreleri")
    isim = st.text_input("İşçinin Adı Soyadı", "Onur Erol")
    g_tarih = st.date_input("İşe Giriş", datetime(2020, 1, 15))
    c_tarih = st.date_input("İşten Çıkış", datetime(2021, 7, 26))
    son_brut = st.number_input("Brüt Ücret", value=5595.11)
    yemek = st.number_input("Yemek (Brüt)", value=350.0)
    fm_s = st.number_input("Haftalık FM Saat", value=12.0)
    iz_g = st.number_input("Kalan İzin", value=14)
    ubgt_y = st.number_input("Yıllık UBGT", value=5)

if st.button("HESAPLA VE RAPORU OLUŞTUR", type="primary"):
    delta = relativedelta(c_tarih, g_tarih); yil, ay, gun = delta.years, delta.months, delta.days
    toplam_g = (c_tarih - g_tarih).days; giyd_b = son_brut + yemek
    tavan = KIDEM_TAVANI_TABLOSU.get(c_tarih.year, 41828.42)
    esas_k = min(giyd_b, tavan); asgari_c = ASGARI_UCRET_TABLOSU.get(c_tarih.year, 3577.50)
    oran = son_brut / asgari_c; ihbar_h = 2 if toplam_g < 180 else 4 if toplam_g < 540 else 6 if toplam_g < 1080 else 8

    # Word için saklanacak bölümler listesi
    word_sections = []

    # 3. ÜCRET TESPİTİ
    df_ucret = pd.DataFrame([["Brüt Ücret", format_tl(son_brut)], ["Giydirilmiş Brüt", format_tl(giyd_b)], ["Kıdem Tavanı", format_tl(tavan)], ["Kıdem Esas Ücret", format_tl(esas_k)], ["Asgari Ücrete Oranı", "{:.5f}".format(oran).replace(".", ",")]], columns=["Kalem", "Miktar"])
    st.markdown("### 3. Ücret Tespitleri"); st.table(df_ucret)
    word_sections.append(("3. ÜCRET TESPİTLERİ", df_ucret))

    # 4. KIDEM
    b_k = (esas_k * yil) + (esas_k/12*ay) + (esas_k/365*gun); k_r = kesinti_hesapla(b_k, "kıdem")
    df_k = pd.DataFrame([[format_tl(esas_k), "x", f"{yil} Yıl", "=", format_tl(esas_k*yil)], ["TOPLAM BRÜT", "", "", "", format_tl(b_k)], ["Damga Vergisi", "", "", "", format_tl(k_r['dv'])], ["NET KIDEM", "", "", "", format_tl(k_r['net'])]])
    st.markdown("### 4. Kıdem Tazminatı"); st.table(df_k)
    word_sections.append(("4. KIDEM TAZMİNATI", df_k))

    # 4.1 İHBAR
    b_i = (son_brut / 30) * 7 * ihbar_h; i_r = kesinti_hesapla(b_i)
    df_i = pd.DataFrame([["Brüt İhbar", format_tl(b_i)], ["GV (%15)", format_tl(i_r['gv'])], ["DV (Binde 7,59)", format_tl(i_r['dv'])], ["NET İHBAR", format_tl(i_r['net'])]], columns=["Kalem", "Tutar"])
    st.markdown("### 4.1 İhbar Tazminatı"); st.table(df_i)
    word_sections.append(("4.1 İHBAR TAZMİNATI", df_i))

    # 5. YILLIK İZİN
    b_iz = (son_brut / 30) * iz_g; z_r = kesinti_hesapla(b_iz)
    df_iz = pd.DataFrame([["Brüt İzin", format_tl(b_iz)], ["Kesintiler Toplamı", format_tl(z_r['toplam'])], ["NET İZİN", format_tl(z_r['net'])]], columns=["Kalem", "Tutar"])
    st.markdown("### 5. Yıllık İzin"); st.table(df_iz)
    word_sections.append(("5. YILLIK İZİN ÜCRETİ", df_iz))

    # 6. FM
    fm_b, fm_r_l = 0, []
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_m = ASGARI_UCRET_TABLOSU.get(y, 25000.0) * oran
        sz = (d_m / 225) * 1.5; h_s = max(0, (min(c_tarih, datetime(y, 12, 31).date()) - max(g_tarih, datetime(y, 1, 1).date())).days / 7)
        d_fm = h_s * fm_s * sz; fm_b += d_fm
        fm_r_l.append([f"{y}", format_tl(sz), f"{fm_s} Saat * {h_s:.2f} Hafta", format_tl(d_fm)])
    df_fm_d = pd.DataFrame(fm_r_l, columns=["Dönem", "Saatlik Zamlı", "FM Süresi", "Brüt"])
    st.markdown("### 6. Fazla Mesai"); st.table(df_fm_d)
    word_sections.append(("6. FAZLA MESAİ DÖNEMSEL DÖKÜM", df_fm_d))
    fm_r = kesinti_hesapla(fm_b)
    df_fm_k = pd.DataFrame([["Brüt FM", format_tl(fm_b)], ["Net FM", format_tl(fm_r['net'])]], columns=["Kalem", "Tutar"])
    st.table(df_fm_k); word_sections.append(("6.1 FAZLA MESAİ ÖZET", df_fm_k))

    # 6.1 UBGT
    ub_b, ub_r_l = 0, []
    for y in range(g_tarih.year, c_tarih.year + 1):
        d_m = ASGARI_UCRET_TABLOSU.get(y, 25000.0) * oran; gu = d_m / 30
        d_g = ubgt_y * ((min(c_tarih, datetime(y, 12, 31).date()) - max(g_tarih, datetime(y, 1, 1).date())).days / 365)
        d_ub = d_g * gu; ub_b += d_ub
        ub_r_l.append([f"{y}", format_tl(gu), f"{d_g:.2f} Gün", format_tl(d_ub)])
    df_ub_d = pd.DataFrame(ub_r_l, columns=["Dönem", "Günlük Ücret", "Gün Sayısı", "Brüt"])
    st.markdown("### 6.1 UBGT Ücreti"); st.table(df_ub_d)
    word_sections.append(("6.2 UBGT DÖNEMSEL DÖKÜM", df_ub_d))
    ub_r = kesinti_hesapla(ub_b)
    df_ub_k = pd.DataFrame([["Brüt UBGT", format_tl(ub_b)], ["Net UBGT", format_tl(ub_r['net'])]], columns=["Kalem", "Tutar"])
    st.table(df_ub_k); word_sections.append(("6.3 UBGT ÖZET", df_ub_k))

    # 7. İCMAL
    df_icmal = pd.DataFrame([["Kıdem", format_tl(b_k), format_tl(k_r['net'])], ["İhbar", format_tl(b_i), format_tl(i_r['net'])], ["İzin", format_tl(b_iz), format_tl(z_r['net'])], ["FM", format_tl(fm_b), format_tl(fm_r['net'])], ["UBGT", format_tl(ub_b), format_tl(ub_r['net'])], ["**TOPLAM**", format_tl(b_k+b_i+b_iz+fm_b+ub_b), format_tl(k_r['net']+i_r['net']+z_r['net']+fm_r['net']+ub_r['net'])]], columns=["Kalem", "Brüt", "Net"])
    st.markdown("### 7. Sonuç ve İcmal"); st.table(df_icmal)
    word_sections.append(("7. SONUÇ VE İCMAL TABLOSU", df_icmal))

    # WORD BUTONU
    st.download_button(label="📥 Raporu Word Olarak İndir", data=create_docx(isim, word_sections), file_name=f"Rapor_{isim}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
