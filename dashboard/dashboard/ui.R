library(shiny)
library(plotly)
library(shinycssloaders)

ui <- fluidPage(
    h2("Arcan Benchmark Monitoring Dashboard"),
    fluidRow(
        column(6, offset = 0,
            withSpinner(plotlyOutput("analysesByLanguagePlot"))
        ),
        column(6, offset = 0,
            withSpinner(plotlyOutput("dailyAnalysesPlot"))
        )
    ),
    fluidRow(
        column(6,
            withSpinner(plotlyOutput("analysesByProjectPlot"))
        ),
        column(6,
            withSpinner(plotlyOutput("analysedTotalPlot"))
        )
    ),
    hr(),
    fluidRow(
        column(12,
            h3("Projects"),
            DT::DTOutput("projectsTable")
        )
    )
)