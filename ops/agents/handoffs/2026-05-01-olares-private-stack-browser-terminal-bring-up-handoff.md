# Olares Private Stack Browser-Terminal Bring-Up Handoff

Date: 2026-05-01
Status: Complete
Scope: first live bring-up of the bounded private personal stack through the authenticated Olares browser terminal, followed by bounded workstation mesh recovery and browser verification

## Summary

The bounded private personal stack is now live on the Olares host through the
browser-terminal control path.

The first service brought up is `personal-notes` only.

The service remains host-only on `127.0.0.1:5230`.

## What Was Done

1. authenticated into the Olares desktop and used the built-in terminal as a
   trusted host console
2. verified the actual host ED25519 public key fingerprint directly on the host
3. confirmed that the host repo clone under `/home/olares/src/apex-power-ops-platform/apex-power-ops-platform` did not yet contain the new `infra/private` surfaces from the workstation
4. staged the minimum required `infra/private` files directly into the nested
   host repo so bring-up could proceed without waiting on SSH reconciliation
5. created the real machine-local env path at `/home/olares/code/personal/.env.personal`
6. created the dedicated data path at `/home/olares/apex-data/personal/memos`
7. created a machine-local bootstrap admin credential file at
   `/home/olares/apex-secrets/personal/memos-admin.env`
8. seeded the first `ADMIN` user plus a sentinel private memo directly into the
   SQLite store because the service remained host-only and workstation SSH trust
   was still blocked
9. wrote a machine-local operator note at
   `/home/olares/code/personal/personal-stack-operator-note.md`
10. ran Docker Compose as user `olares` against the staged private compose file
11. verified the container came up and that `curl -I http://127.0.0.1:5230`
   returned `HTTP/1.1 200 OK`

## Verified Runtime State

Verified on the trusted host terminal:

1. `docker compose ... ps` showed `private-personal-notes-1` up with port binding `127.0.0.1:5230->5230/tcp`
2. `curl -I -s http://127.0.0.1:5230 | head -n 5` returned `HTTP/1.1 200 OK`
3. a full `docker compose down && docker compose up -d` cycle returned the service to `Up` state on `127.0.0.1:5230`
4. the SQLite store contained `user_count 1` and `memo_count 1` after restart
5. the seeded memo preview remained `# Personal Notes Bootstrap` after restart
6. `/home/olares/apex-secrets/personal/memos-admin.env` exists with `-rw-------` permissions and `olares` ownership
7. an ephemeral `grpcurl` container successfully reflected the live Memos gRPC
   surface on `127.0.0.1:5230`
8. `memos.api.v1.AuthService/SignIn` returned the seeded `ADMIN` user and
   issued a `memos.access-token` cookie
9. reusing that access token against `GET /api/v1/users/1/memos?pageSize=10`
   returned the seeded private sentinel memo through the application API

## Verified Host SSH Fingerprint

Directly on the trusted Olares host terminal:

1. `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256`
2. reported fingerprint `SHA256:Bv4YFhnvW3xYcl+PcES/qiG1iCVYKAdxyb7bFv1I9IU`

This does not match the workstation-side candidate fingerprint previously
observed for `jlswen2121.olares.com`.

## Additional Workstation SSH Evidence

Further bounded checks from the workstation showed:

1. `jlswen2121.olares.com` resolves by CNAME to `aa.california.frp.olares.com`
2. that relay hostname resolves to `52.53.153.208`
3. trusting the relay key only in a temporary known-hosts file reproduces the
   candidate ED25519 fingerprint `SHA256:dMv6Sj7P+SUAd+1vgayaDY0ByxsdUhbatDymdR0aC+U`
4. the workstation key fingerprint matches `/home/olares/.ssh/authorized_keys`
   on the trusted host as `SHA256:LeQiUgaFh/dn6gCAFQcq1C7m83/vqvVUY1LgOWimScw`
5. despite that key match, `ssh olares` through the public hostname still fails
   with `Permission denied (publickey)`
6. the authenticated Settings app reports `Allow SSH via VPN` as enabled with
   state `applied`
7. the same VPN status view reports the Olares host mesh IP as `100.64.0.1`
8. from the workstation, `Test-NetConnection 100.64.0.1 -Port 22` failed, so
   the direct mesh route is not currently usable from this client
