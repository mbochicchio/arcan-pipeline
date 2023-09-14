FROM rocker/shiny-verse as base

RUN R -e 'install.packages(c("dotenv", "DBI", "odbc", "RMySQL", "plotly", "thematic", "DT"))'
RUN R -e 'install.packages(c("shinycssloaders", "igraph", "coro"))'

RUN apt-get update && \
    apt-get install -y libglpk-dev
    
RUN R -e 'install.packages(c("languageserver", "httpgd"))'

FROM base AS webapp
WORKDIR /app
COPY benchmark.R .
ENTRYPOINT [ "Rscript", "benchmark.R" ]