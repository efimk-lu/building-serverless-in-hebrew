from dataclasses import dataclass

@dataclass(frozen=True)
class Message:
    subject:str
    body: str
    schedule_on: int