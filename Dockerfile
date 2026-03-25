# TODO: Create your Dockerfile here

# ---------- Stage 1: builder ----------
FROM python:3.11-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y \
    build-essential gcc g++ python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY cpp-lib/ ./cpp-lib/
COPY python-example/requirements.txt ./requirements.txt
RUN make -C cpp-lib
RUN pip install --upgrade pip wheel \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libxcb1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY --from=builder /build/cpp-lib/libimgutils.so /cpp-lib/
#RUN ldconfig

COPY python-example/ ./
COPY static/ ../static/

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["python", "app.py"]




