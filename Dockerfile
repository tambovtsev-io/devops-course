FROM apache/airflow:2.10.5

USER root

# Set default Apache workdir
WORKDIR $AIRFLOW_HOME

# Copy source code
# COPY ./src /opt/airflow/src
# COPY ./dags /opt/airflow/dags

USER airflow

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt
