import logging
from logging import StreamHandler
import os
import sys
import time
import requests

from dotenv import load_dotenv
from telebot import TeleBot, apihelper
from exceptions import (TokensUnavailableException,
                        UnexpectedStatusError,
                        UnexpectedArgException,
                        TokenError,
                        NoHWDict,
                        NoHWName,
                        NoUpdatesException,
                        EmptyResponseList)
load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
INITIAL_STATUS = {}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
DAYS = 40
TIME_DELTA = DAYS * 24 * 60 * 60

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверка переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for token_name in tokens.keys():
        if tokens[token_name] is None:
            logger.critical(TokensUnavailableException(token_name).message)
            raise TokensUnavailableException(token_name)


def send_message(bot, message):
    """Отправка сообщения пользователю."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.debug('Message was sent successfully.')
    except apihelper.ApiException as error:
        message = f'Сбой в работе программы: {error}'
        logger.error(message)
        return error


def get_api_answer(timestamp):
    """Делаем запрос к APi и получаем ответ."""
    from_date = timestamp
    payload = {'from_date': from_date}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        return error
    if response.status_code != 200:
        raise Exception
    else:
        return response.json()


def check_response(response):
    """Проверяем ответ от API на ожидаемый."""
    if isinstance(response, dict):
        if 'code' in response.keys():
            if response['code'] == 'UnknownError':
                raise UnexpectedArgException()
            elif response['code'] == 'not_authenticated':
                raise TokenError()
        elif 'homeworks' in response.keys():
            if isinstance(response['homeworks'], list):
                if not response['homeworks']:
                    raise EmptyResponseList
                else:
                    return response['homeworks'][0]
            else:
                raise TypeError
        else:
            raise NoHWDict
    else:
        raise TypeError


def parse_status(homework):
    """Соотносим статус с ожидаемыми."""
    global INITIAL_STATUS
    if 'homework_name' not in homework.keys():
        raise NoHWName
    else:
        last_hw = homework
        if last_hw['status'] not in HOMEWORK_VERDICTS.keys():
            raise UnexpectedStatusError(last_hw['status'])

        if last_hw['homework_name'] not in INITIAL_STATUS.keys():
            homework_name = last_hw['homework_name']
            verdict = HOMEWORK_VERDICTS[last_hw['status']]
            INITIAL_STATUS = {last_hw['homework_name']: last_hw['status']}
            return f'''Изменился статус проверки работы "{homework_name}".
            {verdict}'''
        elif last_hw['status'] == INITIAL_STATUS[last_hw['homework_name']]:
            raise NoUpdatesException(last_hw['status'])
        elif last_hw['status'] != INITIAL_STATUS[last_hw['homework_name']]:
            homework_name = last_hw['homework_name']
            verdict = HOMEWORK_VERDICTS[last_hw['status']]
            INITIAL_STATUS = {last_hw['homework_name']: last_hw['status']}
            return f'''Изменился статус проверки работы "{homework_name}".
            {verdict}'''


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:

            api_answer = get_api_answer(timestamp)

            response = check_response(api_answer)

            status_message = parse_status(response)

            send_message(bot, status_message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if isinstance(error, NoUpdatesException):
                logger.debug(message)
                send_message(bot, message)
            elif isinstance(error, EmptyResponseList):
                logger.debug(message)
                send_message(bot, message)
            elif isinstance(error, apihelper.ApiException):
                pass
            else:
                logger.error(message)
                send_message(bot, message)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
