# Инструкция по развертыванию Flask-приложения с динамической загрузкой модулей на Ubuntu

Ниже приведена пошаговая инструкция для **последней версии Ubuntu** (например, 24.04 LTS или 22.04 LTS). Мы настроим связку **Gunicorn + Nginx**, а также реализуем структуру проекта, где Flask динамически подключает скрипты из папок (`swap1`, `swap2` и т.д.) на основе URL-параметров.

## 1. Структура проекта

Мы будем использовать следующую структуру директорий. Каждая подпапка (`swap1`, `swap2`...) представляет собой отдельный модуль с логикой от сторонних разработчиков.

```text
/opt/Flask_demo/
├── main.py              # Точка входа Flask
├── wsgi.py              # Точка входа для Gunicorn
├── requirements.txt     # Зависимости
├── venv/                # Виртуальное окружение
├── swap1/               # Модуль 1
│   ├── __init__.py      # Делает папку пакетом Python
│   ├── main.py          # Основной скрипт модуля
│   └── ...              # Другие файлы модуля
├── swap2/               # Модуль 2
│   ├── __init__.py
│   ├── main.py
│   └── ...
└── swap3/               # Модуль 3
    ├── __init__.py
    ├── main.py
    └── ...
```

## 2. Подготовка сервера (Ubuntu)

```bash
sudo apt update
sudo apt update && sudo apt dist-upgrade -y
sudo apt install -y python3-pip python3-venv nginx
```

## 3. Настройка проекта и код приложения

Создайте директорию проекта и виртуальное окружение.

```bash
# mkdir
# cd
python3 -m venv venv

source venv/bin/activate
```
Установите Flask и Gunicorn:

```bash
pip install flask gunicorn
pip freeze > requirements.txt
# #
pip install -r requirements.txt
```


## 5. Настройка Systemd (Gunicorn)

Создайте сервис для автозапуска приложения.

```bash

[Unit]
Description=Gunicorn instance for Flask_demo
After=network.target

[Service]
User=user
Group=www-data
# Путь к папке проекта
WorkingDirectory=/opt/Flask_demo
# Путь к venv внутри проекта
Environment="PATH=/opt/Flask_demo/venv/bin"
Environment=LANG=en_US.UTF-8
Environment=LC_ALL=en_US.UTF-8
Environment=PYTHONUTF8=1
# Вызов gunicorn именно из этого venv
ExecStart=/opt/Flask_demo/venv/bin/gunicorn --workers 3 --bind unix:flask_demo.sock wsgi:app

[Install]
WantedBy=multi-user.target

```

Запустите и включите сервис:

```bash
sudo systemctl start Flask_demo
sudo systemctl enable Flask_demo
sudo systemctl status Flask_demo

sudo systemctl stop Flask_demo
```

## 6. Настройка Nginx

Настройте обратный прокси для передачи запросов к Gunicorn через Unix-сокет.

Создайте конфигурацию сайта:

```bash
sudo nano /etc/nginx/sites-available/Flask_demo
```

Вставьте конфиг:

```nginx


```

Активируйте сайт и перезапустите Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/Flask_demo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

## 7. Настройка прав доступа

Nginx должен иметь доступ к сокету. Мы указали `Group=www-data` в systemd, но также нужно убедиться, что Nginx может попасть в домашнюю директорию пользователя.

Выполните:

```bash
# Предоставляем права на исполнение для домашней директории (безопасно)
sudo chmod 710 /home/user
```

## 8. Финальная проверка

Теперь ваше приложение доступно извне. Попробуйте сделать запрос через браузер или `curl` с внешнего IP:

```bash
 curl 'http://192.168.1.83/run/swap1?name=Test'
```

Если вы увидите JSON-ответ, значит, Flask успешно передал параметры в скрипт `swap1/main.py`, и Nginx вернул результат.
