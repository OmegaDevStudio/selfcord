from typing import Optional, Literal
import time

class Activity:
    def __init__(self) -> None:
        self.dict = {}


    def remove_null(self, dic: dict):
        new = {}
        for key, value in dic.items():
            if value == None:
                continue
            if isinstance(value, dict):
        
                value = self.remove_null(value)
          
            if value == {}:
                continue
            new[key] = value
        return new



    def Playing(
        self,
        application_id: str,
        name: str,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        buttons: list[dict[str, str]] = [],
        party_id: Optional[str] = None,
        party_size: Optional[list[int]] = None,
        match_secret: Optional[str] = None,
        join_secret: Optional[str] = None,
        spectate_secret: Optional[str] = None,
        instance: Optional[bool] = None
    ):
        self.dict['type'] = 0
        self.dict['application_id'] = application_id
        self.dict['name'] = name
        self.dict['details'] = details
        self.dict['state'] = state
        self.dict['timestamps'] = {"start": start, "end": end}
        self.dict['assets'] = {"large_image": large_image, "large_text": large_text, "small_image": small_image, "small_text": small_text}
        if len(buttons) > 0:
            if len(buttons) > 2:
                raise ValueError("You can only have 2 buttons")
            self.dict['buttons'] = []
            self.dict['metadata'] = []
            for button in buttons:
                self.dict['buttons'].append(button['label'])
                self.dict['metadata'].append(button['url'])
        self.dict['party'] = {"id": party_id, "size": party_size}
        self.dict['secrets'] = {"match": match_secret, "join": join_secret, "spectate": spectate_secret}

        self.dict['created_at'] = int(time.time())
        self.dict['instance'] = instance
        
        return self.remove_null(self.dict)


    def Streaming(
        self,
        application_id: str,
        name: str,
        url: Optional[str] = None,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        buttons: list[dict[str, str]] = [],
    ):
        self.dict['type'] = 1
        self.dict['application_id'] = application_id
        self.dict['name'] = name
        self.dict['url'] = url
        self.dict['details'] = details
        self.dict['state'] = state
        self.dict['timestamps'] = {"start": start, "end": end}
        self.dict['assets'] = {"large_image": large_image, "large_text": large_text, "small_image": small_image, "small_text": small_text}
        if len(buttons) > 0:
            if len(buttons) > 2:
                raise ValueError("You can only have 2 buttons")
            self.dict['buttons'] = []
            self.dict['metadata'] = []
            for button in buttons:
                self.dict['buttons'].append(button['label'])
                self.dict['metadata'].append(button['url'])
        self.dict['created_at'] = int(time.time())
     
        return self.remove_null(self.dict)


    def Listening(self,
        application_id: str,
        name: str,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        buttons: list[dict[str, str]] = [],
    ):
        self.dict['type'] = 2
        self.dict['application_id'] = application_id
        self.dict['name'] = name
        self.dict['details'] = details
        self.dict['state'] = state
        self.dict['timestamps'] = {"start": start, "end": end}
        self.dict['assets'] = {"large_image": large_image, "large_text": large_text, "small_image": small_image, "small_text": small_text}
        if len(buttons) > 0:
            if len(buttons) > 2:
                raise ValueError("You can only have 2 buttons")
            self.dict['buttons'] = []
            self.dict['metadata'] = []
            for button in buttons:
                self.dict['buttons'].append(button['label'])
                self.dict['metadata'].append(button['url'])
        self.dict['created_at'] = int(time.time())
 
        return self.remove_null(self.dict)
    
    def Watching(self,
        application_id: str,
        name: str,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        buttons: list[dict[str, str]] = [],
    ):
        self.dict['type'] = 3
        self.dict['application_id'] = application_id
        self.dict['name'] = name
        self.dict['details'] = details
        self.dict['state'] = state
        self.dict['timestamps'] = {"start": start, "end": end}
        self.dict['assets'] = {"large_image": large_image, "large_text": large_text, "small_image": small_image, "small_text": small_text}
        if len(buttons) > 0:
            if len(buttons) > 2:
                raise ValueError("You can only have 2 buttons")
            self.dict['buttons'] = []
            self.dict['metadata'] = []
            for button in buttons:
                self.dict['buttons'].append(button['label'])
                self.dict['metadata'].append(button['url'])
        self.dict['created_at'] = int(time.time())

        return self.remove_null(self.dict)

    def Custom(self, state: str, emoji: Optional[str] = None, id: Optional[str] = None, animated: Optional[bool] = None):
        self.dict['type'] = 4
        self.dict['state'] = state
        self.dict['emoji'] = {"name": emoji, "id": id, "animated": animated}

        self.remove_null(self.dict)
        return self.remove_null(self.dict)

    def Competing(self,
        application_id: str,
        name: str,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        buttons: list[dict[str, str]] = [],
    ):
        self.dict['type'] = 5
        self.dict['application_id'] = application_id
        self.dict['name'] = name
        self.dict['details'] = details
        self.dict['state'] = state
        self.dict['timestamps'] = {"start": start, "end": end}
        self.dict['assets'] = {"large_image": large_image, "large_text": large_text, "small_image": small_image, "small_text": small_text}
        if len(buttons) > 0:
            if len(buttons) > 2:
                raise ValueError("You can only have 2 buttons")
            self.dict['buttons'] = []
            self.dict['metadata'] = []
            for button in buttons:
                self.dict['buttons'].append(button['label'])
                self.dict['metadata'].append(button['url'])
        self.dict['created_at'] = int(time.time())
       
        return self.remove_null(self.dict)

