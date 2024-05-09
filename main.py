from __future__ import annotations
from typing import Dict, List, Optional, Any

import re
import random
import string
import logging
import orjson
from threading import Thread, active_count

from curl_cffi.requests import Session, Cookies
from guns.solver import Solver, SolverConfig
from guns.logger import Logger
from guns.mail import Mail

PATTERN: re.Pattern = re.compile(r"https:\/\/guns\.lol\/verify\/[0-9a-f]{64}")
with open("config.json", "rb") as f:
    config_data: Dict[str, Any] = orjson.loads(f.read().decode("utf-8"))

logger: logging.Logger = logging.getLogger("Generator")
logger.setLevel(logging.DEBUG)
if (handler := logging.StreamHandler()):
    handler.setFormatter(Logger())
    logger.addHandler(handler)
    
class Guns:
    def __init__(self) -> None:
        self.session: Session = Session(
            impersonate="chrome119",
            headers={
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "text/plain;charset=UTF-8",
                "origin": "https://guns.lol",
                "referer": "https://guns.lol/register",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Linux i582 x86_64) AppleWebKit/535.47 (KHTML, like Gecko) Chrome/119.0.1621.282 Safari/537",
            }
        )

        self.mail: Optional[Mail] = None

    def random_username(
        self,
        prefix: str,
        length: int = 4
    ) -> str:
        return f"{prefix}_{''.join(random.choices(string.digits, k=length))}"

    def get_cookies(self) -> Cookies:
        return self.session.get("https://guns.lol/", allow_redirects=True).cookies

    def verify(
        self,
        email: str,
        username: str
    ) -> None:
        if self.mail is None:
            logger.error("Mail object is not initialized.")
            return

        for mail in self.mail.fetch_inbox():
            content = self.mail.get_message_content(mail["id"])
            if "To verify your account" in content:
                verify_id: str = PATTERN.findall(content)[0].split("verify/")[1]

                response = self.session.post(
                    "https://guns.lol/api/verify",
                    json={"id": verify_id}
                ).text
                if '"success":true' in response:
                    logger.info(
                        f"Successfully verified account. | {username} » {email}"
                    )

                    with open("./data/registered.txt", "a+") as file:
                        file.write(
                            f"{username}:{email}:lmfaogunslol123#$#$\n"
                        )
                    file.close()

                else:
                    logger.error(
                        f"Failed to verify account. | {username} » {email}"
                    )

                return

    def register(self) -> None:
        _cookies = self.get_cookies()

        self.mail = Mail(proxy="http://" + config_data["solver"]["proxy"])

        captcha_config = SolverConfig(
            apikey=str(config_data["solver"]["key"]),
            sitekey="227fe119-8d9e-490c-a0f0-5d9f8a41174d",
            host="https://guns.lol",
            proxy=str(config_data["solver"]["proxy"])
        )
        captcha = Solver(captcha_config)

        username: str = self.random_username(
            prefix=config_data["username"],
            length=3
        )

        if len(username) > 14:
            logger.error(f"{username} exceeds the 14 character limit!")
            return

        email: str = self.mail.get_mail()

        payload: Dict[str, str] = orjson.dumps({
            "username": username,
            "password": "lmfaogunslol123#$#$",
            "email": email,
            "captcha": captcha.solve()
        }).decode("utf-8")

        try:
            response = self.session.post(
                "https://guns.lol/api/register-acc",
                data=payload,
                cookies={
                    "_1__bProxy_v": _cookies.get("_1__bProxy_v"),
                    "cf_clearance": "Dvzr3jMSksqgkp5siqkBNlQLebbck1rxYckwkM5mKPM-1714865345-1.0.1.1-0nQQxA5wt_u3EEmDr9wyIdZ9Gr4H1JrWBofy6XiD4GhwGMNgUyD3a5PkYhL9vpZLZpi58_uA26yYsMXDGeLtWA"
                },
                allow_redirects=False
            )

            if response.status_code == 200:
                logger.info(
                    f"Verification email sent. | {username} » {email}"
                )
                self.verify(email, username)

            if response.status_code != 200:
                logger.error(
                    f"Failed to send verification email. » {email}"
                )

        except Exception as e:
            logger.error(f"Failed to create guns.lol account! » {e}")

while True:
    while active_count()-1 < config_data["threads"]:
        Thread(target=Guns().register).start()
