# braves-backup

Runs the nightly encrypted database backup for the Braves system. It is public
only so that GitHub Actions minutes are free.

- `.github/workflows/nightly-backup.yml` dumps the database at 02:17 SGT,
  encrypts it with `supabase/backup-recipient.txt` (an age **public** key), and
  uploads the ciphertext to Cloudflare R2. It keeps 30 daily copies and one per
  month.
- `tools/backup/dump.py` is a copy of the same file in the private
  `braves-system` repository. Change both together.
- Credentials live only in this repository's Actions secrets:
  `SUPABASE_DB_URL`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_ENDPOINT`.
- The decryption key is never stored here. Restore steps and manual
  restore-drill backups live in `braves-system`.
