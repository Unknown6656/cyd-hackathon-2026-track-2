---
title: Submitting Application
parent: "Track 2: Export Control Advisor"
nav_order: 4
layout: home
permalink: /tracks/track-2/submitting-application/
---

# Submitting Application

{: .summary }
> **In short:** you deploy your own application on your team VM. By the deadline it must be **running and reachable**, serving `/advise` on port **8080**, and you submit its URL through the form along with your GitHub repository and the commit you tagged.

## You deploy it yourself

We do not clone or build your application. You run it on your team VM and keep it running:

```bash
docker compose up -d --build
```

`compose.yaml` already sets `restart: unless-stopped` on both containers, so your deployment comes back by itself after a reboot.

- Serve `/advise` on port **8080**
- Keep the data in **`./corpus`** on the VM, which compose mounts read-only at the same path inside the container, with the layout given in [Data]({% link tracks/track-2/data.md %}#how-to-obtain-the-data).
- Pass the inference variables from `inference.env`, which compose reads through `env_file`. Read these exact variable names, do not hard-code them:

  | Variable | Value |
  |---|---|
  | `OPENAI_BASE_URL` | `https://litellm.hackathon.intlab.ch/v1` |
  | `OPENAI_API_KEY` | provided on Monday morning |
  | `MODEL` | one of the ids in [Available models](/infrastructure/#available-models) |

## Before you submit

Check that:

- [ ] it is **running on your VM** and answers `/advise` on port 8080;
- [ ] it reads the data path and inference variables from the environment (nothing hard-coded to one machine);
- [ ] responses follow the [I/O contract]([Building your Application]({% link tracks/track-2/building-application.md %}#the-endpoint));
- [ ] the data is **not** in your repository and not baked into your image;
- [ ] a top-level **`README.md`** notes anything non-obvious about your build.

## Handing in

By the deploy-and-freeze deadline, submit through the [Google Form](https://forms.gle/ijNGXvWJDfQKQnWPA):

- your **GitHub repository URL**, and
- the **commit hash** you tagged `v1`.

The repository is how we verify and judge what you built; the URL is what gets attacked.

## After the deadline

1. We check that your endpoint answers, and run the acceptance battery against it.
2. Your endpoint URL is published to the other teams for the red-team phase.
3. The VM at the time of deployment is **frozen**, and you may not change it until the Thursday blue-team session.

In that Thursday session you may add guardrails and redeploy. Tag the commit you
finish with as `final` and send us the new hash; the endpoint URL stays the same.

---

Next: [Extensions]({% link tracks/track-2/Extensions.md %}) →
