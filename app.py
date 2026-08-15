import logging
import os
from decimal import Decimal, ROUND_HALF_UP

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
APP_ENV = os.getenv('APP_ENV', 'production')
DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'

CURRENCIES = [
    ('USD', '🇺🇸'), ('EUR', '🇪🇺'), ('GBP', '🇬🇧'), ('RUB', '🇷🇺'),
    ('TRY', '🇹🇷'), ('CNY', '🇨🇳'), ('JPY', '🇯🇵'), ('CHF', '🇨🇭'),
    ('KZT', '🇰🇿'), ('UAH', '🇺🇦'), ('INR', '🇮🇳'), ('AED', '🇦🇪'),
    ('GEL', '🇬🇪'), ('AMD', '🇦🇲'), ('BRL', '🇧🇷'), ('KRW', '🇰🇷'),
]
VALID_CODES = {code for code, _ in CURRENCIES}
MAX_AMOUNT = Decimal('1000000000000')


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


@app.route('/')
def index():
    return render_template('index.html', env=APP_ENV, currencies=CURRENCIES)


@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.svg'))


def perform_conversion(from_curr, to_curr, amount_raw):
    """Validates input and fetches a converted amount. Returns (converted, rate, amount, error)."""
    if not all([from_curr, to_curr, amount_raw]):
        return None, None, amount_raw, 'Пожалуйста, заполните все поля'

    if from_curr not in VALID_CODES or to_curr not in VALID_CODES:
        return None, None, amount_raw, 'Неподдерживаемый код валюты'

    try:
        amount = float(amount_raw)
        if amount <= 0:
            return None, None, amount_raw, 'Сумма должна быть положительным числом'
    except (ValueError, TypeError):
        return None, None, amount_raw, 'Сумма должна быть числом'

    amount_dec = Decimal(str(amount))
    if amount_dec > MAX_AMOUNT:
        return None, None, amount, 'Сумма слишком большая'

    data = None
    try:
        url = f'https://api.frankfurter.dev/v2/rate/{from_curr}/{to_curr}'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        rate = Decimal(str(data['rate']))
        converted = (amount_dec * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return converted, rate, amount, None
    except (KeyError, ValueError) as e:
        logger.warning('Unexpected API response for %s/%s: %s (data=%s)', from_curr, to_curr, e, data)
        error = f'Не удалось получить курс для пары {from_curr}/{to_curr}. Проверьте правильность кодов валют.'
        return None, None, amount, error
    except requests.exceptions.RequestException as e:
        logger.error('Frankfurter API request failed: %s', e)
        return None, None, amount, 'Ошибка соединения с сервисом курсов валют. Попробуйте позже.'


@app.route('/convert', methods=['POST'])
def convert():
    from_curr = request.form.get('from_currency')
    to_curr = request.form.get('to_currency')
    amount_raw = request.form.get('amount')

    converted, rate, amount, error = perform_conversion(from_curr, to_curr, amount_raw)

    return render_template(
        'index.html',
        from_curr=from_curr,
        to_curr=to_curr,
        amount=amount,
        converted=converted,
        rate=rate,
        error=error,
        env=APP_ENV,
        currencies=CURRENCIES,
    )


@app.route('/api/convert', methods=['POST'])
def api_convert():
    from_curr = request.form.get('from_currency')
    to_curr = request.form.get('to_currency')
    amount_raw = request.form.get('amount')

    converted, rate, amount, error = perform_conversion(from_curr, to_curr, amount_raw)

    if error:
        return jsonify(error=error), 400

    return jsonify(
        from_currency=from_curr,
        to_currency=to_curr,
        amount=amount,
        converted=str(converted),
        rate=f'{rate:.4f}',
    )


if __name__ == '__main__':
    app.run(debug=DEBUG)
