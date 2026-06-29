# Docker CI Build And GHCR Publish

## Purpose

This workflow verifies that the project Docker image can be built in GitHub Actions and publishes the image to GitHub Container Registry when code is merged to the default branch.

Current scope:

- Build the image from `Dockerfile`.
- Use Docker Buildx.
- Reuse GitHub Actions cache.
- Build pull requests without publishing images.
- Publish images for non-PR runs, including `main`.

This keeps PR validation safe while allowing the default branch to produce deployable images.

## Workflow

The workflow file is:

```text
.github/workflows/docker-build.yml
```

It runs on:

```text
push
pull_request
workflow_dispatch
```

The build step uses:

```text
docker/build-push-action
```

with:

```text
push: ${{ github.event_name != 'pull_request' }}
tags: ${{ steps.meta.outputs.tags }}
labels: ${{ steps.meta.outputs.labels }}
```

## Image Registry

Images are published to:

```text
ghcr.io/buan496/thesis-defense-agent
```

The workflow uses:

```text
docker/login-action
docker/metadata-action
docker/build-push-action
```

The workflow permission required for publishing is:

```yaml
permissions:
  contents: read
  packages: write
```

## Tag Strategy

The workflow generates tags with `docker/metadata-action`:

- `latest` for the default branch.
- `sha-<commit>` for each commit.
- branch tags for branch builds.
- PR tags for pull request builds.

PR tags are only used for local CI metadata. PR builds do not push images.

## Deployment Flow

The intended deployment flow is:

```text
code
-> tests
-> docker build
-> push image to GHCR
-> server pulls image
```

This separates failure types:

- Docker build failure means packaging or dependency issue.
- Registry push failure means authentication or permission issue.
- Server pull failure means runtime or network issue.

## Verify Published Image

After the workflow succeeds on `main`, verify that the image can be pulled:

```powershell
docker pull ghcr.io/buan496/thesis-defense-agent:latest
```

Run the published image locally:

```powershell
docker run --rm `
  -p 18000:8000 `
  ghcr.io/buan496/thesis-defense-agent:latest
```

Check runtime endpoints:

```powershell
curl.exe -fsS http://127.0.0.1:18000/health
curl.exe -fsS http://127.0.0.1:18000/version
curl.exe -fsS http://127.0.0.1:18000/metrics/prometheus
```

Expected result:

```text
/health returns status ok.
/version returns service name and version.
/metrics/prometheus returns Prometheus text metrics.
```

## Next Stage

After this workflow is stable, update server deployment to pull:

```text
ghcr.io/buan496/thesis-defense-agent:latest
```

instead of building the image on the server.
