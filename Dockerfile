FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create logs directory
RUN mkdir -p logs

# Make shell scripts executable
RUN chmod +x start_web.sh start_bot.sh

EXPOSE 10000

CMD ["./start_web.sh"]
