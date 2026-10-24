#!/usr/bin/env python3
"""Inventory portable skills and install non-destructive links (stdlib only)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

EXCLUDED = {'.git', '.archive', '.hub', '.locks', '__pycache__', 'node_modules', 'vendor_imports'}


def discover(root):
    root = Path(root).expanduser().absolute()
    records = []
    seen = set()
    def visit(directory):
        try:
            resolved = directory.resolve(strict=True)
        except (OSError, RuntimeError):
            return
        if resolved in seen:
            return
        seen.add(resolved)
        skill = directory / 'SKILL.md'
        if skill.is_file():
            text = skill.read_text(encoding='utf-8')
            front = text.split('---', 2)[1] if text.startswith('---\n') and text.count('---') >= 2 else ''
            match = re.search(r'^name:\s*[\"\']?([^\n\"\']+)', front, re.M)
            name = match.group(1).strip() if match else directory.name
            assets = {}
            for base, dirs, files in os.walk(directory, followlinks=False):
                dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in EXCLUDED)
                for filename in sorted(files):
                    path = Path(base) / filename
                    if filename.startswith('.') or path.is_symlink():
                        continue
                    assets[str(path.relative_to(directory))] = hashlib.sha256(path.read_bytes()).hexdigest()
            records.append({'name': name, 'path': str(directory), 'resolved': str(resolved), 'files': assets})
            return
        if directory.is_dir():
            for child in sorted(directory.iterdir()):
                if not child.name.startswith('.') and child.name not in EXCLUDED and child.is_dir():
                    visit(child)
    visit(root)
    return records


def plan_install(records, destination):
    destination = Path(destination).expanduser().absolute()
    names = [r['name'] for r in records]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate frontmatter names; resolve conflicts before installation')
    plan = []
    for record in records:
        name = record['name']
        if name in {'.', '..'} or not re.fullmatch(r'[a-zA-Z0-9_-]+', name):
            raise ValueError(f'Unsafe skill name: {name!r}')
        source = Path(record['path']).absolute()
        target = destination / name
        if target == source or (target.exists() and target.resolve() == source.resolve()):
            action = 'already-installed'
        elif target.exists() or target.is_symlink():
            action = 'conflict'
        else:
            action = 'link'
        plan.append({'name': name, 'source': str(source), 'target': str(target), 'action': action})
    return plan


def apply_plan(plan):
    # Preflight the entire batch; never partially apply a known-conflicting plan.
    if any(item['action'] == 'conflict' for item in plan):
        raise ValueError('Existing targets conflict; nothing changed')
    created = []
    try:
        for item in plan:
            if item['action'] != 'link':
                continue
            target = Path(item['target'])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(item['source'], target_is_directory=True)
            created.append(target)
    except OSError:
        for target in reversed(created):
            target.unlink()
        raise
    return [str(p) for p in created]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inv = commands.add_parser('inventory')
    inv.add_argument('roots', nargs='+')
    install = commands.add_parser('install')
    install.add_argument('--source', default=str(Path(__file__).resolve().parents[1]))
    install.add_argument('--destination', required=True, help='Verified native discovery root for the selected harness')
    install.add_argument('--apply', action='store_true', help='Default is dry-run; never overwrites existing entries')
    args = parser.parse_args()
    if args.command == 'inventory':
        result = {str(Path(r).expanduser()): discover(r) for r in args.roots}
        print(json.dumps(result, indent=2))
        return
    plan = plan_install(discover(args.source), args.destination)
    print(json.dumps({'plan': plan, 'dry_run': not args.apply}, indent=2))
    if args.apply:
        try:
            created = apply_plan(plan)
        except (ValueError, OSError) as error:
            parser.exit(1, f'{error}\n')
        print(json.dumps({'created': created}, indent=2))


if __name__ == '__main__':
    main()
