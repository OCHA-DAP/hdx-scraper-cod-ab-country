FROM ghcr.io/osgeo/gdal:alpine-normal-3.12.1

WORKDIR /srv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APPUSER_GID=4000 \
    APPUSER_UID=4000

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    addgroup -g $APPUSER_GID -S appuser && \
    adduser -u $APPUSER_UID -s /sbin/nologin -g 'Docker App User' -h /home/appuser -D -G appuser appuser && \
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

COPY run.py ./run.py
COPY src ./

CMD ["python", "run.py"]
