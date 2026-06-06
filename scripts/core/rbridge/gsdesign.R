# scripts/core/rbridge/gsdesign.R
# Group-sequential upper boundaries via gsDesign. Reads JSON {k, alpha, test_type, sfu}
# on stdin, writes JSON {"upper_bounds": [...]} on stdout.
suppressMessages(library(gsDesign))

con <- file("stdin")
raw <- paste(readLines(con), collapse = "")
close(con)

# Minimal JSON parse without extra deps: rely on jsonlite if present, else a tiny fallback.
parse_req <- function(s) {
  if (requireNamespace("jsonlite", quietly = TRUE)) {
    return(jsonlite::fromJSON(s))
  }
  # Fallback: extract numbers/strings by key (sufficient for our flat schema).
  getnum <- function(key) as.numeric(sub(
    paste0('.*"', key, '"\\s*:\\s*([0-9.]+).*'), "\\1", s))
  list(k = getnum("k"), alpha = getnum("alpha"))
}

req <- parse_req(raw)
k <- as.integer(req$k)
alpha <- as.numeric(req$alpha)

# sfLDOF = Lan-DeMets O'Brien-Fleming spending; test.type=1 = one-sided.
d <- gsDesign(k = k, test.type = 1, alpha = alpha, sfu = sfLDOF)
bounds <- as.numeric(d$upper$bound)

cat(sprintf('{"upper_bounds": [%s]}', paste(sprintf("%.6f", bounds), collapse = ", ")))
