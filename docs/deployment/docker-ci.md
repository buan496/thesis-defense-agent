# Docker CI Build

## Purpose

This workflow verifies that the project Docker image can be built in GitHub Actions.

Current scope:

- Build the image from `Dockerfile`.
- Use Docker Buildx.
- Reuse GitHub Actions cache.
- Do not push the image to any registry.

This is a build-only quality gate. It checks whether container packaging stays healthy when code changes.

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
push: false
tags: thesis-defense-agent:ci
```

## Why This Comes Before Registry Push

The current learning stage only needs to prove that the image can be built consistently in CI.

Registry publishing should be added later as a separate step:

```text
code
-> tests
-> docker build
-> push image to GHCR
-> server pulls image
```

Keeping build and publish separate makes failures easier to locate:

- Docker build failure means packaging or dependency issue.
- Registry push failure means authentication or permission issue.
- Server pull failure means runtime or network issue.

## Next Stage

After this workflow is stable, add GHCR publishing:

```text
ghcr.io/buan496/thesis-defense-agent:<tag>
```

That stage will require:

- `packages: write` permission.
- GitHub Container Registry authentication.
- Image tags for branch, commit SHA, and release.
- A server deployment command that pulls the published image instead of building locally.
