from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import uuid4

import logging

class BaseChunker:
    @abstractmethod
    def create_chunks(self, data):
        pass


class Senetence:
    _id: uuid4
    _content: str = ""

    def __init__(self, content: str = ""):
        self._id = uuid4()
        self._content = content

    def get_id(self):
        return self._id

    def get_content(self) -> str:
        return self._content


class Paragraph:
    _id: uuid4

    def __init__(self, sentences: Optional[List[Senetence]] = None):
        self._id = uuid4()
        self.sentences = sentences if sentences is not None else []

    def get_id(self):
        return self._id

    def restore(self):
        try:
            if self.sentences:
                return " ".join(
                    [sentence.get_content() for sentence in self.sentences]
                ).strip()
            return None
        except Exception as e:
            logging.error(f"Failed to restore at paragraph level: {e}")
            return None

class Section:
    _id: uuid4

    def __init__(self, paragraphs: Optional[List[Paragraph]] = None):
        self._id = uuid4()
        self.paragraphs = paragraphs if paragraphs is not None else []

    def get_id(self):
        return self._id

    def restore(self):
        try: 
            if self.paragraphs:
                return "\n".join(
                    [paragraph.restore() for paragraph in self.paragraphs]
                ).strip()
            return None
        except Exception as e:
            logging.error(f"Failed to restore at section level: {e}")
            return None

class Document(ABC):
    def __init__(self, sections: Optional[List[Section]] = None):
        self._id = uuid4()
        self.sections = sections if sections is not None else []
    
    def restore(self, delimeters: str = "\n\n"):
        try:
            if self.sections:
                return delimeters.join(
                    [section.restore() for section in self.sections]
                ).strip()
            return None
        except Exception as e:
            logging.error(f"Failed to restore at document level: {e}")
            return None
            
        
