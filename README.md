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

### Endpoint fallback

When requesting stat odds the client first calls `/api/v1/match-center/{match_id}/stat-odds`.
If that endpoint responds with an error, it automatically retries `/api/v1/matches/{match_id}/stat-odds`.
Only after both endpoints fail will the CLI report an error, and the message explains that both URLs were attempted.
