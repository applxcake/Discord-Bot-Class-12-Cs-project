Here’s the updated README for your Discord bot project using MySQL instead of SQLite. You can save it as README.md.

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

Created by **Bala Adithya** and **Sri Ram Charan**, this project is a **CS project** for learning and showcasing our coding skills. This Discord bot uses **Python** and **MySQL** to create a simulated booking experience where users can:
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
   git clone https://github.com/your-repo/flight-booking-bot.git
   cd flight-booking-bot

2. Install dependencies:

pip install discord.py mysql-connector-python


3. Setup MySQL Database:

Install MySQL on your system if you haven't already.

Create a database called flight_booking and a table for bookings with the necessary fields. Here’s an example SQL command to create a basic table:

CREATE TABLE tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    flight_number VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL
);



4. Configure Database Connection: Update your database connection details in the code where MySQL connection is established.


5. Run the bot:

python bot.py



> Ensure you have a Discord bot set up and have its token ready to insert in the code. You can create a bot at the Discord Developer Portal.

## 🛠️ Tech Stack

Python: Main programming language for bot functionality.

MySQL: Database for storing and managing ticket data.

Discord API: For interaction within the Discord platform.



---

## 🤝 Contributing

We welcome contributions from the community to enhance this project!

1. Fork the repository and create your branch: git checkout -b feature/AmazingFeature


2. Commit your changes: git commit -m 'Add some AmazingFeature'


3. Push to the branch: git push origin feature/AmazingFeature


4. Open a pull request



Please read our Code of Conduct before contributing.


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

# > Built by Bala Aditya 



