import logging
from logging import handlers

logger = logging.getLogger('server')
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s ")
file_handler = handlers.TimedRotatingFileHandler("log/Server/server.log", 'D', 1, backupCount=7, encoding='utf-8')
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.WARNING)

if __name__ == '__main__':
    logger.info('Тестируем логирование')
