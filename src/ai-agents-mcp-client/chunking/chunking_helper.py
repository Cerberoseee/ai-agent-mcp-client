import logging
from typing import List
from bs4 import BeautifulSoup, Tag
import re
from dotenv import load_dotenv

class WrappingService:
    def __init__(self):
        load_dotenv()

    def clean_html_content(self, html_content):
        try:
            # Kiểm tra nếu html_content là None hoặc không phải là một string
            if not isinstance(html_content, str) or html_content is None:
                logging.error("Invalid or None HTML content provided.")
                return ""  # Trả về chuỗi rỗng nếu đầu vào không hợp lệ

            soup = BeautifulSoup(html_content, 'html.parser')
            if not isinstance(html_content, str):
                try:
                    html_content = html_content.decode("utf-8")
                except Exception:
                    logging.error("HTML content is not a string and cannot be decoded.")
                    return ""
            # Remove video, img tags with src not including https, and select tags
            try:
                
                index = 0
                tags = soup.find_all(['video', 'img', 'select', 'noscript'])
                for tag in list(tags):
                    
                    if tag.name == 'noscript':
                        continue
                    
                    if isinstance(tag, type(None)) or not hasattr(tag, 'name'):
                        continue
                    # print("-----------", tag , "-------------", "0100103013013", index)
                    if tag.name == 'select':
                        tag.decompose()
                    elif tag.has_attr('src'):
                        noscript_inside = tag.find('noscript')
                        if noscript_inside:
                            continue
                        src = tag.get("src")
                        if src is None or not src.startswith('https'):
                            
                            tag.decompose()
                    index += 1
            except Exception as e:
                logging.error(f"Error processing tag : {e}")

            # Remove all class attributes from all tags if they exist
            for tag in soup.find_all(True):  # True means all tags
                if 'class' in tag.attrs:
                    tag.attrs.pop('class', None)
                    
            return str(soup)
        except Exception as e:
            msg = f"Clean html content error: {e}"
            logging.error(msg)
            # Explicitly convert error message to string to avoid concatenation errors
            raise Exception(msg) from e

    def parse_content(self, element):
        try:
            if element is None:
                logging.error("Provided element is None.")
                return ""

            tag_name = element.name.lower()
            # Loại bỏ các thẻ không mong muốn
            if tag_name in ['script', 'style', 'img', 'video']:
                return ""

            children = element.find_all(recursive=False)
            text_tags = ['li', 'ol', 'p', 'h1', 'h2',
                         'h3', 'h4', 'h5', 'h6', 'span', 'a']

            if tag_name in text_tags:
                content_parse = str(element)
                cleaned_html_content = re.sub(
                    r'<svg[^>]*>.*?</svg>', '', content_parse, flags=re.DOTALL)
                if cleaned_html_content:
                    return cleaned_html_content
                else:
                    return ''

            extra_content = ""
            if tag_name in ["section", "footer", "header"]:
                extra_content = '\n****************************************\n'
            else:
                for heading_level in range(1, 3):
                    heading_tags = element.find_all(f'h{heading_level}')
                    if len(heading_tags) == 1:  # Chỉ có một thẻ heading
                        extra_content = '\n****************************************\n'
            contents = [self.parse_content(child) for child in children]
            current_content = '\n--------------------------------------------------\n'.join(
                filter(None, contents))
            current_content = extra_content + current_content + extra_content

            if current_content:
                return current_content
            else:
                return ''
        except Exception as e:
            msg = f"Parse content fail: {e}"
            logging.error(msg)
            raise Exception(msg) from e

    def clean_content(self, input_string):
        input_string = input_string.replace(
            '\n--------------------------------------------------\n', '\n')
        return input_string

    def split_and_clean_content(self, input_text):
        try:
            segments = input_text.split(
                '****************************************')
            cleaned_segments = [segment.strip()
                                for segment in segments if segment.strip()]
            return cleaned_segments
        except Exception as e:
            msg = f"Split and clean content failed: {e}"
            logging.error(msg)
            raise Exception(msg) from e

class HTMLProcessor:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def clean_html(self) -> None:
        for br in self.soup.find_all('br'):
            br.decompose()
        for p in self.soup.find_all('p'):
            if not p.get_text().strip():
                p.decompose()

    def is_potential_heading(self, p_tag: Tag) -> bool:
        # styled span
        if p_tag.find('span', style=lambda x: x and ('tw-prose-bold' in x or 'font-weight:bold' in x)):
            return True
        return False

    def get_elements(self) -> List[Tag]:
        return self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', "li"])

class GenerateKnowledge:
    def __init__(self, content: str, title: str):
        self.content = content
        self.title = title

class ArticleSection:
    def __init__(self, heading: str, heading_tag: Tag, content: List[Tag], level: int):
        self.heading = heading
        self.heading_tag = heading_tag
        self.content = content
        self.level = level

    def get_formatted_content(self) -> str:
        return str(self.heading_tag) + "".join(str(tag) for tag in self.content)

    def get_text_content(self) -> str:
        return " ".join([self.heading] + [tag.get_text() for tag in self.content])

    def __str__(self) -> str:
        return f"Section(heading='{self.heading}', level={self.level}, content_length={len(self.content)})"

def format_loader_article(raw_html: str) -> List[ArticleSection]:
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        html_processor = HTMLProcessor(soup)
        html_processor.clean_html()

        sections: List[ArticleSection] = []
        current_heading = None
        current_heading_tag = None
        current_level = 1
        current_content: List[Tag] = []

        for element in html_processor.get_elements():
            # h3 headings
            if element.name.startswith("h"):
                if current_heading:
                    sections.append(
                        ArticleSection(
                            heading=current_heading,
                            heading_tag=current_heading_tag,
                            content=current_content.copy(),
                            level=current_level,
                        )
                    )
                current_heading = element.get_text().strip()
                current_heading_tag = element
                current_level = int(element.name[1])
                current_content = []

            # p tags
            elif element.name == "p":
                if html_processor.is_potential_heading(element):
                    if current_heading and current_content:
                        sections.append(
                            ArticleSection(
                                heading=current_heading,
                                heading_tag=current_heading_tag,
                                content=current_content.copy(),
                                level=current_level,
                            )
                        )
                    current_heading = element.get_text().strip()
                    current_heading_tag = element
                    current_content = []
                else:
                    if not current_heading:
                        current_heading = element.get_text().strip()
                        current_heading_tag = element
                    else:
                        current_content.append(element)

            # ul elements
            elif element.name == "ul" or element.name == "li":
                if current_heading:
                    current_content.append(element)
                else:
                    if current_content:
                        last_p = current_content[-1]
                        current_heading = last_p.get_text().strip()
                        current_heading_tag = last_p
                        current_content = current_content[:-1]
                    current_content.append(element)

        if current_heading and current_content:
            sections.append(
                ArticleSection(
                    heading=current_heading,
                    heading_tag=current_heading_tag,
                    content=current_content.copy(),
                    level=current_level,
                )
            )
        return sections

    except Exception as e:
        logging.error(f"Error when formatting article data: {e}")
        raise Exception("Error when formatting article data: " + str(e))