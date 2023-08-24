library(dotenv)
library(DBI)
library(odbc)
library(RMySQL)
library(tidyr)
library(dplyr)
library(igraph)

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

fetch_analyses_page <- function(conn, offset = 0, page_size = 5) {
    q_page <- '
        SELECT a.id, a.date_analysis, p.name, p.language,
            v.id_github as version, v.date as version_date
        FROM Analysis as a 
            JOIN Version as v on v.id = a.project_version 
            JOIN Project as p on p.id = id_project 
        WHERE is_completed = 1
        ORDER BY a.date_analysis, a.id ASC'
    q_page <- paste0(q_page, " LIMIT ", page_size, " OFFSET ", offset)
    page <- dbGetQuery(conn, q_page) %>% as_tibble()

    q_data <- "SELECT id, file_result FROM Analysis WHERE id in "
    q_data <- paste0(q_data, "(", paste0(page$id, collapse = ","), ")")

    graphs <- dbGetQuery(conn, q_data) %>% as_tibble()
    graphs %>%
        left_join(page, by = "id") %>%
        select(!file_result, file_result)
}

fetch_graphs <- function(conn) {
    i <- 0
    repeat {
        page_data <- fetch_analyses_page(conn, offset = i, page_size = 5)
        n_page <- nrow(page_data)
        if (n_page <= 0) {
            break
        }
        i <- i + n_page
        tmp_file <- "/tmp/graph.graphml"
        for (analysis in page_data){
            writeLines(analysis$file_result, tmp_file)
            G <- read_graph(tmp_file, "graphml")
            df_nodes <- as_data_frame(G, what = "vertices") %>% as_tibble()
            df_edges <- as_data_frame(G, what = "edges") %>% as_tibble()
            # TODO where to write the data
        }
        suppressWarnings({ file.remove(tmp_file) })
    }
}



conn <- get_connection_from_env(".env")

writeLines(graphs$file_result[1], "/tmp/graph.graphml")
