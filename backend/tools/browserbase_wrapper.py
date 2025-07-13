import tiktoken
import re
from typing import Optional
from crewai_tools import BrowserbaseLoadTool
from bs4 import BeautifulSoup
from pydantic import Field


class BrowserbaseWrapper(BrowserbaseLoadTool):
    """
    A wrapper around BrowserbaseLoadTool that limits content size to prevent token limit errors.
    """
    
    max_tokens: int = Field(default=150000, description="Maximum tokens to process")
    encoding: Optional[object] = Field(default=None, description="Tiktoken encoding object")
    
    def __init__(self, api_key: str, project_id: str, max_tokens: int = 150000, **kwargs):
        # Initialize the parent BrowserbaseLoadTool
        super().__init__(
            api_key=api_key,
            project_id=project_id,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Set our additional attributes
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # Fallback to rough character-based estimation
            return len(text) // 4
    
    def _clean_html_content(self, html_content: str) -> str:
        """Clean and extract main content from HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Remove common navigation and advertisement elements
            for element in soup.find_all(attrs={"class": re.compile(r"nav|menu|sidebar|ad|advertisement|cookie|popup", re.I)}):
                element.decompose()
            
            # Extract main content areas first
            main_content = ""
            for tag in ["main", "article", "section", "div"]:
                content_areas = soup.find_all(tag, attrs={"class": re.compile(r"content|main|article|post", re.I)})
                if content_areas:
                    main_content = " ".join([area.get_text(strip=True) for area in content_areas])
                    break
            
            # If no main content found, get all text
            if not main_content:
                main_content = soup.get_text(strip=True)
            
            # Clean up whitespace
            main_content = re.sub(r'\s+', ' ', main_content).strip()
            
            return main_content
            
        except Exception:
            # Fallback to simple text extraction
            return re.sub(r'<[^>]+>', '', html_content)
    
    def _truncate_content(self, content: str) -> str:
        """Truncate content to stay under token limit."""
        token_count = self._count_tokens(content)
        
        if token_count <= self.max_tokens:
            return content
        
        # Binary search for optimal truncation point
        left, right = 0, len(content)
        best_content = content[:self.max_tokens * 4]  # Rough fallback
        
        while left < right:
            mid = (left + right + 1) // 2
            candidate = content[:mid]
            
            if self._count_tokens(candidate) <= self.max_tokens:
                best_content = candidate
                left = mid
            else:
                right = mid - 1
        
        # Add truncation notice
        if len(best_content) < len(content):
            best_content += "\n\n[Content truncated due to size limits]"
        
        return best_content
    
    def _run(self, url: str, **kwargs) -> str:
        """Run the browserbase tool with content filtering."""
        try:
            # Get content from parent browserbase tool
            raw_content = super()._run(url, **kwargs)
            
            # Handle empty content
            if not raw_content or raw_content.strip() == "":
                return f"No content retrieved from {url}"
            
            # Clean HTML and extract main content
            cleaned_content = self._clean_html_content(raw_content)
            
            # Truncate if necessary
            final_content = self._truncate_content(cleaned_content)
            
            return final_content
            
        except Exception as e:
            return f"Error loading website {url}: {str(e)}"
    
    
