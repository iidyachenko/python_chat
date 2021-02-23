import logging

logger = logging.getLogger('client')
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s ")
file_handler = logging.FileHandler("log/client/client.log", encoding='utf-8')
file_handler .setLevel(logging.INFO)
file_handler .setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

if __name__ == '__main__':
    logger.info('Тестируем логирование')
