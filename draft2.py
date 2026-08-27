from colorama import Fore, Style
from openai import OpenAI
import pymysql
from nsetools import Nse
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import tabulate
from fpdf import FPDF
import os


# ============================================================
# DATABASE CONNECTION
# ============================================================

try:
    db = pymysql.connect(
        host="localhost",
        user="root",
        password="spiderman",
        database="SIH",
        port=3306
    )
    print("Database connected successfully.")

except Exception as e:
    print("Could not connect to database:", e)
    exit()


# ============================================================
# GLOBAL LOGIN VARIABLES
# ============================================================

logged_in = False
username = None
user_id = None


# ============================================================
# SIGNUP
# ============================================================

def signup():
    global logged_in
    global username
    global user_id

    cur = db.cursor()

    try:
        # Get next User ID
        cur.execute("SELECT COALESCE(MAX(userid), 0) FROM Users")
        result = cur.fetchone()

        # IMPORTANT:
        # fetchone() is called only ONCE
        x = result[0] if result else 0

        user_id = int(x) + 1

        username = input("Enter username: ").strip()

        if not username:
            print("Username cannot be empty.")
            return

        password = input("Enter password: ")
        pass_con = input("Confirm password: ")

        if password != pass_con:
            print("Password does not match!")
            return

        # Check whether username already exists
        cur.execute(
            "SELECT userid FROM Users WHERE username = %s",
            (username,)
        )

        existing_user = cur.fetchone()

        if existing_user:
            print("Username already exists. Please choose another username.")
            return

        # Insert new user
        cur.execute(
            """
            INSERT INTO Users
                (userid, username, password)
            VALUES
                (%s, %s, %s)
            """,
            (user_id, username, password)
        )

        db.commit()

        logged_in = True

        print("\nSuccessfully signed up!")
        print("Your UserID is:", user_id)
        print("Note your UserID for future use.")
        print("LOGGED IN AS", username)

    except Exception as error:
        db.rollback()
        print("Signup failed:", error)

    finally:
        cur.close()


# ============================================================
# LOGIN
# ============================================================

def authenticate():
    global logged_in
    global user_id
    global username

    cur = db.cursor()

    try:
        logged_in = False

        print("\n1. Login using UserID.")
        print("2. Login using UserName.")

        try:
            ch = int(input("Enter choice: "))

        except ValueError:
            print("Please enter a valid number.")
            return

        # ----------------------------------------------------
        # LOGIN USING USER ID
        # ----------------------------------------------------

        if ch == 1:

            try:
                id1 = int(input("Enter UserID: "))

            except ValueError:
                print("Invalid UserID.")
                return

            password = input("Enter password: ")

            cur.execute(
                """
                SELECT userid, username, password
                FROM Users
                WHERE userid = %s
                """,
                (id1,)
            )

            user = cur.fetchone()

            if user and user[2] == password:

                logged_in = True
                user_id = user[0]
                username = user[1]

                print("LOGGED IN AS", username)

            else:

                print("Incorrect UserID or password.")

        # ----------------------------------------------------
        # LOGIN USING USERNAME
        # ----------------------------------------------------

        elif ch == 2:

            id1 = input("Enter UserName: ").strip()
            password = input("Enter password: ")

            cur.execute(
                """
                SELECT userid, username, password
                FROM Users
                WHERE username = %s
                """,
                (id1,)
            )

            user = cur.fetchone()

            if user and user[2] == password:

                logged_in = True
                user_id = user[0]
                username = user[1]

                print("LOGGED IN AS", username)

            else:

                print("Incorrect username or password.")

        else:

            print("INVALID CHOICE")
            print("TRY AGAIN!")

    except Exception as error:

        print("Login error:", error)

    finally:

        cur.close()


# ============================================================
# FETCH LIVE NSE DATA
# ============================================================

