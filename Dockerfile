FROM python:3.12
WORKDIR /app
COPY poetry.lock pyproject.toml poetry.toml ./
RUN pip install poetry && poetry install --no-root
COPY . .
