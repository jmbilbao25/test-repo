---
inclusion: always
---

# AgentOS — global kernel

Paste this file into **Kiro Web → Settings → Cloud configuration** as personal
steering. It then loads in *every* web session, including sessions with no repo
selected — which is the only way to get a brain into a session that clones nothing.

You have a persistent second brain. It is not in this sandbox; it is in a git
repo. Boot it before doing anything else.

## Boot — first tool call of every session, no exceptions

Find an existing copy, otherwise fetch one:

1. `ls -d /projects/sandbox/*/bin/os 2>/dev/null` — if that finds a copy, run
   `bash <that path> boot` and you're done.
2. Otherwise clone the brain as a sidecar and boot it:

```bash
git clone -q --depth 1 -b agentos https://github.com/jmbilbao25/test-repo.git /projects/sandbox/brain \
  && bash /projects/sandbox/brain/bin/os boot
```

Do this before answering anything, even "hi" or "what are we doing?". A session
that skips boot starts amnesiac and will confidently tell the user there is no
prior context — which is a lie, the context is one clone away.

If the clone fails, say so plainly. Do not carry on pretending to have memory.

## Save — last tool call of every session

```bash
bash /projects/sandbox/brain/bin/os save "<one-line summary of this session>"
```

The sandbox is torn down when the task ends. `save` commits and pushes the brain
back to its own remote, so it works from any session regardless of which repo (if
any) that session is bound to. Also run it the moment a durable decision is made,
not only at the end.

## While working

- durable correction with a trigger → `bin/os lesson "When X → do Y. Because Z."`
- something happened → `bin/os log "..."`
- decision with a tradeoff → `bin/os decide "<title>"`, then fill it in
- concept worth linking → `bin/os note "<Title>"`
- recall anything → `bin/os recall "<term>"` (grep, not embeddings)
- multi-session work → `bin/os loop next <name>`; the ledger remembers, you don't

## Sidecar vs. bound repo

- **Working in another repo** — the brain is a sidecar at `/projects/sandbox/brain`
  with its own remote. Cross-project lessons land there. The bound repo's own
  `.kiro/steering/` still applies on top; project rules beat global ones.
- **Working in the brain repo itself** — step 1 finds `bin/os` in the workspace.
  Use that copy, never the sidecar clone, or you'll push to the wrong tree.

## Maintenance

Once the AgentOS PR is merged into `main`, drop `-b agentos` from the clone.
If you move the brain to a dedicated repo, this file is the only place the URL
appears — change it here and every future session follows.
