# Сервис "Одноразовые секреты"

Сервис для безопасного хранения конфиденциальных данных, которые выдаются только один раз.

## Особенности

- Шифрование всех секретов
- Выдача секрета только один раз
- Кеширование секретов на сервере (10 минут)
- Поддержка времени жизни секретов
- Защита секретов паролем
- Логирование всех действий
- Запрет кеширования на клиенте

## Требования

- Python 3.9+
- PostgreSQL
- Docker и Docker Compose (для контейнеризации)

## Запуск с помощью Docker

```bash
# Клонировать репозиторий
git clone https://github.com/GeraPegov/secrets
cd secrets

# Запустить с помощью Docker Compose
docker-compose up -d
```

Сервис будет доступен по адресу: http://localhost:8000

## Запуск без Docker

```bash
# Клонировать репозиторий
git clone https://github.com/GeraPegov/secrets
cd secrets

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Настроить PostgreSQL
# Создать базу данных и пользователя согласно config.toml

# Запустить сервис
uvicorn programm:app --reload
```

## Конфигурация

Конфигурация может быть задана через переменные окружения или в файле `config.toml`:

- `ENCRYPTION_KEY` - ключ шифрования
- `POSTGRES_HOST` - хост PostgreSQL
- `POSTGRES_PORT` - порт PostgreSQL
- `POSTGRES_DB` - имя базы данных
- `POSTGRES_USER` - пользователь PostgreSQL
- `POSTGRES_PASSWORD` - пароль PostgreSQL

## API

### Создание секрета

```
POST /secret
```

**Параметры запроса:**

- `secret` (string, обязательный) - конфиденциальные данные
- `passphrase` (string, опциональный) - фраза-пароль для дополнительной защиты

**Пример запроса:**

```json
{
  "secret": "доступ_к_конфиденциальным_данным",
  "passphrase": "my_passphrase",
}
```

**Пример ответа:**

```json
{
  "secret_key": 123
}
```

### Получение секрета

```
GET /
```

**Параметры запроса:**

- `secret_key` (int, обязательный) - секретный ключ(id)

**Пример запроса:**

```json
{
  "secret_key": "my_secret_key"
}
```

**Пример ответа:**

```json
{
  "secret": "доступ_к_конфиденциальным_данным"
}
```

### Удаление секрета

```
DELETE /
```

**Пример запроса:**

```json
{
  "secret_key": "my_secret_key"
  "passphrase": "my_passphrase"
}
```

**Пример ответа:**

```json
{
  "status": "secret_deleted"
}
```

## Безопасность

- Все секреты хранятся в зашифрованном виде
- Пароли хешируются с использованием алгоритма PBKDF2-SHA256
- Установлены HTTP-заголовки для запрета кеширования на клиенте
- Секрет выдается только один раз
- Секреты автоматически удаляются по истечении срока действия

## Структура базы данных

### Таблица `secrets_users`

- `id` = выдается как "секретный ключ"
- `secret` = секрет пользователя(шифруется)
- `passphrase` = пароль пользователя(кешируется)
- `first_add` = время первого добавления секрета
- `last_add` = отсчитывает от first_add 60 минут(время жизни секрета)
- `activity_status` = статус просмотра. Изначально False, менятся на True(просмотрено)
- `ip_client` = айпи клиента 
- `show_secret` = время просмотра секрета

### Таблица `logger_secrets`

- `ip_user` = айпи клиента
- `secret_key` = секретный ключ(id из таблицы secret_user)
- `delete_secret` = время удаления секрета
- `add_secret` = время добавления секрета
- `time_reading` = время просмотра секрета

## Тестирование

Проект включает автоматические тесты для проверки всех основных функций API.

### Запуск тестов

```bash
# Установить зависимости для тестирования
pip install -r requirements.txt

# Запустить тесты
pytest tests_programm_test.py -v
```

### Покрытие тестами

Тесты проверяют следующие аспекты:

1. Создание секрета (с различными параметрами)
2. Получение секрета
3. Удаление секрета
4. Проверка кеширования