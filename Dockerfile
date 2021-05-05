FROM public.ecr.aws/lambda/python:3.8
LABEL Author="Thrivikram Mudunuri"
COPY . ./
RUN pip install -r requirements.txt
CMD ["main.covicheck_pubsub"]