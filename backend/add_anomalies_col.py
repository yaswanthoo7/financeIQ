import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def m():
    e = create_async_engine('postgresql+asyncpg://financeiq:financeiq@localhost:5432/financeiq')
    async with e.begin() as c:
        await c.execute(text('ALTER TABLE financial_records ADD COLUMN anomalies TEXT;'))
    print('Done')

asyncio.run(m())
