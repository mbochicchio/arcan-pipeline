FROM apache/airflow:2.5.3
USER root
RUN apt-get update && apt-get install -y git
USER airflow
RUN pip install ratelimit
RUN umask 0002; \
    mkdir -p projects