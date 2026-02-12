FROM ghcr.io/osgeo/gdal:alpine-normal-3.12.2

COPY --from=ghcr.io/astral-sh/uv:0.10.2 /uv /usr/local/bin/uv

WORKDIR /srv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

RUN --mount=type=bind,source=pyproject.toml,target=/srv/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/srv/uv.lock \
    --mount=type=bind,source=src,target=/srv/src \
    --mount=type=bind,source=.git,target=/srv/.git \
    addgroup -g 4000 -S appuser && \
    adduser -u 4000 -s /sbin/nologin -g 'Docker App User' -h /home/appuser -D -G appuser appuser && \
    apk add --no-cache --virtual .build-deps \
    build-base \
    gdal-dev \
    git \
    python3-dev && \
    uv sync --frozen --no-dev --no-editable && \
    apk del .build-deps

COPY run.py ./run.py

CMD ["python", "run.py"]
