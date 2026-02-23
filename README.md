# Инструкция по развертыванию Flask-приложения с динамической загрузкой модулей на Ubuntu

Ниже приведена пошаговая инструкция для **последней версии Ubuntu** (например, 24.04 LTS или 22.04 LTS). Мы настроим связку **Gunicorn + Nginx**, а также реализуем структуру проекта, где Flask динамически подключает скрипты из папок (`swap1`, `swap2` и т.д.) на основе URL-параметров.

## 1. Структура проекта

Мы будем использовать следующую структуру директорий. Каждая подпапка (`swap1`, `swap2`...) представляет собой отдельный модуль с логикой от сторонних разработчиков.

```text
/home/user/myproject/
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

Подключитесь к серверу по SSH и выполните обновление системы, установку Python, pip, venv и Nginx.

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv nginx
```

## 3. Настройка проекта и код приложения

Создайте директорию проекта и виртуальное окружение.

```bash
mkdir -p /home/user/myproject
cd /home/user/myproject
python3 -m venv venv
source venv/bin/activate
```

Установите Flask и Gunicorn:

```bash
pip install flask gunicorn
pip freeze > requirements.txt
```



## 5. Настройка Systemd (Gunicorn)

Создайте сервис для автозапуска приложения.

```bash
sudo nano /etc/systemd/system/myproject.service
```

Вставьте следующее содержимое (замените `user` на ваше имя пользователя):

```ini
[Unit]
Description=Gunicorn instance for MyProject
After=network.target

[Service]
User=user
Group=www-data
WorkingDirectory=/home/user/myproject
Environment="PATH=/home/user/myproject/venv/bin"
ExecStart=/home/user/myproject/venv/bin/gunicorn --workers 3 --bind unix:/home/user/myproject/myproject.sock wsgi:app

[Install]
WantedBy=multi-user.target
```

Запустите и включите сервис:

```bash
sudo systemctl start myproject
sudo systemctl enable myproject
sudo systemctl status myproject
```

## 6. Настройка Nginx

Настройте обратный прокси для передачи запросов к Gunicorn через Unix-сокет.

Создайте конфигурацию сайта:

```bash
sudo nano /etc/nginx/sites-available/myproject
```

Вставьте конфиг:

```nginx
server {
    listen 80;
    server_name your_domain_or_IP;

    # Логи
    access_log /var/log/nginx/myproject_access.log;
    error_log /var/log/nginx/myproject_error.log;

    # Статические файлы (если будут)
    location /static/ {
        alias /home/user/myproject/static/;
    }

    # Проксирование запросов к Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/user/myproject/myproject.sock;
    }
}
```

Активируйте сайт и перезапустите Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled/
sudo nginx -t
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
curl http://ваш_ip_сервера/run/swap1/name=Test,count=5
```

Если вы увидите JSON-ответ, значит, Flask успешно передал параметры в скрипт `swap1/main.py`, и Nginx вернул результат.

