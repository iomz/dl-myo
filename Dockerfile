FROM python:3.11.3-bullseye

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
RUN pip install dl-myo

COPY examples/sample.py /app/

WORKDIR /app
RUN chmod +x sample.py

ENTRYPOINT ["/app/sample.py"]
