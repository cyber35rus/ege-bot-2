import asyncio
import json
import sys
from pathlib import Path

from models import Question
from services.db import SessionLocal, init_db


async def main(path: str) -> None:
    await init_db()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    async with SessionLocal() as session:
        for item in data:
            session.add(Question(**item))
        await session.commit()
    print(f"Inserted {len(data)} questions")


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "data/questions_sample.json"
    asyncio.run(main(p))
