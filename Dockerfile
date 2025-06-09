FROM python:3.12-alpine as deps
ENV PYTHONUNBUFFERED=1

RUN apk --no-cache upgrade

COPY requirements.txt /app/

WORKDIR /app
RUN pip install -r requirements.txt


FROM deps as dev
COPY requirements-dev.txt /app/
RUN pip install -r requirements-dev.txt
RUN apk add --no-cache git openssh-client-default curl bash
# Install Helm for chart testing
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \
    && chmod 700 get_helm.sh \
    && VERIFY_CHECKSUM=false ./get_helm.sh \
    && rm get_helm.sh
CMD flask run --debug -h 0.0.0.0

# Release image without dev deps
FROM deps as final
COPY . /app/
RUN addgroup -S kronic && adduser -S kronic -G kronic -u 3000
USER kronic
CMD gunicorn -w 4 -b 0.0.0.0 --access-logfile=- app:app
