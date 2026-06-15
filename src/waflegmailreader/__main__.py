"""CLI entry point for wafle-gmail-reader.

Usage:
  wafle-gmail-reader --read --sender Meta --max-wait 180
  wafle-gmail-reader --read --sender Google --max-wait 300 --poll 15
  wafle-gmail-reader --version

Called as subprocess by flow/meta automation to read 2FA codes.
Prints the code to stdout, or exits with code 1 if not found.
"""

import sys
import json
import argparse
import logging
from . import __version__
from .gmail_reader import read_confirmation_code, _HAS_CREDENTIALS


def main():
    parser = argparse.ArgumentParser(
        description="WAFLE Gmail confirmation code reader",
    )
    parser.add_argument("--read", action="store_true",
                        help="Read a confirmation code from Gmail inbox")
    parser.add_argument("--sender", default="Meta",
                        help="Email sender to filter by (default: Meta)")
    parser.add_argument("--max-wait", type=int, default=120,
                        help="Max seconds to wait for email (default: 120)")
    parser.add_argument("--poll", type=int, default=10,
                        help="Poll interval in seconds (default: 10)")
    parser.add_argument("--json", action="store_true",
                        help="Output result as JSON")
    parser.add_argument("--version", action="version",
                        version=f"wafle-gmail-reader {__version__}")
    parser.add_argument("--check-creds", action="store_true",
                        help="Check if credentials are configured and exit")

    args = parser.parse_args()

    # No args → show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.check_creds:
        result = {"has_credentials": _HAS_CREDENTIALS}
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Credentials configured: {_HAS_CREDENTIALS}")
        sys.exit(0 if _HAS_CREDENTIALS else 1)

    if args.read:
        if args.json:
            code = read_confirmation_code(
                sender_hint=args.sender,
                max_wait=args.max_wait,
                poll_interval=args.poll,
            )
            result = {"code": code, "found": code is not None}
            print(json.dumps(result))
        else:
            print(f"Reading confirmation code from Gmail (sender: {args.sender})...",
                   file=sys.stderr)
            code = read_confirmation_code(
                sender_hint=args.sender,
                max_wait=args.max_wait,
                poll_interval=args.poll,
            )
            if code:
                print(code)
            else:
                print("FAILED: No code found", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
