import logging
import uuid
from typing import List

from chunking import BaseChunker, Document, Paragraph, Section, Senetence
from chunking.chunking_const import HEADERLEVEL
from chunking.chunking_helper import format_markdown_article, ArticleSection, WrappingService

class DocumentSpecificChunker(BaseChunker):
    def __init__(self, max_length=100):
        super().__init__()
        self.max_length = max_length
        
        self.wrapper_service = WrappingService()
    
    def get_chunking_method(self):
        return self._chunking_method

    async def create_chunks(self, data) -> Document:
        try:
            content = format_markdown_article(data)
            formatted_content = await self.transform_chunks_into_tree(content)
            if formatted_content:
                return formatted_content
            return None
        except Exception as e:
            logging.error(f'Failed create chunks for document: {e}')
            return None

    async def transform_chunks_into_tree(self, chunks: List[ArticleSection], ) -> Document:
        try: 
            tree: Document = Document()
            current_paragraph_index = 0
            is_create_new_section = False
            for chunk in chunks:
                if chunk.level == HEADERLEVEL.SECTION.value:                    
                        section_obj = Section()
                        parent_id = section_obj.get_id()
                        is_create_new_section = False
                        if chunk.content:
                            section_obj.paragraphs.append(Paragraph(sentences=[Senetence(content=str(content)) for content in chunk.content] if chunk.content else str(chunk.heading_tag)))
                        tree.sections.append(section_obj)
                elif chunk.level >= HEADERLEVEL.PARAGRAPH.value:
                    if parent_id:
                        if is_create_new_section:
                            current_paragraph_index += 1
                        if chunk.content:
                            tree.sections[current_paragraph_index].paragraphs.append(Paragraph(sentences=[Senetence(content=str(content)) for content in chunk.content] if chunk.content else str(chunk.heading_tag)))
            return tree
        except Exception as e:
            logging.error(f"Error transform chunks into tree: {e}")
            return None