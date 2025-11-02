FROM python:3.14-slim

ARG _USER="lilchz"
ARG _UID="1001"
ARG _GID="100"
ARG _SHELL="/bin/bash"

ARG VCS_URL="https://github.com/wayfair-incubator/cloud-functions-buildkite-plugin"

ARG BUILD_DATE

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_NO_CACHE=true

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN useradd -m -s "${_SHELL}" -N -u "${_UID}" "${_USER}"

ENV USER ${_USER}
ENV UID ${_UID}
ENV GID ${_GID}
ENV HOME /home/${_USER}
ENV PATH "${HOME}/.local/bin/:${PATH}"

RUN mkdir /app && chown ${UID}:${GID} /app

COPY --chown=${UID}:${GID} . /app/
WORKDIR /app

# Install dependencies as root before switching users
RUN uv pip install --system -r requirements.txt -r requirements-test.txt

USER ${_USER}

CMD bash

