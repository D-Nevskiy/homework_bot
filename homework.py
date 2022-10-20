from telegram import Bot
from exceptions import SendMessageError, ErrorEndPoint, EmptyList
from logging import StreamHandler, Formatter
from http import HTTPStatus
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
    """Функция отправляет сообщение в Telegram чат."""
    logger.debug(f'Отправляю сообщение в телеграм!')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        raise SendMessageError(f"Ошибка при отправке сообщения: {error}")
    else:
        logger.info(f'Бот отправил сообщение "{message}')


def get_api_answer(current_timestamp):
    """
    Функция делает запрос к эндпоинту API-сервиса.
    В качестве параметра функция получает временную метку.
    """
    logger.debug(f'Отправляю запрос в API Я.Практикума')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    params2 = {'url': ENDPOINT, 'headers': HEADERS, 'params': params}
    response = requests.get(**params2)
    if response.status_code != HTTPStatus.OK:
        raise ErrorEndPoint(f"Сбой в работе программы: Эндпоинт {ENDPOINT} "
                            f"недоступен.Код ответа API:"
                            f" {response.status_code}")
    hw_statuses = response.json()
    logger.debug(f"Успешно получен API. Код ответа API:"
                 f"{response.status_code}")
    return hw_statuses


def check_response(response):
    """
    Функция проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    logger.debug(f'Проверяю ответ API на корректность.')
    if not isinstance(response, dict):
        raise TypeError(f"Ошибка типа в response: {type(response)}")
    if 'homeworks' not in response:
        raise KeyError(f"В словаре нет нужных ключей! {response}")
    homework = response['homeworks']
    if not isinstance(homework, list):
        raise TypeError(f"Тип у 'homework' не list: {type(response)}")
    if len(homework) == 0:
        raise EmptyList("Список домашних работ пуст!")
    last_homework = homework[0]
    logger.debug("Проверка на корректность ответа API пройдена!")
    return last_homework


def parse_status(homework):
    """
    Функция извлекает из дошашней работы название и статус.
    В качестве параметра функция получает только
    один элемент из списка домашних работ.
    """
    logger.debug(f'Извлекаю из ответа API название и статус ДЗ')
    if 'homework_name' not in homework:
        raise KeyError(f"Нет ключа homework_name в ответе API | {homework}")
    if 'status' not in homework:
        raise KeyError(f"Нет ключа status в ответе API | {homework}")
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f"Неизвестный статус работы | {homework_status}")
    verdict = HOMEWORK_STATUSES[homework_status]
    logger.debug("Извлечен из ответа API название и статус ДЗ")
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def parse_current_date(homework):
    """
    Функция извлекает время отправки API ответа.
    В качестве параметра функция получает только один элемент
    из списка домашних работ.
    """
    logger.debug(f'Извлекаю из ответа время отправки API')
    current_date = homework['current_date']
    if 'current_date' not in homework:
        raise KeyError(f"Нет ключа current_date в ответе API | {homework}")
    logger.debug("Извлечен из ответа время отправки API")
    return current_date


def check_tokens():
    logger.debug(f'Проверяю доступность токенов!')
    """Функция проверяет доступность токенов необходимые для работы."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    logger.debug("Все токены валидны!")
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
        current_timestamp = int(time.time())
        send_error_to_bot = False
        while True:
            try:
                response_api = get_api_answer(current_timestamp)
                current_timestamp = parse_current_date(response_api)
                check = check_response(response_api)
                message = parse_status(check)
                logger.info(f"Бот отправил сообщение '{message}'")
                send_message(bot, message)
                send_error_to_bot = False
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
        exit()


if __name__ == '__main__':
    main()
