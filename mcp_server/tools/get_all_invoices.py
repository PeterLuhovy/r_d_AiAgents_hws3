import aiohttp
import json
import mcp.types as types
from typing import List

# URL databázového servisu v Docker sieti
DATABASE_SERVICE_URL = "http://database_service:9002"

def get_all_invoices_tool() -> types.Tool:
    """
    Definícia nástroja pre získanie všetkých faktúr.
    """
    return types.Tool(
        name="get_all_invoices",
        description="Získa všetky faktúry z databázy zoradené podľa dátumu vytvorenia (najnovšie prvé)",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

async def execute_get_all_invoices(**arguments) -> List[types.TextContent]:
    """
    Vykoná získanie všetkých faktúr z databázového servisu.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATABASE_SERVICE_URL}/invoices") as response:
                if response.status == 200:
                    invoices = await response.json()
                    
                    # Formátovanie výsledku pre lepšiu čitateľnosť
                    result = f"Získané faktúry (celkom: {len(invoices)}):\n\n"
                    
                    for invoice in invoices:
                        result += f"ID: {invoice['id']}\n"
                        result += f"Číslo faktúry: {invoice['invoice_number']}\n"
                        result += f"Dodávateľ: {invoice['supplier_name']}\n"
                        result += f"Suma: {invoice['amount']} €\n"
                        result += f"Dátum vytvorenia: {invoice['date_created']}\n"
                        result += f"Dátum splatnosti: {invoice['due_date']}\n"
                        result += "-" * 50 + "\n"
                    
                    if not invoices:
                        result = "V databáze nie sú žiadne faktúry."
                    
                    return [types.TextContent(type="text", text=result)]
                else:
                    error_text = await response.text()
                    return [types.TextContent(
                        type="text", 
                        text=f"Chyba pri získavaní faktúr: HTTP {response.status}\n{error_text}"
                    )]
                    
    except aiohttp.ClientError as e:
        return [types.TextContent(
            type="text", 
            text=f"Chyba pri pripojení k databázovému servisu: {str(e)}"
        )]
    except Exception as e:
        return [types.TextContent(
            type="text", 
            text=f"Neočakávaná chyba: {str(e)}"
        )]