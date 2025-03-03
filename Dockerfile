FROM apache/airflow:2.10.5

USER root

# Set default Apache workdir
WORKDIR $AIRFLOW_HOME

# Copy source code
COPY ./src ./src
COPY pyproject.toml ./

# Install uv and resolve dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync --no-dev
ENV PATH="$AIRFLOW_HOME/.venv/bin:$PATH"
ENV PYTHONPATH="$AIRFLOW_HOME:$PYTHONPATH"

USER airflow
