# Olares SSH Host-Key Reconciliation

Date: 2026-05-01
Status: Completed bounded trust-recovery note with public relay boundary preserved
Scope: safe reconciliation of the workstation `known_hosts` entries for the Olares host aliases after a reported SSH host-key change

## Purpose

Use this note when the workstation can no longer reach the configured Olares SSH
aliases because OpenSSH reports that the remote host identification has changed.

This note exists to keep SSH trust recovery bounded and explicit.

It does not authorize blind acceptance of a newly presented host key.

## Current Local Symptom

At the time of authoring, the workstation reported a host-key mismatch for the
configured Olares hostname alias `jlswen2121.olares.com` and blocked the remote
private-stack wrapper before any host-side command ran.

The newly presented ED25519 fingerprint seen by the local SSH client was:

`SHA256:dMv6Sj7P+SUAd+1vgayaDY0ByxsdUhbatDymdR0aC+U.`

That value is a candidate only until it is verified through a trusted source.

## Trusted Host Result

Using the authenticated Olares browser terminal as a trusted host console,
running:

`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256`

returned:

`SHA256:Bv4YFhnvW3xYcl+PcES/qiG1iCVYKAdxyb7bFv1I9IU`

This means the workstation-side hostname candidate and the host's own ED25519
public key do not currently match.

Until that discrepancy is explained, do not reconcile workstation
`known_hosts` entries by accepting the hostname candidate alone.

## Additional Workstation Evidence

Further bounded checks from the workstation clarified that the public hostname
is not resolving directly to the Olares host itself:

1. `Resolve-DnsName jlswen2121.olares.com` returned a CNAME of
  `aa.california.frp.olares.com`
2. that relay hostname resolved to `52.53.153.208`
3. capturing the advertised SSH key into a temporary `UserKnownHostsFile`
  produced the same candidate ED25519 fingerprint already seen locally:
  `SHA256:dMv6Sj7P+SUAd+1vgayaDY0ByxsdUhbatDymdR0aC+U`
4. the workstation private key still matches the trusted host
  `/home/olares/.ssh/authorized_keys` fingerprint:
  `SHA256:LeQiUgaFh/dn6gCAFQcq1C7m83/vqvVUY1LgOWimScw`
5. even when the relay key was trusted only in a temporary known-hosts file,
  `ssh olares` still failed with `Permission denied (publickey)`
6. the authenticated Settings app reports `Allow SSH via VPN` as enabled and
  applied for the Olares host
7. the same Settings surface reports the host VPN address as `100.64.0.1`
8. from the workstation, `Test-NetConnection 100.64.0.1 -Port 22` failed and
  the direct mesh address did not answer ping or TCP/22
9. the workstation has `LarePassService` and multiple `LarePass.exe` processes
  running, but Windows shows no active or hidden LarePass, Tailscale, or
  Wintun network adapter and no `100.64.0.0/10` route
10. a bounded local recovery attempt with `Restart-Service LarePass -Force`
   failed because the current shell could not control the service without
   additional Windows privileges

At the current boundary, this means the public hostname SSH path is a separate
relay or access layer from the host's own `sshd`. The remaining workstation SSH
block is no longer just a stale host-key collision; it includes both:

1. a public relay authentication boundary that the trusted host-side
  `authorized_keys` state does not by itself satisfy
2. a missing or nonfunctional private-mesh route from the workstation to the
  host VPN address `100.64.0.1`
3. a local Windows elevation boundary that prevents restarting the LarePass
  service from the current shell to attempt tunnel recovery in place

## Resolved Outcome On 2026-05-01

Further bounded recovery from the workstation succeeded without changing trust
for the public relay hostname.

Verified results:

1. the Windows `LarePass` client was recovered by driving the local TermiPass
  named-pipe API directly, re-seeding `ControlURL` as
  `https://headscale.jlswen2121.olares.com`, and setting `WantRunning=true`
2. the current pending node key was then registered in the Olares Headscale pod
  for user `default`
3. local status moved to `BackendState: Running` with workstation mesh IP
  `100.64.0.2`
4. the recovered client reported peer `olares` online at `100.64.0.1`
5. `Test-NetConnection 100.64.0.1 -Port 22` then succeeded from the workstation
6. non-interactive SSH to `olares@100.64.0.1` succeeded using a temporary
  `UserKnownHostsFile`

This resolves the private-mesh SSH path.

It does not change the earlier public-hostname conclusion: `jlswen2121.olares.com`
is still fronted by an FRP relay key that is distinct from the host `sshd` key,
so that relay path remains a separate boundary rather than the controlling proof
surface for trusted operator access.

## Safe Recovery Rule

Do not remove or replace `known_hosts` entries unless the replacement
fingerprint has first been verified out of band.

Acceptable verification examples:

1. read the fingerprint directly from a trusted console on the Olares host
2. compare the fingerprint against a separately governed operator record
3. verify it through another already-trusted management path

## Helper Script

Use `infra/private/reconcile-olares-ssh-hostkey.ps1` only after the expected
fingerprint has been verified.

Example:

```powershell
pwsh -NoProfile -File infra/private/reconcile-olares-ssh-hostkey.ps1 `
  -ExpectedFingerprint 'SHA256:dMv6Sj7P+SUAd+1vgayaDY0ByxsdUhbatDymdR0aC+U.' `
  -ValidateOnly
```

At the current boundary, do not run that non-validate reconciliation command
for `jlswen2121.olares.com` because the trusted host console has reported a
different ED25519 fingerprint and the public hostname has now been shown to
front a relay endpoint with separate authentication behavior.

That default command reconciles only `jlswen2121.olares.com`, which is the
hostname currently used by the remote private-stack wrapper.

If the mesh alias must also be reconciled later, run a separate command such as:

```powershell
pwsh -NoProfile -File infra/private/reconcile-olares-ssh-hostkey.ps1 `
  -ExpectedFingerprint 'SHA256:dMv6Sj7P+SUAd+1vgayaDY0ByxsdUhbatDymdR0aC+U.' `
  -Hosts @('100.64.0.1') `
  -ValidateOnly
```

The helper script:

1. fetches fresh ED25519 host keys for `jlswen2121.olares.com` and `100.64.0.1`
2. computes their SHA256 fingerprints
3. refuses to update `known_hosts` if either fingerprint does not match the
   supplied expected value
4. removes the stale entries only after both hosts match the expected value
5. appends the verified fresh entries to the workstation `known_hosts` file

## After Reconciliation

After the SSH path issue is resolved by either restoring a working mesh route to
`100.64.0.1` or getting the relay path to accept the intended workstation key,
rerun:

1. `pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action setup`
2. `pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action config`
3. `pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action up`

At the current boundary, prefer the restored mesh route to `100.64.0.1` for any
further operator access or local SSH tunneling. Do not treat success over the
mesh alias as evidence that the public relay hostname is reconciled.

## Related Files

1. `infra/private/reconcile-olares-ssh-hostkey.ps1`
2. `infra/private/run-personal-stack-remote.ps1`
3. `docs/architecture/OLARES-PRIVATE-STACK-FIRST-RUN-CHECKLIST-2026-05-01.md`
4. `ops/agents/handoffs/2026-05-01-olares-private-stack-browser-terminal-bring-up-handoff.md`
