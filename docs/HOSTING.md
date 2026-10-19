# Fictional hosted demo

Render uses `deploy/Dockerfile` and `deploy/hosted.py`, branch `claude/venehealth-codebase-review-hop817`, in **Teja#chinnu's workspace**. The demo is at [bring-vene-concept.onrender.com/demo](https://bring-vene-concept.onrender.com/demo), service `srv-dbb1fcmi0phs73b5m49g`, on Render’s Free compute plan ($0 base compute; shared account quotas and cold starts apply). Ten consecutive browser flows passed on the consolidated runtime, each checking private API scoping and an actual sandbox receipt (14–21 seconds per complete scripted tour, including screenshots and cleanup). Automatic deployments are off, so a later push alone does not change the hosted build.

One web service exposes Next.js on Render's PORT. One Python process runs the API, sandbox institutions and the same understanding/administrative workers, with separate database pools for self-HTTP calls. API, office and disposable PostgreSQL listeners bind loopback inside the container. The local live profile retains independent worker processes. The image excludes `.env`, saved databases and evidence. The launcher forces fixture providers and disables the telephone bridge; no provider credentials are needed. Sample text and device speech are explicitly labelled.

The fictional database is ephemeral. It resets with the service filesystem, with a cap of 100 fresh visits per lifetime. Never put real information here.

To take it down, open [this specific demo service](https://dashboard.render.com/web/srv-dbb1fcmi0phs73b5m49g) in the Render dashboard and **Suspend** it, or delete it in Settings. There are no separately provisioned databases or workers to remove. Do not suspend another app or delete the workspace. Check the service's usage page for build/bandwidth charges.

The original four-process hosted layout saturated the 512 MB Free-plan limit and slowed after several tours. The consolidated fixture runner passed ten consecutive tours while using roughly 370 MiB. This is a disposable demo topology, not a production deployment qualification.
