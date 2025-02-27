FROM apache/airflow:2.10.5

USER root

# Set default Apache workdir
WORKDIR $AIRFLOW_HOME

# Copy source code
COPY ./src /opt/airflow/src
COPY ./dags /opt/airflow/dags
COPY pyproject.toml .

# Install uv and resolve dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync
ENV PATH="$AIRFLOW_HOME/.venv/bin:$PATH"

USER airflow
