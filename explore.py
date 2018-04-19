from matstract.nlp.data_preparation import DataPreparation
from matstract.extract import parsing
from pymatgen.core.composition import Composition
from monty.fractions import gcd_float
import regex

simple_parser = parsing.SimpleParser()
parser = parsing.MaterialParser()


def is_simple_formula(text):
    try:
        composition = Composition(text)
        if any([not simple_parser.is_element(key) for key in composition.keys()]):
            return False
        return True
    except Exception:
        return False


def get_ordered_integer_formula(el_amt, max_denominator=1000):
    g = gcd_float(list(el_amt.values()), 1 / max_denominator)
    d = {k: round(v / g) for k, v in el_amt.items()}
    formula = ""
    for k in sorted(d):
        if d[k] != 1:
            formula += k + str(d[k])
        else:
            formula += k
    return formula


dp = DataPreparation()
sentence = ["blabla", "TiO2", "Si(O2H)3(TiO2)2", "1mL",
            "1Mg", "2g", "3mol.", "PBO", "O", "Al224", "LiNi0.5Mn1.5O4", "LiMn1.5Ni0.5O4",
            "III", "VII", "LixCay", "SiO2N2", "Si(OH)4", "Li3Fe2(PO4)3"]
print(parser.parse_formula("Si(O(NH)2H)4P2"))

parsed_sentence = []
for token in sentence:
    if is_simple_formula(token):
        formula_dict = dict(parser.parse_formula(token))
        for key in formula_dict:
            formula_dict[key] = float(formula_dict[key])
        integer_formula = get_ordered_integer_formula(formula_dict)
        parsed_sentence.append(integer_formula)
    else:
        parsed_sentence.append(token)

print(parsed_sentence)

formulas = dp.load_obj("abstracts/formula")

i = 0
for key in sorted(formulas, reverse=False):
    if i < 20000:
        print(key, formulas[key])
        i += 1
    else:
        break

ROMAN_NR_PR = regex.compile(r'\(I+V?\)')
print(ROMAN_NR_PR.search("Ag(III)"))