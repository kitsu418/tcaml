FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY . /workspace

RUN pip install --no-cache-dir -r /workspace/requirements.txt

CMD ["python", "main.py", "analyze", "--all"]
