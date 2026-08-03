"""
将 v3 输出的 LaTeX MD 转为 Unicode 数学符号 MD
"""
import sys
import re

L2U = {
    r'\cup': '∪', r'\cap': '∩', r'\Omega': 'Ω', r'\subset': '⊂', r'\supset': '⊃',
    r'\varnothing': '∅', r'\emptyset': '∅', r'\cdots': '⋯', r'\ldots': '…',
    r'\infty': '∞', r'\sum': '∑', r'\prod': '∏', r'\int': '∫',
    r'\Rightarrow': '⇒', r'\rightarrow': '→', r'\to': '→',
    r'\leftarrow': '←', r'\Leftrightarrow': '⇔',
    r'\leq': '≤', r'\geq': '≥', r'\neq': '≠',
    r'\approx': '≈', r'\equiv': '≡', r'\forall': '∀', r'\exists': '∃',
    r'\in': '∈', r'\notin': '∉', r'\ni': '∋',
    r'\times': '×', r'\cdot': '·', r'\pm': '±', r'\mp': '∓',
    r'\sim': '∼', r'\partial': '∂', r'\nabla': '∇',
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\varepsilon': 'ε', r'\theta': 'θ', r'\lambda': 'λ', r'\mu': 'μ',
    r'\pi': 'π', r'\rho': 'ρ', r'\sigma': 'σ',
    r'\varphi': 'φ', r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
    r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
    r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Phi': 'Φ', r'\Psi': 'Ψ', r'\Omega': 'Ω',
    r'\mathbb{R}': 'ℝ', r'\mathbb{N}': 'ℕ', r'\mathbb{Z}': 'ℤ',
    r'\mathbb{Q}': 'ℚ', r'\mathbb{C}': 'ℂ',
    r'\mathcal{F}': 'ℱ', r'\mathcal{N}': '𝒩',
    r'\xrightarrow{P}': '—P→', r'\xrightarrow{d}': '—d→',
    r'\mid': '|', r'\nmid': '∤',
    r'\lim': 'lim', r'\ln': 'ln', r'\log': 'log',
    r'\exp': 'exp', r'\max': 'max', r'\min': 'min',
    r'\sup': 'sup', r'\inf': 'inf', r'\arg': 'arg',
    # Trig functions
    r'\sin': 'sin', r'\cos': 'cos', r'\tan': 'tan',
    r'\cot': 'cot', r'\sec': 'sec', r'\csc': 'csc',
    r'\arcsin': 'arcsin', r'\arccos': 'arccos',
    r'\arctan': 'arctan', r'\arccot': 'arccot',
    r'\operatorname{arccot}': 'arccot',
    r'\sqrt': '√', r'\cosh': 'cosh', r'\sinh': 'sinh', r'\tanh': 'tanh',
    r'\overline': '', r'\displaystyle': '',
    r'\triangleq': '≜', r'\triangle': '△',
    r'\mathrm{Cov}': 'Cov', r'\operatorname{div}': 'div',
    r'\operatorname{rot}': 'rot', r'\operatorname{grad}': 'grad',
    r'\mathbf{F}': 'F', r'\mathbf{n}': 'n', r'\mathbf{r}': 'r',
    r'\mathbf{l}': 'l',
    r'\vec': '', r'\bar': '', r'\hat': '', r'\tilde': '',
    r'\angle': '∠', r'\parallel': '∥', r'\perp': '⊥',
    r'\propto': '∝', r'\circ': '∘', r'\bullet': '•',
    r'\emptyset': '∅', r'\varnothing': '∅',
    r'\cdot': '·', r'\cdots': '⋯', r'\vdots': '⋮', r'\ddots': '⋱',
    r'\clubsuit': '♣', r'\diamondsuit': '♢', r'\heartsuit': '♡', r'\spadesuit': '♠',
    r'\dagger': '†', r'\ddagger': '‡', r'\S': '§', r'\P': '¶',
    r'\square': '□', r'\Box': '□', r'\Diamond': '◇',
    # Extra math
    r'\approx': '≈', r'\simeq': '≃',
    r'\langle': '⟨', r'\rangle': '⟩',
    r'\lfloor': '⌊', r'\rfloor': '⌋',
    r'\lceil': '⌈', r'\rceil': '⌉',
    r'\binom': '', r'\dbinom': '', r'\tbinom': '',
    r'\setminus': '\\', r'\backslash': '\\',
    r'\vert': '|', r'\lvert': '|', r'\rvert': '|',
    r'\Vert': '‖', r'\lVert': '‖', r'\rVert': '‖',
    r'\longrightarrow': '→', r'\longleftarrow': '←',
    r'\Longrightarrow': '⇒', r'\Longleftarrow': '⇐',
    r'\longmapsto': '↦',
    r'\uparrow': '↑', r'\downarrow': '↓', r'\updownarrow': '↕',
    r'\nearrow': '↗', r'\searrow': '↘', r'\swarrow': '↙', r'\nwarrow': '↖',
    r'\left': '', r'\right': '', r'\big': '', r'\Big': '',
    r'\bigg': '', r'\Bigg': '',
    r'\qquad': '  ', r'\quad': ' ',
    r'\;': ' ', r'\;': ' ', r'\,': '', r'\!': '',
}

