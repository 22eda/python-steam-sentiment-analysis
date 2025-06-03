from flask import Flask, render_template, request, jsonify, send_file
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
import warnings
import io
import base64
import json
import os
from werkzeug.utils import secure_filename
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os
app = Flask(__name__)
# Dosya yolunu dinamik olarak belirle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE_PATH = os.path.join(BASE_DIR, "steam_analiz.xlsx")

# Debug bilgileri
print(f"Çalışma dizini: {os.getcwd()}")
print(f"Script dizini: {BASE_DIR}")
print(f"Excel dosya yolu: {EXCEL_FILE_PATH}")
print(f"Excel dosyası mevcut mu: {os.path.exists(EXCEL_FILE_PATH)}")

# Dizindeki dosyaları listele
try:
    files = os.listdir(BASE_DIR)
    print(f"Dizindeki dosyalar: {files}")
except Exception as e:
    print(f"Dosya listesi alınamadı: {e}")

# Custom JSON Encoder - NumPy ve Pandas tiplerini handle eder
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif hasattr(obj, 'item'):  # NumPy scalar
            return obj.item()
        elif str(type(obj)) == "<class 'Undefined'>" or obj is None:
            return None
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

# Flask app'e custom encoder'ı ekle
app.json_encoder = CustomJSONEncoder

