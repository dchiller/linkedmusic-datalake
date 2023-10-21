FROM python:3.11.5 as build-container
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_OPTIONS_NO_SETUPTOOLS=true \
    POETRY_VIRTUALENVS_OPTIONS_NO_PIP=true
COPY ./poetry.lock ./pyproject.toml  /app/
RUN pip install poetry==1.6.1
WORKDIR /app
RUN poetry install --without dev

FROM python:3.11.5 as app-container
WORKDIR /app
COPY --from=build-container /app/.venv /app/.venv
COPY ./index_data.py /index_data.py
ENV PYTHONPATH="$PYTHONPATH:/app/.venv/lib/python3.11/site-packages/" \
    PATH="$PATH:/app/.venv/bin/"
EXPOSE 5000
WORKDIR /app/linkedmusic_search