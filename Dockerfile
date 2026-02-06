FROM ghcr.io/osgeo/gdal:alpine-normal-3.12.1

WORKDIR /usr/src/app

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

COPY run.py ./run.py
COPY src ./

CMD ["python", "run.py"]
