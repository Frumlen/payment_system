# Решение: #
+ Django REST Framework - взял его за основу, он очень легкий, позволяет легко
стандартизировать запросы к базе данных и одновременно создавать RESTful WEB API.

+ Postgresql - очень мощный, есть опыт использования в платежной системе. В нашем случае можно было еще использовать Mongo, так как у нас тут куча сдаюлсвязанных данных.

+ Celery - для вынесения фоновых задач, создания транзакций, историй переводов, пополений баланса и т.п. В результате быстрый отклик по HTTP API за счет переноса обработки транзакций с использованием очереди обработки.

+ RabbitMQ - для Celery, почему кролик а не Redis? Он надежнее, отказоустойчивее.

+ Docker - для удобства автоматизации и развертывания.


Вся логика расположена в **payment_system.api.task**
Из таблиц созданы: Currency, Wallet, ExchangeRate, Operation, WalletHistory, Transaction
Подбробно можно связи, индексы и т.д. можно посмотреть в **payment_system.api.models**

Миграции расположены в папке **api/migrations**, при развертывании накатятся сами.

Фикстуры для генерация первичных данных лежат в **payment_system/fixtures/**, при развертывании посредством docker'а - добавятся автоматом.


# Интерфейсы API #
В начале хотел все поместить в swagger, но потом вспомнил, что сильно прилизывать смысла нет и оставил.

**CSRF - отключен.**

Все запросы возвращают ответ с кодом 201(CREATED), 200(OK), если все хорошо,
либо с кодом 400(BAD REQUEST) если запрос не удовлетворяет каким-либо требованиям,
либо 500(INTERNAL SERVER ERROR), если ошибка на сервере. Всегда будет возвращаться валидный json,
чтобы фронт смог отобразить пользователю понятный человеку ответ.


+ Регистрация клиента с указанием его имени, страны, города регистрации, валюты создаваемого кошелька.

**URL:**  /api/client

**Метод:** POST

**ТЕЛО запроса:**
```
{
    "name": "Имя",
    "city": "Город",
    "country": "Страна",
    "currency": "USD", # можно передать pk
}
```

**Результат может быть:**

Успешно: 201
```
{
    "id": 1002,
    "name": "Имя",
    "city": "Casd",
    "country": "Страна",
    "created": "2019-05-05 01:09:45",
    "currency": "USD",
    "balance": 0
}
```

Ошибка валидации: 400
```
{
    "currency": [
        "This field is required."
    ]
}
```

Ошибка на сервере: 500
```
{
    "non_field_errors": [
        "(0, 0): (403) ACCESS_REFUSED - Login was refused using authentication mechanism AMQPLAIN. For details see the broker logfile."
    ]
}
```

+ Зачисление денежных средств на кошелек клиента.

**URL:**  /api/wallet_refill_by_name/Aarav

**Метод:** POST

**ТЕЛО запроса:**

```
{
    "amount": 1000,
}
```

**Результат может быть:**

Успешно: 200
```
{
    "message": "Transaction REFILL created",
    "result": "success"
}
```

Ошибка валидации: 400
```
{
    "amount": [
        "This field is required."
    ]
}
```

Ошибка на сервере: 500
```
{
    "non_field_errors": [
        "(0, 0): (403) ACCESS_REFUSED - Login was refused using authentication mechanism AMQPLAIN. For details see the broker logfile."
    ]
}
```

+ Перевод денежных средств с одного кошелька на другой.

**URL:**  /api/wallet2wallet_by_name/Aarav/Aaden

**Метод:** POST

**ТЕЛО запроса:**
```
{
    "amount": 1000,
    "currency_use": "FROM" или "TO" - в зависимости от того, в какой чьей валюте необходимо зачислить средства.
}
```

**Результат может быть:**

Успешно: 200
```
{
    "message": "Transaction TRANSFER created",
    "result": "success"
}
```
Ошибка валидации: 400
```
{
    "amount": [
        "This field is required."
    ]
}
```
Ошибка на сервере: 500
```
{
    "non_field_errors": [
        "(0, 0): (403) ACCESS_REFUSED - Login was refused using authentication mechanism AMQPLAIN. For details see the broker logfile."
    ]
}
```

+ Загрузка котировки валюты к USD на дату.

**URL:**  /api/exchange_rate

**Метод:** POST

**ТЕЛО запроса:**

```
{
    "currency": 1000,
    "created": "2019-05-04 10:17:33"
    "rate": 10.1
}
```


+ Отчёт.

**URL:**  /api/client_report?name=Aarav&start_date=2010-01-01&end_date=2020-01-01

**Метод:** GET

**Параметры: **
```
name - Имя клиента (!обязательно)
start_date - Начало периода (необязательно)
end_date - Конец периода (необязательно)
export_file_type=csv - Получить отчет в виде CSV
export_file_type=xml - Получить отчет в виде XML


DATE_INPUT_FORMATS = [
    '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M:%S.%f',  # '2006-10-25 14:30:59.000200'
    '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
    '%Y-%m-%d',              # '2006-10-25'
    '%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
    '%m/%d/%Y %H:%M:%S.%f',  # '10/25/2006 14:30:59.000200'
    '%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
    '%m/%d/%Y',              # '10/25/2006'
    '%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
    '%m/%d/%y %H:%M:%S.%f',  # '10/25/06 14:30:59.000200'
    '%m/%d/%y %H:%M',        # '10/25/06 14:30'
    '%m/%d/%y',              # '10/25/06'
]
```

**Результат может быть:**

Успешно: 200
```
[
    {
        "id": 1,
        "oper": 1,
        "wallet_partner": null,
        "wallet_partner_name": null,
        "oper_date": "2019-05-05 09:24:03",
        "amount": 300,
        "oper_currency": "CNY",
        "usd_amount": 36.0
    },
    {
        "id": 2,
        "oper": 2,
        "wallet_partner": null,
        "wallet_partner_name": null,
        "oper_date": "2019-05-05 09:24:20",
        "amount": 300,
        "oper_currency": "CNY",
        "usd_amount": 36.0
    },
    {
        "id": 3,
        "oper": 3,
        "wallet_partner": 1,
        "wallet_partner_name": "Aaden",
        "oper_date": "2019-05-05 09:38:17",
        "amount": 200,
        "oper_currency": "CNY",
        "usd_amount": 24.0
    }
]
```

Ошибка валидации: 400
```
{
    "name": [
        "Wallet not exists."
    ]
}
```

Нет транзакций у пользователя: 400
```
{
    "non_field_errors": [
        "There are no transactions for this wallet."
    ]
}
```






# Развертывание решения #
>>> docker-compose build
>>> docker-compose up
```
Миграции и фикстуры(первоначальные данные) сами загрузятся.

