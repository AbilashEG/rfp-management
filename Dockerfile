FROM --platform=linux/arm64 public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

# Copy application files
COPY RFP-main/agentcore_orchestrator.py ${LAMBDA_TASK_ROOT}/
COPY RFP-main/agentcore_memory.py ${LAMBDA_TASK_ROOT}/
COPY RFP-main/config.py ${LAMBDA_TASK_ROOT}/
COPY RFP-main/requirements.txt .

# Install dependencies (pip will resolve rpds-py correctly in Linux environment)
RUN pip install -r requirements.txt --no-cache-dir

# Set the CMD to your handler
CMD [ "agentcore_orchestrator.handler" ]
