from __future__ import annotations
from typing import Optional, Dict
from pydantic import BaseModel

from .logger import Logger
import logging

import requests


class SolverConfig(BaseModel):
    apikey: str
    sitekey: str
    proxy: str
    host: str
    rqdata: Optional[str] = None
    user_agent: Optional[str] = None


logger: logging.Logger = logging.getLogger("Solver")
logger.setLevel(logging.DEBUG)

if (handler := logging.StreamHandler()) is not None:
    handler.setFormatter(Logger())
    logger.addHandler(handler)


class Solver:
    BASE_URL: str = "https://api.fcaptcha.lol/api/"

    def __init__(self, config: SolverConfig) -> None:
        self.config: SolverConfig = config

    def solve(self: Solver) -> str:
        try:
            payload: Dict[str, str] = {
                key: getattr(self.config, key)
                for key in ("host", "sitekey", "proxy", "user_agent", "rqdata")
                if hasattr(self.config, key)
            }

            result = requests.post(
                self.BASE_URL + "createTask",
                headers={"authorization": self.config.apikey},
                json=payload
            ).json()

            task_id: str = result["task"].get(
                "task_id",
                "Failed to get task ID!"
            )
            new_payload: Dict[str, str] = {"task_id": task_id}
            logger.info(f"Retrieved task_id » {task_id}")

            while True:
                result = requests.get(
                    self.BASE_URL + "getTaskData",
                    headers={"authorization": self.config.apikey},
                    json=new_payload
                ).json()

                if result["task"].get("state") == "processing":
                    continue

                logger.info(f"Successfully solved captcha » {result['task']['time']}")
                return result["task"].get("captcha_key")
        except Exception as e:
            logger.error(f"Failed to solve captcha » {e}")
