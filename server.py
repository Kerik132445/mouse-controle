import asyncio
import functools
import http.server
import os
import socket
import socketserver
import sys
import threading
import pyautogui
import qrcode
from websockets.server import serve

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

remainder_x = 0.0
remainder_y = 0.0


def run_http():
    port = 8000
    try:
        # Если запущен скомпилированный exe, берем временную папку PyInstaller (_MEIPASS)
        if getattr(sys, 'frozen', False):
            BASE_DIR = getattr(
                sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0]))
            )
        else:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Указываем HTTP-серверу папку с фронтендом напрямую
        Handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=BASE_DIR
        )

        with socketserver.TCPServer(('0.0.0.0', port), Handler) as httpd:
            httpd.serve_forever()

    except Exception:
        pass


async def echo(websocket):
    async for message in websocket:
        if message == 'click':
            pyautogui.click()

        elif message == 'mousedown':
            pyautogui.mouseDown()

        elif message == 'mouseup':
            pyautogui.mouseUp()

        else:
            try:
                dx, dy = map(float, message.split(','))

                global remainder_x
                global remainder_y

                total_x = dx + remainder_x
                total_y = dy + remainder_y

                move_x = int(total_x)
                move_y = int(total_y)

                remainder_x = total_x - move_x
                remainder_y = total_y - move_y

                pyautogui.moveRel(move_x, move_y)
            except ValueError:
                pass


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()

        if ip.startswith('127.') or ip.startswith('172.'):
            ip_list = socket.gethostbyname_ex(socket.gethostname())[2]
            for candidate in ip_list:
                if candidate.startswith('192.168.') or candidate.startswith('10.'):
                    return candidate
        return ip
    except Exception:
        return '127.0.0.1'


async def main():
    local_ip = get_local_ip()

    try:
        # Конфиг создаем рядом с запущенным exe (в обычной папке), а не во временной
        if getattr(sys, 'frozen', False):
            EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
        else:
            EXE_DIR = os.path.dirname(os.path.abspath(__file__))

        CONFIG_FILE = os.path.join(EXE_DIR, 'config.txt')

        if not os.path.exists(CONFIG_FILE):
            url = f'http://{local_ip}:8000'
            img = qrcode.make(url)
            img.show()

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write('configured')
    except Exception as e:
        print(f'Ошибка при обработке QR/конфига: {e}')

    try:
        async with serve(echo, local_ip, 8765):
            await asyncio.get_running_loop().create_future()
    except Exception:
        pass


if __name__ == '__main__':
    threading.Thread(target=run_http, daemon=True).start()
    asyncio.run(main())
