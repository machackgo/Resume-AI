import copy, unittest
from stage4c1.selection import *

def evidence(n=80):
    return [{'id':str(i),'expected':'UNKNOWN','predicted':'UNKNOWN','raw_predicted':'UNKNOWN',
             'schema_valid':True,'contract_valid':True,'citations':1,'valid_citations':1,
             'entailed_citations':1,'top_level_citations':1,'valid_top_level_citations':1,
             'fabricated_ids':0,'overclaimed_atoms':0} for i in range(n)]

def professional():
    return {'grounding_safe':True,'critical_violation_cases':0,
            'n':14,'cases':[{'id':str(i)} for i in range(14)],
            'measurements':{k:{'rate':1,'correct':1,'total':1,'unassessed_cases':0} for k in MEASUREMENTS}}

def suite():
    return {'evidence_ids':[str(i) for i in range(80)],'professional_ids':[str(i) for i in range(14)]}

class SelectionTests(unittest.TestCase):
    def test_same_model_passes(self):
        rows=evidence(); result=grounding_gates(rows,{'base':rows,'evidence_only':rows},professional(),suite())
        self.assertTrue(result['eligible'])

    def test_two_errors_exceed_two_point_gate(self):
        base=evidence(); candidate=copy.deepcopy(base)
        for row in candidate[:2]: row['predicted']='UNSUPPORTED'
        result=grounding_gates(candidate,{'base':base,'evidence_only':base},professional(),suite())
        self.assertIn('ACCURACY_REGRESSION:base',result['failures'])

    def test_atomic_overclaim_cannot_hide_in_aggregate_accuracy(self):
        base=evidence();candidate=copy.deepcopy(base);candidate[0]['overclaimed_atoms']=1
        result=grounding_gates(candidate,{'base':base,'evidence_only':base},professional(),suite())
        self.assertFalse(result['eligible']);self.assertIn('ATOMIC_OVERCLAIM_REGRESSION:base',result['failures'])

    def test_unassessed_is_not_perfect(self):
        rows=evidence(); pro=professional(); pro['measurements']['numeric_fidelity']['rate']=None
        result=grounding_gates(rows,{'base':rows,'evidence_only':rows},pro,suite())
        self.assertFalse(result['eligible']); self.assertIn('NOT_ASSESSED:numeric_fidelity',result['inconclusive'])

    def test_partial_review_cannot_hide_behind_perfect_rate(self):
        rows=evidence(); pro=professional(); pro['measurements']['numeric_fidelity']['unassessed_cases']=1
        result=grounding_gates(rows,{'base':rows,'evidence_only':rows},pro,suite())
        self.assertFalse(result['eligible']); self.assertIn('INCOMPLETE_REVIEW:numeric_fidelity',result['inconclusive'])

    def test_matching_but_unregistered_subsets_rejected(self):
        rows=evidence(79)
        with self.assertRaises(AssertionError): grounding_gates(rows,{'base':rows,'evidence_only':rows},professional(),suite())

    def test_final_uses_complete_test_with_base_only(self):
        rows=evidence(160);pro=professional();pro.update(n=16,cases=[{'id':str(i)} for i in range(16)])
        final_suite={'evidence_ids':[str(i) for i in range(160)],'professional_ids':[str(i) for i in range(16)]}
        self.assertTrue(grounding_gates(rows,{'base':rows},pro,final_suite,phase='final')['eligible'])
        with self.assertRaises(AssertionError): grounding_gates(evidence(),{'base':evidence()},professional(),suite(),phase='final')

    def test_pair_membership_must_match(self):
        with self.assertRaises(AssertionError): paired(evidence(80),evidence(79),lambda x:1)

    def test_invalid_output_cannot_get_quality(self):
        packet={'cases':[{'id':'x','output_sha256':'hash','schema_valid':False,'generation_complete':True,'automatic_errors':['SCHEMA']}]}
        case={'id':'x','output_sha256':'hash','grounding_score':0,'critical_violations':[],
              'assessment':'Invalid schema; claims cannot be assessed.', 'rubric':{k:4 for k in DIMENSIONS},
              'measurements':{k:None for k in MEASUREMENTS}}
        with self.assertRaises(AssertionError): professional_review(packet,{'cases':[case]})
        case['rubric']={k:0 for k in DIMENSIONS}
        self.assertFalse(professional_review(packet,{'cases':[case]})['grounding_safe'])

    def test_no_final_case_exclusion(self):
        with self.assertRaises(AssertionError): primary_professional_gate({'n':15},{'n':16})

    def test_perfect_prose_does_not_override_fidelity(self):
        candidate=professional();candidate.update(n=16,quality_mean=4,cases=[{'id':str(i),'quality_mean':4,'rubric':{k:4 for k in DIMENSIONS}} for i in range(16)])
        base={'n':16,'cases':[{'id':str(i),'quality_mean':3} for i in range(16)]}
        candidate['measurements']['numeric_fidelity']['rate']=.5
        self.assertFalse(primary_professional_gate(candidate,base)['passed'])

    def test_failed_validation_cannot_be_promoted_on_test(self):
        challenge=professional();challenge['n']=6
        checks={k:True for k in ('protected_artifacts_unchanged','reload_reproducible','base_recovery','no_test_leakage','historical_grounding_gate','development_frozen','validation_eligible')}
        checks['validation_eligible']=False
        result=final_promotion({'eligible':True},{'passed':True},challenge,checks)
        self.assertFalse(result['promote']);self.assertEqual(result['retained_model'],'base')

    def test_early_stop_strict_boundary(self):
        base=evidence(); candidate=copy.deepcopy(base)
        for row in candidate[:4]: row['predicted']='UNSUPPORTED'
        self.assertFalse(early_stop(candidate,base,professional(),professional())['stop_required'])
        candidate[4]['predicted']='UNSUPPORTED'
        self.assertTrue(early_stop(candidate,base,professional(),professional())['stop_required'])

if __name__=='__main__': unittest.main()
