# How the ERIS assistant answers questions

## What it does
The assistant answers plain-English questions about sales, products, outlets, stock, customers, forecasts, unusual days and the reasons behind changes. It works fully offline with a built-in rule-based language parser; when a local Ollama model is running it is also used to understand unusual phrasing and to word general answers.

## How answers are grounded
The assistant never writes database queries from free text. It recognises the question type and its filters (period, outlets, category, product, horizon) and runs one of a fixed set of analysis functions, the same ones behind the dashboard and reports. Numbers in answers come only from these functions. Definitions and how-to answers come from the project documentation, and the source document is shown.

## Provenance shown with every answer
Every answer shows where the numbers came from: the data source (synthetic demo data, manual entries or imports), the filters applied, how long the query took, the forecast model version when a forecast is involved, and a note when the data is insufficient, for example when the period starts before the first recorded sale.

## Access control
Answers only include outlets the signed-in user is allowed to see. A manager asking about another outlet gets results for their own outlets.
