library(DBI)
library(odbc)
library(RMySQL)
library(tidyr)
library(dplyr)

get_connection_from_options <- function() {
    dbConnect(
        MySQL(),
        dbname = getOption("db.db"),
        host = getOption("db.url"),
        port = as.numeric(getOption("db.port")),
        user = getOption("db.username"),
        password = getOption("db.password")
    )
}

get_connection_from_env <- function(file = ".env") {
    dotenv::load_dot_env(file)
    conn <- dbConnect(
        MySQL(),
        dbname = Sys.getenv("DATABASE_DB"),
        host = Sys.getenv("DATABASE_URL"),
        port = as.numeric(Sys.getenv("DATABASE_PORT")),
        user = Sys.getenv("DATABASE_USERNAME"),
        password = Sys.getenv("DATABASE_PASSWORD")
    )
    conn
}

close_connection <- function(conn) {
    dbDisconnect(conn)
}

fetch_analyses_status <- function(conn) {
    analyses <- dbGetQuery(conn, '
        SELECT * FROM analyses_status
        ORDER BY (n_success + n_failed) DESC 
    ') %>% as_tibble() %>%
        mutate_if(is.character, as.factor) %>%
        mutate_if(is.numeric, \(x) replace_na(x, 0))
    analyses
}

fetch_analyses_by_day <- function(conn) {
    analyses_by_day <- dbGetQuery(conn, '
        SELECT date_analysis, is_completed FROM Analysis
    ') %>% as_tibble() %>%
        mutate(date_analysis = as.Date(date_analysis)) %>%
        mutate(is_completed = as.logical(is_completed)) %>%
        mutate(day = as.Date(cut(date_analysis, "day"))) %>%
        mutate_if(is.character, as.factor) %>%
        group_by(day, is_completed) %>%
        tally()
    analyses_by_day
}
