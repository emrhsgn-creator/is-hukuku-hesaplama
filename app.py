import streamlit as st
from google import genai
from google.genai import types

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="İşçilik Alacakları Hesaplama", page_icon="⚖️", layout="wide")
st.title("⚖️ İşçilik Alacakları Bilirkişi Raporu Oluşturucu")
st.markdown("Lütfen işçiye ait bilgileri girin. Sistem geçmiş dönem ve güncel asgari ücret/tavan bilgilerini bularak bilirkişi raporu formatında hesaplama yapacaktır.")

# --- 2. API ANAHTARI ---
st.sidebar.header("Ayarlar")
api_key = st.sidebar.text_input("Gemini API Anahtarınızı Girin", type="password")
st.sidebar.markdown("*(API anahtarınız yoksa [Google AI Studio](https://aistudio.google.com/) üzerinden ücretsiz alabilirsiniz.)*")

# --- 3. KULLANICI VERİ GİRİŞ FORMU ---
st.subheader("İşçi Bilgileri")
col1, col2 = st.columns(2)

with col1:
    isim = st.text_input("İşçinin Adı Soyadı", placeholder="Örn: Ahmet Yılmaz")
    giris_tarihi = st.date_input("İşe Giriş Tarihi")
    cikis_tarihi = st.date_input("İşten Çıkış Tarihi")

with col2:
    maas = st.number_input("Son Çıplak Brüt Ücret (TL)", min_value=0.0, step=1000.0, format="%.2f")
    yan_haklar = st.number_input("Aylık Diğer Sürekli Kazançlar (Yol, Yemek vb. Brüt TL)", min_value=0.0, step=100.0, format="%.2f")
    fazla_mesai = st.number_input("Haftalık Ortalama Fazla Mesai (Saat)", min_value=0.0, step=1.0)
    yillik_izin = st.number_input("Kalan Yıllık İzin (Gün)", min_value=0, step=1)

