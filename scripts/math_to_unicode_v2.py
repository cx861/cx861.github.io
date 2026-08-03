"""
最终版：Markdown 优化 + LaTeX→Unicode 完整转换
输入: v3 提取的 LaTeX MD | 输出: 干净Unicode MD
"""
import sys, re

# ========== 完整 LaTeX → Unicode 映射 ==========
LATEX_SYMBOLS = {
    # 希腊字母
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\epsilon': 'ϵ', r'\varepsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η',
    r'\theta': 'θ', r'\vartheta': 'ϑ', r'\iota': 'ι', r'\kappa': 'κ',
    r'\lambda': 'λ', r'\mu': 'μ', r'\nu': 'ν', r'\xi': 'ξ',
    r'\pi': 'π', r'\varpi': 'ϖ', r'\rho': 'ρ', r'\varrho': 'ϱ',
    r'\sigma': 'σ', r'\varsigma': 'ς', r'\tau': 'τ', r'\upsilon': 'υ',
    r'\phi': 'ϕ', r'\varphi': 'φ', r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
    r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
    r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Upsilon': 'Υ',
    r'\Phi': 'Φ', r'\Psi': 'Ψ', r'\Omega': 'Ω',

    # 数学符号
    r'\infty': '∞', r'\partial': '∂', r'\nabla': '∇', r'\emptyset': '∅',
    r'\varnothing': '∅', r'\forall': '∀', r'\exists': '∃', r'\nexists': '∄',
    r'\in': '∈', r'\notin': '∉', r'\ni': '∋', r'\subset': '⊂',
    r'\supset': '⊃', r'\subseteq': '⊆', r'\supseteq': '⊇',
    r'\cup': '∪', r'\cap': '∩', r'\setminus': '\\',
    r'\times': '×', r'\cdot': '·', r'\pm': '±', r'\mp': '∓',
    r'\div': '÷', r'\ast': '∗', r'\star': '⋆', r'\circ': '∘',
    r'\bullet': '•', r'\oplus': '⊕', r'\ominus': '⊖', r'\otimes': '⊗',
    r'\oslash': '⊘', r'\odot': '⊙',
    r'\leq': '≤', r'\geq': '≥', r'\neq': '≠', r'\equiv': '≡',
    r'\approx': '≈', r'\simeq': '≃', r'\cong': '≅', r'\sim': '∼',
    r'\propto': '∝', r'\ll': '≪', r'\gg': '≫',
    r'\Rightarrow': '⇒', r'\implies': '⇒', r'\Leftarrow': '⇐',
    r'\Leftrightarrow': '⇔', r'\iff': '⇔',
    r'\rightarrow': '→', r'\to': '→', r'\longrightarrow': '→',
    r'\leftarrow': '←', r'\longleftarrow': '←',
    r'\mapsto': '↦', r'\longmapsto': '↦',
    r'\uparrow': '↑', r'\downarrow': '↓', r'\updownarrow': '↕',
    r'\nearrow': '↗', r'\searrow': '↘',
    r'\Longrightarrow': '⇒', r'\Longleftarrow': '⇐',
    r'\nRightarrow': '⇏', r'\not\Rightarrow': '⇏',

    # 集合与逻辑
    r'\mathbb{R}': 'ℝ', r'\mathbb{N}': 'ℕ', r'\mathbb{Z}': 'ℤ',
    r'\mathbb{Q}': 'ℚ', r'\mathbb{C}': 'ℂ', r'\mathcal{F}': 'ℱ',
    r'\wedge': '∧', r'\vee': '∨', r'\neg': '¬', r'\lnot': '¬',
    r'\top': '⊤', r'\bot': '⊥',
    r'\vdash': '⊢', r'\models': '⊨',

    # 几何
    r'\angle': '∠', r'\triangle': '△', r'\triangleq': '≜',
    r'\perp': '⊥', r'\parallel': '∥', r'\nparallel': '∦',
    r'\diamond': '◇', r'\square': '□', r'\Box': '□',
    r'\langle': '⟨', r'\rangle': '⟩',
    r'\lceil': '⌈', r'\rceil': '⌉',
    r'\lfloor': '⌊', r'\rfloor': '⌋',

    # 标准函数
    r'\sin': 'sin', r'\cos': 'cos', r'\tan': 'tan',
    r'\cot': 'cot', r'\sec': 'sec', r'\csc': 'csc',
    r'\arcsin': 'arcsin', r'\arccos': 'arccos', r'\arctan': 'arctan',
    r'\sinh': 'sinh', r'\cosh': 'cosh', r'\tanh': 'tanh',
    r'\log': 'log', r'\ln': 'ln', r'\lg': 'lg',
    r'\exp': 'exp', r'\det': 'det', r'\dim': 'dim',
    r'\ker': 'ker', r'\hom': 'hom',
    r'\arg': 'arg', r'\deg': 'deg',
    r'\gcd': 'gcd', r'\lcm': 'lcm',
    r'\Pr': 'Pr',

    # 微积分
    r'\lim': 'lim', r'\limsup': 'limsup', r'\liminf': 'liminf',
    r'\min': 'min', r'\max': 'max', r'\sup': 'sup', r'\inf': 'inf',
    r'\displaystyle': '', r'\textstyle': '', r'\scriptstyle': '',
    r'\dfrac': '', r'\frac': '', r'\tfrac': '', r'\binom': '',
    r'\sqrt': '√', r'\surd': '√',

    # 求和积分
    r'\sum': '∑', r'\prod': '∏', r'\int': '∫', r'\iint': '∬',
    r'\iiint': '∭', r'\oint': '∮', r'\oiint': '∯',

    # 省略号
    r'\dots': '…', r'\ldots': '…', r'\cdots': '⋯',
    r'\vdots': '⋮', r'\ddots': '⋱',

    # 向量
    r'\mathbf{F}': 'F', r'\mathbf{n}': 'n', r'\mathbf{r}': 'r',
    r'\mathbf{l}': 'l', r'\mathbf{v}': 'v', r'\mathbf{f}': 'f',
    r'\vec{a}': 'a⃗', r'\vec{b}': 'b⃗', r'\vec': '', r'\bar': '',
    r'\hat': '', r'\tilde': '', r'\widehat': '', r'\widetilde': '',

    # 间距与分隔
    r'\qquad': '  ', r'\quad': ' ', r'\;': '', r'\,': '', r'\!': '',
    r'\ ': ' ',  # backslash space

    # 大型运算符修饰
    r'\limits': '', r'\nolimits': '',

    # misc
    r'\mid': '|', r'\vert': '|', r'\lvert': '|', r'\rvert': '|',
    r'\|': '‖', r'\Vert': '‖', r'\lVert': '‖', r'\rVert': '‖',
    r'\backslash': '\\',
    r'\pmod': 'mod', r'\bmod': 'mod',
    r'\cdot': '·', r'\cdots': '⋯',
    r'\left': '', r'\right': '', r'\big': '', r'\Big': '', r'\bigg': '', r'\Bigg': '',
    r'\overline': '', r'\underline': '', r'\overbrace': '', r'\underbrace': '',
    r'\xrightarrow': '-', r'\xleftarrow': '-',
    r'\overrightarrow': '→', r'\overleftarrow': '←',
    r'\operatorname': '', r'\mathrm': '', r'\mathit': '', r'\mathbf': '',
    r'\mathsf': '', r'\mathtt': '',
    r'\text': '', r'\mbox': '',
}

