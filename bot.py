import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yfinance as yf
import sqlite3
import asyncio
import time

# -------------------------
# LOAD ENV
# -------------------------
load_dotenv()

# -------------------------
# DATABASE SETUP
# -------------------------
conn = sqlite3.connect("stocks.db")
cursor = conn.cursor()

# user tracked stocks
cursor.execute("""
CREATE TABLE IF NOT EXISTS portfolio (
    user_id TEXT,
    symbol TEXT,
    quantity REAL,
    buy_price REAL
)
""")

# alerts table
cursor.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    user_id TEXT,
    symbol TEXT,
    target_price REAL,
    direction TEXT,
    channel_id TEXT,
    last_triggered REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS percent_alerts (
    user_id TEXT,
    symbol TEXT,
    start_price REAL,
    percent REAL,
    direction TEXT,
    channel_id TEXT
)
""")
conn.commit()


# -------------------------
# DISCORD SETUP
# -------------------------
intents = discord.Intents.default()
intents.message_content = True

# -------------------------
# DATA LAYER (SQLite)
# -------------------------

def add_stock(user_id, symbol):
    cursor.execute(
        "SELECT 1 FROM user_stocks WHERE user_id = ? AND symbol = ?",
        (str(user_id), symbol)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO user_stocks (user_id, symbol) VALUES (?, ?)",
            (str(user_id), symbol)
        )
        conn.commit()
        return True
    return False


def get_stocks(user_id):
    cursor.execute(
        "SELECT symbol FROM user_stocks WHERE user_id = ?",
        (str(user_id),)
    )
    rows = cursor.fetchall()
    return [row[0] for row in rows]


def remove_stock(user_id, symbol):
    cursor.execute(
        "SELECT 1 FROM user_stocks WHERE user_id = ? AND symbol = ?",
        (str(user_id), symbol)
    )

    if cursor.fetchone():
        cursor.execute(
            "DELETE FROM user_stocks WHERE user_id = ? AND symbol = ?",
            (str(user_id), symbol)
        )
        conn.commit()
        return True

    return False


def get_price(symbol):
    data = yf.Ticker(symbol)
    hist = data.history(period="2d")

    if hist.empty:
        return None

    return hist["Close"].iloc[-1]


def add_alert(user_id, symbol, price, direction, channel_id):
    cursor.execute(
        """INSERT INTO alerts 
        (user_id, symbol, target_price, direction, channel_id, last_triggered)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (str(user_id), symbol, price, direction, str(channel_id), 0)
    )
    conn.commit()


def get_alerts(user_id):
    cursor.execute(
        "SELECT rowid, symbol, target_price, direction FROM alerts WHERE user_id = ?",
        (str(user_id),)
    )
    return cursor.fetchall()


def delete_alert(user_id, alert_id):
    cursor.execute(
        "SELECT 1 FROM alerts WHERE rowid = ? AND user_id = ?",
        (alert_id, str(user_id))
    )

    if cursor.fetchone():
        cursor.execute(
            "DELETE FROM alerts WHERE rowid = ?",
            (alert_id,)
        )
        conn.commit()
        return True

    return False


