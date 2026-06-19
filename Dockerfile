FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY RFP-main/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY RFP-main/agentcore_orchestrator.py .
COPY RFP-main/agentcore_memory.py .
COPY RFP-main/config.py .

EXPOSE 8080

CMD ["python", "agentcore_orchestrator.py"]
