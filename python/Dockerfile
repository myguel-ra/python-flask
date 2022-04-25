# Overly complicated multistage build to reduce incremental upload on push to
# *just* the files from this project, ie about 12 KiB. This could almost
# certainly be simpler.


# Export dependencies as requirements.txt
FROM python:3.7-slim as gen-requirements

RUN python3 -m pip install --user pipx && python3 -m pipx ensurepath

# Dockerfile RUN directove runs commands in a non-login shell; source .profile
# to get pipx on the path.
RUN . $HOME/.profile && pipx install poetry

COPY pyproject.toml poetry.lock /src/
WORKDIR /src

RUN . $HOME/.profile && pipx run poetry export --output requirements.txt


# Install dependencies
FROM python:3.7-alpine as deps-installer

COPY --from=gen-requirements /src/requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install -r /tmp/requirements.txt


# Minimal image with dependencies installed
FROM python:3.7-alpine as deps
COPY --from=deps-installer /opt/venv /opt/venv


# Build this project
FROM deps as build
RUN . /opt/venv/bin/activate && pip install poetry-core>=1.0.0

COPY pyproject.toml poetry.lock /src/
COPY support/*.py /src/support/
WORKDIR /src

RUN . /opt/venv/bin/activate && pip install .


# Finally just copy this project's package on top of the deps image.
FROM deps
COPY --from=build \
    /opt/venv/lib/python3.7/site-packages/support \
    /opt/venv/lib/python3.7/site-packages/support


ENTRYPOINT [ \
    "/opt/venv/bin/gunicorn", \
    "--workers", "4", \
    "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-", \
    "support:app" \
]
