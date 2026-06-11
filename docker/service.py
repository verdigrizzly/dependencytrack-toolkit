import sys

from src.composer import main
import asyncio

if __name__ == "__main__":
    if sys.argv[1:]:
        asyncio.run(main(sys.argv[1]))
    else:
        asyncio.run(main())
