FROM gsscogs/pythonversiontesting:v1.0.1

ARG VENV_PATH=/gss-utils-venv
ARG VENV_PIP=${VENV_PATH}/bin/pip
ARG VENV_POETRY=${VENV_PATH}/bin/poetry


RUN pyenv global 3.9.7

RUN mkdir -p /workspace

WORKDIR /workspace

# Install all dependencies for project
COPY poetry.lock .
COPY pyproject.toml .

# Using a manually created venv so that poetry uses the same venv no matter where the source code is mounted.
# Jenkins will mount the source code at some esoteric path, and vscode will mount the code at /workspaces/<project-name>.
# This gives us consistency so that the docker container genuinely caches the dependencies.
RUN python -m venv ${VENV_PATH}

# Write all dependencies to file.
RUN poetry export --format requirements.txt --output /requirements.txt --without-hashes --dev

# Install all dependencies listed in text file to the venv.
RUN ${VENV_PIP} install --requirement /requirements.txt
RUN ${VENV_PIP} install poetry

# The install from requirements.txt is cirumventing the pin to cacheControl 0.12.6 as it lacks
# sufficiant dependency resolution (something somewhere is bumping us to 0.12.11).
# Unfortunetly when the "poetry install" in the ENTRYPOINT tries to resolve this on Jenkins it errors
# while attempting the downgrade of 0.12.11 -> 0.12.6.
# As a work around we're directly uninstalling cachecontrol (0.12.11) here with the venv
# pip - poetry in the ENTRYPOINT will then install the required version.
RUN ${VENV_PIP} uninstall cachecontrol -y

# Patch behave
RUN patch -Nf -d "${VENV_PATH}/lib/python3.9/site-packages/behave/formatter" -p1 < /cucumber-format.patch

RUN rm -rf /workspace/*

WORKDIR /workspace


# Trick poetry into thinking it's inside the virtual environment
# This will make all poetry commands work naturally, even outside the virtual environment.
ENV VIRTUAL_ENV="${VENV_PATH}"
ENV PATH="${PATH}:${VENV_PATH}/bin/"
ENV PYTHONDONTWRITEBYTECODE=1

# On container start, the source code is loaded so we call poetry install so the venv knows where the local project's package/code lives.
ENTRYPOINT poetry install && bash