SUB_MAP = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉',
           'a':'ₐ','e':'ₑ','i':'ᵢ','j':'ⱼ','k':'ₖ','n':'ₙ','m':'ₘ','x':'ₓ','y':'ᵧ',
           '+':'₊','-':'₋'}

SUP_MAP = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹',
           '+':'⁺','-':'⁻','n':'ⁿ','k':'ᵏ','m':'ᵐ','T':'ᵀ','i':'ⁱ','=':'⁼'}


def replace_all(text, mapping):
    for k, v in sorted(mapping.items(), key=lambda x: -len(x[0])):
        text = text.replace(k, v)
    return text


def convert_formula(formula):
    formula = replace_all(formula, L2U)

    # \text{...} → extract inner text
    formula = re.sub(r'\\text\{([^}]*)\}', r'\1', formula)
    # \operatorname{...} → extract inner text
    formula = re.sub(r'\\operatorname\{([^}]*)\}', r'\1', formula)
    # \mathXX{...} → just inner
    formula = re.sub(r'\\math[a-z]+\{([^}]*)\}', r'\1', formula)

    # Subscripts _{...}
    def sub_repl(m):
        inner = m.group(1)
        return ''.join(SUB_MAP.get(c, c) for c in inner)
    formula = re.sub(r'_\{([^}]+)\}', sub_repl, formula)

    # Simple \_ single char
    def sub_single(m):
        c = m.group(1)
        return SUB_MAP.get(c, c)
    formula = re.sub(r'_(\w)', sub_single, formula)

    # Superscripts ^{...}
    def sup_repl(m):
        inner = m.group(1)
        return ''.join(SUP_MAP.get(c, c) for c in inner)
    formula = re.sub(r'\^\{([^}]+)\}', sup_repl, formula)

    # Simple ^ single char
    def sup_single(m):
        c = m.group(1)
        return SUP_MAP.get(c, c)
    formula = re.sub(r'\^(\w)', sup_single, formula)

    # Fractions
    formula = re.sub(r'\\dfrac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', formula)
    formula = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', formula)

    # Cleanup
    formula = formula.replace('{', '').replace('}', '')
    formula = re.sub(r'\s+', ' ', formula).strip()
    return formula


def convert_file(input_text):
    # Display math $$...$$
    def dmath(m):
        inner = m.group(1)
        return '\n\n  ' + convert_formula(inner.strip()) + '\n'
    text = re.sub(r'\$\$\s*(.+?)\s*\$\$', dmath, input_text, flags=re.DOTALL)

    # Inline math $...$
    def imath(m):
        inner = m.group(1)
        return convert_formula(inner)
    text = re.sub(r'\$(.+?)\$', imath, text)

    # Cleanup
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


if __name__ == '__main__':
    if len(sys.argv) < 2:
        content = sys.stdin.read()
    else:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            content = f.read()

    converted = convert_file(content)
    print(converted)
