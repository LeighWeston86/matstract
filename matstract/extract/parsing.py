import re
import collections
from chemdataextractor.doc import Document, Paragraph, Title
from pymatgen.core.periodic_table import Element
from pymatgen.core.composition import Composition, CompositionError


class MaterialParser:
    def __init__(self):
        self.list_of_elements_1 = ['H', 'B', 'C', 'N', 'O', 'F', 'P', 'S', 'K', 'V', 'Y', 'I', 'W', 'U']
        self.list_of_elements_2 = ['He', 'Li', 'Be', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'Cl', 'Ar', 'Ca', 'Sc', 'Ti', 'Cr',
                                   'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr',
                                   'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'Xe',
                                   'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er',
                                   'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi',
                                   'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf',
                                   'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn',
                                   'Fl', 'Lv']

    def get_sym_dict(self, f, factor):
        sym_dict = collections.defaultdict(str)
        r = "([A-Z]{1}[a-z]{0,1})\s*([-*\.\da-z\+/]*)"
        for m in re.finditer(r, f):

            """
            checking for correct elements names
            """
            el_bin = "{0}{1}".format(str(int(m.group(1)[0] in self.list_of_elements_1 + ['M'])), str(
                int(m.group(1) in self.list_of_elements_1 + self.list_of_elements_2 + ['Ln', 'M'])))
            if el_bin in ['01', '11']:
                el = m.group(1)
                amt = m.group(2)
            if el_bin in ['10', '00']:
                el = m.group(1)[0]
                amt = m.group(1)[1:] + m.group(2)

            if len(sym_dict[el]) == 0:
                sym_dict[el] = "0"
            if amt.strip() == "":
                amt = "1"
            sym_dict[el] = '(' + sym_dict[el] + ')' + '+' + '(' + amt + ')' + '*' + '(' + str(factor) + ')'
            f = f.replace(m.group(), "", 1)
        if f.strip():
            print("{} is an invalid formula!".format(f))

        """
        refinement of non-variable values
        """
        for el, amt in sym_dict.items():
            if len(re.findall('[a-z]', amt)) == 0:
                sym_dict[el] = str(round(eval(amt), 3))

        return sym_dict

    def parse_formula(self, formula):
        """
        Args:
            formula (str): A string formula, e.g. Fe2O3, Li3Fe2(PO4)3

        Returns:
            Composition with that formula.
        """
        formula_dict = collections.defaultdict(str)
        r = "\(([^\(\)]+)\)\s*([-*\.\da-z\+/]*)"

        for m in re.finditer(r, formula):
            factor = "1"
            if m.group(2) != "":
                factor = m.group(2)
            unit_sym_dict = self.get_sym_dict(m.group(1), factor)
            for el, amt in unit_sym_dict.items():
                if len(formula_dict[el]) == 0:
                    formula_dict[el] = amt
                else:
                    formula_dict[el] = '(' + formula_dict[el] + ')' + '+' + '(' + amt + ')'

            formula = formula.replace('(' + m.group(1) + ')' + m.group(2), '', 1)

        # if there is coefficient before formula, change factor
        unit_sym_dict = self.get_sym_dict(formula, "1")
        for el, amt in unit_sym_dict.items():
            if len(formula_dict[el]) == 0:
                formula_dict[el] = amt
            else:
                formula_dict[el] = '(' + formula_dict[el] + ')' + '+' + '(' + amt + ')'

        """
        refinement of non-variable values
        """
        incorrect = []
        for el, amt in formula_dict.items():
            if len(re.findall('[a-z]', amt)) == 0:
                formula_dict[el] = str(round(eval(amt), 3))
            if any(len(c) > 1 for c in re.findall('[A-Za-z]+', formula_dict[el])):
                incorrect.append(el)

        for el in incorrect:
            del formula_dict[el]

        return formula_dict

    def get_formula_structure(self, formula):
        # check if material name or formula
        # check [/, :] in formula

        init_formula = formula
        formula = formula.replace(' ', '')
        formula = formula.replace('−', '-')

        elements_variables = collections.defaultdict(str)
        stoichiometry_variables = collections.defaultdict(str)

        # check for any weird syntax
        r = "\(([^\(\)]+)\)\s*([-*\.\da-z\+/]*)"
        for m in re.finditer(r, formula):
            if not m.group(1).isupper() and m.group(2) == '':
                formula = formula.replace('(' + m.group(1) + ')', m.group(1), 1)
            if ',' in m.group(1):
                elements_variables['M'] = re.split(',', m.group(1))
                formula = formula.replace('(' + m.group(1) + ')' + m.group(2), 'M' + m.group(2), 1)

        composition = self.parse_formula(formula)

        # looking for variables in elements and stoichiometry
        for el, amt in composition.items():
            if el not in self.list_of_elements_1 + self.list_of_elements_2 + list(elements_variables.keys()):
                elements_variables[el] = []
            for var in re.findall('[a-z]', amt):
                stoichiometry_variables[var] = []

        formula_structure = dict(
            formula_=init_formula,
            formula=formula,
            composition=composition,
            stoichiometry_vars=stoichiometry_variables,
            elements_vars=elements_variables,
            targets=[]
        )

        return formula_structure

    def get_values(self, string, mode, count=None, default_value=0.1, incr=None):
        values = []

        """
        given range
        """
        if mode == 'range' and len(string) != 0:
            string = string[0]
            if any(c in string for c in ['-', '–']):
                interval = re.split('[-–]', string)
            else:
                interval = [string[0], string[1]]

            if len(interval) > 0:
                start = float(interval[0])
                end = float(interval[1])
                if incr != None:
                    values = [round(start + i * incr, 2) for i in range(round((end - start) / incr))]

                if count != None:
                    incr = (end - start) / count
                    values = [round(start + i * incr, 2) for i in range(count)]

                if incr == None and count == None:
                    values = [default_value]

        """
        given list
        """
        if mode == 'values' and len(string) != 0:
            values = [round(float(c), 2) for c in re.findall('[0-9.]+', string[0])]

        return values

    def get_stoichiometric_values(self, var, sentence):
        values = []
        # equal to exact values
        if len(values) == 0:
            values = self.get_values(re.findall(var + '\s*=\s*([0-9.,and\s]+)[\s\)\]]', sentence), mode='values')
        # equal to range
        if len(values) == 0:
            values = self.get_values(re.findall(var + '\s*=\s*([0-9-–.\s]+)[\s\)\]]', sentence), mode='range', count=5)
        # within range
        if len(values) == 0:
            values = self.get_values(
                re.findall('([0-9\.\s]*)\s*[<≤]{0,1}\s*' + var + '\s*[<≤>]{1}\s*([0-9.\s]+)[\s\)\]\.]', sentence),
                mode='range', count=5)

        return values

    def get_elements_values(self, var, sentence):
        values = re.findall(var + '\s*=\s*([A-Za-z,\s]+)', sentence)
        if len(values) > 0:
            values = [c for c in re.split('[,\s]', values[0]) if c in self.list_of_elements_1 + self.list_of_elements_2]

        return values

    def replace_stoichiometry(self, string, variable, amount):
        new_string = '0'
        if len(re.findall('([0-9]*[a-z]*)' + variable, string)) != 0:
            if re.findall('([0-9]*[a-z]*)' + variable, string)[0] != '':
                new_string = string.replace(variable, '*' + str(amount))
        else:
            new_string = string.replace(variable, str(amount))

        return new_string

    def substitute_elements(self, structure):
        output = []
        for elem, values in structure['elements_vars'].items():
            # print('For element', elem, values)
            for v in values:
                target = dict(structure['composition'])
                target[v] = target[elem]
                del target[elem]
                output.append(dict(
                    formula_=structure['formula_'],
                    formula=structure['formula'],
                    composition=dict(target),
                    stoichiometry_vars=structure['stoichiometry_vars'],
                    elements_vars=structure['elements_vars'],
                    targets=structure['targets']
                ))

        return output

    def substitute_stoichiometry(self, structure):
        output = []
        for var, amounts in structure['stoichiometry_vars'].items():
            for amt in amounts:
                target_var = dict(structure['composition'])
                for el in target_var:
                    target_var[el] = eval(self.replace_stoichiometry(target_var[el], var, amt))
                output.append(target_var)

        return output

    def test_parsing(self, material_name, sentence):
        formula_structure = self.get_formula_structure(material_name)

        # find stoichiometric variables in text
        for var in list(formula_structure['stoichiometry_vars'].keys()):
            if len(formula_structure['stoichiometry_vars'][var]) == 0:
                formula_structure['stoichiometry_vars'][var] = self.get_stoichiometric_values(var, sentence)

        # find element variables
        for var in list(formula_structure['elements_vars'].keys()):
            if len(formula_structure['elements_vars'][var]) == 0:
                formula_structure['elements_vars'][var] = self.get_elements_values(var, sentence)

        # substitute
        targets = self.substitute_elements(formula_structure)

        if len(targets) == 0:
            targets.append(dict(
                formula_=formula_structure['formula_'],
                formula=formula_structure['formula'],
                composition=formula_structure['composition'],
                stoichiometry_vars=formula_structure['stoichiometry_vars'],
                elements_vars=formula_structure['elements_vars'],
                targets=formula_structure['targets']
            ))

        for target in targets:
            formula_structure['targets'].extend(dict(t) for t in self.substitute_stoichiometry(target))

        return formula_structure

    def make_pretty(self, formula):
        pretty_formula = ''
        for key in formula.keys():
            if formula[key] == "1":
                pretty_formula += key
            else:
                pretty_formula += key + formula[key]
        # pretty_formula = [key+formula[key] if formula[key] != 1 else key for key in formula.keys()]
        print(pretty_formula)
        return pretty_formula