SUB_MAP = {'0': '₀','1': '₁','2': '₂','3': '₃','4': '₄','5': '₅','6': '₆','7': '₇','8': '₈','9': '₉',
           'a': 'ₐ','e': 'ₑ','i': 'ᵢ','j': 'ⱼ','k': 'ₖ','n': 'ₙ','m': 'ₘ','x': 'ₓ','y': 'ᵧ','+': '₊','-': '₋'}

SUP_MAP = {'0': '⁰','1': '¹','2': '²','3': '³','4': '⁴','5': '⁵','6': '⁶','7': '⁷','8': '⁸','9': '⁹',
           '+': '⁺','-': '⁻','n': 'ⁿ','k': 'ᵏ','m': 'ᵐ','T': 'ᵀ','i': 'ⁱ','=': '⁼','(': '⁽',')': '⁾'}


def replace_all(text, mapping):
    for k, v in sorted(mapping.items(), key=lambda x: -len(x[0])):
        text = text.replace(k, v)
    return text


def convert_formula(formula):
    formula = replace_all(formula, LATEX_SYMBOLS)

    # \text{...} → inner text
    formula = re.sub(r'\\text\s*\{([^}]*)\}', r'\1', formula)
    # \operatorname{...} → inner text
    formula = re.sub(r'\\operatorname\s*\{([^}]*)\}', r'\1', formula)

    # Subscripts _{...}
    formula = re.sub(r'_\{([^}]+)\}', lambda m: ''.join(SUB_MAP.get(c, c) for c in m.group(1)), formula)
    formula = re.sub(r'_(\w)', lambda m: SUB_MAP.get(m.group(1), m.group(1)), formula)

    # Superscripts ^{...}
    formula = re.sub(r'\^\{([^}]+)\}', lambda m: ''.join(SUP_MAP.get(c, c) for c in m.group(1)), formula)
    formula = re.sub(r'\^(\w)', lambda m: SUP_MAP.get(m.group(1), m.group(1)), formula)

    # Fractions
    formula = re.sub(r'\\dfrac\s*\{([^}]+)\}\s*\{([^}]+)\}', r'(\1)/(\2)', formula)
    formula = re.sub(r'\\frac\s*\{([^}]+)\}\s*\{([^}]+)\}', r'(\1)/(\2)', formula)
    formula = re.sub(r'\\binom\s*\{([^}]+)\}\s*\{([^}]+)\}', r'C(\1,\2)', formula)

    # Cleanup
    formula = formula.replace('{', '').replace('}', '')
    formula = formula.replace('\\(', '(').replace('\\)', ')')
    formula = formula.replace('\\[', '[').replace('\\]', ']')
    formula = re.sub(r'\s+', ' ', formula).strip()
    return formula


