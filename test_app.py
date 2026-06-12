import pytest
from unittest.mock import patch, MagicMock
import requests
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'name="amount"' in response.text
    assert 'name="from_currency"' in response.text
    assert 'name="to_currency"' in response.text
    assert 'type="submit"' in response.text
    assert 'Конвертировать' in response.text
    assert 'Конвертер валют' in response.text

def test_convert_missing_fields(client):
    response = client.post('/convert', data={
        'from_currency': 'USD',
        'to_currency': 'EUR',
        'amount': ''
    })
    assert 'Пожалуйста, заполните все поля' in response.text

def test_convert_invalid_amount(client):
    response = client.post('/convert', data={
        'from_currency': 'USD',
        'to_currency': 'EUR',
        'amount': 'abc'
    })
    assert 'Сумма должна быть числом' in response.text

def test_convert_negative_amount(client):
    response = client.post('/convert', data={
        'from_currency': 'USD',
        'to_currency': 'EUR',
        'amount': '-50'
    })
    assert 'Сумма должна быть положительным числом' in response.text

@patch('app.requests.get')
def test_convert_success(mock_get, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {'rate': 0.85}
    mock_get.return_value = mock_response

    response = client.post('/convert', data={
        'from_currency': 'USD',
        'to_currency': 'EUR',
        'amount': '100'
    })
    assert response.status_code == 200
    assert '85.00' in response.text
    mock_get.assert_called_once_with(
        'https://api.frankfurter.dev/v2/rate/USD/EUR', timeout=5
    )

@patch('app.requests.get')
def test_convert_api_key_error(mock_get, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_get.return_value = mock_response

    response = client.post('/convert', data={
        'from_currency': 'USD',
        'to_currency': 'EUR',
        'amount': '100'
    })
    assert 'Не удалось получить курс для пары' in response.text

@patch('app.requests.get')
def test_convert_request_exception(mock_get, client):
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")

    response = client.post('/convert', data={
        'from_currency': 'USD',
        'to_currency': 'EUR',
        'amount': '100'
    })
    assert 'Ошибка соединения с сервисом курсов валют' in response.text