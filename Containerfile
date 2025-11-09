FROM python:3.11-slim

WORKDIR /app

# Version als Build Argument (FRÜH definieren, damit Cache nicht betroffen)
ARG APP_VERSION=unknown

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY app_new.py .
COPY models.py .
COPY config.py .
COPY recipe_scraper.py .
COPY index.html .
COPY config/recipe-format-config.json config/
COPY config/themealdb-config.json config/
COPY config/migusto-import-config.json config/
COPY migrations/ migrations/
COPY tests/ tests/
COPY pytest.ini .
COPY alembic.ini .
COPY alembic-test.ini .
COPY alembic-prod.ini .

# ENV Variable setzen (NACH den Copies, damit bei Version-Änderung nur dieser Layer neu gebaut wird)
ENV APP_VERSION=${APP_VERSION}

EXPOSE 80

CMD ["python", "app.py"]
