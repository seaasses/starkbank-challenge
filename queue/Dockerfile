FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl

ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

COPY requirements.txt .

RUN /root/.local/bin/uv pip install -r requirements.txt --system

COPY . .

# Restart consumer.py if it fails, with production settings
CMD ["sh", "-c", "while true; do python consumer.py || echo 'Consumer crashed, restarting...'; sleep 1; done"]