def fetchlivedata():

    cur = db.cursor()

    print("\nFetching live data...")

    try:

        nse = Nse()

        all_stock_codes = nse.get_stock_codes()

        print("Stock codes fetched:", len(all_stock_codes))

        # Delete existing companies
        cur.execute("DELETE FROM companies")
        db.commit()

        companyid = 0

        for symbol in all_stock_codes:

            # Skip unwanted entries
            if symbol == "SYMBOL":
                continue

            companyid += 1

            try:

                cur.execute(
                    """
                    INSERT INTO companies
                        (companyid, symbol)
                    VALUES
                        (%s, %s)
                    """,
                    (companyid, symbol + ".NS")
                )

                db.commit()

                print(
                    f"{companyid}. {symbol}.NS inserted successfully."
                )

            except Exception as error:

                db.rollback()

                print(
                    f"Could not insert {symbol}: {error}"
                )

        print("\nLive company data fetched successfully.")

    except Exception as error:

        print("Error fetching live data:", error)

    finally:

        cur.close()


# ============================================================
# FETCH COMPANY NAME FROM YAHOO FINANCE
# ============================================================

def fetch_company_name(symbol):

    try:

        ticker = yf.Ticker(symbol)

        info = ticker.info

        return info.get("longName") or info.get("shortName")

    except Exception as error:

        print(
            f"Error fetching name for {symbol}: {error}"
        )

        return None


# ============================================================
# UPDATE COMPANY NAMES IN PARALLEL
# ============================================================

def update_company_names_parallel(start_from_id=1):

    cur = db.cursor()

    try:

        cur.execute(
            """
            SELECT companyid, symbol
            FROM companies
            WHERE companyid >= %s
            """,
            (start_from_id,)
        )

        companies = cur.fetchall()

        print(
            f"Found {len(companies)} companies "
            f"with companyid >= {start_from_id}."
        )

        with ThreadPoolExecutor(max_workers=3) as executor:

            future_to_company = {
                executor.submit(
                    fetch_company_name,
                    symbol
                ): (companyid, symbol)

                for companyid, symbol in companies
            }

            for future in as_completed(future_to_company):

                companyid, symbol = future_to_company[future]

                try:

                    name = future.result()

                    if name:

                        cur.execute(
                            """
                            UPDATE companies
                            SET companyname = %s
                            WHERE companyid = %s
                            """,
                            (name, companyid)
                        )

                        db.commit()

                        print(
                            f"{symbol} -> {name}"
                        )

                    else:

                        print(
                            f"No name found for {symbol}"
                        )

                except Exception as error:

                    print(
                        f"Error updating {symbol}: {error}"
                    )

        print("\nCompany name update complete.")

    except Exception as error:

        db.rollback()

        print(
            "Could not update company names:",
            error
        )

    finally:

        cur.close()


# ============================================================
# SEARCH COMPANY
# ============================================================

def search_company(keyword):

    cur = db.cursor()

    try:

        cur.execute(
            """
            SELECT companyid, companyname, symbol
            FROM companies
            WHERE companyname LIKE %s
               OR symbol LIKE %s
            """,
            (
                f"%{keyword}%",
                f"%{keyword}%"
            )
        )

        data = cur.fetchall()

        if not data:

            print("\nNo companies found.")

        else:

            print("\nSearch Results:")
            print("---------------------------------------------")
            print("COMPANY ID | COMPANY NAME | SYMBOL")
            print("---------------------------------------------")

            for company_id, company_name, symbol in data:

                print(
                    f"Code: {company_id} | "
                    f"{company_name or 'Unknown'} | "
                    f"{symbol}"
                )

            print("---------------------------------------------")

    except Exception as error:

        print("Search error:", error)

    finally:

        cur.close()


# ============================================================
# SHOW STOCK GRAPH
# ============================================================

