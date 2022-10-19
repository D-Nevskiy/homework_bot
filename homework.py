from telegram import Bot
from logging import StreamHandler, Formatter
import sys
import time
import requests
import os
import logging

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
handler.setFormatter(
    Formatter(fmt='[%(asctime)s: %(levelname)s]: %(message)s'))


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info(f'Бот отправил сообщение "{message}')


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params=params)
        if response.status_code == 200:
            hw_statuses = response.json()
            logger.info(f"Успешно получен API. Код ответа API: "
                        f"{response.status_code}")
            return hw_statuses
        else:
            raise (f"Ошибка! Статус код ответа API: {response.status_code}")
    except Exception:
        raise Exception(f"Сбой в работе программы: Эндпоинт {ENDPOINT} "
                        f"недоступен.Код ответа API: {response.status_code}")


def check_response(response):
    if type(response) is not dict:
        logger.error("В ответе API тип данных не DICT!")
        raise TypeError("В ответе API тип данных не DICT!")
    try:
        list = response['homeworks']
    except KeyError:
        logger.error("Ошибка при запросе к ключу homeworks")
        raise KeyError("Ошибка при запросе к ключу homeworks")
    try:
        homework = list[0]
    except IndexError:
        raise IndexError("Список homeworks пуст")
    return homework


def parse_status(homework):
    if isinstance(homework, dict):
        homework_name = homework['homework_name']
        homework_status = homework['status']
    if 'homework_name' not in homework:
        logger.error("Нет ключа homework_name в ответе API")
        raise KeyError("Нет ключа homework_name в ответе API")
    if 'status' not in homework:
        logger.error("Нет ключа status в ответе API")
        raise KeyError("Нет ключа status в ответе API")
    if homework_status not in HOMEWORK_STATUSES:
        logger.error("Неизвестный статус работы")
        raise KeyError(f"Неизвестный статус работы")
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def parse_current_date(homework):
    current_date = homework['current_date']
    if 'current_date' not in homework:
        logger.error("Нет ключа current_date в ответе API")
        raise KeyError("Нет ключа current_date в ответе API")
    return current_date


def check_tokens():
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    return True


def main():
    """Основная логика работы бота."""
    bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
    current_timestamp = int(time.time())
    send_error_to_bot = False
    if check_tokens() is True:
        while True:
            try:
                response_api = get_api_answer(-1)
                current_timestamp = parse_current_date(response_api)
                check = check_response(response_api)
                message = parse_status(check)
                send_message(bot, message)
                send_error_to_bot = False
                logger.info(f"Бот отправил сообщение '{message}'")
                time.sleep(RETRY_TIME)
            except Exception as error:
                message = f'Сбой в работе программы: "{error}"'
                logger.error(message)
                if send_error_to_bot is False:
                    send_message(bot, message)
                    send_error_to_bot = True
                time.sleep(RETRY_TIME)
            else:
                logger.critical("Токены неверные!")
    else:
        logger.critical("Токены неверные! Программа принудительно остановлена")


if __name__ == '__main__':
    main()
