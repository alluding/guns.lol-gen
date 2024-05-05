from __future__ import annotations
from typing import (
    Dict,
    List,
    Literal,
    Optional,
    Any
)

from curl_cffi.requests import Session, Cookies

import orjson
import random
import string
import logging

from guns.solver import Solver, SolverConfig
from guns.logger import Logger


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
        self.config_logger()

    def config_logger(self) -> None:
        self.logger: logging.Logger = logging.getLogger("Generator")
        self.logger.setLevel(logging.DEBUG)
        if (handler := logging.StreamHandler()):
            handler.setFormatter(Logger())
            self.logger.addHandler(handler)

    def random_username(
        self,
        prefix: str,
        length: int = 4
    ) -> str:
        return f"{prefix}_{''.join(random.choices(string.digits, k=length))}"

    def random_email(
        self,
        prefix: str,
        domain: Literal["gmail.com", "hotmail.com", "yahoo.com"] = "gmail.com"
    ) -> str:
        return f"{self.random_username(prefix, 3)}@{domain}"

    def get_cookies(self) -> Cookies:
        response = self.session.get(
            "https://guns.lol/",
            allow_redirects=True
        )
        return response.cookies

    def register(self) -> None:
        _cookies = self.get_cookies()

        with open("config.json", "rb") as f:
            config_data: Dict[str, Any] = orjson.loads(f.read().decode("utf-8"))

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
            self.logger.error(f"{username} exceeds the 14 character limit!")
            return False

        email: str = self.random_email(
            prefix=config_data["username"],
            domain=random.choice(["gmail.com", "hotmail.com", "yahoo.com"])
        )

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
                # proxies={
                #     "http": "http://" + config_data["solver"]["proxy"],
                #     "https": "http://" + config_data["solver"]["proxy"]
                # },
                cookies={
                    "_1__bProxy_v": _cookies.get("_1__bProxy_v"),
                    "cf_clearance": "Dvzr3jMSksqgkp5siqkBNlQLebbck1rxYckwkM5mKPM-1714865345-1.0.1.1-0nQQxA5wt_u3EEmDr9wyIdZ9Gr4H1JrWBofy6XiD4GhwGMNgUyD3a5PkYhL9vpZLZpi58_uA26yYsMXDGeLtWA"
                },
                allow_redirects=False
            )
            
            print(response.text)
            self.logger.info(f"{username} » {email}")
        except Exception as e:
            self.logger.error(f"Failed to create guns.lol account! » {e}")


Guns().register()
