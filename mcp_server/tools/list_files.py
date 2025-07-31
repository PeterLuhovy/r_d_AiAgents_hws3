import aiohttp
import json
import mcp.types as types
from typing import List

# URL file servisu v Docker sieti
FILE_SERVICE_URL = "http://file_service:9001"

def list_files_tool() -> types.Tool:
    """
    Definícia nástroja pre získanie zoznamu súborov.
    """
    return types.Tool(
        name="list_files",
        description="Získa zoznam všetkých súborov v zložke na spracovanie (PDF súbory)",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

async def execute_list_files(**arguments) -> List[types.TextContent]:
    """
    Vykoná získanie zoznamu súborov z file servisu.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{FILE_SERVICE_URL}/files") as response:
                if response.status == 200:
                    files_data = await response.json()
                    files = files_data.get("files", [])
                    count = files_data.get("count", 0)
                    
                    # Formátovanie výsledku
                    if count == 0:
                        result = "📁 V zložke nie sú žiadne súbory."
                    else:
                        result = f"📁 Súbory v zložke (celkom: {count}):\n\n"
                        
                        # Rozdelenie súborov podľa typu
                        pdf_files = [f for f in files if f.lower().endswith('.pdf') and not f.startswith('raw_')]
                        raw_files = [f for f in files if f.startswith('raw_')]
                        other_files = [f for f in files if not f.lower().endswith('.pdf')]
                        
                        if pdf_files:
                            result += "🔴 PDF súbory na spracovanie:\n"
                            for file in sorted(pdf_files):
                                result += f"  • {file}\n"
                            result += "\n"
                        else:
                            result += "✅ Žiadne PDF súbory na spracovanie.\n\n"
                        
                        if raw_files:
                            result += "🟢 Spracované PDF súbory (raw_):\n"
                            for file in sorted(raw_files):
                                result += f"  • {file}\n"
                            result += "\n"
                        
                        if other_files:
                            result += "📄 Ostatné súbory:\n"
                            for file in sorted(other_files):
                                result += f"  • {file}\n"
                    
                    return [types.TextContent(type="text", text=result)]
                else:
                    error_text = await response.text()
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Chyba pri získavaní zoznamu súborov: HTTP {response.status}\n{error_text}"
                    )]
                    
    except aiohttp.ClientError as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Chyba pri pripojení k file servisu: {str(e)}"
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Neočakávaná chyba: {str(e)}"
        )]