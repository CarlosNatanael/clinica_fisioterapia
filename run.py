from waitress import serve
from app import app
import webbrowser
from threading import Timer
import socket

# --- LÓGICA PARA PEGAR O IP LOCAL DA MÁQUINA ---
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

HOST_IP = get_ip_address()
PORT = 5000
URL = f"http://{HOST_IP}:{PORT}"

# Função para abrir o navegador com a URL correta
def open_browser():
    webbrowser.open_new(URL)

if __name__ == '__main__':
    print(f" * Servidor iniciado. Acesse em: {URL}")
    
    # Usa um Timer para dar tempo ao servidor de iniciar antes de abrir o navegador
    Timer(1, open_browser).start()
    serve(app, host='0.0.0.0', port=PORT)