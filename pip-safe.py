#!/usr/bin/env python3
import sys, subprocess, urllib.request, urllib.error, json
from packaging.requirements import Requirement
from packaging.specifiers   import SpecifierSet
from packaging.version      import Version, InvalidVersion
from packaging.utils        import canonicalize_name

def is_install_cmd(args):
    for tok in args:
        if not tok.startswith('-'):
            return tok == 'install'
    return False

def parse_req(spec):
    try:
        req = Requirement(spec)
        name = canonicalize_name(req.name)
        spec_set = req.specifier or SpecifierSet()
    except Exception:
        # bare name with no PEP 508 details
        name, spec_set = canonicalize_name(spec), SpecifierSet()
    return name, spec_set

def select_version(name, specifier):
    url = f'https://pypi.org/pypi/{name}/json'
    try:
        data = json.load(urllib.request.urlopen(url))
    except Exception:
        return None
    releases = data.get('releases', {})
    candidates = []
    for ver_str, files in releases.items():
        try:
            ver = Version(ver_str)
        except InvalidVersion:
            continue
        # version must satisfy specifier (handles prereleases correctly)
        if not specifier.contains(ver, prereleases=False):
            continue
        # skip if *all* files are yanked
        if files and all(f.get('yanked', False) for f in files):
            continue
        candidates.append(ver)
    if not candidates:
        return None
    return str(max(candidates))

def fetch_metadata(name, version):
    # run pip install --dry-run --no-deps --disable-pip-version-check --quiet --only-binary :all: --report - package_name
    # to get metadata in json form without actually installing the package
    subprocess_args = [sys.executable, '-m', 'pip', 'install', '--dry-run', '--no-deps', '--disable-pip-version-check', '--quiet', '--only-binary', ':all:', '--report', '-']
    if version:
        subprocess_args.append(f'{name}=={version}')
    else:
        subprocess_args.append(name)
    data = subprocess.check_output(subprocess_args, text=True, stderr=subprocess.DEVNULL)
    # parse the metadata from the pip output
    try:
        data = json.loads(data)['install'][0]['metadata']
    except json.JSONDecodeError:
        return None
    if not data:
        return None
    get = lambda *keys: next((data.get(k) for k in keys if data.get(k)), 'N/A')
    author  = get('author', 'maintainer')
    summary = get('summary')
    proj_urls = data.get('project_url') or []
    proj_urls_dict = {}
    for purl in proj_urls:
        pkey, url = purl.split(', ', 1)
        proj_urls_dict[pkey] = url
    proj_urls = proj_urls_dict
    docs = proj_urls.get('Documentation') or next((v for k,v in proj_urls.items() if k.lower()=='documentation'), 'N/A')
    home = proj_urls.get('Homepage') or next((v for k,v in proj_urls.items() if k.lower()=='homepage'), data.get('home_page','N/A'))
    return {
        'version':     data.get('version', version),
        'summary':     summary,
        'author':      author,
        'documentation': docs,
        'homepage':    home
    }

def main():
    args = sys.argv[1:]
    if not is_install_cmd(args):
        # pass everything else straight to pip
        return subprocess.call([sys.executable, '-m', 'pip'] + args)

    # collect install specs (skip options)
    idx   = args.index('install')
    specs = [tok for tok in args[idx+1:] if not tok.startswith('-')]

    results = {}
    for spec in specs:
        name, spec_set = parse_req(spec)
        ver = select_version(name, spec_set)
        if not ver:
            results[spec] = None
        else:
            results[spec] = fetch_metadata(name, ver)

    # display metadata
    for spec, md in results.items():
        if md is not None:
            print(f"\n→ {spec}  (will install v{md['version']})")
            print(f"    Summary      : {md['summary']}")
            print(f"    Author       : {md['author']}")
            print(f"    Documentation: {md['documentation']}")
            print(f"    Homepage     : {md['homepage']}")
        else:
            print(f"\n→ {spec}  — no matching release found on PyPI")

    ans = input("\nProceed with installation? [y/N]: ").strip().lower()
    if ans == 'y':
        return subprocess.call([sys.executable, '-m', 'pip'] + args)
    print("Aborted.")
    return 1

if __name__=='__main__':
    sys.exit(main())
