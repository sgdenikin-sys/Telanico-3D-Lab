"""Public-safe provenance. Never copy environment, private source or raw archives."""
from pathlib import Path
import os,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
commit=os.environ.get('BUILD_SOURCE_SHA') or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
branch=os.environ.get('BUILD_SOURCE_BRANCH') or subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
build=dict(version='telanico-v2',commit=commit,branch=branch,source_run_id=os.environ.get('GITHUB_RUN_ID','local'))
text=json.dumps(build,sort_keys=True)
# Runtime source metadata is stamped BEFORE export; public copy AFTER export.
if '--before' in __import__('sys').argv:
    (ROOT/'godot/assets/generated/build_info.json').write_text(text+'\n')
else:
    directory=ROOT/'build/web';(directory/'build.json').write_text(text+'\n')
    (directory/'LICENSES.html').write_text('<!doctype html><meta charset="utf-8"><title>Asset credits</title><h1>Telanico preview assets</h1><p>KayKit Medieval Hexagon Pack 1.0 and Adventurers 1.0 — Kay Lousberg — CC0. Derived palettes and department additions: Telanico.</p><p><a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0 1.0</a> · <a href="https://github.com/KayKit-Game-Assets">Author source</a></p>')
    p=directory/'index.html';html=p.read_text();html=html.replace('</head>',f'<meta name="telanico-build" content="{commit}"></head>');p.write_text(html)
    print('BUILD_STAMP_OK',commit)
