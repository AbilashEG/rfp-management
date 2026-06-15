FROM public.ecr.aws/lambda/python:3.12

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy all project source
COPY config.py       ${LAMBDA_TASK_ROOT}/
COPY tools/          ${LAMBDA_TASK_ROOT}/tools/
COPY agent/          ${LAMBDA_TASK_ROOT}/agent/
COPY lambda/         ${LAMBDA_TASK_ROOT}/lambda/

# Lambda handler entry point
CMD ["lambda/rfp_agent_handler.handler"]
