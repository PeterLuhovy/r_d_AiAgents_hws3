import mcp.types as types
from typing import List, Any, Dict

# Import všetkých nástrojov s error handling
try:
    from .get_all_invoices import get_all_invoices_tool, execute_get_all_invoices
except ImportError as e:
    print(f"Warning: Could not import get_all_invoices: {e}")
    def get_all_invoices_tool(): return None
    async def execute_get_all_invoices(**args): return []

try:
    from .create_invoice import create_invoice_tool, execute_create_invoice
except ImportError as e:
    print(f"Warning: Could not import create_invoice: {e}")
    def create_invoice_tool(): return None
    async def execute_create_invoice(**args): return []

try:
    from .list_files import list_files_tool, execute_list_files
except ImportError as e:
    print(f"Warning: Could not import list_files: {e}")
    def list_files_tool(): return None
    async def execute_list_files(**args): return []

try:
    from .process_pdf_file import process_pdf_file_tool, execute_process_pdf_file
except ImportError as e:
    print(f"Warning: Could not import process_pdf_file: {e}")
    def process_pdf_file_tool(): return None
    async def execute_process_pdf_file(**args): return []

def get_all_tools() -> List[types.Tool]:
    """
    Vráti zoznam všetkých dostupných nástrojov.
    """
    tools = []
    
    # Pridaj len nástroje, ktoré sa podarilo načítať
    tool = get_all_invoices_tool()
    if tool:
        tools.append(tool)
        
    tool = create_invoice_tool()
    if tool:
        tools.append(tool)
        
    tool = list_files_tool()
    if tool:
        tools.append(tool)
        
    tool = process_pdf_file_tool()
    if tool:
        tools.append(tool)
    
    return tools

async def execute_tool(name: str, **arguments) -> List[types.TextContent]:
    """
    Vykoná špecifický nástroj s poskytnutými argumentmi.
    """
    if name == "get_all_invoices":
        return await execute_get_all_invoices(**arguments)
    elif name == "create_invoice":
        return await execute_create_invoice(**arguments)
    elif name == "list_files":
        return await execute_list_files(**arguments)
    elif name == "process_pdf_file":
        return await execute_process_pdf_file(**arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")