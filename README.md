# 🤖 Finance Chatbot s MCP

Inteligentný chatbot pre správu faktúr a spracovanie PDF súborov pomocou Model Context Protocol (MCP) a OpenAI GPT.

## 🎯 Čo tento projekt vie robiť

### 📊 **Správa faktúr**
- ✅ Zobrazenie všetkých faktúr z PostgreSQL databázy
- ✅ Vytvorenie nových faktúr s automatickou validáciou
- ✅ Zoradenie faktúr podľa dátumu (najnovšie prvé)
- ✅ Formátovanie sumy v eurách a slovenských dátumoch

### 📄 **Spracovanie PDF súborov**
- ✅ Zoznam PDF súborov pripravených na spracovanie
- ✅ Konverzia PDF → JPG obrázok (všetky stránky do jedného)
- ✅ Automatické premenovanie spracovaných súborov (`raw_` prefix)
- ✅ **AI analýza obrázkov** - GPT-4o vie opísať obsah PDF

### 🧠 **Inteligentné rozpoznávanie**
- ✅ Automatická detekcia kedy použiť nástroje (slovenčina + angličtina)
- ✅ Kontextová komunikácia s pamäťou konverzácie
- ✅ Podpora pre vision modely (analýza obrázkov)
- ✅ Konfigurovateľný system prompt a model

### 🔧 **Technické možnosti**
- ✅ Mikroservisová architektúra (Docker)
- ✅ RESTful API endpointy
- ✅ Detailné logovanie a debugging
- ✅ Automatická inštalácia závislostí
- ✅ Health check monitoring

## 🏗️ Architektúra

```
Terminal Chat (chat.py)
    ↓ HTTP API
Chatbot Service (port 9003) + OpenAI GPT
    ↓ MCP Protocol  
MCP Server (port 9000)
    ↓ HTTP calls
├── Database Service (port 9002) ↔ PostgreSQL
└── File Service (port 9001) ↔ PDF súbory
```

## 🚀 Rýchle spustenie

```bash
# 1. Nastav OpenAI API kľúč
export OPENAI_API_KEY="sk-your-api-key-here"

# 2. Spusti všetky servisy
docker-compose up --build

# 3. Spusti chat (v novom termináli)
python chat.py
```

## 💬 Zoznam použiteľných promptov

### 📊 **Faktúry - Zobrazenie**
```
"Zobraz mi všetky faktúry"
"Aké faktúry máme v databáze?"
"Show me all invoices"
"Zoznam faktúr"
"Aké fatúry máme?" (funguje aj bez diakritiky)
```

### 📊 **Faktúry - Vytvorenie**
```
"Vytvor novú faktúru"
"Vygeneruj a ulož do databázy jednu faktúru s náhodnými údajmi a potom mi ju zobraz"
"Create new invoice"
"Pridaj faktúru pre dodávateľa XYZ na sumu 1500€"
"Chcem vytvoriť faktúru"
```

### 📄 **PDF súbory - Zoznam**
```
"Aké súbory máme na spracovanie?"
"List PDF files"
"Zobraz súbory v zložke"
"Aké subory sa nachadzaju v zlozke?" (funguje aj bez diakritiky)
"Show me files"
```

### 📄 **PDF súbory - Spracovanie**
```
"Spracuj PDF súbor"
"Process next PDF file"
"Konvertuj PDF na obrázok"
"Spracuj ďalší dokument"
"Process file"
"Spracuj prvý súbor v zložke. Ak je to bloček alebo iný dokument len ho spracuj ale ak je to faktúra spracuj ju pozri si jej obsah a obsah zapíš do databázy"
"Spracuj všetky súbory v zložke. Ak je to bloček alebo iný dokument len ho spracuj ale ak je to faktúra spracuj ju pozri si jej obsah a obsah zapíš do databázy"
```

### 🔄 **Správa konverzácie**
```
"/reset" - vymaže históriu konverzácie
"/quit" - ukončí chat
```

### 💭 **Bežná konverzácia**
```
"Ahoj, ako sa máš?"
"Dobrý deň"
"Ďakujem za pomoc"
"Ako funguje tento systém?"
"Hello, how are you?"
```

## 🎛️ Konfigurácia

### Editovanie nastavení
Uprav súbor `mcp_client/config.json`:

```json
{
  "model": "gpt-4o-mini",
  "system_prompt": "You are a helpful assistant..."
}
```

**Dostupné modely:**
- `gpt-4o-mini` - rýchly a lacný (default)
- `gpt-4o` - najlepší pre obrázky a komplexné úlohy
- `gpt-4` - silný model pre text

## 📁 Štruktúra projektu

