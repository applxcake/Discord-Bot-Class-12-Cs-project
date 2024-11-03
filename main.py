import discord
import mysql.connector
from discord.ext import commands
import random
import string
import os
import asyncio

# Discord bot setup with necessary intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# MySQL database connection setup
db_config = {
    'host': 'HOST_NAME',
    'port': 'PORT',
    'user': 'USER_NAME',
    'password': 'USER_PSWD',
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

# Prices for different flight types
FLIGHT_PRICES = {
    "economy": 100.00,
    "business": 250.00,
    "first": 500.00
}

# Channel IDs
# Channel IDs
channel_ids = {
    "ticket_purchasing": <purchase channel id>,
    "inquiry": <inquiry channel id>,
    "support": <support channel id>,
    "cancel": <cancel channel id>,
    "show_table": <show_table channel id>,
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
        new_channel = await create_ticket_channel(ctx.guild, category, "ticket", guide_message, interaction.user)
        await new_channel.send(f"{interaction.user.mention}, your ticket purchasing support has been created here.")
        await interaction.response.send_message("Your ticket has been created!", ephemeral=True)

    ticket_button.callback = ticket_button_callback
    view.add_item(ticket_button)

    await channel.send(embed=embed, view=view)

# Inquiry Embed
@bot.command(name='channel-inquiry')
@commands.is_owner()
async def inquiry_command(ctx):
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
            "For help, please provide details of your inquiry here or use the command `!ask` for specific questions. 💬"
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
            "To confirm cancellation, please use `!confirm_cancel` in this channel. 📑"
        )
        new_channel = await create_ticket_channel(ctx.guild, category, "cancel", guide_message, interaction.user)
        await new_channel.send(f"{interaction.user.mention}, your cancellation support has been created here.")
        await interaction.response.send_message("A cancellation ticket has been created!", ephemeral=True)

    cancel_button.callback = cancel_button_callback
    view.add_item(cancel_button)

    await channel.send(embed=embed, view=view)

# Show Table Embed
@bot.command(name='channel-show_table')
@commands.is_owner()
async def show_table_command(ctx):
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
        ticket_number, name, age, passport_number, departure, destination, flight_type, price, arrival_date = row
        ticket_info = (
            f"🎟️ **Ticket Number**: {ticket_number}\n"
            f"👤 **Passenger Name**: {name}\n"
            f"🛂 **Passport No.**: {passport_number}\n"
            f"💺 **Flight Type**: {flight_type.capitalize()}\n"
            f"🛫 **Departure**: {departure}\n"
            f"🛬 **Destination**: {destination}\n"
            f"💵 **Price**: ${price:.2f}\n"
            f"📅 **Arrival Date**: {arrival_date}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(name=f"Ticket #{ticket_number}", value=ticket_info, inline=False)

    view = discord.ui.View()
    show_table_button = discord.ui.Button(label="Show Table", style=discord.ButtonStyle.blurple)

    async def show_table_callback(interaction):
        category = channel.category
        guide_message = (
            "📋 Viewing ticket table details.\n\n"
            "Use `!table_details` to interact with the ticket information or make updates. 💼"
        )
        new_channel = await create_ticket_channel(ctx.guild, category, "table", guide_message, interaction.user)
        await new_channel.send(f"{interaction.user.mention}, the table view has been created here.")
        await interaction.response.send_message("Table ticket has been created!", ephemeral=True)

    show_table_button.callback = show_table_callback
    view.add_item(show_table_button)

    await channel.send(embed=embed, view=view)

# RPC

@bot.event
async def on_ready():
    # Set rich presence with combined details and state
    activity = discord.Activity(
        type=discord.ActivityType.listening, 
        name="Type !helpme to get started",
        details="Type !helpme to get started",  # Main activity line
        state="Made by aditya._0"  # Combined small text
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)
    print(f'{bot.user} is online with the rich presence!')

#HELPME CMD

@bot.command(name='helpme')
async def helpme_command(ctx):
    embed = discord.Embed(
        title="📋 Help Menu",
        description="Here's a list of available commands:",
        color=discord.Color.blue()
    )
    embed.add_field(name="✈️ !purchase", value="Purchase a flight ticket", inline=False)
    embed.add_field(name="🔍 !inquiry", value="Check flight information", inline=False)
    embed.add_field(name="🛠️ !support", value="Support for issues like luggage delay or ticket postpone", inline=False)
    embed.add_field(name="❌ !cancel", value="Cancel a booking", inline=False)
    embed.add_field(name="📋 !show_table", value="Show all booked tickets", inline=False)
    embed.add_field(name="💬 !purge", value="Deletes Messages (in whole)", inline=False)
    embed.add_field(name="🧮 !calc", value="A basic Calculator for our needs", inline=False)
    await ctx.send(embed=embed)

#PURCHASE CMD

@bot.command(name='purchase')
async def purchase_ticket(ctx):
    embed = discord.Embed(
        title="✈️ Flight Ticket Booking",
        description="Click the button below to start the booking process.",
        color=discord.Color.blue()
    )
    view = discord.ui.View()
    start_button = discord.ui.Button(label="Start Booking", style=discord.ButtonStyle.primary)

    async def start_booking_callback(interaction):
        # Modal to collect initial passenger information
        class PassengerInfoModal(discord.ui.Modal, title="Passenger Information"):
            name = discord.ui.TextInput(label="👤 Passenger Name", placeholder="Enter your name")
            age = discord.ui.TextInput(label="📅 Age", placeholder="Enter your age", style=discord.TextStyle.short)
            passport_number = discord.ui.TextInput(label="🛂 Passport Number", placeholder="Enter your passport number")
            departure_country = discord.ui.TextInput(label="🛫 Departure Country", placeholder="Where are you departing from?")
            destination_country = discord.ui.TextInput(label="🛬 Destination Country", placeholder="Where are you going?")

            async def on_submit(self, interaction):
                # Store collected passenger information
                passenger_data = {
                    "name": self.name.value.upper(),
                    "age": str(self.age.value).upper(),
                    "passport_number": self.passport_number.value.upper(),
                    "departure_country": self.departure_country.value.upper(),
                    "destination_country": self.destination_country.value.upper()
                }

                # Query the database to retrieve the flight number based on departure country
                cursor.execute("SELECT flight_number FROM flight WHERE place = %s", (passenger_data['departure_country'],))
                flight_result = cursor.fetchone()
                if flight_result:
                    flight_number = flight_result[0].upper()  # Retrieve and convert the flight number to uppercase
                else:
                    await interaction.response.send_message("⚠️ No flight found for the selected departure country. Please try again.", ephemeral=True)
                    return

                # Ask for arrival date in a follow-up message
                await interaction.response.send_message("📅 Please enter your arrival date in the format `YYYY-MM-DD`:")

                # Wait for user's response with the arrival date
                def check(msg):
                    return msg.author == ctx.author and msg.channel == ctx.channel

                try:
                    arrival_msg = await bot.wait_for("message", check=check, timeout=60.0)
                    passenger_data["arrival_date"] = arrival_msg.content.upper()  # Save and convert arrival date to uppercase

                    # Prompt for flight type selection with buttons
                    embed = discord.Embed(
                        title="Select Flight Type",
                        description="Choose your preferred flight type.",
                        color=discord.Color.blue()
                    )
                    view = discord.ui.View()

                    for flight_type, price in FLIGHT_PRICES.items():
                        button = discord.ui.Button(label=f"{flight_type.capitalize()} - ${price}", style=discord.ButtonStyle.secondary)

                        async def flight_type_callback(interaction, flight_type=flight_type, price=price):
                            ticket_number = generate_ticket_number().upper()  # Convert ticket number to uppercase

                            # Insert details into the database
                            cursor.execute("""
                                INSERT INTO tickets (ticket_number, passenger_name, age, passport_number, 
                                                     departure_country, destination_country, flight_type, price, arrival_date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (ticket_number, passenger_data['name'], passenger_data['age'], passenger_data['passport_number'], 
                                  passenger_data['departure_country'], passenger_data['destination_country'], flight_type, price,
                                  passenger_data['arrival_date']))
                            db.commit()

                            # Confirmation message with uppercase details
                            confirmation_embed = discord.Embed(
                                title="Ticket Purchase Confirmation 🎫",
                                description="Your ticket has been successfully booked!",
                                color=discord.Color.green()
                            )
                            confirmation_embed.add_field(name="👤 Passenger Name", value=passenger_data['name'], inline=False)
                            confirmation_embed.add_field(name="📅 Age", value=str(passenger_data['age']), inline=False)
                            confirmation_embed.add_field(name="🛂 Passport Number", value=passenger_data['passport_number'], inline=False)
                            confirmation_embed.add_field(name="🛫 Departure", value=passenger_data['departure_country'], inline=True)
                            confirmation_embed.add_field(name="🛬 Destination", value=passenger_data['destination_country'], inline=True)
                            confirmation_embed.add_field(name="💺 Flight Type", value=flight_type.upper(), inline=False)
                            confirmation_embed.add_field(name="💵 Price", value=f"${price:.2f}", inline=False)
                            confirmation_embed.add_field(name="🎟️ Ticket Number", value=ticket_number, inline=False)
                            confirmation_embed.add_field(name="📅 Arrival Date", value=passenger_data['arrival_date'], inline=False)
                            confirmation_embed.add_field(name="✈️ Flight Number", value=flight_number, inline=False)  # Include flight number in uppercase
                            await interaction.response.send_message(embed=confirmation_embed)

                        button.callback = flight_type_callback
                        view.add_item(button)

                    await ctx.send(embed=embed, view=view)

                except TimeoutError:
                    await interaction.followup.send("⚠️ You took too long to respond. Please start the purchase process again.", ephemeral=True)

        await interaction.response.send_modal(PassengerInfoModal())

    start_button.callback = start_booking_callback
    view.add_item(start_button)

    await ctx.send(embed=embed, view=view)


#INQUIRY CMD

@bot.command(name='inquiry')
async def inquiry_command(ctx):
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


#SHOW_TABLE CMD

@bot.command(name='show_table')
@commands.has_role(1302680610187509793)
async def show_table_command(ctx):
    cursor.execute("SELECT * FROM tickets")
    results = cursor.fetchall()
    if results:
        embed = discord.Embed(
            title="📋 **Booked Tickets**",
            description="Here’s the list of all booked tickets:",
            color=discord.Color.green()
        )

        for row in results:
            ticket_number, name, age, passport_number, departure, destination, flight_type, price, arrival_date = row

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
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            embed.add_field(name=f"**Ticket #{ticket_number}**", value=ticket_info, inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send("ℹ️ No tickets booked yet.")


#CANCEL CMD

@bot.command(name='cancel')
async def cancel_command(ctx):
    try:
        # Embed with "Cancel Ticket" button
        embed = discord.Embed(
            title="🎫 Cancel Flight Ticket",
            description="Click the button below to enter your ticket number and name for cancellation.",
            color=discord.Color.red()
        )
        view = discord.ui.View(timeout=180)  # 3-minute timeout for the view
        cancel_button = discord.ui.Button(label="Cancel Ticket", style=discord.ButtonStyle.danger)

        async def cancel_ticket_callback(interaction: discord.Interaction):
            # Modal for entering the ticket number and passenger name
            class CancelTicketModal(discord.ui.Modal):
                def __init__(self):
                    super().__init__(title="Cancel Ticket")
                    self.ticket_number = discord.ui.TextInput(label="Ticket Number", style=discord.TextStyle.short)
                    self.passenger_name = discord.ui.TextInput(label="Passenger Name", style=discord.TextStyle.short)
                    self.add_item(self.ticket_number)
                    self.add_item(self.passenger_name)

                async def on_submit(self, interaction: discord.Interaction):
                    # Retrieve ticket number and passenger name from the modal
                    ticket_number = self.ticket_number.value
                    passenger_name = self.passenger_name.value

                    try:
                        # Update the query to use the correct column name for the passenger's name
                        cursor.execute(
                            "SELECT * FROM tickets WHERE ticket_number = %s AND LOWER(passenger_name) = LOWER(%s)",
                            (ticket_number, passenger_name)
                        )
                        result = cursor.fetchone()

                        if result:
                            # Delete the matching ticket record
                            cursor.execute("DELETE FROM tickets WHERE ticket_number = %s", (ticket_number,))
                            db.commit()

                            # Confirmation message if the ticket was deleted
                            confirmation_embed = discord.Embed(
                                title="✅ Ticket Cancelled Successfully!",
                                description=(
                                    f"🎟️ **Ticket Number**: `{ticket_number}`\n"
                                    f"👤 **Passenger Name**: `{passenger_name}`\n\n"
                                    "Your ticket has been successfully cancelled. "
                                    "If you need further assistance, please contact support."
                                ),
                                color=discord.Color.green()
                            )
                            confirmation_embed.set_footer(text="Thank you for choosing our service!")
                            await interaction.response.send_message(embed=confirmation_embed)
                        else:
                            # Error message if no matching ticket was found
                            error_embed = discord.Embed(
                                title="❌ Ticket Not Found",
                                description="No ticket found with the provided number and name. Please try again.",
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

            # Show the modal to enter the ticket number and passenger name
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


# SQL CMD


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

@bot.command(name='nig')
async def joker_gif(ctx):
    await ctx.send(f"I like sri ram and v hemanth oiled up")
    embed = discord.Embed(title="💦")
    # Replace the URL with a direct link to a GIF. You might need to use an actual GIF link here.
    embed.set_image(url="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExejBtOWVlaW13MWhvZTM4bTJ6MTRvdzdvdGFoZ2U0N29saXA3Y3JjdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/XCKQMMZWkzs51TEEgz/giphy-downsized-large.gif")
    await ctx.send(embed=embed)

@bot.command(name='hob')
async def joker_gif(ctx):
    await ctx.send(f"""Well, let me tell ya ’bout hobt0, one of the finest moderators you’ll find ridin' the virtual plains over on Zeqa Minecraft. This here feller knows them server rules better than a cowboy knows his trusty steed. Folks around the server got a deep respect for hobt0, not just ‘cause they keep order like a true sheriff, but ‘cause they’re fair as a prairie sunrise, always lookin’ out for everyone from the greenest newcomer to the most seasoned players.

Hobt0's got a knack for defusin’ trouble faster than a rattlesnake strikes, and if there’s an issue brewin’ in the chat or on the fields, they’re the first to saddle up and ride to set things right. Ain’t just about keepin' folks in line, neither—hobt0's as friendly and helpful as a good neighbor, makin' sure everyone feels welcome and knows where to start if they're lost.

Reckon folks’d say Zeqa Minecraft wouldn't be quite the same without ‘em.""")
    embed = discord.Embed(title="🔥")
    embed.set_image(url="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3Fqc2wwaHRuYTRibWp3c2NhMzBnZXVhNm80OTV2YzI5M2o2cGc1MCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/TIcqppfavXjhqxhUVV/giphy.gif")
    await ctx.send(embed=embed)

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


# Run the bot
bot_token = 'BOT_TOKEN'
if bot_token:
    bot.run(bot_token)
else:
    print("Bot token not found. Please set the DISCORD_BOT_TOKEN environment variable.")
