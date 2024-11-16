from config import CHANNELS


async def check_channel(userId, bot):
    http_prefixes = (
        "https://t.me/",
        "http://t.me/",
        "http://telegram.me/",
        "https://telegram.me/",
    )

    for channel in CHANNELS:
        channel_username = channel
        for prefix in http_prefixes:
            if channel.startswith(prefix):
                channel_username = channel.replace(prefix, "@")
                break
        channel_member = await bot.get_chat_member(channel_username, userId)
        if channel_member.status in ["member", "administrator", "creator"]:
            continue
        else:
            return False
    return True
