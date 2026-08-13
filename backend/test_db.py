import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://invoiceiq:invoiceiq@localhost:5432/invoiceiq')
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT id, error_message FROM financial_records WHERE id = '2b1ab28e-6791-4a8c-b1e1-37e50cf6b431'"))
        print([dict(r) for r in res.mappings()])

asyncio.run(main())
