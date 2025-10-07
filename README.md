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

### Export multiple matches at once
python -m main --match_ids=461102,461103,461104
```
