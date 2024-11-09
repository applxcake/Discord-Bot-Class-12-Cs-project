import discord
import mysql.connector
from discord.ext import commands
import random
import string
import os
import asyncio
import pytz
from discord.ui import Modal, TextInput, Button, View
from datetime import datetime, timedelta, time
from discord import app_commands, ui, Interaction, Embed
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Discord bot setup with necessary intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
geolocator = Nominatim(user_agent="flight_bot")

# MySQL database connection setup
db_config = {
    'host': 'HOST',
    'port': 'PORT',
    'user': 'USER_NAME',
    'password': 'PSWD',
    'database': 'DB_NAME'
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
    "ticket_purchasing": "channel_id",
    "inquiry": "channel_id",
    "support": "channel_id",
    "cancel": "channel_id",
    "show_table": "channel_id",
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
        ticket_number, name, age, passport_number, departure, destination, flight_type, price, arrival_date, flight_number, seat_number, purchase_time, grptno = row
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
    
# Function to generate a random seat number
def generate_seat_number():
    row = random.randint(1, 30)  # Example: 30 rows in the plane
    seat = random.choice("ABCDEF")  # Example: seats labeled A-F
    return f"{row}{seat}"

    
#PURCHASE CMD
@bot.command(name='purchase')
async def purchase_ticket(ctx):
    """Purchase command for purchasing flight tickets."""

    embed = discord.Embed(
        title="✈️ Flight Ticket Booking",
        description="Click the button below to start the booking process, \n Put commas in between for Group purchase 👥.",
        color=discord.Color.blue()
    )
    view = discord.ui.View(timeout=None)
    start_button = discord.ui.Button(label="Start Booking", style=discord.ButtonStyle.primary)

    def generate_group_number():
        return ''.join(random.choices(string.ascii_uppercase, k=2)) + ''.join(random.choices(string.digits, k=4)) + ''.join(random.choices(string.ascii_uppercase, k=2))

    async def start_booking_callback(interaction: discord.Interaction):

        class PassengerInfoModal(discord.ui.Modal, title="Passenger Information"):
            names = discord.ui.TextInput(label="👤 Passenger Names", placeholder="Enter your name ( eg: Alice, Bob ..)")
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
                    await interaction.followup.send("⚠️ Ensure the same number of names, ages, and passport numbers are provided \n Ensure that there are commas in between the fields.", ephemeral=True)
                    return

                # Validate ages to ensure they are realistic
                try:
                    passenger_ages = [int(age.strip()) for age in passenger_ages]  # Convert ages to integers
                    if not all(0 <= age <= 120 for age in passenger_ages):  # Check if all ages are within 0-120
                        await interaction.followup.send("⚠️ Ages must be between 0 and 120.", ephemeral=True)
                        return
                except ValueError:
                    await interaction.followup.send("⚠️ Please ensure all ages are valid integers.", ephemeral=True)
                    return

                cursor.execute("SELECT flight_number FROM flight WHERE place = %s", (self.departure_country.value.upper(),))
                flight_results = cursor.fetchall()
                flight_number = random.choice([result[0] for result in flight_results]).upper() if flight_results else "FL123"

                try:
                    departure_location = geolocator.geocode(self.departure_country.value)
                    destination_location = geolocator.geocode(self.destination_country.value)
                    if not departure_location or not destination_location:
                        await interaction.followup.send("⚠️ Could not locate one of the places. Check country names.", ephemeral=True)
                        return
                    distance_km = geodesic((departure_location.latitude, departure_location.longitude),
                                           (destination_location.latitude, destination_location.longitude)).km
                    price = distance_km * 0.1

                except Exception as e:
                    await interaction.followup.send(f"⚠️ Error in location calculation: {e}", ephemeral=True)
                    return

                async def prompt_arrival_date():
                    arrival_embed = discord.Embed(
                        title="📅 Arrival Date",
                        description="Please enter your **arrival date** in the format YYYY-MM-DD (e.g., 2024-11-06).",
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=arrival_embed)
                    def check(msg):
                        return msg.author == ctx.author and msg.channel == ctx.channel
                    try:
                        while True:
                            arrival_msg = await bot.wait_for("message", check=check, timeout=60.0)
                            try:
                                arrival_date = datetime.strptime(arrival_msg.content, "%Y-%m-%d").date()
                                if arrival_date < datetime.today().date():
                                    await ctx.send(embed=discord.Embed(
                                        title="❌ Invalid Date",
                                        description="The date is in the past! Enter a future date.",
                                        color=discord.Color.red()
                                    ))
                                else:
                                    return arrival_date.strftime("%Y-%m-%d").upper()
                            except ValueError:
                                await ctx.send(embed=discord.Embed(
                                    title="⚠️ Incorrect Format",
                                    description="The date format is incorrect! Use YYYY-MM-DD.",
                                    color=discord.Color.orange()
                                ))
                    except TimeoutError:
                        await ctx.send(embed=discord.Embed(
                            title="⏰ Time Out",
                            description="You took too long to respond. Please restart the purchase process.",
                            color=discord.Color.red()
                        ))
                arrival_date = await prompt_arrival_date()

                # Set group number to "NILL" if only one passenger
                group_number = "NILL" if num_passengers == 1 else generate_group_number()

                embed = discord.Embed(
                    title="Select Flight Type ✈️",
                    description="Choose your flight type from the options below.",
                    color=discord.Color.blue()
                )
                view = discord.ui.View()
                flight_types = {"economy": price, "business": price * 1.5, "first": price * 2}

                for flight_type, calculated_price in flight_types.items():
                    button = discord.ui.Button(label=f"{flight_type.capitalize()} - ${calculated_price:.2f}", style=discord.ButtonStyle.secondary)

                    async def flight_type_callback(interaction, flight_type=flight_type, calculated_price=calculated_price):
                        confirmation_embed = discord.Embed(
                            title="Ticket Purchase Confirmation 🎫",
                            description="Your ticket has been successfully booked! Here are your details:",
                            color=discord.Color.green()
                        )

                        # Display passenger names at the top
                        passenger_list = "\n".join(passenger_names)
                        confirmation_embed.add_field(name="👤 Passengers List", value=passenger_list, inline=False)

                        confirmation_embed.add_field(name="🛫 Departure", value=self.departure_country.value.upper(), inline=True)
                        confirmation_embed.add_field(name="🛬 Destination", value=self.destination_country.value.upper(), inline=True)
                        confirmation_embed.add_field(name="💺 Flight Type", value=flight_type.upper(), inline=False)
                        confirmation_embed.add_field(name="📅 Arrival Date", value=arrival_date, inline=False)
                        confirmation_embed.add_field(name="✈️ Flight Number", value=flight_number, inline=False)

                        ist = pytz.timezone("Asia/Kolkata")
                        current_time_ist = datetime.now(ist).strftime("%I:%M %p")

                        for i, (name, age, passport) in enumerate(zip(passenger_names, passenger_ages, passport_numbers)):
                            ticket_number = generate_ticket_number().upper()
                            seat_number = generate_seat_number()
                            cursor.execute("""
                                INSERT INTO tickets (ticket_number, passenger_name, age, passport_number, 
                                                     departure_country, destination_country, flight_type, 
                                                     price, arrival_date, flight_number, seat_number, purchase_time, grptno)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (ticket_number, name, age, passport, self.departure_country.value.upper(),
                                  self.destination_country.value.upper(), flight_type, calculated_price, 
                                  arrival_date, flight_number, seat_number, current_time_ist, group_number))
                            db.commit()
                            
                            if i > 0:
                                confirmation_embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━", inline=False)
                                
                            confirmation_embed.add_field(name="🎟️ Ticket Number", value=ticket_number, inline=False)
                            confirmation_embed.add_field(name="👤 Name", value=name, inline=True)
                            confirmation_embed.add_field(name="📅 Age", value=age, inline=True)
                            confirmation_embed.add_field(name="🛂 Passport", value=passport, inline=True)
                            confirmation_embed.add_field(name="🪑 Seat", value=seat_number, inline=False)

                        confirmation_embed.add_field(name="👥 Group Number", value=group_number, inline=False)
                        confirmation_embed.add_field(name="🕒 Purchase Time (IST)", value=current_time_ist, inline=False)
                        await interaction.response.send_message(embed=confirmation_embed)

                    button.callback = flight_type_callback
                    view.add_item(button)

                await ctx.send(embed=embed, view=view)

        await interaction.response.send_modal(PassengerInfoModal())

    start_button.callback = start_booking_callback
    view.add_item(start_button)
    await ctx.send(embed=embed, view=view)

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

                # Retrieve the requested info from the flight table based on the selected option
                cursor.execute("SELECT delay, terminal FROM flight WHERE flight_number = %s", (flight_num,))
                result = cursor.fetchone()

                if result:
                    delay, terminal = result
                    description = ""
                    if info_type == "delay":
                        description = "⏱️ Checking delay status..."

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

                # Fetch delay info based on flight number
                cursor.execute("SELECT delay FROM flight WHERE flight_number = %s", (flight_num,))
                result = cursor.fetchone()

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

                # Check if ticket number and name match in the tickets table
                cursor.execute("SELECT arrival_date FROM tickets WHERE ticket_number = %s AND passenger_name = %s", 
                               (ticket_num, name))
                result = cursor.fetchone()

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
@commands.has_role(1302680610187509793)
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
            ticket_number, name, age, passport_number, departure, destination, flight_type, price, arrival_date, flight_number, seat_number, purchase_time, grptno = row

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

#CANCEL CMD
@bot.command(name='cancel')
async def cancel_command(ctx):
    """Cancels Tickets."""
    try:
        # Embed with "Cancel Ticket" button
        embed = discord.Embed(
            title="🎫 Cancel Flight Ticket",
            description="Click the button below to enter your details for ticket cancellation.",
            color=discord.Color.red()
        )
        view = discord.ui.View(timeout=180)  # 3-minute timeout for the view
        cancel_button = discord.ui.Button(label="Cancel Ticket", style=discord.ButtonStyle.danger)

        async def cancel_ticket_callback(interaction: discord.Interaction):
            # Modal for entering flight number, ticket number, seat number, and passenger name
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
                    # Retrieve details from the modal
                    flight_number = self.flight_number.value
                    ticket_number = self.ticket_number.value
                    seat_number = self.seat_number.value
                    passenger_name = self.passenger_name.value

                    try:
                        # Query to verify all details in the database
                        cursor.execute(
                            """
                            SELECT arrival_date, purchase_time 
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
                            # Extract arrival date and purchase time
                            arrival_date_db, purchase_time_str = result

                            # Combine arrival date with time (if the time is needed and available)
                            arrival_date = datetime.combine(arrival_date_db, time(23, 59))  # assuming arrival is end of the day if time is not specified
                            
                            # Make arrival_date timezone-aware in IST
                            ist_timezone = pytz.timezone("Asia/Kolkata")
                            arrival_date = ist_timezone.localize(arrival_date)

                            # Get current time in IST
                            current_time = datetime.now(ist_timezone)

                            # Calculate time difference
                            time_difference = arrival_date - current_time
                            refund_message = ""
                            refund_embed_color = discord.Color.green()  # Default to green for refundable

                            if time_difference < timedelta(hours=8):
                                # If cancellation is within 8 hours of arrival date
                                refund_message = "⛔ **No Refund Available**\nYou are cancelling your ticket within 8 hours of arrival. Therefore, **no refund** will be issued."
                                refund_embed_color = discord.Color.red()
                            else:
                                # If cancellation is before the 8-hour window
                                refund_message = "💸 **Refund Available**\nYou are cancelling your ticket with more than 8 hours remaining until arrival. Your **refund will be processed** shortly."

                            # Delete the matching ticket record if all details are correct
                            cursor.execute("DELETE FROM tickets WHERE ticket_number = %s", (ticket_number,))
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
                                color=refund_embed_color
                            )
                            confirmation_embed.set_footer(text="Thank you for choosing our service!")
                            await interaction.response.send_message(embed=confirmation_embed)
                        else:
                            # Error message if no matching ticket was found
                            error_embed = discord.Embed(
                                title="❌ Ticket Not Found",
                                description="No ticket found with the provided details. Please check and try again.",
                                color=discord.Color.red()
                            )
                            await interaction.response.send_message(embed=error_embed)
                    except Exception as e:
                        # Send an error message if there’s an issue with the database
                        error_embed = discord.Embed(
                            title="⚠️ Database Error",
                            description=f"An error occurred while processing your request: {e}",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=error_embed)

            # Show the modal to enter the details
            await interaction.response.send_modal(CancelTicketModal())

        # Attach the callback to the button
        cancel_button.callback = cancel_ticket_callback
        view.add_item(cancel_button)

        # Send the embed with the cancel button
        await ctx.send(embed=embed, view=view)
        print("Cancel command embed and button sent successfully.")

    except Exception as e:
        # Error handling if the command fails to execute
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
# Helper function to format results from the "tickets" table
def format_tickets_embed(headers, rows):
    embed = discord.Embed(
        title="🎟️ Tickets Table Results",
        description="Here are the results from the `tickets` table.",
        color=discord.Color.blue()
    )
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
        embed.add_field(name="Ticket", value=ticket_info, inline=False)
    return embed
# Helper function to format general SQL query results in an embed
def format_query_result_embed(headers, rows):
    embed = discord.Embed(
        title="📊 Query Results",
        description="Here are the results from your query.",
        color=discord.Color.green()
    )
    for row in rows:
        row_info = ""
        for header, value in zip(headers, row):
            row_info += f"**{header}:** {value}\n"
        embed.add_field(name="Result", value=row_info, inline=False)
    return embed

@bot.command(name="sql")
@commands.has_role(1300878206349475860)  # Restrict to the bot owner
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

        # If it's a SELECT query, fetch and display results
        if query.strip().lower().startswith("select"):
            rows = cursor.fetchall()
            if rows:
                # Format differently if fetching from the tickets table
                if query.strip().lower() == "select * from tickets":
                    headers = [desc[0] for desc in cursor.description]
                    embed = format_tickets_embed(headers, rows)
                else:
                    headers = [desc[0] for desc in cursor.description]  # Column names
                    embed = format_query_result_embed(headers, rows)
            else:
                embed = discord.Embed(
                    title="✅ Query Executed Successfully",
                    description="No results to display.",
                    color=discord.Color.green()
                )
        else:
            # Ensure all results are read before commit for non-SELECT queries
            cursor.fetchall()
            db.commit()
            embed = discord.Embed(
                title="✅ Query Executed Successfully",
                description="Your SQL query was executed and committed.",
                color=discord.Color.green()
            )
        # Send the embed
        await ctx.send(embed=embed)

    except mysql.connector.ProgrammingError as e:
        # Handle specific MySQL programming errors, showing the query that caused the issue
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
async def calc(ctx, operation: str, num1: float, num2: float):
    """
    Perform basic arithmetic calculations.
    Usage: !calc [operation] [num1] [num2]
    Supported operations: add, subtract, multiply, divide
    """
    if operation == 'add':
        result = num1 + num2
        await ctx.send(f"The result of {num1} + {num2} is {result}")
    elif operation == 'subtract':
        result = num1 - num2
        await ctx.send(f"The result of {num1} - {num2} is {result}")
    elif operation == 'multiply':
        result = num1 * num2
        await ctx.send(f"The result of {num1} * {num2} is {result}")
    elif operation == 'divide':
        if num2 == 0:
            await ctx.send("Cannot divide by zero!")
        else:
            result = num1 / num2
            await ctx.send(f"The result of {num1} / {num2} is {result}")
    else:
        await ctx.send("Invalid operation! Please use add, subtract, multiply, or divide.")


#nsfw stuff and self boasting
#nsfw cmd
@bot.command(name='nig')
async def joker_gif(ctx):
    """NSFW joke."""
    await ctx.send(f"I like sri ram and v hemanth oiled up")
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


# RPC and Sync commands on bot ready event
@bot.event
async def on_ready():
    # Set Rich Presence status with emojis and formatted text
    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name="commands 🎧 | Type !help to get started 💡",
    )
    await bot.change_presence(activity=activity)
    print(f"{bot.user} is online and ready! | Built by aditya._0 💻")

    #sync commands 

    await bot.tree.sync()
    print("Bot is ready and slash commands are synced.")

