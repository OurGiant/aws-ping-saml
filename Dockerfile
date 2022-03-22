FROM --platform=linux/amd64 python:3.9-alpine3.14
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev
RUN mkdir ~/.aws
RUN ls ~/.aws/samlsts
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "/get-saml/getCredentials.py", "--guideme"]