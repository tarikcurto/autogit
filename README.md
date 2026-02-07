# AutoGIT

AutoGIT is a Python script that automates the process of committing and pushing changes to Git repositories. It is designed to be run as a scheduled task (e.g., via cron) to keep your repositories up-to-date without manual intervention.

## Configuration
To use AutoGIT, you need to create a `config.json` file in the same directory as the script. This file should contain an array of repository configurations. Each configuration should include the following fields:
- `path`: The file system path to the Git repository.
- `remote`: The name of the remote repository (e.g., "origin").
- `branch`: The name of the branch to push to (e.g., "main").
- `message`: The commit message template, which can include `{timestamp}` to insert the current timestamp.
- `excludes`: An array of file patterns to exclude from commits (e.g., `[".obsidian/**", ".trash/**"]`).
Example `config.json`:
```json
{
  "repos": [
    {
      "path": "/mnt/c/Users/user1/Documents/Obsidian/Homework",
      "remote": "origin",
      "branch": "master",
      "message": "Auto-sync {timestamp}",
      "excludes": [
        ".obsidian/**",
        ".trash/**"
      ]
    }
  ]
}
```

## Usage

```bash
python autogit.py

# - or -
python autogit.py --config /path/to/your/config.json

# - or - 
python autogit.py --dry-run
```


## Cron installing

```bash
./install_cron.sh
```

## Cron management
To manage your cron jobs, you can use the following commands:

```bash
# Edit the crontab
crontab -e

# Check the status of the cron jobs
crontab -l

# See crontab logs
sudo grep "[CRON]" /var/log/syslog
---


