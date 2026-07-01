# 📊 Discord Stock Portfolio Bot

A Python-based Discord bot that provides real-time stock market data, portfolio tracking, and customizable price alerts. The bot uses live financial data and a persistent SQLite database to simulate a personal investing assistant inside Discord.

---

## 🚀 Features

### 📈 Stock Data
- Real-time stock price lookup
- Market data via Yahoo Finance API
- Basic stock statistics (price, volume, daily change)

### 💼 Portfolio System
- Add stocks with quantity and purchase price
- Track real-time portfolio value
- Calculate profit/loss per position
- View total portfolio performance
- Persistent storage using SQLite

### 🚨 Alerts
- Price-based alerts (above/below target)
- Percentage-based alerts (up/down movement)
- Background monitoring system
- Persistent alerts across restarts

### 💾 Data Persistence
- SQLite database for:
  - Portfolio holdings
  - Stock alerts
- Data is saved locally and persists after restart

---

## 🧠 Tech Stack

- Python
- discord.py
- yfinance
- SQLite
- python-dotenv
- asyncio

---

## 📦 Installation

### 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/discord-stock-bot.git  
cd discord-stock-bot  

---

### 2. Create virtual environment
python -m venv venv  
venv\Scripts\activate   # Windows  

---

### 3. Install dependencies
pip install -r requirements.txt  

---

### 4. Create `.env` file
TOKEN=your_discord_bot_token_here  

---

### 5. Run the bot
python bot.py  

---

## 💬 Commands

### 📈 Stock Commands
- `!stock SYMBOL` → Get stock information
- `!track SYMBOL` → Track a stock

### 💼 Portfolio Commands
- `!buy SYMBOL QUANTITY PRICE` → Add stock to portfolio
- `!sell SYMBOL` → Remove stock from portfolio
- `!portfolio` → View portfolio performance

### 🚨 Alert Commands
- `!alert SYMBOL PRICE above/below` → Price-based alert
- `!alertpercent SYMBOL % up/down` → Percentage-based alert

---


## 📊 Example Workflow

### 1. Buy stock
!buy AAPL 5 180  

### 2. Check portfolio
!portfolio  

### 3. Set alert
!alert TSLA 250 above  

---

## 📌 Future Improvements

- Portfolio performance charts
- Machine learning price prediction
- News sentiment integration
- Slash command support
- Web dashboard for portfolio tracking
- Advanced analytics (risk/diversification scoring)

---

## ⚠️ Disclaimer

This project is for educational purposes only and is not financial advice. Stock data is provided via third-party APIs and may be delayed or inaccurate.
