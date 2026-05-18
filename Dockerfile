FROM python:3.11-slim

# Vajalikud sõltuvused süsteemile

RUN apt-get update && \
    apt-get install -y \
    default-jre \
    wget \
    tar \
    r-base \
    pandoc \
    libcurl4-openssl-dev \
    libssl-dev \
    libuv1-dev \
    build-essential \
    libxml2-dev && \
    rm -rf /var/lib/apt/lists/*


# Installime OpenRefine

WORKDIR /opt

ENV OPENREFINE_VERSION=3.8.2

RUN wget https://github.com/OpenRefine/OpenRefine/releases/download/${OPENREFINE_VERSION}/openrefine-linux-${OPENREFINE_VERSION}.tar.gz && \
    tar -xzf openrefine-linux-${OPENREFINE_VERSION}.tar.gz && \
    mv openrefine-${OPENREFINE_VERSION} openrefine && \
    rm openrefine-linux-${OPENREFINE_VERSION}.tar.gz

# Installime R pakid

RUN R -e "install.packages(c( \
    'rmarkdown', \
    'knitr', \
    'readr', \
    'dplyr', \
    'ggplot2', \
    'scales', \
    'ggrepel', \
    'ineq' \
    ), repos='https://cloud.r-project.org/')"

# Installime Python pakid

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopeerime kogu projekti konteinerisse

COPY . .

RUN mkdir -p \
    data/raw \
    data/cleaned \
    data/db \
    reports

CMD ["python", "scripts/pipeline.py"]