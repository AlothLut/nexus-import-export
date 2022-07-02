### Набор скриптов для импорта пакетов из nexus в файловую систему и дальнейшей отправкой в новый nexus
API Sonatype Nexus Repository Manager OSS 3.36.0-01

#### Скачивание пакетов c SOURCE_NEXUS_URL( url без / в конце):

- создать и заполнить .env файл, по примеру из .env.dist (все переменные обязательны)
- запустить скрипт import.py
- проверить установленные пакеты в `DOWNLOAD_DIR`

#### Загрузка пакетов в новый nexus TARGET_NEXUS_URL( url без / в конце):

- запустить nuget_export.py

### Для локального теста:
`docker-compose up -d`

login: admin

password:

`docker-compose exec -T nexus bash -c "cat /nexus-data/admin.password ; echo"`

`docker-compose exec -T nexus-src bash -c "cat /nexus-data/admin.password ; echo"`