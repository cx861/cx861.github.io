import re, sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()

# Check $$ blocks for brace pairing
blocks = re.findall(r'\$\$(.*?)\$\$', content, re.DOTALL)
errors = []
for i, block in enumerate(blocks):
    opens = block.count('{')
    closes = block.count('}')
    if opens != closes:
        errors.append(f'Block {i+1}: {{ = {opens}, }} = {closes}, diff = {opens - closes}')

if errors:
    print('FAIL: Brace mismatch in $$ blocks:')
    for e in errors:
        print(f'  {e}')
else:
    print(f'PASS: All {len(blocks)} $$ blocks have matching braces')

# Check raw markdown syntax
md_issues = []
if re.search(r'(?<!<)#{2,3}\s', content):
    md_issues.append('raw ###/## heading')
if re.search(r'(?<!<)-{3}\s*\n', content):
    md_issues.append('raw --- divider')
if re.search(r'(?<!<)\*\*[^*]+\*\*', content):
    md_issues.append('raw **bold**')
if re.search(r'^-\s', content, re.MULTILINE):
    md_issues.append('raw - list item')

if md_issues:
    print('FAIL: Raw markdown syntax:')
    for i in md_issues:
        print(f'  {i}')
else:
    print('PASS: No raw markdown syntax')

# Check HTML tags inside $$ blocks
html_in_math = []
for i, block in enumerate(blocks):
    if re.search(r'<\w+[^>]*>', block):
        html_in_math.append(f'Block {i+1}')
if html_in_math:
    print('FAIL: HTML tags inside $$ blocks:')
    for e in html_in_math:
        print(f'  {e}')
else:
    print('PASS: No HTML tags inside $$ blocks')

# Check \begin...\end pairing
begins = len(re.findall(r'\\begin\{', content))
ends = len(re.findall(r'\\end\{', content))
if begins != ends:
    print(f'FAIL: \\begin/\\end mismatch: {begins} begins vs {ends} ends')
else:
    print(f'PASS: \\begin/\\end paired ({begins} environments)')

# Quick sanity
total_dollar = content.count('$')
print(f'INFO: Total $ signs: {total_dollar}')

all_ok = not (errors or md_issues or html_in_math or begins != ends)
print(f'\n{"=== ALL CHECKS PASSED ===" if all_ok else "=== ISSUES FOUND ==="}')
