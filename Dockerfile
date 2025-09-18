FROM public.ecr.aws/unocha/python:3.13-stable

WORKDIR /srv

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    apk add --no-cache \
    gdal-driver-parquet \
    gdal-tools && \
    apk add --no-cache --virtual .build-deps \
    apache-arrow-dev \
    build-base \
    cmake \
    gdal-dev \
    geos-dev \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && \
    rm -rf /root/.cache

COPY src ./

CMD ["python", "-m", "hdx.scraper.cod_ab"]
