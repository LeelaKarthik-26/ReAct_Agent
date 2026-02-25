FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY requirements.txt .

RUN uv pip install --system -r requirements.txt

COPY . .

#Expose Port
EXPOSE 8000

CMD ["python","main.py"]