import asyncio

from server import DbManager
from game_player import play_invaders


async def main():
    dbm = DbManager(
        url="https://canvas-f06e2-default-rtdb.europe-west1.firebasedatabase.app"
    )
    await play_invaders(dbm)


if __name__ == "__main__":
    asyncio.run(main())