#LISTCMD 
# Command to list all available commands
@bot.command(name="listcmds")
async def list_commands(ctx):
    """Lists all the commands."""
    list_embed = discord.Embed(
        title="📜 List of Commands",
        description="Here are all the available commands:",
        color=discord.Color.purple()
    )
    
    # Loop through all commands in the bot and add them to the embed
    for command in bot.commands:
        list_embed.add_field(
            name=f"🔹 **!{command.name}**",
            value=command.help if command.help else "No description available",
            inline=False
        )
    
    list_embed.set_footer(text="⚙️ Built by aditya._0 | Use !help <command> for more info on each command.")
    await ctx.send(embed=list_embed)

#STATUS CMD
# The target channel ID where the message will be sent
TARGET_CHANNEL_ID = "channel_id"

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
    

#GAY METER
# In-memory dictionary to store user "gayness" levels
gayness_levels = {}

# Keywords that affect "gayness" levels
increase_keywords = ["fabulous", "yass", "queen", "slay", "work it"]
decrease_keywords = ["bro", "dude", "straight", "no homo"]


@bot.command()
async def gay(ctx, member: discord.Member = None):
    """Rates gayness👅."""
    if member is None:
        member = ctx.author  # Use the command invoker if no member is mentioned

    # Get or initialize gayness level
    gayness = gayness_levels.get(member.id, random.randint(0, 100))
    gayness_levels[member.id] = gayness  # Store it if new

    # Create an embed with the gayness level
    embed = discord.Embed(
        title="🌈💋 Gayness Detector 💋🌈",
        description=f"{member.mention}'s gayness level is:",
        color=discord.Color.purple()
    )
    embed.add_field(name="Gayness Level", value=f"👅💖 **{gayness}%** 💖👅", inline=False)
    embed.set_footer(text="Just having some fun! 😜")
    
    # Send the embedded message
    await ctx.send(embed=embed)

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


# Run the bot
bot_token = 'BOT_TOKEN_GOES_HERE'
if bot_token:
    bot.run(bot_token)
else:
    print("Bot token not found. Please set the DISCORD_BOT_TOKEN environment variable.")
