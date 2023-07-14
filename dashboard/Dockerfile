FROM rocker/shiny-verse as base

RUN R -e 'install.packages(c("dotenv", "DBI", "odbc", "RMySQL", "plotly", "thematic"))'

FROM base AS devenv
RUN apt-get update && \
    apt-get install -y python3 python3-pip git && \
    pip3 install -U radian
    
RUN R -e 'install.packages(c("languageserver", "httpgd"))'

FROM base AS webapp
WORKDIR /app
COPY run-app.R .
COPY dashboard .
ENTRYPOINT [ "Rscript", "run-app.R" ]