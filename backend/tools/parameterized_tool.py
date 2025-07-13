"""
Parameterized Tool Wrapper
Allows tools to be pre-configured with specific parameters
"""

from crewai.tools import BaseTool
from typing import Dict, Any, Callable
import json

class ParameterizedTool(BaseTool):
    """
    A wrapper that pre-configures a tool with specific parameters.
    When CrewAI calls _run, it uses the pre-configured parameters.
    """
    
    def __init__(self, base_tool: BaseTool, fixed_params: Dict[str, Any]):
        """
        Initialize with a base tool and fixed parameters
        
        Args:
            base_tool: The original tool to wrap
            fixed_params: Parameters that will always be passed to the tool
        """
        # Set the name and description for the parameterized tool
        # Create a unique name based on the action/parameters
        action = fixed_params.get('action', 'unknown')
        name = f"{base_tool.name}_{action}"
        description = f"{base_tool.description} (Pre-configured with: {fixed_params})"
        
        # Call parent constructor with just the required fields
        super().__init__(
            name=name,
            description=description
        )
        
        # Store the base tool and parameters as instance attributes
        self._base_tool = base_tool
        self._fixed_params = fixed_params
    
    def _run(self, *args, **kwargs) -> str:
        """
        Use the pre-configured parameters to call the base tool
        CrewAI might pass arguments or kwargs, but we prioritize our fixed parameters
        """
        # Handle case where CrewAI passes a JSON string as first argument
        if args and isinstance(args[0], str):
            try:
                # Try to parse as JSON and merge with our fixed params
                import json
                json_params = json.loads(args[0])
                
                # Smart merge: allow JSON params to override fixed params if they're not placeholders
                merged_params = {}
                
                # Start with fixed params
                for key, value in self._fixed_params.items():
                    merged_params[key] = value
                
                # Override with JSON params if they're not placeholders
                for key, value in json_params.items():
                    if self._is_real_value(value):
                        merged_params[key] = value
                
                # Finally, override with any additional kwargs
                merged_params.update(kwargs)
                
                all_params = merged_params
            except json.JSONDecodeError:
                # If not valid JSON, just use our fixed params
                all_params = {**self._fixed_params, **kwargs}
        else:
            # Use our pre-configured parameters, but allow additional kwargs to override if needed
            all_params = {**self._fixed_params, **kwargs}
        
        print(f"🔧 ParameterizedTool calling {self._base_tool.name} with: {all_params}")
        
        # Call the base tool's _run method with all parameters
        return self._base_tool._run(**all_params)
    
    def _is_real_value(self, value: Any) -> bool:
        """
        Check if a value is a real value (not a placeholder)
        """
        if not isinstance(value, str):
            return True
        
        # Remove # prefix for channel names before checking
        value_to_check = value.lstrip('#').lower().strip()
        
        # List of common placeholder patterns (without # prefix)
        placeholders = [
            "selected_channel", "your_channel", "target_channel", "channel_name",
            "your_message", "message_here", "message_content", "text_here", "your message here",
            "selected_user", "target_user", "user_name", "username",
            "query_here", "search_term", "search_query",
            "placeholder", "example", "sample"
        ]
        
        return not any(placeholder in value_to_check for placeholder in placeholders)

def create_parameterized_tool(tool_name: str, params: Dict[str, Any]) -> ParameterizedTool:
    """
    Factory function to create a parameterized tool
    
    Args:
        tool_name: Name of the tool to parameterize
        params: Parameters to pre-configure
    
    Returns:
        ParameterizedTool instance
    """
    from tools.tool_registry import instantiate_tool
    
    # Get the base tool
    base_tool = instantiate_tool(tool_name)
    
    # Create parameterized version
    return ParameterizedTool(base_tool, params) 