"""
Fix of @imvast MailGw wrapper.
"""

from typing import Optional, List, Dict

import httpx
import random
import string

import logging

logger: logging.Logger = logging.getLogger("Generator")


class Mail:
    def __init__(self, proxy: str = None, timeout: int = 15) -> None:
        self.session: httpx.Client = httpx.Client(
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
        self.base_url: str = "https://api.mail.gw"

    def get_domains(self) -> List[str]:
        response = self.session.get(f"{self.base_url}/domains").json()
        domains = [item["domain"] for item in response.get("hydra:member", [])]
        return domains

    def get_token(
        self,
        data: str
    ) -> None:
        response = self.session.post(
            f"{self.base_url}/token",
            json={"address": data, "password": data}
        )
        if token := response.json().get("token"):
            self.session.headers["authorization"] = f"Bearer {token}"

    def get_mail(
        self,
        name: str = None,
        password: str = None,
        domain: Optional[str] = None
    ) -> str:
        name: str = name or "".join(random.choice(string.ascii_lowercase) for _ in range(15))
        domain: str = domain or self.get_domains()[0]
        mail: str = f"{name}@{domain}"

        try:
            response = self.session.post(
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

    def fetch_inbox(self) -> List[Dict]:
        response = self.session.get(f"{self.base_url}/messages").json()
        return response.get("hydra:member", [])

    def get_message(self, message_id: str) -> Dict:
        response = self.session.get(f"{self.base_url}/messages/{message_id}").json()
        return response

    def get_message_content(self, message_id: str) -> str:
        message = self.get_message(message_id)
        return message.get("text", "")