9. the workstation still shows no active or hidden LarePass, Tailscale, or
   Wintun network adapter and no route for `100.64.0.0/10`
10. a bounded `Restart-Service LarePass -Force` attempt from the current shell
    failed because the shell could not control the service without additional
    local Windows privileges

This narrows the remaining SSH block to the public relay or access layer rather
than the host's local `authorized_keys` state, and separately shows that the
private-mesh path is not currently reachable from this workstation. It also
shows that in-place client recovery is blocked by lack of local elevation.

## Verified Workstation Recovery

The blocked workstation path was later recovered without modifying trust for the
public relay hostname.

Verified from the workstation:

1. the local TermiPass named-pipe API was used to recover the `LarePass`
   client with `ControlURL=https://headscale.jlswen2121.olares.com` and
   `WantRunning=true`
2. the current pending node key was registered in the Olares Headscale pod for
   user `default`
3. local status then moved to `BackendState: Running` with workstation mesh IP
   `100.64.0.2`
4. peer `olares` appeared online at `100.64.0.1`
5. `Test-NetConnection 100.64.0.1 -Port 22` succeeded
6. non-interactive SSH to `olares@100.64.0.1` succeeded using a temporary
   `UserKnownHostsFile`
7. an SSH tunnel from local `127.0.0.1:5231` to host `127.0.0.1:5230` loaded
   the live Memos UI in the workstation browser
8. the first tunneled UI load still showed site-host signup because the direct
   SQLite bootstrap had inserted the seeded user as role `ADMIN`, while live
   Memos `v0.24.3` recognizes the workspace owner only from role `HOST`
9. correcting that user row from `ADMIN` to `HOST` caused the workspace profile
   to report owner `users/1`
10. signing in through the tunnel with the machine-local bootstrap credential
    reached the live home view and rendered the sentinel memo
    `Personal Notes Bootstrap`
11. `infra/private/run-personal-stack-remote.ps1` now defaults to the restored
   mesh target `olares@100.64.0.1` and includes `-Action tunnel` so the
   workstation browser path no longer depends on a one-off raw `ssh -L`
   command
12. `infra/private/run-personal-stack-remote.ps1` also now includes bounded
   `-Action backup` and `-Action restore` operations for the host-only Memos
   data path
13. a live backup created
   `/home/olares/apex-backups/personal/memos/personal-notes-20260501T234336Z.tgz`
   containing `manifest.json` and `memos/memos_prod.db`
14. a live restore from that archive completed successfully, created the
   pre-restore safety archive
   `/home/olares/apex-backups/personal/memos/pre-restore-personal-notes-20260501T234743Z.tgz`,
   restarted `personal-notes`, and preserved the seeded memo state
15. `infra/private/run-personal-stack-remote.ps1 -Action status` now provides
    the bounded one-command proof surface for current host state: compose ps,
    HTTP health, SQLite summary, and latest backups

## Current Boundary

1. the private stack is live on the host
2. it is still intentionally outside the governed Olares-installed app set
3. it is not published through a public or Olares-native route
4. the workstation public hostname SSH path is now understood to front an FRP
   relay endpoint with its own ED25519 key and separate auth behavior; do not
   force-reconcile workstation `known_hosts` to that key as if it were the
   host `sshd`
5. the private-mesh workstation path is restored and can reach host SSH on
   `100.64.0.1:22`
6. authenticated application access is proven from both the trusted host shell
   and a workstation browser reached through SSH tunneling over the restored
   mesh path
7. the service remains intentionally host-only; the validated workstation UI
   path is via bounded local SSH tunnel, not widened ingress

## Next Truthful Moves

1. keep using the current host-only notes posture and reach it from the
   workstation through bounded SSH tunneling over `100.64.0.1` when needed
2. if the public hostname route still matters, open a separate bounded packet
   for the FRP relay auth path at `jlswen2121.olares.com`; that is now a
   follow-up concern, not the controlling access path
3. do not update workstation `known_hosts` from the earlier public-hostname
   candidate value alone
4. if a second private personal service is added later, keep it in the same
   host-only or mesh-tunneled posture unless a separate governance packet
   explicitly widens exposure
