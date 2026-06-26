FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

COPY RFP-main/lambda/rfp_api_handler.py ${LAMBDA_TASK_ROOT}/
COPY RFP-main/config.py ${LAMBDA_TASK_ROOT}/
COPY RFP-main/requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

CMD ["rfp_api_handler.handler"]
