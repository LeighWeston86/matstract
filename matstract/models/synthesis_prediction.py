import nltk
import pickle
from matstract.extract.parsing import SimpleParser
from matstract.models.database import AtlasConnection
from matstract.models.similar_materials import SimilarMaterials
from nltk.stem import PorterStemmer

class SynthesisPredictor:
    '''
    A materials synthesis prediction tool.

    Usage is as follows:
    >>> sp = SynthesisPredictor()
    >>> summary = sp.get_synthesis_summary('LiFePO4')
    >>> sp.print_synthesis_summary('LiFePO4')
    '''
    def __init__(self):
        #Similar mats
        self.sm = SimilarMaterials()
        # Connect to db
        self.db = AtlasConnection().db
        # Mat parser
        self.parser = SimpleParser()

    def similar_mat_synthesis(self, mat, num_mats=10, num_smt=20):
        '''
        Find similar metraials and print their synthesis methods
        :param mat: stirng; chemical formula
        :param num_mats: int; number of similar materials to consider
        :param num_smt: int; number of synthesis methods to return
        :return: smt_list: list; list of synthesis methods
        '''
        similar_mats = self.sm.get_similar_mats(mat, num_mats)
        smt_list = self.get_synthesis(similar_mats, num_smt)
        return smt_list

    def get_synthesis(self, mat_list, num_smt=20):
        '''
        Get the most common synthesis methods for a list of materials
        :param mat_list: list; list of material formuale
        :param num_smt: int; number of synthesis methods to return
        :return: smt_list: list; list of synthesis methods
        '''
        mat_list_norm = [self.parser.matgen_parser(_mat) for _mat in mat_list]
        docs = list(self.db.ne_norm.find({'MAT': {'$in': mat_list_norm}}))
        num_docs = len(docs)
        SMT = [smt for doc in docs
               for smt in list(set(doc['SMT'])) if smt not in rm_list]
        fd = nltk.FreqDist(SMT)
        smt_list = [(item, score / num_docs) for item, score in fd.most_common(num_smt)]
        return smt_list

    def get_synthesis_summary(self, mat):
        '''
        Get a synthesis summary for a material
        :param mat: string; chemcial formula
        :return: synthesis_summary: dict; a summary of synthesis for the input mat
        '''
        synthesis_summary = {}
        synthesis_summary['mat_synthesis'] = self.get_synthesis([mat])
        synthesis_summary['similar_mats'] = self.sm.get_similar_mats(mat)
        synthesis_summary['similar_mat_synthesis'] = self.similar_mat_synthesis(mat)
        return synthesis_summary

    def print_synthesis_summary(self, mat):
        '''
        Prints a synthesis summary for a material
        :param mat: string; chemical formula
        '''
        # Get the synthesis for the current mat
        print('##############################')
        print('Synthesis summary for {}'.format(mat))
        print('##############################')
        print('\n')

        print('Common synthesis methods for {}:'.format(mat))
        print('-----------------------------------------------------------------------------')
        smt = self.get_synthesis([mat])
        if smt:
            print('{:<70} {:>6}'.format('SMT', 'SCORE'))
            print('-----------------------------------------------------------------------------')
            for smt, score in smt:
                print('{:<70} {:>6.3f}'.format(smt, score))
        else:
            print('{} not found in database...'.format(mat))
        print('\n')

        # Get the similar mats
        print('Similar materials to {}:'.format(mat))
        print('----------')
        similar_mats = self.sm.get_similar_mats(mat)
        print('{:<70}'.format('MAT'))
        print('----------')
        for _mat in similar_mats:
            print('{:<70}'.format(_mat))
        print('\n')

        # Synthesis for similar materials
        print('Common synthesis methods for {} similar materials:'.format(mat))
        print('-----------------------------------------------------------------------------')
        smt = self.similar_mat_synthesis(mat)
        if smt:
            print('{:<70} {:>6}'.format('SMT', 'SCORE'))
            print('-----------------------------------------------------------------------------')
            for smt, score in smt:
                print('{:<70} {:>6.3f}'.format(smt, score))
        else:
            print('{} not found in database...'.format(mat))
        print('\n')

rm_list = ['annealing',
          'coated',
          'annealed',
          'heat treatment',
          'oxidation',
          'anodization',
          'irradiation',
          'visible light irradiation',
          'heating',
          'cooling',
          'humidified'
          'implanted'
          'patterned',
          'implanted',
          'nitridation',
          'oxidation',
          'sulfurization',
          'polished',
          'heat - treated',
          'melting',
          'aging',
          'heated',
          'thermal annealing',
          'thermal treatment',
          'brazing']
stemmer = PorterStemmer()
rm_list += [stemmer.stem(token) for token in rm_list]

if __name__ == '__main__':
    sp = SynthesisPredictor()
    print(sp.get_synthesis_summary('GaN'))
