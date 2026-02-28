from ..ollama_client import check_ollama

def ollama_status():
    return check_ollama()
