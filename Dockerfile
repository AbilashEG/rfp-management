FROM public.ecr.aws/lambda/python:3.12

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install dependencies
COPY RFP-main/requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy orchestrator files
COPY RFP-main/agentcore_orchestrator.py .
COPY RFP-main/agentcore_memory.py .
COPY RFP-main/config.py .

# Set the CMD to your handler (this will be overridden per Lambda)
CMD [ "agentcore_orchestrator.handler" ]
