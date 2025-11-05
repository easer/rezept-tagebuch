FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY index.html .

# Version als Build Argument und ENV Variable
ARG APP_VERSION=unknown
ENV APP_VERSION=${APP_VERSION}

EXPOSE 80

CMD ["python", "app.py"]
