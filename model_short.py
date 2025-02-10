import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error
import logging
import sys
import os
from pymongo import MongoClient

logging.getLogger().setLevel(logging.INFO)

# Loading data from Mongodb
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db_name = os.getenv("MONGO_DB", "weather_data_iso")
db = client[db_name]

args = sys.argv[1:]
for arg in args:
    arg.encode('utf-8').decode('utf-8')

date_start = sys.argv[1]
date_end = sys.argv[2]
city_name = sys.argv[3]

# Get date and time data or specific cities
cursor = db.days.find({
    "city": city_name,
    "datetime": {
        "$gte": date_start,
        "$lte": date_end
    }
})
# Preparation of data
data = list(cursor)
df = pd.DataFrame(data)

# Step 1: Prepare the temperature series

temp_series = df['temp'] 
temp_series = temp_series.dropna().squeeze()

# Step 2: Check for stationarity using the Augmented Dickey-Fuller (ADF) test

result = adfuller(temp_series)
logging.info(f"ADF Statistic: {result[0]}")
logging.info(f"p-value: {result[1]}")

if result[1] > 0.05:
    temp_series_diff = temp_series.diff().dropna()
    logging.info("Data was non-stationary, differencing applied.")
else:
    temp_series_diff = temp_series
    logging.info("Data is already stationary.")

# Step 3: Define and fit the SARIMA model

p, d, q = 1, 1, 1  # Non-seasonal parameters: AR(1), I(1), MA(1)
P, D, Q, m = 1, 1, 1, 7  # Seasonal parameters: AR(1), I(1), MA(1), m=7 for weekly seasonality
# Initialize the SARIMA model with the specified parameters
model = SARIMAX(temp_series_diff,
                order=(p, d, q),
                seasonal_order=(P, D, Q, m),
                enforce_stationarity=False,  
                enforce_invertibility=False)
# Fit the SARIMA model to the data
sarima_fit = model.fit(disp=False)

forecast_steps = 5
forecast = sarima_fit.forecast(steps=forecast_steps)
predict_temp_fahrenheit = forecast.iloc[0]
predict_temp_celsius = round(float((predict_temp_fahrenheit -32)*5/9), 2)
logging.info(f"Forecast for the next {forecast_steps} days: {predict_temp_celsius}")

# Step 4: Evaluate the model (if historical test data is available)

if len(temp_series) > 7:
    y_true = temp_series[-7:]
    forecast_7_days = sarima_fit.get_forecast(steps=7).predicted_mean
    mae = mean_absolute_error(y_true, forecast_7_days)
    logging.info(f"Mean Absolute Error (MAE) for the last 7 days: {mae:.2f}")


logging.info(f'Predicted temperature for {city_name} based on date from {date_start} to {date_end}:\n'
             f'\t{predict_temp_fahrenheit} Fahrenheit degrees, which answers {predict_temp_celsius} Celsius degrees.')