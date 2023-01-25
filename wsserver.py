import asyncio
import json
import websockets
import numpy as np
from invaders.invaders import Game as SpaceInvaders
from games.interface import CanvasApp
import pathlib
import ssl


class CanvasInvaders(SpaceInvaders, CanvasApp):
    pass


CONNECTIONS = set()
COMMANDS = asyncio.Queue()

# ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# localhost_pem = pathlib.Path(__file__).with_name("localhost.pem")
# print(localhost_pem)
# ssl_context.load_cert_chain(localhost_pem)


async def handle_client(websocket):
    CONNECTIONS.add(websocket)
    while True:
        try:
            message = await websocket.recv()
            # print(f"message:{message}")
            await COMMANDS.put(message)
        except websockets.exceptions.ConnectionClosedOK:
            print("Closed OK")
            break
        except Exception as e:
            print(f"{e}")
            break


async def broadcast_game():
    while True:
        game = CanvasInvaders(framerate=1)
        x_max = game.screen.get_width()
        y_max = game.screen.get_height()
        # last_owners = {0: 0}
        # last_pixels = {0: 0}
        while game._winner() == None:
            game.update()
            fr = np.array(game.frame.convert("P")).flatten().tolist()
            gameframe = fr  # {"frame": fr}
            owners = game.owners_map
            owners_dict = {}  # ["" for _ in range(x_max * y_max)]
            for ((x, y), owner) in owners.items():
                owners_dict[x * x_max + y] = owner
            # pixels_dict = {}
            # for idx in range(len(fr)):
            #     pixels_dict[idx] = fr[idx]

            # owners_dict = last_owners and owners_dict
            # gameframe = last_pixels and pixels_dict
            message_dict = {"pixels": gameframe, "owners": owners_dict}
            # print(message_dict)
            last_owners = owners_dict
            last_pixels = gameframe
            message = json.dumps(message_dict)
            websockets.broadcast(CONNECTIONS, message)

            while True:
                try:
                    command = COMMANDS.get_nowait()
                    command = json.loads(command)
                    game.click_at(x=command["x"], y=command["y"], owner=command["user"])
                except asyncio.QueueEmpty:
                    break
                await asyncio.sleep(0)

            await asyncio.sleep(0)


# async def check_socket_for_message(socket):
#     # while True:
#     print("receiving..")
#     message = await socket.recv()
#     print(f"Received message from socket: {message}")


async def main():
    async with websockets.serve(
        handle_client, "pixels.today", 8765
    ):  # , ssl=ssl_context):
        # await broadcast_game()
        await asyncio.gather(broadcast_game())  # , get_all_messages(CONNECTIONS))


if __name__ == "__main__":
    asyncio.run(main())

"""
To enable secure web sockets (WSS) in your application, you will need to do the following steps:

    Obtain a SSL/TLS certificate: To establish a secure connection, you will need to have a valid SSL/TLS certificate. You can either get a free one from Let's Encrypt or purchase one from a trusted certificate authority (CA).

    Configure your web server: Depending on the web server you are using, you will need to configure it to enable HTTPS. For example, in Apache, you will need to enable the mod_ssl module and configure the virtual host to use your SSL certificate. In Nginx, you will need to enable the ssl module and configure the server block to use your SSL certificate.

    Update your client-side code to use WSS: Instead of connecting to the WS protocol, you will need to update your client-side code to connect to the WSS protocol. For example, instead of connecting to "ws://example.com", you will need to connect to "wss://example.com".

    Update your server-side code to handle WSS: You will need to update your server-side code to handle the WSS protocol. This may involve updating the library you are using to handle web sockets.

    Test your application: Once you have made the changes, it's important to test your application to ensure that everything is working properly and that the connection is secure.

It's also important to keep in mind that WSS provides encryption to WebSockets but it doesn't provide any kind of authentication and authorization, you need to handle that separately.

"""
