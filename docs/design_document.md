# CivitAI Image Analytics Project (by Claude3.5)

## Project Overview
This project aims to analyze factors affecting image ratings on CivitAI by collecting and analyzing image data, generation parameters, and user interactions over time. The system will track reactions, comments, and metadata to identify patterns and correlations between generation parameters and image popularity.

## System Architecture

### Components
1. **Data Collection Service**
   - Python-based API client
   - Scheduled execution via Apache Airflow
   - Docker containerization for consistent deployment

2. **Database Layer**
   - PostgreSQL database
   - Stores historical data and analytics

3. **Infrastructure**
   - Docker Compose for service orchestration
   - Environment configuration management

## Database Schema

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
    username VARCHAR(255)
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

-- Generation parameters
CREATE TABLE generation_parameters (
    id BIGSERIAL PRIMARY KEY,
    image_id BIGINT REFERENCES images(id),
    model VARCHAR(255),
    prompt TEXT,
    negative_prompt TEXT,
    sampler VARCHAR(50),
    cfg_scale FLOAT,
    steps INTEGER,
    seed BIGINT,
    size VARCHAR(20),
    additional_params JSONB
);
```

## Implementation Details

### 1. Data Collection
```python
# Airflow DAG structure
with DAG(
    'civitai_data_collection',
    schedule_interval='0 */4 * * *',  # Every 4 hours
    start_date=datetime(2024, 1, 1),
) as dag:

    collect_new_images = PythonOperator(
        task_id='collect_new_images',
        python_callable=collect_images,
        op_kwargs={'limit': 200, 'sort': 'Newest'}
    )

    update_existing_stats = PythonOperator(
        task_id='update_existing_stats',
        python_callable=update_stats
    )
```

### 2. API Client
The api specification is available at [Public REST API | Civitai | Developer Portal](https://developer.civitai.com/docs/api/public-rest#get-apiv1images)

```python
class CivitAIClient:
    BASE_URL = "https://civitai.com/api/v1"

    def get_images(self, limit=100, sort="Most Reactions", period="Day"):
        endpoint = f"{self.BASE_URL}/images"
        params = {
            "limit": limit,
            "sort": sort,
            "period": period
        }
        return self._make_request("GET", endpoint, params)
```

### 3. Data Processing Pipeline
- Image data collection
- Stats history tracking
- Parameter extraction and normalization
- Database insertion with upsert logic

## Deployment

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: civitai_analytics
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  airflow:
    build: ./airflow
    depends_on:
      - postgres
    environment:
      AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:${AIRFLOW_PASSWORD}@postgres/airflow
    volumes:
      - ./dags:/opt/airflow/dags

volumes:
  postgres_data:
```

## Analysis Capabilities

1. **Time-based Analysis**
   - Track reaction growth over time
   - Identify peak engagement periods

2. **Parameter Analysis**
   - Correlation between generation parameters and popularity
   - Model performance comparison
   - Prompt pattern analysis

3. **User Behavior**
   - Comment sentiment analysis
   - User engagement patterns
   - Content creator success factors

## Future Enhancements

1. **Real-time Analytics**
   - Implement streaming updates for high-engagement images
   - Real-time notification system

2. **Advanced Analysis**
   - Machine learning models for popularity prediction
   - Automated prompt optimization suggestions

3. **API Rate Limiting**
   - Implement exponential backoff
   - Request queueing system

## Monitoring and Maintenance

1. **Health Checks**
   - API availability monitoring
   - Database performance metrics
   - Data collection completeness

2. **Error Handling**
   - Retry mechanism for failed requests
   - Error logging and alerting
   - Data validation and cleanup
