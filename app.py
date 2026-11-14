import sqlite3
import pandas as pd
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Müşteri, Gelir, Gider ve Vergi Takip Yazılımı",
    layout="wide",
)

# SQLite Veritabanı Bağlantısı ve Tablo Oluşturma
conn = sqlite3.connect("finans_takip.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS satislar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musteri_adi TEXT,
        urun_hizmet TEXT,
        adet INTEGER,
        birim_fiyat REAL,
        toplam_gelir REAL,
        tarih TEXT
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS giderler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kategori TEXT,
        aciklama TEXT,
        tutar REAL,
        tarih TEXT
    )
"""
)
conn.commit()

# Ana Başlık
st.title("📊 İşletme Finans ve Müşteri Takip Programı")
st.write(
    "Müşteri satışlarını, giderleri ve vergi hesaplamalarını tek panelden"
    " yönetin."
)

# Sekmeler (Tabs)
tab1, tab2, tab3 = st.tabs(
    ["🛒 Satışlar ve Gelir", "💸 İşletme Giderleri", "📈 Finansal Özet ve Vergi"]
)

# --- 1. SEKME: SATIŞLAR VE GELİR ---
with tab1:
  st.header("Satış ve Gelir Kaydı")

  with st.form("satis_formu", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
      musteri = st.text_input("Müşteri Adı Soyadı / Unvanı")
      urun = st.text_input("Satılan Ürün veya Hizmet")
    with col2:
      adet = st.number_input("Adet", min_value=1, value=1, step=1)
      fiyat = st.number_input("Birim Fiyat (TL)", min_value=0.0, format="%.2f")

    tarih = st.date_input("Satış Tarihi")
    submit_satis = st.form_submit_button("Satışı Kaydet")

    if submit_satis:
      if musteri and urun:
        toplam_gelir = adet * fiyat
        cursor.execute(
            "INSERT INTO satislar (musteri_adi, urun_hizmet, adet, birim_fiyat,"
            " toplam_gelir, tarih) VALUES (?, ?, ?, ?, ?, ?)",
            (musteri, urun, adet, fiyat, toplam_gelir, str(tarih)),
        )
        conn.commit()
        st.success(
            f"'{musteri}' adlı müşterinin satışı başarıyla kaydedildi!"
        )
      else:
        st.error("Lütfen müşteri adı ve ürün/hizmet alanlarını doldurun.")

  st.divider()
  st.subheader("Müşteri Satış Geçmişi")
  df_satis = pd.read_sql("SELECT * FROM satislar", conn)
  if not df_satis.empty:
    st.dataframe(df_satis, use_container_width=True)
  else:
    st.info("Henüz kayıtlı satış bulunmuyor.")

# --- 2. SEKME: GİDERLER ---
with tab2:
  st.header("İşletme Giderleri Kaydı")

  with st.form("gider_formu", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
      kategori = st.selectbox(
          "Gider Kategorisi",
          [
              "Yazılım & Sunucu",
              "Ofis Kirası",
              "Pazarlama & Reklam",
              "Muhasebe",
              "Maaşlar",
              "Diğer",
          ],
      )
      aciklama = st.text_input("Açıklama / Tedarikçi")
    with col2:
      tutar = st.number_input("Gider Tutarı (TL)", min_value=0.0, format="%.2f")
      tarih_gider = st.date_input("Gider Tarihi", key="gider_tarih_key")

    submit_gider = st.form_submit_button("Gideri Kaydet")

    if submit_gider:
      if aciklama:
        cursor.execute(
            "INSERT INTO giderler (kategori, aciklama, tutar, tarih) VALUES"
            " (?, ?, ?, ?)",
            (kategori, aciklama, tutar, str(tarih_gider)),
        )
        conn.commit()
        st.success("Gider başarıyla kaydedildi!")
      else:
        st.error("Lütfen gider açıklamasını doldurun.")

  st.divider()
  st.subheader("Gider Listesi")
  df_gider = pd.read_sql("SELECT * FROM giderler", conn)
  if not df_gider.empty:
    st.dataframe(df_gider, use_container_width=True)
  else:
    st.info("Henüz kayıtlı gider bulunmuyor.")

# --- 3. SEKME: ÖZET VE VERGİ ---
with tab3:
  st.header("Finansal Özet ve Vergi Hesaplama Paneli")

  # Veritabanından toplamları çek
  df_s = pd.read_sql(
      "SELECT SUM(toplam_gelir) as toplam_gelir FROM satislar", conn
  )
  df_g = pd.read_sql("SELECT SUM(tutar) as toplam_gider FROM giderler", conn)

  toplam_gelir = (
      df_s["toplam_gelir"].iloc[0]
      if df_s["toplam_gelir"].iloc[0] is not None
      else 0.0
  )
  toplam_gider = (
      df_g["toplam_gider"].iloc[0]
      if df_g["toplam_gider"].iloc[0] is not None
      else 0.0
  )
  net_kar_oncesi = toplam_gelir - toplam_gider

  # Vergi Oranı Ayarı
  vergi_orani = (
      st.slider(
          "Vergi Oranı (%) Belirleyin",
          min_value=0,
          max_value=50,
          value=20,
          step=1,
      )
      / 100.0
  )

  hesaplanan_vergi = net_kar_oncesi * vergi_orani if net_kar_oncesi > 0 else 0.0
  net_kar_sonrasi = net_kar_oncesi - hesaplanan_vergi

  # Metrik Kartları
  col1, col2, col3 = st.columns(3)
  col1.metric("Toplam Brüt Gelir", f"{toplam_gelir:,.2f} ₺")
  col2.metric("Toplam Giderler", f"{toplam_gider:,.2f} ₺")
  col3.metric("Vergi Öncesi Net Kâr", f"{net_kar_oncesi:,.2f} ₺")

  st.divider()

  col4, col5 = st.columns(2)
  col4.metric(
      f"Hesaplanan Vergi (%{int(vergi_orani*100)})",
      f"{hesaplanan_vergi:,.2f} ₺",
  )
  col5.metric("Vergi Sonrası Net Kâr", f"{net_kar_sonrasi:,.2f} ₺")
