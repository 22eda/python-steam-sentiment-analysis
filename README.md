# Steam Yorum Duygu Analizi Web Uygulaması

Steam oyun yorumlarını analiz ederek duygu durumunu belirleyen Flask tabanlı web uygulaması. TextBlob ve VADER sentiment analysis araçlarını kullanarak pozitif, negatif ve nötr yorumları sınıflandırır.

## 🎮 Özellikler

- **Çift Duygu Analizi**: TextBlob ve VADER algoritmalarını kullanarak daha doğru sonuçlar
- **Görsel Raporlama**: Pasta grafikleri ve kelime frekansı grafikleri
- **Oyun Bazlı Filtreleme**: Belirli oyunlar için analiz yapabilme
- **Kelime Bulutu**: En sık kullanılan kelimelerin görselleştirilmesi
- **Gerçek Zamanlı Analiz**: Tek metin girişi için anlık duygu analizi
- **Responsive Tasarım**: Mobil ve masaüstü uyumlu arayüz

## 🛠️ Teknolojiler

- **Backend**: Flask (Python)
- **Duygu Analizi**: TextBlob, VADER Sentiment
- **Veri İşleme**: Pandas, NumPy
- **Görselleştirme**: Matplotlib, WordCloud
- **Doğal Dil İşleme**: NLTK
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Render

## 📋 Gereksinimler

```
Flask==2.3.3
matplotlib==3.7.2
wordcloud==1.9.2
pandas==2.0.3
numpy==1.24.3
nltk==3.8.1
textblob==0.17.1
vaderSentiment==3.3.2
openpyxl==3.1.2
```

## 🚀 Kurulum

1. **Projeyi klonlayın:**
```bash
git clone https://github.com/kullaniciadi/steam-sentiment-analysis.git
cd steam-sentiment-analysis
```

2. **Sanal ortam oluşturun:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

4. **NLTK verilerini indirin:**
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')
```

5. **Excel dosyasını yerleştirin:**
   - `steam_analiz.xlsx` dosyasını proje ana dizinine koyun
   - Dosya `yorum_metni_temiz` sütununu içermelidir

6. **Uygulamayı çalıştırın:**
```bash
python app.py
```

## 📊 Veri Formatı

Excel dosyasının içermesi gereken sütunlar:
- `yorum_metni_temiz`: Temizlenmiş yorum metinleri (zorunlu)
- `oyun_adi`: Oyun adları (opsiyonel, filtreleme için)
- `begenildi_mi`: Beğeni durumu (opsiyonel, istatistikler için)

## 🔧 API Endpoints

- `GET /`: Ana sayfa
- `GET /analyze_data`: Veri analizi (oyun filtresi: `?game=oyun_adi`)
- `POST /analyze_text`: Tek metin analizi
- `GET /get_data_info`: Veri hakkında bilgi
- `GET /health`: Sağlık kontrolü

## 📈 Analiz Sonuçları

### Duygu Sınıflandırması
- **Pozitif**: TextBlob polarity > 0.1 veya VADER compound > 0.05
- **Negatif**: TextBlob polarity < -0.1 veya VADER compound < -0.05
- **Nötr**: Diğer durumlar

### Görselleştirmeler
- Duygu dağılımı pasta grafikleri
- En sık kullanılan kelimeler bar grafikleri
- Pozitif/negatif yorumlarda kelime frekansları

## 🌐 Deployment

### Render.com'da Deployment
1. GitHub'da repo oluşturun
2. Render.com'da yeni web service oluşturun
3. GitHub repo'nuzu bağlayın
4. Build ve start komutlarını ayarlayın:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`

### Environment Variables
```
PORT=5000
RENDER=true
```

## 📝 Kullanım Örnekleri

### Toplu Analiz
```python
# Excel dosyası yüklendikten sonra
# /analyze_data endpoint'ini kullanarak tüm yorumları analiz edin
```

### Tek Metin Analizi
```javascript
fetch('/analyze_text', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: 'Bu oyun gerçekten harika!'})
})
```

## 🎯 Özellik Detayları

### Metin Ön İşleme
- Küçük harfe çevirme
- Noktalama işaretlerini kaldırma
- Stop words filtreleme
- Lemmatization (kök bulma)
- Gaming-specific stop words

### Duygu Analizi Algoritmaları

**TextBlob:**
- Polarity: -1 (negatif) ile +1 (pozitif) arası
- Subjectivity: 0 (objektif) ile 1 (subjektif) arası

**VADER:**
- Compound score: -1 ile +1 arası normalize edilmiş skor
- Sosyal medya metinleri için optimize edilmiş

## 🔍 Örnek Çıktı

```json
{
  "total_reviews": 1500,
  "textblob_stats": {
    "positive": 750,
    "negative": 450,
    "neutral": 300
  },
  "avg_polarity": 0.15,
  "avg_compound": 0.23,
  "top_words": {
    "general": [["fun", 45], ["story", 38], ["graphics", 32]],
    "positive": [["amazing", 25], ["love", 22], ["perfect", 18]],
    "negative": [["boring", 15], ["bugs", 12], ["terrible", 10]]
  }
}
```


## 👨‍💻 Geliştirici

**[Edanur Demirel]**
- GitHub: [@22eda](https://github.com/kullaniciadi)
- LinkedIn: [[LinkedIn Profiliniz](https://www.linkedin.com/in/edanur-demirel-b00644250/)]
- Email:edademirel13@gmail.com

## 🙏 Teşekkürler

- Steam Community (veri kaynağı için)
- NLTK ve TextBlob geliştiricileri
- VADER Sentiment Analysis araştırmacıları


---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
