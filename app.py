from flask import Flask, render_template, request
from decimal import Decimal, ROUND_HALF_UP
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    from_curr = request.form.get('from_currency')
    to_curr = request.form.get('to_currency')
    amount = request.form.get('amount')
    
    if not all([from_curr, to_curr, amount]):
        return render_template('index.html', error='Пожалуйста, заполните все поля')
    
    try:
        amount = float(amount)
        if amount <= 0:
            return render_template('index.html', error='Сумма должна быть положительным числом')
    except ValueError:
        return render_template('index.html', error='Сумма должна быть числом')
    
    converted = None
    error = None

    try:
        url = f'https://api.frankfurter.dev/v2/rate/{from_curr}/{to_curr}'
        response = requests.get(url, timeout=5)
        data = response.json()
        rate = Decimal(str(data['rate']))
        amount = Decimal(str(amount))
        converted = (amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    except KeyError as e:
        error = f"Не удалось получить курс для пары {from_curr}/{to_curr}. Проверьте правильность кодов валют."
        print(f"KeyError: {e}, ответ API: {data}")
    except requests.exceptions.RequestException as e:
        error = "Ошибка соединения с сервисом курсов валют. Попробуйте позже."
        print(f"RequestException: {e}")

    if error:
        return render_template('index.html', error=error)

        # Кэшируем курс на 1 час (простейшая оптимизация)
        # TODO: добавить Redis или просто словарь в памяти
        
    return render_template(
        'index.html',
        from_curr=from_curr,
        to_curr=to_curr,
        amount=amount,
        converted=converted
    )

if __name__ == '__main__':
    app.run(debug=True)
