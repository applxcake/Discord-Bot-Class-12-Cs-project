import discord
import mysql.connector
from discord.ext import commands, tasks
import random
import string
import os
import asyncio
import pytz
import textwrap
import sys
import json
import math
import difflib
import subprocess
import uuid
import aiohttp
import io
import re
import requests
import time as t
import datetime
from mysql.connector.errors import OperationalError
import traceback
from discord.ui import Modal, TextInput, Button, View
from datetime import datetime, timedelta, time
from discord import app_commands, ui, Interaction, Embed
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from math import floor
from decimal import Decimal

# Discord bot setup with necessary intents
# Define the intents
intents = discord.Intents.default()
intents.messages = True  # Listen for messages
intents.guilds = True
intents.message_content = True  # Required for message content (text) monitoring
intents.guild_messages = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
geolocator = Nominatim(user_agent="flight_bot")

# MySQL database connection setup
db_config = {
    'host': 'HOST_NAME',
    'port': 'PORT',
    'user': 'USER_NAME',
    'password': 'PASSWORD',
    'database': 'DB_NAME',
    'connection_timeout': 99999999999999
}

try:
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    print("Connected to the MySQL database successfully.")
except mysql.connector.Error as err:
    print(f"Error connecting to the database: {err}")
    exit(1)

# Function to generate a ticket number
def generate_ticket_number():
    return "".join(
        random.choice(string.digits) if i % 2 == 0 else random.choice(string.ascii_uppercase)
        for i in range(8)
    )

# Creating the tickets table if it doesn't already exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    ticket_number VARCHAR(8) PRIMARY KEY,
    passenger_name VARCHAR(100),
    age INT,
    passport_number VARCHAR(20),
    departure_country VARCHAR(50),
    destination_country VARCHAR(50),
    flight_type VARCHAR(20),
    price DECIMAL(10, 2),
    arrival_date DATE
)
""")
db.commit()


# Channel IDs for different categories
channel_ids = {
    "ticket_purchasing": <channel_id>,
    "inquiry": <channel_id>,
    "support": <channel_id>,
    "cancel": <channel_id>,
    "show_table": <channel_id>,
}

# Counter for ticket numbering
ticket_count = 0

# Function to create a new ticket channel with a formatted name and guide message
async def create_ticket_channel(guild, category, ticket_type, guide_message, user):
    global ticket_count
    ticket_count += 1  # Increment for each new ticket
    channel_name = f"{ticket_type}#{ticket_count:03}"  # Format as ticket#NNN

    # Set up permissions: allow only the user and the bot to access the channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),  # Hide from everyone
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),  # Allow only the user
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),  # Allow the bot
    }

    # Create a new text channel in the specified category with permissions
    channel = await guild.create_text_channel(
        name=channel_name,
        category=category,
        topic=f"{ticket_type.capitalize()} support ticket number {ticket_count:03}",
        overwrites=overwrites
    )

    # Send a guide message with an embedded look
    embed = discord.Embed(
        title=f"📄 {ticket_type.capitalize()} Support Guide",
        description=guide_message,
        color=discord.Color.blue()
    )
    await channel.send(embed=embed)

    return channel

# Ensure ticket counter is set based on existing ticket channels
async def initialize_ticket_count(guild):
    global ticket_count
    # Count channels that match the ticket naming pattern (e.g., ticket#001)
    ticket_count = sum(1 for channel in guild.text_channels if channel.name.startswith(tuple(channel_ids.keys())) and "#" in channel.name and channel.name.split("#")[1].isdigit())

# Ticket Purchasing Embed
@bot.command(name='channel-purchase')
@commands.is_owner()
async def ticket_purchasing_command(ctx):
    """Embeds purchase command in a specific channel."""
    channel = bot.get_channel(channel_ids["ticket_purchasing"])
    if not channel:
        await ctx.send("Ticket Purchasing channel not found.")
        return

    embed = discord.Embed(
        title="🎟️ Ticket Purchasing",
        description="Click below to start purchasing a ticket.",
        color=discord.Color.blue()
    )
    view = discord.ui.View()
    ticket_button = discord.ui.Button(label="Purchase Ticket", style=discord.ButtonStyle.green)

    async def ticket_button_callback(interaction):
        category = channel.category
        guide_message = (
            "✅ Thank you for starting a ticket purchase!\n\n"
            "To begin, use the command `!purchase` in this channel and follow the steps provided. 🎫"
        )
        new_channel = await create_ticket_channel(interaction.guild, category, "ticket", guide_message, interaction.user)
        await new_channel.send(f"{interaction.user.mention}, your ticket purchasing support has been created here.")
        await interaction.response.send_message("Your ticket has been created!", ephemeral=True)

    ticket_button.callback = ticket_button_callback
    view.add_item(ticket_button)

    await channel.send(embed=embed, view=view)

# Inquiry Embed
@bot.command(name='channel-inquiry')
@commands.is_owner()
async def inquiry_command(ctx):
    """Embeds inquiry command in a specific channel."""
    channel = bot.get_channel(channel_ids["inquiry"])
    if not channel:
        await ctx.send("Inquiry channel not found.")
        return

    embed = discord.Embed(
        title="💬 Inquiry",
        description="Click below for assistance with inquiries.",
        color=discord.Color.blue()
    )
    view = discord.ui.View()
    inquiry_button = discord.ui.Button(label="Get Help", style=discord.ButtonStyle.blurple)

    async def inquiry_button_callback(interaction):
        category = channel.category
        guide_message = (
            "💡 You’ve opened an inquiry ticket!\n\n"
            "For help, please provide details of your inquiry here or use the command `!inquiry` for specific questions. 💬"
        )
        new_channel = await create_ticket_channel(ctx.guild, category, "inquiry", guide_message, interaction.user)
        await new_channel.send(f"{interaction.user.mention}, your inquiry support has been created here.")
        await interaction.response.send_message("An inquiry ticket has been created!", ephemeral=True)

    inquiry_button.callback = inquiry_button_callback
    view.add_item(inquiry_button)

    await channel.send(embed=embed, view=view)

# Support Embed
@bot.command(name='channel-support')
@commands.is_owner()
async def support_command(ctx):
    """Embeds support command in a specific channel."""
    channel = bot.get_channel(channel_ids["support"])
    if not channel:
        await ctx.send("Support channel not found.")
        return

    embed = discord.Embed(
        title="🛠️ Support",
        description="Need help? Click below for assistance.",
        color=discord.Color.blue()
    )
    view = discord.ui.View()
    support_button = discord.ui.Button(label="Get Support", style=discord.ButtonStyle.green)

    async def support_button_callback(interaction):
        category = channel.category
        guide_message = (
            "🛠️ Welcome to support!\n\n"
            "Describe your issue here or use `!help` to get started with your support request. 🆘"
        )
        new_channel = await create_ticket_channel(ctx.guild, category, "support", guide_message, interaction.user)
        await new_channel.send(f"{interaction.user.mention}, your support ticket has been created here.")
        await interaction.response.send_message("A support ticket has been created!", ephemeral=True)

    support_button.callback = support_button_callback
    view.add_item(support_button)

    await channel.send(embed=embed, view=view)

# Cancel Embed
@bot.command(name='channel-cancel')
@commands.is_owner()
async def cancel_command(ctx):
    """Embeds cancel command in a specific channel."""
    channel = bot.get_channel(channel_ids["cancel"])
    if not channel:
        await ctx.send("Cancel channel not found.")
        return

    embed = discord.Embed(
        title="❌ Cancel",
        description="Use this button to cancel your ticket if needed.",
        color=discord.Color.red()
    )
    view = discord.ui.View()
    cancel_button = discord.ui.Button(label="Cancel Ticket", style=discord.ButtonStyle.danger)

    async def cancel_button_callback(interaction):
        category = channel.category
        guide_message = (
            "❌ You have requested a ticket cancellation.\n\n"
            "To confirm cancellation, please use `!cancel` in this channel and follow the steps. 📑"
        )
        new_channel = await create_ticket_channel(ctx.guild, category, "cancel", guide_message, interaction.user)
        await new_channel.send(f"{interaction.user.mention}, your cancellation support has been created here.")
        await interaction.response.send_message("A cancellation ticket has been created!", ephemeral=True)

    cancel_button.callback = cancel_button_callback
    view.add_item(cancel_button)

    await channel.send(embed=embed, view=view)

# Showtb_tickets Embed
@bot.command(name='channel-showtb_tickets')
@commands.is_owner()
async def show_table_command(ctx):
    """Embeds show table list in a specific channel."""
    channel = bot.get_channel(channel_ids["show_table"])
    if not channel:
        await ctx.send("Show Table channel not found.")
        return

    cursor.execute("SELECT * FROM tickets")
    results = cursor.fetchall()
    embed = discord.Embed(
        title="📋 Booked Tickets",
        description="List of all booked tickets:",
        color=discord.Color.green()
    )

    for row in results:
        ticket_number, name, age, passport_number, departure, destination, flight_type, price, arrival_date, flight_number, seat_number, purchase_time, grptno, member_id = row
        ticket_info = (
            f"🎟️ **Ticket Number**: {ticket_number}\n"
            f"👤 **Passenger Name**: {name}\n"
            f"🛂 **Passport No.**: {passport_number}\n"
            f"💺 **Flight Type**: {flight_type.capitalize()}\n"
            f"🛫 **Departure**: {departure}\n"
            f"🛬 **Destination**: {destination}\n"
            f"💵 **Price**: ${price:.2f}\n"
            f"📅 **Arrival Date**: {arrival_date}\n"
            f"✈️ **Flight Number**: {flight_number}\n"
            f"💺 **Seat Number **: {seat_number}\n"
            f"🕒 **Purchase Time (IST)**: {purchase_time}\n"
            f"👥 **Group Number**: {grptno}\n"
            f"🪪 **Member ID**: {member_id}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(name=f"Ticket #{ticket_number}", value=ticket_info, inline=False)

    view = discord.ui.View()
    show_table_button = discord.ui.Button(label="Show Table", style=discord.ButtonStyle.blurple)

    async def show_table_callback(interaction):
        category = channel.category
        guide_message = (
            "📋 Viewing ticket table details.\n\n"
            "Use `!showtb_tickets` to view the tickets table. 💼"
        )
        new_channel = await create_ticket_channel(ctx.guild, category, "table", guide_message, interaction.user)
        await new_channel.send(f"{interaction.user.mention}, the table view has been created here.")
        await interaction.response.send_message("Table ticket has been created!", ephemeral=True)

    show_table_button.callback = show_table_callback
    view.add_item(show_table_button)

    await channel.send(embed=embed, view=view)
    
#HELPME CMD
# Remove the default help command
bot.remove_command('help')

@bot.command(name='help')
async def help_command(ctx):
    """Lists all the intended commands."""
    embed = discord.Embed(
        title="📋 Help Menu",
        description="Here's a list of available commands:",
        color=discord.Color.blue()
    )
    embed.add_field(name="✈️ !purchase", value="Purchase a flight ticket", inline=False)
    embed.add_field(name="🔍 !inquiry", value="Check flight information", inline=False)
    embed.add_field(name="🛠️ !support", value="Support for issues like luggage delay or ticket postpone", inline=False)
    embed.add_field(name="❌ !cancel", value="Cancel a booking", inline=False)
    embed.add_field(name="🎟️ !lookup", value="Check the details of your ticket!", inline=False)
    embed.add_field(name="📋 !showtb_tickets", value="Show all booked tickets ", inline=False)
    embed.add_field(name="📋 !showtb_flight", value="Show all the information in 'flight' table. ", inline=False)
    embed.add_field(name="💬 !purge", value="Deletes Messages (in whole)", inline=False)
    embed.add_field(name="🧮 !calc", value="A basic Calculator for our needs", inline=False)
    embed.add_field(name="📢 !about", value="Tells about the bot :3", inline=False)
    await ctx.send(embed=embed)
#purchase
# Function to generate a random seat number
def generate_seat_number():
    row = random.randint(1, 30)  # Example: 30 rows in the plane
    seat = random.choice("ABCDEF")  # Example: seats labeled A-F
    return f"{row}{seat}"

# Function to generate a group number
def generate_group_number():
    return (
        "".join(random.choices(string.ascii_uppercase, k=2)) +
        "".join(random.choices(string.digits, k=4)) +
        "".join(random.choices(string.ascii_uppercase, k=2))
    )

# Function to generate a ticket number
def generate_ticket_number():
    letters = string.ascii_uppercase
    digits = string.digits
    return (
        ''.join(random.choices(letters, k=2)) +
        ''.join(random.choices(digits, k=4)) +
        ''.join(random.choices(letters, k=2))
    )

@bot.command(name="purchase")
async def purchase_ticket(ctx):
    """Purchase command for flight tickets."""
    embed = discord.Embed(
        title="✈️ Flight Ticket Booking",
        description="Click the button below to start the booking process. \nPut commas in between for Group purchase 👥.",
        color=discord.Color.blue(),
    )
    view = discord.ui.View(timeout=None)
    start_button = discord.ui.Button(label="Start Booking", style=discord.ButtonStyle.primary)

    async def start_booking_callback(interaction: discord.Interaction):
        # Step 1: Ask for passenger details
        class PassengerInfoModal(discord.ui.Modal, title="Passenger Information"):
            names = discord.ui.TextInput(label="👤 Passenger Names", placeholder="Enter your name (e.g., Alice, Bob...)")
            ages = discord.ui.TextInput(label="📅 Ages", placeholder="Enter your age")
            passport_numbers = discord.ui.TextInput(label="🛂 Passport Numbers", placeholder="Enter your passport number")
            departure_country = discord.ui.TextInput(label="🛫 Departure Country", placeholder="Where are you departing from?")
            destination_country = discord.ui.TextInput(label="🛬 Destination Country", placeholder="Where are you going?")

            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.defer()

                passenger_names = self.names.value.upper().split(",")
                passenger_ages = self.ages.value.split(",")
                passport_numbers = self.passport_numbers.value.upper().split(",")

                num_passengers = len(passenger_names)
                if num_passengers != len(passenger_ages) or num_passengers != len(passport_numbers):
                    await interaction.followup.send("⚠️ Ensure the same number of names, ages, and passport numbers are provided. Use commas to separate values.", ephemeral=True)
                    return

                try:
                    passenger_ages = [int(age.strip()) for age in passenger_ages]
                    if not all(0 <= age <= 120 for age in passenger_ages):
                        await interaction.followup.send("⚠️ Ages must be between 0 and 120.", ephemeral=True)
                        return
                except ValueError:
                    await interaction.followup.send("⚠️ Please ensure all ages are valid integers.", ephemeral=True)
                    return

                # Step 2: Ask for the travel date
                await interaction.followup.send("Please enter the **travel date** (YYYY-MM-DD):", ephemeral=True)

                # Wait for the user to enter the date
                def check(message):
                    return message.author == interaction.user and message.content

                try:
                    message = await bot.wait_for("message", check=check, timeout=60.0)
                    travel_date_str = message.content.strip()

                    # Check if the date is valid
                    try:
                        travel_date = datetime.strptime(travel_date_str, "%Y-%m-%d")
                    except ValueError:
                        await interaction.followup.send("⚠️ Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
                        return

                    # Check if the date is in the past
                    if travel_date < datetime.now():
                        await interaction.followup.send("⚠️ The travel date cannot be in the past. Please enter a valid future date.", ephemeral=True)
                        return

                    # Continue with processing flight and ticket information
                    # Fetch flight details from the database
                    cursor.execute(
                        "SELECT flight_number FROM flight WHERE LOWER(place) = LOWER(%s) LIMIT 1",
                        (self.departure_country.value,)
                    )
                    flight_results = cursor.fetchone()

                    if not flight_results:
                        await interaction.followup.send(
                            f"⚠️ No flights found departing from **{self.departure_country.value.upper()}**. Please check the departure location.",
                            ephemeral=True,
                        )
                        return

                    flight_number = flight_results[0].upper()

                    # Calculate flight price based on distance
                    try:
                        departure_location = geolocator.geocode(self.departure_country.value)
                        destination_location = geolocator.geocode(self.destination_country.value)
                        if not departure_location or not destination_location:
                            await interaction.followup.send("⚠️ Could not locate one of the places. Check country names.", ephemeral=True)
                            return

                        distance_km = geodesic(
                            (departure_location.latitude, departure_location.longitude),
                            (destination_location.latitude, destination_location.longitude)
                        ).km
                        price = distance_km * 0.1
                    except Exception as e:
                        await interaction.followup.send(f"⚠️ Error in location calculation: {e}", ephemeral=True)
                        return

                    # Flight type selection
                    async def prompt_flight_type():
                        embed = discord.Embed(
                            title="Select Flight Type ✈️",
                            description="Choose your flight type from the options below.",
                            color=discord.Color.blue(),
                        )
                        view = discord.ui.View()
                        flight_types = {"economy": price, "business": price * 1.5, "first": price * 2}

                        for flight_type, calculated_price in flight_types.items():
                            button = discord.ui.Button(label=f"{flight_type.capitalize()} - ${calculated_price:.2f}", style=discord.ButtonStyle.secondary)

                            async def flight_type_callback(interaction, flight_type=flight_type, calculated_price=calculated_price):
                                total_price = calculated_price * num_passengers

                                # Check user balance
                                cursor.execute("SELECT balance FROM users WHERE user_id = %s", (ctx.author.id,))
                                user_data = cursor.fetchone()
                                if not user_data or user_data[0] < total_price:
                                    await interaction.response.send_message(embed=discord.Embed(
                                        title="❌ Insufficient Funds",
                                        description=f"You need **${total_price:.2f}** for this purchase, but your current balance is **${user_data[0]:.2f}**.",
                                        color=discord.Color.red(),
                                    ))
                                    return

                                # Deduct money and generate tickets
                                cursor.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (total_price, ctx.author.id))
                                db.commit()

                                confirmation_embed = discord.Embed(
                                    title="Ticket Purchase Confirmation 🎫",
                                    description="Your ticket has been successfully booked! Here are your details:",
                                    color=discord.Color.green(),
                                )

                                passenger_list = "\n".join(passenger_names)
                                confirmation_embed.add_field(name="👤 Passengers List", value=passenger_list, inline=False)
                                confirmation_embed.add_field(name="🛫 Departure", value=self.departure_country.value.upper(), inline=True)
                                confirmation_embed.add_field(name="🛬 Destination", value=self.destination_country.value.upper(), inline=True)
                                confirmation_embed.add_field(name="💺 Flight Type", value=flight_type.upper(), inline=False)
                                confirmation_embed.add_field(name="✈️ Flight Number", value=flight_number, inline=False)
                                confirmation_embed.add_field(name="💰 Total Price", value=f"${total_price:.2f}", inline=False)

                                ist = pytz.timezone("Asia/Kolkata")
                                current_time_ist = datetime.now(ist).strftime("%I:%M %p")

                                for i, (name, age, passport) in enumerate(zip(passenger_names, passenger_ages, passport_numbers)):
                                    ticket_number = generate_ticket_number().upper()
                                    seat_number = generate_seat_number()
                                    cursor.execute("""
                                        INSERT INTO tickets (ticket_number, passenger_name, age, passport_number, 
                                                             departure_country, destination_country, flight_type, 
                                                             price, flight_number, seat_number, purchase_time, grptno, member_id)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (
                                        ticket_number, name, age, passport, self.departure_country.value.upper(),
                                        self.destination_country.value.upper(), flight_type, calculated_price,
                                        flight_number, seat_number, current_time_ist, generate_group_number(), ctx.author.id
                                    ))
                                    db.commit()

                                    if i > 0:
                                        confirmation_embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━", inline=False)

                                    confirmation_embed.add_field(name="🎟️ Ticket Number", value=ticket_number, inline=False)
                                    confirmation_embed.add_field(name="👤 Name", value=name, inline=True)
                                    confirmation_embed.add_field(name="📅 Age", value=age, inline=True)
                                    confirmation_embed.add_field(name="🛂 Passport", value=passport, inline=True)
                                    confirmation_embed.add_field(name="🪑 Seat", value=seat_number, inline=False)

                                await interaction.response.send_message(embed=confirmation_embed)

                            button.callback = flight_type_callback
                            view.add_item(button)

                        await ctx.send(embed=embed, view=view)

                    await prompt_flight_type()

                except Exception as e:
                    await interaction.followup.send(f"⚠️ Error: {e}", ephemeral=True)

        # Show the modal directly (without adding it to the view)
        await interaction.response.send_modal(PassengerInfoModal())

    start_button.callback = start_booking_callback
    view.add_item(start_button)
    await ctx.send(embed=embed, view=view)
