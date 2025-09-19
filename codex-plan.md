# Codex Deployment Plan – Memorial Subdomains

## Overview
This document captures the agreed direction for enabling per-client subdomains under `memorial-4u.com`. The goal is to let every memorial owner reserve a unique host name during onboarding, validate availability, and automatically provision DNS and ingress rules that route traffic through the existing AWS Application Load Balancer (ALB) exposed by the AWS Load Balancer Controller on EKS.

## Implementation Plan
- **Data Model & Configuration**
  - Extend the `memorials` table with fields such as `desired_subdomain`, `provision_status`, `provision_error`, `provisioned_at`, plus optional metadata for Route53 change ids and ingress annotations.
  - Surface configuration for Route53 hosted zone id, ALB DNS name, and feature toggles via `Settings`.

- **API & Domain Flow**
  - Accept a preferred subdomain during memorial onboarding and expose a `GET /subdomains/check?name=` endpoint for real-time availability.
  - Provide a protected `POST /memorials/{id}/subdomain/claim` endpoint that reserves the name, queues provisioning, and prevents duplicate usage by other clients.

- **Subdomain Validation Service**
  - Enforce naming rules (`[a-z0-9-]`, length, no reserved words) and confirm uniqueness both in the database and in Route53 to avoid collisions.
  - Lock the subdomain while provisioning to handle concurrent requests safely.

- **Provisioning Worker**
  - Use an async background task (or existing job system) to create Route53 `A`/`ALIAS` records pointing to the shared ALB via the EKS IAM service account.
  - Patch the Kubernetes ingress managed by the AWS Load Balancer Controller to append a host rule for each new tenant, ensuring idempotency and retry/backoff logic.
  - Update `provision_status` and error fields, and log lifecycle events for observability.

- **Frontend & UX Adjustments**
  - Update onboarding templates/UI to request a subdomain, show availability feedback, and surface provisioning status on the memorial dashboard.
  - Warn users if DNS is still propagating or provisioning failed, with an option to retry.

- **Testing, Logging, and Operations**
  - Add unit tests for validation and orchestration layers using boto3 stubs and fake Kubernetes client.
  - Create a smoke test script for non-production environments that provisions and tears down a sample subdomain.
  - Document rollback steps (delete Route53 record and remove ingress rule) and add structured logging for traceability.

## Infrastructure Assumptions
- Workload runs on Amazon EKS with the AWS Load Balancer Controller already managing ingress resources.
- A wildcard ACM certificate for `*.memorial-4u.com` is attached to the ALB.
- AWS credentials are supplied via an EKS service account/IRSA; application code uses ambient IAM permissions without storing secrets.
- Tenants are restricted to subdomains under `memorial-4u.com` (no custom domains).

## Immediate Next Steps
1. Gather concrete values for the Route53 hosted zone id, ALB DNS name, and ingress resource that needs patching.
2. Decide whether FastAPI background tasks are sufficient or if a dedicated worker queue is required.
3. Define retry thresholds, timeout policy, and operational alerts for provisioning failures.
