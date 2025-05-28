# pip-info
Wrapper for pip for displaying package information before installation.
Will only wrap around the `install` command, and ask for user verification.

## Usage:
- Make executable with `chmod +x pip-safe.py`
- (Optional) Add alias in shell startup: `alias pips=/path/to/pip-safe.py`
- Run: pips install requests

## Example:
```
user:~$ pips install requests

→ requests  (will install v2.32.3)
    Summary      : Python HTTP for Humans.
    Author       : Kenneth Reitz
    Documentation: https://requests.readthedocs.io
    Homepage     : https://requests.readthedocs.io

Proceed with installation? [y/N]: n
Aborted.
```

## Note
This relies on the pypi json being available and informative. Package managers can write pretty much whatever they want in that information. It's a bit of extra, useful information to validate you are installing the correct package, but it's not a guarantee. Rely on this information at your own risk - as usual, be wary with what you're installing on your machine.
