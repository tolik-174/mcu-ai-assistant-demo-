FROM python:3.11-slim

# системні залежності
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# робоча папка
WORKDIR /app

# залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# код
COPY . .

# порт
EXPOSE 8000

# запуск
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]