class SimplifiedMaterialParser:
    def __init__(self):
        self.name = "ImprovedMaterialParser"

    def is_element(self, element):
        try:
            Element(element)
            return True
        except:
            return False

    def parse_formula(self, formula):

        try:
            composition = Composition(formula)

        except CompositionError:
            print("need a better parser!")

        if any([not self.is_element(key) for key in composition.keys()]):
            print("need to handle substitution")

        # if "(" and ")" in formula:
        # separate by elements and trailing expressions
        bits = re.findall('[A-Z][^A-Z]*', formula)
        parsed_formula = {}
        for bit in bits:
            if self.is_element(bit):
                parsed_formula[bit] = 1
            elif self.is_element(bit[0:2]):
                parsed_formula[bit[0:2]] = bit[2::]
            elif self.is_element(bit[0]):
                parsed_formula[bit[0]] = bit[1::]
            else:
                raise ValueError("Formula contains non-element.")

    # def is_chemical_formula(self, composition):
    #     current_element=''
    #     for letter in composition:
    #         if letter.isupper():
    #             current_element =


class TextParser:

    def __init__(self):
        self.name = "Parser"

    def extract_chemdata(self, text):
        doc = Document(text)
        cems = doc.cems
        chem_mentions = doc.records.serialize()
        materials = []
        for chem in chem_mentions:
            materials.append(chem["names"])
        # print(cems)
        # extracted_materials = []
        return materials


def extract_materials(text):
    P = TextParser()
    M = MaterialParser()
    materials = P.extract_chemdata(text)
    extracted_materials = []
    for material_names in materials:
        newnames = []
        for name in material_names:
            print("Trying ", name)
            possible_material = M.make_pretty(M.parse_formula(name))
            if possible_material == '':
                possible_material = name
            #     print(possible_material)
            # except:
            #     possible_material = name
            #     print("still adding {}".format(possible_material))
            newnames.append(possible_material)
        newname = "{}{}".format(newnames[0], " " + str(newnames[1:] if len(newnames) > 1 else ""))
        extracted_materials.append(newname)
    # print("extracted:", extracted_materials)
    return extracted_materials


def test_text_parsing():
    hard_text = """New TbFeAs(O,F) and DyFeAs(O,F) superconductors with critical temperatures Tc = 46 and 45 K and very 
    high critical fields, ≥100 T, have been prepared at 1100–1150 °C and 10–12 GPa, demonstrating that high pressure may 
    be used to synthesise late rare earth derivatives of the recently reported RFeAs(O,F) (R = La–Nd, Sm, Gd) high 
    temperature superconductors."""
    hard_text_materials = ["TbFeAsO", "TbFeAsF", "DyFeAsO", "DyFeAsF", "LaFeAsO", "CeFeAsO", "PrFeAsO", "NdFeAsO",
                           "SmFeAsO", "GdFeAsO", "LaFeAsF", "CeFeAsF", "PrFeAsF", "NdFeAsF", "SmFeAsF", "GdFeAsF"]

    easy_text = """From 1997 to present, continuous efforts have been made to 
    understand and improve the performance of LiFePO4. """
    easy_materials = "LiFePO4"

    P = TextParser()
    M = MaterialParser()
    # print(M.test_parsing(material_name="TbFeAsO", sentence="""New TbFeAs(O,F) and DyFeAs(O,F) superconductors with critical temperatures Tc = 46 and 45 K and very
    # high critical fields, ≥100 T, have been prepared at 1100–1150 °C and 10–12 GPa, demonstrating that high pressure may
    # be used to synthesise late rare earth derivatives of the recently reported RFeAs(O,F) (R = La–Nd, Sm, Gd) high
    # temperature superconductors."""))
    P.extract_chemdata(easy_text)
    P.extract_chemdata(hard_text)
    print(M.parse_formula("LiFePO4"))
    print(M.parse_formula(("LFP")))


if __name__ == "__main__":
    test_text_parsing()