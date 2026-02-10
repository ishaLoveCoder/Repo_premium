# info.py

API_ID = 12345
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_BOT_TOKEN"

MONGO_URI = "mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "star_premium_bot"

# Your premium channel
CHANNEL_ID = -1001234567890
CHANNEL_NAME = "🔥 My Premium Channel"

# Admins
ADMINS = [123456789]

# Premium logs (optional)
PREMIUM_LOGS = -1001234567890  # same channel or another private log channel

# Invite link settings
INVITE_LINK_VALID_SECONDS = 3600  # 1 hour
INVITE_LINK_MEMBER_LIMIT = 1

# ⭐ Stars Plans
# Stars amount : premium time string
STAR_PREMIUM_PLANS = {
    10: "1 day",
    50: "7 days",
    150: "1 month",
    400: "3 months",
}
