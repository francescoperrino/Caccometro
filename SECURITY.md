# Security

## Reporting a vulnerability

Please report it privately from [Security → Report a vulnerability](https://github.com/francescoperrino/Caccometro/security/advisories/new), not in a public issue. Only the latest release is supported.

## What the project does to stay safe

- The webhook accepts only the calls that carry the secret token registered on Telegram; the others get 403.
- The bot never stores or logs the text of the messages: only user IDs, usernames, names and the 💩 per day.
- Tokens are never in the repository: `.env` is not tracked, and the hosting API token lives in an environment variable.
- GitHub secret scanning and push protection are on; `main` takes only signed commits through pull requests with green tests; the workflow actions are pinned to a commit.
