FROM python:3.11-slim-bookworm

LABEL maintainer="f.rhiem@fz-juelich.de"
LABEL org.opencontainers.image.source=https://github.com/sciapp/sampledb
LABEL org.opencontainers.image.url=https://scientific-it-systems.iffgit.fz-juelich.de/SampleDB/
LABEL org.opencontainers.image.documentation=https://scientific-it-systems.iffgit.fz-juelich.de/SampleDB/
LABEL org.opencontainers.image.title="SampleDB"
LABEL org.opencontainers.image.description="A web-based electronic lab notebook with a focus on sample and measurement metadata"
LABEL org.opencontainers.image.licenses=MIT


# Install required system packages
# GCC is required to build python dependencies on ARM architectures
# git is required to build python dependencies from git repositories
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y gcc libpangocairo-1.0-0 gettext git

# Switch to non-root user
RUN useradd -ms /bin/bash sampledb
USER sampledb
WORKDIR /home/sampledb

# Set up virtual environment
ENV VIRTUAL_ENV=/home/sampledb/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN  pip install --upgrade pip

# Install required Python packages
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Clean up system packages that are no longer required
USER root
RUN apt-get remove -y gcc && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
USER sampledb

# Copy sampledb source code
COPY --chown=sampledb:sampledb sampledb sampledb

# By default, expect a normal postgres container to be linked
ENV SAMPLEDB_SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://postgres:@postgres:5432/postgres"

# Set default file storage path
ENV SAMPLEDB_FILE_STORAGE_PATH=/home/sampledb/files

# Set the path for pybabel
ENV SAMPLEDB_PYBABEL_PATH=/home/sampledb/venv/bin/pybabel

# Write Docker build arg SAMPLEDB_VERSION to environment to be read by sampledb/version.py.
ARG SAMPLEDB_VERSION
ENV SAMPLEDB_VERSION=$SAMPLEDB_VERSION

# Copy the SampleDB helper script
COPY ./docker-helper.sh /usr/local/bin/sampledb

# The entrypoint script will set the file permissions for a mounted files directory and then start SampleDB
COPY docker-entrypoint.sh docker-entrypoint.sh

USER root
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["run"]

HEALTHCHECK --interval=1m --timeout=3s --start-period=1m CMD curl -f -H "Host: $SAMPLEDB_SERVER_NAME" "http://localhost:8000$SAMPLEDB_SERVER_PATH/status/" || exit 1
