FROM public.ecr.aws/lambda/python:3.12

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY

ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY

# Set HOME to /tmp to avoid IO error
ENV HOME=/tmp

WORKDIR /var/task

# Copy only necessary files
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy application files
COPY . ./

# Set Lambda handler
CMD [ "lambda_function.handler" ]
