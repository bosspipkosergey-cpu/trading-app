import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from deep_translator import GoogleTranslator
import streamlit.components.v1 as components # 👈 ИМПОРТИРУЕМ КОМПОНЕНТ ДЛЯ HTML

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Crypto & Gold Analyst", page_icon="📈", layout="centered")

# --- ФУНКЦИЯ АНАЛИЗА (Ваша оригинальная логика) ---
def analyze(symbol):
    try:
        # Корректировка тикеров для удобства
        if symbol == "GOLD": symbol = "GC=F"
        if symbol == "EURUSD": symbol = "EURUSD=X"
        if symbol == "GBPUSD": symbol = "GBPUSD=X"
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        
        if df.empty:
            return None
            
        # Считаем индикаторы
        df.ta.rsi(length=14, append=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        
        current = df.iloc[-1]
        
        # Логика тренда
        price = current['Close']
        sma20 = current['SMA_20']
        sma50 = current['SMA_50']
        
        trend = "➡️ БОКОВИК"
        if price > sma20 and price > sma50:
            trend = "🚀 ВОСХОДЯЩИЙ"
        elif price < sma20 and price < sma50:
            trend = "🐻 НИСХОДЯЩИЙ"
            
        # Новости (с защитой от ошибок Yahoo)
        news_list = []
        try:
            if ticker.news:
                translator = GoogleTranslator(source='auto', target='ru')
                
                for n in ticker.news[:3]:
                    title = n.get('content', {}).get('title') or n.get('title')
                    if title:
                        translated_title = translator.translate(title)
                        news_list.append(translated_title)
            
            if not news_list:
                news_list = ["Свежих новостей по активу не найдено."]
        except Exception as e:
            news_list = ["Новости временно недоступны (ошибка источника)."]
                
        return {
            "symbol": symbol,
            "price": price,
            "rsi": current['RSI_14'],
            "trend": trend,
            "news": news_list
        }
    except Exception as e:
        return None

# --- БОКОВОЕ МЕНЮ (НАВИГАЦИЯ) ---
st.sidebar.title("Меню инструментов")
page = st.sidebar.radio(
    "Выберите приложение:", 
    ["Карманный Аналитик", "Математический предсказатель"]
)

# --- МАРШРУТИЗАЦИЯ СТРАНИЦ ---

if page == "Карманный Аналитик":
    # === ВАШЕ ОРИГИНАЛЬНОЕ ПРИЛОЖЕНИЕ ===
    st.title("🤖 Карманный Аналитик")
    st.write("Введите тикер (например: BTC-USD, GOLD, EURUSD)")

    symbol = st.text_input("Тикер актива:", value="GBPUSD=X").upper()

    if st.button("АНАЛИЗИРОВАТЬ 🔥"):
        with st.spinner('Сканирую рынок и перевожу новости...'):
            data = analyze(symbol)
            
            if data:
                st.metric(label="Цена", value=f"${data['price']:.4f}")
                
                rsi = data['rsi']
                if rsi > 70: 
                    st.error(f"RSI: {rsi:.1f} (ПЕРЕГРЕВ!)")
                elif rsi < 30:
                    st.success(f"RSI: {rsi:.1f} (ПЕРЕПРОДАН - СКИДКИ!)")
                else:
                    st.info(f"RSI: {rsi:.1f} (Норма)")
                    
                st.write(f"**Тренд:** {data['trend']}")
                
                st.subheader("📰 Новости:")
                for n in data['news']:
                    st.write(f"- {n}")
                    
                st.divider()
                st.subheader("💡 Скопируй в ИИ:")
                
                news_str = "; ".join(data['news'])
                prompt = f"Анализ {data['symbol']}. Цена: {data['price']:.4f}. RSI: {data['rsi']:.1f}. Тренд: {data['trend']}. Новости: {news_str}. Дай прогноз."
                st.code(prompt, language="text")
                
            else:
                st.error("Ошибка! Проверь тикер или интернет.")

elif page == "Математический предсказатель":
    # === НОВОЕ ПРИЛОЖЕНИЕ С ГРАФИКОМ ===
    st.title("📈 Математический предсказатель")
    st.write("Загрузите историю котировок (CSV) для расчета математического тренда.")
    
    try:
        # Читаем HTML файл, который должен лежать в той же папке
        with open("predictor.html", "r", encoding="utf-8") as f:
            html_data = f.read()
            
        # Встраиваем HTML в интерфейс Streamlit
        components.html(html_data, height=850, scrolling=True)
    except FileNotFoundError:
        st.error("⚠️ Файл `predictor.html` не найден! Убедитесь, что вы загрузили его в ваш репозиторий на GitHub (в ту же папку, где лежит app.py).")
