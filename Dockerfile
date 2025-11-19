FROM ghcr.io/osgeo/gdal:alpine-normal-3.12.0

WORKDIR /srv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    apk add --no-cache python3 && \
    python -m venv /opt/venv && \
    apk add --no-cache --virtual .build-deps \
    apache-arrow-dev \
    build-base \
    cmake \
    gdal-dev \
    geos-dev \
    python3-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && \
    rm -rf /root/.cache

COPY src ./src

CMD ["python", "-m", "src.hdx.scraper.cod_ab_country"]
