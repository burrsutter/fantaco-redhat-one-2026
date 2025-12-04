<!--
Sync Impact Report:
- Version change: 1.0.1 → 1.0.2 (patch update)
- Modified principles: None
- Added sections: None
- Removed sections: None
- Changes:
  * Technology Stack: Containerization base image updated from Eclipse Temurin to Red Hat UBI9
  * Rationale: Enterprise-grade security, Red Hat support, OpenShift compatibility
- Templates requiring updates:
  ✅ plan-template.md (already references Constitution Check)
  ✅ tasks-template.md (already follows TDD principles)
  ✅ spec-template.md (no updates needed)
  ✅ research.md (updated Dockerfile pattern to use UBI9)
  ✅ tasks.md (T005 updated to specify UBI9 images)
- Follow-up TODOs: None
-->

# Customer Master Data API Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

All code MUST be developed following strict Test-Driven Development:
- Contract tests MUST be written first for all API endpoints
- Integration tests MUST be written before implementing business logic
- Tests MUST fail before implementation begins (Red-Green-Refactor cycle)
- No code commits without corresponding tests
- Minimum test coverage: 80% for service layer, 100% for controllers

**Rationale**: TDD ensures correctness, prevents regressions, and serves as living documentation. In a customer data system, data integrity is paramount.

### II. API-First Design

All features MUST start with formal API contract definition:
- OpenAPI 3.0 specification MUST be created before coding
- Contracts MUST be reviewed and approved before implementation
- Breaking changes MUST be explicitly versioned
- All endpoints MUST have complete request/response schemas
- Example data MUST be provided in API documentation

**Rationale**: External systems depend on stable contracts. API-first design prevents integration breakage and facilitates parallel development.

### III. Data Integrity & Validation

All data operations MUST enforce strict validation:
- Bean Validation annotations MUST be applied to all DTOs
- Database constraints MUST mirror application-layer validation
- Customer ID uniqueness MUST be enforced at database level
- Field length limits MUST be validated before database operations
- Validation errors MUST return clear, actionable error messages

**Rationale**: Customer master data is shared across systems. Invalid data propagates errors downstream. Validation at multiple layers (application + database) provides defense in depth.

### IV. Observability & Monitoring

All services MUST be observable in production:
- Structured logging MUST use consistent format (JSON recommended)
- All API endpoints MUST log request/response at INFO level (excluding sensitive data)
- Health checks MUST be exposed via Spring Boot Actuator
- Kubernetes readiness/liveness probes MUST be configured
- Database connection health MUST be monitored

**Rationale**: Production issues require rapid diagnosis. Structured logs enable automated analysis. Health checks prevent cascading failures.

### V. Simplicity & Pragmatism

Design MUST favor simplicity over premature optimization:
- Use Spring Boot defaults unless justified deviation required
- Avoid unnecessary abstractions (repositories extend JpaRepository directly)
- No custom query frameworks unless Spring Data JPA insufficient
- YAGNI principle applies: implement only specified requirements
- Document deviations from Spring Boot conventions

**Rationale**: Maintenance burden grows with complexity. Spring Boot provides battle-tested patterns. Custom solutions require ongoing maintenance.

## Technology Stack

**REQUIRED Stack** (MUST be used for all implementations):
- **Language**: Java 21 or later (LTS versions only)
- **Framework**: Spring Boot 3.x (latest stable minor version)
- **Build Tool**: Maven 3.8+ (Gradle prohibited for consistency)
- **Database**: PostgreSQL 15+ (production), Testcontainers (testing)
- **Testing**: JUnit 5, Spring Boot Test, Testcontainers
- **API Documentation**: Springdoc OpenAPI 2.x
- **Containerization**: Docker with multi-stage builds, Red Hat UBI9 base images (`ubi9/openjdk-21` for build, `ubi9/openjdk-21-runtime` for runtime)
- **Orchestration**: Kubernetes 1.27+ (OpenShift compatible)
- **Package Management**: Helm 3.x for Kubernetes deployments

**RECOMMENDED Libraries** (use unless strong justification for alternatives):
- **Logging**: SLF4J with Logback (Spring Boot default)
- **Validation**: Hibernate Validator (Bean Validation 3.0)
- **HTTP Client**: Spring WebClient (reactive) or RestTemplate (blocking)
- **JSON Processing**: Jackson (Spring Boot default)

**PROHIBITED**:
- Spring XML configuration (annotation-based only)
- H2 database for integration tests (use Testcontainers PostgreSQL)
- Custom ORM frameworks (JPA/Hibernate only)
- Non-standard dependency injection frameworks

**Rationale**: Standardized stack reduces cognitive load, simplifies hiring, and ensures compatibility. PostgreSQL chosen for ACID compliance and full-text search capabilities. Testcontainers ensures test/prod parity. Red Hat UBI9 provides enterprise-grade security updates, Red Hat support, and OpenShift compatibility for hybrid cloud deployments.

## Development Workflow

**Branching Strategy**:
- Feature branches MUST follow pattern: `###-feature-name` (e.g., `001-create-a-new`)
- All work happens on feature branches (no direct commits to main)
- Branch created automatically by `/specify` command

**Code Review**:
- All changes require review before merge
- Constitution compliance MUST be verified
- Tests MUST pass in CI before merge
- Breaking changes require explicit approval

**Testing Gates**:
- Unit tests run on every commit
- Integration tests run before merge
- Contract tests validate API stability
- Performance regression tests for p95 latency targets

**Documentation Requirements**:
- README.md MUST include curl examples for all endpoints
- OpenAPI spec MUST be kept in sync with implementation
- Database schema changes MUST be documented in migration files
- Architecture Decision Records (ADRs) for major design choices

## Governance

**Amendment Process**:
1. Propose amendment via pull request to constitution file
2. Version bump according to semantic versioning:
   - MAJOR: Breaking principle changes (requires team vote)
   - MINOR: New principles or sections added
   - PATCH: Clarifications or wording improvements
3. Update dependent templates (plan, tasks, spec) to align
4. All in-flight features reassessed for compliance

**Compliance Verification**:
- `/plan` command MUST check constitution before Phase 0
- `/plan` command MUST re-check after Phase 1 design
- Code reviews MUST verify adherence to principles
- Violations MUST be documented in Complexity Tracking with justification

**Conflict Resolution**:
- Constitution supersedes all other development practices
- When principles conflict, prioritize in order: I → V (Test-First has highest priority)
- Exceptions require explicit documentation and remediation plan

**Living Document Status**:
- Constitution MUST be reviewed quarterly
- Retrospectives MAY propose amendments
- All developers MUST read constitution before contributing
- CLAUDE.md and agent guidance files derive from this constitution

**Version**: 1.0.1 | **Ratified**: 2025-10-05 | **Last Amended**: 2025-10-05
