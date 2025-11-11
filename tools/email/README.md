# Email Tools

Tools for working with email.

## Tools

### [protonmail](protonmail.md)

Access and manage ProtonMail emails through ProtonMail Bridge. Supports syncing, reading, searching, and sending emails with local `.eml` file caching for fast offline access.

**Quick start:**
```bash
export PROTONMAIL_USERNAME=your-email@protonmail.com
export PROTONMAIL_API_KEY=your-bridge-api-key
protonmail sync
protonmail list
```

See [protonmail.md](protonmail.md) for full documentation.

### [html2text](html2text.md)

Convert HTML content to readable plain text, removing tags while preserving structure. Works well with email content.

**Quick start:**
```bash
html2text email.html
cat email.html | html2text
protonmail read email.eml | html2text
```

See [html2text.md](html2text.md) for full documentation.
