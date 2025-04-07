import asyncio
import logging
from uuid import UUID
from json import dumps
import time

from app.database.utils.service_mgr import start_services, stop_services
from app.logic.accounts import get_tree_from_account, get_all_account_amounts

APP_NAME = "app"
logger = logging.getLogger(APP_NAME)


async def main():
    await start_services(app_name=APP_NAME)

    # before = time.perf_counter()
    # tree = await get_account_tree(
    #     account_id=UUID("2ef59c07-3f18-4a63-9128-e134eccccd2b"),
    #     entity_id=UUID("9556625e-fcba-49bf-967c-1e3409679fcd"),
    # )
    # after = time.perf_counter()
    # print(dumps(tree, indent=2))
    # print(f"Elapsed Time: {after-before:0.1f} s")

    before = time.perf_counter()
    tree = await get_all_account_amounts(
        entity_id=UUID("82ff3356-c67d-4f00-9c55-80b261913ec1"),
    )
    after = time.perf_counter()
    print(dumps(tree, indent=2))
    print(f"Elapsed Time: {after-before:0.1f} s")

    await stop_services()


if __name__ == '__main__':
    asyncio.run(main())
