FROM rocker/shiny-verse as base

RUN R -e 'install.packages(c("dotenv", "DBI", "odbc", "RMySQL", "plotly", "thematic"))'
RUN R -e 'install.packages(c("shinycssloaders"))'

FROM base AS devenv
RUN apt-get update && \
    apt-get install -y python3 python3-pip git && \
    pip3 install -U radian
    
RUN R -e 'install.packages(c("languageserver", "httpgd"))'

FROM base AS webapp
WORKDIR /app
COPY run-app.R .
COPY dashboard dashboard/
ENTRYPOINT [ "Rscript", "run-app.R" ]