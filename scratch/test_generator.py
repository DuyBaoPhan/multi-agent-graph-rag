import asyncio
from src.agents.generator import get_generator

async def main():
    gen = get_generator()
    history = [
        {"role": "user", "content": "Cho tôi order 1 ly latte M và 2 Cappuccino size L"},
        {"role": "assistant", "content": "Dạ, em đã thêm 1 ly Latte (M) và 2 Cốc Cappuccino (L) vào giỏ hàng rồi ạ. Tổng bill hiện tại là 170,000đ. Anh/chị có cần thêm gì không ạ?"}
    ]
    raw_data = "Dạ, em đã thêm 1 Bánh Mì Que Gà Cay () vào giỏ hàng rồi ạ. Tổng bill hiện tại là 189,000đ. Anh chị có muốn dùng thêm gì nữa không ạ?"
    user_query = "thêm 1 cái bánh mì que gà cay"
    
    # We will test using LM Studio which the system is currently using
    # because SGLang failed in our previous test.
    res = await gen.generate(raw_data, user_query, history)
    print("Generator output:", res)

asyncio.run(main())
