# Security and privacy notes

- Never publish a complete `console_mp.log`; it may contain server credentials or other service parameters.
- `config.json` and `config.backup.json` are user-specific and are excluded from the repository.
- The updater validates the SHA256 declared in the release manifest before applying an update.
- Update archives are validated against unsafe paths before extraction.

For a security-sensitive report, contact the repository owner privately rather than posting credentials or private logs in a public issue.
