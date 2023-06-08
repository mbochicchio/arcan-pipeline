FROM apache/airflow:2.6.1
USER root
RUN apt-get update && apt-get install -y git
USER airflow
RUN umask 0002; \
    mkdir -p projects