import discord
import mysql.connector
from discord.ext import commands
import random
import string
import os

# Discord bot setup with necessary intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# MySQL database connection setup
db_config = {
    'host': 'host',
    'port': 'port',
    'user': 'user',
    'password': 'pswd',
    'database': 'db'
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
# RPC

@bot.event
async def on_ready():
    # Set rich presence with combined details and state
    activity = discord.Activity(
        type=discord.ActivityType.playing, 
        name="The Aeroplane Company",
        details="The Aeroplane Company",  # Main activity line
        state="Type !helpme to get started | Made by Sri Ram & Bala Aditya"  # Combined small text
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)
    print(f'{bot.user} is online with rich presence!')

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
                    "name": self.name.value,
                    "age": int(self.age.value),
                    "passport_number": self.passport_number.value,
                    "departure_country": self.departure_country.value,
                    "destination_country": self.destination_country.value
                }

                # Ask for arrival date in a follow-up message
                await interaction.response.send_message("📅 Please enter your arrival date in the format `YYYY-MM-DD`:")

                # Wait for user's response with the arrival date
                def check(msg):
                    return msg.author == ctx.author and msg.channel == ctx.channel

                try:
                    arrival_msg = await bot.wait_for("message", check=check, timeout=60.0)
                    passenger_data["arrival_date"] = arrival_msg.content  # Save arrival date

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
                            ticket_number = generate_ticket_number()

                            # Insert details into the database
                            cursor.execute("""
                                INSERT INTO tickets (ticket_number, passenger_name, age, passport_number, 
                                                     departure_country, destination_country, flight_type, price, arrival_date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (ticket_number, passenger_data['name'], passenger_data['age'], passenger_data['passport_number'], 
                                  passenger_data['departure_country'], passenger_data['destination_country'], flight_type, price,
                                  passenger_data['arrival_date']))
                            db.commit()

                            # Confirmation message
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
                            confirmation_embed.add_field(name="💺 Flight Type", value=flight_type.capitalize(), inline=False)
                            confirmation_embed.add_field(name="💵 Price", value=f"${price:.2f}", inline=False)
                            confirmation_embed.add_field(name="🎟️ Ticket Number", value=ticket_number, inline=False)
                            confirmation_embed.add_field(name="📅 Arrival Date", value=passenger_data['arrival_date'], inline=False)
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

    # Button callbacks
    async def delay_callback(interaction):
        await interaction.response.send_message("🔍 Checking for any flight delays...")

    async def arrival_callback(interaction):
        await interaction.response.send_message("🔍 Retrieving estimated arrival time...")

    async def terminal_callback(interaction):
        await interaction.response.send_message("🔍 Fetching terminal information...")

    delay_button.callback = delay_callback
    arrival_button.callback = arrival_callback
    terminal_button.callback = terminal_callback

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

    luggage_button = discord.ui.Button(label="Luggage Delay", style=discord.ButtonStyle.primary, emoji="📦")
    missing_items_button = discord.ui.Button(label="Missing Items", style=discord.ButtonStyle.primary, emoji="📦")
    postpone_button = discord.ui.Button(label="Ticket Postpone", style=discord.ButtonStyle.primary, emoji="🗓️")

    # Button callbacks
    async def luggage_callback(interaction):
        await interaction.response.send_message("🔍 Reporting delayed luggage...")

    async def missing_items_callback(interaction):
        await interaction.response.send_message("🔍 Reporting missing items...")

    async def postpone_callback(interaction):
        await interaction.response.send_message("🔍 Requesting ticket postponement...")

    luggage_button.callback = luggage_callback
    missing_items_button.callback = missing_items_callback
    postpone_button.callback = postpone_callback

    view.add_item(luggage_button)
    view.add_item(missing_items_button)
    view.add_item(postpone_button)

    await ctx.send(embed=embed, view=view)

#SHOW_TABLE CMD

@bot.command(name='show_table')
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

            # Organize ticket information with spaces and add a line separator between each ticket
            ticket_info = (
                f"🎟️ **Ticket Number**\n`{ticket_number}`\n\n"

                f"👤 **Passenger Name**              🛂 **Passport No.**                💺 **Flight Type**\n"
                f"`{name:<25}  {passport_number:<25}       {flight_type.capitalize()}`\n\n"

                f"🛫 **Departure**                     🛬 **Destination**                    💵 **Price**\n"
                f"`{departure:<25}  {destination:<25}       ${price:.2f}`\n\n"

                f"📅 **Arrival Date**\n`{arrival_date}`\n"
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
            description="Click the button below to enter your ticket number for cancellation.",
            color=discord.Color.red()
        )
        view = discord.ui.View(timeout=180)  # 3-minute timeout for the view
        cancel_button = discord.ui.Button(label="Cancel Ticket", style=discord.ButtonStyle.danger)

        async def cancel_ticket_callback(interaction: discord.Interaction):
            # Modal for entering the ticket number
            class CancelTicketModal(discord.ui.Modal):
                def __init__(self):
                    super().__init__(title="Cancel Ticket")
                    self.ticket_number = discord.ui.TextInput(label="Ticket Number", style=discord.TextStyle.short)
                    self.add_item(self.ticket_number)

                async def on_submit(self, interaction: discord.Interaction):
                    # Retrieve ticket number from the modal
                    ticket_number = self.ticket_number.value

                    try:
                        # Delete the ticket record from the database
                        cursor.execute("DELETE FROM tickets WHERE ticket_number = %s", (ticket_number,))
                        db.commit()

                        if cursor.rowcount > 0:
                            # Confirmation message if a row was deleted
                            confirmation_embed = discord.Embed(
                                title="✅ Ticket Cancelled",
                                description=f"Ticket **{ticket_number}** has been successfully cancelled.",
                                color=discord.Color.green()
                            )
                            await interaction.response.send_message(embed=confirmation_embed)
                        else:
                            # Error message if no matching ticket was found
                            error_embed = discord.Embed(
                                title="❌ Error",
                                description="No ticket found with the provided number.",
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

            # Show the modal to enter the ticket number
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

# Run the bot
bot_token = ''
if bot_token:
    bot.run(bot_token)
else:
    print("Bot token not found. Please set the DISCORD_BOT_TOKEN environment variable.")
