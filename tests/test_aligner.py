import unittest
from power.aligner import PowerAligner, CharToWordAligner
from power.pronounce import PronouncerType
from power.levenshtein import Levenshtein, ExpandedAlignment

def preproc(aligned_string):
    aligned = [x if x != '_' else "" for x in aligned_string.split()]
    words = [x for x in aligned if x]
    return dict(words=words, string=' '.join(words), alignment=aligned)

class test_aligner(unittest.TestCase):

    lex = "lex/cmudict.rep.json"

    def test_power_punct_preservation(self):
        hyp = "so to address this we developed with the doctor brahmin stanford virtual dissection table"
        ref = "So to address this we developed with a Dr. Brown in Stanford virtual dissection table"
        aligner = PowerAligner(ref, hyp, lowercase=True, lexicon=self.lex)
        aligner.align()
        
        print("WER")
        print(aligner.wer_alignment)
        print("POWER")
        print(aligner.power_alignment)

        expected = ref.split()
        actual = aligner.wer_alignment.s1_string().split()
        self.assertEqual(actual, expected)
        actual = aligner.power_alignment.s1_string().split()
        self.assertEqual(actual, expected)

        expected = hyp.split()
        actual = aligner.wer_alignment.s2_string().split()
        self.assertEqual(actual, expected)
        actual = aligner.power_alignment.s2_string().split()
        self.assertEqual(actual, expected)

    def test_power_word_fix(self):
        #hyp = """you might have a low bar pneumonia for example and they could give you"""
        hyp = """an 'anti serum and injection of rabbit anti bodies"""  # to the bacterium streptococcus if the interned sub typed it correctly"""
        #ref = """You might have a lobar pneumonia, for example, and they could give you"""
        ref = """an antiserum, an injection of rabid antibodies"""  # to the bacterium streptococcus, if the intern sub-typed it correctly."""
        aligner = PowerAligner(ref, hyp, lowercase=True, lexicon=self.lex)
        aligner.align()
        
        print("WER")
        print(aligner.wer_alignment)
        print("POWER")
        print(aligner.power_alignment)

        expected = ref.split()
        actual = aligner.wer_alignment.s1_string().split()
        self.assertEqual(actual, expected)
        actual = aligner.power_alignment.s1_string().split()
        self.assertEqual(actual, expected)

        expected = hyp.split()
        actual = aligner.wer_alignment.s2_string().split()
        self.assertEqual(actual, expected)
        actual = aligner.power_alignment.s2_string().split()
        self.assertEqual(actual, expected)

    def test_power_misaligned_asked(self):
        ref = """They said Yes We asked them how happy they were and then we gave them an envelope"""
        hyp = """they said yes we gave we ask them how happy they were and then we gave them on low"""
        aligner = PowerAligner(ref, hyp, lowercase=True, lexicon=self.lex)
        aligner.align()
        # print "WER"
        # print aligner.wer_alignment
        # print "POWER"
        # print aligner.power_alignment

        expected_ref =   ["They",  "said",  "Yes",  "",    "",      "We",  "asked",  "them",  "how",  "happy",  "they",  "were",  "and",  "then",  "we",  "gave",  "them",  "an",  "envelope"]
        expected_hyp =   ["they",  "said",  "yes",  "we",  "gave",  "we",  "ask",    "them",  "how",  "happy",  "they",  "were",  "and",  "then",  "we",  "gave",  "them",  "on",  "low"]
        expected_align = ["C",     "C",     "C",    "I",   "I",     "C",   "S",      "C",     "C",    "C",      "C",     "C",     "C",    "C",     "C",   "C",     "C",     "S",   "S"]
        print(aligner.power_alignment)
        print(expected_align)

        self.assertEqual(expected_align, aligner.power_alignment.align)
        self.assertEqual(expected_ref,   aligner.power_alignment.s1)
        self.assertEqual(expected_hyp,   aligner.power_alignment.s2)

        expected = hyp.split()
        actual = aligner.wer_alignment.s2_string().split()
        self.assertEqual(actual, expected)
        actual = aligner.power_alignment.s2_string().split()
        self.assertEqual(actual, expected)

    def test_power_SS_to_DS(self):
        # TODO: This test currently fails because of number normalization. Need to reintroduce the number normalizer into the codebase.
        expected_ref =   preproc("A  50-year-old     business  man")
        expected_hyp =   preproc("_  fifty year old  business  man")
        expected_align = preproc("D  S               C         C")

        aligner = PowerAligner(expected_ref['string'], expected_hyp['string'], lowercase=True, lexicon=self.lex)
        aligner.align()

        print("WER")
        print(aligner.wer_alignment)
        print ("POWER")
        print(aligner.power_alignment)

        self.assertEqual(expected_align['alignment'], aligner.power_alignment.align)

    def test_power_SS_to_DS_digit(self):
        # TODO: This test currently fails because of number normalization. Need to reintroduce the number normalizer into the codebase.
        expected_ref =   preproc("A  fifty-year-old  business  man")
        expected_hyp =   preproc("_  50 year old     business  man")
        expected_align = preproc("D  S               C         C")

        aligner = PowerAligner(expected_ref['string'], expected_hyp['string'], lowercase=True, lexicon=self.lex)
        aligner.align()

        print("WER")
        print(aligner.wer_alignment)
        print ("POWER")
        print(aligner.power_alignment)

        self.assertEqual(expected_align['alignment'], aligner.power_alignment.align)

    def test_charToWordAlign_extra_hyp_syl_no_overlap(self):
        ref = """_     _   asked""".split()
        hyp = """gave  we  ask""".split()
        align = """I     I   S""".split()

        refwords = ' '.join([r for r in ref if r != '_'])
        hypwords = ' '.join([h for h in hyp if h != "_"])

        ref_phones =   """|  #  _  _   _  _  _  _  _   _  _  ae  s  k  t  |""".split()
        hyp_phones =   """|  #  g  ey  v  |  #  w  iy  |  #  ae  s  k  _  |""".split()
        align_phones = """C  C  I  I   I  I  I  I  I   I  I  C   C  C  D  C""".split()

        ref_phones = [r.replace('_', '') for r in ref_phones]
        hyp_phones = [r.replace('_', '') for r in hyp_phones]

        lev = Levenshtein.align(ref_phones, hyp_phones,
                                PowerAligner.reserve_list, PowerAligner.exclusive_sets)
        lev.editops()
        phone_align = lev.expandAlign()

        # self.assertEqual(phone_align.align, align_phones)

        word_align, phone_align = PowerAligner.phoneAlignToWordAlign(
            refwords.split(), hypwords.split(), ref_phones, hyp_phones)
        self.assertEqual(word_align.align, align)
        self.assertEqual(word_align.s1, [x if x != "_" else "" for x in ref])
        self.assertEqual(word_align.s2, [x if x != "_" else "" for x in hyp])

    def test_charToWordAlign_extra_hyp_syl_overlap(self):
        ref = """_     butchering""".split()
        hyp = """the   maturing""".split()
        align = """I     S""".split()

        refwords = ' '.join([r for r in ref if r != '_'])
        hypwords = ' '.join([h for h in hyp if h != "_"])

        ref_phones   =  """              |  #  b  uh  ch  #      er  #  ih  ng  |""".split()
        hyp_phones   =  """|  #  dh  ax  |  #  m  ax  ch  #  uh  r   #  ih  ng  |""".split()
        align_phones =  """I  I  I   I   C  C  S  S   C   C  I   S   C  C   C   C""".split()

        print(ref_phones)
        print(hyp_phones)

        lev = Levenshtein.align(ref_phones, hyp_phones,
                                PowerAligner.reserve_list, PowerAligner.exclusive_sets)
        lev.editops()
        phone_align = lev.expandAlign()

        word_align, phone_align = PowerAligner.phoneAlignToWordAlign(
            refwords.split(), hypwords.split(), ref_phones, hyp_phones)

        print("POWER")
        print(word_align)
        
        self.assertEqual(word_align.align, align)
        self.assertEqual(word_align.s1, [x if x != "_" else "" for x in ref])
        self.assertEqual(word_align.s2, [x if x != "_" else "" for x in hyp])


if __name__ == "__main__":
    unittest.main()