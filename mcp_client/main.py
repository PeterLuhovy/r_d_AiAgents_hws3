from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import re
import requests
import json
from config_loader import config
from typing import List, Dict
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('chatbot.log')
    ]
)
logger = logging.getLogger(__name__)

def extract_base64_images(text: str) -> tuple[str, list[dict]]:
    """Extract base64 images from text and return cleaned text + image data"""
    images = []
    cleaned_text = text
    
    # Pattern for our MCP format: IMAGE_BASE64:format:base64data
    mcp_pattern = r'IMAGE_BASE64:(\w+):([A-Za-z0-9+/]+={0,2})'
    mcp_matches = re.findall(mcp_pattern, text)
    
    for format_type, base64_data in mcp_matches:
        if len(base64_data) > 100:  # Validate minimum length
            images.append({
                "format": format_type.lower(),
                "data": base64_data
            })
            # Remove the MCP format from text
            pattern_to_remove = f"IMAGE_BASE64:{format_type}:{base64_data}"
            cleaned_text = cleaned_text.replace(pattern_to_remove, "[IMAGE PROCESSED]")
            logger.info(f"📸 Found MCP image: {format_type}, size: {len(base64_data)} chars")
    
    # Fallback: Look for other base64 patterns
    if not images:
        base64_patterns = [
            r'data:image\/([^;]+);base64,([A-Za-z0-9+/]{100,}={0,2})',  # Standard data URL
            r'🔗 Base64 obrázok[^:]*:\s*([A-Za-z0-9+/]{1000,}={0,2})',  # Old MCP format
            r'([A-Za-z0-9+/]{2000,}={0,2})'  # Raw base64 (very long strings)
        ]
        
        for pattern in base64_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                if isinstance(match, tuple):
                    # Standard data URL: (format, base64)
                    format_type, base64_data = match
                else:
                    # Raw base64
                    format_type = "jpeg"  # Default
                    base64_data = match
                
                # Validate it looks like image data
                if len(base64_data) > 1000:
                    # Check for common image format headers in base64
                    if (base64_data.startswith('/9j/') or  # JPEG
                        base64_data.startswith('iVBOR') or  # PNG
                        base64_data.startswith('R0lGOD') or  # GIF
                        base64_data.startswith('UklGR')):   # WebP
                        
                        images.append({
                            "format": format_type,
                            "data": base64_data
                        })
                        # Remove from text
                        cleaned_text = re.sub(re.escape(base64_data), '[IMAGE PROCESSED]', cleaned_text)
                        logger.info(f"📸 Found fallback image: {format_type}, size: {len(base64_data)} chars")
    
    logger.info(f"📸 Total images extracted: {len(images)}")
    return cleaned_text, images

def create_image_message_content(text: str, images: list[dict]) -> list[dict]:
    """Create OpenAI message content with text and images"""
    content = [{"type": "text", "text": text}]
    
    for image in images:
        image_format = image["format"]
        base64_data = image["data"]
        
        # Map format to MIME type
        mime_type = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg", 
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }.get(image_format, "image/jpeg")
        
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_data}",
                "detail": "high"  # Use "high" for better analysis
            }
        })
        
        logger.info(f"📸 Added image to message: {mime_type}, {len(base64_data)} chars")
    
    return content

# Request models
class TestAPIKeyRequest(BaseModel):
    api_key: str
    test_message: str = "Hello, this is a test."

class ChatRequest(BaseModel):
    message: str
    api_key: str
    reset_history: bool = False

class ChatResponse(BaseModel):
    response: str
    model_used: str
    tools_used: List[str] = []

# Global chat history storage (in production use database)
chat_histories: Dict[str, List[Dict[str, str]]] = {}

