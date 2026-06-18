import re

latex_to_unicode = {
    r'\cup': '∪', r'\cap': '∩', r'\Omega': 'Ω',
    r'\subset': '⊂', r'\supset': '⊃',
    r'\varnothing': '∅', r'\emptyset': '∅',
    r'\cdots': '⋯', r'\ldots': '…',
    r'\infty': '∞',
    r'\sum': '∑', r'\prod': '∏', r'\int': '∫',
    r'\Rightarrow': '⇒', r'\Leftrightarrow': '⇔',
    r'\rightarrow': '→', r'\to': '→',
    r'\leftarrow': '←',
    r'\leq': '≤', r'\geq': '≥', r'\neq': '≠',
    r'\approx': '≈', r'\equiv': '≡',
    r'\forall': '∀', r'\exists': '∃',
    r'\in': '∈', r'\notin': '∉',
    r'\times': '×', r'\cdot': '·', r'\pm': '±',
    r'\sim': '∼', r'\partial': '∂',
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\varepsilon': 'ε',
    r'\theta': 'θ', r'\lambda': 'λ', r'\mu': 'μ',
    r'\pi': 'π', r'\rho': 'ρ', r'\sigma': 'σ',
    r'\varphi': 'φ', r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
    r'\mathbb{R}': 'ℝ', r'\mathbb{N}': 'ℕ',
    r'\mathcal{F}': 'ℱ',
    r'\xrightarrow{P}': ' -P-> ', r'\xrightarrow{d}': ' -d-> ',
    r'\mid': '|',
    r'\lim': 'lim', r'\ln': 'ln', r'\log': 'log',
    r'\exp': 'exp', r'\max': 'max', r'\min': 'min',
    r'\sup': 'sup', r'\inf': 'inf',
    r'\emptyset': '∅',
    r'\triangleq': '≜',
}

sub_map = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    'a': 'ₐ', 'e': 'ₑ', 'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ',
    'n': 'ₙ', 'm': 'ₘ', 'x': 'ₓ', 'y': 'ᵧ',
    '+': '₊', '-': '₋',
}

sup_map = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    '+': '⁺', '-': '⁻', 'n': 'ⁿ', 'k': 'ᵏ', 'm': 'ᵐ',
    'T': 'ᵀ',
}


def replace_all(text, mapping):
    for latex, uni in sorted(mapping.items(), key=lambda x: -len(x[0])):
        text = text.replace(latex, uni)
    return text


def convert_subscripts(text):
    def repl(m):
        content = m.group(1)
        if len(content) == 1 and content in sub_map:
            return sub_map[content]
        return '_' + content
    return re.sub(r'_\{([^}]+)\}', repl, text)


def convert_superscripts(text):
    def repl(m):
        content = m.group(1)
        if len(content) == 1 and content in sup_map:
            return sup_map[content]
        return '^' + content
    return re.sub(r'\^\{([^}]+)\}', repl, text)


def frac_to_slash(m):
    num = m.group(1).strip()
    den = m.group(2).strip()
    combined = num + '/' + den
    if len(combined) < 25:
        return combined
    return '(' + num + ')/(' + den + ')'


def convert_formula(text):
    text = replace_all(text, latex_to_unicode)

    # Subscripts
    text = convert_subscripts(text)

    # Superscripts
    text = convert_superscripts(text)

    # \frac and \dfrac
    text = re.sub(r'\\dfrac\{([^}]+)\}\{([^}]+)\}', frac_to_slash, text)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', frac_to_slash, text)

    # \text{...} -> keep content only
    text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)

    # \overline{X} -> X̄ (combining overline)
    text = re.sub(r'\\overline\{([^}]+)\}', lambda m: m.group(1) + '\u0305', text)

    # \mathrm{...} -> keep content
    text = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', text)

    # Remove \left, \right
    text = text.replace('\\left', '').replace('\\right', '')

    # \bigcup, \bigcap
    text = text.replace('\\bigcup', '⋃').replace('\\bigcap', '⋂')

    # \, thin space -> nothing
    text = text.replace('\\,', '')

    # \; -> space
    text = text.replace('\\;', ' ')

    # \! -> nothing (negative space)
    text = text.replace('\\!', '')

    # Remove remaining LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+', '', text)

    # Clean up leftover braces and whitespace
    text = text.replace('{', '').replace('}', '')
    text = re.sub(r'\s+', ' ', text).strip()

    return text


# Process both files
files = [
    ('math/probability/数学一-概率论全章节知识点完整版.md',
     'C:/Users/陈鑫/Desktop/概率论知识库-数学一.md'),
    ('math/probability/数学一-概率论分章节经典题型与关联知识点.md',
     'C:/Users/陈鑫/Desktop/概率论常考题型与解法-数学一.md'),
]

for src, dst in files:
    with open(src, 'r', encoding='utf-8') as f:
        content = f.read()

    # Process display math $$...$$
    def dmath(m):
        formula = m.group(1)
        formula = convert_formula(formula)
        # Handle cases and pmatrix environments
        formula = formula.replace('begin{cases}', '')
        formula = formula.replace('end{cases}', '')
        formula = formula.replace('begin{pmatrix}', '')
        formula = formula.replace('end{pmatrix}', '')
        formula = formula.replace('\\\\', '\n  ')
        return '\n\n  ' + formula.strip() + '\n'

    content = re.sub(r'\$\$\s*(.+?)\s*\$\$', dmath, content, flags=re.DOTALL)

    # Process inline math $...$
    def imath(m):
        formula = m.group(1)
        return convert_formula(formula)

    content = re.sub(r'\$(.+?)\$', imath, content)

    # Clean up multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    with open(dst, 'w', encoding='utf-8', newline='') as f:
        f.write(content)

    print('Written: ' + dst)

print('Done!')
