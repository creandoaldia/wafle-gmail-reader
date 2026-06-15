"""Core: Gmail confirmation code reader using Playwright.

Reads 2FA codes from Gmail inbox using EMAIL_FLOW / CLAVE_EMAIL_FLOW env vars.
Used as an independent process by wafle-automations-flow and wafle-automations-meta.
"""

import os
import re
import time
import logging
from typing import Optional

logger = logging.getLogger("waflegmailreader")

_EMAIL = os.environ.get("EMAIL_FLOW", "")
_PASSWORD = os.environ.get("CLAVE_EMAIL_FLOW", "")
_HAS_CREDENTIALS = bool(_EMAIL and _PASSWORD)


def _extract_code(text: str) -> Optional[str]:
    """Extract a numeric confirmation code from email body text.

    Supports patterns in both English and Spanish:
      - 'Your Meta confirmation code is 123456'
      - 'código de verificación: 987654'
      - '123456 is your code'
      - Fallback: first 6-digit number found
    """
    patterns = [
        # "999731 is your Meta confirmation code"
        r"(\d{4,8})(?:\s*(?:is|es)\s*your\s*(?:Meta|Google|confirmation|verification)\s*code)",
        # "Meta code: 999731" / "código: 999731"
        r"(?:Meta|Google|confirmation|verification|security)\s*(?:code|código|codigo)\s*(?::|is|es)\s*(\d{4,8})",
        # "999731 es tu Meta code" / "999731 is your login code"
        r"(\d{4,8})\s*(?:is|es)\s*(?:your|tu)\s*(?:Meta|login|confirmation)",
        # "código: 999731" / "codigo 999731"
        r"(?:código|codigo|code|sesión|session)[:\s]*(\d{4,8})",
        # "Código de inicio de sesión 999731" (Meta email format)
        r"(?:código|codigo|code)[^0-9]*(\d{4,8})",
        # Fallback: first 6-digit number found
        r"(\d{6})",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def read_confirmation_code(
    sender_hint: str = "Meta",
    max_wait: int = 120,
    poll_interval: int = 10,
) -> Optional[str]:
    """Open Gmail inbox, search for latest email from sender_hint, extract confirmation code.

    Args:
        sender_hint: Email sender to filter by (e.g. 'Meta', 'Google', 'security@meta').
        max_wait: Max seconds to wait for the email to arrive.
        poll_interval: Seconds between inbox refreshes.

    Returns:
        The confirmation code string, or None if not found.
    """
    if not _HAS_CREDENTIALS:
        logger.error("No Gmail credentials — set EMAIL_FLOW and CLAVE_EMAIL_FLOW in .env")
        return None

    from waflescraper.stealth import StealthConfig
    from playwright.sync_api import sync_playwright

    stealth = StealthConfig()
    code = None

    with sync_playwright() as pw:
        launch_cfg = stealth.browser_launch_args()
        browser = pw.chromium.launch(headless=True, **launch_cfg)
        context = browser.new_context(**stealth.context_params())
        page = context.new_page()
        page.set_default_timeout(30000)
        page.set_default_navigation_timeout(45000)

        try:
            _gmail_login(page, stealth)
            code = _poll_inbox(page, sender_hint, max_wait, poll_interval, stealth)
        except Exception as e:
            logger.error(f"Gmail reader failed: {e}")
        finally:
            page.close()
            context.close()
            browser.close()

    return code


def _gmail_login(page, stealth):
    page.goto("https://mail.google.com", wait_until="domcontentloaded")
    stealth.human_delay(2.0, 3.0)

    if "mail.google.com/mail" in page.url:
        logger.info("Already logged into Gmail")
        return

    email_sel = page.locator("#identifierId")
    email_sel.wait_for(state="visible", timeout=10000)
    email_sel.fill(_EMAIL)
    stealth.human_delay(0.5, 1.0)
    page.locator("#identifierNext button").click()
    stealth.human_delay(2.0, 4.0)

    try:
        pwd_sel = page.locator("input[type='password']")
        pwd_sel.wait_for(state="visible", timeout=10000)
        pwd_sel.fill(_PASSWORD)
        stealth.human_delay(0.5, 1.0)
        page.locator("#passwordNext button").click()
        stealth.human_delay(3.0, 5.0)
    except Exception:
        pass

    try:
        page.wait_for_url("**/mail/**", timeout=30000)
    except Exception:
        pass
    stealth.human_delay(2.0, 3.0)
    logger.info("Gmail login completed")


def _poll_inbox(page, sender_hint: str, max_wait: int, poll_interval: int, stealth) -> Optional[str]:
    deadline = time.time() + max_wait

    while time.time() < deadline:
        _search_emails(page, sender_hint, stealth)
        stealth.human_delay(2.0, 3.0)

        email_body = _read_latest_email(page, stealth)
        if email_body:
            code = _extract_code(email_body)
            if code:
                logger.info(f"Found confirmation code: {code}")
                return code
            logger.info("Email found but no code in body — may need more time")
        else:
            logger.info(f"No email from '{sender_hint}' yet — retrying in {poll_interval}s")

        remaining = deadline - time.time()
        if remaining > 0:
            time.sleep(min(poll_interval, remaining))

    logger.warning(f"Timed out after {max_wait}s waiting for confirmation code")
    return None


def _search_emails(page, sender_hint: str, stealth):
    search_terms = [sender_hint]
    if sender_hint.lower() == "meta":
        search_terms = ["Meta", "facebookmail", "security@facebook"]
    elif sender_hint.lower() == "google":
        search_terms = ["Google", "security@google", "no-reply@google"]

    try:
        search_box = page.locator("input[aria-label*='search']")
        if not search_box.count():
            search_box = page.locator("input[name='q']")
        if search_box.count():
            for term in search_terms:
                search_box.click()
                search_box.fill("")
                stealth.human_delay(0.2, 0.4)
                search_box.fill(term)
                stealth.human_delay(0.3, 0.6)
                search_box.press("Enter")
                stealth.human_delay(2.0, 3.0)
                # Check if there are results
                first = page.locator("tr.zA").first
                if first.count():
                    return
    except Exception as e:
        logger.warning(f"Search failed: {e}")

    # Fallback: navigate directly to search URL
    for term in search_terms:
        try:
            page.goto(f"https://mail.google.com/mail/u/0/#search/{term}",
                      wait_until="domcontentloaded")
            stealth.human_delay(2.0, 3.0)
            first = page.locator("tr.zA").first
            if first.count():
                return
        except Exception:
            continue


def _read_latest_email(page, stealth) -> Optional[str]:
    try:
        first_email = page.locator("tr.zA").first
        if not first_email.count():
            first_email = page.locator("div[role='main'] a").first
        if not first_email.count():
            return None

        first_email.click()
        stealth.human_delay(2.0, 3.0)

        body_div = page.locator("div[role='main'] div.a3s")
        body_div.wait_for(state="visible", timeout=10000)
        return body_div.inner_text()
    except Exception as e:
        logger.debug(f"Read email failed: {e}")
        return None