# MCP Client
class MCPClient:
    def __init__(self):
        self.mcp_url = "http://mcp_server:9000/mcp/"
        self.available_tools = []
        
    async def get_available_tools(self):
        """Get available MCP tools"""
        try:
            mcp_request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
            logger.debug(f"🔧 MCP tools/list request: {json.dumps(mcp_request, indent=2)}")
            
            response = requests.post(
                self.mcp_url,
                json=mcp_request,
                headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
                timeout=10
            )
            
            logger.debug(f"🔧 MCP tools/list response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"🔧 MCP tools/list response: {json.dumps(data, indent=2)}")
                tools = data.get("result", {}).get("tools", [])
                self.available_tools = tools
                logger.info(f"✅ Loaded {len(tools)} MCP tools")
                return tools
            else:
                logger.error(f"❌ MCP tools/list failed: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ MCP connection error: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call MCP tool"""
        try:
            mcp_request = {
                "jsonrpc": "2.0", 
                "id": 2, 
                "method": "tools/call", 
                "params": {"name": tool_name, "arguments": arguments}
            }
            logger.debug(f"🔧 MCP tool call request: {json.dumps(mcp_request, indent=2)}")
            
            response = requests.post(
                self.mcp_url,
                json=mcp_request,
                headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
                timeout=30
            )
            
            logger.debug(f"🔧 MCP tool call response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"🔧 MCP tool call response: {json.dumps(data, indent=2)}")
                result = data.get("result", {})
                content = result.get("content", [])
                
                # Extract text from content and combine all parts
                text_result = ""
                for item in content:
                    if item.get("type") == "text":
                        text_result += item.get("text", "") + "\n"
                
                logger.info(f"✅ MCP tool {tool_name} result length: {len(text_result)} chars")
                logger.debug(f"✅ MCP tool {tool_name} result preview: {text_result[:200]}...")
                return text_result.strip()
            else:
                logger.error(f"❌ MCP tool call failed: HTTP {response.status_code}")
                return f"Tool error: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"❌ MCP tool call failed: {str(e)}")
            return f"Tool call failed: {str(e)}"

# Global MCP client
mcp_client = MCPClient()

# FastAPI app
app = FastAPI(title="Finance Chatbot API", version="1.0.0")

def get_chat_history(session_id: str) -> List[Dict[str, str]]:
    """Get chat history for session"""
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    return chat_histories[session_id]

def add_to_history(session_id: str, role: str, content: str):
    """Add message to chat history"""
    history = get_chat_history(session_id)
    history.append({"role": role, "content": content})
    
    # Keep only last 20 messages (10 exchanges)
    if len(history) > 20:
        chat_histories[session_id] = history[-20:]

def reset_history(session_id: str):
    """Reset chat history for session"""
    chat_histories[session_id] = []
    logger.info(f"🔄 Chat history reset for session: {session_id}")

def should_use_tools(message: str, chat_history: List[Dict[str, str]]) -> bool:
    """Check if message needs MCP tools"""
    message_lower = message.lower().strip()
    
    # Direct tool-related patterns
    invoice_patterns = ["faktúr", "faktur", "fatúr", "fatur", "invoice"]
    file_patterns = ["súbor", "subor", "file", "pdf", "zložk", "zlozk", "folder"]
    action_patterns = ["spracuj", "vytvor", "zoznam", "show", "list", "create", "zobraz", "ukáž", "analyzuj"]
    
    # Check for direct tool-related words
    found_invoice = any(pattern in message_lower for pattern in invoice_patterns)
    found_file = any(pattern in message_lower for pattern in file_patterns)
    found_action = any(pattern in message_lower for pattern in action_patterns)
    
    direct_match = found_invoice or found_file or found_action
    
    # Check for contextual responses (ano/yes after assistant asked)
    contextual_match = False
    if message_lower in ["ano", "yes", "áno", "ok", "hej", "jasne"]:
        # Check if assistant's last message was asking for confirmation
        if chat_history and len(chat_history) > 0:
            last_assistant_message = None
            # Find the last assistant message
            for msg in reversed(chat_history):
                if msg["role"] == "assistant":
                    last_assistant_message = msg["content"].lower()
                    break
            
            if last_assistant_message:
                confirmation_phrases = [
                    "chceš", "chces", "môžem", "mozem", "mám", "mam", 
                    "should i", "shall i", "want me to", "spracova", 
                    "aby som", "previes", "urobil"
                ]
                if any(phrase in last_assistant_message for phrase in confirmation_phrases):
                    contextual_match = True
    
    needs_tools = direct_match or contextual_match
    
    logger.debug(f"🔍 Should use tools for '{message[:30]}...': {needs_tools}")
    logger.debug(f"🔍 Direct: {direct_match} (Invoice: {found_invoice}, File: {found_file}, Action: {found_action})")
    logger.debug(f"🔍 Contextual: {contextual_match}")
    
    return needs_tools

def create_tools_for_openai():
    """Convert MCP tools to OpenAI function format"""
    openai_tools = []
    for tool in mcp_client.available_tools:
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool.get("inputSchema", {"type": "object", "properties": {}})
            }
        }
        openai_tools.append(openai_tool)
    
    logger.debug(f"🔧 Created {len(openai_tools)} OpenAI tools")
    return openai_tools

@app.get("/health")
async def health_check():
    logger.info("🏥 Health check requested")
    return {
        "timestamp": time.time(),
        "status": "healthy", 
        "service": "chatbot_api",
        "version": "1.0.0",
        "model": config.model
    }

@app.get("/")
async def root():
    logger.info("🏠 Root endpoint accessed")
    return {
        "message": "Finance Chatbot API is running",
        "model": config.model,
        "system_prompt_preview": config.system_prompt[:100] + "..."
    }

@app.post("/test-api-key")
async def test_api_key(request: TestAPIKeyRequest):
    """Test OpenAI API key validity using direct HTTP requests"""
    logger.info(f"🧪 Testing API key: {request.api_key[:8]}...{request.api_key[-4:]}")
    logger.info(f"🤖 Using model: {config.model}")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {request.api_key}"
    }
    data = {
        "model": config.model,
        "messages": [{"role": "user", "content": request.test_message}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            test_response = response_data["choices"][0]["message"]["content"]
            logger.info(f"✅ API key valid. Response: {test_response}")
            
            return {
                "valid": True,
                "model": config.model,
                "test_response": test_response,
                "message": "API key is working correctly"
            }
        else:
            logger.error(f"❌ OpenAI error: HTTP {response.status_code}")
            return {
                "valid": False,
                "error": f"OpenAI API error: HTTP {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"❌ Request failed: {str(e)}")
        return {
            "valid": False,
            "error": f"Request failed: {str(e)}"
        }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat with the AI assistant"""
    session_id = request.api_key[-10:]
    logger.info(f"💬 Chat request from session {session_id}: {request.message[:50]}...")
    
    # Reset history if requested
    if request.reset_history:
        reset_history(session_id)
    
    # Get available MCP tools
    tools = await mcp_client.get_available_tools()
    logger.info(f"🔧 Available MCP tools: {len(tools)}")
    
    # Get chat history
    history = get_chat_history(session_id)
    
    # Prepare messages for OpenAI
    messages = [{"role": "system", "content": config.system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": request.message})
    
    # Check if we should use tools
    use_tools = should_use_tools(request.message, history)
    tools_used = []
    
    # Call OpenAI API
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {request.api_key}"
    }
    data = {
        "model": config.model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    # Add tools if needed
    if use_tools and tools:
        data["tools"] = create_tools_for_openai()
        data["tool_choice"] = "auto"
        logger.info("🔧 Added MCP tools to OpenAI request")
    
    try:
        logger.info(f"🤖 Calling OpenAI with {len(messages)} messages...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            message = response_data["choices"][0]["message"]
            
            # Handle tool calls if present
            if message.get("tool_calls"):
                logger.info(f"🔧 OpenAI wants to use {len(message['tool_calls'])} tools")
                
                # Add assistant message with tool calls to conversation
                messages.append({
                    "role": "assistant",
                    "content": message.get("content"),
                    "tool_calls": message["tool_calls"]
                })
                
                # Execute each tool call
                has_images = False
                all_images = []
                
                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    try:
                        tool_args = json.loads(tool_call["function"]["arguments"])
                    except:
                        tool_args = {}
                    
                    logger.info(f"🔧 Calling MCP tool: {tool_name}")
                    tools_used.append(tool_name)
                    
                    # Call MCP tool
                    tool_result = await mcp_client.call_tool(tool_name, tool_args)
                    
                    # Check for base64 images in tool result
                    cleaned_result, images = extract_base64_images(tool_result)
                    
                    if images:
                        logger.info(f"📸 Tool {tool_name} returned {len(images)} images")
                        has_images = True
                        all_images.extend(images)
                        
                        # Add cleaned tool result
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": cleaned_result
                        }
                        messages.append(tool_message)
                    else:
                        # Regular tool result without images
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": tool_result
                        }
                        messages.append(tool_message)
                
                # If we have images, add them to the conversation
                if has_images:
                    image_content = create_image_message_content(
                        "Analyzuj obrázky, ktoré boli spracované z PDF súborov. Povedz mi čo vidíš a aké informácie môžeš extrahovať.",
                        all_images
                    )
                    messages.append({
                        "role": "user",
                        "content": image_content
                    })
                
                # Get final response from OpenAI with tool results
                final_data = data.copy()
                final_data["messages"] = messages
                final_data.pop("tools", None)  # Remove tools from final call
                final_data.pop("tool_choice", None)
                
                # Use vision model if we have images
                if has_images:
                    if "gpt-4o" not in final_data["model"]:
                        final_data["model"] = "gpt-4o"  # Switch to vision-capable model
                        logger.info(f"📸 Switched to {final_data['model']} for image analysis")
                
                final_response = requests.post(url, headers=headers, json=final_data, timeout=60)
                
                if final_response.status_code == 200:
                    final_response_data = final_response.json()
                    ai_response = final_response_data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"❌ Final OpenAI call failed: HTTP {final_response.status_code}")
                    ai_response = "Prepáčte, nastala chyba pri spracovaní výsledkov nástrojov."
            else:
                ai_response = message["content"]
            
            # Add to history
            add_to_history(session_id, "user", request.message)
            add_to_history(session_id, "assistant", ai_response)
            
            logger.info(f"✅ Chat response: {ai_response[:100]}...")
            logger.info(f"🔧 Tools used: {tools_used}")
            
            return ChatResponse(
                response=ai_response,
                model_used=config.model,
                tools_used=tools_used
            )
        else:
            logger.error(f"❌ OpenAI error: HTTP {response.status_code}")
            raise HTTPException(
                status_code=500, 
                detail=f"OpenAI API error: HTTP {response.status_code}"
            )
            
    except Exception as e:
        logger.error(f"❌ Chat request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat request failed: {str(e)}"
        )

@app.post("/reset-history")
async def reset_chat_history(request: dict):
    """Reset chat history for session"""
    api_key = request.get("api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    session_id = api_key[-10:]
    reset_history(session_id)
    return {"message": "Chat history reset successfully"}

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Finance Chatbot API on port 9003...")
    logger.info(f"🤖 Model: {config.model}")
    logger.info(f"📝 System prompt: {config.system_prompt[:100]}...")
    uvicorn.run(app, host="0.0.0.0", port=9003)