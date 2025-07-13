"""
Google Slides Tool for CrewAI
Handles creating, editing, and managing Google Slides presentations
"""

import os
from typing import Dict, Any, List, Optional, ClassVar
from crewai.tools import BaseTool
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import json
from pydantic import PrivateAttr, Field

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class GoogleSlidesTool(BaseTool):
    """
    A tool for creating and editing Google Slides presentations.
    
    Capabilities:
    - Create new presentations
    - Add slides with different layouts
    - Insert text, images, and shapes
    - Modify slide content
    - Export presentations
    - Share presentations
    
    Required parameters:
    - action: The operation to perform (create, add_slide, insert_text, etc.)
    - presentation_id: ID of the presentation (for existing presentations)
    - title: Title for new presentations or slides
    """
    
    # Class variable for Google API scopes
    SCOPES: ClassVar[List[str]] = ['https://www.googleapis.com/auth/presentations']
    _creds: Any = PrivateAttr(default=None)
    _service: Any = PrivateAttr(default=None)
    
    # Required BaseTool fields
    name: str = Field(default="google_slides_tool", description="Tool name")
    description: str = Field(default="Tool for creating and editing Google Slides presentations. Use with action parameter: create_presentation, add_slide, insert_text, insert_image, get_presentation, update_slide, delete_slide", description="Tool description")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Slides API"""
        # Try to load from environment variables first
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError(
                "Google credentials not found in environment variables. "
                "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file"
            )
        
        # Check for existing token in env
        token_info = os.getenv('GOOGLE_TOKEN_INFO')
        if token_info:
            try:
                token_data = json.loads(token_info)
                self._creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
            except Exception as e:
                print(f"Warning: Could not load token from GOOGLE_TOKEN_INFO: {e}")
                self._creds = None
        
        # If no valid credentials, use OAuth flow
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                try:
                    self._creds.refresh(Request())
                except Exception as e:
                    print(f"Warning: Could not refresh token: {e}")
                    self._creds = None
            
            if not self._creds or not self._creds.valid:
                # Create OAuth flow with env credentials
                try:
                    flow = InstalledAppFlow.from_client_config({
                        "installed": {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost"]
                        }
                    }, self.SCOPES)
                    print("🌐 Opening browser for Google OAuth authentication...")
                    self._creds = flow.run_local_server(port=0)
                    print("✅ Google OAuth authentication successful!")
                except Exception as e:
                    raise Exception(f"Google OAuth authentication failed: {e}")
        
        if not self._creds:
            raise Exception("Failed to obtain valid Google credentials")
        
        self._service = build('slides', 'v1', credentials=self._creds)
    
    def _run(self, action: str, **kwargs) -> str:
        """
        Dispatches the requested Google Slides action. This method is called by CrewAI with all task parameters.
        Required parameter: action (str)
        Other parameters depend on the action.
        """
        try:
            if action == "create_presentation":
                return self._create_presentation(title=kwargs.get("title", "New Presentation"))
            elif action == "add_slide":
                presentation_id = kwargs.get("presentation_id")
                if not presentation_id:
                    return json.dumps({"status": "error", "message": "Missing required parameter: presentation_id"})
                layout = kwargs.get("layout", "TITLE_AND_BODY")
                return self._add_slide(presentation_id=presentation_id, layout=layout)
            elif action == "insert_text":
                presentation_id = kwargs.get("presentation_id")
                slide_id = kwargs.get("slide_id")
                text = kwargs.get("text")
                if not presentation_id or not slide_id or not text:
                    return json.dumps({"status": "error", "message": "Missing required parameter(s): presentation_id, slide_id, text"})
                x = kwargs.get("x", 100)
                y = kwargs.get("y", 100)
                return self._insert_text(
                    presentation_id=presentation_id,
                    slide_id=slide_id,
                    text=text,
                    x=x,
                    y=y
                )
            elif action == "insert_image":
                presentation_id = kwargs.get("presentation_id")
                slide_id = kwargs.get("slide_id")
                image_url = kwargs.get("image_url")
                if not presentation_id or not slide_id or not image_url:
                    return json.dumps({"status": "error", "message": "Missing required parameter(s): presentation_id, slide_id, image_url"})
                x = kwargs.get("x", 100)
                y = kwargs.get("y", 100)
                return self._insert_image(
                    presentation_id=presentation_id,
                    slide_id=slide_id,
                    image_url=image_url,
                    x=x,
                    y=y
                )
            elif action == "get_presentation":
                presentation_id = kwargs.get("presentation_id")
                if not presentation_id:
                    return json.dumps({"status": "error", "message": "Missing required parameter: presentation_id"})
                return self._get_presentation(presentation_id=presentation_id)
            elif action == "update_slide":
                presentation_id = kwargs.get("presentation_id")
                slide_id = kwargs.get("slide_id")
                updates = kwargs.get("updates") or {}
                if not presentation_id or not slide_id:
                    return json.dumps({"status": "error", "message": "Missing required parameter(s): presentation_id, slide_id"})
                return self._update_slide(
                    presentation_id=presentation_id,
                    slide_id=slide_id,
                    updates=updates
                )
            elif action == "delete_slide":
                presentation_id = kwargs.get("presentation_id")
                slide_id = kwargs.get("slide_id")
                if not presentation_id or not slide_id:
                    return json.dumps({"status": "error", "message": "Missing required parameter(s): presentation_id, slide_id"})
                return self._delete_slide(
                    presentation_id=presentation_id,
                    slide_id=slide_id
                )
            else:
                return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Exception in GoogleSlidesTool: {str(e)}"})
    
    def _create_presentation(self, title: str = "New Presentation") -> str:
        """Create a new Google Slides presentation"""
        try:
            if not self._service:
                return json.dumps({
                    "status": "error",
                    "message": "Google Slides service not initialized. Check authentication."
                })
            
            presentation = {
                'title': title
            }
            presentation = self._service.presentations().create(body=presentation).execute()
            presentation_id = presentation.get('presentationId')
            
            return json.dumps({
                "status": "success",
                "message": f"Presentation '{title}' created successfully",
                "presentation_id": presentation_id,
                "presentation_url": f"https://docs.google.com/presentation/d/{presentation_id}/edit"
            })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to create presentation: {str(e)}"
            })
    
    def _add_slide(self, presentation_id: str, layout: str = "TITLE_AND_BODY") -> str:
        """Add a new slide to the presentation"""
        try:
            if not self._service:
                return json.dumps({
                    "status": "error",
                    "message": "Google Slides service not initialized. Check authentication."
                })
            
            # Get the current presentation
            presentation = self._service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            # Get the slide layout
            layouts = presentation.get('layouts')
            layout_id = None
            for layout_obj in layouts:
                if layout_obj.get('layoutProperties', {}).get('displayName') == layout:
                    layout_id = layout_obj.get('objectId')
                    break
            
            if not layout_id:
                # Use the first available layout
                layout_id = layouts[0].get('objectId')
            
            # Create the slide
            requests = [
                {
                    'createSlide': {
                        'objectId': f'slide_{len(presentation.get("slides", [])) + 1}',
                        'slideLayoutReference': {
                            'predefinedLayout': layout
                        }
                    }
                }
            ]
            
            body = {'requests': requests}
            response = self._service.presentations().batchUpdate(
                presentationId=presentation_id, body=body
            ).execute()
            
            return json.dumps({
                "status": "success",
                "message": f"Slide added with layout '{layout}'",
                "slide_id": response['replies'][0]['createSlide']['objectId']
            })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to add slide: {str(e)}"
            })
    
    def _insert_text(self, presentation_id: str, slide_id: str, text: str, 
                    element_id = None, x: float = 100, y: float = 100) -> str:
        """Insert text into a slide"""
        try:
            if not self._service:
                return json.dumps({
                    "status": "error",
                    "message": "Google Slides service not initialized. Check authentication."
                })
            
            requests = []
            
            if element_id:
                # Insert text into existing element
                requests.append({
                    'insertText': {
                        'objectId': element_id,
                        'text': text
                    }
                })
            else:
                # Create new text box
                requests.append({
                    'createShape': {
                        'objectId': f'textbox_{slide_id}_{len(requests)}',
                        'shapeType': 'RECTANGLE',
                        'elementProperties': {
                            'pageObjectId': slide_id,
                            'size': {
                                'width': {'magnitude': 400, 'unit': 'PT'},
                                'height': {'magnitude': 100, 'unit': 'PT'}
                            },
                            'transform': {
                                'scaleX': 1,
                                'scaleY': 1,
                                'translateX': x,
                                'translateY': y,
                                'unit': 'PT'
                            }
                        }
                    }
                })
                
                # Add text to the shape
                requests.append({
                    'insertText': {
                        'objectId': f'textbox_{slide_id}_{len(requests)-1}',
                        'text': text
                    }
                })
            
            body = {'requests': requests}
            self._service.presentations().batchUpdate(
                presentationId=presentation_id, body=body
            ).execute()
            
            return json.dumps({
                "status": "success",
                "message": f"Text inserted: '{text[:50]}...'"
            })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to insert text: {str(e)}"
            })
    
    def _insert_image(self, presentation_id: str, slide_id: str, 
                     image_url: str, x: float = 100, y: float = 100) -> str:
        """Insert an image into a slide"""
        try:
            if not self._service:
                return json.dumps({
                    "status": "error",
                    "message": "Google Slides service not initialized. Check authentication."
                })
            
            requests = [
                {
                    'createImage': {
                        'objectId': f'image_{slide_id}_0',
                        'url': image_url,
                        'elementProperties': {
                            'pageObjectId': slide_id,
                            'size': {
                                'width': {'magnitude': 300, 'unit': 'PT'},
                                'height': {'magnitude': 200, 'unit': 'PT'}
                            },
                            'transform': {
                                'scaleX': 1,
                                'scaleY': 1,
                                'translateX': x,
                                'translateY': y,
                                'unit': 'PT'
                            }
                        }
                    }
                }
            ]
            
            body = {'requests': requests}
            self._service.presentations().batchUpdate(
                presentationId=presentation_id, body=body
            ).execute()
            
            return json.dumps({
                "status": "success",
                "message": f"Image inserted from URL: {image_url}"
            })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to insert image: {str(e)}"
            })
    
    def _get_presentation(self, presentation_id: str) -> str:
        """Get presentation details"""
        try:
            if not self._service:
                return json.dumps({
                    "status": "error",
                    "message": "Google Slides service not initialized. Check authentication."
                })
            
            presentation = self._service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            slides_info = []
            for slide in presentation.get('slides', []):
                slides_info.append({
                    'slide_id': slide.get('objectId'),
                    'elements': len(slide.get('pageElements', []))
                })
            
            return json.dumps({
                "status": "success",
                "presentation": {
                    "title": presentation.get('properties', {}).get('title'),
                    "presentation_id": presentation_id,
                    "slides_count": len(slides_info),
                    "slides": slides_info
                }
            })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to get presentation: {str(e)}"
            })
    
    def _update_slide(self, presentation_id: str, slide_id: str, 
                     updates: Dict[str, Any]) -> str:
        """Update slide content"""
        try:
            if not self._service:
                return json.dumps({
                    "status": "error",
                    "message": "Google Slides service not initialized. Check authentication."
                })
            
            requests = []
            
            # Process different types of updates
            if 'text' in updates:
                requests.append({
                    'replaceAllText': {
                        'containsText': {
                            'text': updates['text']['find']
                        },
                        'replaceText': updates['text']['replace']
                    }
                })
            
            if 'background' in updates:
                requests.append({
                    'updatePageProperties': {
                        'objectId': slide_id,
                        'pageProperties': {
                            'colorScheme': {
                                'colors': [
                                    {'opaqueColor': {'rgbColor': updates['background']}}
                                ]
                            }
                        },
                        'fields': 'colorScheme.colors'
                    }
                })
            
            if requests:
                body = {'requests': requests}
                self._service.presentations().batchUpdate(
                    presentationId=presentation_id, body=body
                ).execute()
            
            return json.dumps({
                "status": "success",
                "message": "Slide updated successfully"
            })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to update slide: {str(e)}"
            })
    
    def _delete_slide(self, presentation_id: str, slide_id: str) -> str:
        """Delete a slide from the presentation"""
        try:
            if not self._service:
                return json.dumps({
                    "status": "error",
                    "message": "Google Slides service not initialized. Check authentication."
                })
            
            requests = [
                {
                    'deleteObject': {
                        'objectId': slide_id
                    }
                }
            ]
            
            body = {'requests': requests}
            self._service.presentations().batchUpdate(
                presentationId=presentation_id, body=body
            ).execute()
            
            return json.dumps({
                "status": "success",
                "message": f"Slide {slide_id} deleted successfully"
            })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to delete slide: {str(e)}"
            }) 