#rm */migrations/0*
python3 ./manage.py makemigrations
python3 ./manage.py migrate
python3 ./manage.py loaddata payment_system/fixtures/currency.json
python3 ./manage.py loaddata payment_system/fixtures/exchange_rate.json
python3 ./manage.py loaddata payment_system/fixtures/wallet.json
#python3 ./manage.py loaddata */fixtures/*
python3 ./manage.py runserver 0.0.0.0:8000
