import aiohttp
import json
import mcp.types as types
from typing import List

# URL databázového servisu v Docker sieti
DATABASE_SERVICE_URL = "http://database_service:9002"

def create_invoice_tool() -> types.Tool:
    """
    Definícia nástroja pre vytvorenie novej faktúry.
    """
    return types.Tool(
        name="create_invoice",
        description="Vytvorí novú faktúru v databáze. Všetky parametre sú povinné.",
        inputSchema={
            "type": "object",
            "properties": {
                "invoice_number": {
                    "type": "string",
                    "description": "Číslo faktúry (napr. INV-2024-003)"
                },
                "supplier_name": {
                    "type": "string", 
                    "description": "Názov dodávateľa"
                },
                "amount": {
                    "type": "number",
                    "description": "Suma faktúry v eurách (napr. 1250.50)"
                },
                "date_created": {
                    "type": "string",
                    "description": "Dátum vytvorenia faktúry vo formáte YYYY-MM-DD (napr. 2024-07-31)"
                },
                "due_date": {
                    "type": "string", 
                    "description": "Dátum splatnosti faktúry vo formáte YYYY-MM-DD (napr. 2024-08-31)"
                }
            },
            "required": ["invoice_number", "supplier_name", "amount", "date_created", "due_date"]
        }
    )

async def execute_create_invoice(**arguments) -> List[types.TextContent]:
    """
    Vykoná vytvorenie novej faktúry v databázovom servise.
    """
    try:
        # Overenie povinných parametrov
        required_fields = ["invoice_number", "supplier_name", "amount", "date_created", "due_date"]
        missing_fields = [field for field in required_fields if field not in arguments]
        
        if missing_fields:
            return [types.TextContent(
                type="text",
                text=f"Chýbajú povinné parametre: {', '.join(missing_fields)}"
            )]
        
        # Príprava dát pre POST request
        invoice_data = {
            "invoice_number": arguments["invoice_number"],
            "supplier_name": arguments["supplier_name"], 
            "amount": float(arguments["amount"]),
            "date_created": arguments["date_created"],
            "due_date": arguments["due_date"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{DATABASE_SERVICE_URL}/invoices",
                json=invoice_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    success_text = f"✅ Faktúra úspešne vytvorená!\n\n"
                    success_text += f"ID: {result.get('id', 'N/A')}\n"
                    success_text += f"Číslo faktúry: {result.get('invoice_number', 'N/A')}\n"
                    success_text += f"Dodávateľ: {invoice_data['supplier_name']}\n"
                    success_text += f"Suma: {invoice_data['amount']} €\n"
                    success_text += f"Dátum vytvorenia: {invoice_data['date_created']}\n"
                    success_text += f"Dátum splatnosti: {invoice_data['due_date']}\n"
                    
                    return [types.TextContent(type="text", text=success_text)]
                else:
                    error_text = await response.text()
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Chyba pri vytváraní faktúry: HTTP {response.status}\n{error_text}"
                    )]
                    
    except ValueError as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Chyba vo formáte dát: {str(e)}\nSkontrolujte formát dátumov (YYYY-MM-DD) a číselné hodnoty."
        )]
    except aiohttp.ClientError as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Chyba pri pripojení k databázovému servisu: {str(e)}"
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Neočakávaná chyba: {str(e)}"
        )]