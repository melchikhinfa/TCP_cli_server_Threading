import asyncio
import logging

logging.basicConfig(level=logging.INFO)

class EchoServerProtocol(asyncio.Protocol):
    def __init__(self):
        super().__init__()
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        peername = transport.get_extra_info('peername')
        logging.info(f'Connection from {peername}')

    def data_received(self, data):
        message = data.decode()
        logging.info(f'Data received: {message.strip()}')
        logging.info('Sending data back')
        self.transport.write(data)

    def connection_lost(self, exc):
        logging.info('Connection lost')

async def main():
    loop = asyncio.get_running_loop()

    server = await loop.create_server(
        lambda: EchoServerProtocol(),
        '127.0.0.1',
        8888)

    logging.info('Serving on {}'.format(server.sockets[0].getsockname()))

    async with server:
        await server.serve_forever()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.info('Server has been stopped')