def show_stock_graph(comp_id):

    cur = db.cursor()

    try:

        cur.execute(
            """
            SELECT symbol, companyname
            FROM companies
            WHERE companyid = %s
            """,
            (comp_id,)
        )

        stock = cur.fetchone()

    except Exception as error:

        print("Could not find company:", error)
        return

    finally:

        cur.close()

    if not stock:

        print("Invalid company code.")
        return

    symbol, name = stock

    name = name or symbol

    print(f"\nFetching data for {name}...")

    try:

        ticker = yf.Ticker(symbol)

        month_data = ticker.history(period="1mo")
        year_data = ticker.history(period="1y")
        five_year_data = ticker.history(period="5y")

        if month_data.empty:
            print("No monthly historical data available.")
            return

        if year_data.empty:
            print("No yearly historical data available.")
            return

        if five_year_data.empty:
            print("No 5-year historical data available.")
            return

        plt.style.use("seaborn-v0_8-darkgrid")

        fig, axes = plt.subplots(
            1,
            3,
            figsize=(14, 4),
            dpi=100
        )

        graphs = [
            ("Last Month", month_data, "#00c853"),
            ("Last Year", year_data, "#2962ff"),
            ("Last 5 Years", five_year_data, "#ff6d00")
        ]

        for axis, (title, data, color) in zip(
            axes,
            graphs
        ):

            axis.plot(
                data.index,
                data["Close"],
                color=color,
                linewidth=2
            )

            axis.set_title(
                title,
                fontsize=11,
                fontweight="bold"
            )

            axis.set_xlabel("Date")
            axis.set_ylabel("Price (Rs)")

            axis.tick_params(
                axis="x",
                rotation=30
            )

        plt.suptitle(
            f"{name} Stock Trends Overview",
            fontsize=13,
            fontweight="bold"
        )

        plt.tight_layout()

        plt.show()

    except Exception as error:

        print(
            "Could not fetch or display stock data:",
            error
        )


# ============================================================
# ADD STOCK TO PORTFOLIO
# ============================================================