def add_percent_alert(user_id, symbol, start_price, percent, direction, channel_id):
    cursor.execute(
        """INSERT INTO percent_alerts 
        (user_id, symbol, start_price, percent, direction, channel_id)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (str(user_id), symbol, start_price, percent, direction, str(channel_id))
    )
    conn.commit()

# -------------------------
# BACKGROUND TASK
# -------------------------

async def check_alerts():
    await bot.wait_until_ready()

    COOLDOWN = 300  # 5 minutes

    while not bot.is_closed():

        current_time = time.time()

        cursor.execute("SELECT rowid, user_id, symbol, start_price, percent, direction, channel_id FROM percent_alerts")
        alerts = cursor.fetchall()

        for rowid, user_id, symbol, target, direction, channel_id, last_triggered in alerts:
            try:
                # -------------------------
                # COOLDOWN CHECK
                # -------------------------
                if last_triggered and (current_time - last_triggered < COOLDOWN):
                    continue

                # -------------------------
                # GET PRICE
                # -------------------------
                data = yf.Ticker(symbol)
                price = data.history(period="1d")["Close"].iloc[-1]

                # -------------------------
                # CHECK CONDITION
                # -------------------------
                triggered = (
                    (direction == "above" and price >= target) or
                    (direction == "below" and price <= target)
                )

                if triggered:
                    channel = bot.get_channel(int(channel_id))

                    if channel:
                        embed = discord.Embed(
                            title="🚨 Stock Alert Triggered",
                            description=f"{symbol} hit your target condition",
                            color=discord.Color.red()
                        )

                        embed.add_field(name="Current Price", value=f"${price:.2f}", inline=True)
                        embed.add_field(name="Target", value=f"{direction} ${target}", inline=True)

                        await channel.send(
                            content=f"<@{user_id}>",
                            embed=embed
                        )

                    # -------------------------
                    # UPDATE COOLDOWN TIMER
                    # -------------------------
                    cursor.execute(
                        "UPDATE alerts SET last_triggered = ? WHERE rowid = ?",
                        (current_time, rowid)
                    )
                    conn.commit()

            except Exception as e:
                print(f"Alert error: {e}")

        await asyncio.sleep(60)


# -------------------------
# BOT CLASS (FIXED LOOP)
# -------------------------

class MyBot(commands.Bot):
    async def setup_hook(self):
        self.loop.create_task(check_alerts())


bot = MyBot(command_prefix="!", intents=intents)

# -------------------------
# COMMANDS
# -------------------------

@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.command()
async def stock(ctx, symbol):
    try:
        data = yf.Ticker(symbol)
        hist = data.history(period="1d")

        if hist.empty:
            await ctx.send("Invalid stock symbol")
            return

        row = hist.iloc[-1]

        await ctx.send(
            f"📈 {symbol.upper()}\n"
            f"Price: ${row['Close']:.2f}\n"
            f"High: ${row['High']:.2f}\n"
            f"Low: ${row['Low']:.2f}\n"
            f"Volume: {int(row['Volume'])}"
        )
    except:
        await ctx.send("Error fetching stock data")


@bot.command()
async def track(ctx, symbol):
    symbol = symbol.upper()

    if add_stock(ctx.author.id, symbol):
        await ctx.send(f"Tracking {symbol}")
    else:
        await ctx.send(f"Already tracking {symbol}")


@bot.command()
async def list(ctx):
    stocks = get_stocks(ctx.author.id)

    if not stocks:
        await ctx.send("You are not tracking any stocks")
    else:
        await ctx.send(f"Your stocks: {', '.join(stocks)}")


@bot.command()
async def untrack(ctx, symbol):
    symbol = symbol.upper()

    if remove_stock(ctx.author.id, symbol):
        await ctx.send(f"Stopped tracking {symbol}")
    else:
        await ctx.send("You were not tracking that stock")


@bot.command()
async def alert(ctx, symbol, price: float, direction):
    symbol = symbol.upper()
    direction = direction.lower()

    if direction not in ["above", "below"]:
        await ctx.send("Use: above or below")
        return

    add_alert(ctx.author.id, symbol, price, direction, ctx.channel.id)
    await ctx.send(f"Alert set: {symbol} {direction} ${price}")


@bot.command()
async def alerts(ctx):
    alerts = get_alerts(ctx.author.id)

    if not alerts:
        await ctx.send("You have no active alerts")
        return

    message = "📊 Your Alerts:\n"

    for alert_id, symbol, price, direction in alerts:
        message += f"ID {alert_id}: {symbol} {direction} ${price}\n"

    await ctx.send(message)


@bot.command()
async def removealert(ctx, alert_id: int):
    if delete_alert(ctx.author.id, alert_id):
        await ctx.send(f"Removed alert {alert_id}")
    else:
        await ctx.send("Alert not found or not yours")


@bot.command()
async def alertpercent(ctx, symbol, percent: float, direction):
    symbol = symbol.upper()
    direction = direction.lower()

    if direction not in ["up", "down"]:
        await ctx.send("Use: up or down")
        return

    try:
        data = yf.Ticker(symbol)
        price = data.history(period="1d")["Close"].iloc[-1]

        add_percent_alert(
            ctx.author.id,
            symbol,
            price,
            percent,
            direction,
            ctx.channel.id
        )

        await ctx.send(
            f"Percent alert set: {symbol} {percent}% {direction} from ${price:.2f}"
        )

    except:
        await ctx.send("Error fetching stock data")


@bot.command()
async def buy(ctx, symbol, quantity: float, buy_price: float):
    symbol = symbol.upper()

    cursor.execute(
        """
        INSERT INTO portfolio (user_id, symbol, quantity, buy_price)
        VALUES (?, ?, ?, ?)
        """,
        (str(ctx.author.id), symbol, quantity, buy_price)
    )

    conn.commit()

    await ctx.send(
        f"Added {quantity} shares of {symbol} at ${buy_price:.2f}"
    )

@bot.command()
async def sell(ctx, symbol):
    symbol = symbol.upper()

    cursor.execute(
        """
        DELETE FROM portfolio
        WHERE user_id = ? AND symbol = ?
        """,
        (str(ctx.author.id), symbol)
    )

    conn.commit()

    await ctx.send(f"Removed {symbol} from portfolio")

@bot.command()
async def portfolio(ctx):

    cursor.execute(
        """
        SELECT symbol, quantity, buy_price
        FROM portfolio
        WHERE user_id = ?
        """,
        (str(ctx.author.id),)
    )

    holdings = cursor.fetchall()

    if not holdings:
        await ctx.send("Your portfolio is empty")
        return

    embed = discord.Embed(
        title="📊 Your Portfolio",
        color=discord.Color.green()
    )

    total_value = 0
    total_cost = 0

    for symbol, quantity, buy_price in holdings:

        try:
            data = yf.Ticker(symbol)
            current_price = data.history(period="1d")["Close"].iloc[-1]

            position_value = current_price * quantity
            position_cost = buy_price * quantity

            gain = position_value - position_cost
            percent = (gain / position_cost) * 100

            total_value += position_value
            total_cost += position_cost

            embed.add_field(
                name=f"{symbol} ({quantity} shares)",
                value=(
                    f"Buy: ${buy_price:.2f}\n"
                    f"Current: ${current_price:.2f}\n"
                    f"Value: ${position_value:.2f}\n"
                    f"Gain: ${gain:.2f} ({percent:.2f}%)"
                ),
                inline=False
            )

        except Exception as e:
            print(f"Portfolio error: {e}")

    total_gain = total_value - total_cost
    total_percent = (total_gain / total_cost) * 100 if total_cost else 0

    embed.add_field(
        name="💰 Total Portfolio",
        value=(
            f"Total Value: ${total_value:.2f}\n"
            f"Total Gain: ${total_gain:.2f}\n"
            f"Total Return: {total_percent:.2f}%"
        ),
        inline=False
    )

    await ctx.send(embed=embed)

# -------------------------
# RUN BOT
# -------------------------

bot.run(os.getenv("TOKEN"))