def convert_file(text):
    # Display math $$...$$
    text = re.sub(r'\$\$\s*(.+?)\s*\$\$',
                  lambda m: '\n\n  ' + convert_formula(m.group(1)).strip() + '\n',
                  text, flags=re.DOTALL)
    # Inline math $...$
    text = re.sub(r'\$(.+?)\$', lambda m: convert_formula(m.group(1)), text)

    # Handle \begin/\end environments (cases, pmatrix, etc.)
    text = re.sub(r'\\begin\{([^}]+)\}\s*', '', text)
    text = re.sub(r'\\end\{([^}]+)\}', '', text)
    # \\+ in cases → line break
    text = re.sub(r'\\\\+', '\n  ', text)

    # Line-level cleanup: convert bare LaTeX on math-looking lines
    MATH_LINE_PAT = re.compile(r'\\[a-zA-Z]{2,}')
    lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped.startswith('```') and MATH_LINE_PAT.search(line):
            if '$' not in line:
                # Pre-clean: remove \begin + suffix, \end + suffix
                line = re.sub(r'\\begin\w*', '', line)
                line = re.sub(r'\\end\w*', '', line)
                line = line.replace(r'\xrightarrow', '→')
                line = convert_formula(line)
        lines.append(line)
    text = '\n'.join(lines)

    # Cleanup
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +\n', '\n', text)
    return text


if __name__ == '__main__':
    content = sys.stdin.read()
    print(convert_file(content))
