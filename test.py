import asyncio
from utils.llm_queries import different_metaphors


async def run_lmql_test():
    result = await different_metaphors("2 spidermen are pointing at each other. Both look the exact same. They are trying to accuse each other of something.")
    print(result)


asyncio.run(run_lmql_test())
