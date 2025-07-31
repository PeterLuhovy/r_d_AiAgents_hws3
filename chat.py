#!/usr/bin/env python3
"""
Terminal chat client for Finance Chatbot
"""

import subprocess
import sys
import time

def install_requests():
    """Install requests library automatically"""
    print("📦 Inštalujem knižnicu 'requests'...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        print("✅ Knižnica 'requests' bola úspešne nainštalovaná")
        return True
    except subprocess.CalledProcessError:
        print("❌ Nepodarilo sa nainštalovať 'requests'")
        return False

# Auto-install requests if missing
try:
    import requests
except ImportError:
    if not install_requests():
        sys.exit(1)
    import requests

def check_service(name, url):
    """Check if a service is running"""
    print(f"🔍 {name}...", end=" ", flush=True)
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅")
        else:
            print(f"❌ (HTTP {response.status_code})")
            return False
    except requests.exceptions.RequestException:
        print("❌ (Nedostupný)")
        return False
    
    time.sleep(1)
    return True

def check_all_services():
    """Check all required services"""
    print("🔍 Overujem stav servisov...")
    print("-" * 40)
    
    services = [
        ("MCP Server", "http://localhost:9000/health"),
        ("Database Service", "http://localhost:9002/health"), 
        ("File Service", "http://localhost:9001/health"),
        ("Chatbot Service", "http://localhost:9003/health"),
    ]
    
    all_running = True
    for name, url in services:
        if not check_service(name, url):
            all_running = False
    
    print("-" * 40)
    
    if all_running:
        print("🎉 Všetky servisy bežia správne!")
        return True
    else:
        print("⚠️  Niektoré servisy nie sú dostupné.")
        print("   Spustite: docker-compose up --build")
        return False

def get_openai_api_key():
    """Get OpenAI API key from user"""
    print("\n🔑 Pre použitie chatbota potrebujete OpenAI API kľúč.")
    print("   Môžete ho získať na: https://platform.openai.com/api-keys")
    print()
    
    while True:
        api_key = input("📝 Zadajte váš OpenAI API kľúč: ").strip()
        
        if not api_key:
            print("❌ API kľúč nemôže byť prázdny. Skúste znovu.")
            continue
            
        if not api_key.startswith("sk-"):
            print("⚠️  API kľúč by mal začínať 'sk-'. Pokračovať? (y/n): ", end="")
            confirm = input().strip().lower()
            if confirm not in ['y', 'yes', 'ano', 'a']:
                continue
        
        return api_key

def test_openai_api_key(api_key):
    """Test OpenAI API key"""
    print(f"\n🧪 Testujem API kľúč s OpenAI...")
    print("🔍 Overujem pripojenie...", end=" ", flush=True)
    
    try:
        response = requests.post(
            "http://localhost:9003/test-api-key",
            json={"api_key": api_key, "test_message": "Hello, this is a test."},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("valid", False):
                print("✅")
                print(f"🎉 API kľúč je platný! Model: {data.get('model', 'unknown')}")
                return True
            else:
                print("❌")
                print(f"❌ API kľúč nie je platný: {data.get('error', 'Unknown error')}")
                return False
        else:
            print("❌")
            print(f"❌ Chyba testovania: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print("❌")
        print(f"❌ Chyba pripojenia: {str(e)}")
        return False

def send_chat_message(api_key, message, reset_history=False):
    """Send chat message to chatbot"""
    try:
        response = requests.post(
            "http://localhost:9003/chat",
            json={
                "message": message,
                "api_key": api_key,
                "reset_history": reset_history
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", ""), data.get("model_used", "unknown")
        else:
            error_msg = f"Chyba API: HTTP {response.status_code}"
            try:
                error_detail = response.json().get("detail", "")
                if error_detail:
                    error_msg += f" - {error_detail}"
            except:
                pass
            return error_msg, ""
            
    except requests.exceptions.RequestException as e:
        return f"Chyba pripojenia: {str(e)}", ""

def reset_chat_history(api_key):
    """Reset chat history"""
    try:
        response = requests.post(
            "http://localhost:9003/reset-history",
            json={"api_key": api_key},
            timeout=5
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def chat_loop(api_key):
    """Main chat loop"""
    print("\n💬 Chat je pripravený! Môžete začať písať správy.")
    print("📝 Príklady: 'Zobraz mi faktúry', 'Ako sa máš?', 'Aké súbory máme?'")
    print("🔄 Napíšte '/reset' pre vymazanie histórie")
    print("🚪 Napíšte '/quit' pre ukončenie")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n👤 Vy: ").strip()
            
            if not user_input:
                continue
                
            # Special commands
            if user_input.lower() in ['/quit', '/exit']:
                print("👋 Ďakujem za rozhovor! Dovidenia!\n\n")
                break
            
            if user_input.lower() == '/reset':
                if reset_chat_history(api_key):
                    print("🔄 História konverzácie bola vymazaná.")
                else:
                    print("❌ Nepodarilo sa vymazať históriu.")
                continue
            
            # Send message
            print("🤖 Thinking...", end="", flush=True)
            response, model = send_chat_message(api_key, user_input)
            print("\r" + " " * 15 + "\r", end="")  # Clear "Thinking..."
            
            if model:
                print(f"🤖 Bot ({model}): {response}")
            else:
                print(f"❌ {response}")
                
        except KeyboardInterrupt:
            print("\n👋 Dovidenia!\n\n")
            break
        except Exception as e:
            print(f"\n❌ Chyba: {e}\n\n")

def main():
    """Main function"""
    print()
    print()
    print("🚀 Vítame vás v Finance Chatbot terminálovom klientovi!")
    print(".....")
    time.sleep(1)
    print("🤖 Finance Chatbot Terminal Client")
    print("=" * 50)
    time.sleep(1)
    
    # 1. Check services
    if not check_all_services():
        print("\n❌ Systém nie je pripravený. Najprv spustite Docker servisy.")
        print("   Spustite: docker-compose up --build")
        return
    
    # 2. Get API key
    api_key = get_openai_api_key()
    print(f"\n✅ API kľúč prijatý: {api_key[:8]}...{api_key[-4:]}")
    
    # 3. Test API key
    if test_openai_api_key(api_key):
        # 4. Start chat
        chat_loop(api_key)
    else:
        print("\n❌ API kľúč nefunguje. Skontrolujte ho a skúste znovu.")
        print("   Získajte nový na: https://platform.openai.com/api-keys")

if __name__ == "__main__":
    main()