from matstract.utils import open_db_connection
from chemdataextractor.doc import Paragraph
from tqdm import tqdm
from matstract.nlp.utils import process_sentence
import zipfile
import os

ELEMENTS = ['H', 'B', 'C', 'N', 'O', 'F', 'P', 'S', 'K', 'V', 'Y', 'I', 'W', 'U',
            'He', 'Li', 'Be', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'Cl', 'Ar', 'Ca', 'Sc', 'Ti', 'Cr',
            'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr',
            'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'Xe',
            'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er',
            'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi',
            'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf',
            'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn',
            'Fl', 'Lv']


class DataPreparation:
    RAW_ABSTRACT_COL = "abstracts"
    TOK_ABSTRACT_COL = "abstract_tokens"
    TTL_FILED = "title"
    ABS_FIELD = "abstract"
    DOI_FIELD = "doi"

    def __init__(self, db_name="matstract_db", local=True):
        self._db = open_db_connection(local=local, db=db_name)
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

        for abstract in abstracts:
            ttl = abstract[self.TTL_FILED]
            abs = abstract[self.ABS_FIELD]
            if ttl is not None and abs is not None:
                for sentence in ttl:
                    txt += " ".join(process_sentence(sentence, elements=ELEMENTS) + [nl_tok])
                for sentence in abs:
                    txt += " ".join(process_sentence(sentence, elements=ELEMENTS) + [nl_tok])
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
