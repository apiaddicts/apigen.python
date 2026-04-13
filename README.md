# 🐍 Apigen Python ![Python](https://img.shields.io/badge/3.12.2-3670A0?logo=python&logoColor=ffdd54) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)

[![Quality Gate Status](https://sonarqube.cloudappi.net/api/project_badges/measure?project=fastapi-template-python&metric=alert_status&token=sqb_12efbe84dd3f43d5e599aa227caac8086fcfde5b)](https://sonarqube.cloudappi.net/dashboard?id=fastapi-template-python)
[![Coverage](https://sonarqube.cloudappi.net/api/project_badges/measure?project=fastapi-template-python&metric=coverage&token=sqb_12efbe84dd3f43d5e599aa227caac8086fcfde5b)](https://sonarqube.cloudappi.net/dashboard?id=fastapi-template-python)
[![Maintainability Rating](https://sonarqube.cloudappi.net/api/project_badges/measure?project=fastapi-template-python&metric=sqale_rating&token=sqb_12efbe84dd3f43d5e599aa227caac8086fcfde5b)](https://sonarqube.cloudappi.net/dashboard?id=fastapi-template-python)

Project created to transform openapi into functional python archetypes.

# ▶️ Usage

```
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

# 📡 API Endpoint

## `POST /api/v1/generate`

Generates a Python project from an OpenAPI, AsyncAPI, or GraphQL specification file.

### Request (`multipart/form-data`)

| Field              | Type   | Required | Description                                                                                                                                                           |
|--------------------|--------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `file`             | binary | ✅ Yes   | The specification file (OpenAPI, AsyncAPI, or GraphQL).                                                                                                               |
| `fileType`         | string | ✅ Yes   | Type of the specification file. Allowed values: `openapi`, `asyncapi`, `graphql`.                                                                                     |
| `existing_project` | binary | ❌ No    | ZIP file of a previously generated project. When provided, the project is regenerated preserving custom code blocks (marked with `CUSTOM CODE` markers in the source). |

### Response

- **200** — Generated project returned as a `.zip` file (`application/zip`).
- **400** — Invalid request (bad file format, missing fields, etc.).
- **422** — Validation error.

### Example

```bash
# Generate a new project
curl -X POST https://api.cloudappi.com/api/v1/generate \
  -F "file=@openapi.yaml" \
  -F "fileType=openapi" \
  -o project.zip

# Regenerate an existing project (preserves CUSTOM CODE blocks)
curl -X POST https://api.cloudappi.com/api/v1/generate \
  -F "file=@openapi.yaml" \
  -F "fileType=openapi" \
  -F "existing_project=@project.zip" \
  -o project_updated.zip
```

# ⚙️ ️ Environments
file `.env` 

| Variable       | Description  | Example                                      |
|----------------|--------------|----------------------------------------------|
| `DATABASE_URL` | Database Url | postgresql+asyncpg://user:password@host/dbname |

# ▶️ Usage

## Using Alembic to perform database migrations

Please note that when performing migrations, a history table is created in the target database.

!!!Please note that Alembic does not verify existing data in the event of column or table deletions!!!

### Generate migration file

This command generates a file with the SQL queries to perform the migration in the alembic/environment/versions folder.

```
alembic -n [environment] revision --autogenerate -m "Message"
```

### Background check

This command displays the migration history generated.

```
alembic -n [environment] history
```

### Execute migration

With this command, you can run the last migration generated.

```
alembic -n [environment] upgrade head
```

# ▶️Technical procedures

## Create first database

To create the database in development, you must set the ENV environment variable to DEV. This will start the database verification to update the tables in each update.

## Writing in the changelog

Writing the changelog is the responsibility of the developer who implements the functionality. You must update the changelog each time you move to development environments.

## [CHANGELOG](./CHANGELOG.md)

Link to the [CHANGELOG](./CHANGELOG.md) file generated following this [good practices](https://keepachangelog.com/en/1.0.0/).

# 🛠️ Apigen Extensions (`x-apigen`)

As with other Apigen generators (like SpringBoot or .NET), the Python archetype generation process relies heavily on specific OpenAPI/AsyncAPI extensions to map specs to code (models, database tables, handlers, etc.).

Below is the list of supported `x-apigen` extensions tailored to `apigen-python`.

## 1. Project Level configuration
### `x-apigen-project`
Located at the root of the specification. Controls global generation settings.

**Schema:**
```yaml
x-apigen-project:
  name: string
  description: string
  version: string
```
*Note: Unlike the Java generator, Python does not require `java-properties`.*

## 2. Model Persistence Definitions
### `x-apigen-models`
Located at the root of the specification. Defines models that map to SQLAlchemy database tables.

**Schema:**
```yaml
x-apigen-models:
  <model_name>:
    relational-persistence:
      table: string
```
*Note: In `apigen-python`, properties and types are inferred directly from the `#components/schemas` references used in your spec.*

## 3. Path / Channel Bindings
### `x-apigen-binding`
Located under each operation (`paths/<path>/get` or `channels/<channel>/publish`).
Wires the endpoint/channel to a specific logic handler and database model.

**Schema:**
```yaml
paths: # or channels:
  /users: # or user/signedup
    post: # or subscribe:
      x-apigen-binding:
        model: string
        action: string # e.g., 'create', 'update', 'delete'
```

- `model`: Exact name of the schema/model this endpoint manages.
- `action`: Crucial for AsyncAPI where it dictates if a handler will `create`, `update`, or `delete` records.
> **Opt-in Generation:** If `x-apigen-binding` is missing, the generator ignores the operation and creates no logic for it.

## 4. Field Mappings
### `x-apigen-mapping`
Located under property definitions inside `components/schemas`.
Establishes relationships or maps a JSON payload field to a differently named database column/model.

**Schema:**
```yaml
components:
  schemas:
    OrderPayload:
      properties:
        client_id:
          type: integer
          x-apigen-mapping:
            model: Client
            field: id
```
- `model`: Points to a related model (creating a Foreign Key in SQLAlchemy).
- `field`: Specifies which field in the target model this property maps to.
