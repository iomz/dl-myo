FROM python:3.11.3-bullseye
LABEL org.opencontainers.image.source = "https://github.com/iomz/dl-myo"
LABEL maintainer="iomz@sazanka.io"

ARG BUILD_DEPS=" \
    bluez \
    libglib2.0-dev"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ${BUILD_DEPS}

RUN apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install --upgrade pip
RUN pip install dl-myo "influxdb-client[ciso]"

COPY examples/influxdb/influx_client.py /app/

WORKDIR /app

ENTRYPOINT ["/app/influx_client.py"]
