# Prints the installed skill's version as one line for the skill's published output, e.g.
# "0.30.0 (abc1234, with local changes)", "0.30.0 (abc1234)", "0.30.0", or with no manifest
# "abc1234 (with local changes)". Copy into skills/<name>/; it looks two directories up.
# Usage: python3 skill_version.py OUT_DIR
#   Version: "version" in the plugin's agent manifest (.claude-plugin/plugin.json, else
#   gemini-extension.json, two directories up from this script).
#   If that directory is in a git checkout: the checkout's short HEAD, and whether
#   `git --no-optional-locks status --porcelain -- .` there shows changes. If it does,
#   `git diff HEAD -- .` plus untracked files' names (`git ls-files --others
#   --exclude-standard -- .`) go to OUT_DIR/skill-local.diff (gitignore it; never publish it).
#   With neither a manifest nor git: "unknown".
# Only reads the checkout; never writes to it.
import json, subprocess, sys
from pathlib import Path

MANIFESTS = ['.claude-plugin/plugin.json', 'gemini-extension.json']


def git(plugin, *args):
    r = subprocess.run(['git', '--no-optional-locks', *args], cwd=plugin,
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def version(plugin):
    for name in MANIFESTS:
        try:
            v = json.loads((plugin / name).read_text()).get('version')
        except (OSError, ValueError):
            continue
        if v:
            return str(v)
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 skill_version.py OUT_DIR')
    out = Path(sys.argv[1])
    plugin = Path(__file__).resolve().parents[2]
    v = version(plugin)
    head = git(plugin, 'rev-parse', '--short', 'HEAD')
    if not head:
        print(v or 'unknown')
        return
    head = head.strip()
    extra = [head] if v else []
    if git(plugin, 'status', '--porcelain', '--', '.'):
        diff = git(plugin, 'diff', 'HEAD', '--', '.') or ''
        untracked = git(plugin, 'ls-files', '--others', '--exclude-standard', '--', '.') or ''
        if untracked:
            diff += '\n# Untracked files:\n' + ''.join('# ' + f + '\n' for f in untracked.splitlines())
        (out / 'skill-local.diff').write_text(diff)
        extra.append('with local changes')
    print((v or head) + (' (' + ', '.join(extra) + ')' if extra else ''))


main()
