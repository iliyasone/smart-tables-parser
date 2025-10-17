# Smart Tables Parser

### Installation


```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r pip-requirements.txt
```

### Secrets

Create `.env` based on `.env.example` or put your config variables into the env.

### Parse

```bash
python -m main --match_ids=461102
```

### Export multiple matches at once

```bash
python -m main --match_ids=461102,461103,461104
```

# Docs

### Return value of `export_match_stats`

`main.export_match_stats` returns the same summary that you see in the console, but as plain Python data. The layout is captured by the `ExportMatchStatsSummary` `TypedDict`:

```python
ExportMatchStatsSummary = TypedDict("ExportMatchStatsSummary", {
    "stat_odds": {
        "retrieved": list[str],
        "missing": list[str],
        "errors": list[tuple[str, str]],
    },
    "charts": {
        "retrieved": list[str],
        "missing": list[str],
        "errors": list[tuple[str, str]],
    },
})
```

`main()` loops over the match IDs you pass, calls `export_match_stats`, and prints the dictionary in a readable form. You can import the function in your own code if you prefer to use the dictionary directly.


### Example

```python
>>> export_match_stats(build_client(), 530674)

{
    "stat_odds": {
        "retrieved": [],  # nothing saved under out/530674/stat-odds
        "missing": [      # server errors, you may try again later
            "fouls",
            "throwins",
            "shotstarget",
            "goalkicks",
            "yellowcards",
            "offsides",
            "shots",
        ],  
        "errors": [],     # no fatal 4xx failures
    },
    "charts": {
        "retrieved": [    # saved under out/530674/charts
            "fouls",
            "throwins",
            "shotstarget",
            "yellowcards",
            "offsides",
            "shots",
        ],  
        "missing": [],   # no temporary server failures
        "errors": [
            ("goalkicks", "/api/v1/matches/530674/chart returned HTTP 400"),
        ],               # endpoints rejected with 4xx, so nothing to save
    },
}
```

### Understanding the CLI output

`python -m main --match_ids=<id>` starts `main()`, and for each match ID it calls `export_match_stats()`. The function returns a dictionary, and `main()` prints it with short labels so you can scan the result quickly.

Every summary is split into `stat-odds` and `charts`. Each section always shows three lines:

- `retrieved`: stats that were downloaded successfully and saved under `out/<match_id>/<group>/<stat>.json`.
- `missing (server error)`: (e.g. `HTTP 500`) the resource was likely available before but isn’t available now — try again later
- `errors`: request errors (e.g. `HTTP 400`); likely means that the resource have never existed.

Example console output:

```text
Match 530674 results:
  stat-odds retrieved: none
  stat-odds missing (server error): fouls, throwins, shotstarget, goalkicks, yellowcards, offsides, shots
  stat-odds errors: none
  charts retrieved: fouls, throwins, shotstarget, yellowcards, offsides, shots
  charts missing (server error): none
  charts errors:
    goalkicks: /api/v1/matches/530674/chart returned HTTP 400
```



### Endpoint fallback

For stat odds and charts the client keeps a list of fallback URLs. It calls the first one; if the server answers with a 4xx it quietly tries the next URL. A 5xx response means “temporary problem”, so the function returns `None` and the CLI shows the stat under `missing (server error)`. Only when every URL ends with 4xx does the client raise an error, and that message appears in the `errors` list.
