FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY RFP-main/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Copy application files
COPY RFP-main/agentcore_orchestrator.py .
COPY RFP-main/agentcore_memory.py .
COPY RFP-main/config.py .

# Expose port 8080 for AgentCore Runtime
EXPOSE 8080

# Start HTTP server
CMD ["python", "agentcore_orchestrator.py"]
