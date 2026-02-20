import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Crypto & Gold Analyst", page_icon="📈", layout="centered")

# --- ФУНКЦИЯ АНАЛИЗА ---
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
                for n in ticker.news[:3]:
                    # Ищем заголовок в новом формате (content) или откатываемся к старому (title)
                    title = n.get('content', {}).get('title') or n.get('title')
                    if title:
                        news_list.append(title)
            
            # Если новости так и не нашлись, но список пуст
            if not news_list:
                news_list = ["Свежих новостей по активу не найдено."]
        except Exception:
            # Защита от непредвиденных изменений API или блокировок
            news_list = ["Новости временно недоступны (ошибка источника)."]
                
        return {
            "symbol": symbol,
            "price": price,
            "rsi": current['RSI_14'],
            "trend": trend,
            "news": news_list
        }
    except Exception as e:
        # Общая ошибка анализа
        return None

# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---
st.title("🤖 Карманный Аналитик")
st.write("Введите тикер (например: BTC-USD, GOLD, EURUSD)")

symbol = st.text_input("Тикер актива:", value="GBPUSD=X").upper()

if st.button("АНАЛИЗИРОВАТЬ 🔥"):
    with st.spinner('Сканирую рынок...'):
        data = analyze(symbol)
        
        if data:
            # Красивые метрики
            st.metric(label="Цена", value=f"${data['price']:.4f}")
            
            # Цветной RSI
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
            
            # Формируем красивую строку с новостями для промпта
            news_str = "; ".join(data['news'])
            prompt = f"Анализ {data['symbol']}. Цена: {data['price']:.4f}. RSI: {data['rsi']:.1f}. Тренд: {data['trend']}. Новости: {news_str}. Дай прогноз."
            st.code(prompt, language="text")
            
        else:
            st.error("Ошибка! Проверь тикер или интернет.")
