# wafle-gmail-reader

Lee códigos de confirmación 2FA desde Gmail usando Playwright.

## Uso

```bash
# CLI
wafle-gmail-reader --read --sender Meta --max-wait 180

# Como subprocess (desde flow/meta)
code=$(wafle-gmail-reader --read --sender Google --json)
echo $code  # {"code": "123456", "found": true}
```

## Variables de entorno

- `EMAIL_FLOW` — correo Gmail
- `CLAVE_EMAIL_FLOW` — contraseña de la cuenta

## Como dependencia

```python
from waflegmailreader import read_confirmation_code
code = read_confirmation_code("Meta", max_wait=180)
```
