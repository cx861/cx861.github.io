"""Final pass: convert remaining LaTeX fragments"""
import re

FIXES = [
    (r'\\leq', '≤'), (r'\\geq', '≥'), (r'\\lambda', 'λ'), (r'\\theta', 'θ'),
    (r'\\min', 'min'), (r'\\max', 'max'), (r'\\infty', '∞'), (r'\\to', '→'),
    (r'\\hat', ''), (r'\\xrightarrow', '→'), (r'\\not', '¬'), (r'\\cdot', '·'),
    (r'\\approx', '≈'), (r'\\frac', ''), (r'\\begin', ''), (r'\\end', ''),
    (r'\\overrightarrow', '→'),
    (r'\\x', ''), (r'\\d', ''), (r'\\a', ''), (r'\\b', ''), (r'\\B', ''),
    (r'\\S', ''), (r'\\mathbf', ''),
]

import sys
for path in sys.argv[1:]:
    with open(path, 'r', encoding='utf-8') as f:
        t = f.read()
    for pat, rep in FIXES:
        t = re.sub(pat, rep, t)
    t = re.sub(r'\\[a-zA-Z]', '', t)
    t = t.replace('\\{', '{').replace('\\}', '}')
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(t)
    cnt = len(re.findall(r'\\[a-zA-Z]{2,}', t))
    print(f'{path}: {cnt} remnants')