def add_stock(userid, idco):

    if not logged_in:

        print("LOGIN FIRST")
        return

    try:

        shares = int(
            input("Enter number of shares: ")
        )

        if shares <= 0:

            print(
                "Number of shares must be greater than zero."
            )

            return

    except ValueError:

        print(
            "Enter a valid whole number of shares."
        )

        return

    cur = db.cursor()

    try:

        # Find selected company
        cur.execute(
            """
            SELECT symbol, companyname
            FROM companies
            WHERE companyid = %s
            """,
            (idco,)
        )

        result = cur.fetchone()

        if not result:

            print("Invalid company code.")
            return

        symbol = result[0]

        # Fetch current market price
        print(
            f"Fetching current price for {symbol}..."
        )

        data = yf.Ticker(symbol).history(
            period="1d"
        )

        if data.empty:

            print(
                f"No current price data available "
                f"for {symbol}."
            )

            return

        price = float(
            data["Close"].iloc[-1]
        )

        # Generate next portfolio ID
        cur.execute(
            """
            SELECT COALESCE(MAX(portid), 0) + 1
            FROM portfolio
            """
        )

        portid = cur.fetchone()[0]

        # Insert portfolio record
        cur.execute(
            """
            INSERT INTO portfolio
                (
                    portid,
                    userid,
                    companyid,
                    shares,
                    price,
                    strtprice,
                    Curr_sold
                )
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                portid,
                userid,
                idco,
                shares,
                price,
                price,
                "Holding"
            )
        )

        db.commit()

        print(
            f"{shares} shares of {symbol} "
            f"added at Rs {price:.2f} each."
        )

    except Exception as error:

        db.rollback()

        print(
            "Could not add stock:",
            error
        )

    finally:

        cur.close()


# ============================================================
# SEARCH STOCK PRICE
# ============================================================

def srchprice(comp_id):

    cur = db.cursor()

    try:

        cur.execute(
            """
            SELECT symbol
            FROM companies
            WHERE companyid = %s
            """,
            (comp_id,)
        )

        result = cur.fetchone()

        if not result:

            print("Invalid company code.")
            return

        symbol = result[0]

        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period="1d"
        )

        if data.empty:

            print(
                f"No price data available for {symbol}."
            )

            return

        price = float(
            data["Close"].iloc[-1]
        )

        print(
            f"Share Price of {symbol} "
            f"is Rs {price:.2f} each."
        )

    except Exception as error:

        print(
            "Could not fetch stock price:",
            error
        )

    finally:

        cur.close()


# ============================================================
# UPDATE PORTFOLIO PRICES
# ============================================================

def update_prices():

    cur = db.cursor()

    print(
        "\nUpdating live stock prices..."
    )

    try:

        cur.execute(
            """
            SELECT
                p.portid,
                c.symbol
            FROM portfolio p
            JOIN companies c
                ON p.companyid = c.companyid
            WHERE p.Curr_sold = 'Holding'
            """
        )

        data = cur.fetchall()

        for pid, symbol in data:

            try:

                ticker = yf.Ticker(symbol)

                history = ticker.history(
                    period="1d"
                )

                if history.empty:

                    print(
                        f"No price data for {symbol}"
                    )

                    continue

                new_price = float(
                    history["Close"].iloc[-1]
                )

                datetime1 = datetime.now()

                cur.execute(
                    """
                    UPDATE portfolio
                    SET
                        price = %s,
                        last_updated = %s
                    WHERE portid = %s
                    """,
                    (
                        new_price,
                        datetime1,
                        pid
                    )
                )

                print(
                    f"{symbol} updated to "
                    f"Rs {new_price:.2f}"
                )

            except Exception as error:

                print(
                    f"Could not update {symbol}: "
                    f"{error}"
                )

        db.commit()

        print(
            "\nPrices updated successfully."
        )

    except Exception as error:

        db.rollback()

        print(
            "Could not update portfolio prices:",
            error
        )

    finally:

        cur.close()


# ============================================================
# VIEW PORTFOLIO
# ============================================================

def view_portfolio1(user_id):

    cur = db.cursor()

    try:

        # Update prices first
        update_prices()

        cur.execute(
            """
            SELECT
                COALESCE(
                    c.companyname,
                    c.symbol
                ) AS companyname,

                p.shares,
                p.strtprice,
                p.price,

                (p.shares * p.price) AS value,

                (
                    (p.price - p.strtprice)
                    * p.shares
                ) AS profit,

                p.Curr_sold AS presently

            FROM portfolio p

            JOIN companies c
                ON p.companyid = c.companyid

            WHERE p.userid = %s
            """,
            (user_id,)
        )

        data = cur.fetchall()

        if not data:

            print(
                "No stocks found in this portfolio."
            )

            return

        rec = []

        for (
            company,
            shares,
            start_price,
            current_price,
            value,
            profit,
            status
        ) in data:

            rec.append(
                (
                    company or "Unknown",
                    int(shares),
                    round(float(start_price), 2),
                    round(float(current_price), 2),
                    round(float(value), 2),
                    round(float(profit), 2),
                    status
                )
            )

        # Get portfolio holder name
        cur.execute(
            """
            SELECT username
            FROM users
            WHERE userid = %s
            """,
            (user_id,)
        )

        user = cur.fetchone()

        name = (
            user[0]
            if user
            else "Unknown User"
        )

        # Portfolio calculations
        total_investment = sum(
            row[1] * row[2]
            for row in rec
        )

        current_value = sum(
            row[4]
            for row in rec
        )

        profit = (
            current_value
            - total_investment
        )

        # Refresh user portfolio summary
        cur.execute(
            """
            DELETE FROM userport
            WHERE userid = %s
            """,
            (user_id,)
        )

        cur.execute(
            """
            INSERT INTO userport
                (
                    userid,
                    Total_inv,
                    Currentprice,
                    profit,
                    last_updated
                )
            VALUES
                (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                total_investment,
                current_value,
                profit,
                datetime.now()
            )
        )

        db.commit()

        print(
            f"\nUserID: {user_id}"
        )

        print(
            f"NAME OF THE PORTFOLIO HOLDER: {name}"
        )

        print(
            f"TOTAL INVESTMENT: "
            f"Rs {total_investment:.2f}"
        )

        print(
            f"Current Value: "
            f"Rs {current_value:.2f}"
        )

        if profit >= 0:

            print(
                Fore.GREEN
                + f"Net Profit: Rs {profit:.2f}"
                + Style.RESET_ALL
            )

        else:

            print(
                Fore.RED
                + f"Net Loss: Rs {abs(profit):.2f}"
                + Style.RESET_ALL
            )

        print()

        print(
            tabulate.tabulate(
                rec,
                headers=[
                    "Company Name",
                    "No. of Shares",
                    "Bought at Price",
                    "Current Price",
                    "Total Value",
                    "Profit",
                    "Presently"
                ],
                tablefmt="pretty"
            )
        )

    except Exception as error:

        db.rollback()

        print(
            "Could not display portfolio:",
            error
        )

    finally:

        cur.close()


# ============================================================
# AI PORTFOLIO ANALYSIS
# ============================================================

