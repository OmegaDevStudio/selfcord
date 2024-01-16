from typing import Optional, Literal


class Activity:
    def __init__(self, status: Literal[
        "online", "dnd", "idle", "invisible", "offline"
    ], afk: bool) -> None:
        self.status = status
        self.afk = afk

    

    def Streaming(
        self, name: str,
        url: Optional[str] = None,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        party_id: Optional[str] = None,
        party_size: Optional[list] = None,
        join: Optional[str] = None,
        match: Optional[str] = None,
        spectate: Optional[str] = None,
        buttons: Optional[list] = None,
        instance: bool = True, payload_override: Optional[dict] = None
    ):
        if payload_override:
            payload = payload_override
        else:
            if start:
                start = int(start)
            if end:
                end = int(end)

            activity = {
                "name": name,
                "type": 1,
                "state": state,
                "details": details,
                "url": url,
                "timestampts": {
                    "start": start,
                    "end": end
                },
                "assets": {
                    "large_image": large_image,
                    "large_text": large_text,
                    "small_image": small_image,
                    "small_text": small_text,
                },
                "party": {
                    "party_id": party_id,
                    "size": party_size
                },
                "secrets": {
                    "join": join,
                    "spectate": spectate,
                    "match": match
                },
                "buttons": buttons,
                "instance": instance
            }
            payload = {
                "op": 3,
                "d": {
                    "activities": [activity],
                    "status": self.status,
                    "afk": self.afk
                }
            }
        return payload

    def Listening(
        self, name: str,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        party_id: Optional[str] = None,
        party_size: Optional[list] = None,
        join: Optional[str] = None,
        match: Optional[str] = None,
        spectate: Optional[str] = None,
        buttons: Optional[list] = None,
        instance: bool = True, payload_override: Optional[dict] = None
    ):
        if payload_override:
            payload = payload_override
        else:
            if start:
                start = int(start)
            if end:
                end = int(end)

            activity = {
                "name": name,
                "type": 2,
                "state": state,
                "details": details,
                "timestampts": {
                    "start": start,
                    "end": end
                },
                "assets": {
                    "large_image": large_image,
                    "large_text": large_text,
                    "small_image": small_image,
                    "small_text": small_text,
                },
                "party": {
                    "party_id": party_id,
                    "size": party_size
                },
                "secrets": {
                    "join": join,
                    "spectate": spectate,
                    "match": match
                },
                "buttons": buttons,
                "instance": instance
            }
            payload = {
                "op": 3,
                "d": {
                    "activities": [activity],
                    "status": self.status,
                    "afk": self.afk
                }
            }
        return payload

    def Watching(
        self, name: str,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        party_id: Optional[str] = None,
        party_size: Optional[list] = None,
        join: Optional[str] = None,
        match: Optional[str] = None,
        spectate: Optional[str] = None,
        buttons: Optional[list] = None,
        instance: bool = True, payload_override: Optional[dict] = None
    ):
        if payload_override:
            payload = payload_override
        else:
            if start:
                start = int(start)
            if end:
                end = int(end)

            activity = {
                "name": name,
                "type": 3,
                "state": state,
                "details": details,
                "timestampts": {
                    "start": start,
                    "end": end
                },
                "assets": {
                    "large_image": large_image,
                    "large_text": large_text,
                    "small_image": small_image,
                    "small_text": small_text,
                },
                "party": {
                    "party_id": party_id,
                    "size": party_size
                },
                "secrets": {
                    "join": join,
                    "spectate": spectate,
                    "match": match
                },
                "buttons": buttons,
                "instance": instance
            }
            payload = {
                "op": 3,
                "d": {
                    "activities": [activity],
                    "status": self.status,
                    "afk": self.afk
                }
            }
        return payload

    def Competing(
        self, name: str,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        party_id: Optional[str] = None,
        party_size: Optional[list] = None,
        join: Optional[str] = None,
        match: Optional[str] = None,
        spectate: Optional[str] = None,
        buttons: Optional[list] = None,
        instance: bool = True, payload_override: Optional[dict] = None
    ):
        if payload_override:
            payload = payload_override
        else:
            if start:
                start = int(start)
            if end:
                end = int(end)

            activity = {
                "name": name,
                "type": 5,
                "state": state,
                "details": details,
                "timestampts": {
                    "start": start,
                    "end": end
                },
                "assets": {
                    "large_image": large_image,
                    "large_text": large_text,
                    "small_image": small_image,
                    "small_text": small_text,
                },
                "party": {
                    "party_id": party_id,
                    "size": party_size
                },
                "secrets": {
                    "join": join,
                    "spectate": spectate,
                    "match": match
                },
                "buttons": buttons,
                "instance": instance
            }
            payload = {
                "op": 3,
                "d": {
                    "activities": [activity],
                    "status": self.status,
                    "afk": self.afk
                }
            }
        return payload

    def Custom(self, status: str, emoji_name: Optional[str], id: Optional[str], animated: Optional[bool] = False):
        payload = {
            "op": 3,
            "d": {
                "activities": [{
                    "type": 4,
                    "name": status,
                    "emoji": {
                        "name": emoji_name,
                        "id": id,
                        "animated": animated
                    }
                }],
                "status": self.status,
                "afk": self.afk
            }
        }
        return payload

    def Playing(
        self, name: str,
        state: Optional[str] = None,
        details: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        party_id: Optional[str] = None,
        party_size: Optional[list] = None,
        join: Optional[str] = None,
        match: Optional[str] = None,
        spectate: Optional[str] = None,
        buttons: Optional[list] = None,
        instance: bool = True, payload_override: Optional[dict] = None
    ):
        if payload_override:
            payload = payload_override
        else:
            if start:
                start = int(start)
            if end:
                end = int(end)

            activity = {
                "name": name,
                "type": 0,
                "state": state,
                "details": details,
                "timestampts": {
                    "start": start,
                    "end": end
                },
                "assets": {
                    "large_image": large_image,
                    "large_text": large_text,
                    "small_image": small_image,
                    "small_text": small_text,
                },
                "party": {
                    "party_id": party_id,
                    "size": party_size
                },
                "secrets": {
                    "join": join,
                    "spectate": spectate,
                    "match": match
                },
                "buttons": buttons,
                "instance": instance
            }
            payload = {
                "op": 3,
                "d": {
                    "activities": [activity],
                    "status": self.status,
                    "afk": self.afk
                }
            }
        return payload