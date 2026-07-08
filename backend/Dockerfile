FROM python:3.12-slim

# Usuario sin privilegios: nunca corras la API como root
RUN useradd --create-home appuser
WORKDIR /app

# Capa de dependencias separada: solo se reconstruye si cambia requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/

RUN mkdir -p /data/docs /data/state && chown -R appuser:appuser /data /app
USER appuser

EXPOSE 5001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]
