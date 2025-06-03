W

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