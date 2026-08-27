# Stoxly – Stock Portfolio Tracker & Analyzer

> **Invest with Insight. Grow with Stoxly.**

A Python-based desktop application that helps users track and analyze their stock portfolio using real-time NSE data, interactive visualizations, and AI-powered insights.

---

## Features

- **User Authentication System**  
  Secure signup/login using a MySQL database. Supports login via UserID or Username.

- **Real-Time Stock Data Integration**  
  - Fetches all listed company symbols from NSE (`nsetools`).  
  - Retrieves live stock prices, company names, and historical data (1 month, 1 year, 5 years) via Yahoo Finance (`yfinance`).

- **Multi-Threaded Company Name Updation**  
  Uses `ThreadPoolExecutor` to fetch and update thousands of company names in parallel for faster performance.

- **Personal Portfolio Management**  
  - Add stocks at current live prices.  
  - Sell stocks (status updated & price locked).  
  - Auto-update live prices for all holdings.  
  - View portfolio table with:
    - Current value  
    - Investment value  
    - Profit/Loss  
    - Status (Holding/Sold)

- **Stock Graph Visualization**  
  Displays three high-quality trend graphs using `matplotlib`:
  - Last 30 days  
  - Last 1 year  
  - Last 5 years  

- **AI-Powered Portfolio Analysis**  
  Uses OpenAI GPT to generate human-like financial analysis covering:
  - Performance  
  - Risk  
  - Best/Worst stocks  
  - Suggestions for portfolio improvement  
  Analysis is automatically saved in the database.

- **Professional PDF Portfolio Report**  
  Generates a downloadable PDF report using `FPDF`, including:
  - User details  
  - Investment summary  
  - Detailed holdings table  
  - AI-generated financial analysis

- **SQL Database Integration**  
  Multiple tables (`users`, `companies`, `portfolio`, `userport`, `analysis`) handle insert, update, delete, and join operations.

- **Strong Error Handling & Input Validation**  
  Manages invalid input, API failures, and missing data safely.

---

## Technologies & Libraries Used

| Library                | Purpose                                      |
|------------------------|----------------------------------------------|
| `colorama`             | Colored terminal text for profit/loss        |
| `openai`               | AI-based portfolio analysis                  |
| `pymysql`              | MySQL database connectivity                  |
| `nsetools`             | Fetch NSE stock symbols                      |
| `yfinance`             | Live prices, company names, historical data  |
| `matplotlib.pyplot`    | Stock graphs and plotting                    |
| `matplotlib.image`     | Displaying logo images                       |
| `datetime`             | Time/date management                         |
| `ThreadPoolExecutor`   | Multithreading for fast data fetching        |
| `tabulate`             | Neatly formatted console tables              |
| `fpdf`                 | PDF report generation                        |

---

## Database Configuration

Update the following in your code to match your MySQL setup:

```python
HOST = "localhost"
USER = "root"
PASSWORD = "bhavya"
DATABASE = "CSProject"
PORT = 3308
```

### SQL Tables

- **users** – Stores user login details  
- **companies** – All NSE companies with symbols and names  
- **portfolio** – Individual share holdings of each user  
- **userport** – Summary table with total investment & profits  
- **analysis** – Stores AI-generated portfolio analysis  

---

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Stoxly-Stock-Portfolio-Tracker.git
   cd Stoxly-Stock-Portfolio-Tracker
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the MySQL database**
   - Create a database named `CSProject`.
   - Create the required tables (`users`, `companies`, `portfolio`, `userport`, `analysis`) as described in the project documentation.
   - Update the database credentials in the code if different from the defaults.

5. **Run the application**
   ```bash
   python main.py
   ```

---

## Project Structure
