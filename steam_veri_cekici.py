

import requests
import pandas as pd
import time
from datetime import datetime
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

class SteamVeriCekici:
    def __init__(self):
        self.base_url = "https://store.steampowered.com/appreviews/"
        self.search_url = "https://store.steampowered.com/api/storesearch/"

        # Oyun listesi ve Steam App ID'leri
        self.oyun_listesi = {
            'The Last of Us Part I': 1888930,
            'Red Dead Redemption 2': 1174180,
            'Elden Ring': 1245620,
            'Cyberpunk 2077': 1091500,
            "Baldur's Gate 3": 1086940,
            'Hogwarts Legacy': 990080,
            'Stardew Valley': 413150,
            'The Witcher 3: Wild Hunt': 292030,
            'Detroit: Become Human': 1222140,
            "Marvel's Spider-Man": 1817070,
            'Hades': 1145360,
            'Resident Evil 4': 2050650,
            'Grand Theft Auto V': 271590,
            'The Sims 4': 1222670,
            'Counter-Strike 2': 730,
            'Dota 2': 570,
            'PUBG: BATTLEGROUNDS': 578080,
            'eFootball 2024': 1665460,
            'Battlefield 2042': 1517290,
            'Fallout 4': 377160,
            'Valheim':892970,
            'NBA 2K24': 2338770,
            'Gotham Knights': 1496790,
            'Call of Duty': 2519060,
            "Assassin’s Creed Odyssey": 812140,
            'It Takes Two': 1426210,
            'Divinity: Original Sin 2': 435150,
            'Path of Exile': 238960,
            'ARK: Survival Evolved': 346110,
            'Sekiro™: Shadows Die Twice': 814380,
        }

    def oyun_id_bul(self, oyun_adi):
        """Oyun adından Steam App ID bulma (eğer listede yoksa)"""
        params = {
            'term': oyun_adi,
            'l': 'english',
            'cc': 'US'
        }

        try:
            response = requests.get(self.search_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    return data['items'][0]['id']
        except Exception as e:
            print(f"Oyun arama hatası: {e}")

        return None

    def yorumlari_cek(self, app_id, oyun_adi, hedef_yorum_sayisi=1000):
        """Belirli bir oyunun yorumlarını Steam API'den çek - Hedef sayıya ulaşana kadar"""
        print(f"📥 {oyun_adi} için {hedef_yorum_sayisi} yorum çekiliyor... (App ID: {app_id})")

        tum_yorumlar = []
        cursor = "*"
        sayfa = 0
        max_sayfa = 100  # Güvenlik için maksimum sayfa limiti

        while len(tum_yorumlar) < hedef_yorum_sayisi and sayfa < max_sayfa:
            url = f"{self.base_url}{app_id}"

            # Steam API parametreleri - daha fazla veri için optimize edildi
            params = {
                'json': 1,
                'filter': 'all',        # Tüm yorumlar (recent, helpful, funny, all)
                'language': 'all',      # Tüm diller
                'day_range': 9999,      # Tüm zamanlar (maksimum değer)
                'cursor': cursor,
                'review_type': 'all',   # Tüm yorum türleri
                'purchase_type': 'all', # Tüm satın alma türleri
                'num_per_page': 20      # Steam'in maksimum değeri
            }

            try:
                response = requests.get(url, params=params, timeout=15)

                if response.status_code == 200:
                    data = response.json()

                    if not data.get('success', False):
                        print(f"❌ API hatası: {data.get('error', 'Bilinmeyen hata')}")
                        break

                    reviews = data.get('reviews', [])
                    if not reviews:
                        print(f"⚠️ {oyun_adi} - Sayfa {sayfa + 1}: Daha fazla yorum bulunamadı")
                        break

                    # Yeni cursor değeri al
                    yeni_cursor = data.get('cursor')
                    if yeni_cursor == cursor or not yeni_cursor:
                        print(f"⚠️ {oyun_adi} - Cursor değişmedi, sonlandırılıyor")
                        break

                    sayfa_yorum_sayisi = 0
                    for review in reviews:
                        try:
                            # Hedef sayıya ulaştıysak dur
                            if len(tum_yorumlar) >= hedef_yorum_sayisi:
                                break

                            yorum_data = {
                                'oyun_adi': oyun_adi,
                                'yorum_metni': review.get('review', '').strip(),
                                'begenildi_mi': review.get('voted_up', True),
                                'oyun_saati': review.get('author', {}).get('playtime_forever', 0),
                                'tarih': datetime.fromtimestamp(review.get('timestamp_created', 0)),
                                'yardimci_oy': review.get('votes_helpful', 0),
                                'komik_oy': review.get('votes_funny', 0),
                                'app_id': app_id,
                                'review_id': review.get('recommendationid', ''),
                                'dil': review.get('language', 'english'),
                                'yazar_oyun_sayisi': review.get('author', {}).get('num_games_owned', 0),
                                'yazar_yorum_sayisi': review.get('author', {}).get('num_reviews', 0)
                            }

                            # Boş ve çok kısa yorumları filtrele
                            if len(yorum_data['yorum_metni']) > 5:
                                tum_yorumlar.append(yorum_data)
                                sayfa_yorum_sayisi += 1

                        except Exception as e:
                            print(f"Yorum işleme hatası: {e}")
                            continue

                    cursor = yeni_cursor
                    sayfa += 1

                    print(f"✅ {oyun_adi} - Sayfa {sayfa}: {sayfa_yorum_sayisi} yorum çekildi "
                          f"(Toplam: {len(tum_yorumlar)}/{hedef_yorum_sayisi})")

                    # Hedef sayıya ulaştıysak döngüyü kır
                    if len(tum_yorumlar) >= hedef_yorum_sayisi:
                        print(f"🎯 {oyun_adi} - Hedef sayıya ulaşıldı: {len(tum_yorumlar)} yorum")
                        break

                else:
                    print(f"❌ HTTP Hatası {response.status_code}")
                    if response.status_code == 429:  # Too Many Requests
                        print("⏳ Rate limit aşıldı, 10 saniye bekleniyor...")
                        time.sleep(10)
                    break

                # Rate limiting - Steam'i yormamak için
                time.sleep(1.2)  # Biraz daha hızlı ama güvenli

            except requests.exceptions.Timeout:
                print(f"⏰ Timeout hatası, 5 saniye bekleyip tekrar denenecek...")
                time.sleep(5)
                continue
            except requests.exceptions.RequestException as e:
                print(f"❌ İstek hatası: {e}")
                time.sleep(5)
                break
            except Exception as e:
                print(f"❌ Genel hata: {e}")
                break

        # Duplikatları kaldır (aynı review_id)
        onceki_sayfa = len(tum_yorumlar)
        unique_yorumlar = []
        gorulmus_idler = set()

        for yorum in tum_yorumlar:
            review_id = yorum.get('review_id', '')
            if review_id and review_id not in gorulmus_idler:
                unique_yorumlar.append(yorum)
                gorulmus_idler.add(review_id)
            elif not review_id:
                # ID yoksa yorum metnini kontrol et
                yorum_hash = hash(yorum['yorum_metni'] + yorum['oyun_adi'])
                if yorum_hash not in gorulmus_idler:
                    unique_yorumlar.append(yorum)
                    gorulmus_idler.add(yorum_hash)

        if len(unique_yorumlar) < onceki_sayfa:
            print(f"🔄 {onceki_sayfa - len(unique_yorumlar)} duplikat yorum kaldırıldı")

        # Hedef sayıdan fazla varsa kısalt
        if len(unique_yorumlar) > hedef_yorum_sayisi:
            unique_yorumlar = unique_yorumlar[:hedef_yorum_sayisi]

        print(f"🎯 {oyun_adi} son durum: {len(unique_yorumlar)} yorum (Hedef: {hedef_yorum_sayisi})")
        return unique_yorumlar

    def tum_oyunlari_cek(self, kaydet=True, oyun_basi_yorum=1000):
        """Tüm oyunların yorumlarını çek - Her oyundan belirli sayıda"""
        print(f"🎮 Steam oyun yorumları çekme işlemi başlıyor... (Oyun başı {oyun_basi_yorum} yorum)")
        print("=" * 80)

        tum_veriler = []
        basarili_oyunlar = []
        basarisiz_oyunlar = []
        toplam_oyun = len(self.oyun_listesi)
        mevcut_oyun = 0

        for oyun_adi, app_id in self.oyun_listesi.items():
            mevcut_oyun += 1
            print(f"\n🎯 İşleniyor: {oyun_adi} ({mevcut_oyun}/{toplam_oyun})")
            print("-" * 50)

            try:
                yorumlar = self.yorumlari_cek(app_id, oyun_adi, hedef_yorum_sayisi=oyun_basi_yorum)

                if yorumlar:
                    tum_veriler.extend(yorumlar)
                    basarili_oyunlar.append(f"{oyun_adi}: {len(yorumlar)} yorum")

                    # Her oyun sonrası ara kayıt
                    if kaydet:
                        temp_df = pd.DataFrame(yorumlar)
                        temp_filename = f"temp_{oyun_adi.replace(':', '').replace(' ', '_').replace(chr(39), '')}.xlsx"
                        temp_df.to_excel(temp_filename, index=False, engine='openpyxl')
                        print(f"💾 Ara kayıt: {temp_filename}")
                else:
                    basarisiz_oyunlar.append(oyun_adi)
                    print(f"❌ {oyun_adi} - Yorum çekilemedi")

                # Oyunlar arası bekleme (Steam'e saygı)
                if mevcut_oyun < toplam_oyun:
                    print("⏳ Sonraki oyun için 5 saniye bekleniyor...")
                    time.sleep(5)

            except Exception as e:
                print(f"❌ {oyun_adi} kritik hatası: {e}")
                basarisiz_oyunlar.append(f"{oyun_adi}: {str(e)}")
                continue

        # Sonuçları DataFrame'e çevir
        if tum_veriler:
            df = pd.DataFrame(tum_veriler)

            # Veri temizleme
            df = self.veri_temizle(df)

            if kaydet:
                # Ana dosyayı kaydet
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                dosya_adi = f"steam_yorumlar_{oyun_basi_yorum}per_game_{timestamp}.xlsx"
                df.to_excel(dosya_adi, index=False, engine='openpyxl')
                print(f"💾 Ana veri kaydedildi: {dosya_adi}")

                # JSON olarak da kaydet
                json_adi = dosya_adi.replace('.xlsx', '.json')
                df.to_json(json_adi, orient='records', date_format='iso', indent=2)
                print(f"💾 JSON kaydedildi: {json_adi}")

                # Temp dosyaları temizle
                try:
                    for file in os.listdir('.'):
                        if file.startswith('temp_') and file.endswith('.xlsx'):
                            os.remove(file)
                    print("🧹 Geçici dosyalar temizlendi")
                except:
                    pass

            # Detaylı özet rapor
            self.ozet_rapor_yazdir(df, basarili_oyunlar, basarisiz_oyunlar, oyun_basi_yorum)

            return df
        else:
            print("❌ Hiç veri çekilemedi!")
            return None

    def ozet_rapor_yazdir(self, df, basarili_oyunlar, basarisiz_oyunlar, hedef_sayi):
        """Detaylı özet rapor yazdır"""
        print("\n" + "=" * 80)
        print("📊 DETAYLI ÖZET RAPOR")
        print("=" * 80)

        print(f"🎯 HEDEF: Her oyundan {hedef_sayi} yorum")
        print(f"✅ Başarılı oyunlar ({len(basarili_oyunlar)}):")
        for oyun in basarili_oyunlar:
            print(f"   • {oyun}")

        if basarisiz_oyunlar:
            print(f"\n❌ Başarısız oyunlar ({len(basarisiz_oyunlar)}):")
            for oyun in basarisiz_oyunlar:
                print(f"   • {oyun}")

        # Oyun bazlı istatistikler
        oyun_stats = df.groupby('oyun_adi').agg({
            'yorum_metni': 'count',
            'begenildi_mi': ['mean', 'sum'],
            'oyun_saati_saat': 'mean',
            'yorum_uzunlugu': 'mean',
            'yardimci_oy': 'mean'
        }).round(2)

        print(f"\n📈 OYUN BAZLI İSTATİSTİKLER:")
        print("-" * 80)
        for oyun in oyun_stats.index:
            stats = oyun_stats.loc[oyun]
            yorum_sayisi = int(stats[('yorum_metni', 'count')])
            pozitif_oran = stats[('begenildi_mi', 'mean')] * 100
            ortalama_saat = stats[('oyun_saati_saat', 'mean')]

            print(f"🎮 {oyun}")
            print(f"   Yorum sayısı: {yorum_sayisi}")
            print(f"   Pozitif oran: %{pozitif_oran:.1f}")
            print(f"   Ort. oyun süresi: {ortalama_saat:.1f} saat")
            print()

        print("=" * 80)
        print(f"🎯 GENEL TOPLAM:")
        print(f"   • Toplam yorum: {len(df):,}")
        print(f"   • Toplam oyun: {df['oyun_adi'].nunique()}")
        print(f"   • Pozitif yorum: {df['begenildi_mi'].sum():,} (%{df['begenildi_mi'].mean()*100:.1f})")
        print(f"   • Ortalama oyun süresi: {df['oyun_saati_saat'].mean():.1f} saat")
        print(f"   • Ortalama yorum uzunluğu: {df['yorum_uzunlugu'].mean():.0f} karakter")
        print(f"   • Tarih aralığı: {df['tarih'].min()} - {df['tarih'].max()}")
        print(f"   • En çok yorumlanan: {df['oyun_adi'].value_counts().index[0]}")
        print("=" * 80)

    def veri_temizle(self, df):
        """Çekilen veriyi temizle ve standardize et"""
        print("\n🧹 Veriler temizleniyor...")

        # Boş değerleri temizle
        df = df.dropna(subset=['yorum_metni'])
        df = df[df['yorum_metni'].str.len() > 5]

        # Duplikatları kaldır (yorum metni + oyun adı kombinasyonu)
        onceki_boyut = len(df)
        df = df.drop_duplicates(subset=['yorum_metni', 'oyun_adi'])
        print(f"   • {onceki_boyut - len(df)} duplikat kaldırıldı")

        # Veri tiplerini düzelt
        df['oyun_saati'] = pd.to_numeric(df['oyun_saati'], errors='coerce').fillna(0)
        df['yardimci_oy'] = pd.to_numeric(df['yardimci_oy'], errors='coerce').fillna(0)
        df['komik_oy'] = pd.to_numeric(df['komik_oy'], errors='coerce').fillna(0)
        df['yazar_oyun_sayisi'] = pd.to_numeric(df['yazar_oyun_sayisi'], errors='coerce').fillna(0)
        df['yazar_yorum_sayisi'] = pd.to_numeric(df['yazar_yorum_sayisi'], errors='coerce').fillna(0)

        # Tarih sütununu düzelt
        df['tarih'] = pd.to_datetime(df['tarih'], errors='coerce')

        # Yorum uzunluğu sütunu ekle
        df['yorum_uzunlugu'] = df['yorum_metni'].str.len()

        # Oyun saatini saat cinsine çevir (dakikadan)
        df['oyun_saati_saat'] = (df['oyun_saati'] / 60).round(1)

        # Kategorik sütunlar ekle
        df['yorum_uzunluk_kategori'] = pd.cut(df['yorum_uzunlugu'],
                                            bins=[0, 50, 150, 500, float('inf')],
                                            labels=['Kısa', 'Orta', 'Uzun', 'Çok Uzun'])

        df['oyun_deneyim_kategori'] = pd.cut(df['oyun_saati_saat'],
                                           bins=[0, 1, 10, 50, 100, float('inf')],
                                           labels=['Yeni', 'Az', 'Orta', 'Çok', 'Uzman'])

        print(f"✅ Temizlik tamamlandı. Final veri: {len(df)} yorum")
        return df

# Kullanım örneği
if __name__ == "__main__":
    # Veri çekici oluştur
    cekici = SteamVeriCekici()

    # Tüm oyunların verilerini çek - Her oyundan 1000 yorum
    print("🚀 Steam veri çekme işlemi başlatılıyor...")
    print("⚠️  Bu işlem uzun sürebilir (yaklaşık 2-3 saat)")
    print("💡 Her oyundan 1000 yorum hedefleniyor")

    df = cekici.tum_oyunlari_cek(kaydet=True, oyun_basi_yorum=1000)

    if df is not None:
        print("\n🎉 İşlem başarıyla tamamlandı!")
        print(f"📁 Dosyalar oluşturuldu:")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        print(f"   • Excel: steam_yorumlar_1000per_game_{timestamp}.xlsx")
        print(f"   • JSON: steam_yorumlar_1000per_game_{timestamp}.json")

        print(f"\n🏆 BAŞARIYLA TAMAMLANDI!")
        print(f"   • Hedeflenen toplam: {len(cekici.oyun_listesi) * 1000:,} yorum")
        print(f"   • Gerçekleşen toplam: {len(df):,} yorum")
        print(f"   • Başarı oranı: %{(len(df) / (len(cekici.oyun_listesi) * 1000)) * 100:.1f}")
    else:
        print("❌ Veri çekme işlemi başarısız!")



        from google.colab import files
files.download('steam_yorumlar_1000per_game_20250531_2301.xlsx')

import pandas as pd
import numpy as np
import re
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import warnings
warnings.filterwarnings('ignore')

# Dil algılama tutarlılığı için seed ayarla
DetectorFactory.seed = 0

def clean_text(text):
    """Metni temizle ve normalize et"""
    if pd.isna(text) or text == '':
        return ''
    
    # String'e çevir
    text = str(text)
    
    # HTML etiketlerini kaldır
    text = re.sub(r'<[^>]+>', '', text)
    
    # URL'leri kaldır
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Steam emoticon'larını kaldır (:steamhappy:, :steamsad: vs.)
    text = re.sub(r':[a-zA-Z0-9_]+:', '', text)
    
    # Fazla boşlukları tek boşluğa çevir
    text = re.sub(r'\s+', ' ', text)
    
    # Baş ve sondaki boşlukları kaldır
    text = text.strip()
    
    return text

def detect_language(text):
    """Metnin dilini algıla"""
    try:
        if pd.isna(text) or text == '' or len(text.strip()) < 3:
            return 'unknown'
        
        # Temizlenmiş metni kullan
        cleaned_text = clean_text(text)
        if len(cleaned_text.strip()) < 3:
            return 'unknown'
            
        detected_lang = detect(cleaned_text)
        return detected_lang
    except (LangDetectException, Exception):
        return 'unknown'

def process_steam_reviews(file_path, output_path=None):
    """Steam yorumlarını işle ve temizle"""
    
    print("Excel dosyası okunuyor...")
    try:
        df = pd.read_excel( file_path )
    except Exception as e:
        print(f"Dosya okuma hatası: {e}")
        return None
    
    print(f"Toplam veri sayısı: {len(df)}")
    print(f"Sütunlar: {list(df.columns)}")
    
    # Eksik değerleri kontrol et
    print(f"\nEksik değer sayıları:")
    print(df.isnull().sum())
    
    # Yorum metni boş olanları kaldır
    initial_count = len(df)
    df = df.dropna(subset=['yorum_metni'])
    df = df[df['yorum_metni'].str.strip() != '']
    print(f"\nBoş yorumlar çıkarıldıktan sonra: {len(df)} veri ({initial_count - len(df)} veri çıkarıldı)")
    
    # Dil algılama
    print("\nDil algılama yapılıyor...")
    df['detected_language'] = df['yorum_metni'].apply(detect_language)
    
    # Dil dağılımını göster
    print("\nDil dağılımı:")
    print(df['detected_language'].value_counts())
    
    # Sadece İngilizce yorumları filtrele
    english_df = df[df['detected_language'] == 'en'].copy()
    print(f"\nİngilizce yorumlar: {len(english_df)} veri")
    
    # Yorum metinlerini temizle
    print("Metin temizleme yapılıyor...")
    english_df['yorum_metni_temiz'] = english_df['yorum_metni'].apply(clean_text)
    
    # Temizlendikten sonra çok kısa kalan yorumları çıkar (3 kelimeden az)
    english_df['kelime_sayisi'] = english_df['yorum_metni_temiz'].apply(lambda x: len(str(x).split()))
    english_df = english_df[english_df['kelime_sayisi'] >= 3]
    print(f"Kısa yorumlar çıkarıldıktan sonra: {len(english_df)} veri")
    
    # Duplicate yorumları kaldır
    before_dedup = len(english_df)
    english_df = english_df.drop_duplicates(subset=['yorum_metni_temiz'])
    print(f"Duplicate yorumlar çıkarıldıktan sonra: {len(english_df)} veri ({before_dedup - len(english_df)} duplicate çıkarıldı)")
    
    # Veri tiplerini düzenle
    if 'begenildi_mi' in english_df.columns:
        english_df['begenildi_mi'] = english_df['begenildi_mi'].astype(bool)
    
    if 'oyun_saati' in english_df.columns:
        english_df['oyun_saati'] = pd.to_numeric(english_df['oyun_saati'], errors='coerce')
    
    # Tarih sütununu datetime'a çevir
    if 'tarih' in english_df.columns:
        english_df['tarih'] = pd.to_datetime(english_df['tarih'], errors='coerce')
    
    # İstatistikleri göster
    print(f"\n=== TEMİZLENMİŞ VERİ İSTATİSTİKLERİ ===")
    print(f"Toplam İngilizce yorum: {len(english_df)}")
    print(f"Ortalama yorum uzunluğu: {english_df['yorum_uzunlugu'].mean():.1f} karakter")
    print(f"Ortalama kelime sayısı: {english_df['kelime_sayisi'].mean():.1f} kelime")
    
    if 'begenildi_mi' in english_df.columns:
        print(f"Pozitif yorumlar: {english_df['begenildi_mi'].sum()} (%{english_df['begenildi_mi'].mean()*100:.1f})")
        print(f"Negatif yorumlar: {(~english_df['begenildi_mi']).sum()} (%{(~english_df['begenildi_mi']).mean()*100:.1f})")
    
    # Dosyayı kaydet
    if output_path is None:
        output_path = file_path.replace('.xlsx', '_temizlenmis.xlsx')
    
    print(f"\nTemizlenmiş veri kaydediliyor: {output_path}")
    english_df.to_excel(output_path, index=False)
    
    return english_df

# Kullanım örneği
if __name__ == "__main__":
    # Dosya yolunu buraya yazın
    file_path = "a.xlsx"  # Kendi dosya yolunuzu yazın
    
    # Veri temizleme işlemini başlat
    cleaned_df = process_steam_reviews(file_path)
    
    if cleaned_df is not None:
        print("\n=== İŞLEM TAMAMLANDI ===")
        print("Duygu analizi için hazır!")
        
        # Örnek temizlenmiş yorumları göster
        print("\n--- Örnek Temizlenmiş Yorumlar ---")
        for i, row in cleaned_df.head(3).iterrows():
            print(f"\nOyun: {row['oyun_adi']}")
            print(f"Orijinal: {row['yorum_metni'][:100]}...")
            print(f"Temizlenmiş: {row['yorum_metni_temiz'][:100]}...")
            print(f"Beğenildi mi: {row['begenildi_mi']}")

            import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')

# NLTK verilerini indir (ilk çalıştırmada gerekli)
def download_nltk_data():
    """NLTK verilerini indir"""
    nltk_downloads = [
        'punkt',
        'punkt_tab', 
        'stopwords',
        'wordnet',
        'omw-1.4',
        'averaged_perceptron_tagger'
    ]
    
    for item in nltk_downloads:
        try:
            nltk.data.find(f'tokenizers/{item}')
        except LookupError:
            try:
                print(f"İndiriliyor: {item}")
                nltk.download(item, quiet=True)
            except:
                print(f"İndirilemedi: {item} (atlanıyor)")
        except:
            try:
                print(f"İndiriliyor: {item}")
                nltk.download(item, quiet=True)
            except:
                print(f"İndirilemedi: {item} (atlanıyor)")

# NLTK verilerini indir
download_nltk_data()

class SteamSentimentAnalyzer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Gaming-specific stop words ekle
        gaming_stopwords = {'game', 'play', 'playing', 'played', 'steam', 'review', 
                           'recommend', 'good', 'bad', 'like', 'really', 'much', 
                           'would', 'could', 'one', 'get', 'also', 'even', 'still',
                            "fucking","bf","ass","dont","isn","ea","im","fuck","shit",
                        "fallout","aminake","bolas", "ve", "don", "didn", "doesn", 
                        "ll", "elden", "stardew", "spider", "ps", "dlc", "pc","the", 
                        "and", "it","games","played","playing","hours","lot","feels",
                        "gameplay","characters","harry","batman","potter","sims","hades",
                        "witcher","battlefield","left","dota","yeah","lots","times","arkham",
                        "fighting","enjoyed ","runs","de","ive","cant"}
        self.stop_words.update(gaming_stopwords)
    
    def preprocess_text(self, text):
        """Metni ön işleme"""
        if pd.isna(text):
            return ""
        
        text = str(text).lower()
        
        # Özel karakterleri kaldır, sadece harfler ve boşluk bırak
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Basit tokenize et (NLTK bağımlılığını azalt)
        try:
            tokens = word_tokenize(text)
        except:
            # NLTK sorun yaşarsa basit split kullan
            tokens = text.split()
        
        # Stop words ve kısa kelimeleri kaldır, lemmatize et
        processed_tokens = []
        for token in tokens:
            if (token not in self.stop_words and 
                len(token) > 2 and 
                token.isalpha()):
                try:
                    lemmatized = self.lemmatizer.lemmatize(token)
                    processed_tokens.append(lemmatized)
                except:
                    # Lemmatizer sorun yaşarsa orijinal kelimeyi kullan
                    processed_tokens.append(token)
        
        return ' '.join(processed_tokens)
    
    def get_word_frequency(self, texts, top_n=50):
        """Kelime frekansı analizi"""
        all_words = []
        for text in texts:
            if text:
                words = text.split()
                all_words.extend(words)
        
        word_freq = Counter(all_words)
        return word_freq.most_common(top_n)
    
    def analyze_sentiment_textblob(self, text):
        """TextBlob ile duygu analizi"""
        if pd.isna(text) or text == '':
            return {'polarity': 0, 'subjectivity': 0, 'sentiment': 'neutral'}
        
        blob = TextBlob(str(text))
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment
        }
    
    def analyze_sentiment_vader(self, text):
        """VADER ile duygu analizi"""
        if pd.isna(text) or text == '':
            return {'compound': 0, 'pos': 0, 'neu': 1, 'neg': 0, 'sentiment': 'neutral'}
        
        scores = self.vader_analyzer.polarity_scores(str(text))
        
        if scores['compound'] >= 0.05:
            sentiment = 'positive'
        elif scores['compound'] <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        scores['sentiment'] = sentiment
        return scores
    
    def create_wordcloud(self, text_data, title="Word Cloud", figsize=(12, 8)):
        """Kelime bulutu oluştur"""
        if not text_data:
            print("Kelime bulutu için yeterli veri yok")
            return
        
        # Tüm metinleri birleştir
        all_text = ' '.join([str(text) for text in text_data if str(text).strip()])
        
        if not all_text.strip():
            print("Kelime bulutu için yeterli veri yok")
            return
        
        wordcloud = WordCloud(
            width=1200, height=600,
            background_color='white',
            max_words=100,
            colormap='viridis'
        ).generate(all_text)
        
        plt.figure(figsize=figsize)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.show()
    
    def plot_sentiment_distribution(self, df):
        """Duygu dağılımı grafikleri"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # TextBlob Sentiment Distribution
        sentiment_counts = df['textblob_sentiment'].value_counts()
        axes[0, 0].pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%')
        axes[0, 0].set_title('TextBlob Duygu Dağılımı')
        
        # VADER Sentiment Distribution
        vader_counts = df['vader_sentiment'].value_counts()
        axes[0, 1].pie(vader_counts.values, labels=vader_counts.index, autopct='%1.1f%%')
        axes[0, 1].set_title('VADER Duygu Dağılımı')
        
        # Steam Recommendation vs Sentiment
        if 'begenildi_mi' in df.columns:
            recommendation_sentiment = pd.crosstab(df['begenildi_mi'], df['textblob_sentiment'])
            recommendation_sentiment.plot(kind='bar', ax=axes[0, 2])
            axes[0, 2].set_title('Steam Tavsiyesi vs TextBlob Duygu')
            axes[0, 2].set_xlabel('Steam Tavsiyesi')
            axes[0, 2].legend(title='Duygu')
        
        # Polarity Distribution
        axes[1, 0].hist(df['textblob_polarity'], bins=30, alpha=0.7, color='blue')
        axes[1, 0].set_title('TextBlob Polarity Dağılımı')
        axes[1, 0].set_xlabel('Polarity')
        
        # Compound Score Distribution
        axes[1, 1].hist(df['vader_compound'], bins=30, alpha=0.7, color='green')
        axes[1, 1].set_title('VADER Compound Score Dağılımı')
        axes[1, 1].set_xlabel('Compound Score')
        
        # Game Hours vs Sentiment
        if 'oyun_saati' in df.columns:
            df_filtered = df[df['oyun_saati'] < 1000]  # Outlier'ları filtrele
            sentiment_hours = df_filtered.groupby('textblob_sentiment')['oyun_saati'].mean()
            axes[1, 2].bar(sentiment_hours.index, sentiment_hours.values)
            axes[1, 2].set_title('Ortalama Oyun Saati vs Duygu')
            axes[1, 2].set_xlabel('Duygu')
            axes[1, 2].set_ylabel('Ortalama Saat')
        
        plt.tight_layout()
        plt.show()
    
    def plot_word_frequency(self, word_freq, title="En Sık Kullanılan Kelimeler", top_n=20):
        """Kelime frekansı grafiği"""
        if not word_freq:
            print("Kelime frekansı verisi yok")
            return
        
        words, counts = zip(*word_freq[:top_n])
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(range(len(words)), counts)
        plt.yticks(range(len(words)), words)
        plt.xlabel('Frekans')
        plt.title(title)
        plt.gca().invert_yaxis()
        
        # Bar'lara değerleri ekle
        for i, bar in enumerate(bars):
            plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    str(counts[i]), va='center')
        
        plt.tight_layout()
        plt.show()
    
    def analyze_reviews(self, df, text_column='yorum_metni_temiz'):
        """Ana analiz fonksiyonu"""
        print("Duygu analizi başlıyor...")
        
        # Metinleri ön işleme
        print("Metin ön işleme yapılıyor...")
        df['processed_text'] = df[text_column].apply(self.preprocess_text)
        
        # TextBlob analizi
        print("TextBlob duygu analizi yapılıyor...")
        textblob_results = df[text_column].apply(self.analyze_sentiment_textblob)
        df['textblob_polarity'] = [r['polarity'] for r in textblob_results]
        df['textblob_subjectivity'] = [r['subjectivity'] for r in textblob_results]
        df['textblob_sentiment'] = [r['sentiment'] for r in textblob_results]
        
        # VADER analizi
        print("VADER duygu analizi yapılıyor...")
        vader_results = df[text_column].apply(self.analyze_sentiment_vader)
        df['vader_compound'] = [r['compound'] for r in vader_results]
        df['vader_pos'] = [r['pos'] for r in vader_results]
        df['vader_neu'] = [r['neu'] for r in vader_results]
        df['vader_neg'] = [r['neg'] for r in vader_results]
        df['vader_sentiment'] = [r['sentiment'] for r in vader_results]
        
        # Kelime frekansı analizi
        print("Kelime frekansı analizi yapılıyor...")
        
        # Genel kelime frekansı
        all_word_freq = self.get_word_frequency(df['processed_text'].tolist())
        
        # Pozitif yorumlar için kelime frekansı
        positive_texts = df[df['textblob_sentiment'] == 'positive']['processed_text'].tolist()
        positive_word_freq = self.get_word_frequency(positive_texts)
        
        # Negatif yorumlar için kelime frekansı
        negative_texts = df[df['textblob_sentiment'] == 'negative']['processed_text'].tolist()
        negative_word_freq = self.get_word_frequency(negative_texts)
        
        # Sonuçları göster
        print(f"\n=== DUYGU ANALİZİ SONUÇLARI ===")
        print(f"Toplam analiz edilen yorum: {len(df)}")
        
        print("\n--- TextBlob Sonuçları ---")
        textblob_counts = df['textblob_sentiment'].value_counts()
        for sentiment, count in textblob_counts.items():
            print(f"{sentiment.capitalize()}: {count} (%{count/len(df)*100:.1f})")
        
        print("\n--- VADER Sonuçları ---")
        vader_counts = df['vader_sentiment'].value_counts()
        for sentiment, count in vader_counts.items():
            print(f"{sentiment.capitalize()}: {count} (%{count/len(df)*100:.1f})")
        
        # Steam tavsiyesi ile karşılaştır
        if 'begenildi_mi' in df.columns:
            print("\n--- Steam Tavsiyesi vs Analiz Sonuçları ---")
            steam_positive = df['begenildi_mi'].sum()
            steam_negative = len(df) - steam_positive
            print(f"Steam Pozitif Tavsiye: {steam_positive} (%{steam_positive/len(df)*100:.1f})")
            print(f"Steam Negatif Tavsiye: {steam_negative} (%{steam_negative/len(df)*100:.1f})")
        
        # Grafikler
        self.plot_sentiment_distribution(df)
        
        # Kelime frekansı grafikleri
        self.plot_word_frequency(all_word_freq, "Genel En Sık Kullanılan Kelimeler")
        
        if positive_word_freq:
            self.plot_word_frequency(positive_word_freq, "Pozitif Yorumlarda En Sık Kelimeler")
        
        if negative_word_freq:
            self.plot_word_frequency(negative_word_freq, "Negatif Yorumlarda En Sık Kelimeler")
        
        # Kelime bulutları
        print("Kelime bulutları oluşturuluyor...")
        self.create_wordcloud(df['processed_text'].tolist(), "Genel Kelime Bulutu")
        
        if positive_texts:
            self.create_wordcloud(positive_texts, "Pozitif Yorumlar Kelime Bulutu")
        
        if negative_texts:
            self.create_wordcloud(negative_texts, "Negatif Yorumlar Kelime Bulutu")
        
        return df, {
            'all_words': all_word_freq,
            'positive_words': positive_word_freq,
            'negative_words': negative_word_freq
        }

# Ana kullanım fonksiyonu
def main():
    # Temizlenmiş veriyi yükle
    file_path = "a_temizlenmis.xlsx"  # Dosya yolunu buraya yazın
    
    print("Veri yükleniyor...")
    try:
        df = pd.read_excel(file_path)
        print(f"Veri başarıyla yüklendi: {len(df)} yorum")
    except Exception as e:
        print(f"Dosya yükleme hatası: {e}")
        return
    
    # Analyzer'ı başlat
    analyzer = SteamSentimentAnalyzer()
    
    # Analiz yap
    analyzed_df, word_frequencies = analyzer.analyze_reviews(df)
    
    # Sonuçları kaydet
    output_path = file_path.replace('.xlsx', '_analiz_sonuclari.xlsx')
    analyzed_df.to_excel(output_path, index=False)
    print(f"\nAnaliz sonuçları kaydedildi: {output_path}")
    
    # En sık kullanılan kelimeleri yazdır
    print(f"\n=== EN SIK KULLANILAN KELİMELER ===")
    print("Genel:")
    for word, count in word_frequencies['all_words'][:10]:
        print(f"  {word}: {count}")
    
    if word_frequencies['positive_words']:
        print("\nPozitif yorumlarda:")
        for word, count in word_frequencies['positive_words'][:10]:
            print(f"  {word}: {count}")
    
    if word_frequencies['negative_words']:
        print("\nNegatif yorumlarda:")
        for word, count in word_frequencies['negative_words'][:10]:
            print(f"  {word}: {count}")

if __name__ == "__main__":
    main()