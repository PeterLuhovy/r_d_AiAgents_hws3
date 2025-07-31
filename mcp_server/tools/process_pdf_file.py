import aiohttp
import json
import mcp.types as types
from typing import List

# URL file servisu v Docker sieti
FILE_SERVICE_URL = "http://file_service:9001"

def process_pdf_file_tool() -> types.Tool:
    """
    Definícia nástroja pre spracovanie PDF súboru.
    """
    return types.Tool(
        name="process_pdf_file",
        description="Spracuje prvý dostupný PDF súbor - skonvertuje ho na JPG obrázok a premenuje pôvodný súbor s prefixom 'raw_'",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

async def execute_process_pdf_file(**arguments) -> List[types.TextContent]:
    """
    Vykoná spracovanie PDF súboru cez file servis.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{FILE_SERVICE_URL}/process-file") as response:
                if response.status == 200:
                    result_data = await response.json()
                    
                    # Kontrola, či boli nejaké súbory na spracovanie
                    if result_data.get("message") == "no files to process":
                        return [types.TextContent(
                            type="text",
                            text="📄 Žiadne PDF súbory na spracovanie.\n\nVšetky súbory už boli spracované alebo v zložke nie sú žiadne PDF súbory bez 'raw_' prefixu."
                        )]
                    
                    # Úspešné spracovanie
                    original_filename = result_data.get("original_filename", "N/A")
                    raw_filename = result_data.get("raw_filename", "N/A")
                    base64_data = result_data.get("base64", "")
                    format_type = result_data.get("format", "jpeg")
                    
                    success_text = f"✅ PDF súbor úspešne spracovaný!\n\n"
                    success_text += f"📁 Pôvodný súbor: {original_filename}\n"
                    success_text += f"📁 Premenovaný na: {raw_filename}\n"
                    success_text += f"🖼️ Formát obrázka: {format_type.upper()}\n"
                    success_text += f"📊 Veľkosť base64 dát: {len(base64_data):,} znakov\n\n"
                    
                    if base64_data:
                        success_text += f"🔗 Base64 obrázok (prvých 100 znakov):\n"
                        success_text += f"{base64_data[:100]}...\n\n"
                        success_text += f"💡 Tip: Base64 dáta môžete použiť na zobrazenie obrázka alebo ďalšie spracovanie."
                    
                    return [types.TextContent(type="text", text=success_text)]
                    
                else:
                    error_text = await response.text()
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Chyba pri spracovaní PDF súboru: HTTP {response.status}\n{error_text}"
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