import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import random
import asyncio
import json
from datetime import datetime, timedelta
import database as db
import math

class StockMarket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stocks = {
            "TECH": {"name": "TechCorp", "base_price": 100, "volatility": 0.15, "sector": "Technology"},
            "FOOD": {"name": "FoodCorp", "base_price": 50, "volatility": 0.10, "sector": "Consumer Goods"},
            "ENERGY": {"name": "EnergyCorp", "base_price": 75, "volatility": 0.20, "sector": "Energy"},
            "HEALTH": {"name": "HealthCorp", "base_price": 120, "volatility": 0.12, "sector": "Healthcare"},
            "AUTO": {"name": "AutoCorp", "base_price": 80, "volatility": 0.18, "sector": "Automotive"},
            "BANK": {"name": "BankCorp", "base_price": 90, "volatility": 0.08, "sector": "Finance"},
            "MINING": {"name": "MiningCorp", "base_price": 60, "volatility": 0.25, "sector": "Mining"},
            "GAMING": {"name": "GamingCorp", "base_price": 110, "volatility": 0.22, "sector": "Entertainment"}
        }
        self.current_prices = {}
        self.price_history = {}
        self.last_update = datetime.now()
        
        # Initialize prices
        for symbol, info in self.stocks.items():
            self.current_prices[symbol] = info['base_price']
            self.price_history[symbol] = [info['base_price']]
        
        # Start price update loop
        self.bot.loop.create_task(self.update_prices())

    async def update_prices(self):
        """Update stock prices every 5 minutes"""
        while True:
            await asyncio.sleep(300)  # 5 minutes
            for symbol, info in self.stocks.items():
                current_price = self.current_prices[symbol]
                volatility = info['volatility']
                
                # Calculate price change based on volatility
                change_percent = random.gauss(0, volatility * 0.1)  # Normal distribution
                new_price = current_price * (1 + change_percent)
                
                # Ensure price doesn't go below 1 or above 1000
                new_price = max(1, min(1000, new_price))
                
                self.current_prices[symbol] = new_price
                self.price_history[symbol].append(new_price)
                
                # Keep only last 100 price points
                if len(self.price_history[symbol]) > 100:
                    self.price_history[symbol] = self.price_history[symbol][-100:]
            
            self.last_update = datetime.now()

    def get_user_portfolio(self, user_id: int) -> dict:
        """Get user's stock portfolio"""
        user_data = db.get_user_data(user_id)
        return user_data.get('portfolio', {})

    def save_portfolio(self, user_id: int, portfolio: dict):
        """Save user's portfolio"""
        user_data = db.get_user_data(user_id)
        user_data['portfolio'] = portfolio
        db.update_user_data(user_id, user_data)

    @app_commands.command(name="stocks", description="📈 View stock market prices")
    async def stocks(self, interaction: discord.Interaction, symbol: str = None):
        if symbol and symbol.upper() not in self.stocks:
            embed = discord.Embed(
                title="❌ Invalid Stock Symbol",
                description=f"Available stocks: {', '.join(self.stocks.keys())}",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if symbol:
            # Show specific stock
            symbol = symbol.upper()
            stock_info = self.stocks[symbol]
            current_price = self.current_prices[symbol]
            
            # Calculate price change
            if len(self.price_history[symbol]) > 1:
                prev_price = self.price_history[symbol][-2]
                change = current_price - prev_price
                change_percent = (change / prev_price) * 100
                change_emoji = "📈" if change >= 0 else "📉"
            else:
                change = 0
                change_percent = 0
                change_emoji = "➡️"

            embed = discord.Embed(
                title=f"{change_emoji} {stock_info['name']} ({symbol})",
                description=f"**Current Price:** {current_price:.2f} coins",
                color=0x00ff00 if change >= 0 else 0xff0000
            )
            
            embed.add_field(
                name="📊 Price Change",
                value=f"**Change:** {change:+.2f} ({change_percent:+.2f}%)\n"
                      f"**Sector:** {stock_info['sector']}\n"
                      f"**Volatility:** {stock_info['volatility']:.2%}",
                inline=True
            )
            
            # Show price history (last 10 points)
            history = self.price_history[symbol][-10:]
            history_text = "\n".join([f"{i+1}. {price:.2f}" for i, price in enumerate(history)])
            embed.add_field(
                name="📈 Recent History",
                value=history_text,
                inline=True
            )
            
            embed.set_footer(text=f"Last updated: {self.last_update.strftime('%H:%M:%S')}")
            
        else:
            # Show all stocks
            embed = discord.Embed(
                title="📈 Stock Market",
                description="Current stock prices:",
                color=0x4ecdc4
            )
            
            for symbol, info in self.stocks.items():
                current_price = self.current_prices[symbol]
                
                # Calculate price change
                if len(self.price_history[symbol]) > 1:
                    prev_price = self.price_history[symbol][-2]
                    change = current_price - prev_price
                    change_percent = (change / prev_price) * 100
                    change_emoji = "📈" if change >= 0 else "📉"
                    change_text = f"{change:+.2f} ({change_percent:+.2f}%)"
                else:
                    change_emoji = "➡️"
                    change_text = "No change"

                embed.add_field(
                    name=f"{change_emoji} {symbol}",
                    value=f"**{info['name']}**\n"
                          f"**Price:** {current_price:.2f} coins\n"
                          f"**Change:** {change_text}\n"
                          f"**Sector:** {info['sector']}",
                    inline=True
                )
            
            embed.set_footer(text=f"Prices update every 5 minutes | Last: {self.last_update.strftime('%H:%M:%S')}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="💰 Buy stocks")
    async def buy(self, interaction: discord.Interaction, symbol: str, shares: int):
        symbol = symbol.upper()
        
        if symbol not in self.stocks:
            embed = discord.Embed(
                title="❌ Invalid Stock Symbol",
                description=f"Available stocks: {', '.join(self.stocks.keys())}",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if shares <= 0:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="You must buy at least 1 share.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        current_price = self.current_prices[symbol]
        total_cost = current_price * shares
        
        user_data = db.get_user_data(interaction.user.id)
        balance = user_data.get('coins', 0)
        
        if balance < total_cost:
            embed = discord.Embed(
                title="❌ Insufficient Funds",
                description=f"You need {total_cost:.2f} coins to buy {shares} shares of {symbol}. You have {balance} coins.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Execute trade
        portfolio = self.get_user_portfolio(interaction.user.id)
        if symbol not in portfolio:
            portfolio[symbol] = {"shares": 0, "avg_price": 0}
        
        # Calculate new average price
        current_shares = portfolio[symbol]["shares"]
        current_avg = portfolio[symbol]["avg_price"]
        new_shares = current_shares + shares
        new_avg = ((current_shares * current_avg) + (shares * current_price)) / new_shares
        
        portfolio[symbol]["shares"] = new_shares
        portfolio[symbol]["avg_price"] = new_avg
        
        # Deduct coins
        db.remove_coins(interaction.user.id, total_cost)
        self.save_portfolio(interaction.user.id, portfolio)
        
        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"You bought {shares} shares of {symbol} at {current_price:.2f} coins per share.",
            color=0x00ff00
        )
        embed.add_field(
            name="💰 Transaction Details",
            value=f"**Total Cost:** {total_cost:.2f} coins\n"
                  f"**New Balance:** {balance - total_cost:.2f} coins\n"
                  f"**Total Shares:** {new_shares}\n"
                  f"**Average Price:** {new_avg:.2f} coins",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell", description="💰 Sell stocks")
    async def sell(self, interaction: discord.Interaction, symbol: str, shares: int):
        symbol = symbol.upper()
        
        if symbol not in self.stocks:
            embed = discord.Embed(
                title="❌ Invalid Stock Symbol",
                description=f"Available stocks: {', '.join(self.stocks.keys())}",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if shares <= 0:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="You must sell at least 1 share.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        portfolio = self.get_user_portfolio(interaction.user.id)
        if symbol not in portfolio or portfolio[symbol]["shares"] < shares:
            embed = discord.Embed(
                title="❌ Insufficient Shares",
                description=f"You don't have enough shares of {symbol} to sell.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        current_price = self.current_prices[symbol]
        total_revenue = current_price * shares
        avg_price = portfolio[symbol]["avg_price"]
        profit = (current_price - avg_price) * shares
        
        # Execute trade
        portfolio[symbol]["shares"] -= shares
        if portfolio[symbol]["shares"] == 0:
            del portfolio[symbol]
        
        # Add coins
        db.add_coins(interaction.user.id, total_revenue)
        self.save_portfolio(interaction.user.id, portfolio)
        
        profit_emoji = "📈" if profit >= 0 else "📉"
        profit_color = 0x00ff00 if profit >= 0 else 0xff0000
        
        embed = discord.Embed(
            title="✅ Sale Successful!",
            description=f"You sold {shares} shares of {symbol} at {current_price:.2f} coins per share.",
            color=profit_color
        )
        embed.add_field(
            name="💰 Transaction Details",
            value=f"**Total Revenue:** {total_revenue:.2f} coins\n"
                  f"**Profit/Loss:** {profit_emoji} {profit:+.2f} coins\n"
                  f"**Average Buy Price:** {avg_price:.2f} coins\n"
                  f"**Remaining Shares:** {portfolio.get(symbol, {}).get('shares', 0)}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="portfolio", description="💼 View your stock portfolio")
    async def portfolio(self, interaction: discord.Interaction):
        portfolio = self.get_user_portfolio(interaction.user.id)
        
        if not portfolio:
            embed = discord.Embed(
                title="💼 Empty Portfolio",
                description="You don't own any stocks yet. Use `/stocks` to view available stocks and `/buy` to start investing!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        total_value = 0
        total_profit = 0
        
        embed = discord.Embed(
            title="💼 Your Portfolio",
            description="Your current stock holdings:",
            color=0x4ecdc4
        )
        
        for symbol, holding in portfolio.items():
            if holding["shares"] > 0:
                current_price = self.current_prices[symbol]
                stock_value = current_price * holding["shares"]
                avg_price = holding["avg_price"]
                profit = (current_price - avg_price) * holding["shares"]
                profit_percent = ((current_price - avg_price) / avg_price) * 100
                
                total_value += stock_value
                total_profit += profit
                
                profit_emoji = "📈" if profit >= 0 else "📉"
                profit_color = 0x00ff00 if profit >= 0 else 0xff0000
                
                embed.add_field(
                    name=f"{profit_emoji} {symbol}",
                    value=f"**Shares:** {holding['shares']}\n"
                          f"**Current Price:** {current_price:.2f} coins\n"
                          f"**Avg Price:** {avg_price:.2f} coins\n"
                          f"**Value:** {stock_value:.2f} coins\n"
                          f"**P/L:** {profit:+.2f} ({profit_percent:+.2f}%)",
                    inline=True
                )
        
        embed.add_field(
            name="📊 Portfolio Summary",
            value=f"**Total Value:** {total_value:.2f} coins\n"
                  f"**Total P/L:** {total_profit:+.2f} coins\n"
                  f"**Last Updated:** {self.last_update.strftime('%H:%M:%S')}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="market", description="📊 Market overview and trends")
    async def market(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📊 Market Overview",
            description="Current market trends and statistics:",
            color=0x4ecdc4
        )
        
        # Calculate market statistics
        total_market_cap = sum(self.current_prices.values())
        avg_price = total_market_cap / len(self.stocks)
        
        # Find best and worst performers
        performers = []
        for symbol in self.stocks:
            if len(self.price_history[symbol]) > 1:
                change = ((self.current_prices[symbol] - self.price_history[symbol][0]) / self.price_history[symbol][0]) * 100
                performers.append((symbol, change))
        
        performers.sort(key=lambda x: x[1], reverse=True)
        
        embed.add_field(
            name="📈 Market Statistics",
            value=f"**Total Market Cap:** {total_market_cap:.2f} coins\n"
                  f"**Average Price:** {avg_price:.2f} coins\n"
                  f"**Active Stocks:** {len(self.stocks)}\n"
                  f"**Last Update:** {self.last_update.strftime('%H:%M:%S')}",
            inline=True
        )
        
        if performers:
            best = performers[0]
            worst = performers[-1]
            
            embed.add_field(
                name="🏆 Top Performers",
                value=f"**Best:** {best[0]} ({best[1]:+.2f}%)\n"
                      f"**Worst:** {worst[0]} ({worst[1]:+.2f}%)\n"
                      f"**Spread:** {best[1] - worst[1]:.2f}%",
                inline=True
            )
        
        # Sector breakdown
        sectors = {}
        for symbol, info in self.stocks.items():
            sector = info['sector']
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(self.current_prices[symbol])
        
        sector_text = ""
        for sector, prices in sectors.items():
            avg_sector_price = sum(prices) / len(prices)
            sector_text += f"**{sector}:** {avg_sector_price:.2f} coins\n"
        
        embed.add_field(
            name="🏢 Sector Breakdown",
            value=sector_text,
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(StockMarket(bot))