# 🌤️ weather-mongo  

**Short-term temperature forecasting using MongoDB and Machine Learning**  

## 📜 Table of Contents  
- [📌 Project Overview](#project-overview)  
- [🛠️ Tech Stack](#tech-stack)  
- [⚙️ Installation & Setup](#installation--setup)  
- [📊 Example Forecast Output](#example-forecast-output)  
- [📂 Suggested Project Structure](#suggested-project-structure)  
- [📄 License](#license)  

## 📌 Project Overview  
This project retrieves weather data from an API, stores it in **MongoDB**, and applies **SARIMA** & **Gradient Boosting** to predict short-term temperature changes.  

## 🛠️ Tech Stack  
- **MongoDB** – NoSQL database for storing weather data  
- **Python** – Main programming language  
- **SARIMA & Gradient Boosting** – Forecasting models for temperature prediction  
- **Docker & Docker Compose** – Containerization for easy deployment  

## ⚙️ Installation & Setup  

### 1️⃣ Clone the repository  
```sh
git clone https://github.com/yourusername/weather-mongo.git
cd weather-mongo
```

### 2️⃣ Install dependencies  
```sh
pip install -r requirements.txt
```
### 3️⃣ Set up environment variables & API keys  
Edit the **config/config_cred.json** file with your API keys.  

### 4️⃣ Run the application  


#### 🔹 Run with Docker  
```sh
docker-compose up --build
```

---

## 📊 Example Forecast Output  
![image](https://github.com/user-attachments/assets/2c728cab-b529-4401-a79d-5e9be1693f6c)  

---

## 📂 Suggested Project Structure  

```bash
weather-mongo/
│── config/                    # Configuration files
│   ├── config_cred.json       # Credentials (API keys, MongoDB access)
│   ├── config_locations.json  # Location settings for weather data
│── functions/                 # Custom functions for processing & modeling
│   ├── custom_functions_app.py # Helper functions for the main app
│── models/                    # Machine learning models
│   ├── model.py               # SARIMA & boosting models
│   ├── model_short.py         # Short-term forecasting models
│── docker/                    # Docker-related files
│   ├── Dockerfile             # Docker image configuration
│   ├── docker-compose.yaml    # Docker Compose setup
│── app_main.py                # Main application entry point
│── requirements.txt           # Python dependencies
│── README.md                  # Documentation
```

---

## 📄 License  
Distributed under the **MIT License**. See **LICENSE.txt** for more information.  
```
