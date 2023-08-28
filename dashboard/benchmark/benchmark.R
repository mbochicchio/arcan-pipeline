library(dotenv)
library(DBI)
library(odbc)
library(RMySQL)
library(tidyr)
library(dplyr)
library(igraph)
library(coro)

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

new_data_generator <-
    generator(function(conn, max_projects = -1, page_size = 5) {
    i <- 0

    pb <- txtProgressBar(title = "Projects")
    repeat {
        page_data <-
            fetch_analyses_page(conn, offset = i, page_size = page_size)
        n_page <- nrow(page_data)
        if (n_page <= 0 || (max_projects > 0 && i > max_projects)) {
            break
        }
        i <- i + n_page
        tmp_file <- "/tmp/graph.graphml"
        for (index in seq_len(n_page)){
            analysis <- page_data[index, ]

            writeLines(analysis$file_result, tmp_file)
            G <- read_graph(tmp_file, "graphml")
            V(G)$qualified_name <- V(G)$name
            V(G)$name <- V(G)$id
            df_nodes <- as_data_frame(G, what = "vertices") %>% as_tibble()
            df_edges <- as_data_frame(G, what = "edges") %>% as_tibble()

            df_nodes$project_id <- analysis$id
            df_nodes$project_analysis_data <- analysis$date_analysis
            df_nodes$project_name <- analysis$name
            df_nodes$project_language <- analysis$language
            df_nodes$project_version <- analysis$version
            df_nodes$project_version_date <- as.Date(analysis$version_date)

            df_edges$project_id <- analysis$id
            df_edges$project_analysis_data <- analysis$date_analysis
            df_edges$project_name <- analysis$name
            df_edges$project_language <- analysis$language
            df_edges$project_version <- analysis$version
            df_edges$project_version_date <- as.Date(analysis$version_date)
            df_edges$index <- NULL

            df_nodes <- df_nodes %>%
                mutate_if(is.character, as.factor) %>%
                mutate_if(is.numeric, \(x) replace_na(x, 0))

            df_edges <- df_edges %>%
                mutate_if(is.character, as.factor) %>%
                mutate_if(is.numeric, \(x) replace_na(x, 0))
            setTxtProgressBar(pb, 1 / max_projects)
            yield(list(nodes = df_nodes, edges = df_edges))
        }
        close(pb)
        suppressWarnings({ file.remove(tmp_file) })
    }
})

save_to_sqlite <- function(db_file_name, data_generator) {
    mydb <- dbConnect(RSQLite::SQLite(), db_file_name)

    types_map <- list("factor" = "TEXT", "integer" = "REAL",
        "numeric" = "REAL", "character" = "TEXT", "logical" = "INTEGER")
    defaults_map <- list("factor" = "''", "integer" = "0",
        "numeric" = "0", "character" = "''", "logical" = "FALSE")

    while (!is_exhausted(data <- data_generator())) {
        nodes_info <- dbGetQuery(mydb, "PRAGMA table_xinfo(nodes);")
        if (nrow(nodes_info) > 0) {
            missing_cols <- setdiff(colnames(data$nodes), nodes_info$name)
            for (col in missing_cols) {
                col_type <- class(data$nodes[[col]])
                query <- paste(sep = " ",
                    "ALTER TABLE nodes", "ADD", col,
                    types_map[col_type],
                    "NOT NULL", "CONSTRAINT", paste0("D_nodes_", col),
                    "DEFAULT", "(", defaults_map[col_type], ")", ";")
                dbExecute(mydb, query)
            }
        }

        edges_info <- dbGetQuery(mydb, "PRAGMA table_xinfo(edges);")
        if (nrow(edges_info) > 0) {
            missing_cols <- setdiff(colnames(data$edges), edges_info$name)
            for (col in missing_cols) {
                col_type <- class(data$edges[[col]])
                query <- paste(sep = " ",
                    "ALTER TABLE edges", "ADD", col,
                    types_map[col_type],
                    "NOT NULL", "CONSTRAINT", paste0("D_edges_", col),
                    "DEFAULT", "(", defaults_map[col_type], ")", ";")
                dbExecute(mydb, query)
            }
        }
        dbWriteTable(mydb, "nodes", data$nodes, append = TRUE)
        dbWriteTable(mydb, "edges", data$edges, append = TRUE)
    }

    dbDisconnect(mydb)
}

conn <- get_connection_from_env(".env")
fetch_data <- new_data_generator(conn, max_projects = 50)
save_to_sqlite("test-projects.sqlite", fetch_data)
dbDisconnect(conn)

# writeLines(graphs$file_result[1], "/tmp/graph.graphml")
