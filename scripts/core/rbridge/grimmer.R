# GRIMMER (granularity-related inconsistency of means mapped to error repeats) via scrutiny.
# Reads JSON {x, sd, n, items?} on stdin (x and sd are STRINGS to preserve reported decimals),
# writes JSON {"consistent": <bool>, "reason": <str>} on stdout.
#
# NOTE: scrutiny's grimmer() has a known bug (issue #80) where "test 3" can flag consistent
# values as inconsistent (false positives). We therefore return the raw reason so the Python
# caller can demote a test-3-only failure to "indeterminate". GRIM and tests 1-2 are sound.
suppressMessages(library(scrutiny))

con <- file("stdin")
raw <- paste(readLines(con), collapse = "")
close(con)

req <- if (requireNamespace("jsonlite", quietly = TRUE)) {
  jsonlite::fromJSON(raw)
} else {
  # minimal fallback for our flat schema
  getstr <- function(key) sub(paste0('.*"', key, '"\\s*:\\s*"([^"]*)".*'), "\\1", raw)
  getnum <- function(key) as.numeric(sub(paste0('.*"', key, '"\\s*:\\s*([0-9]+).*'), "\\1", raw))
  list(x = getstr("x"), sd = getstr("sd"), n = getnum("n"), items = getnum("items"))
}

items <- if (is.null(req$items) || is.na(req$items)) 1L else as.integer(req$items)

res <- suppressWarnings(grimmer(
  x = as.character(req$x), sd = as.character(req$sd),
  n = as.integer(req$n), items = items, show_reason = TRUE
))

cat(sprintf('{"consistent": %s, "reason": "%s"}',
            tolower(as.character(res[[1]])), paste(res[[2]], collapse = "; ")))
