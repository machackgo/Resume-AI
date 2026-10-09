"""Post-validation contract regressions; synthetic examples, no benchmark IDs."""
import json
import sys
import unittest
from pathlib import Path

D = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(D / 'application'))
from resume_pipeline.reselection import exclusions, quote_key


class DiscoveryLicenseBoundary(unittest.TestCase):
    def proposal(self):
        return dict(evidence_id='canonical_proposal', quote='Designed a typed web interface for authenticated account views.',
                    requirement_ids=['frontend_requirement'])

    def test_discovery_bookkeeping_cannot_veto_unlicensed_pair(self):
        q = self.proposal()
        review = dict(quote=q, accepted=False,
                      reason='Discovery did not associate this citation with the target query.')
        denied, links = exclusions([review], [])
        self.assertNotIn(quote_key(q['quote']), denied)
        self.assertNotIn((quote_key(q['quote']), 'frontend_requirement'), links,
                         'No independent license has evaluated this canonical evidence/requirement pair.')

    def test_independent_link_rejection_stays_scoped(self):
        q = self.proposal()
        denied, links = exclusions([dict(quote=q, accepted=False, support='NOT_ASSESSED',
                                        link_only_rejection=True)], [])
        self.assertNotIn(quote_key(q['quote']), denied)
        self.assertIn((quote_key(q['quote']), 'frontend_requirement'), links)

    def test_factual_contradiction_remains_blocked(self):
        q = self.proposal()
        denied, _ = exclusions([dict(quote=q, accepted=False, support='CONTRADICTED', eligibility='F')], [])
        self.assertIn(quote_key(q['quote']), denied)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DiscoveryLicenseBoundary)
    with (D / 'discovery-license-regression.log').open('x') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = dict(tests_run=result.testsRun,
                  passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
                  failed=len(result.failures)+len(result.errors), skipped=len(result.skipped),
                  failures=[dict(test=str(t), error=e) for t,e in result.failures+result.errors],
                  purpose='New general contract regression derived from independent full-suite audit; application unchanged.')
    with (D / 'discovery-license-regression-results.json').open('x') as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