#bank stuff
# Function to generate a bank ID
def generate_bank_id():
    return "".join(random.choices(string.digits, k=8))

# Function to generate a bank PIN
def generate_bank_pin():
    return "".join(random.choices(string.digits, k=4))

# CREATE ACCOUNT COMMAND
@bot.command(name="create_account")
async def create_account(ctx):
    """Creates a new bank account for the user."""
    cursor.execute("SELECT bank_id FROM users WHERE user_id = %s", (ctx.author.id,))
    if cursor.fetchone():
        await ctx.send(embed=discord.Embed(
            title="❌ Account Already Exists",
            description="You already have a bank account!",
            color=discord.Color.red(),
        ))
        return

    # Generate a unique bank ID and PIN
    bank_id = generate_bank_id()
    bank_pin = generate_bank_pin()

    # Insert new account into the database
    cursor.execute(
        """
        INSERT INTO users (user_id, bank_id, bank_pin, balance)
        VALUES (%s, %s, %s, %s)
        """,
        (ctx.author.id, bank_id, bank_pin, 0.0),
    )
    db.commit()

    # Send confirmation to the user's DMs
    try:
        await ctx.author.send(embed=discord.Embed(
            title="✅ Account Created",
            description=(
                f"Your bank account has been successfully created!\n\n"
                f"**Bank ID:** {bank_id}\n"
                f"**PIN:** {bank_pin}\n\n"
                f"Keep this information secure!"
            ),
            color=discord.Color.green(),
        ))

        await ctx.send(embed=discord.Embed(
            title="✅ Account Created",
            description="Your bank account has been successfully created! Check your DMs for credentials.",
            color=discord.Color.green(),
        ))
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(
            title="⚠️ DM Failed",
            description="Your account was created, but I couldn't send your credentials via DM. Please check your DM settings.",
            color=discord.Color.orange(),
        ))
# BALANCE CMD
@bot.command(name="bal", aliases=["balance"])
async def balance(ctx):
    """Check the user's current balance."""
    cursor.execute("SELECT balance FROM users WHERE user_id = %s", (ctx.author.id,))
    user = cursor.fetchone()
    if user:
        balance = user[0]
        embed = discord.Embed(
            title="💰 Your Balance",
            description=f"Your current balance is **${balance:.2f}**.",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(embed=discord.Embed(
            title="❌ No Account Found",
            description="You don't have a bank account. Start a purchase to create one!",
            color=discord.Color.red()
        ))
@bot.command(name="history")
async def history(ctx):
    """View transaction history."""
    cursor.execute("""
        SELECT type, amount, recipient_id, description, timestamp
        FROM transactions
        WHERE user_id = %s
        ORDER BY timestamp DESC LIMIT 10
    """, (ctx.author.id,))
    transactions = cursor.fetchall()

    if not transactions:
        await ctx.send(embed=discord.Embed(
            title="📜 Transaction History",
            description="No recent transactions found.",
            color=discord.Color.blue(),
        ))
        return

    embed = discord.Embed(
        title="📜 Transaction History",
        color=discord.Color.blue(),
    )

    for transaction in transactions:
        type_, amount, recipient_id, description, timestamp = transaction
        recipient_info = f"Recipient: <@{recipient_id}>" if recipient_id else ""
        embed.add_field(
            name=f"{type_.capitalize()} - ${amount:.2f}",
            value=f"{description or ''}\n{recipient_info}\n*{timestamp}*",
            inline=False,
        )

    await ctx.send(embed=embed)
# Your user ID for loan approvals
ADMIN_USER_ID = ...

# Cooldown trackers
daily_cooldowns = {}
steal_cooldowns = {}
class LoanApprovalView(View):
    def __init__(self, user_id, loan_amount):
        super().__init__(timeout=3600)  # Timeout after 1 hour
        self.user_id = user_id
        self.loan_amount = loan_amount

    @discord.ui.button(label="Approve Loan", style=discord.ButtonStyle.green, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != ADMIN_USER_ID:
            await interaction.response.send_message("You are not authorized to perform this action.", ephemeral=True)
            return

        # Grant the loan
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (self.loan_amount, self.user_id))
        db.commit()
        cursor.execute(
            """
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (%s, 'loan', %s, 'Loan approved by admin')
            """,
            (self.user_id, self.loan_amount)
        )
        db.commit()

        # Notify the user who requested the loan
        user = await bot.fetch_user(self.user_id)
        try:
            await user.send(embed=discord.Embed(
                title="✅ Loan Approved",
                description=f"Your loan of **${self.loan_amount:.2f}** has been approved and added to your account.",
                color=discord.Color.green(),
            ))
        except discord.Forbidden:
            await interaction.response.send_message(
                f"⚠️ Could not send a DM to the user <@{self.user_id}>. They might have DMs disabled.", ephemeral=True
            )

        # Notify the admin and update the interaction message
        await interaction.response.edit_message(embed=discord.Embed(
            title="✅ Loan Approved",
            description=f"The loan request from <@{self.user_id}> has been approved.",
            color=discord.Color.green(),
        ), view=None)

    @discord.ui.button(label="Reject Loan", style=discord.ButtonStyle.red, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != ADMIN_USER_ID:
            await interaction.response.send_message("You are not authorized to perform this action.", ephemeral=True)
            return

        user = await bot.fetch_user(self.user_id)
        try:
            await user.send(embed=discord.Embed(
                title="❌ Loan Rejected",
                description=f"Your loan request for **${self.loan_amount:.2f}** has been rejected.",
                color=discord.Color.red(),
            ))
        except discord.Forbidden:
            await interaction.response.send_message(
                f"⚠️ Could not send a DM to the user <@{self.user_id}>. They might have DMs disabled.", ephemeral=True
            )

        await interaction.response.edit_message(embed=discord.Embed(
            title="❌ Loan Rejected",
            description=f"The loan request from <@{self.user_id}> has been rejected.",
            color=discord.Color.red(),
        ), view=None)

# Cooldown trackers
daily_cooldowns = {}
steal_cooldowns = {}
class LoanApprovalView(View):
    def __init__(self, user_id, loan_amount):
        super().__init__(timeout=3600)  # Timeout after 1 hour
        self.user_id = user_id
        self.loan_amount = loan_amount

    @discord.ui.button(label="Approve Loan", style=discord.ButtonStyle.green, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != ADMIN_USER_ID:
            await interaction.response.send_message("You are not authorized to perform this action.", ephemeral=True)
            return

        # Grant the loan
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (self.loan_amount, self.user_id))
        db.commit()
        cursor.execute(
            """
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (%s, 'loan', %s, 'Loan approved by admin')
            """,
            (self.user_id, self.loan_amount)
        )
        db.commit()

        # Notify the user who requested the loan
        user = await bot.fetch_user(self.user_id)
        try:
            await user.send(embed=discord.Embed(
                title="✅ Loan Approved",
                description=f"Your loan of **${self.loan_amount:.2f}** has been approved and added to your account.",
                color=discord.Color.green(),
            ))
        except discord.Forbidden:
            await interaction.response.send_message(
                f"⚠️ Could not send a DM to the user <@{self.user_id}>. They might have DMs disabled.", ephemeral=True
            )

        # Notify the admin and update the interaction message
        await interaction.response.edit_message(embed=discord.Embed(
            title="✅ Loan Approved",
            description=f"The loan request from <@{self.user_id}> has been approved.",
            color=discord.Color.green(),
        ), view=None)

    @discord.ui.button(label="Reject Loan", style=discord.ButtonStyle.red, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != ADMIN_USER_ID:
            await interaction.response.send_message("You are not authorized to perform this action.", ephemeral=True)
            return

        user = await bot.fetch_user(self.user_id)
        try:
            await user.send(embed=discord.Embed(
                title="❌ Loan Rejected",
                description=f"Your loan request for **${self.loan_amount:.2f}** has been rejected.",
                color=discord.Color.red(),
            ))
        except discord.Forbidden:
            await interaction.response.send_message(
                f"⚠️ Could not send a DM to the user <@{self.user_id}>. They might have DMs disabled.", ephemeral=True
            )

        await interaction.response.edit_message(embed=discord.Embed(
            title="❌ Loan Rejected",
            description=f"The loan request from <@{self.user_id}> has been rejected.",
            color=discord.Color.red(),
        ), view=None)

def format_money(amount):
    """Formats a number with commas and two decimal places."""
    return f"${amount:,.2f}"

@bot.command(name="bank")
async def bank(ctx, action=None, *args):
    """Bank command for transfers, deposits, withdrawals, loans, gambling, stealing, and more."""
    cursor.execute("SELECT bank_id, bank_pin, balance, pocket FROM users WHERE user_id = %s", (ctx.author.id,))
    user = cursor.fetchone()
    if not user:
        await ctx.send(embed=discord.Embed(
            title="❌ No Account Found",
            description="You don't have a bank account. Start a purchase to create one!",
            color=discord.Color.red()
        ))
        return

    bank_id, bank_pin, balance, pocket = user
    balance = Decimal(balance)  # Ensure balance is treated as Decimal
    pocket = Decimal(pocket)    # Ensure pocket is treated as Decimal
    action = action.lower() if action else None

    if not action:
        embed = discord.Embed(
            title="🏦 Bank Menu",
            description=(
                f"💳 **Bank Balance:** {format_money(balance)}\n"
                f"🪙 **Pocket Money:** {format_money(pocket)}\n\n"
                f"**Available Commands:**\n"
                f"💰 `!bank earn` - Earn money with daily rewards\n"
                f"💸 `!bank transfer <amount> <recipient>` - Transfer money to another user\n"
                f"💵 `!bank deposit <amount>` - Add pocket money to your account\n"
                f"🏧 `!bank withdraw <amount>` - Withdraw money from your account\n"
                f"🎲 `!bank gamble <amount>` - Gamble for a chance to win big\n"
                f"🦹 `!bank steal <user>` - Attempt to steal pocket money from another user\n"
                f"📄 `!bank loan <amount>` - Request a loan (requires admin approval)\n"
                f"🔄 `!bank history` - View your transaction history"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use !bank <command> for more details.")
        await ctx.send(embed=embed)
        return

    if action == "deposit":
        if len(args) < 1:
            await ctx.send("❌ Usage: !bank deposit <amount>")
            return
        try:
            deposit_amount = Decimal(args[0])  # Convert deposit amount to Decimal
            if deposit_amount <= 0 or deposit_amount > pocket:
                raise ValueError
        except (ValueError, ArithmeticError):
            await ctx.send(embed=discord.Embed(
                title="❌ Invalid Deposit Amount",
                description=f"Enter an amount between $0.01 and {format_money(pocket)}.",
                color=discord.Color.red()
            ))
            return

        # Update the user's balance and pocket
        cursor.execute("UPDATE users SET pocket = pocket - %s, balance = balance + %s WHERE user_id = %s",
                       (deposit_amount, deposit_amount, ctx.author.id))
        db.commit()

        new_balance = balance + deposit_amount
        new_pocket = pocket - deposit_amount

        await ctx.send(embed=discord.Embed(
            title="💵 Deposit Successful",
            description=(
                f"You deposited **{format_money(deposit_amount)}** to your bank.\n"
                f"💳 **New Bank Balance:** {format_money(new_balance)}\n"
                f"🪙 **Remaining Pocket Money:** {format_money(new_pocket)}"
            ),
            color=discord.Color.green()
        ))

        # Log the transaction
        cursor.execute(
            """
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (%s, 'deposit', %s, 'User deposited money')
            """,
            (ctx.author.id, deposit_amount)
        )
        db.commit()
        return

    if action == "earn":
        now = t.time()
        if ctx.author.id in daily_cooldowns and now - daily_cooldowns[ctx.author.id] < 86400:
            time_left = int(86400 - (now - daily_cooldowns[ctx.author.id]))
            hours, remainder = divmod(time_left, 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.send(embed=discord.Embed(
                title="⏳ Already Claimed",
                description=f"You've already claimed your daily reward! Come back in {hours}h {minutes}m {seconds}s.",
                color=discord.Color.orange()
            ))
            return

        daily_reward = Decimal(100)  # Use Decimal for consistency
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (daily_reward, ctx.author.id))
        db.commit()
        daily_cooldowns[ctx.author.id] = now

        await ctx.send(embed=discord.Embed(
            title="🎉 Daily Reward Claimed",
            description=f"You've earned **{format_money(daily_reward)}**! Check your balance for updates.",
            color=discord.Color.green()
        ))
        return

    elif action.lower() == "gamble":
        if len(args) < 1:
            await ctx.send("❌ Usage: !bank gamble <amount>")
            return
        try:
            gamble_amount = float(args[0])
            if gamble_amount <= 0 or gamble_amount > balance:
                raise ValueError
        except ValueError:
            await ctx.send(embed=discord.Embed(
                title="❌ Invalid Gamble Amount",
                description=f"Please enter an amount between $0.01 and ${balance:.2f}.",
                color=discord.Color.red()
            ))
            return

        # Gambling probabilities and rewards
        outcomes = [
            (0.5, 0),          # 50% chance to lose
            (0.3, 1.5),        # 30% chance to win 1.5x
            (0.15, 2),         # 15% chance to win 2x
            (0.05, 5),         # 5% chance to win 5x
        ]
        outcome = random.choices(outcomes, weights=[50, 30, 15, 5], k=1)[0]

        if outcome[1] == 0:
            cursor.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (gamble_amount, ctx.author.id))
            db.commit()
            await ctx.send(embed=discord.Embed(
                title="😢 You Lost!",
                description=f"You gambled **${gamble_amount:.2f}** and lost it all.",
                color=discord.Color.red()
            ))
        else:
            winnings = gamble_amount * outcome[1]
            cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (winnings, ctx.author.id))
            db.commit()
            await ctx.send(embed=discord.Embed(
                title="🎉 You Won!",
                description=f"You gambled **${gamble_amount:.2f}** and won **${winnings:.2f}**!",
                color=discord.Color.green()
            ))

    elif action.lower() == "steal":
        if len(args) < 1:
            await ctx.send("❌ Usage: !bank steal <user>")
            return
        try:
            target_id = int(args[0].strip("<@!>"))
        except ValueError:
            await ctx.send("❌ Invalid user format! Mention the user you want to steal from.")
            return

        now = t.time()
        if ctx.author.id in steal_cooldowns and now - steal_cooldowns[ctx.author.id] < 3600:
            time_left = int(3600 - (now - steal_cooldowns[ctx.author.id]))
            minutes, seconds = divmod(time_left, 60)
            await ctx.send(embed=discord.Embed(
                title="⏳ Steal Cooldown",
                description=f"You can steal again in {minutes}m {seconds}s.",
                color=discord.Color.orange()
            ))
            return

        cursor.execute("SELECT pocket FROM users WHERE user_id = %s", (target_id,))
        target = cursor.fetchone()
        if not target or target[0] <= 0:
            await ctx.send(embed=discord.Embed(
                title="❌ Steal Failed",
                description="The target has no pocket money to steal.",
                color=discord.Color.red()
            ))
            return

        steal_success = random.random() < 0.5  # 50% chance to succeed
        if steal_success:
            stolen_amount = random.randint(1, min(100, target[0]))  # Steal up to $100 or the target's pocket money
            cursor.execute("UPDATE users SET pocket = pocket - %s WHERE user_id = %s", (stolen_amount, target_id))
            cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (stolen_amount, ctx.author.id))
            db.commit()

            steal_cooldowns[ctx.author.id] = now
            await ctx.send(embed=discord.Embed(
                title="🦹 Steal Successful",
                description=f"You stole **${stolen_amount:.2f}** from <@{target_id}>!",
                color=discord.Color.green()
            ))
        else:
            penalty = random.randint(1, 50)  # Lose up to $50
            cursor.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (penalty, ctx.author.id))
            cursor.execute("UPDATE users SET pocket = pocket + %s WHERE user_id = %s", (penalty, target_id))
            db.commit()

            steal_cooldowns[ctx.author.id] = now
            await ctx.send(embed=discord.Embed(
                title="🚨 Steal Failed!",
                description=f"You got caught trying to steal from <@{target_id}> and lost **${penalty:.2f}**!",
                color=discord.Color.red()
            ))

    elif action.lower() == "withdraw":
        if len(args) < 1:
            await ctx.send("❌ Usage: !bank withdraw <amount>")
            return
        try:
            withdraw_amount = float(args[0])
            if withdraw_amount <= 0 or withdraw_amount > balance:
                raise ValueError
        except ValueError:
            await ctx.send(embed=discord.Embed(
                title="❌ Invalid Withdrawal Amount",
                description=f"Please enter an amount between $0.01 and ${balance:.2f}.",
                color=discord.Color.red()
            ))
            return

        cursor.execute("UPDATE users SET balance = balance - %s, pocket = pocket + %s WHERE user_id = %s",
                       (withdraw_amount, withdraw_amount, ctx.author.id))
        db.commit()

        await ctx.send(embed=discord.Embed(
            title="🏧 Withdrawal Successful",
            description=f"You have withdrawn **${withdraw_amount:.2f}**. Check your pocket for the funds.",
            color=discord.Color.green()
        ))

        cursor.execute(
            """
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (%s, 'withdraw', %s, 'User withdrew money')
            """,
            (ctx.author.id, withdraw_amount)
        )
        db.commit()

    elif action.lower() == "loan":
        if len(args) < 1:
            await ctx.send("❌ Usage: !bank loan <amount>")
            return
        try:
            loan_amount = float(args[0])
            if loan_amount <= 0 or loan_amount > 10000:
                raise ValueError
        except ValueError:
            await ctx.send("❌ Invalid loan amount! Maximum loan amount is $10000.")
            return

        await ctx.send(embed=discord.Embed(
            title="⌛ Loan Request Sent",
            description="Your loan request has been sent to the admin for approval. You will be notified soon.",
            color=discord.Color.orange()
        ))

        admin_user = await bot.fetch_user(ADMIN_USER_ID)
        await admin_user.send(embed=discord.Embed(
            title="📩 Loan Approval Request",
            description=f"User <@{ctx.author.id}> has requested a loan of **${loan_amount:.2f}**.\n"
                        f"Use the buttons below to approve or reject the request.",
            color=discord.Color.blue(),
        ), view=LoanApprovalView(ctx.author.id, loan_amount))

    elif action.lower() == "transfer":
        if len(args) < 2:
            await ctx.send("❌ Usage: !bank transfer <amount> <recipient>")
            return
        try:
            amount = float(args[0])
            recipient_id = int(args[1].strip("<@!>"))
        except ValueError:
            await ctx.send("❌ Invalid amount or recipient format!")
            return

        if balance < amount:
            await ctx.send(embed=discord.Embed(
                title="❌ Insufficient Funds",
                description="You don't have enough money for this transfer.",
                color=discord.Color.red(),
            ))
            return

        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (recipient_id,))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amount, ctx.author.id))
            cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, recipient_id))
            db.commit()

            await ctx.send(embed=discord.Embed(
                title="✅ Transfer Successful",
                description=f"You have transferred **${amount:.2f}** to <@{recipient_id}>.",
                color=discord.Color.green(),
            ))
        else:
            await ctx.send(embed=discord.Embed(
                title="❌ User Not Found",
                description="The recipient does not have a bank account.",
                color=discord.Color.red(),
            ))

    elif action.lower() == "history":
        cursor.execute("SELECT type, amount, description, timestamp FROM transactions WHERE user_id = %s ORDER BY timestamp DESC LIMIT 10", (ctx.author.id,))
        transactions = cursor.fetchall()

        if transactions:
            description = "\n".join([
                f"**{type.title()}**: ${amount:.2f} - {desc} *(on {timestamp.strftime('%Y-%m-%d %H:%M:%S')})*"
                for type, amount, desc, timestamp in transactions
            ])
            await ctx.send(embed=discord.Embed(
                title="📜 Transaction History",
                description=description,
                color=discord.Color.blue(),
            ))
        else:
            await ctx.send(embed=discord.Embed(
                title="📜 No Transactions Found",
                description="You don't have any transaction history yet.",
                color=discord.Color.blue(),
            ))

        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (deposit_amount, ctx.author.id))
        db.commit()

        await ctx.send(embed=discord.Embed(
            title="💵 Deposit Successful",
            description=f"You have successfully deposited **${deposit_amount:.2f}** to your account.",
            color=discord.Color.green()
        ))

        cursor.execute(
            """
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (%s, 'deposit', %s, 'User deposited money')
            """,
            (ctx.author.id, deposit_amount)
        )
        db.commit()
