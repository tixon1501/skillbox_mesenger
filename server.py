"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None
        self.history = []

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                if login in self.server.logins:
                    self.transport.write(f"Логин {login} занят, попробуйте другой".encode())
                    self.transport.close()
                else:
                    self.login = login
                    self.server.logins.add(self.login)
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.data_history()
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.server.history.append(format_string)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")

    def data_history(self):
        i = -10
        while i < 0:
            if i * -1 <= len(self.server.history):
                string = f"{self.server.history[i]} \r\n"
                self.transport.write(string.encode())
            i += 1


class Server:
    clients: list

    def __init__(self):
        self.clients = []
        self.logins = set()
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