```
hw3/
├── chat.py                    # 🖥️ Terminal chat klient
├── docker-compose.yml         # 🐳 Docker orchestrácia
├── mcp_client/               # 🤖 AI Chatbot service
│   ├── chatbot.py            # FastAPI server s OpenAI
│   ├── config.json           # Konfigurácia modelu a promptov
│   ├── config_loader.py      # Načítavač konfigurácie
│   └── requirements.txt
├── mcp_server/               # 🔧 MCP server
│   ├── main.py
│   └── tools/                # MCP nástroje
│       ├── get_all_invoices.py
│       ├── create_invoice.py
│       ├── list_files.py
│       └── process_pdf_file.py
├── database_service/         # 💾 Database API
├── file_service/            # 📄 File processing API
└── example_docs/            # 📁 PDF súbory na spracovanie
```

## 🛠️ Dostupné MCP nástroje

| Nástroj | Popis | Parametre |
|---------|-------|-----------|
| `get_all_invoices` | Získa všetky faktúry z databázy | žiadne |
| `create_invoice` | Vytvorí novú faktúru | invoice_number, supplier_name, amount, date_created, due_date |
| `list_files` | Zobrazí PDF súbory na spracovanie | žiadne |
| `process_pdf_file` | Spracuje prvý PDF súbor na obrázok | žiadne |

## 🔍 Príklady použitia

### Príklad 1: Zobrazenie faktúr
```
👤 Vy: Zobraz mi všetky faktúry
🔧 Použité nástroje: get_all_invoices
🤖 Bot: Tu sú všetky faktúry z databázy:

1. **INV-2024-003** - Elektro Slovakia s.r.o.
   Suma: 750.25 € | Splatnosť: 31.8.2024

2. **INV-2024-002** - Office Supply Plus  
   Suma: 358.75 € | Splatnosť: 10.8.2024
   
3. **INV-2024-001** - TechSoft s.r.o.
   Suma: 1250.0 € | Splatnosť: 20.8.2024
```

### Príklad 2: Spracovanie PDF s AI analýzou
```
👤 Vy: Spracuj PDF súbor
🔧 Použité nástroje: process_pdf_file
📸 Nástroj vrátil 1 obrázok
🤖 Bot (gpt-4o): Spracoval som PDF súbor "Scan_LIND202507_006_inter.pdf". 

Na obrázku vidím faktúru s týmito údajmi:
- Dodávateľ: ABC Company s.r.o.
- Číslo faktúry: 2024/0123
- Suma: 1,245.50 €
- Dátum splatnosti: 15.9.2024

Pôvodný súbor bol premenovaný na "raw_Scan_LIND202507_006_inter.pdf".
```

## 🔧 API Endpointy

### Chatbot API (port 9003)
- `GET /health` - Health check
- `GET /` - Info o servise
- `POST /test-api-key` - Test OpenAI API kľúča
- `POST /chat` - Pošle správu chatbotovi
- `POST /reset-history` - Resetuje históriu

### Testovanie API
```bash
# Test chatu
curl -X POST http://localhost:9003/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Zobraz faktúry",
    "api_key": "sk-your-key-here"
  }'
```

## 🐛 Riešenie problémov

### Chatbot nereaguje na slovenské príkazy
- ✅ Skontroluj súbor `mcp_client/config.json`
- ✅ Funkcia `should_use_tools()` podporuje aj slová bez diakritiky
- ✅ Pridaj vlastné kľúčové slová do `chatbot.py`

### MCP nástroje nefungujú
```bash
# Skontroluj MCP server
curl http://localhost:9000/health

# Skontroluj dostupné nástroje
curl -X POST http://localhost:9000/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
```

### Problémy s OpenAI API
- ✅ Skontroluj API kľúč: `echo $OPENAI_API_KEY`
- ✅ Pozri logy: `docker logs name_chatbot_service`
- ✅ Skontroluj kredit na OpenAI účte

### Reštart celého systému
```bash
docker-compose down
docker-compose up --build
```

## 📊 Servis porty

| Servis | Port | Popis |
|--------|------|-------|
| Chatbot API | 9003 | AI chatbot s OpenAI |
| MCP Server | 9000 | Model Context Protocol |
| Database Service | 9002 | Faktúry API |
| File Service | 9001 | PDF spracovanie |
| PostgreSQL | 5432 | Databáza faktúr |

## 🔮 Budúce možnosti

- 🔄 **Webhooks** - automatické spracovanie nových PDF
- 📈 **Analytics** - štatistiky faktúr a výdavkov  
- 🔐 **Multi-user** - viacero používateľov s vlastnými session
- 🌐 **Web UI** - webové rozhranie namiesto terminálu
- 📱 **Mobile API** - podpora pre mobilné aplikácie
- 🤖 **Viac AI modelov** - Claude, Gemini integrácia

---

**Autor:** Peter Luhový  
**Verzia:** 1.0.0  
**Posledná aktualizácia:** Júl 2025

🎉 **Projekt úspešne spája AI, mikroservisy a MCP protokol pre efektívnu správu faktúr a dokumentov!**