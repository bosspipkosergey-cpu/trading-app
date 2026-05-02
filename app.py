import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np # 👈 НОВАЯ СТРОКА: Для математических расчетов
import datetime # 👈 НОВАЯ СТРОКА: Для работы со временем
from deep_translator import GoogleTranslator
import streamlit.components.v1 as components

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Crypto & Gold Analyst", page_icon="📈", layout="centered")

# --- ФУНКЦИЯ МАКРО-АНАЛИЗА (YFinance) ---
def analyze_macro(symbol):
    try:
        if symbol == "GOLD": symbol = "GC=F"
        if symbol == "EURUSD": symbol = "EURUSD=X"
        if symbol == "GBPUSD": symbol = "GBPUSD=X"
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        
        if df.empty: return None
            
        df.ta.rsi(length=14, append=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        current = df.iloc[-1]
        
        # Запоминаем дату последней свечи
        last_date = current.name.strftime('%d.%m.%Y')
        
        price = current['Close']
        sma20 = current['SMA_20']
        sma50 = current['SMA_50']
        
        trend = "➡️ БОКОВИК"
        if price > sma20 and price > sma50: trend = "🚀 ВОСХОДЯЩИЙ"
        elif price < sma20 and price < sma50: trend = "🐻 НИСХОДЯЩИЙ"
            
        news_list = []
        try:
            if ticker.news:
                translator = GoogleTranslator(source='auto', target='ru')
                for n in ticker.news[:3]:
                    title = n.get('content', {}).get('title') or n.get('title')
                    
                    # Извлекаем дату и время публикации новости
                    pub_time = n.get('providerPublishTime')
                    time_str = ""
                    if pub_time:
                        dt = datetime.datetime.fromtimestamp(pub_time)
                        time_str = f"[{dt.strftime('%d.%m %H:%M')}] "
                    
                    if title: 
                        translated_title = translator.translate(title)
                        # Добавляем время перед заголовком новости
                        news_list.append(f"{time_str}{translated_title}")
            if not news_list: news_list = ["Свежих новостей нет."]
        except:
            news_list = ["Новости недоступны."]
                
        return {
            "symbol": symbol,
            "date": last_date, # Передаем дату в интерфейс
            "price": price,
            "rsi": current['RSI_14'],
            "trend": trend,
            "news": news_list
        }
    except Exception as e:
        return None

# --- ФУНКЦИЯ МИКРО-АНАЛИЗА (Математика по CSV) ---
def analyze_micro_math(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        
        # Ищем колонку с ценой закрытия
        headers = [str(col).lower() for col in df.columns]
        close_col = df.columns[-1] 
        for i, h in enumerate(headers):
            if 'close' in h or 'закрытие' in h:
                close_col = df.columns[i]
                break
                
        # Очищаем данные от запятых и превращаем в числа
        df[close_col] = pd.to_numeric(df[close_col].astype(str).str.replace(',', '.'), errors='coerce')
        prices = df[close_col].dropna().values
        
        if len(prices) < 2: return None
        
        # Математика: Линейная регрессия (Метод наименьших квадратов)
        x = np.arange(len(prices))
        m, b = np.polyfit(x, prices, 1) # m - наклон, b - смещение
        
        # Создаем линию тренда для графика
        trendline = m * x + b
        chart_df = pd.DataFrame({"Реальная цена": prices, "Мат. Тренд": trendline})
        
        # Предсказание на 10% шагов вперед
        future_x = len(prices) + len(prices)*0.1
        prediction = m * future_x + b
        
        trend_direction = "🚀 РАСТУЩИЙ (Локально)" if m > 0 else "🐻 ПАДАЮЩИЙ (Локально)"
        
        return {
            "m": m,
            "trend": trend_direction,
            "prediction": prediction,
            "chart_data": chart_df,
            "points": len(prices)
        }
    except:
        return None

# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---
st.title("🤖 Карманный Аналитик 2.0 (Синтез)")
st.write("Комплексный анализ: Глобальный тренд (YFinance) + Локальная математика (CSV)")

symbol = st.text_input("Тикер актива:", value="GOLD").upper()
uploaded_csv = st.file_uploader("Прикрепить график торговой сессии (CSV) для мат. прогноза:", type=['csv'])

if st.button("СИНТЕЗИРОВАТЬ ПРОГНОЗ 🔥"):
    with st.spinner('Анализирую макро-данные и считаю математику...'):
        
        macro_data = analyze_macro(symbol)
        micro_data = analyze_micro_math(uploaded_csv) if uploaded_csv else None
        
        if not macro_data:
            st.error("Ошибка глобального анализа. Проверьте тикер или интернет.")
        else:
            # === РАЗДЕЛ 1: ГЛОБАЛЬНЫЙ АНАЛИЗ ===
            st.subheader(f"🌍 Глобальная картина (Дневки) — Актуально на: {macro_data['date']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Текущая цена", f"${macro_data['price']:.4f}")
            col2.metric("RSI (14)", f"{macro_data['rsi']:.1f}")
            col3.metric("Тренд (SMA)", macro_data['trend'])
            
            with st.expander("Читать новости"):
                for n in macro_data['news']:
                    st.write(f"- {n}")

            # === РАЗДЕЛ 2: ЛОКАЛЬНАЯ МАТЕМАТИКА ===
            if micro_data:
                st.divider()
                st.subheader("🔬 Математический микро-тренд (Внутри дня)")
                
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("Локальный мат. тренд", micro_data['trend'])
                col_m2.metric("Мат. прогноз (цель)", f"${micro_data['prediction']:.4f}")
                
                # Рисуем график прямо в Streamlit!
                st.line_chart(micro_data['chart_data'])
                
            st.divider()
            
            # === РАЗДЕЛ 3: КОМПЛЕКСНЫЙ ПРОМПТ ДЛЯ ИИ ===
            st.subheader("🧠 Консенсус ИИ (Скопируйте текст ниже):")
            
            # Формируем умный запрос, который объясняет ИИ конфликт таймфреймов
            news_str = "; ".join(macro_data['news'])
            
            prompt = f"Выступи в роли старшего аналитика-трейдера. Проанализируй тикер {macro_data['symbol']}.\n\n"
            prompt += f"ГЛОБАЛЬНО (6 месяцев): Тренд {macro_data['trend']}, RSI {macro_data['rsi']:.1f}. Последняя цена: {macro_data['price']:.4f}.\n"
            prompt += f"ФУНДАМЕНТАЛ (Новости): {news_str}\n\n"
            
            if micro_data:
                prompt += f"ЛОКАЛЬНО (Данные за текущую сессию, {micro_data['points']} точек): "
                prompt += f"Математическая линейная регрессия показывает {micro_data['trend']} тренд "
                prompt += f"с целевой отметкой около {micro_data['prediction']:.4f}.\n\n"
                prompt += "ЗАДАЧА: Возник конфликт таймфреймов. Глобальный тренд и новости могут расходиться с локальной математикой. Как мне действовать прямо сейчас? Дай четкий прогноз и посоветуй точки входа."
            else:
                prompt += "ЗАДАЧА: На основе этих глобальных и фундаментальных данных, дай торговый прогноз."
                
            st.info("Этот промпт объединяет оба подхода. Отправьте его в ChatGPT или Claude, чтобы ИИ разрешил противоречия.")
            st.code(prompt, language="text")
