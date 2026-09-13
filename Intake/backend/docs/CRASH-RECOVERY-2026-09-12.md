# Intake session recovery — 2026-09-12

Recovered after the owner reported a crash. The prior subagents were no longer
running. Use the explicit working directory
`E:/AI_Workspace/Projects/Propria/Consignatio`; the task default directory failed
with Windows error 267.

Verified after recovery:

- Independent surreal-intake service survived and returned HTTP 200 on health.
- Rotated the administrative password reported exposed by a prior agent's CLI
  help command; updated Coolify and restarted only the remote Intake service
  through Coolify. The new service is healthy and authenticated INFO FOR DB works.
- Credential bridge and projection adapter files survived. Their combined
  focused pytest run passed all 18 tests.
- Backup scripts and timer/service definitions survived, but installation and
  restore verification remain pending.
- Tailscale skill reference contains the tag:docker service auto-approval
  procedure. Live tailnet policy application remains unverified.

Do not run Surreal CLI help with secrets in the environment: its help output
includes environment values. For help only, explicitly unset authentication
environment variables in that subprocess first.

No user files were deleted or reverted during recovery.