def safe_convert_to_serializable(obj):
    """Nesneyi JSON serializable hale getir"""
    if isinstance(obj, dict):
        return {k: safe_convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_convert_to_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(safe_convert_to_serializable(item) for item in obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif hasattr(obj, 'item'):  # NumPy scalar
        return obj.item()
    elif pd.isna(obj):
        return None
    else:
        return obj

# NLTK verilerini indir
def download_nltk_data():
    """NLTK verilerini indir"""
    nltk_downloads = [
        'punkt', 'punkt_tab', 'stopwords', 'wordnet', 'omw-1.4', 'averaged_perceptron_tagger'
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
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        try:
            tokens = word_tokenize(text)
        except:
            tokens = text.split()
        
        processed_tokens = []
        for token in tokens:
            if (token not in self.stop_words and 
                len(token) > 2 and 
                token.isalpha()):
                try:
                    lemmatized = self.lemmatizer.lemmatize(token)
                    processed_tokens.append(lemmatized)
                except:
                    processed_tokens.append(token)
        
        return ' '.join(processed_tokens)
    
    def get_word_frequency(self, texts, top_n=50):
        all_words = []
        for text in texts:
            if not isinstance(text, str):
                text = str(text) if not pd.isna(text) else ""
            words = text.split()
            all_words.extend(words)
        
        word_freq = Counter(all_words)
        return word_freq.most_common(top_n)

    def analyze_sentiment_textblob(self, text):
        """TextBlob ile duygu analizi"""
        if pd.isna(text) or text == '':
            return {'polarity': 0.0, 'subjectivity': 0.0, 'sentiment': 'neutral'}
        
        blob = TextBlob(str(text))
        polarity = float(blob.sentiment.polarity)
        subjectivity = float(blob.sentiment.subjectivity)
        
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
            return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0, 'sentiment': 'neutral'}
        
        scores = self.vader_analyzer.polarity_scores(str(text))
        
        # Skorları float'a çevir
        scores = {k: float(v) for k, v in scores.items()}
        
        if scores['compound'] >= 0.05:
            sentiment = 'positive'
        elif scores['compound'] <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        scores['sentiment'] = sentiment
        return scores
    
    def create_wordcloud_base64(self, text_data, title="Word Cloud"):
        """Kelime bulutu oluştur ve base64 string döndür"""
        if not text_data:
            return None
        
        all_text = ' '.join([str(text) for text in text_data if str(text).strip()])
        
        if not all_text.strip():
            return None
        
        wordcloud = WordCloud(
            width=800, height=400,
            background_color='white',
            max_words=100,
            colormap='viridis'
        ).generate(all_text)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(title, fontsize=14, fontweight='bold')
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return plot_url
    
    def create_sentiment_charts_base64(self, df):
        """Duygu analizi grafiklerini oluştur ve base64 döndür"""
        charts = {}
        
        # TextBlob Sentiment Distribution
        plt.figure(figsize=(8, 6))
        sentiment_counts = df['textblob_sentiment'].value_counts()
        colors = ['#2ecc71', '#e74c3c', '#95a5a6']  # green, red, gray
        plt.pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%', colors=colors)
        plt.title('TextBlob Duygu Dağılımı')
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
        img.seek(0)
        charts['textblob_pie'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        # VADER Sentiment Distribution
        plt.figure(figsize=(8, 6))
        vader_counts = df['vader_sentiment'].value_counts()
        plt.pie(vader_counts.values, labels=vader_counts.index, autopct='%1.1f%%', colors=colors)
        plt.title('VADER Duygu Dağılımı')
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
        img.seek(0)
        charts['vader_pie'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        # Polarity Distribution
        plt.figure(figsize=(10, 6))
        plt.hist(df['textblob_polarity'], bins=30, alpha=0.7, color='blue', edgecolor='black')
        plt.title('TextBlob Polarity Dağılımı')
        plt.xlabel('Polarity')
        plt.ylabel('Frekans')
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
        img.seek(0)
        charts['polarity_hist'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return charts
    
    def create_word_frequency_chart_base64(self, word_freq, title="En Sık Kullanılan Kelimeler", top_n=15):
        """Kelime frekansı grafiği oluştur ve base64 döndür"""
        if not word_freq:
            return None
        
        words, counts = zip(*word_freq[:top_n])
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(range(len(words)), counts, color='steelblue')
        plt.yticks(range(len(words)), words)
        plt.xlabel('Frekans')
        plt.title(title)
        plt.gca().invert_yaxis()
        
        for i, bar in enumerate(bars):
            plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    str(counts[i]), va='center')
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return plot_url
    
    def create_game_stats_chart_base64(self, df):
        """En çok oynanan oyunlar grafiği oluştur"""
        if 'oyun_adi' not in df.columns:
            return None
        
        game_counts = df['oyun_adi'].value_counts().head(10)
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(range(len(game_counts)), game_counts.values, color='#3498db')
        plt.yticks(range(len(game_counts)), game_counts.index)
        plt.xlabel('Yorum Sayısı')
        plt.title('En Çok Yorumu Olan Oyunlar')
        plt.gca().invert_yaxis()
        
        for i, bar in enumerate(bars):
            plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    str(game_counts.values[i]), va='center')
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return plot_url
    
    def analyze_reviews_web(self, df, text_column='yorum_metni_temiz', selected_game=None):
        """Web için ana analiz fonksiyonu - oyun filtresi eklendi"""
        results = {}
        
        # Oyun filtresi uygula
        if selected_game and selected_game != 'all' and 'oyun_adi' in df.columns:
            df_filtered = df[df['oyun_adi'] == selected_game].copy()
            results['selected_game'] = selected_game
        else:
            df_filtered = df.copy()
            results['selected_game'] = 'all'
        
        if len(df_filtered) == 0:
            return {'error': 'Seçilen oyun için yorum bulunamadı'}
        
        # Mevcut sütunları kontrol et
        if 'processed_text' not in df_filtered.columns:
            df_filtered['processed_text'] = df_filtered[text_column].apply(self.preprocess_text)
        
        if 'textblob_sentiment' not in df_filtered.columns:
            textblob_results = df_filtered[text_column].apply(self.analyze_sentiment_textblob)
            df_filtered['textblob_polarity'] = [float(r['polarity']) for r in textblob_results]
            df_filtered['textblob_subjectivity'] = [float(r['subjectivity']) for r in textblob_results]
            df_filtered['textblob_sentiment'] = [r['sentiment'] for r in textblob_results]
        
        if 'vader_sentiment' not in df_filtered.columns:
            vader_results = df_filtered[text_column].apply(self.analyze_sentiment_vader)
            df_filtered['vader_compound'] = [float(r['compound']) for r in vader_results]
            df_filtered['vader_pos'] = [float(r['pos']) for r in vader_results]
            df_filtered['vader_neu'] = [float(r['neu']) for r in vader_results]
            df_filtered['vader_neg'] = [float(r['neg']) for r in vader_results]
            df_filtered['vader_sentiment'] = [r['sentiment'] for r in vader_results]
        
        # Temel istatistikler - safe conversion ile
        results['total_reviews'] = int(len(df_filtered))
        results['textblob_stats'] = safe_convert_to_serializable(df_filtered['textblob_sentiment'].value_counts().to_dict())
        results['vader_stats'] = safe_convert_to_serializable(df_filtered['vader_sentiment'].value_counts().to_dict())
        
        # Steam tavsiyesi karşılaştırması
        if 'begenildi_mi' in df_filtered.columns:
            steam_positive = int(df_filtered['begenildi_mi'].sum())
            results['steam_stats'] = {
                'positive': steam_positive,
                'negative': int(len(df_filtered) - steam_positive)
            }
        
        # Ortalama değerler - NaN kontrolü ile
        avg_polarity = df_filtered['textblob_polarity'].mean()
        avg_compound = df_filtered['vader_compound'].mean()
        
        results['avg_polarity'] = float(avg_polarity) if not pd.isna(avg_polarity) else 0.0
        results['avg_compound'] = float(avg_compound) if not pd.isna(avg_compound) else 0.0
        
        # Kelime frekansı
        all_word_freq = self.get_word_frequency(df_filtered['processed_text'].tolist())
        positive_texts = df_filtered[df_filtered['textblob_sentiment'] == 'positive']['processed_text'].tolist()
        negative_texts = df_filtered[df_filtered['textblob_sentiment'] == 'negative']['processed_text'].tolist()
        
        positive_word_freq = self.get_word_frequency(positive_texts)
        negative_word_freq = self.get_word_frequency(negative_texts)
        
        # Grafikler
        results['charts'] = self.create_sentiment_charts_base64(df_filtered)
        results['word_freq_chart'] = self.create_word_frequency_chart_base64(all_word_freq)
        results['positive_word_chart'] = self.create_word_frequency_chart_base64(positive_word_freq, "Pozitif Yorumlarda En Sık Kelimeler")
        results['negative_word_chart'] = self.create_word_frequency_chart_base64(negative_word_freq, "Negatif Yorumlarda En Sık Kelimeler")
        
        # En çok oynanan oyunlar grafiği (sadece tüm oyunlar seçiliyse)
        if selected_game == 'all' or selected_game is None:
            results['game_stats_chart'] = self.create_game_stats_chart_base64(df)
        
        # Kelime bulutları
        results['wordcloud_general'] = self.create_wordcloud_base64(df_filtered['processed_text'].tolist(), "Genel Kelime Bulutu")
        results['wordcloud_positive'] = self.create_wordcloud_base64(positive_texts, "Pozitif Yorumlar")
        results['wordcloud_negative'] = self.create_wordcloud_base64(negative_texts, "Negatif Yorumlar")
        
        # En sık kullanılan kelimeler - safe conversion ile
        results['top_words'] = {
            'general': safe_convert_to_serializable(all_word_freq[:10]),
            'positive': safe_convert_to_serializable(positive_word_freq[:10]),
            'negative': safe_convert_to_serializable(negative_word_freq[:10])
        }
        
        return results

# Global analyzer instance
analyzer = SteamSentimentAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze_data')
def analyze_data():
    try:
        # Excel dosyasını oku
        if not os.path.exists(EXCEL_FILE_PATH):
            return jsonify({'error': f'Excel dosyası bulunamadı: {EXCEL_FILE_PATH}'}), 404
        
        df = pd.read_excel(EXCEL_FILE_PATH)
        
        # Gerekli sütunları kontrol et
        required_columns = ['yorum_metni_temiz']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'Gerekli sütunlar bulunamadı. yorum_metni_temiz sütunu gerekli.'}), 400
        
        # URL parametrelerinden seçilen oyunu al
        selected_game = request.args.get('game', 'all')
        
        # Analiz yap
        results = analyzer.analyze_reviews_web(df, selected_game=selected_game)
        
        # Hata kontrolü
        if 'error' in results:
            return jsonify(results), 400
        
        # Sonuçları safe conversion ile temizle
        results = safe_convert_to_serializable(results)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': f'Analiz hatası: {str(e)}'}), 500

@app.route('/get_data_info')
def get_data_info():
    """Veri hakkında temel bilgileri döndür"""
    try:
        if not os.path.exists(EXCEL_FILE_PATH):
            return jsonify({'error': f'Excel dosyası bulunamadı: {EXCEL_FILE_PATH}'}), 404
        
        df = pd.read_excel(EXCEL_FILE_PATH)
        
        info = {
            'total_reviews': int(len(df)),
            'columns': list(df.columns),
            'file_path': EXCEL_FILE_PATH,
            'file_exists': True
        }
        
        # Oyun adları varsa
        if 'oyun_adi' in df.columns:
            info['unique_games'] = int(df['oyun_adi'].nunique())
            # Tüm oyunları listele (sadece ilk 50'sini değil)
            all_games = df['oyun_adi'].value_counts().to_dict()
            info['all_games'] = safe_convert_to_serializable(all_games)
            info['top_games'] = safe_convert_to_serializable(df['oyun_adi'].value_counts().head(10).to_dict())
        
        # Beğeni bilgisi varsa
        if 'begenildi_mi' in df.columns:
            info['positive_reviews'] = int(df['begenildi_mi'].sum())
            info['negative_reviews'] = int(len(df) - df['begenildi_mi'].sum())
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({'error': f'Veri okuma hatası: {str(e)}'}), 500

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text.strip():
            return jsonify({'error': 'Metin boş olamaz'}), 400
        
        # Tek metin analizi
        textblob_result = analyzer.analyze_sentiment_textblob(text)
        vader_result = analyzer.analyze_sentiment_vader(text)
        processed_text = analyzer.preprocess_text(text)
        
        result = {
            'original_text': text,
            'processed_text': processed_text,
            'textblob': safe_convert_to_serializable(textblob_result),
            'vader': safe_convert_to_serializable(vader_result)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Metin analizi hatası: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)

    # Flask uygulamanızın sonuna ekleyin

if __name__ == '__main__':
    # Public access için gerekli ayarlar
    import os
    
    # Port'u environment variable'dan al (Render, Heroku vs için)
    port = int(os.environ.get('PORT', 5000))
    
    # Debug mode'u sadece local'de açık tutun
    debug_mode = os.environ.get('ENVIRONMENT', 'development') == 'development'
    
    # Public erişim için host='0.0.0.0' şart
    app.run(
        host='0.0.0.0',  # Tüm network interface'lerinde dinle
        port=port,
        debug=debug_mode,
        threaded=True  # Çoklu istek desteği
    )

# Güvenlik için CORS ayarları (gerekirse)
from flask_cors import CORS

# Tüm origin'lere izin ver (sadece development için)
if os.environ.get('ENVIRONMENT') == 'development':
    CORS(app, origins='*')
else:
    # Production'da sadece belirli domain'lere izin ver
    CORS(app, origins=['https://yourdomain.com'])

# Rate limiting ekleyin (opsiyonel)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Önemli route'lara rate limit ekleyin
@app.route('/analyze_data')
@limiter.limit("5 per minute")  # Dakikada 5 analiz
def analyze_data():
    # Mevcut kodunuz...
    pass

limiter.init_app(app)
