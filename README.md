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
      "path": "/mnt/c/Users/Tarik Curto/Documents/Obsidian/TCC",
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
1. Run the `autogit.py` script. It will read the configuration, check for changes in the specified repositories, and if there are any, it will commit and push them to the remote repository.

## Cron installing
To set up AutoGIT to run automatically at regular intervals using cron, follow these steps:
1. Use the script `install-cron.sh` to install the cron job. This script will add an entry to your crontab that runs the `autogit.py` script at the desired frequency.
2. You can customize the frequency by editing the cron entry.
