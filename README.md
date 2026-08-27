<p><b>STOXLY</b></p>
<br>
<b>1. User Authentication System</b><br>
   Secure Signup/Login using MySQL database<br>
   Supports login via UserID or Username.<br>
   Stores user credentials and manages session state.<br>
<b>2. Real-Time Stock Data Integration </b><br>      
Uses NSE (nsetools) to fetch all listed company symbols.<br>   
Uses Yahoo Finance (yfinance) to fetch:<br>       
   Live stock prices<br>       
   Historical price data (1 month, 1 year, 5 years)<br>     
   Company names<br>
<b>3. Multi-Threaded Company Name Updation</b><br>    
   Fetches company names using ThreadPoolExecutor to significantly speed up the process.<br>       
   Updates thousands of entries in parallel<br>
   <b>4. Personal Portfolio Management</b><br>
   Users can:<br>
   Add stocks with current live price<br>
   Sell stocks (status updated & price locked upon selling)<br>
   Auto-update live prices for all holdings<br>
   View portfolio table with:<br>
   Current value<br>
   Investment value<br>
   Profit/Loss<br>
   Status (Holding/Sold)<br>
