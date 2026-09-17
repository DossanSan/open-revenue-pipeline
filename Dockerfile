FROM apache/airflow:3.3.1-python3.12
USER root
RUN python -m venv /opt/pipeline-venv && chown -R airflow:root /opt/pipeline-venv
USER airflow
COPY requirements.txt /tmp/pipeline-requirements.txt
RUN /opt/pipeline-venv/bin/pip install --no-cache-dir -r /tmp/pipeline-requirements.txt
WORKDIR /opt/project
