library(shiny)
library(dplyr)

source("queries.R")
source("plot.R")

conn <- get_connection_from_options()
onStop(\(){
    close_connection(conn)
})
server <- function(input, output, session) {

    analyses_status <- reactive({
        fetch_analyses_status(conn)
    })

    analyses_by_day <- reactive({
        fetch_analyses_by_day(conn)
    })

    output$analysesByLanguagePlot <- renderPlotly({
        analyses_status() %>%
            plot_analyses_by_language()
    })

    output$analysesByProjectPlot <- renderPlotly({
        analyses_status() %>%
            plot_analyses_by_project()
    })

    output$dailyAnalysesPlot <- renderPlotly({
        analyses_by_day() %>%
            plot_analyses_by_day()
    })

    output$analysedTotalPlot <- renderPlotly({
        analyses_status() %>% 
            plot_analysed_total()
    })

    output$projectsTable <- DT::renderDT({
        analyses_status() %>%
            select(name, language, n_failed, n_success) %>%
            mutate(Link = paste0("<a target='_blank' href='https://github.com/", name, "'>View</a>")) %>%
            arrange(desc(n_failed + n_success)) %>%
            rename(Name = name, Language = language,
                Failed = n_failed, Success = n_success) %>%
            DT::datatable(escape = FALSE)
    }, filter = "top")
}