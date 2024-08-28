from http import HTTPStatus
import logging
from logging import StreamHandler
import os
import sys
import time
import json
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
    token_names = ''
    counter = 0
    for token_name in tokens.keys():
        if tokens[token_name] is None:
            token_names = token_names + token_name + ';'
            counter += 1
    if counter > 0:
        logger.critical(TokensUnavailableException(token_names).message)
        raise TokensUnavailableException(token_names)


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
        raise error


def get_api_answer(timestamp):
    """Делаем запрос к APi и получаем ответ."""
    from_date = timestamp - TIME_DELTA
    payload = {'from_date': from_date}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            raise Exception
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError as error:
                raise error
    except requests.RequestException('Something wrong') as error:
        raise error


def check_response(response):
    """Проверяем ответ от API на ожидаемый."""
    if not isinstance(response, dict):
        raise TypeError
    if 'code' in response.keys():
        if response['code'] == 'UnknownError':
            raise UnexpectedArgException()
        elif response['code'] == 'not_authenticated':
            raise TokenError()
    elif 'homeworks' in response.keys():
        if not isinstance(response['homeworks'], list):
            raise TypeError
        if not response['homeworks']:
            raise EmptyResponseList
        else:
            return response['homeworks'][0]
    else:
        raise NoHWDict


def parse_status(homework):
    """Соотносим статус с ожидаемыми."""
    global INITIAL_STATUS
    if (
        'homework_name' not in homework.keys()
        or 'status' not in homework.keys()
    ):
        raise NoHWName
    last_hw = homework
    if last_hw['status'] not in HOMEWORK_VERDICTS.keys():
        raise UnexpectedStatusError(last_hw['status'])

    if last_hw['homework_name'] not in INITIAL_STATUS.keys():
        homework_name = last_hw['homework_name']
        verdict = HOMEWORK_VERDICTS[last_hw['status']]
        INITIAL_STATUS = {last_hw['homework_name']: last_hw['status']}
        return f'''Изменился статус проверки работы "{homework_name}".
        {verdict}'''
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

            if response['homework_name'] in INITIAL_STATUS.keys():
                if response['status'] == INITIAL_STATUS[
                    response['homework_name']
                ]:
                    logger.debug(
                        NoUpdatesException(response['status'])
                    )

            status_message = parse_status(response)

            send_message(bot, status_message)

            if api_answer['current_date']:
                timestamp = api_answer['current_date']
            else:
                timestamp = int(time.time())

        except Exception as error:
            error_msg = f'Сбой в работе программы: {error}'
            if isinstance(error, EmptyResponseList):
                logger.debug(error_msg)
                send_message(bot, error_msg)
            elif isinstance(error, apihelper.ApiException):
                pass
            else:
                logger.error(error_msg)
                send_message(bot, error_msg)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
