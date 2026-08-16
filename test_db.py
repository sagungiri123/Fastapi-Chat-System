import asyncio
from app.core.database import engine
from sqlalchemy import text

async def test_connection():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            print('Database connection successful!')
            print(f'Result: {result.scalar()}')
    except Exception as e:
        print(f'Database connection failed: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test_connection())