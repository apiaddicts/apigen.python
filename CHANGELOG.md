# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Endpoint `POST /api/generate` to validate API definition files and return generated ZIP file
- Support for validating GraphQL schemas using `graphql-core` with base64 content encoding
- Unified validator service to route validation requests based on file type
- `ValidationSuccess` and `ValidationFailure` models for type-safe validation responses
- `ErrorResponse` model for standardized API error responses
- Unit tests for GraphQL validator, unified service, and generate endpoint using real files
- Support for returning ZIP files on successful validation via `FileResponse`
- `docs/api_documentation.json` containing the OpenAPI specification for the `/generate` endpoint
- `FileType` enum for better type safety in the API

- Generator router
- Generator service
- Templates Models
- Template parser

### Changed
- Refactored `ValidationResponse` from single model to `Union[ValidationSuccess, ValidationFailure]`
- Updated `GraphQLValidatorService` to parse GraphQL content and return base64 encoded input
- Updated `UnifiedValidatorService` to return file path (ZIP) on success or `ValidationFailure` on error
- Updated `/api/generate` endpoint to return `FileResponse` (ZIP) on success and `JSONResponse` (error) on failure
- Simplified unit tests to use real files from `prueba/` directory instead of mocks
- Refactored generator services to return a mock path (`prueba` directory) instead of generating a ZIP file directly
- Centralized ZIP compression logic in `UnifiedValidatorService` using `ZipService`
- Reorganized `src/infrastructure/services` into `validators` and `generators` directories
- Simplified `generate_router.py` by removing inline documentation in favor of external JSON file

### Removed
- Redundant test directories and files (`tests/generators`, `tests/fixtures`, `tests/base64`, `tests/integration`, `tests/data`, `tests/unit/unified_service_test`)
- Internal zipping logic from individual generator services

- Removed patient xamples

### Fixed
- Fixed `AsyncAPIValidator` logic to strictly enforce the presence of the `asyncapi` key, preventing invalid files (like GraphQL or generic YAML) from being accepted as valid AsyncAPI specs.

### Security
