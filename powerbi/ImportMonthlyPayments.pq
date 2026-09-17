// Create a Text parameter named DataFilePath pointing to exports/powerbi.json.
// During extraction-only exploration, data/snapshot.json has the same core columns.
let
    Source = Json.Document(File.Contents(DataFilePath)),
    Records = Table.FromRecords(Source[records]),
    Core = Table.SelectColumns(Records, {
        "month", "payment_type", "trip_count", "priced_trip_count",
        "trip_total_usd", "fare_usd", "tips_usd", "tolls_usd", "extras_usd"
    }),
    Typed = Table.TransformColumnTypes(Core, {
        {"month", type date}, {"payment_type", type text},
        {"trip_count", Int64.Type}, {"priced_trip_count", Int64.Type},
        {"trip_total_usd", Currency.Type}, {"fare_usd", Currency.Type},
        {"tips_usd", Currency.Type}, {"tolls_usd", Currency.Type},
        {"extras_usd", Currency.Type}
    }, "en-US")
in
    Typed
