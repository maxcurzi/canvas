import asyncio

from old.server import DbManager
from old.game_player import play_invaders


async def main():
    dbm = DbManager(
        url="https://canvas-f06e2-default-rtdb.europe-west1.firebasedatabase.app"
    )
    await play_invaders(dbm, fps=0.2)


if __name__ == "__main__":
    asyncio.run(main())
