FROM python:3.13-slim

# Evitar buffering em logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copia requirements e instala deps
COPY ./agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do agente
COPY agents ./agents

# Garante que /app está no PYTHONPATH
ENV PYTHONPATH=/app

# Entry-point padrão (pode ser sobrescrito pelo Kestra se quiser)
CMD ["python", "-m", "agents.main"]
