# Use the official PostgreSQL image as the base
FROM postgres:latest

# Set environment variables to control PostgreSQL settings
ENV POSTGRES_DB=pgvector_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=1234

# Install build dependencies for pgvector
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-all

# Clone pgvector and build it
RUN git clone https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install

# Clean up installation packages to reduce image size
RUN apt-get remove -y build-essential git postgresql-server-dev-all \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to the postgres user
USER postgres

# Run SQL commands to enable pgvector extension
COPY extension.sql /docker-entrypoint-initdb.d/

# Set the default command to run when starting the container
CMD ["postgres"]
