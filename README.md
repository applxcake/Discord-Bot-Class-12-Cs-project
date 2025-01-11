Here’s the updated README for your Discord bot project using MySQL instead of SQLite. You can save it as README.md.

(OUTDATED AS OF 11 JANUARY, 2024)
# ✈️ Flight Ticket Booking Discord Bot

Welcome to the **Flight Ticket Booking Discord Bot** project! This bot simulates a flight ticket booking system within Discord, providing users with a fun and interactive experience. **Disclaimer**: This bot is purely for educational and entertainment purposes and is not associated with any real-life booking service.

---

## 📋 Table of Contents
- [Introduction](#-introduction)
- [Features](#-features)
- [Setup](#-setup)
- [Commands](#-commands)
- [Tech Stack](#-tech-stack)
- [Contributing](#-contributing)
- [License](#-license)
- [Code of Conduct](#-code-of-conduct)

---

## 💡 Introduction

Created by **Bala Aditya** and **Sri Ram Charan**, this project is a **CS project** for learning and showcasing our coding skills. This Discord bot uses **Python** and **MySQL** to create a simulated booking experience where users can:
- Book tickets
- Lookup flight details
- Cancel tickets
- Get support on various issues

This bot is a fun tool to engage users and can be used as a project in various CS-related curricula.

> **Disclaimer**: This bot is a fictional project and not intended for real-life ticket booking. It does not guarantee any real-world bookings or reservations.

---

## ✨ Features

- **Interactive Ticket Booking**: Users can purchase and manage tickets within Discord.
- **Database Integration**: All bookings are saved to a MySQL database, providing a persistent record.
- **User Support**: Users can ask questions and get assistance with their fictional bookings.
- **Inquiries**: Check flight status, delays, and terminal information.
- **Modern UI**: Uses rich embeds and interactive buttons for a sleek look.

---

## ⚙️ Setup

To run this bot locally, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/applxcake/Discord-Python-MYSQL-bot
   cd Discord-Python-MYSQL-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install discord.py mysql-connector-python
   ```

3. **Setup MySQL Database**:
   - Install MySQL on your system if you haven't already.
   - Create a database called `flight_booking` and add the following tables for bookings and flights:

   ```sql
    CREATE TABLE IF NOT EXISTS tickets (
    ticket_number VARCHAR(8) PRIMARY KEY,
    passenger_name VARCHAR(100),
    age INT,
    passport_number VARCHAR(20),
    departure_country VARCHAR(50),
    destination_country VARCHAR(50),
    flight_type VARCHAR(20),
    price DECIMAL(10, 2),
    arrival_date DATE,
    grptno varchar(30),
   member_id BIGINT NOT NULL
   );

   CREATE TABLE flight (
       place VARCHAR(255) NOT NULL,
       flight_number VARCHAR(50) NOT NULL,
       delay VARCHAR(50),
       terminal VARCHAR(50) PRIMARY KEY
   );
   ```

4. **Configure Database Connection**:
   - Update your database connection details in the code where the MySQL connection is established.

5. **Run the bot**:
   ```bash
   python main.py
   ```

> Ensure you have a Discord bot set up and have its token ready to insert into the code. You can create a bot at the Discord Developer Portal.

## 🛠️ Tech Stack

- **Python**: Main programming language for bot functionality.
- **MySQL**: Database for storing and managing ticket data.
- **Discord API**: For interaction within the Discord platform.

---

## ⚠️ Disclaimer

This bot is strictly for educational purposes and should be used solely as a CS project or fun Discord bot. It is not a real booking service and does not guarantee any real-life ticket reservations or support. All interactions and data are simulated.

---

## 📝 License

This project is licensed under the MIT License. For more details, see the LICENSE file.

---

## 📜 Code of Conduct

We have adopted a Code of Conduct for this project. All contributors are expected to uphold this code to create a welcoming and inclusive environment.

---

# Built by Bala Aditya, Sri Ram Charan and V Hemanth.
