FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-dev binutils ca-certificates \
    libgl1 libegl1 libfontconfig1 libfreetype6 libx11-6 libxext6 libxrender1 \
    libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 \
    libdbus-1-3 libglib2.0-0 libsm6 libice6 libxcb-shape0 libxcomposite1 \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
WORKDIR /src
COPY pyproject.toml README.md LICENSE.txt ./
COPY zencad ./zencad
COPY tools/standalone/constraints-linux.txt /tmp/constraints.txt
RUN pip install -c /tmp/constraints.txt '.[gui,examples]' pyinstaller
