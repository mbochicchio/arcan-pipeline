library(shiny)

genv <- \(x, default = NULL) ifelse(Sys.getenv(x) == "", default, Sys.getenv(x))
local(options(
    shiny.port = as.numeric(genv("DASHBOARD_PORT", "5001")),
    shiny.host = "0.0.0.0",
    db.url = genv("DATABASE_URL"),
    db.port = as.numeric(genv("DATABASE_PORT")),
    db.db = genv("DATABASE_DB"),
    db.username = genv("DATABASE_USERNAME"),
    db.password = genv("DATABASE_PASSWORD")
))
runApp("dashboard")