"""WAFLE Gmail confirmation code reader.

Standalone package. Read 2FA verification codes from Gmail inbox
using EMAIL_FLOW / CLAVE_EMAIL_FLOW environment variables.

Usage (CLI):
  wafle-gmail-reader --read --sender Meta --max-wait 180

Usage (import):
  from waflegmailreader import read_confirmation_code
  code = read_confirmation_code("Meta", max_wait=180)
"""

from .gmail_reader import read_confirmation_code, _extract_code

__version__ = "0.1.0"
__description__ = __doc__
