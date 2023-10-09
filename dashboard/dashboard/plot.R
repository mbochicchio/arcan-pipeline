library(dplyr)
library(ggplot2)
library(thematic)

theme_set(theme_classic())

colors <- list(
    colors_2 = okabe_ito(2),
    colors_3 = okabe_ito(3)
)

plot_analyses_by_language <- function(analyses_status) {
    data <- analyses_status %>%
        select(!id & !total) %>%
        rename(Success = n_success, Failed = n_failed) %>%
        group_by(language) %>%
        summarise_if(is.numeric, sum, na.rm = TRUE) %>%
        pivot_longer(cols = c("Failed", "Success"))
    data %>%
        ggplot(aes(language, value, fill = name)) +
        geom_col(position = "dodge") +
        scale_fill_manual(values = colors$colors_2) +
        labs(x = "Language", y = "Num. of analyses", fill = "",
            title = "Number of analyses by programming language"
        ) +
        theme(legend.position = "top")
}

plot_analyses_by_project <- function(analyses_status, n_top = 500) {
    data <- analyses_status %>%
        rename(Success = n_success, Failed = n_failed) %>%
        mutate(`In queue for analysis` = total - Success - Failed) %>%
        select(!id & !total) %>%
        slice_head(n = n_top) %>%
        pivot_longer(cols = c("Failed", "Success", "In queue for analysis"),
            names_to = "var") %>%
        mutate(var = as.factor(var))
    data %>%
        ggplot(aes(reorder(name, -value), value, fill = var)) +
        geom_col(position = "stack") +
        theme(axis.text.x = element_blank(), axis.ticks.x = element_blank(),
            legend.position = "top") +
        scale_fill_manual(values = colors$colors_3) +
        labs(x = "Project index", y = "Num. of analyses", fill = "",
            title = "Status of the analyses for each project")
}

plot_analyses_by_status <- function(analyses_status) {
    analyses_status %>% 
        rename(Success = n_success, Failed = n_failed) %>%
        mutate(`In queue for analysis` = total - Success - Failed) %>%
        select(!id & !total) %>%
        pivot_longer(cols = c("Failed", "Success", "In queue for analysis"),
            names_to = "var") %>%
        mutate(var = as.factor(var)) %>%
        group_by(var) %>%
        summarise(value = sum(value, na.rm = TRUE))
}

plot_analysed_total <- function(analyses_status) {
    analyses_status %>%
        select(!id & !total) %>%
        rename(Success = n_success, Failed = n_failed) %>%
        group_by() %>%
        summarise_if(is.numeric, sum, na.rm = TRUE) %>%
        pivot_longer(cols = everything()) %>%
        ggplot(aes(name, value, fill = name)) +
        geom_col() +
        scale_fill_manual(values = colors$colors_2) +
        labs(x = "", y = "Num. of Analyses", fill = "",
            title = "Number of analyses")
}

plot_analyses_by_day <- function(analyses_by_day) {
    analyses_by_day %>%
        mutate(outcome = ifelse(status, "Success", "Failed")) %>%
        ggplot(aes(day, n, color = outcome)) +
        geom_line(lwd = 1.1) +
        geom_point() +
        scale_color_manual(values = colors$colors_2) +
        labs(x = "", y = "Num. of analyses", color = "",
            title = "Number of analyses by day"
        ) +
        theme(legend.position = "top")
}

plot_failure_rate_by_language <- function(analyses_status) {
    rates <- analyses_status %>%
        group_by(language) %>%
        summarise(n_failed = sum(n_failed),
            n_success = sum(n_success))
    rates <- rates %>%
        bind_rows(tibble(
            language = "TOTAL", n_failed = sum(rates$n_failed),
            n_success = sum(rates$n_success)))
    rates %>%
        mutate(total = n_failed + n_success) %>%
        mutate(Success = n_success / total * 100) %>%
        mutate(Failed = n_failed / total * 100)
        pivot_longer(cols = c("Success", "Failed")) %>%
        ggplot(aes(language, value, fill = name)) +
        geom_col() +
        scale_fill_manual(values = colors$colors_2) +
        labs(x = "", y = "Percentage (Rate)", fill = "",
            title = "Success and failure rates by programming language") +
        theme(legend.position = "top")
}