# Homework Bot

 💻 Бот опрашивает API Яндекс Практикума и получает статус домашних работ, при обновлении статуса анализирует ответ API и отправляет уведомление в Telegram, а так же логирует свою работу.

📁 Это учебный проект разработанный с использованием **Telegram API**, бот логирует свою работу при помощи библеотеки  **logging**


## Порядок установки и запуска приложения на localhost

- Устанока и активация виртуальное окружение
```
# Windows:
python -m venv venv
source venv/Scripts/activate 
# MacOS или Linux:
python3 -m venv venv
source venv/bin/activate 
```
- Установка зависимостей из файла requirements.txt
```
pip install -r requirements.txt
```
- Запуск бота
```
python homework.py
```