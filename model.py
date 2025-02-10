import pandas as pd
import sys
import logging
import os
from numpy import nan_to_num
from xgboost import XGBRegressor
from pymongo import MongoClient
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import explained_variance_score, max_error
from sklearn.preprocessing import StandardScaler
from datetime import datetime

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
df['datetime'] = pd.to_datetime(df['datetime'])
df['month'] = df['datetime'].dt.month
df['day_of_year'] = df['datetime'].dt.dayofyear
df['day_of_week'] = df['datetime'].dt.weekday

# Dynamic selection of numeric variables
numeric_features = df.select_dtypes(include=['number']).columns.tolist()
exluded_features = ["tempmax", "tempmin", "feelslikemax", "feelslikemin", "feelslike", "datetime"]
numeric_features = [feature for feature in numeric_features if feature not in exluded_features]


# Define the variable to be predicted (target)
target = 'temp'
# Generate lag data for forecasting
lag_range = range(1, 4)

for feature in numeric_features:
    for lag in lag_range:
        df[f'{feature}_lag{lag}'] = df[feature].shift(lag)

df = df.apply(lambda x: nan_to_num(x, nan=0))

# Create a matrix of explanatory variables and target
X = df[[f'{feature}_lag{lag}' for feature in numeric_features if feature != target for lag in lag_range]]
scaler = StandardScaler()
X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

y = df[target]

# Split data on test and training set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

logging.info("Preparation of data finished")


# Define parameter grid for GridSearchCV
param_grid = {
    'n_estimators': [100, 200],
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [3, 5, 7],
    'subsample': [0.8, 1.0],
    'colsample_bytree': [0.8, 1.0]
}

# Set up GridSearchCV with XGBoost
grid_search = GridSearchCV(XGBRegressor(objective='reg:squarederror', eval_metric='mae'), 
                           param_grid, 
                           cv=3, 
                           scoring='neg_mean_absolute_error', 
                           verbose=1)

# Train model using GridSearchCV
grid_search.fit(X_train, y_train, 
                eval_set=[(X_train, y_train), (X_test, y_test)], 
                early_stopping_rounds=50, 
                verbose=True)

# Get the best model from grid search
model = grid_search.best_estimator_

# Print best parameters
logging.info(f"Best parameters found: {grid_search.best_params_}")

# Prediction of test dataset
y_pred = model.predict(X_test)
y_pred_celsius = [round((temp - 32) * 5 / 9, 2) for temp in y_pred]
# Print predicted temperatures
print(f'Predicted temperatures are: {y_pred_celsius} celsius')  # Displaying first 5 predicted temperatures for example

# Review evaluation metrics
mse = round(float(mean_absolute_error(y_test, y_pred)), 8)
evs = round(float(explained_variance_score(y_test, y_pred)), 8)
max_err = round(float(max_error(y_test, y_pred)), 8)

logging.info(f'MAE: {mse}')
logging.info(f'Explained Variance Score: {evs}')
logging.info(f'Max Error: {max_err}')

# Return Predicted Temperature
predict_temp_fahrenheit = round(float(y_pred[0]), 2)
predict_temp_celsjusz = round(float(y_pred_celsius[0]), 2)

logging.info(f'Predicted first temperature for {city_name} based on date from {date_start} to {date_end}:\n'
             f'\t{predict_temp_fahrenheit} Fahrenheit degrees, which answers {predict_temp_celsjusz} Celsius degrees.')
