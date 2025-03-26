import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application

# handlers
from handlers.basic_commands import register_basic_commands
from handlers.music_commands import register_music_commands


# env variables
load_dotenv()

# logging
logging.basicConfig(fromat='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    token = os.getenv('TOKEN')

    if not token:
        logger.error("No token provided. Set it in .env file")
        return
    

    app = Application.builder().token(token).build()

    register_basic_commands(app)
    register_music_commands(app)

    logger.info("Starting bot")
    app.run_polling()

if __name__ == '__main__':
    main()

