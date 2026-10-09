#!/usr/bin/env python3
"""Independent integrity checks for a restored Resume-AI checkout.

Usage:
  python3 tools/verify_snapshot.py                       # source tree vs provenance/SOURCE_SHA256SUMS.txt
  python3 tools/verify_snapshot.py --model-dir PATH      # + Qwen3.8-27B shards vs provenance/base-model.lock.json
  python3 tools/verify_snapshot.py --adapters-dir PATH   # + adapters/ tree vs provenance/adapter-inventory.json

Exit code 0 only if every requested check passes. Hashing the base model reads ~56 GB.
"""
import argparse, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def check_source():
    bad = n = 0
    for line in open(os.path.join(ROOT, 'provenance/SOURCE_SHA256SUMS.txt')):
        want, rel = line.rstrip('\n').split('  ', 1)
        p = os.path.join(ROOT, rel)
        n += 1
        if not os.path.exists(p) or sha256(p) != want:
            bad += 1
            print('SOURCE MISMATCH', rel)
    print(f'source: {n - bad}/{n} files match')
    return bad == 0


def check_model(model_dir):
    lock = json.load(open(os.path.join(ROOT, 'provenance/base-model.lock.json')))
    bad = n = 0
    for name, rec in lock['files'].items():
        if not rec.get('local_sha256'):
            continue
        p = os.path.join(model_dir, name)
        n += 1
        ok = os.path.exists(p) and os.path.getsize(p) == rec['bytes'] and sha256(p) == rec['local_sha256']
        bad += not ok
        print(('OK  ' if ok else 'FAIL'), name)
    print(f"model {lock['repo_id']}@{lock['revision'][:8]}: {n - bad}/{n} files match")
    return bad == 0


def check_adapters(adapters_dir):
    inv = json.load(open(os.path.join(ROOT, 'provenance/adapter-inventory.json')))
    bad = n = 0
    for ckpt, rec in inv.items():
        base = os.path.join(adapters_dir, os.path.relpath(ckpt, 'adapters'))
        for name, want in rec['checksums'].items():
            want = want['sha256'] if isinstance(want, dict) else want
            p = os.path.join(base, name)
            n += 1
            if not os.path.exists(p) or sha256(p) != want:
                bad += 1
                print('ADAPTER MISMATCH', ckpt, name)
    print(f'adapters: {n - bad}/{n} files match across {len(inv)} checkpoints')
    return bad == 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--model-dir')
    ap.add_argument('--adapters-dir')
    a = ap.parse_args()
    ok = check_source()
    if a.model_dir:
        ok &= check_model(a.model_dir)
    if a.adapters_dir:
        ok &= check_adapters(a.adapters_dir)
    sys.exit(0 if ok else 1)
