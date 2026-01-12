FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY exporter/ ./exporter/

EXPOSE 9493

CMD ["python", "-m", "exporter.main"]
