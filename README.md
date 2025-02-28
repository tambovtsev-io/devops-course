# CivitAI Scraper
Проект реализует сбор информации о параметрах генерации популярных изображений из онлайн-галереи генеративного искусства [CivitAI](https://civitai.com/).

Качество генерации изображений сильно зависит от промпта, модели, и заданных параметров. Поэтому анализ удачных примеров может выявить best-practice's для составления промптов для диффузионных моделей и выбора параметров. Впоследствии, это можно использовать для создания LLM-копайлота для генерации изображений.

CivitAI - популярная галерея генеративного искусства. Пользователи выкладывают туда картинки с промптами и использованными параметрами. Для каждой картинки прописываются теги: "anime", "outdoors", "photography", и т.д. Есть возможность ставить реакции и оставлять комментарии.

Идея проекта: каждый день собирать самые залайканные изображения и сохранять в БД для последующего анализа.

Автор: Илья Тамбовцев - https://t.me/ilchos

*Проект в рамках курса Devops.*

## Запуск проекта
Для запуска приложения нужно задать переменные в `.env` и запустить проект через `docker compose`.

Пример `.env`:
```
# Airflow Configs
AIRFLOW_UID=50000
AIRFLOW_GID=0
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=1234

# Postgres Common Configs
POSTGRES_HOST=localhost
POSTGRES_SCHEMA=public

# CivitAI Configs
POSTGRES_USER=civitai_user
POSTGRES_PASSWORD=1234
POSTGRES_PORT=5050
POSTGRES_DB=civitai_analytics
```

1. Запустите контейнеры: `docker compose up`
2. Войдите в AirFlow: `localhost:8080`. Логин: `admin`, Пароль: `1234`
3. Запустите DAG `civitai_etl`
4. Протестировать функционал можно в ноутбуке: [ноутбук с тестами](./notebooks/analyse_images.ipynb)

## Схема БД для хранения изображений
Спецификация API для изображений [по ссылке](https://developer.civitai.com/docs/api/public-rest#get-apiv1images).

Используются 3 таблицы:
1) `images` для хранения картинок данных
2) `generation_parameters` для хранения параметров генерации. Всего доступно много параметров. Но мне нужны не все. Хотя, возможно, в будущем понадобится больше, чем сейчас. Поэтому на всякий случай отдельная таблица
3) `image_stats_history` для хранения информации о динамике реакциий: какие реакции, сколько, и дата сбора.

```sql
-- Images table
CREATE TABLE images (
    id BIGINT PRIMARY KEY,
    url TEXT,
    width INTEGER,
    height INTEGER,
    nsfw BOOLEAN,
    nsfw_level VARCHAR(10),
    created_at TIMESTAMP,
    post_id BIGINT,
    username VARCHAR(255),
    base_model VARCHAR(255),
);

-- Generation parameters
CREATE TABLE generation_parameters (
    id BIGSERIAL PRIMARY KEY,
    image_id BIGINT REFERENCES images(id),
    model VARCHAR(255),
    prompt TEXT,
    negative_prompt TEXT,
    sampler VARCHAR(50),
    scheduler VARCHAR(50),
    cfg_scale FLOAT,
    steps INTEGER,
    seed BIGINT,
    size VARCHAR(20),
    additional_params JSONB
);

-- Image stats history
CREATE TABLE image_stats_history (
    id BIGSERIAL PRIMARY KEY,
    image_id BIGINT REFERENCES images(id),
    cry_count INTEGER,
    laugh_count INTEGER,
    like_count INTEGER,
    heart_count INTEGER,
    comment_count INTEGER,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
