"""
Fix of @imvast MailGw wrapper.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any

import httpx
import random
import string

import logging

logger: logging.Logger = logging.getLogger("Generator")

class Mail(httpx.Client):
    BASE_URL: str = "https://api.mail.gw"
    
    def __init__(self, proxy: str = None, timeout: int = 15) -> None:
        super().__init__(
            headers={
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json",
                "origin": "https://mail.gw",
                "referer": "https://mail.gw/",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Linux i582 x86_64) AppleWebKit/535.47 (KHTML, like Gecko) Chrome/119.0.1621.282 Safari/537",
            },
            timeout=timeout,
            proxies=proxy
        )

    def get_domains(self: Mail) -> List[str]:
        response = self.get(f"{self.base_url}/domains").json()
        return [item["domain"] for item in response.get("hydra:member", [])]

    def get_token(
        self: Mail,
        data: str
    ) -> None:
        response = self.post(
            f"{self.base_url}/token",
            json={"address": data, "password": data}
        )
        if token := response.json().get("token"):
            self.headers["authorization"] = f"Bearer {token}"

    def get_mail(
        self: Mail,
        name: Optional[str] = None,
        password: Optional[str] = None,
        domain: Optional[str] = None
    ) -> str:
        name: str = name or "".join(random.choice(string.ascii_lowercase) for _ in range(15))
        domain: str = domain or self.get_domains()[0]
        mail: str = f"{name}@{domain}"

        try:
            response = self.post(
                f"{self.base_url}/accounts",
                json={"address": mail, "password": mail}
            )
            if response.status_code == 201:
                self.get_token(mail)
                return mail
            else:
                print(response.text)
              
        except Exception as e:
            logger.error(f"Failed to create email! - {mail} » {e}")

    def fetch_inbox(self: Mail) -> List[Dict]:
        return self.get(f"{self.base_url}/messages").json().get("hydra:member", [])

    def get_message(self: Mail, message_id: str) -> Dict[Any, Any]:
        return self.session.get(f"{self.base_url}/messages/{message_id}").json()

    def get_message_content(self: Mail, message_id: str) -> str:
        return self.get_message(message_id).get("text", "")