# --- 4. HESAPLAMA BUTONU VE API BAĞLANTISI ---
if st.button("Hesapla ve Raporu Oluştur", type="primary"):
    if not api_key:
        st.error("Lütfen sol menüden Gemini API anahtarınızı girin.")
    elif not isim or maas <= 0:
        st.warning("Lütfen işçinin adını ve son brüt ücretini geçerli bir şekilde girin.")
    elif giris_tarihi >= cikis_tarihi:
        st.warning("İşten çıkış tarihi, işe giriş tarihinden önce veya aynı olamaz.")
    else:
        with st.spinner("Yargıtay içtihatlarına uygun hesaplama yapılıyor, güncel tavan/asgari ücret verileri aranıyor... Bu işlem 10-15 saniye sürebilir."):
            try:
                # API İstemcisini Başlat
                client = genai.Client(api_key=api_key)

                # --- 5. SABİTLENMİŞ REFERANS RAPOR FORMATI (6. Sayfa ve Sonrası) ---
                referans_rapor_formati = """
                Aşağıdaki tablo yapılarını birebir kullanarak çıktıyı oluştur:

                ### 1. BİLGİLER VE SÜRE HESABI
                | Bilgi | Detay |
                | :--- | :--- |
                | **Davacı Adı Soyadı** | [İsim] |
                | **İşe Giriş Tarihi** | [Tarih] |
                | **İşten Çıkış Tarihi** | [Tarih] |
                | **Hizmet Süresi** | [X] Yıl, [Y] Ay, [Z] Gün |
                | **Son Çıplak Brüt Ücret** | [Tutar] TL |
                | **Giydirilmiş Brüt Ücret** | [Tutar] TL |
                | **Fesih Tarihindeki Kıdem Tavanı** | [Tutar] TL |

                ### 2. KIDEM TAZMİNATI HESABI
                | Hesap Kalemi | Süre / Çarpan | Tutar (TL) |
                | :--- | :--- | :--- |
                | **Hesaba Esas Ücret (Giydirilmiş/Tavan)** | 1 Aylık | [Tutar] |
                | **Tam Yıllar İçin** | [X] Yıl | [Tutar] |
                | **Artık Aylar İçin** | [Y] Ay | [Tutar] |
                | **Artık Günler İçin** | [Z] Gün | [Tutar] |
                | **Brüt Kıdem Tazminatı** | Toplam | [Tutar] |
                | **Damga Vergisi Kesintisi (%0.759)** | - | [Tutar] |
                | **NET KIDEM TAZMİNATI** | Toplam | **[Tutar] TL** |

                ### 3. İHBAR TAZMİNATI HESABI
                | Hesap Kalemi | Detay / Oran | Tutar (TL) |
                | :--- | :--- | :--- |
                | **İhbar Süresi** | [X] Hafta ([Y] Gün) | - |
                | **Brüt İhbar Tazminatı** | 30 Günlük Çıplak Ücret Üzerinden | [Tutar] |
                | **Gelir Vergisi Kesintisi** | %15 | [Tutar] |
                | **Damga Vergisi Kesintisi** | %0.759 | [Tutar] |
                | **NET İHBAR TAZMİNATI** | Toplam | **[Tutar] TL** |

                ### 4. YILLIK İZİN ÜCRETİ HESABI
                | Hesap Kalemi | Detay / Oran | Tutar (TL) |
                | :--- | :--- | :--- |
                | **Bakiye İzin Süresi** | [X] Gün | - |
                | **Son Günlük Çıplak Brüt Ücret** | Ücret/30 | [Tutar] |
                | **Brüt Yıllık İzin Ücreti** | Gün x Günlük Ücret | [Tutar] |
                | **SGK İşçi Payı** | %14 | [Tutar] |
                | **İşsizlik Sigortası İşçi Payı**| %1 | [Tutar] |
                | **Gelir Vergisi Kesintisi** | %15 (İlk Dilim) | [Tutar] |
                | **Damga Vergisi Kesintisi** | %0.759 | [Tutar] |
                | **NET YILLIK İZİN ÜCRETİ** | Toplam | **[Tutar] TL** |

                ### 5. FAZLA ÇALIŞMA (MESAİ) ÜCRETİ HESABI
                | Dönem Yılı | Brüt Ücret | Saatlik Ücret | Haftalık FM | Toplam Saat | Brüt Tutar | SGK+İşz. | GV+DV | Net Tutar |
                | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
                | [Yıl] | [Tutar] | [Tutar] | [Saat] | [Saat] | [Tutar] | [Tutar] | [Tutar] | [Tutar] |
                | **TOPLAM** | - | - | - | - | **[Brüt Toplam]** | - | - | **[Net Toplam]** |

                ### 6. SONUÇ VE İCMAL (ÖZET) TABLOSU
                | Alacak Kalemi | Brüt Tutar (TL) | Yasal Kesintiler (TL) | Net Ödenecek Tutar (TL) |
                | :--- | :--- | :--- | :--- |
                | **Kıdem Tazminatı** | [Tutar] | [Tutar] | [Tutar] |
                | **İhbar Tazminatı** | [Tutar] | [Tutar] | [Tutar] |
                | **Yıllık İzin Ücreti**| [Tutar] | [Tutar] | [Tutar] |
                | **Fazla Mesai Ücreti**| [Tutar] | [Tutar] | [Tutar] |
                | **GENEL TOPLAM** | **[Tutar]** | **[Tutar]** | **[Tutar]** |
                """

                # --- 6. ARKA PLAN SİSTEM PROMPTU ---
                sistem_promptu = f"""
                Sen uzman bir İş Hukuku Hesaplama Bilirkişisisin. 
                Görevin, kullanıcı verilerini kullanarak Türk İş Hukuku kurallarına göre işçi alacaklarını hesaplamak ve TAM OLARAK referans formatta sunmaktır.
                
                KULLANILACAK TABLO FORMATI VE BAŞLIKLAR:
                {referans_rapor_formati}
                
                HESAPLAMA KURALLARI:
                1. İnternet araması yaparak işten çıkış tarihindeki Kıdem Tazminatı Tavanı'nı ve Brüt Asgari Ücreti BUL.
                2. Geçmiş yılların fazla mesai hesabını yapabilmek için son brüt ücretin, son asgari ücrete oranını bul. Bu oranı geçmiş yılların asgari ücretleriyle çarparak o yılların maaşını bul ve saatlik ücreti buna göre (Maaş/225*1.5) hesapla.
                3. Kıdem tazminatı için giydirilmiş brüt ücret (Çıplak Brüt + Yan Haklar) kullan. Çıkan giydirilmiş ücret tavanı aşıyorsa, hesabı tavan üzerinden yap. Sadece binde 7.59 Damga Vergisi kes.
                4. İhbar süresi (6 aydan az 14 gün, 6 ay-1.5 yıl 28 gün, 1.5-3 yıl 42 gün, 3 yıldan fazla 56 gün) hesabı çıplak brüt ücretten yapılır.
                5. Kesinlikle sohbet metni (Merhaba, işte raporunuz vb.) EKLEME. Doğrudan '1. BİLGİLER VE SÜRE HESABI' başlığıyla başla. Rakamları 1.234,56 TL formatında yaz.
                """

                # Formdan gelen veriler
                kullanici_verisi = f"""
                İşçinin Adı Soyadı: {isim}
                İşe Giriş Tarihi: {giris_tarihi.strftime('%d.%m.%Y')}
                İşten Çıkış Tarihi: {cikis_tarihi.strftime('%d.%m.%Y')}
                Son Çıplak Brüt Ücret: {maas} TL
                Aylık Diğer Sürekli Kazançlar: {yan_haklar} TL
                Haftalık Ortalama Fazla Mesai: {fazla_mesai} Saat
                Kalan Yıllık İzin: {yillik_izin} Gün
                """

                # Gemini'yi Google Arama aracı açık şekilde çağır
                response = client.models.generate_content(
                    model='gemini-2.5-pro',
                    contents=kullanici_verisi,
                    config=types.GenerateContentConfig(
                        system_instruction=sistem_promptu,
                        temperature=0.1,
                        tools=[{"google_search": {}}] # Güncel asgari ücret ve tavan verileri için
                    )
                )

                # --- 7. SONUCU EKRANA BAS ---
                st.success("Hesaplama Başarılı! Rapor aşağıda sunulmuştur.")
                st.markdown("---")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Hesaplama sırasında bir hata oluştu: {e}")
