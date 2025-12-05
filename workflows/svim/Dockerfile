FROM python:3.14-slim

# Evitar buffering em logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        python3-dev \
        pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Copia requirements e instala deps
COPY workflows/svim/agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do agente
COPY workflows/svim/agents ./agents

# Garante que /app está no PYTHONPATH
ENV PYTHONPATH=/app

# Entry-point padrão (pode ser sobrescrito pelo Kestra se quiser)
CMD ["python", "-m", "agents.main"]
