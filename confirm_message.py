async def send_confirm(bot, user_id: int, slot: str):
    await bot.send_message(
        user_id,
        f"✅ Konsultatsiyangiz tasdiqlandi!\n\n"
        f"⏰ Vaqt: {slot}\n\n"
        f"Konsultatsiya vaqtida tayyor bo'ling. Aloqa uchun: @kaccocii"
    )
