FROM public.ecr.aws/unocha/python:3.13-stable

WORKDIR /srv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

RUN --mount=type=bind,source=pyproject.toml,target=/srv/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/srv/uv.lock \
    --mount=type=bind,source=src,target=/srv/src,rw \
    --mount=type=bind,source=.git,target=/srv/.git \
    apk add --no-cache \
        gdal-driver-parquet \
        gdal-tools && \
    apk add --no-cache --virtual .build-deps \
        build-base \
        gdal-dev \
        git \
        python3-dev \
        uv && \
    uv sync --frozen --no-dev --no-editable && \
    apk del .build-deps

COPY run.py ./run.py

CMD ["python", "run.py"]
