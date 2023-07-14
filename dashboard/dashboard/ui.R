library(shiny)
library(plotly)

ui <- fluidPage(
    fluidRow(
        column(6, offset = 0,
            plotlyOutput("analysesByLanguagePlot")
        ),
        column(6, offset = 0,
            plotlyOutput("dailyAnalysesPlot")
        )
    ),
    fluidRow(
        column(6,
            plotlyOutput("analysesByProjectPlot")
        )
    )
)