#HPUR COMMAND
@bot.command(name='hpur')
async def history_purchase(ctx, member_id: int):
    """Displays previous tickets for a specific member."""
    try:
        # Fetch tickets from the database for the given member_id
        cursor.execute("""
            SELECT ticket_number, passenger_name, age, passport_number, departure_country, 
                   destination_country, flight_type, price, arrival_date, flight_number, 
                   seat_number, grptno, purchase_time 
            FROM tickets WHERE member_id = %s
        """, (member_id,))
        tickets = cursor.fetchall()

        if not tickets:
            # If no tickets are found for the member_id
            await ctx.send(embed=discord.Embed(
                title="📜 Ticket History",
                description=f"No tickets found for member ID: `{member_id}`.",
                color=discord.Color.orange()
            ))
            return

        # Create an embed to display ticket history
        embed = discord.Embed(
            title="🎫 Ticket History",
            description=f"Showing all tickets for member ID: `{member_id}`",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://emoji.gg/assets/emoji/airplane.gif")  # Airplane emoji thumbnail

        # Format and add ticket details
        for i, ticket in enumerate(tickets, start=1):
            ticket_number, passenger_name, age, passport_number, departure_country, destination_country, flight_type, price, arrival_date, flight_number, seat_number, grptno, purchase_time = ticket

            embed.add_field(
                name=f"🎟️ Ticket {i}: {ticket_number}",
                value=(
                    f"👤 **Passenger Name**: {passenger_name}\n"
                    f"📅 **Age**: {age}\n"
                    f"🛂 **Passport**: {passport_number}\n"
                    f"🛫 **Departure**: {departure_country}\n"
                    f"🛬 **Destination**: {destination_country}\n"
                    f"💺 **Flight Type**: {flight_type.capitalize()}\n"
                    f"💰 **Price**: ${price:.2f}\n"
                    f"📅 **Arrival Date**: {arrival_date}\n"
                    f"✈️ **Flight Number**: {flight_number}\n"
                    f"🪑 **Seat**: {seat_number}\n"
                    f"👥 **Group Number**: {grptno if grptno != 'NILL' else 'N/A'}\n"
                    f"🕒 **Purchase Time**: {purchase_time}\n"
                ),
                inline=False
            )

        embed.set_footer(text="Thanks for flying with us! ✈️")
        await ctx.send(embed=embed)

    except Exception as e:
        # Handle any errors during execution
        await ctx.send(embed=discord.Embed(
            title="❌ Error",
            description=f"An error occurred while retrieving ticket history: `{e}`",
            color=discord.Color.red()
        ))

#INQUIRY CMD
@bot.command(name='inquiry')
async def inquiry_command(ctx):
    """Inquiry command."""
    embed = discord.Embed(
        title="🔍 Flight Inquiry",
        description="Select what you'd like to inquire about:",
        color=discord.Color.gold()
    )
    view = discord.ui.View()

    delay_button = discord.ui.Button(label="Flight Delay", style=discord.ButtonStyle.primary, emoji="⏱️")
    arrival_button = discord.ui.Button(label="Arrival Time", style=discord.ButtonStyle.primary, emoji="🛬")
    terminal_button = discord.ui.Button(label="Terminal Info", style=discord.ButtonStyle.primary, emoji="🏢")

    # Function to create a modal and fetch data based on the user's selection
    async def fetch_flight_info(interaction, info_type):
        # Modal to prompt for flight number
        class FlightNumberModal(discord.ui.Modal, title="Enter Flight Number"):
            flight_number = discord.ui.TextInput(
                label="✈️ Flight Number",
                placeholder="Enter the flight number (e.g., AC2442)"
            )

            async def on_submit(self, interaction):
                flight_num = self.flight_number.value.upper()

                try:
                    # Execute the query to fetch flight information
                    cursor.execute("SELECT delay, terminal FROM flight WHERE flight_number = %s", (flight_num,))
                    result = cursor.fetchone()
                    cursor.fetchall()  # Ensure all results are consumed

                    if result:
                        delay, terminal = result
                        description = ""
                        if info_type == "delay":
                            description = f"⏱️ Delay: {delay} minutes"

                        # Create an embed with the requested flight information
                        response_embed = discord.Embed(
                            title=f"Flight Information for {flight_num}",
                            color=discord.Color.blue()
                        )
                        response_embed.add_field(name="🛩️ Flight Number", value=flight_num, inline=False)

                        # Display specific information based on the selected inquiry type
                        if info_type == "delay":
                            response_embed.add_field(name="⏱️ Delay", value=f"{delay} minutes", inline=True)
                        elif info_type == "arrival":
                            description = "Estimated arrival time may vary due to the delay. Please check with the airline website for real-time updates."
                            response_embed.add_field(name="🛬 Arrival Info", value=description, inline=True)
                        elif info_type == "terminal":
                            response_embed.add_field(name="🏢 Terminal", value=f"Terminal {terminal}", inline=True)

                        await interaction.response.send_message(embed=response_embed)
                    else:
                        # Handle case where the flight number isn't found
                        await interaction.response.send_message(
                            "❌ No information found for the specified flight number. Please try again with a valid number.",
                            ephemeral=True
                        )

                except mysql.connector.Error as err:
                    await interaction.response.send_message(
                        f"⚠️ An error occurred while retrieving flight information: {err}",
                        ephemeral=True
                    )

        # Show the modal to the user
        await interaction.response.send_modal(FlightNumberModal())

    # Button callbacks to display modal and fetch specific information
    delay_button.callback = lambda interaction: fetch_flight_info(interaction, "delay")
    arrival_button.callback = lambda interaction: fetch_flight_info(interaction, "arrival")
    terminal_button.callback = lambda interaction: fetch_flight_info(interaction, "terminal")

    view.add_item(delay_button)
    view.add_item(arrival_button)
    view.add_item(terminal_button)

    await ctx.send(embed=embed, view=view)


#SUPPORT CMD
@bot.command(name='support')
async def support_command(ctx):
    """Support command."""
    embed = discord.Embed(
        title="🛠️ Support Options",
        description="Choose an option for assistance with your booking:",
        color=discord.Color.orange()
    )
    view = discord.ui.View()

    # Define support buttons
    luggage_button = discord.ui.Button(label="Luggage Delay", style=discord.ButtonStyle.primary, emoji="📦")
    missing_items_button = discord.ui.Button(label="Missing Items", style=discord.ButtonStyle.primary, emoji="🔍")
    postpone_button = discord.ui.Button(label="Ticket Postpone", style=discord.ButtonStyle.primary, emoji="🗓️")

    # Callback for Luggage Delay - Prompt for Flight Number and fetch delay
    async def luggage_callback(interaction):
        class FlightNumberModal(discord.ui.Modal, title="Enter Flight Number for Luggage Delay"):
            flight_number = discord.ui.TextInput(
                label="✈️ Flight Number",
                placeholder="Enter the flight number (e.g., AC2442)"
            )

            async def on_submit(self, interaction):
                flight_num = self.flight_number.value.upper()

                try:
                    # Fetch delay info based on flight number
                    cursor.execute("SELECT delay FROM flight WHERE flight_number = %s", (flight_num,))
                    result = cursor.fetchone()
                    cursor.fetchall()  # Ensure the result set is fully consumed

                    if result:
                        delay = result[0]
                        response_embed = discord.Embed(
                            title=f"Luggage Delay Information for Flight {flight_num}",
                            description=f"⏱️ Estimated delay: **{delay} minutes**",
                            color=discord.Color.blue()
                        )
                        await interaction.response.send_message(embed=response_embed)
                    else:
                        await interaction.response.send_message(
                            "❌ No delay information found for the specified flight number. Please try again with a valid number.",
                            ephemeral=True
                        )

                except mysql.connector.Error as err:
                    await interaction.response.send_message(
                        f"⚠️ An error occurred while retrieving luggage delay information: {err}",
                        ephemeral=True
                    )

        await interaction.response.send_modal(FlightNumberModal())

    # Callback for Missing Items - Display contact information
    async def missing_items_callback(interaction):
        response_embed = discord.Embed(
            title="Missing Items Support",
            description="For assistance with missing items, please contact airline support at **1800-0120-XXX**.",
            color=discord.Color.red()
        )
        response_embed.set_footer(text="We apologize for the inconvenience and appreciate your patience.")
        await interaction.response.send_message(embed=response_embed)

    # Callback for Ticket Postpone - Prompt for Ticket Number, Name, and New Arrival Date
    async def postpone_callback(interaction):
        class TicketPostponeModal(discord.ui.Modal, title="Ticket Postpone Information"):
            ticket_number = discord.ui.TextInput(
                label="🎟️ Ticket Number",
                placeholder="Enter your ticket number"
            )
            passenger_name = discord.ui.TextInput(
                label="👤 Passenger Name",
                placeholder="Enter your full name"
            )
            new_arrival_date = discord.ui.TextInput(
                label="📅 New Arrival Date",
                placeholder="Enter new arrival date (YYYY-MM-DD)"
            )

            async def on_submit(self, interaction):
                ticket_num = self.ticket_number.value.upper()
                name = self.passenger_name.value.upper()
                new_date = self.new_arrival_date.value

                try:
                    # Check if ticket number and name match in the tickets table
                    cursor.execute("SELECT arrival_date FROM tickets WHERE ticket_number = %s AND passenger_name = %s", 
                                   (ticket_num, name))
                    result = cursor.fetchone()
                    cursor.fetchall()  # Ensure the result set is fully consumed

                    if result:
                        # Update the arrival date in the database
                        cursor.execute("UPDATE tickets SET arrival_date = %s WHERE ticket_number = %s AND passenger_name = %s",
                                       (new_date, ticket_num, name))
                        db.commit()

                        response_embed = discord.Embed(
                            title="Ticket Postponement Confirmation",
                            description=f"🎟️ Your arrival date has been updated successfully!",
                            color=discord.Color.green()
                        )
                        response_embed.add_field(name="Ticket Number", value=ticket_num, inline=False)
                        response_embed.add_field(name="New Arrival Date", value=new_date, inline=False)
                        await interaction.response.send_message(embed=response_embed)
                    else:
                        await interaction.response.send_message(
                            "❌ Ticket number and name do not match our records. Please try again.",
                            ephemeral=True
                        )

                except mysql.connector.Error as err:
                    await interaction.response.send_message(
                        f"⚠️ An error occurred while processing ticket postponement: {err}",
                        ephemeral=True
                    )

        await interaction.response.send_modal(TicketPostponeModal())

    # Set callbacks to each button
    luggage_button.callback = luggage_callback
    missing_items_button.callback = missing_items_callback
    postpone_button.callback = postpone_callback

    # Add buttons to view and send the embed
    view.add_item(luggage_button)
    view.add_item(missing_items_button)
    view.add_item(postpone_button)

    await ctx.send(embed=embed, view=view)
#SHOWTB_TICKETS CMD
@bot.command(name='showtb_tickets')
@commands.has_role(...)
async def show_table_command(ctx):
    """Shows the "tickets" table from the Database."""
    cursor.execute("SELECT * FROM tickets")
    results = cursor.fetchall()
    if results:
        embeds = []
        current_embed = discord.Embed(
            title="📋 **Booked Tickets**",
            description="Here’s the list of all booked tickets:",
            color=discord.Color.green()
        )

        current_embed_length = len(current_embed.description)  # Track the current length of the embed

        for row in results:
            ticket_number, name, age, passport_number, departure, destination, flight_type, price, arrival_date, flight_number, seat_number, purchase_time, grptno, member_id = row

            # Organize ticket information with proper spacing
            ticket_info = (
                f"🎟️ **Ticket Number**\n***{ticket_number}***\n\n"

                f"👤 **Passenger Name : **     `{name}`\n"
                f"🛂 **Passport No. :   **        `{passport_number}`\n"
                f"💺 **Flight Type :    **         `{flight_type.capitalize()}`\n\n"

                f"🛫 **Departure : **           `{departure}`\n"
                f"🛬 **Destination : **         `{destination}`\n"
                f"💵 **Price : **               `${price:.2f}`\n\n"

                f"📅 **Arrival Date : **\n`{arrival_date}`\n"
                f"✈️ **Flight Number : **\n`{flight_number}`\n"
                f"💺 **Seat Number : **\n`{seat_number}`\n"
                f"🕒 **Purchase Time (IST) : **\n`{purchase_time}`\n"
                f"👥 **Group Number : **\n`{grptno}`\n"
                f"🪪 **Member ID : **\n`{member_id}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )

            # Check if adding the current ticket's info exceeds the limit
            if current_embed_length + len(ticket_info) + 1024 > 6000:  # Leave room for title, footer, etc.
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title="📋 **Booked Tickets** (Continued)",
                    description="Continued from previous message...",
                    color=discord.Color.green()
                )
                current_embed_length = len(current_embed.description)

            # Add ticket information to the current embed
            current_embed.add_field(name=f"**Ticket #{ticket_number}**", value=ticket_info, inline=False)
            current_embed_length += len(ticket_info)

        # Add the final embed if there's any remaining content
        if current_embed.fields:
            embeds.append(current_embed)

        # Send the embeds
        for embed in embeds:
            await ctx.send(embed=embed)
    else:
        await ctx.send("ℹ️ No tickets booked yet.")

@bot.command(name="cancel")
async def cancel_command(ctx):
    """Cancels tickets and processes refunds if applicable."""
    try:
        # Embed with "Cancel Ticket" button
        embed = discord.Embed(
            title="🎫 Cancel Flight Ticket",
            description="Click the button below to enter your details for ticket cancellation.",
            color=discord.Color.red(),
        )
        view = discord.ui.View(timeout=180)  # 3-minute timeout for the view
        cancel_button = discord.ui.Button(label="Cancel Ticket", style=discord.ButtonStyle.danger)

        async def cancel_ticket_callback(interaction: discord.Interaction):
            # Modal for entering flight details
            class CancelTicketModal(discord.ui.Modal):
                def __init__(self):
                    super().__init__(title="Cancel Ticket")
                    self.flight_number = discord.ui.TextInput(
                        label="Flight Number",
                        style=discord.TextStyle.short,
                        placeholder="Enter your flight number (e.g., AA123)"
                    )
                    self.ticket_number = discord.ui.TextInput(
                        label="Ticket Number",
                        style=discord.TextStyle.short,
                        placeholder="Enter your ticket number (e.g., 456789)"
                    )
                    self.seat_number = discord.ui.TextInput(
                        label="Seat Number",
                        style=discord.TextStyle.short,
                        placeholder="Enter your seat number (e.g., 12A)"
                    )
                    self.passenger_name = discord.ui.TextInput(
                        label="Passenger Name",
                        style=discord.TextStyle.short,
                        placeholder="Enter your full name"
                    )
                    self.add_item(self.flight_number)
                    self.add_item(self.ticket_number)
                    self.add_item(self.seat_number)
                    self.add_item(self.passenger_name)

                async def on_submit(self, interaction: discord.Interaction):
                    flight_number = self.flight_number.value.strip().upper()
                    ticket_number = self.ticket_number.value.strip().upper()
                    seat_number = self.seat_number.value.strip().upper()
                    passenger_name = self.passenger_name.value.strip().upper()

                    try:
                        # Query to verify ticket details
                        cursor.execute(
                            """
                            SELECT price, arrival_date, purchase_time, member_id 
                            FROM tickets 
                            WHERE flight_number = %s 
                            AND ticket_number = %s 
                            AND seat_number = %s 
                            AND LOWER(passenger_name) = LOWER(%s)
                            """,
                            (flight_number, ticket_number, seat_number, passenger_name)
                        )
                        result = cursor.fetchone()

                        if result:
                            price, arrival_date_db, purchase_time_str, member_id = result
                            arrival_date = datetime.combine(arrival_date_db, time(23, 59))  # Assuming end of the day
                            ist_timezone = pytz.timezone("Asia/Kolkata")
                            arrival_date = ist_timezone.localize(arrival_date)
                            current_time = datetime.now(ist_timezone)
                            time_difference = arrival_date - current_time

                            refund_message = ""
                            refund_embed_color = discord.Color.green()  # Default to green for refundable

                            if time_difference < timedelta(hours=8):
                                # No refund for cancellations within 8 hours
                                refund_message = (
                                    "⛔ **No Refund Available**\n"
                                    "You are cancelling your ticket within 8 hours of arrival. **No refund** will be issued."
                                )
                                refund_embed_color = discord.Color.red()
                                refund_amount = 0
                            else:
                                # Refund processing
                                refund_message = (
                                    "💸 **Refund Available**\n"
                                    "You are cancelling your ticket with more than 8 hours remaining until arrival. "
                                    "Your **refund of ${:.2f}** will be processed shortly."
                                ).format(price)
                                refund_amount = price

                                # Update user balance in the database
                                cursor.execute(
                                    "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                                    (refund_amount, member_id),
                                )
                                db.commit()

                            # Delete ticket record
                            cursor.execute(
                                "DELETE FROM tickets WHERE ticket_number = %s",
                                (ticket_number,)
                            )
                            db.commit()

                            # Confirmation message
                            confirmation_embed = discord.Embed(
                                title="✅ Ticket Cancelled Successfully!",
                                description=(
                                    f"🎟️ **Ticket Number**: `{ticket_number}`\n"
                                    f"✈️ **Flight Number**: `{flight_number}`\n"
                                    f"🪑 **Seat Number**: `{seat_number}`\n"
                                    f"👤 **Passenger Name**: `{passenger_name}`\n\n"
                                    f"{refund_message}"
                                ),
                                color=refund_embed_color,
                            )
                            confirmation_embed.set_footer(text="Thank you for choosing our service!")
                            await interaction.response.send_message(embed=confirmation_embed)
                        else:
                            # Error message if no matching ticket was found
                            error_embed = discord.Embed(
                                title="❌ Ticket Not Found",
                                description="No ticket found with the provided details. Please check and try again.",
                                color=discord.Color.red(),
                            )
                            await interaction.response.send_message(embed=error_embed)
                    except Exception as e:
                        # Error handling
                        error_embed = discord.Embed(
                            title="⚠️ Database Error",
                            description=f"An error occurred while processing your request: {e}",
                            color=discord.Color.red(),
                        )
                        await interaction.response.send_message(embed=error_embed)

            # Show the modal
            await interaction.response.send_modal(CancelTicketModal())

        # Attach the callback to the button
        cancel_button.callback = cancel_ticket_callback
        view.add_item(cancel_button)

        # Send the embed with the cancel button
        await ctx.send(embed=embed, view=view)
    except Exception as e:
        # Error handling
        print(f"Error in cancel_command: {e}")
        await ctx.send("⚠️ An error occurred while processing the cancel request. Please try again later.")
#LOOKUP CMD
# Lookup Modal for gathering ticket information
class LookupModal(Modal):
    def __init__(self):
        super().__init__(title="🎟️ Ticket Lookup")

        # Add text inputs for ticket number and name
        self.ticket_number = TextInput(label="🎫 Ticket Number", placeholder="Enter your ticket number", required=True)
        self.name = TextInput(label="👤 Your Name", placeholder="Enter your name", required=True)

        # Add text inputs to the modal
        self.add_item(self.ticket_number)
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        # Fetch input values
        ticket_number = self.ticket_number.value
        name = self.name.value

        # Check if 'name' is indeed a column; adjust the query accordingly.
        # Ensure this query aligns with your actual table schema.
        query = """
        SELECT ticket_number, passenger_name, age, passport_number, departure_country, 
               destination_country, flight_type, price, arrival_date, flight_number, 
               seat_number
        FROM tickets WHERE ticket_number = %s AND passenger_name = %s
        """

        try:
            cursor.execute(query, (ticket_number, name))
            result = cursor.fetchone()

            if result:
                # Unpack the result for readability
                (ticket_number, passenger_name, age, passport_number, departure_country, 
                 destination_country, flight_type, price, arrival_date, flight_number, 
                 seat_number) = result

                # Format ticket details in an embed
                embed = discord.Embed(
                    title="🎟️ Ticket Details",
                    description="Here are the details of your ticket:",
                    color=discord.Color.green()
                )
                embed.add_field(name="👤 Passenger Name", value=passenger_name, inline=False)
                embed.add_field(name="📅 Age", value=str(age), inline=False)
                embed.add_field(name="🛂 Passport Number", value=passport_number, inline=False)
                embed.add_field(name="🛫 Departure", value=departure_country, inline=True)
                embed.add_field(name="🛬 Destination", value=destination_country, inline=True)
                embed.add_field(name="💺 Flight Type", value=flight_type.upper(), inline=False)
                embed.add_field(name="💵 Price", value=f"${price:.2f}", inline=False)
                embed.add_field(name="🎟️ Ticket Number", value=ticket_number, inline=False)
                embed.add_field(name="📅 Arrival Date", value=arrival_date.strftime('%Y-%m-%d'), inline=False)
                embed.add_field(name="✈️ Flight Number", value=flight_number, inline=False)
                embed.add_field(name="🪑 Seat Number", value=seat_number, inline=False)

                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                # If no match found, send an error message
                await interaction.response.send_message(
                    "⚠️ No matching ticket found. Please ensure your ticket number and name are correct.",
                    ephemeral=True
                )

        except mysql.connector.Error as err:
            await interaction.response.send_message(
                f"⚠️ Database error: {err}",
                ephemeral=True
            )

# View with a button that triggers the modal
class LookupView(View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="👀 Lookup Ticket", style=discord.ButtonStyle.primary)
    async def open_lookup_modal(self, interaction: discord.Interaction, button: Button):
        # Show the LookupModal when the button is clicked
        await interaction.response.send_modal(LookupModal())

# Command to initiate the lookup process with a single button
@bot.command(name="lookup")
async def lookup(ctx):
    """Command to initiate the lookup process with a button."""
    # Send a message with the button
    view = LookupView()
    await ctx.send("⬇️ Click the button below to lookup your ticket:", view=view)

#SQL CMD
MAX_DISCORD_CHAR_LIMIT = 2000  # Discord's message character limit
MAX_EMBED_FIELD_CHAR_LIMIT = 1024  # Discord's max character limit per field
MAX_EMBED_TOTAL_CHAR_LIMIT = 6000  # Discord's max character limit per embed

# Helper function to split content into multiple messages
def split_content(content, max_length=MAX_DISCORD_CHAR_LIMIT):
    return textwrap.wrap(content, max_length, replace_whitespace=False)

# Helper function to format results from the "tickets" table
def format_tickets_embed(headers, rows):
    embeds = []
    embed = discord.Embed(
        title="🎟️ Tickets Table Results",
        description="Here are the results from the `tickets` table.",
        color=discord.Color.blue()
    )
    total_length = 0

    for row in rows:
        ticket_info = ""
        for header, value in zip(headers, row):
            if header == "ticket_id":
                ticket_info += f"**🎫 Ticket ID:** {value}\n"
            elif header == "user_name":
                ticket_info += f"**👤 User:** {value}\n"
            elif header == "issue":
                ticket_info += f"**📋 Issue:** {value}\n"
            elif header == "status":
                status_emoji = "✅" if value == "resolved" else "❗"
                ticket_info += f"**{status_emoji} Status:** {value}\n"
            else:
                ticket_info += f"**{header}:** {value}\n"

        if total_length + len(ticket_info) > MAX_EMBED_TOTAL_CHAR_LIMIT:
            embeds.append(embed)
            embed = discord.Embed(color=discord.Color.blue())
            total_length = 0

        embed.add_field(name="Ticket", value=ticket_info, inline=False)
        total_length += len(ticket_info)

    embeds.append(embed)
    return embeds

# Helper function to format general SQL query results
def format_query_result_embed(headers, rows):
    embeds = []
    embed = discord.Embed(
        title="📊 Query Results",
        description="Here are the results from your query.",
        color=discord.Color.green()
    )
    total_length = 0

    for row in rows:
        row_info = ""
        for header, value in zip(headers, row):
            row_info += f"**{header}:** {value}\n"

        if total_length + len(row_info) > MAX_EMBED_TOTAL_CHAR_LIMIT:
            embeds.append(embed)
            embed = discord.Embed(color=discord.Color.green())
            total_length = 0

        embed.add_field(name="Result", value=row_info, inline=False)
        total_length += len(row_info)

    embeds.append(embed)
    return embeds

@bot.command(name="sql")
@commands.has_role(...)  # Restrict to the bot owner
async def sql(ctx, *, query: str):
    """Executes a SQL query and returns the result in a styled embed. Restricted to Admin role."""

    await ctx.send("Connected to the MySQL database successfully.")

    try:
        # Check if the query is empty or invalid
        if not query.strip():
            await ctx.send("⚠️ Error: The SQL query cannot be empty.")
            return

        # Basic check to prevent "table" from being used as a table name
        if "from table" in query.lower():
            await ctx.send("⚠️ Error: 'table' is a reserved keyword in SQL. Please specify a valid table name in your query.")
            return

        # Execute the query
        cursor.execute(query)
        
        # Handle "SHOW" commands to display tables and databases
        if query.strip().lower().startswith("show"):
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]
            result_content = "\n".join([", ".join(map(str, row)) for row in rows])

            if len(result_content) > MAX_DISCORD_CHAR_LIMIT:
                # Split long output into multiple messages without using embeds
                chunks = split_content(result_content)
                for i, chunk in enumerate(chunks, start=1):
                    await ctx.send(f"📄 {query} Result - Part {i}:\n```{chunk}```")
            else:
                await ctx.send(f"📄 {query} Result:\n```{result_content}```")

        # Handle SELECT queries separately
        elif query.strip().lower().startswith("select"):
            rows = cursor.fetchall()
            if rows:
                headers = [desc[0] for desc in cursor.description]
                if query.strip().lower() == "select * from tickets":
                    embeds = format_tickets_embed(headers, rows)
                else:
                    embeds = format_query_result_embed(headers, rows)
                
                for embed in embeds:
                    await ctx.send(embed=embed)
            else:
                await ctx.send(embed=discord.Embed(
                    title="✅ Query Executed Successfully",
                    description="No results to display.",
                    color=discord.Color.green()
                ))

        # Handle other non-SELECT commands
        else:
            cursor.fetchall()  # Ensure all results are read before commit
            db.commit()
            await ctx.send(embed=discord.Embed(
                title="✅ Query Executed Successfully",
                description="Your SQL query was executed and committed.",
                color=discord.Color.green()
            ))

    except mysql.connector.ProgrammingError as e:
        error_embed = discord.Embed(
            title="⚠️ SQL Syntax Error",
            description=(
                f"SQL syntax error occurred in the following query:\n**{query}**\n\n"
                f"Error details:\n**{e}**"
            ),
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
#EASTER EGGS
@bot.command()
async def calc(ctx, *, expression: str = None):
    """
    A calculator that supports both basic and scientific calculations.
    Example usage: !calc 2 + 2, !calc sin(90), or !calc sqrt(16)
    """
    if not expression:
        embed = discord.Embed(
            title="🧮 Calculator",
            description=(
                "**You can use this command to perform basic or scientific calculations.**\n\n"
                "📌 **Basic Examples:**\n"
                "`!calc 2 + 2`\n"
                "`!calc (3 * 5) / 2`\n\n"
                "📌 **Scientific Examples:**\n"
                "`!calc sin(90)`\n"
                "`!calc sqrt(25)`\n"
                "`!calc log(10)`"
            ),
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🛠 Supported Operations",
            value=(
                "**Basic Operations:** `+`, `-`, `*`, `/`, `**` (power), `()`\n"
                "**Scientific Functions:**\n"
                "`sin(x)`, `cos(x)`, `tan(x)`, `sqrt(x)` (square root), `log(x)` (logarithm), `abs(x)`\n"
                "**Constants:** `pi`, `e`\n"
                "**Additional:** `floor(x)`, `ceil(x)`, `degrees(x)`, `radians(x)`"
            ),
            inline=False
        )
        embed.set_footer(text="Tip: Use !calc followed by your expression!")
        await ctx.send(embed=embed)
        return

    try:
        # Define safe evaluation environment
        allowed_functions = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "log": math.log,
            "abs": abs,
            "round": round,
            "pow": pow,
            "floor": math.floor,
            "ceil": math.ceil,
            "degrees": math.degrees,
            "radians": math.radians,
            "pi": math.pi,
            "e": math.e,
        }
        # Evaluate the expression
        result = eval(expression, {"__builtins__": None}, allowed_functions)

        # Prepare success embed
        embed = discord.Embed(
            title="🧮 Calculator Result",
            color=discord.Color.green()
        )
        embed.add_field(name="📥 Input", value=f"`{expression}`", inline=False)
        embed.add_field(name="📤 Result", value=f"`{result}`", inline=False)
        await ctx.send(embed=embed)

    except Exception as e:
        # Prepare error embed
        embed = discord.Embed(
            title="❌ Calculation Error",
            description=f"Something went wrong while processing your expression:\n`{expression}`\n\n**Error:** `{str(e)}`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
#nsfw stuff and self boasting
#nsfw cmd
@bot.command(name='nig')
async def joker_gif(ctx):
    """NSFW joke."""
    await ctx.send(f"I like sri ram, raghav and v hemanth oiled up")
    embed = discord.Embed(title="💦")
    # Replace the URL with a direct link to a GIF. You might need to use an actual GIF link here.
    embed.set_image(url="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExejBtOWVlaW13MWhvZTM4bTJ6MTRvdzdvdGFoZ2U0N29saXA3Y3JjdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/XCKQMMZWkzs51TEEgz/giphy-downsized-large.gif")
    await ctx.send(embed=embed)
#self boasting cmd
@bot.command(name='hob')
async def joker_gif(ctx):
    """Self boasting."""
    await ctx.send(f"""Well, let me tell ya ’bout hobt0, one of the finest moderators you’ll find ridin' the virtual plains over on Zeqa Minecraft. This here feller knows them server rules better than a cowboy knows his trusty steed. Folks around the server got a deep respect for hobt0, not just ‘cause they keep order like a true sheriff, but ‘cause they’re fair as a prairie sunrise, always lookin’ out for everyone from the greenest newcomer to the most seasoned players.

Hobt0's got a knack for defusin’ trouble faster than a rattlesnake strikes, and if there’s an issue brewin’ in the chat or on the fields, they’re the first to saddle up and ride to set things right. Ain’t just about keepin' folks in line, neither—hobt0's as friendly and helpful as a good neighbor, makin' sure everyone feels welcome and knows where to start if they're lost.

Reckon folks’d say Zeqa Minecraft wouldn't be quite the same without ‘em.""")
    embed = discord.Embed(title="🔥")
    embed.set_image(url="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3Fqc2wwaHRuYTRibWp3c2NhMzBnZXVhNm80OTV2YzI5M2o2cGc1MCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/TIcqppfavXjhqxhUVV/giphy.gif")
    await ctx.send(embed=embed)
#ty cmd
@bot.command(name='ty')
async def ty(ctx):
    """Sends a thank you message."""
    await ctx.send(f"You're very welcome! I'm glad to assist you.")

#about cmd
@bot.command(name="about")
async def about_command(ctx):
    """About the bot and developer."""
    # Creating an embed for the bot information
    embed = discord.Embed(
        title="📢 About SQL Discord Bot",
        description="A powerful bot designed to interact with MySQL databases directly from Discord! Perfect for admins. 💻📊",
        color=discord.Color.blue()
    )
    embed.add_field(name="Features ✨", value=(
        "• **Execute SQL Queries:** Run `SELECT`, `INSERT`, `UPDATE`, `DELETE`, etc. from Discord! 📄\n"
        "• **Rich Embeds:** Display results in rich, readable formats. 🖌️\n"
        "• **Admin-Only Access:** Restricted to specified admins. 🔒\n"
        "• **Status & Credits:** Shows bot status and creator credits. 🎨"
    ), inline=False)
    embed.add_field(name="👨‍💻 Built By", value="Bala Aditya and Sri Ram", inline=False)
    embed.set_footer(text="Type !helpme to see available commands!")

    await ctx.send(embed=embed)


#ticket delete
class DeleteTicketModal(ui.Modal):
    def __init__(self):
        super().__init__(title="🗑️ Delete Ticket(s)")

        # Define the modal's input field
        self.channel_ids = ui.TextInput(
            label="📝 Enter Channel IDs",
            placeholder="Enter channel IDs separated by commas",
            style=discord.TextStyle.short,
            required=True,
            max_length=500,
        )
        self.add_item(self.channel_ids)

    async def on_submit(self, interaction: discord.Interaction):
        # Split the channel IDs by commas and strip whitespace
        channel_ids = self.channel_ids.value.split(',')
        failed_deletions = []
        success_count = 0

        for channel_id in channel_ids:
            channel_id = channel_id.strip()  # Remove any surrounding whitespace
            try:
                # Attempt to fetch and delete each channel
                channel = await bot.fetch_channel(int(channel_id))
                await channel.delete()
                success_count += 1
            except Exception:
                failed_deletions.append(channel_id)

        # Create a summary embed for the deletions
        embed = discord.Embed(
            title="🗑️ Ticket Deletion Summary",
            color=discord.Color.red()
        )

        if success_count > 0:
            embed.add_field(
                name="✅ Successful Deletions",
                value=f"{success_count} channel(s) deleted successfully! 🎉",
                inline=False
            )

        if failed_deletions:
            embed.add_field(
                name="⚠️ Failed Deletions",
                value=f"Couldn't delete the following channels: {', '.join(failed_deletions)}. ❌",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class DeleteTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DeleteButton())

class DeleteButton(ui.Button):
    def __init__(self):
        super().__init__(label="🗑️ Delete Tickets", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        # Display the modal when the button is clicked
        await interaction.response.send_modal(DeleteTicketModal())

# Command to open the delete ticket embed with a button
@bot.command()
async def del_ticket(ctx):
    """Sends an embed with a button to open the delete ticket modal."""
    # Create an embed to confirm the action
    embed = discord.Embed(
        title="🗑️ Ticket Deletion",
        description="Press the button below and enter the channel IDs you want to delete, separated by commas.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Be careful, this action is irreversible! 🔥")

    # Send the embed with the delete button
    await ctx.send(embed=embed, view=DeleteTicketView())
# About command
@bot.tree.command(name="about", description="Learn more about this bot and its creator.")
async def about(interaction: discord.Interaction):
  
    # Create an embed for the about information
    embed = discord.Embed(
        title="🤖 About This Bot",
        description="This bot is designed to make your experience smoother and more enjoyable! It features a variety of commands to assist you.",
        color=discord.Color.blue()
    )
    embed.add_field(name="👤 Creator", value="Bala Aditya", inline=True)
    embed.add_field(name="🔧 Purpose", value="To automate tasks and provide helpful information.", inline=False)
    embed.set_footer(text="Thank you for using the bot!")

    # Send the embed in response to the slash command
    await interaction.response.send_message(embed=embed, ephemeral=True)  # Only visible to the user who used the command

# Create the /developerbadge slash command
@bot.event
async def on_ready():
    # Sync the commands with Discord
    await bot.tree.sync()
    print(f'We have logged in as {bot.user}')

@bot.tree.command(name="developerbadge", description="Get information about the Discord Developer Badge")
async def developerbadge(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Discord Developer Badge",
        description=(
            "The Discord Developer Badge is awarded to developers who own a verified Discord bot. "
            "To earn the badge, developers must have created a bot that has been verified by Discord."
        ),
        color=discord.Color.blue()  # Discord's primary color
    )
    embed.set_footer(text="Learn more at https://support.discord.com")

    await interaction.response.send_message(embed=embed)



#LISTCMD 
@bot.command(name="listcmds")
async def list_commands(ctx):
    """Lists all the commands, splitting the output if needed."""
    list_embed = discord.Embed(
        title="📜 List of Commands",
        description="Here are all the available commands:",
        color=discord.Color.purple()
    )
    
    command_text = ""
    # Loop through all commands in the bot and add them to the command_text
    for command in bot.commands:
        command_info = f"🔹 **!{command.name}**: {command.help if command.help else 'No description available'}\n"
        command_text += command_info
    
    # Handle cases where the footer text is None
    footer_text = list_embed.footer.text if list_embed.footer.text else ""
    max_length = 2000 - len(list_embed.title) - len(list_embed.description) - len(footer_text) - 10  # Allow space for other parts of the embed
    
    # Check if the text exceeds Discord's 2000 character limit and split it
    if len(command_text) > max_length:
        # Split the command list into multiple parts
        parts = [command_text[i:i+max_length] for i in range(0, len(command_text), max_length)]
        
        # Send the embed with each part
        for part in parts:
            list_embed.description = part
            await ctx.send(embed=list_embed)
    else:
        # If the text fits, send it in one message
        list_embed.description = command_text
        await ctx.send(embed=list_embed)

    list_embed.set_footer(text="⚙️ Built by aditya._0 | Use !help <command> for more info on each command.")

#STATUS CMD
# The target channel ID where the message will be sent
TARGET_CHANNEL_ID = <channel_id>

# Define the modal for title and body input
class StatusModal(discord.ui.Modal, title="Status :"):
    # Define the TextInput fields for title and body
    title = discord.ui.TextInput(label="Enter Title", placeholder="Enter your title here", max_length=100)
    body = discord.ui.TextInput(label="Enter Body", style=discord.TextStyle.paragraph, placeholder="Enter your message body here", max_length=2000)

    async def on_submit(self, interaction: discord.Interaction):
        # Access the title and body directly, no need for .value
        title = self.title
        body = self.body

        # Create the embed with the provided title and body
        embed = discord.Embed(
            title=title,  # Title from the input field
            description=body,  # Body from the input field
            color=discord.Color.blurple()  # Embed color
        )

        # Add an emoji to the footer for some flair
        embed.set_footer(text="Status created by bot 🤖", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")

        # Send the embed to the target channel
        target_channel = interaction.guild.get_channel(TARGET_CHANNEL_ID)
        await target_channel.send(embed=embed)

        # Confirm the submission to the user
        await interaction.response.send_message(f"Your status **'{title}'** has been posted successfully in the channel!", ephemeral=True)

# Define the button view to trigger the modal
class StatusButton(discord.ui.View):
    @discord.ui.button(label="Create Status 📄", style=discord.ButtonStyle.primary)
    async def create_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Show the modal when the button is clicked
        await interaction.response.send_modal(StatusModal())

# Command to send the initial message with the button
@bot.command(name="status")
async def status(ctx):
    """Status command."""
    view = StatusButton()  # Create an instance of the button view
    await ctx.send("Click the button below to create a status message 📝:", view=view)

#showtb_flight CMD
# Command to show flight table data
@bot.command(name='showtb_flight')
async def show_flight_table(ctx):
    try:
        # Use the pre-defined db_config
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)

        # Query to fetch all records from the "flight" table
        cursor.execute("SELECT * FROM flight")
        records = cursor.fetchall()

        # Split the records into chunks for Discord message limit
        chunk_size = 20  # You can adjust this depending on the content
        record_chunks = [records[i:i + chunk_size] for i in range(0, len(records), chunk_size)]

        # Prepare and send messages
        for chunk in record_chunks:
            embed = Embed(title="✈️ **Flight Details** ✈️", description="Here are all the flight records:", color=0x1abc9c)
            for record in chunk:
                embed.add_field(
                    name=f"🌍 **{record['place']}**",
                    value=(
                        f"**Flight Number:** {record['flight_number']}\n"
                        f"**Delay:** {record['delay']} minutes\n"
                        f"**Terminal:** {record['terminal']}"
                    ),
                    inline=False
                )

            await ctx.send(embed=embed)
        
        # Close the cursor and connection
        cursor.close()
        db.close()
    
    except mysql.connector.Error as err:
        print(f"Error connecting to the database: {err}")
        await ctx.send("There was an error fetching flight data. Please try again later.")

#LOG CMD
LOG_CHANNEL_ID = ...  # Channel ID where logs will be sent
log_active = False  # Variable to track if logging is active
end_logging_time = None  # Variable to store the end time for logging

@bot.command(name="log")
async def start_logging(ctx):
    """Starts the logging process with a modal to input the duration."""

    embed = discord.Embed(
        title="📝 Logging Setup",
        description="Click the button below to enter the logging duration.",
        color=discord.Color.blue()
    )
    view = discord.ui.View(timeout=None)
    duration_button = discord.ui.Button(label="Enter Duration (mins)", style=discord.ButtonStyle.primary)

    async def duration_button_callback(interaction: discord.Interaction):
        
        class DurationModal(discord.ui.Modal, title="Enter Logging Duration"):
            duration = discord.ui.TextInput(label="⏳ Duration (in minutes)", placeholder="Enter a number of minutes")

            async def on_submit(self, interaction: discord.Interaction):
                global log_active, end_logging_time

                try:
                    duration_minutes = int(self.duration.value)
                    if duration_minutes <= 0:
                        await interaction.response.send_message("⚠️ Please enter a positive number.", ephemeral=True)
                        return

                    # Set the logging state and end time
                    log_active = True
                    end_logging_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
                    await interaction.response.send_message(f"📝 Logging started for {duration_minutes} minutes!", ephemeral=True)
                    bot.loop.create_task(stop_logging_after_duration())

                except ValueError:
                    await interaction.response.send_message("⚠️ Please enter a valid integer.", ephemeral=True)

        await interaction.response.send_modal(DurationModal())

    duration_button.callback = duration_button_callback
    view.add_item(duration_button)
    await ctx.send(embed=embed, view=view)

async def stop_logging_after_duration():
    """Stops logging after the specified duration."""
    global log_active, end_logging_time

    while datetime.utcnow() < end_logging_time:
        await asyncio.sleep(10)  # Check every 10 seconds to reduce unnecessary resource usage

    log_active = False
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    await log_channel.send("🛑 Logging has ended.")

@bot.event
async def on_message_edit(before, after):
    """Logs edited messages."""
    global log_active
    if log_active and before.content != after.content:
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=before.author.mention, inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Before", value=before.content or "N/A", inline=False)
        embed.add_field(name="After", value=after.content or "N/A", inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    """Logs deleted messages."""
    global log_active
    if log_active:
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=message.author.mention, inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Content", value=message.content or "N/A", inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    """Logs member joins and leaves in voice channels."""
    global log_active
    if log_active:
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        
        if before.channel is None and after.channel is not None:
            # User joined a voice channel
            embed = discord.Embed(
                title="🔊 Voice Channel Join",
                description=f"{member.mention} joined {after.channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            await log_channel.send(embed=embed)

        elif before.channel is not None and after.channel is None:
            # User left a voice channel
            embed = discord.Embed(
                title="🔇 Voice Channel Leave",
                description=f"{member.mention} left {before.channel.mention}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            await log_channel.send(embed=embed)

        elif before.channel != after.channel:
            # User switched voice channels
            embed = discord.Embed(
                title="🔄 Voice Channel Switch",
                description=f"{member.mention} moved from {before.channel.mention} to {after.channel.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            await log_channel.send(embed=embed)

#STOPLOG CMD
@bot.command(name="stoplog")
async def stop_logging(ctx):
    """Stops the logging process manually."""

    global log_active
    if log_active:
        log_active = False
        embed = discord.Embed(
            title="🛑 Logging Stopped",
            description="Logging has been stopped manually.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        await ctx.send(embed=embed)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(embed=embed)
    else:
        embed = discord.Embed(
            title="⚠️ Logging Not Active",
            description="Logging is not currently active.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        await ctx.send(embed=embed)
        
#BACKUPS
OWNER_ID = ...  # Replace with your actual user ID
BACKUP_CHANNEL_ID = <channel_id>  # Replace with the desired channel ID for backgrounds

# Ensure the messages table exists
def ensure_messages_table():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            guild_id BIGINT NOT NULL,
            channel_id BIGINT NOT NULL,
            author_id BIGINT NOT NULL,
            content TEXT,
            timestamp DATETIME NOT NULL
        )
    """)
    db.close()

# Command: !backupbg
@bot.command()
async def backupbg(ctx):
    """Checks messages in the specific channel and updates the database with new backgrounds."""
    if ctx.author.id != OWNER_ID:
        await ctx.send(embed=discord.Embed(
            title="⛔ Access Denied",
            description="You don't have permission to run this command.",
            color=discord.Color.red()
        ))
        return

    BACKGROUND_IMAGES_CHANNEL_ID = <channel_id>  # Background images channel ID

    # Connect to the database
    db = connect_db()
    cursor = db.cursor()

    # Create the backgrounds table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backgrounds (
            id INT AUTO_INCREMENT PRIMARY KEY,
            link VARCHAR(2083) NOT NULL,
            UNIQUE (link(255))
        )
    """)

    # Get the specific background images channel
    bg_channel = bot.get_channel(BACKGROUND_IMAGES_CHANNEL_ID)
    if not bg_channel:
        await ctx.send(embed=discord.Embed(
            title="⚠️ Error",
            description="Background channel not found.",
            color=discord.Color.orange()
        ))
        return

    # Process messages in the background channel
    added_count = 0
    async for message in bg_channel.history(limit=None):
        for attachment in message.attachments:
            if attachment.url:  # Ensure the attachment has a valid URL
                try:
                    # Insert the link into the database if it doesn't already exist
                    cursor.execute("INSERT IGNORE INTO backgrounds (link) VALUES (%s)", (attachment.url,))
                    if cursor.rowcount > 0:  # If a new row was added
                        added_count += 1
                except Exception as e:
                    print(f"Error inserting background: {e}")

    db.commit()
    db.close()

    await ctx.send(embed=discord.Embed(
        title="✅ Backgrounds Updated",
        description=f"{added_count} new background(s) have been added to the database.",
        color=discord.Color.green()
    ))
# Command: !backupbglist
@bot.command()
async def backupbglist(ctx):
    """Shows a list of available background IDs."""
    # Connect to the database
    db = connect_db()
    cursor = db.cursor()

    # Fetch the background IDs and links
    cursor.execute("SELECT id, link FROM backgrounds")
    rows = cursor.fetchall()
    db.close()

    if not rows:
        await ctx.send(embed=discord.Embed(
            title="⚠️ No Backgrounds Found",
            description="The database does not contain any backgrounds.",
            color=discord.Color.orange()
        ))
        return

    # Display the list of backgrounds
    embed = discord.Embed(
        title="🖼️ Available Backgrounds",
        description="Here are the backgrounds available for backups:",
        color=discord.Color.blue()
    )
    for row in rows:
        embed.add_field(name=f"🔹 ID: {row[0]}", value=row[1], inline=False)

    await ctx.send(embed=embed)
@bot.command()
async def backup(ctx: commands.Context, background_id: int):
    """Generates a backup with buttons for channels and sends a summary along with the bot's code."""
    if ctx.author.id != OWNER_ID:
        await ctx.send(embed=discord.Embed(
            title="⛔ Access Denied",
            description="You don't have permission to run this command.",
            color=discord.Color.red()
        ))
        return

    # Connect to the database
    db = connect_db()
    cursor = db.cursor()

    # Fetch the background link
    cursor.execute("SELECT link FROM backgrounds WHERE id = %s", (background_id,))
    result = cursor.fetchone()
    db.close()

    if not result:
        await ctx.send(embed=discord.Embed(
            title="⚠️ Invalid Background ID",
            description="The specified background ID was not found in the database.",
            color=discord.Color.orange()
        ))
        return

    background_link: str = result[0]

    # Generate the HTML backup file
    folder_path: str = "backups"
    os.makedirs(folder_path, exist_ok=True)
    timestamp: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name: str = f"backup_{ctx.guild.name}_{timestamp}.html"
    file_path: str = f"{folder_path}/{file_name}"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backup of {ctx.guild.name}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: url('{background_link}') no-repeat center center fixed;
            background-size: cover;
            color: #ffffff;
        }}
        .container {{
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background-color: rgba(47, 49, 54, 0.9);
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
        }}
        .channel-btn {{
            display: block;
            margin: 10px 0;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.6);
            border: none;
            border-radius: 8px;
            color: #ffffff;
            font-size: 16px;
            cursor: pointer;
            text-align: left;
        }}
        .channel-btn:hover {{
            background-color: rgba(0, 0, 0, 0.8);
        }}
        .messages {{
            display: none;
            margin-top: 20px;
        }}
        .message {{
            margin-bottom: 10px;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.6);
            border-radius: 8px;
        }}
        .author {{
            font-weight: bold;
            color: #ffcc00;
        }}
        .content {{
            margin-top: 5px;
        }}
    </style>
    <script>
        function toggleMessages(channelId) {{
            const messages = document.querySelectorAll('.messages');
            messages.forEach(msg => msg.style.display = 'none');
            document.getElementById(channelId).style.display = 'block';
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>📁 Backup: {ctx.guild.name}</h1>
        <p>Backup generated on: {timestamp}</p>
        <h2>Channels:</h2>
""")

        for channel in ctx.guild.text_channels:
            f.write(f"""
        <button class="channel-btn" onclick="toggleMessages('channel-{channel.id}')">{channel.name}</button>
        <div id="channel-{channel.id}" class="messages">
            <h3>Messages in #{channel.name}</h3>
""")
            async for message in channel.history(limit=None):
                text_color_class: str = "dark-bg" if message.author.color == discord.Color.dark_gray() else "light-bg"
                f.write(f"""
            <div class="message {text_color_class}">
                <div class="author">{message.author.display_name}</div>
                <div class="content">{message.content or "(No content)"}</div>
            </div>
""")
            f.write("</div>")

        f.write("""
    </div>
</body>
</html>
""")

    # Send the backup summary in the channel
    await ctx.send(embed=discord.Embed(
        title="✅ Backup Complete",
        description=f"The server backup has been completed successfully!\n\n"
                    f"📂 **File Info**\nFile Name: {file_name}\n📤 **Uploading...**\n"
                    f"Sending the backup file to the designated channel.\n\n"
                    f"Backup initiated by {ctx.author.mention} • {timestamp}",
        color=discord.Color.green()
    ))

    # Send the backup file and bot's code to the backup channel
    backup_channel = bot.get_channel(BACKUP_CHANNEL_ID)
    if backup_channel:
        # Send the backup file
        await backup_channel.send(
            content=f"🗂️ Backup generated using Background ID {background_id}:",
            file=discord.File(file_path),
        )

        # Send the bot's code
        code_file_path: str = "bot_code.py"
        with open(code_file_path, "w", encoding="utf-8") as code_file:
            code_file.write(open(__file__, "r").read())
        
        await backup_channel.send(
            content="📄 Bot's code has been attached:",
            file=discord.File(code_file_path),
        )

        # Clean up temporary files
        os.remove(file_path)
        os.remove(code_file_path)

#LEVELS
@bot.event
async def on_ready():
    """Triggered when the bot is ready."""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_levels (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id BIGINT NOT NULL,
        username VARCHAR(255),
        xp INT DEFAULT 0,
        level INT DEFAULT 1
    )
    """)
    db.commit()
    print(f"Logged in as {bot.user}. Database table `user_levels` is ready.")


@bot.event
async def on_message(message):
    """Track XP, levels, and assign roles on each message."""
    if message.author.bot:
        return  # Ignore bot messages

    # Ignore bot command messages (messages starting with "!")
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    user_id = message.author.id
    username = message.author.name
    guild = message.guild
    member = guild.get_member(user_id)

    # Fetch or insert user data
    cursor.execute("SELECT xp, level FROM user_levels WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if not result:
        # User not found, insert new record
        cursor.execute("INSERT INTO user_levels (user_id, username) VALUES (%s, %s)", (user_id, username))
        db.commit()
        xp, level = 0, 1
    else:
        xp, level = result

    # Increment XP and calculate level-up
    xp += 10  # XP per message
    xp_for_next_level = floor(100 * (level ** 1.5))

    leveled_up = False
    if xp >= xp_for_next_level:
        level += 1
        leveled_up = True
        xp -= xp_for_next_level  # Carry over remaining XP

        # Notify about level-up
        await message.channel.send(
            embed=discord.Embed(
                title=f"🎉 Level Up! {username}",
                description=f"**You've reached Level {level}!** Keep it up!",
                color=discord.Color.green()
            )
        )

    # Update database with the new XP and level
    cursor.execute(
        "UPDATE user_levels SET xp = %s, level = %s WHERE user_id = %s",
        (xp, level, user_id)
    )
    db.commit()

    # Assign roles based on levels
    roles_to_assign = {
        5: 1312269980447801414,
        15: 1312270064606511195,
        30: 1312270149407080458,
        60: 1312270201378832454,
        90: 1312270275144060990,
        95: 1312270336003149864,
        100: 1312270383470088212,
    }

    if leveled_up:
        for required_level, role_id in roles_to_assign.items():
            role = guild.get_role(role_id)
            if role and level >= required_level and role not in member.roles:
                try:
                    await member.add_roles(role)
                    await message.channel.send(
                        embed=discord.Embed(
                            title="🎭 Role Assigned!",
                            description=f"**{member.mention}**, you've been granted the **{role.name}** role for reaching Level {required_level}!",
                            color=discord.Color.gold()
                        )
                    )
                except discord.DiscordException as e:
                    print(f"Error assigning role {role.name} to {member.name}: {e}")
                    await message.channel.send(
                        embed=discord.Embed(
                            title="Error Assigning Role",
                            description=f"Could not assign the role **{role.name}** to {member.mention} due to an error.",
                            color=discord.Color.red()
                        )
                    )

    await bot.process_commands(message)
    await bot.process_commands(message)

#LEVELS SHI
@bot.command(name="lvl")
async def level_command(ctx, member: discord.Member = None):
    """Display a user's level."""
    member = member or ctx.author
    cursor.execute("SELECT xp, level FROM user_levels WHERE user_id = %s", (member.id,))
    result = cursor.fetchone()

    if result:
        xp, level = result
        xp_for_next_level = floor(100 * (level ** 1.5))
        progress = (xp / xp_for_next_level) * 100

        embed = discord.Embed(
            title=f"📈 Level Stats for {member.name}",
            description="Here are your current stats:",
            color=discord.Color.blue()
        )
        embed.add_field(name="🏅 Level", value=f"{level}", inline=True)
        embed.add_field(name="⚡ XP", value=f"{xp}/{xp_for_next_level} ({progress:.2f}%)", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send(
            embed=discord.Embed(
                title="No Level Data Found",
                description=f"{member.mention} has not started earning XP yet.",
                color=discord.Color.red()
            )
        )


@bot.command(name="lvlupdate")
@commands.has_permissions(administrator=True)  # Restrict to admins only
async def lvlupdate_command(ctx):
    """Check users' levels and assign roles based on their level."""
    roles_to_assign = {
        5: 1312269980447801414,
        15: 1312270064606511195,
        30: 1312270149407080458,
        60: 1312270201378832454,
        90: 1312270275144060990,
        95: 1312270336003149864,
        100: 1312270383470088212,
    }

    guild = ctx.guild

    # Iterate through each member
    for member in guild.members:
        if member.bot:
            continue  # Skip bots

        cursor.execute("SELECT level FROM user_levels WHERE user_id = %s", (member.id,))
        result = cursor.fetchone()

        if result:
            level = result[0]
        else:
            continue  # No level data

        # Assign roles
        for required_level, role_id in roles_to_assign.items():
            role = guild.get_role(role_id)
            if level >= required_level and role and role not in member.roles:
                try:
                    await member.add_roles(role)
                    await ctx.send(
                        embed=discord.Embed(
                            title=f"🎭 Role Assigned to {member.name}",
                            description=f"**{member.name}** has been granted the **{role.name}** role for reaching Level {required_level}.",
                            color=discord.Color.gold()
                        )
                    )
                except discord.DiscordException as e:
                    print(f"Error assigning role {role.name} to {member.name}: {e}")

    await ctx.send("✅ Level check and role assignment completed!")

#PING
# !ping command to check bot's latency
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)  # Convert from seconds to milliseconds
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**Bot Latency:** `{latency} ms`",
        color=discord.Color.green()
    )
    embed.set_footer(text="Ping command executed")
    await ctx.send(embed=embed)

# !pingdb command to check SQL server latency
@bot.command()
async def pingdb(ctx):
    try:
        start_time = t.time()  # Explicitly use the time module
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")  # Simple query to test the connection
        cursor.fetchall()
        cursor.close()
        conn.close()
        end_time = t.time()  # End timer
        db_latency = round((end_time - start_time) * 1000)  # Convert to milliseconds
        embed = discord.Embed(
            title="🗄️ SQL Server Ping",
            description=f"**Database Latency:** `{db_latency} ms`",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Database ping command executed")
        await ctx.send(embed=embed)
    except mysql.connector.Error as e:
        embed = discord.Embed(
            title="⚠️ SQL Server Error",
            description=f"Unable to connect to the SQL server:\n```{str(e)}```",
            color=discord.Color.red()
        )
        embed.set_footer(text="Database ping command failed")
        await ctx.send(embed=embed)

#emoji
@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Create a table for storing emoji data
@bot.event
async def on_connect():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emojis (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            url TEXT NOT NULL
        )
    """)
    db.commit()

# Modal for adding an emoji
class EmojiAddModal(discord.ui.Modal, title="Add a New Emoji"):
    emoji_name = discord.ui.TextInput(label="Emoji Name", placeholder="Enter the emoji name", max_length=255)
    emoji_url = discord.ui.TextInput(label="Emoji URL", placeholder="Enter the emoji URL")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.emoji_name.value.strip()
        url = self.emoji_url.value.strip()

        # Insert emoji into database
        try:
            cursor.execute("INSERT INTO emojis (name, url) VALUES (%s, %s)", (name, url))
            db.commit()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Emoji Added",
                    description=f"Emoji `{name}` added successfully!",
                    color=discord.Color.green()
                )
            )
        except pymysql.IntegrityError:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Duplicate Emoji Name",
                    description=f"An emoji with the name `{name}` already exists.",
                    color=discord.Color.red()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred while adding the emoji: {e}",
                    color=discord.Color.red()
                )
            )

# Button for opening the add emoji modal
class AddEmojiButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Add Emoji", style=discord.ButtonStyle.primary)
    async def add_emoji_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Use a unique custom_id for the button to avoid duplication issues
        button.custom_id = str(uuid.uuid4())  # Generate a unique ID
        await interaction.response.send_modal(EmojiAddModal())

# Command to trigger the add emoji modal
@bot.command(name="emoji")
async def emoji_add_command(ctx):
    view = AddEmojiButton()
    await ctx.send(
        embed=discord.Embed(
            title="Add an Emoji",
            description="Click the button below to add a new emoji.",
            color=discord.Color.blue()
        ),
        view=view
    )

# Slash command to send an emoji by name
@bot.tree.command(name="emoji", description="Send an emoji by its name.")
@app_commands.describe(name="The name of the emoji you want to send.")
async def send_emoji(interaction: discord.Interaction, name: str):
    # Fetch the emoji URL from the database
    cursor.execute("SELECT url FROM emojis WHERE name = %s", (name,))
    result = cursor.fetchone()

    if result:
        url = result[0]
        # Send the emoji as an image
        await interaction.response.send_message(
            embed=discord.Embed(
                color=discord.Color.green()
            ).set_image(url=url)
        )
    else:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Emoji Not Found",
                description=f"No emoji found with the name `{name}`.",
                color=discord.Color.red()
            )
        )

#STUDY
import discord
from discord.ext import commands
import mysql.connector
import random
import difflib

# Database connection configuration
def connect_db():
    return mysql.connector.connect(**db_config)

# Helper function to split text into chunks
def chunk_text(text, limit):
    """
    Splits the text into chunks that fit within the character limit.
    """
    lines = text.split("\n")
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > limit:  # +1 for the newline
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += f"\n{line}"
    
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

# Modal for adding a topic/question
class AddQuestionModal(discord.ui.Modal, title="📝 Add a Topic or Question"):
    topic = discord.ui.TextInput(label="📚 Topic", placeholder="Enter the topic", required=True)
    statement = discord.ui.TextInput(
        label="🖋️ Statement/Question",
        placeholder="Enter a statement or a question",
        style=discord.TextStyle.paragraph,
        required=True
    )
    solution = discord.ui.TextInput(
        label="💡 Answer (for questions only)",
        placeholder="Provide the answer if it's a question",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            conn = connect_db()
            cursor = conn.cursor()

            is_question = "?" in self.statement.value
            solution = self.solution.value if is_question else None

            cursor.execute(
                "INSERT INTO study (topic, statement, solution) VALUES (%s, %s, %s)",
                (self.topic.value, self.statement.value, solution)
            )
            conn.commit()
            cursor.close()
            conn.close()

            await interaction.response.send_message(
                f"✅ Successfully added to topic **{self.topic.value}**!", ephemeral=True
            )
        except mysql.connector.Error as e:
            await interaction.response.send_message(
                f"⚠️ Database error: {str(e)}", ephemeral=True
            )

# Command for interacting with the study assistant
@bot.command()
async def study(ctx, subcommand=None, *, topic=None):
    if subcommand is None:
        embed = discord.Embed(
            title="📚 Study Assistant",
            description="Use the buttons below to interact with the study system!",
            color=discord.Color.gold()
        )
        view = StudyView()
        await ctx.send(embed=embed, view=view)

    elif subcommand.lower() == "test" and topic:
        try:
            conn = connect_db()
            cursor = conn.cursor()

            # Fetch only questions (statements with a question mark)
            cursor.execute(
                "SELECT statement, solution FROM study WHERE topic = %s AND statement LIKE '%?%'",
                (topic,)
            )
            questions = cursor.fetchall()
            cursor.close()
            conn.close()

            if not questions:
                await ctx.send(f"🚫 No questions found for the topic **{topic}**.")
                return

            question = random.choice(questions)
            statement, solution = question

            embed = discord.Embed(
                title=f"📝 Question from: {topic}",
                description=f"❓ {statement}",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Click the button below to answer!")

            view = AnswerView(topic, statement, solution)
            await ctx.send(embed=embed, view=view)
        except mysql.connector.Error as e:
            await ctx.send(f"⚠️ Database error: {str(e)}")

    elif subcommand.lower() == "notes" and topic:
        try:
            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT statement, solution FROM study WHERE topic = %s",
                (topic,)
            )
            entries = cursor.fetchall()
            cursor.close()
            conn.close()

            if not entries:
                await ctx.send(f"🚫 No notes found for the topic **{topic}**.")
                return

            notes = []
            questions = []
            for statement, solution in entries:
                if "?" in statement:
                    questions.append((statement, solution))
                else:
                    notes.append(statement)

            embed_base = discord.Embed(
                title=f"📚 Notes for Topic: {topic}",
                color=discord.Color.green()
            )

            # Prepare and send notes
            if notes:
                notes_content = "\n".join([f"📜 **Note:** {note}" for note in notes])
                note_chunks = chunk_text(notes_content, 1024)
                embed_base.add_field(name="📖 Notes", value=note_chunks[0], inline=False)
                
                for chunk in note_chunks[1:]:
                    embed_part = discord.Embed(
                        description=chunk, 
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed_part)
            else:
                embed_base.add_field(name="📖 Notes", value="No notes available.", inline=False)

            # Prepare and send questions
            if questions:
                questions_content = "\n".join(
                    [f"❓ **Question:** {question}\n💡 **Answer:** {answer if answer else 'No answer provided.'}" for question, answer in questions]
                )
                question_chunks = chunk_text(questions_content, 1024)
                embed_base.add_field(name="🧐 Questions", value=question_chunks[0], inline=False)
                
                for chunk in question_chunks[1:]:
                    embed_part = discord.Embed(
                        description=chunk, 
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed_part)
            else:
                embed_base.add_field(name="🧐 Questions", value="No questions available.", inline=False)

            await ctx.send(embed=embed_base)

        except mysql.connector.Error as e:
            await ctx.send(f"⚠️ Database error: {str(e)}")

# Modal for answering a question
class AnswerModal(discord.ui.Modal, title="✏️ Answer the Question"):
    answer = discord.ui.TextInput(label="💬 Your Answer", placeholder="Type your answer here", required=True)

    def __init__(self, topic, statement, solution):
        super().__init__()
        self.topic = topic
        self.statement = statement
        self.solution = solution

    def calculate_similarity(self, answer, solution):
        similarity_score = difflib.SequenceMatcher(None, answer.lower(), solution.lower()).ratio()
        return similarity_score

    async def on_submit(self, interaction: discord.Interaction):
        similarity_score = self.calculate_similarity(self.answer.value, self.solution)

        threshold = 0.8
        if similarity_score >= threshold:
            result = "🎉 Correct!"
            color = discord.Color.green()
        else:
            result = f"❌ Incorrect. The correct answer was: **{self.solution}**"
            color = discord.Color.red()

        embed = discord.Embed(
            title=result,
            description=f"📝 {self.statement}\n\n**Your Answer:** {self.answer.value}\n**Similarity Score:** {similarity_score:.2f}",
            color=color
        )
        await interaction.response.send_message(embed=embed)

# Button for answering a question
class AnswerButton(discord.ui.Button):
    def __init__(self, topic, statement, solution):
        super().__init__(label="🖊️ Answer", style=discord.ButtonStyle.primary)
        self.topic = topic
        self.statement = statement
        self.solution = solution

    async def callback(self, interaction: discord.Interaction):
        modal = AnswerModal(self.topic, self.statement, self.solution)
        await interaction.response.send_modal(modal)

# View for answering a question
class AnswerView(discord.ui.View):
    def __init__(self, topic, statement, solution):
        super().__init__()
        self.add_item(AnswerButton(topic, statement, solution))

# View for main !study buttons
class StudyView(discord.ui.View):
    @discord.ui.button(label="➕ Add Topic/Question", style=discord.ButtonStyle.primary)
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddQuestionModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🧪 Take a Test", style=discord.ButtonStyle.secondary)
    async def test_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "To test a specific topic, use the command: `!study test <topic>`",
            ephemeral=True
        )

#CONSOLE 

# Ensure only authorized users can run this command
AUTHORIZED_USERS = [...]  # Replace with your Discord user ID

@bot.command()
async def console(ctx, *, command: str):
    """
    Executes a shell command and returns the output.
    """
    if ctx.author.id not in AUTHORIZED_USERS:
        embed = discord.Embed(
            title="⛔ Access Denied",
            description="You are not authorized to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    try:
        # Run the shell command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        # Filter out pip-related notices or other non-critical messages
        output = result.stdout.strip() or "No output."
        error = result.stderr.strip()

        if error:
            output = f"⚠️ **Error:**\n```\n{error}\n```"

        # Embed the result
        embed = discord.Embed(
            title="💻 Console Command Executed",
            description=f"**Command:**\n```\n{command}\n```",
            color=discord.Color.green() if not error else discord.Color.red()
        )
        embed.add_field(name="📤 Output", value=f"```\n{output}\n```", inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Command Execution Failed",
            description=f"An error occurred:\n```\n{str(e)}\n```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
#LOST CONN AUTO RESTARTS
# Global error handler
@bot.event
async def on_error(event_method, *args, **kwargs):
    # Log the error traceback in console
    error_details = traceback.format_exc()
    print(f"Error in {event_method}: {error_details}")

    # Detect MySQL 'Lost connection' error
    if "mysql.connector.errors.OperationalError" in error_details and "Lost connection to MySQL server" in error_details:
        print("Detected MySQL connection loss. Restarting the bot...")
        
        # Restart the bot
        await bot.close()  # Gracefully close the bot
        os.execv(sys.executable, ['python'] + sys.argv)  # Restart the script

#voice memes
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

class AudioModal(discord.ui.Modal, title="Add Meme Audio"):
    name = discord.ui.TextInput(
        label="Audio Name",
        placeholder="Enter the name of the audio",
        max_length=255
    )
    url = discord.ui.TextInput(
        label="Discord Audio Link",
        placeholder="Paste the link to the audio",
        style=discord.TextStyle.long
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Generate a UUID for the audio entry
        audio_id = str(uuid.uuid4())

        try:
            # Insert data into the database
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO meme_audios (id, name, audio_url) VALUES (%s, %s, %s)",
                (audio_id, self.name.value, self.url.value)
            )
            db.commit()
            cursor.close()

            # Confirmation message
            embed = discord.Embed(
                description=f"✅ **Audio '{self.name.value}' has been added successfully!**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except mysql.connector.Error as e:
            # Handle duplicate or other errors
            embed = discord.Embed(
                description=f"❌ **Failed to add audio: {e}**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command(name="vm")
async def vm_add(ctx):
    """
    Sends an embed with a button to open a modal for adding meme audio.
    """
    class AddButton(discord.ui.View):
        @discord.ui.button(label="Add Audio", style=discord.ButtonStyle.primary)
        async def add_audio(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Show the modal when the button is pressed
            await interaction.response.send_modal(AudioModal())

    embed = discord.Embed(
        title="Add Meme Audio",
        description="Click the button below to add a new meme audio.",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed, view=AddButton())

import discord
import aiohttp
import io

@bot.tree.command(name="vm", description="Play a meme audio by name")
async def vm(interaction: discord.Interaction, name: str):
    """
    Searches the database for the given audio name and sends it as an audio attachment.
    """
    await interaction.response.defer()  # Acknowledge the command to prevent timeout

    try:
        # Fetch the audio URL from the database
        cursor = db.cursor()
        cursor.execute("SELECT audio_url FROM meme_audios WHERE name = %s", (name,))
        result = cursor.fetchone()
        cursor.close()

        if not result:
            await interaction.followup.send(f"🔍 No audio found with the name '{name}'.", ephemeral=True)
            return

        audio_url = result[0]

        # Download the audio file
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    # Save the audio file temporarily
                    input_path = f"/tmp/{name}.mp3"  # Use original extension
                    output_path = f"/tmp/{name}.ogg"  # Converted file

                    with open(input_path, "wb") as f:
                        f.write(audio_data)

                    # Convert to .ogg format for Discord playback
                    convert_to_ogg(input_path, output_path)

                    # Read the converted file into memory
                    with open(output_path, "rb") as f:
                        audio_file = io.BytesIO(f.read())
                        audio_file.seek(0)

                    # Send the converted file as an attachment
                    await interaction.followup.send(
                        file=discord.File(audio_file, filename=f"{name}.ogg")
                    )
                else:
                    await interaction.followup.send("❌ Failed to download the audio file.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ An error occurred: {e}", ephemeral=True)

# Helper function to convert MP3 to OGG
def convert_to_ogg(input_path, output_path):
    """
    Converts an audio file to .ogg format using ffmpeg.
    """
    subprocess.run(
        ["ffmpeg", "-i", input_path, "-c:a", "libopus", "-b:a", "64k", output_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

#meme
import discord
from discord import app_commands
from discord.ext import commands
import requests

MEME_API_BASE = "https://meme-api.com/gimme"

async def fetch_meme(endpoint):
    try:
        response = requests.get(endpoint)
        if response.status_code != 200:
            raise Exception("Failed to fetch meme.")
        return response.json()
    except Exception as e:
        return None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    await bot.tree.sync()
    print("Slash commands synced.")

# 1. Random Meme
@bot.tree.command(name="meme", description="Get a random meme!")
async def meme(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(MEME_API_BASE)
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Random Meme"), color=discord.Color.blue())
        embed.set_image(url=meme_data["url"])
        embed.set_footer(text=f"👍 {meme_data.get('ups', 0)} | Subreddit: {meme_data.get('subreddit', 'Unknown')}")
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch a meme.")

# 2. Wholesome Meme
@bot.tree.command(name="wholesome", description="Get a random wholesome meme!")
async def wholesome(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/wholesomememes")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Wholesome Meme"), color=discord.Color.green())
        embed.set_image(url=meme_data["url"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch a wholesome meme.")

# 3. Dank Meme
@bot.tree.command(name="dankmeme", description="Get a random dank meme!")
async def dankmeme(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/dankmemes")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Dank Meme"), color=discord.Color.purple())
        embed.set_image(url=meme_data["url"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch a dank meme.")

# 4. Cat Meme
@bot.tree.command(name="catmeme", description="Get a random cat meme!")
async def catmeme(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/catmemes")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Cat Meme"), color=discord.Color.orange())
        embed.set_image(url=meme_data["url"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch a cat meme.")

# 5. Dog Meme
@bot.tree.command(name="dogmeme", description="Get a random dog meme!")
async def dogmeme(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/dogmemes")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Dog Meme"), color=discord.Color.yellow())
        embed.set_image(url=meme_data["url"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch a dog meme.")

# 6. Relatable Meme
@bot.tree.command(name="relatable", description="Get a random relatable meme!")
async def relatable(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/me_irl")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Relatable Meme"), color=discord.Color.blurple())
        embed.set_image(url=meme_data["url"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch a relatable meme.")

# 7. Programming Meme
@bot.tree.command(name="programmingmeme", description="Get a random programming meme!")
async def programmingmeme(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/ProgrammerHumor")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Programming Meme"), color=discord.Color.teal())
        embed.set_image(url=meme_data["url"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch a programming meme.")

# 8. Spicy Meme
@bot.tree.command(name="spicymeme", description="Get a random spicy meme (NSFW warning)!")
async def spicymeme(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/spicymemes")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Spicy Meme"), color=discord.Color.red())
        embed.set_image(url=meme_data["url"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch a spicy meme.")

# 9. Random Subreddit Meme
@bot.tree.command(name="randomsubreddit", description="Get a meme from a subreddit of your choice!")
async def randomsubreddit(interaction: discord.Interaction, subreddit: str):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/{subreddit}")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", f"Meme from {subreddit}"), color=discord.Color.magenta())
        embed.set_image(url=meme_data["url"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"Failed to fetch a meme from r/{subreddit}.")

# 10. Meme vs Reality (Static Example)
@bot.tree.command(name="memevsreality", description="Get a funny meme vs reality comparison!")
async def memevsreality(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_image = "https://i.imgur.com/exampleMeme.jpg"  # Replace with actual image URL
    reality_image = "https://i.imgur.com/exampleReality.jpg"  # Replace with actual image URL

    embed = discord.Embed(title="Meme vs Reality", color=discord.Color.dark_blue())
    embed.add_field(name="Meme", value="Here's the funny version:", inline=False)
    embed.set_image(url=meme_image)
    embed.add_field(name="Reality", value="And here's the reality:", inline=False)
    embed.set_thumbnail(url=reality_image)

    await interaction.followup.send(embed=embed)

# 11. Custom Meme
# Predefined list of popular meme templates
TEMPLATES = {
    "distracted_boyfriend": "112126428",
    "drake": "181913649",
    "two_buttons": "87743020",
    "change_my_mind": "129242436",
    "gru_plan": "1035805",
    "success_kid": "61544",
    "mocking_spongebob": "102156234",
    "one_does_not_simply": "61579",
    "condescending_wonka": "61582",
    "roll_safe": "89370399",
    "sad_pablo": "80707627",
    "expanding_brain": "93895088",
    "squidward_looking": "157978170",
    "is_this_a_pigeon": "100777631",
    "distracted_cat": "155067746",
    "running_away_balloon": "131940431",
    "surprised_pikachu": "155067746",
    "trade_offer": "24557067",
    "change_my_mind": "129242436",
    "math_lady": "124822590",
    "shut_up_and_take_my_money": "176908",
    "this_is_fine": "91401121",
    "angry_woman_cat": "188390779",
    "finding_neverland": "6235864",
    "philosoraptor": "61516",
    "futurama_fry": "61520",
    "grumpy_cat": "405658",
    "bad_luck_brian": "61585",
}
IMGFLIP_API_USERNAME = "..."  # Replace with your Imgflip username
IMGFLIP_API_PASSWORD = "..."  # Replace with your Imgflip password

@bot.tree.command(name="custommeme", description="Create a custom meme with text!")
async def custommeme(
    interaction: discord.Interaction,
    template_name: str,
    top_text: str,
    bottom_text: str
):
    """Generate a custom meme based on a template and user-provided text."""
    await interaction.response.defer()

    template_id = TEMPLATES.get(template_name.lower())
    if not template_id:
        available_templates = ", ".join(TEMPLATES.keys())
        await interaction.followup.send(
            f"Invalid template name! Available templates: {available_templates}"
        )
        return

    try:
        # Make the POST request to Imgflip API
        response = requests.post(
            "https://api.imgflip.com/caption_image",
            data={
                "template_id": template_id,
                "username": IMGFLIP_API_USERNAME,
                "password": IMGFLIP_API_PASSWORD,
                "text0": top_text,
                "text1": bottom_text,
            }
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                # Embed with the generated meme URL
                embed = discord.Embed(title="Your Custom Meme", color=discord.Color.gold())
                embed.set_image(url=data["data"]["url"])
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"Failed to generate meme: {data.get('error_message', 'Unknown error')}")
        else:
            await interaction.followup.send("Failed to connect to the Imgflip API. Try again later!")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

@custommeme.autocomplete("template_name")
async def template_name_autocomplete(interaction: discord.Interaction, current: str):
    # Filter templates that contain the current input (case-insensitive)
    filtered_templates = [
        app_commands.Choice(name=key, value=key)
        for key in TEMPLATES.keys()
        if current.lower() in key.lower()
    ]

    # Limit the number of choices to 25
    limited_templates = filtered_templates[:25]

    # Return no more than 25 choices
    await interaction.response.autocomplete(limited_templates)

@bot.event
async def on_ready():
    # Sync the slash commands
    try:
        await bot.tree.sync()
        print(f"Logged in as {bot.user}!")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Add autocomplete for template names
@custommeme.autocomplete("template_name")
async def template_name_autocomplete(interaction: discord.Interaction, current: str):
    # Suggest templates that start with the user's input
    return [
        app_commands.Choice(name=key, value=key)
        for key in TEMPLATES.keys()
        if key.startswith(current.lower())
    ]

# 12. Meme Vote
@bot.tree.command(name="memevote", description="Start a meme voting session!")
async def memevote(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(MEME_API_BASE)
    if meme_data:
        embed = discord.Embed(title="Vote on this meme!", description="React with 👍 or 👎", color=discord.Color.green())
        embed.set_image(url=meme_data["url"])
        message = await interaction.followup.send(embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")
    else:
        await interaction.followup.send("Failed to fetch a meme for voting.")

# 13. Gif Meme
GIPHY_API_KEY = "RX8ZvbKQeoBSdWm6BsZmYNNznmObNUHM"  # Replace with your Giphy API Key

@bot.tree.command(name="gifmeme", description="Get a random GIF meme!")
async def gifmeme(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        # Fetch a random GIF from Giphy API
        response = requests.get(
            "https://api.giphy.com/v1/gifs/random",
            params={"tag": "funny", "api_key": GIPHY_API_KEY}
        )
        if response.status_code == 200:
            data = response.json()
            gif_url = data["data"]["images"]["original"]["url"]
            
            # Create and send the embed with the GIF
            embed = discord.Embed(title="Random GIF Meme", color=discord.Color.blue())
            embed.set_image(url=gif_url)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Failed to fetch a GIF meme. Try again later!")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

# 14. Historical Meme
@bot.tree.command(name="historicalmeme", description="Get a random history-themed meme!")
async def historicalmeme(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/HistoryMemes")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Historical Meme"), color=discord.Color.dark_gold())
        embed.set_image(url=meme_data["url"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch a historical meme.")

# 15. Today's Meme
@bot.tree.command(name="todaysmeme", description="Get the top meme of the day!")
async def todaysmeme(interaction: discord.Interaction):
    await interaction.response.defer()
    meme_data = await fetch_meme(f"{MEME_API_BASE}/memes/top")
    if meme_data:
        embed = discord.Embed(title=meme_data.get("title", "Top Meme of the Day"), color=discord.Color.dark_teal())
        embed.set_image(url=meme_data["url"])
        embed.set_footer(text=f"👍 {meme_data.get('ups', 0)} | Subreddit: {meme_data.get('subreddit', 'Unknown')}")
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to fetch the top meme of the day.")



#FUN SHIT
@bot.tree.command(name="whoasked", description="Who asked?")
async def whoasked(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤔 Who Asked?",
        description="Searching... 🔍",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)
    
    # Correct use of datetime module
    await discord.utils.sleep_until(t.datetime.utcnow() + t.timedelta(seconds=2))  # Corrected line
    
    embed.description = "🔎 **Nobody. Absolutely nobody.**"
    await interaction.edit_original_message(embed=embed)

@bot.tree.command(name="sus", description="Determine sus levels!")
async def sus(interaction: discord.Interaction, user: discord.User):
    sus_level = random.randint(70, 100)
    embed = discord.Embed(
        title="🚨 SUS ALERT!",
        description=f"{user.mention} is **{sus_level}% SUS**! 🕵️‍♂️ Eject immediately!",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="crushreveal", description="Reveal someone's crush!")
async def crushreveal(interaction: discord.Interaction):
    random_user = random.choice(interaction.guild.members)
    embed = discord.Embed(
        title="❤️ Secret Crush Revealed!",
        description=f"🚨 **Breaking news**: {interaction.user.mention}’s crush is... {random_user.mention}! 😘",
        color=discord.Color.pink()
    )
    await interaction.response.send_message(embed=embed)
#team list
TEAM_MEMBERS = [
    {"name": "Lorem", "job": "ipsum "},
    {"name": "dolor", "job": "idk"}
]
TEAM_CHANNEL_ID = <channel_id>  # Replace with your team channel ID
@bot.command()
async def team(ctx):
    """Lists the existing team members and their jobs."""
    embed = discord.Embed(
        title="🌟 Team Members",
        description="Here's a list of our amazing team members and the work they do!",
        color=discord.Color.purple(),
    )
    
    # Add each member to the embed
    for member in TEAM_MEMBERS:
        embed.add_field(
            name=f"🧍 {member['name']}",
            value=f"> {member['job']}",
            inline=False
        )

    embed.set_footer(text="Team Information", icon_url=bot.user.avatar.url)

    # Send the embed to the team channel
    team_channel = ctx.guild.get_channel(TEAM_CHANNEL_ID)
    if team_channel:
        await team_channel.send(embed=embed)
        await ctx.send("✅ Team list has been posted in the team channel!")
    else:
        await ctx.send("⚠️ Could not find the team channel. Please check the channel ID.")
#!sync
# Sync command to register slash commands globally
@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx):
    embed = discord.Embed(
        title="🔄 Synchronizing Commands",
        description="Attempting to sync all slash commands...",
        color=discord.Color.blue()
    )
    loading_message = await ctx.send(embed=embed)

    try:
        # Syncing globally
        synced_commands = await bot.tree.sync()
        embed = discord.Embed(
            title="✅ Sync Successful!",
            description=f"**{len(synced_commands)}** commands have been globally synced. 🌍",
            color=discord.Color.green()
        )
        embed.set_footer(text="Slash commands are now available in all servers and DMs.")
    except Exception as e:
        embed = discord.Embed(
            title="❌ Sync Failed!",
            description=f"An error occurred while syncing:\n```{e}```",
            color=discord.Color.red()
        )
        embed.set_footer(text="Please check the error and try again.")

    await loading_message.edit(embed=embed)

# Error handling for non-owners
@sync.error
async def sync_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            title="🚫 Permission Denied",
            description="You do not have permission to use this command. 🔒",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
#RESTART
@bot.command(name='restart')
@commands.has_permissions(administrator=True)  # Restrict to admins only
async def restart_command(ctx, member: discord.Member = None):
    member = member or ctx.author
    """Restart the bot."""
    embed = discord.Embed(
        title="🔄 Bot Restart",
        description="The bot is restarting. Please wait a moment...",
        color=discord.Color.orange(),
    )
    embed.set_footer(text="Initiated by an Administrator")

    restarting_message = await ctx.send(embed=embed)
    
    # Optionally, log the restart in the console
    print("Bot is restarting...")

    # Add a slight delay to allow the message to be seen
    await asyncio.sleep(2)

    # Update the embed to indicate the restart process
    embed = discord.Embed(
        title="🔄 Bot Restart",
        description="The bot has been restarted successfully! 🎉",
        color=discord.Color.green(),
    )
    embed.set_footer(text="Restart completed")
    
    try:
        # Restart the bot process
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        # If something goes wrong, update with an error message
        error_embed = discord.Embed(
            title="❌ Bot Restart Failed",
            description=f"An error occurred while restarting:\n```\n{e}\n```",
            color=discord.Color.red(),
        )
        await restarting_message.edit(embed=error_embed)

#purge cmd
@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, number: int):
    """
    Deletes the specified number of messages in the channel.
    Usage: !purge <number>
    """
    if number <= 0:
        await ctx.send("Please specify a positive number of messages to delete.")
        return

    # Delete the specified number of messages plus the command message itself
    deleted = await ctx.channel.purge(limit=number + 1)
    confirmation_message = await ctx.send(f"✅ Deleted {len(deleted) - 1} messages.")

    # Wait 10 seconds and then delete the confirmation message
    await asyncio.sleep(10)
    await confirmation_message.delete()

    await confirmation_message.delete()

#EMOJIFAKER 2
@bot.command(name="aupdate")
async def aupdate(ctx):
    channel_id = 1314922724782772314  # Replace with your desired channel ID
    conn = None
    cursor = None

    try:
        # Get the channel by ID
        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.send(f"❌ Could not find channel with ID {channel_id}.")
            return

        # Prepare to store extracted emoji data
        emoji_data = []

        # Regex to match custom Discord emojis (e.g., :smile:) and Unicode emojis (e.g., 🙂)
        custom_emoji_pattern = re.compile(r"<:(\w+):(\d+)>")
        unicode_emoji_pattern = re.compile(r"[\U00010000-\U0010FFFF]", flags=re.UNICODE)

        # Asynchronously iterate through the last 100 messages in the specified channel
        async for message in channel.history(limit=100):
            # Check if the message contains custom or unicode emojis
            custom_emojis = custom_emoji_pattern.findall(message.content)
            unicode_emojis = unicode_emoji_pattern.findall(message.content)

            # Extract custom emojis (name and ID)
            for emoji_name, emoji_id in custom_emojis:
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
                emoji_data.append({"name": emoji_name, "url": emoji_url})

            # Extract Unicode emojis and add them with a placeholder URL
            for emoji in unicode_emojis:
                emoji_data.append({"name": emoji, "url": "https://example.com/placeholder.png"})  # Placeholder URL

        if not emoji_data:
            await ctx.send("No valid emoji data found in recent messages.")
            return

        # Update the database with extracted emoji data
        conn = connect_db()
        cursor = conn.cursor()

        for emoji in emoji_data:
            cursor.execute("""
                INSERT INTO custom_emojis (name, url)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE url = VALUES(url)
            """, (emoji["name"], emoji["url"]))

        conn.commit()

        # Create an embed for the success message
        embed = Embed(
            title="✅ Database Updated!",
            description=f"Checked messages in <#{channel_id}> and updated the emoji database.",
            color=0x00FF00
        )
        embed.add_field(name="Total Emojis Updated", value=f"**{len(emoji_data)}**")
        embed.set_footer(text="Emoji Management System")

        await ctx.send(embed=embed)

    except Exception as e:
        # Send error message as an embed
        embed = Embed(
            title="❌ Update Failed!",
            description=f"An error occurred: `{e}`",
            color=0xFF0000
        )
        await ctx.send(embed=embed)

    finally:
        # Only close cursor and connection if they are initialized
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@bot.tree.command(name="a", description="Retrieve the URL of an emoji by its name.")
@app_commands.describe(emoji_name="The name of the emoji to retrieve.")
async def get_emoji(interaction: discord.Interaction, emoji_name: str):
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # Fetch emoji URL from the database
        cursor.execute("SELECT url FROM custom_emojis WHERE name = %s", (emoji_name,))
        result = cursor.fetchone()

        if result:
            # Respond with just the URL (as requested)
            await interaction.response.send_message(result["url"])
        else:
            # Respond with an error embed if the emoji is not found
            embed = discord.Embed(
                title="❓ Emoji Not Found",
                description=f"The emoji `{emoji_name}` could not be found in the database.",
                color=0xFFA500
            )
            embed.set_footer(text="Try adding it with !aupdate!")
            await interaction.response.send_message(embed=embed)

    except Exception as e:
        # Respond with an error embed in case of database issues
        embed = discord.Embed(
            title="❌ Error Fetching Emoji",
            description=f"An error occurred: `{e}`",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed)

    finally:
        cursor.close()
        conn.close()

@bot.event
async def on_ready():
    # Sync the slash commands with Discord when the bot is ready
    await bot.tree.sync()
    print(f"Bot is ready and synced with slash commands!")

@bot.command(name="alist")
async def elist(ctx):
    try:
        # Connect to the database and retrieve the emoji data
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT name, url FROM custom_emojis")
        emojis = cursor.fetchall()

        # Check if there are emojis in the database
        if not emojis:
            await ctx.send("No emojis found in the database.")
            return

        # Create embeds, ensuring there are no more than 25 fields per embed
        embeds = []
        current_embed = Embed(title="Emoji List", description="Here are the emojis in the database:")
        field_count = 0

        for emoji in emojis:
            emoji_name, emoji_url = emoji
            # Add emoji and URL as a field to the embed
            current_embed.add_field(name=emoji_name, value=emoji_url)

            field_count += 1
            # If we exceed 25 fields, create a new embed
            if field_count == 25:
                embeds.append(current_embed)
                current_embed = Embed(title="Emoji List (continued)", description="Continued...")
                field_count = 0

        # Don't forget to append the last embed if there are any fields
        if field_count > 0:
            embeds.append(current_embed)

        # Send all embeds
        for embed in embeds:
            await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Error Fetching Emoji List\nAn error occurred: `{e}`")

    finally:
        # Clean up the database connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#!watch
#!watch
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1
import requests

def downloadsong(song_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(title)s.%(ext)s',
        'restrictfilenames': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{song_name}", download=True)['entries'][0]
        file_name = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        return file_name, info

def add_metadata(file_name, info):
    audio = MP3(file_name, ID3=ID3)

    if audio.tags is None:
        audio.add_tags()

    audio.tags["TIT2"] = TIT2(encoding=3, text=info.get('title', 'Unknown Title'))
    audio.tags["TPE1"] = TPE1(encoding=3, text=info.get('uploader', 'Unknown Artist'))

    if 'thumbnail' in info:
        response = requests.get(info['thumbnail'])
        if response.status_code == 200:
            audio.tags["APIC"] = APIC(
                encoding=3,  # UTF-8
                mime='image/jpeg',
                type=3,  # Cover (front)
                desc='Cover',
                data=response.content,
            )
    audio.save()

@bot.tree.command(name="watch", description="Search and download a song from YouTube")
async def watch(interaction: discord.Interaction, songname: str):
    embed = discord.Embed(
        title="🎵 Searching for Your Song...",
        description=f"Looking up `{songname}`. Please wait a moment! 🔍",
        color=discord.Color.blurple(),
    )
    await interaction.response.send_message(embed=embed)
    
    try:
        # Download the song
        file_name, info = downloadsong(songname)

        # Add metadata
        add_metadata(file_name, info)

        # Prepare a success embed
        success_embed = discord.Embed(
            title="✅ Song Found!",
            description=f"Here is your song: **{info['title']}**",
            color=discord.Color.green(),
        )
        success_embed.add_field(name="Uploader", value=info.get('uploader', 'Unknown'), inline=True)
        success_embed.add_field(name="Duration", value=f"{info['duration'] // 60}:{info['duration'] % 60:02d}", inline=True)

        if 'thumbnail' in info:
            success_embed.set_thumbnail(url=info['thumbnail'])

        # Edit the original message with the success embed
        await interaction.edit_original_response(embed=success_embed, attachments=[discord.File(file_name)])

        # Clean up the file
        os.remove(file_name)

    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Error Occurred",
            description=f"Something went wrong: `{str(e)}`",
            color=discord.Color.red(),
        )
        await interaction.edit_original_response(embed=error_embed)
#GAY METER
@bot.command()
async def gay(ctx, member: discord.Member = None):
    """
    Rates the gayness of a user. 
    If no member is mentioned, it rates the command invoker.
    """
    if member is None:
        member = ctx.author

    # Re-fetch gayness level after potential updates from keywords
    cursor.execute("SELECT gayness FROM gayness_levels WHERE user_id = %s", (member.id,))
    result = cursor.fetchone()

    if result is None:
        # Initialize gayness level if not in the database
        gayness = random.randint(0, 100)
        cursor.execute("INSERT INTO gayness_levels (user_id, gayness) VALUES (%s, %s)", (member.id, gayness))
        db.commit()
    else:
        gayness = result[0]

    # Create the embed message
    embed = discord.Embed(
        title="🌈💋 Gayness Detector 💋🌈",
        description=f"{member.mention}'s gayness level is:",
        color=discord.Color.purple()
    )
    embed.add_field(name="Gayness Level", value=f"👅💖 **{gayness}%** 💖👅", inline=False)

    # Add reactions based on gayness level
    if gayness == 100:
        embed.add_field(
            name="Mocking Message",
            value="🔥🔥 **WOAH!** You're so fabulously gay, you probably glitter in the dark! 🌟✨",
            inline=False
        )
    elif gayness == 0:
        embed.add_field(
            name="Praise Message",
            value="🐺 **ALPHA WOLF!** You're the embodiment of straight dominance. Absolute unit. 💪🦁",
            inline=False
        )
    else:
        embed.set_footer(text="Just having some fun! 😜")

    # Send the embed
    await ctx.send(embed=embed)
#VC SONGS
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
import uuid
import re

# Emojis
LOOP_EMOJI = '<a:LoopEmoji:1321156866151153784>'
PAUSE_EMOJI = '<:pause:1321157139124977728>'
PLAY_EMOJI = '<:play:1321156390676467845>'
STOP_EMOJI = '<a:StopSignEmoji:1321157435624259697>'
SKIP_EMOJI = '<:skip:1321157748502564978>'
QUEUE_EMOJI = '<:queue:1321155867495628871>'
MUSIC_EMOJI = '<a:music:1321155327575719976>'

# Global variables
is_looping = {}
voice_clients = {}
queue = {}
is_playing = {}
current_track = {}
volume_level = {}

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands to Discord.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

class MusicView(discord.ui.View):
    def __init__(self, interaction, guild_id):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.guild_id = guild_id

    @discord.ui.button(label="Pause", emoji=PAUSE_EMOJI, style=discord.ButtonStyle.secondary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = voice_clients.get(self.guild_id)
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message(embed=discord.Embed(description=f"{PAUSE_EMOJI} Music paused.", color=0xFF5733), ephemeral=True)

    @discord.ui.button(label="Resume", emoji=PLAY_EMOJI, style=discord.ButtonStyle.primary)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = voice_clients.get(self.guild_id)
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message(embed=discord.Embed(description=f"{PLAY_EMOJI} Music resumed.", color=0x28A745), ephemeral=True)

    @discord.ui.button(label="Stop", emoji=STOP_EMOJI, style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = voice_clients.get(self.guild_id)
        if vc:
            await cleanup(vc, self.guild_id)
            await interaction.response.send_message(embed=discord.Embed(description=f"{STOP_EMOJI} Music stopped and cleaned up.", color=0xDC3545), ephemeral=True)

    @discord.ui.button(label="Skip", emoji=SKIP_EMOJI, style=discord.ButtonStyle.success)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = voice_clients.get(self.guild_id)
        if not vc or not vc.is_playing():
            await interaction.response.send_message(embed=discord.Embed(description="❌ No song is currently playing to skip.", color=0xDC3545), ephemeral=True)
            return

        is_looping[self.guild_id] = False  # Disable looping when skipping
        vc.stop()
        await interaction.response.send_message(embed=discord.Embed(description=f"{SKIP_EMOJI} Skipping to the next song...", color=0x1DB954), ephemeral=True)

    @discord.ui.button(label="Loop", emoji=LOOP_EMOJI, style=discord.ButtonStyle.secondary)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        global is_looping
        if is_looping.get(self.guild_id, False):
            await interaction.response.send_message(embed=discord.Embed(description=f"{LOOP_EMOJI} This song is already being looped.", color=0xFFC107), ephemeral=True)
        else:
            is_looping[self.guild_id] = True
            await interaction.response.send_message(embed=discord.Embed(description=f"{LOOP_EMOJI} Song looping enabled.", color=0x1DB954), ephemeral=True)

    @discord.ui.button(label="Queue", emoji=QUEUE_EMOJI, style=discord.ButtonStyle.secondary)
    async def queue_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_queue = queue.get(self.guild_id, [])
        if guild_queue:
            embed = discord.Embed(title=f"{QUEUE_EMOJI} Current Queue", color=0x1DB954)
            for i, track in enumerate(guild_queue, start=1):
                embed.add_field(name=f"{i}.", value=track['title'], inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=discord.Embed(description=f"❌ The queue is empty.", color=0xDC3545), ephemeral=True)

async def cleanup(vc, guild_id):
    """Cleanup function to stop playback, disconnect, and remove downloaded files."""
    if vc.is_connected():
        vc.stop()
        await vc.disconnect()

    voice_clients.pop(guild_id, None)
    queue.pop(guild_id, None)
    is_playing.pop(guild_id, None)

    # Remove current track file
    current = current_track.pop(guild_id, None)
    if current and os.path.exists(current['file']):
        os.remove(current['file'])

    # Remove all remaining files for the guild
    files_to_remove = [file for file in os.listdir() if file.startswith(f"{guild_id}_")]
    for file in files_to_remove:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Failed to remove file {file}: {e}")

@bot.tree.command(name="play", description="Play a song by title or YouTube URL.")
@app_commands.describe(title="Title of the song or URL")
async def play(interaction: discord.Interaction, title: str):
    guild_id = interaction.guild_id
    author_voice = interaction.user.voice

    if not author_voice:
        await interaction.response.send_message(embed=discord.Embed(description="❌ You need to join a voice channel first!", color=0xDC3545), ephemeral=True)
        return

    vc = voice_clients.get(guild_id)
    if not vc:
        vc = await author_voice.channel.connect()
        voice_clients[guild_id] = vc

    await interaction.response.defer()

    try:
        song_data = await download_song(title, guild_id)
        queue.setdefault(guild_id, []).append(song_data)

        if not vc.is_playing():
            await play_next_in_queue(vc, guild_id, interaction)
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"✅ **{song_data['title']}** added to the queue.", color=0x1DB954))
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(description=f"❌ Failed to play song: {e}", color=0xDC3545))

async def download_song(title, guild_id):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': f"{guild_id}_{uuid.uuid4()}.%(ext)s"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{title}", download=True)
        audio_info = info['entries'][0]
        audio_file = ydl.prepare_filename(audio_info)
        return {'file': audio_file, 'title': audio_info['title']}

async def play_next_in_queue(vc, guild_id, interaction):
    if is_looping.get(guild_id, False):  # Loop the current track
        current = current_track.get(guild_id)
        if current:
            def after_play(_):
                asyncio.run_coroutine_threadsafe(play_next_in_queue(vc, guild_id, interaction), bot.loop)

            vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(current['file']), volume=volume_level.get(guild_id, 1.0)), after=after_play)
    elif queue[guild_id]:  # Play the next song in the queue
        current = queue[guild_id].pop(0)
        current_track[guild_id] = current

        def after_play(_):
            if not is_looping.get(guild_id, False):
                if os.path.exists(current['file']):
                    os.remove(current['file'])
            asyncio.run_coroutine_threadsafe(play_next_in_queue(vc, guild_id, interaction), bot.loop)

        vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(current['file']), volume=volume_level.get(guild_id, 1.0)), after=after_play)

        embed = discord.Embed(title=f"Now Playing 🎤", description=f"{MUSIC_EMOJI} {current['title']}", color=0x1DB954)
        embed.set_footer(text="Use the buttons below to control playback!")
        view = MusicView(interaction, guild_id)
        await interaction.followup.send(embed=embed, view=view)
    else:  # Cleanup when the queue is empty
        await cleanup(vc, guild_id)
# RPC and Sync commands on bot ready event
@bot.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name="commands 🎧 | Type !help to get started 💡",
    )
    await bot.change_presence(activity=activity)
    print(f"{bot.user} is online and ready! | Built by aditya._0 💻")

    #sync commands 

    await bot.tree.sync()
    print("Bot is ready and slash commands are synced.")

# Run the bot
bot_token = 'DISCORD_BOT_TOKEN'
if bot_token:
    bot.run(bot_token)
else:
    print("Bot token not found. Please set the DISCORD_BOT_TOKEN environment variable.")
