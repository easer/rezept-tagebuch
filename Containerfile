FROM python:3.11-slim

WORKDIR /app

# Version als Build Argument (FRÜH definieren, damit Cache nicht betroffen)
ARG APP_VERSION=unknown

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY index.html .

# ENV Variable setzen (NACH den Copies, damit bei Version-Änderung nur dieser Layer neu gebaut wird)
ENV APP_VERSION=${APP_VERSION}

EXPOSE 80

CMD ["python", "app.py"]
