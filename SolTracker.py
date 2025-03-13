import asyncio
import nest_asyncio
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from solana.rpc.async_api import AsyncClient

nest_asyncio.apply()

TELEGRAM_BOT_TOKEN = "put_Your_bOt_tOkEn_HeRe" #make sure you replace this with your bot token....get it from bot daddy lol 
POLLING_INTERVAL = 10  

SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com" #replace with an actual RPC URL because this one is ASS 💀
solana_client = AsyncClient(SOLANA_RPC_URL)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

seen_mints = set()
active_users = set()

TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"  

def get_recent_tokens():
    """Fetches recent SPL token mints from Solana blockchain."""
    try:
        logger.info("Connecting to Solana RPC...")
        response = requests.post(SOLANA_RPC_URL, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getProgramAccounts",
            "params": [
                TOKEN_PROGRAM_ID,
                {"encoding": "jsonParsed"}
            ]
        })
        data = response.json()
        if "result" in data:
            logger.info("Successfully fetched token data from Solana.")
        else:
            logger.warning("No valid response received from Solana.")
        return data.get("result", [])
    except Exception as e:
        logger.error(f"Error fetching recent tokens: {e}")
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user_id = update.message.from_user.id
    active_users.add(user_id)
    await update.message.reply_text(
        "🚀 Solana Token Monitor Started!\n\n"
        "I will notify you whenever a new SPL token is deployed on the Solana blockchain."
    )
    logger.info(f"User {user_id} started the bot.")

async def monitor_solana(application: Application):
    """Monitor Solana blockchain for new token mints."""
    logger.info("Starting Solana token monitor...")
    while True:
        try:
            recent_tokens = get_recent_tokens()
            for token in recent_tokens:
                mint_address = token["pubkey"]
                token_data = token.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                token_name = token_data.get("name", "Unknown")
                token_symbol = token_data.get("symbol", "Unknown")
                tx_hash = token.get("transactionHash", "N/A")

                if mint_address not in seen_mints:
                    seen_mints.add(mint_address)
                    logger.info(f"New SPL Token Minted: {mint_address}")
                    logger.info(f"Token Name: {token_name}")
                    logger.info(f"Token Symbol: {token_symbol}")
                    logger.info(f"Transaction Hash: {tx_hash}")

                    message = (
                        f"🚀 New SPL Token Deployed on Solana!\n\n"
                        f"Mint Address: `{mint_address}`\n"
                        f"Name: `{token_name}`\n"
                        f"Symbol: `{token_symbol}`\n"
                        f"Transaction Hash: `{tx_hash}`"
                    )

                    for user_id in active_users.copy():
                        try:
                            await application.bot.send_message(
                                chat_id=user_id,
                                text=message,
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.error(f"Failed to send message to user {user_id}: {e}")
                            active_users.discard(user_id)  # Remove inactive users
        except Exception as e:
            logger.error(f"Error monitoring Solana: {e}")

        await asyncio.sleep(POLLING_INTERVAL)

async def main():
    """Start the bot and the Solana monitor."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    asyncio.create_task(monitor_solana(application))
    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