def aianalysis(user_id):

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:

        print(
            "OPENAI_API_KEY is not set."
        )

        return None

    cur = db.cursor()

    try:

        print(
            "AI Generating response..."
        )

        cur.execute(
            """
            SELECT
                COALESCE(
                    c.companyname,
                    c.symbol
                ),

                p.shares,
                p.strtprice,
                p.price,
                p.Curr_sold

            FROM portfolio p

            JOIN companies c
                ON p.companyid = c.companyid

            WHERE p.userid = %s
            """,
            (user_id,)
        )

        data = cur.fetchall()

        if not data:

            print(
                "No portfolio data found for analysis."
            )

            return None

        portfolio_summary = []

        total_inv = 0.0
        total_val = 0.0

        for (
            company,
            shares,
            start_price,
            current_price,
            status
        ) in data:

            investment = (
                float(shares)
                * float(start_price)
            )

            value = (
                float(shares)
                * float(current_price)
            )

            profit = value - investment

            total_inv += investment
            total_val += value

            portfolio_summary.append(
                f"{company}: "
                f"{shares} shares, "
                f"bought at Rs {float(start_price):.2f}, "
                f"now Rs {float(current_price):.2f}, "
                f"profit/loss Rs {profit:.2f}, "
                f"status: {status}."
            )

        total_profit = (
            total_val
            - total_inv
        )

        returns_pct = (
            total_profit
            / total_inv
            * 100
        ) if total_inv else 0

        prompt = f"""
You are an expert stock portfolio analyst.

User ID: {user_id}

Total Investment:
Rs {total_inv:,.2f}

Current Value:
Rs {total_val:,.2f}

Net Profit/Loss:
Rs {total_profit:,.2f}
({returns_pct:.2f}%)

Holdings:

{chr(10).join(portfolio_summary)}

Write a concise 6-8 sentence analysis covering:

- Portfolio health and diversification
- Strongest and weakest positions
- Risk exposure
- Possible rebalancing improvements

Use plain, human-friendly language.

This is educational information,
not personalized financial advice.
"""

        client = OpenAI(
            api_key=api_key
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",

            messages=[
                {
                    "role": "system",
                    "content":
                        "You are an expert stock "
                        "portfolio analyst."
                },

                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        ai_analysis = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        # Update existing analysis
        cur.execute(
            """
            UPDATE analysis
            SET aianalysis = %s
            WHERE userid = %s
            """,
            (
                ai_analysis,
                user_id
            )
        )

        # Insert if no previous analysis
        if cur.rowcount == 0:

            cur.execute(
                """
                INSERT INTO analysis
                    (userid, aianalysis)
                VALUES
                    (%s, %s)
                """,
                (
                    user_id,
                    ai_analysis
                )
            )

        db.commit()

        return ai_analysis

    except Exception as error:

        db.rollback()

        print(
            "Error generating AI analysis:",
            error
        )

        return None

    finally:

        cur.close()


# ============================================================
# GENERATE PDF
# ============================================================

def prntpdf(user_id):

    cur = None

    try:

        # Make sure portfolio summary exists
        cur = db.cursor()

        cur.execute(
            """
            SELECT
                userid,
                Total_inv,
                Currentprice,
                profit
            FROM userport
            WHERE userid = %s
            """,
            (user_id,)
        )

        dat = cur.fetchone()

        if not dat:

            print(
                "No portfolio summary found."
            )

            print(
                "Please view your portfolio first."
            )

            return

        pdf = FPDF()

        pdf.add_page()

        pdf.set_font(
            "Arial",
            "B",
            16
        )

        pdf.cell(
            200,
            10,
            txt="STOXLY PORTFOLIO",
            ln=True,
            align="C"
        )

        pdf.ln(10)

        pdf.set_font(
            "Arial",
            size=12
        )

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        pdf.cell(
            200,
            10,
            txt=f"USERID: {dat[0]}",
            ln=True,
            align="L"
        )

        pdf.cell(
            200,
            10,
            txt=f"USERNAME: {username}",
            ln=True,
            align="L"
        )

        pdf.cell(
            200,
            10,
            txt=f"Date: {today}",
            ln=True,
            align="L"
        )

        pdf.cell(
            0,
            10,
            txt=f"Total Investment: Rs {float(dat[1]):.2f}",
            ln=True
        )

        pdf.cell(
            0,
            10,
            txt=f"Current Price: Rs {float(dat[2]):.2f}",
            ln=True
        )

        pdf.cell(
            0,
            10,
            txt=f"Profit: Rs {float(dat[3]):.2f}",
            ln=True
        )

        pdf.ln(3)

        pdf.set_font(
            "Arial",
            "B",
            12
        )

        pdf.cell(
            0,
            10,
            txt="PORTFOLIO DETAILS",
            ln=True,
            align="C"
        )

        pdf.ln(3)

        headers = [
            "Company",
            "Shares",
            "Bought@",
            "Current",
            "Value",
            "Profit"
        ]

        col_widths = [
            50,
            25,
            25,
            25,
            30,
            30
        ]

        pdf.set_font(
            "Arial",
            "B",
            11
        )

        for i, header in enumerate(headers):

            pdf.cell(
                col_widths[i],
                10,
                header,
                border=1,
                align="C"
            )

        pdf.ln()

        cur.execute(
            """
            SELECT
                c.companyname,
                p.shares,
                p.strtprice,
                p.price,

                (p.shares * p.price) AS value,

                (
                    (p.price - p.strtprice)
                    * p.shares
                ) AS profit

            FROM portfolio p

            JOIN companies c
                ON p.companyid = c.companyid

            WHERE p.userid = %s
            """,
            (user_id,)
        )

        data = cur.fetchall()

        pdf.set_font(
            "Arial",
            size=10
        )

        for row in data:

            company = (
                row[0]
                or "Unknown"
            )

            pdf.cell(
                col_widths[0],
                10,
                str(company)[:25],
                border=1
            )

            pdf.cell(
                col_widths[1],
                10,
                str(row[1]),
                border=1,
                align="C"
            )

            pdf.cell(
                col_widths[2],
                10,
                f"{float(row[2]):.2f}",
                border=1,
                align="C"
            )

            pdf.cell(
                col_widths[3],
                10,
                f"{float(row[3]):.2f}",
                border=1,
                align="C"
            )

            pdf.cell(
                col_widths[4],
                10,
                f"{float(row[4]):.2f}",
                border=1,
                align="C"
            )

            pdf.cell(
                col_widths[5],
                10,
                f"{float(row[5]):.2f}",
                border=1,
                align="C"
            )

            pdf.ln()

        # AI analysis
        a = aianalysis(user_id)

        pdf.ln(5)

        pdf.set_font(
            "Arial",
            "B",
            12
        )

        pdf.cell(
            0,
            10,
            txt="AI Portfolio Summary",
            ln=True,
            align="C"
        )

        pdf.ln(3)

        pdf.set_font(
            "Arial",
            size=10
        )

        if a:

            # FPDF's default Arial font may not support
            # certain Unicode characters.
            # Replace problematic characters.
            safe_ai = (
                a.replace("₹", "Rs")
                 .replace("→", "->")
                 .replace("—", "-")
                 .replace("–", "-")
            )

            pdf.multi_cell(
                0,
                5,
                txt=safe_ai,
                align="L"
            )

        else:

            pdf.multi_cell(
                0,
                5,
                txt="AI analysis was not available.",
                align="L"
            )

        pdf.ln(15)

        pdf.set_font(
            "Arial",
            "I",
            11
        )

        pdf.cell(
            0,
            10,
            txt="Thank you for choosing Stoxly!",
            ln=True,
            align="C"
        )

        pdf.cell(
            0,
            10,
            txt="This is a computer-generated portfolio summary.",
            ln=True,
            align="C"
        )

        filename = (
            f"Portfolio_{username}.pdf"
        )

        pdf.output(filename)

        print(
            f"\nPortfolio saved as '{filename}'"
        )

    except Exception as error:

        print(
            "Error generating PDF:",
            error
        )

    finally:

        if cur:
            cur.close()


# ============================================================
# SELL STOCK
# ============================================================

def sellstock(user_id):

    print(
        "\nYour Portfolio Stocks:"
    )

    cur = db.cursor()

    try:

        cur.execute(
            """
            SELECT
                c.companyid,
                c.companyname,
                c.symbol,
                p.shares

            FROM portfolio p

            JOIN companies c
                ON p.companyid = c.companyid

            WHERE p.userid = %s
              AND p.Curr_sold = 'Holding'
            """,
            (user_id,)
        )

        data = cur.fetchall()

        if not data:

            print(
                "You have no stocks to sell."
            )

            return

        for d in data:

            print(
                f"Code: {d[0]} | "
                f"{d[1] or d[2]} | "
                f"Shares: {d[3]}"
            )

        try:

            comp_id = int(
                input(
                    "\nEnter company code to sell "
                    "its stocks: "
                )
            )

        except ValueError:

            print(
                "Invalid input. Please enter a number."
            )

            return

        # Check whether selected stock belongs to user
        cur.execute(
            """
            SELECT
                portid,
                shares
            FROM portfolio
            WHERE companyid = %s
              AND userid = %s
              AND Curr_sold = 'Holding'
            """,
            (
                comp_id,
                user_id
            )
        )

        stock = cur.fetchone()

        if not stock:

            print(
                "Invalid company code or stock "
                "is already sold."
            )

            return

        # Mark stock as sold
        cur.execute(
            """
            UPDATE portfolio
            SET Curr_sold = 'Sold'
            WHERE companyid = %s
              AND userid = %s
              AND Curr_sold = 'Holding'
            """,
            (
                comp_id,
                user_id
            )
        )

        db.commit()

        print(
            "Stock sold successfully!"
        )

    except Exception as error:

        db.rollback()

        print(
            "Could not sell stock:",
            error
        )

    finally:

        cur.close()


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # DISPLAY STOXLY IMAGE
    # ========================================================

    try:

        img = mpimg.imread(
            r"C:\Users\btute\OneDrive\Desktop\study\cs\stoxly.jpeg.jpg"
        )

        plt.imshow(img)

        plt.axis("off")

        plt.tight_layout()

        plt.show()

    except Exception as error:

        print(
            "Could not display Stoxly image:",
            error
        )


    # ========================================================
    # FIRST MENU
    # ========================================================

    while True:

        print("\n======================================")
        print("              STOXLY")
        print("======================================")
        print("1. Search for a company")
        print("2. Login")
        print("3. Signup")
        print("4. Exit")
        print("======================================")

        try:

            ch = int(
                input("Enter choice: ")
            )

        except ValueError:

            print(
                "Please enter a valid number."
            )

            continue


        # ====================================================
        # SEARCH COMPANY
        # ====================================================

        if ch == 1:

            keyword = input(
                "Enter keyword to search companies: "
            )

            search_company(keyword)

            try:

                idco = int(
                    input(
                        "Select a company (Enter ID): "
                    )
                )

            except ValueError:

                print(
                    "Invalid company ID."
                )

                continue

            try:

                show_stock_graph(idco)

                srchprice(idco)

            except Exception as error:

                print(
                    "Error displaying company information:",
                    error
                )


        # ====================================================
        # LOGIN
        # ====================================================

        elif ch == 2:

            authenticate()

            if logged_in:

                break

            else:

                print(
                    "Login failed."
                )


        # ====================================================
        # SIGNUP
        # ====================================================

        elif ch == 3:

            signup()

            if logged_in:

                print(
                    "\nNO STOCKS FOUND!"
                )

                print(
                    "ADD STOCK DATA TO USE "
                    "OTHER FEATURES."
                )

                x = input(
                    "Enter 1 to add a stock: "
                )

                if x == "1":

                    keyword = input(
                        "Search company: "
                    )

                    search_company(keyword)

                    try:

                        idco = int(
                            input(
                                "Enter company ID: "
                            )
                        )

                    except ValueError:

                        print(
                            "Invalid company ID."
                        )

                        break

                    add_stock(
                        user_id,
                        idco
                    )

                else:

                    print(
                        "No stock added."
                    )

                break


        # ====================================================
        # EXIT
        # ====================================================

        elif ch == 4:

            print(
                "Program ended."
            )

            db.close()

            exit()


        else:

            print(
                "Wrong choice. Please try again."
            )


    # ========================================================
    # USER PORTFOLIO MENU
    # ========================================================

    if logged_in:

        print("\n======================================")

        print(
            "WELCOME",
            username
        )

        print("======================================")


        # ====================================================
        # SHOW PORTFOLIO AFTER LOGIN
        # ====================================================

        try:

            view_portfolio1(
                user_id
            )

        except Exception as error:

            print(
                "Error displaying portfolio:",
                error
            )


        # ====================================================
        # DASHBOARD
        # ====================================================

        while True:

            print("\n======================================")
            print("           STOXLY DASHBOARD")
            print("======================================")
            print("1. See graph data of a company")
            print("2. Get AI analysis for your portfolio")
            print("3. Search a company")
            print("4. Show updated portfolio")
            print("5. Sell a stock")
            print("6. Download portfolio as PDF")
            print("7. Exit")
            print("======================================")

            try:

                choice = int(
                    input("Enter choice: ")
                )

            except ValueError:

                print(
                    "Please enter a valid number."
                )

                continue


            # =================================================
            # 1. GRAPH
            # =================================================

            if choice == 1:

                cur = db.cursor()

                try:

                    cur.execute(
                        """
                        SELECT
                            c.companyid,
                            c.companyname,
                            c.symbol

                        FROM portfolio p

                        JOIN companies c
                            ON p.companyid = c.companyid

                        WHERE p.userid = %s
                          AND p.Curr_sold = 'Holding'
                        """,
                        (user_id,)
                    )

                    data = cur.fetchall()

                finally:

                    cur.close()

                if not data:

                    print(
                        "You have no stocks to visualize."
                    )

                else:

                    print(
                        "\nYour Portfolio Stocks:"
                    )

                    for d in data:

                        print(
                            f"Code: {d[0]} | "
                            f"{d[1] or d[2]}"
                        )

                    try:

                        comp_id = int(
                            input(
                                "\nEnter company code "
                                "to view graph: "
                            )
                        )

                    except ValueError:

                        print(
                            "Invalid company code."
                        )

                        continue

                    show_stock_graph(
                        comp_id
                    )


            # =================================================
            # 2. AI ANALYSIS
            # =================================================

            elif choice == 2:

                a = aianalysis(
                    user_id
                )

                if a:

                    print(
                        "\nAI Portfolio Analysis"
                    )

                    print(
                        "--------------------------------------"
                    )

                    print(a)

                    print(
                        "--------------------------------------"
                    )

                else:

                    print(
                        "Could not generate AI analysis."
                    )


            # =================================================
            # 3. SEARCH COMPANY
            # =================================================

            elif choice == 3:

                keyword = input(
                    "Enter keyword to search companies: "
                )

                search_company(
                    keyword
                )

                try:

                    idco = int(
                        input(
                            "Select a company (Enter ID): "
                        )
                    )

                except ValueError:

                    print(
                        "Invalid company ID."
                    )

                    continue

                cur = db.cursor()

                try:

                    cur.execute(
                        """
                        SELECT
                            companyname,
                            symbol
                        FROM companies
                        WHERE companyid = %s
                        """,
                        (idco,)
                    )

                    rec = cur.fetchone()

                finally:

                    cur.close()

                if not rec:

                    print(
                        "INVALID COMPANY."
                    )

                else:

                    print(
                        "\nCompany:",
                        rec[0] or rec[1]
                    )

                    show_stock_graph(
                        idco
                    )

                    srchprice(
                        idco
                    )

                    add_choice = input(
                        "Add stock to your portfolio? (y/n): "
                    )

                    if add_choice.upper() == "Y":

                        add_stock(
                            user_id,
                            idco
                        )

                    else:

                        print(
                            "Stock not added."
                        )


            # =================================================
            # 4. UPDATED PORTFOLIO
            # =================================================

            elif choice == 4:

                view_portfolio1(
                    user_id
                )


            # =================================================
            # 5. SELL STOCK
            # =================================================

            elif choice == 5:

                sellstock(
                    user_id
                )


            # =================================================
            # 6. PDF REPORT
            # =================================================

            elif choice == 6:

                prntpdf(
                    user_id
                )


            # =================================================
            # 7. EXIT
            # =================================================

            elif choice == 7:

                print(
                    "\nThank you for using Stoxly!"
                )

                break


            else:

                print(
                    "Wrong choice. Please enter 1-7."
                )


    # ========================================================
    # CLOSE DATABASE
    # ========================================================

    if db.open:

        db.close()

    print(
        "\nDatabase connection closed."
    )

    print(
        "Stoxly closed successfully."
    )