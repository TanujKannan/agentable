import re
from crewai_tools import DallETool
from pydantic import Field


class DalleWrapper(DallETool):
    """
    A wrapper around DallETool that cleans up markdown output formatting.
    """
    
    def _run(self, image_description: str, **kwargs) -> str:
        """Run the DALL-E tool and clean up the markdown output."""
        try:
            # Get result from parent DALL-E tool
            raw_result = super()._run(image_description, **kwargs)
            
            # Clean up the markdown output
            # Remove the "!Generated Image" placeholder text that pollutes the output
            cleaned_result = self._clean_dalle_output(raw_result)
            
            return cleaned_result
            
        except Exception as e:
            return f"Error generating image: {str(e)}"
    
    def _clean_dalle_output(self, output: str) -> str:
        """Clean up DALL-E output to remove markdown pollution."""
        if not output or not isinstance(output, str):
            return output
        
        # Only remove standalone "!Generated Image" text that pollutes the markdown
        # Do NOT modify the actual image markdown syntax - that breaks the images
        
        # Remove standalone "!Generated Image" text (not in markdown brackets)
        # This preserves actual image URLs while removing pollution
        cleaned = output.replace('!Generated Image', '')
        
        # Clean up any extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned