from matstract.utils import open_db_connection
from chemdataextractor.doc import Paragraph
from gensim.utils import deaccent
from matstract.extract import parsing
from tqdm import tqdm
import zipfile
import os
import regex
import pickle
from pymatgen.core.composition import Composition
from monty.fractions import gcd_float


class DataPreparation:
    RAW_ABSTRACT_COL = "abstracts"
    TOK_ABSTRACT_COL = "abstract_tokens"
    TTL_FILED = "title"
    ABS_FIELD = "abstract"
    DOI_FIELD = "doi"

    UNITS = ['K', 'h', 'V', 'wt', 'wt.', 'MHz', 'kHz', 'GHz', 'days', 'weeks',
             'hours', 'minutes', 'seconds', 'T', 'MPa', 'GPa', 'at.', 'mol.',
             'at', 'm', 'N', 's-1', 'vol.', 'vol', 'eV', 'A', 'atm', 'bar',
             'kOe', 'Oe', 'h.', 'mWcm−2', 'keV', 'MeV', 'meV', 'day', 'week', 'hour',
             'minute', 'month', 'mo,nths', 'year', 'cycles', 'years', 'fs', 'ns',
             'ps', 'rpm', 'g', 'mg', 'mAcm−2', 'mA', 'mK', 'mT', 's-1', 'dB',
             'Ag-1', 'mAg-1', 'mAg−1', 'mAg', 'mAh', 'mAhg−1', 'm-2', 'mJ', 'kJ',
             'm2g−1', 'THz', 'KHz', 'kJmol−1', 'Torr', 'gL-1', 'Vcm−1', 'mVs−1',
             'J', 'GJ', 'mTorr', 'bar', 'cm2', 'mbar', 'kbar', 'mmol', 'mol', 'molL−1',
             'MΩ', 'Ω', 'kΩ', 'mΩ', 'mgL−1', 'moldm−3', 'm2', 'm3', 'cm-1', 'cm',
             'Scm−1', 'Acm−1', 'eV−1cm−2', 'cm-2', 'sccm', 'cm−2eV−1', 'cm−3eV−1',
             'kA', 's−1', 'emu', 'L', 'cmHz1', 'gmol−1', 'kVcm−1', 'MPam1',
             'cm2V−1s−1', 'Acm−2', 'cm−2s−1', 'MV', 'ionscm−2', 'Jcm−2', 'ncm−2',
             'Jcm−2', 'Wcm−2', 'GWcm−2', 'Acm−2K−2', 'gcm−3', 'cm3g−1', 'mgl−1',
             'mgml−1', 'mgcm−2', 'mΩcm', 'cm−2s−1', 'cm−2', 'ions', 'moll−1',
             'nmol', 'psi', 'mol·L−1', 'Jkg−1K−1', 'km', 'Wm−2', 'mass', 'mmHg',
             'mmmin−1', 'GeV', 'm−2', 'm−2s−1', 'Kmin−1', 'gL−1', 'ng', 'hr', 'w',
             'months', 'mN', 'kN', 'Mrad', 'rad', 'arcsec', 'Ag−1', 'dpa', 'cdm−2',
             'cd', 'mcd', 'mHz', 'm−3', 'ppm', 'phr', 'mL', 'ML', 'mlmin−1', 'MWm−2',
             'Wm−1K−1', 'Wm−1K−1', 'kWh', 'Wkg−1', 'Jm−3', 'm-3', 'gl−1', 'A−1',
             'Ks−1', 'mgdm−3', 'mms−1', 'ks', 'appm', 'ºC', 'HV', 'kDa', 'Da', 'kG',
             'kGy', 'MGy', 'Gy', 'mGy', 'Gbps']

    ELEMENTS = ['H', 'B', 'C', 'N', 'O', 'F', 'P', 'S', 'K', 'V', 'Y', 'I', 'W', 'U',
                'He', 'Li', 'Be', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'Cl', 'Ar', 'Ca', 'Sc', 'Ti', 'Cr',
                'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr',
                'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'Xe',
                'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er',
                'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi',
                'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf',
                'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn',
                'Fl', 'Lv']

    NR_UNIT = regex.compile(r'^([\d.?]+)([\p{script=Latin}]+.*)', regex.DOTALL)

    ROMAN_NR_PR = regex.compile(r'\(I+V?\)')

    def __init__(self, db_name="matstract_db", local=True):
        self._db = open_db_connection(local=local, db=db_name)
        self.parser = parsing.MaterialParser()
        self.simple_parser = parsing.SimpleParser()
        self.mat_list = []
    """
    Provides tools for converting the data in the database to suitable
    format for machine learning tasks
    """
    def to_word2vec_zip(self, filepath=None, limit=None, newlines=False, line_per_abstract=False):
        """
        Coverts the tokenized abstracts in the database to a zip file with a single vocabulary line.
        :param limit: number of abstracts to use. If not specified, all data will be considered
        :return: a 2d list of words from the abstract / titles, with each abstract on a separate line
        """
        abstracts = self._get_abstracts(limit=limit, col=self.TOK_ABSTRACT_COL)
        txt = ""
        if line_per_abstract:
            nl_tok = ""
        elif newlines:
            nl_tok = "\n"
        else:
            nl_tok = ""

        for i, abstract in enumerate(abstracts):
            print("processing abstract {}".format(i), end="\r")
            ttl = abstract[self.TTL_FILED]
            abs = abstract[self.ABS_FIELD]
            if ttl is not None and abs is not None:
                for sentence in ttl:
                    txt += " ".join(self.process_sentence(sentence) + [nl_tok])
                for sentence in abs:
                    txt += " ".join(self.process_sentence(sentence) + [nl_tok])
            if line_per_abstract:
                txt += "\n"
        text = txt

        if filepath is None:
            zip_path = os.getcwd()
        else:
            zip_path = filepath
        filename = "abstracts.zip"

        print("%s created at %s" % (filename, zip_path))
        zf = zipfile.ZipFile(os.path.join(zip_path, "abstracts.zip"), "w")
        zf.writestr("/abstracts", text)
        DataPreparation.save_obj(self.material_counts(), "formula")
        zf.write("formula.pkl")
        os.remove("formula.pkl")

    def tokenize_abstracts(self, limit=None, override=False):
        def tokenize(text):
            """
            Returns a 1d list of tokens using chemdataextractor tokenizer. Removes all punctuation but
            keeps the structure of sentences.
            """
            cde_p = Paragraph(text)
            tokens = cde_p.tokens
            toks = []
            for sentence in tokens:
                toks.append([])
                for tok in sentence:
                    toks[-1].append(tok.text)
            return toks

        # get the abstracts
        abstracts = self._get_abstracts(limit=limit)
        existing_dois = [abstr[self.DOI_FIELD] for abstr in self._get_abstracts(col=self.TOK_ABSTRACT_COL)]

        count = abstracts.count() if limit is None else limit

        def insert_abstract(a):
            if override or (not override and a[self.DOI_FIELD] not in existing_dois):
                # saving time by not tokenizing the text if abstract already exists
                try:
                    abs_tokens = {
                        self.DOI_FIELD: a[self.DOI_FIELD],
                        self.TTL_FILED: tokenize(a[self.TTL_FILED]),
                        self.ABS_FIELD: tokenize(a[self.ABS_FIELD]),
                    }
                except Exception as e:
                    print("Exception type: %s, doi: %s" % (type(e).__name__, a[self.DOI_FIELD]))
                    abs_tokens = {
                        self.DOI_FIELD: a[self.DOI_FIELD],
                        self.TTL_FILED: None,
                        self.ABS_FIELD: None,
                        "error": "%s: %s " % (type(e).__name__, str(e))
                    }
                if override:
                    # getattr(self._db, self.TOK_ABSTRACT_COL).insert_one(abs_tokens)
                    getattr(self._db, self.TOK_ABSTRACT_COL).replace_one({
                        "doi": a[self.DOI_FIELD]},
                        abs_tokens,
                        upsert=True)
                else:
                    try:
                        # we have already filtered so there should not be doi overlap
                        getattr(self._db, self.TOK_ABSTRACT_COL).insert_one(abs_tokens)
                    except Exception as e:
                        print("Exception type: %s, doi: %s" % (type(e).__name__, a[self.DOI_FIELD]))

        # tokenize and insert into the new collection (doi as unique key)
        for abstract in tqdm(abstracts, total=count):
            insert_abstract(abstract)

        # # with Pool() as p:
        # list(tqdm(parmap(insert_abstract, abstracts), total=count))

    def _get_abstracts(self, limit=None, col=None):
        """
        Returns a cursor of abstracts form mongodb
        :param limit:
        :return:
        """
        if col is None:
            col = self.RAW_ABSTRACT_COL
        if limit is not None:
            abstracts = getattr(self._db, col).aggregate([{"$sample": {"size": limit}}], allowDiskUse=True)
        else:
            abstracts = getattr(self._db, col).find()
        return abstracts

    @staticmethod
    def is_number(t):
        try:
            float(t.replace(',', ''))  # also considering digits separated with commas
            return True
        except ValueError:
            return False

    # @staticmethod
    def process_sentence(self, s):
        st = []
        for tok in s:
            if DataPreparation.is_number(tok):
                tok = "<nUm>"  # replace all numbers with a string <nUm>
            else:
                if self.is_simple_formula(tok):
                    formula = self.get_norm_formula(tok)
                    self.mat_list.append((tok, formula))
                    tok = formula
                elif (len(tok) == 1 or (len(tok) > 1 and tok[0].isupper() and tok[1:].islower())) \
                        and tok not in self.ELEMENTS and tok not in self.UNITS:
                    # to lowercase if only first letter is uppercase (chemical elements already covered above)
                    tok = deaccent(tok.lower())
                else:
                    # splitting units from numbers (e.g. you can get 2mol., 3V, etc..)
                    nr_unit = self.NR_UNIT.match(tok)
                    if nr_unit is None or nr_unit.group(2) not in self.UNITS:
                        tok = deaccent(tok)  # matches the pattern but not in the list of units
                    else:
                        # splitting the unit from number
                        st.append("<nUm>")
                        tok = deaccent(nr_unit.group(2))
            st.append(tok)
        return st

    def material_counts(self):
        counts = dict()
        for mat in self.mat_list:
            if mat[1] not in counts:
                counts[mat[1]] = dict()
                counts[mat[1]][mat[0]] = 1
            elif mat[0] not in counts[mat[1]]:
                counts[mat[1]][mat[0]] = 1
            else:
                counts[mat[1]][mat[0]] += 1
        return counts

    def is_simple_formula(self, text):
        if self.ROMAN_NR_PR.search(text) is not None:
            # contains roman numbers up to IV in parenthesis
            # related to valence state, so dont want to mix with I and V elements
            return False
        elif any(char.isdigit() or char.islower() for char in text):
            # has to contain at least one lowercase letter or at least one number (to ignore abbreviations)
            try:
                composition = Composition(text)
                # has to contain more than one element
                if len(composition.keys()) < 2 or any([not self.simple_parser.is_element(key) for key in composition.keys()]):
                    return False
                return True
            except Exception:
                return False
        else:
            return False

    def get_ordered_integer_formula(self, el_amt, max_denominator=1000):
        # return alphabetically ordered formula with integer fractions
        g = gcd_float(list(el_amt.values()), 1 / max_denominator)
        d = {k: round(v / g) for k, v in el_amt.items()}
        formula = ""
        for k in sorted(d):
            if d[k] > 1:
                formula += k + str(d[k])
            else:
                formula += k
        return formula

    def get_norm_formula(self, text):
        try:
            # using Olga's parser
            formula_dict = dict(self.parser.parse_formula(text))
            for key in formula_dict:
                formula_dict[key] = float(formula_dict[key])
            integer_formula = self.get_ordered_integer_formula(formula_dict)
            return integer_formula
        except Exception:
            return text

    @staticmethod
    def save_obj(obj, name):
        with open(name + '.pkl', 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load_obj(name):
        with open(name + '.pkl', 'rb') as f:
            return pickle.load(f)
