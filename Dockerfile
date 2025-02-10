# Choosing base image
FROM python:3.9-slim

# Creating working directory
WORKDIR /app

# Copying and installing of dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copying rest of files
COPY . .

# Starting the script
CMD ["python", "app.py"]
