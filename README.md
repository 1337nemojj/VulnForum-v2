# VulnForum-v2

## Установка и запуск

### Локальный запуск

#### 1. Клон репозитория
```bash
git clone https://github.com/1337nemojj/VulnForum-v2.git
cd VulnForum-v2
```

#### 2. Установите зависимости
```bash
pip install -r requirements.txt
```

#### 3. Инициализируйте базу данных
Запустите следующую команду для создания базы данных SQLite:
```bash
python database.py
```

#### 4. Запустите приложение
```bash
python app.py
```
Приложение будет доступно по адресу `http://127.0.0.1:5000`.

### Запуск через Docker

#### 1. Соберите и запустите контейнер (80 - падает не актуально)
```bash
docker-compose up --build
```

#### 2. Доступ к приложению
Приложение будет доступно по адресу `http://127.0.0.1:80`.

## OWASP Top 10 + Доп уязвимости

### A01:2021 – Broken Access Control
- `/update_profile/<int:user_id>` — Mass Assignment → можно сделать себя админом
- `/internal-admin` — доступ только с localhost, обходится через SSRF

### A02:2021 – Cryptographic Failures
- Нет HTTPS (`ssl_context=None`)
- Пароли хранятся в открытом виде

### A03:2021 – Injection
- SQL Injection:
  - `/login` — классический `admin'--`
  - `/search?q=` — `q=' UNION SELECT username,password,role FROM users--`
  - `/profile/<username>` — инъекция в username
- OS Command Injection:
  - `/ping` → `127.0.0.1 && id` или reverse shell

### A04:2021 – Insecure Design |
- Предсказуемые ID + отсутствие проверки владельца

### A05:2021 – Security Misconfiguration
- `app.secret_key = 'super_secret_key'` (слабый и хардкод)
- `app.debug = True` → утечка стека при ошибках

### A06:2021 – Vulnerable and Outdated Components (КРИТИЧЕСКО!)
- Flask==2.0.1 → CVE-2023-30861 → SSTI → RCE
- Werkzeug==2.2.2 → CVE-2023-25577 (DoS)
- requests==2.26.0 → CVE-2022-0391

### A07:2021 – Identification and Authentication Failures
- Нет хэширования паролей
- Нет защиты от брутфорса

### A08:2021 – Software and Data Integrity Failures
- Отсутствие CSRF-защиты
- Прямое обновление роли без подписи/токена

### A09:2021 – Security Logging and Monitoring Failures
- Полное отсутствие логирования

### A10:2021 – Server-Side Request Forgery (SSRF)
- `/ssrf` — `requests.get(user_url)` без фильтрации
- Обход `/internal-admin` через `http://127.0.0.1/internal-admin`

### Дополнительно
- Stored XSS в форуме (`/forum`) — `<script>alert(document.cookie)</script>`
- Открытый debug-режим + слабый secret → подделка сессий через `flask-unsign`

## Самые быстрые пути к root-shell'у

1. SSTI → RCE (самый простой):

### 5. Уязвимость в админ-панели
- **Описание**: Доступ к маршруту `/admin` возможен без проверки роли, если изменить cookie.
- **Эксплуатация**:
  - Измените cookie `role=user` на `role=admin`.

## Важные замечания
- Этот проект предназначен только для образовательных целей. Не используйте его в продуктивной среде.
- Эксплуатация уязвимостей возможна только в локальной среде.

## Лицензия
Этот проект лицензирован под лицензией MIT.