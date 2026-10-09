"""Prospective input-only catalog tests; no teacher targets are accessed."""
import copy
import hashlib
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from . import contracts
from .grounding import validate_scenario
from .scenarios import digest
from .scenario_catalog_v2 import ROOT, VERSION, PARENTS, generate_catalog, generate_new, read_parents, check_catalog

CATALOG=ROOT/'scenarios/catalog-v2'
def read_rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CatalogV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=generate_catalog()
        cls.parents=read_parents()

    def test_catalog_is_a_replacement_with_bounded_gap_expansion(self):
        self.assertEqual(len(self.parents),143)
        self.assertEqual(len(self.rows),155)
        self.assertEqual(Counter(r['split'] for r in self.rows),{'train':125,'validation':14,'test':16})
        self.assertEqual(sum(r['metadata'].get('new_coverage_family',False) for r in self.rows),12)
        for split in ['train','validation','test']:
            self.assertEqual({r['input']['task'] for r in self.rows if r['split']==split},set(contracts.TASKS))

    def test_seeded_generation_is_reproducible_and_persisted_snapshot_matches(self):
        self.assertEqual(self.rows,generate_catalog())
        self.assertNotEqual(generate_new(seed=1),generate_new(seed=2))
        self.assertEqual(self.rows,read_rows(CATALOG/'catalog.jsonl'))
        self.assertEqual(read_rows(CATALOG/'catalog_inputs.jsonl'),[{'scenario_id':r['scenario_id'],'input':r['input']} for r in self.rows])

    def test_frozen_manifest_checksums_and_parent_inputs_are_preserved(self):
        manifest=json.loads((CATALOG/'manifest.json').read_text())
        self.assertEqual(manifest['version'],VERSION)
        self.assertFalse(manifest['full_teacher_outputs_consulted'])
        self.assertFalse(manifest['teacher_target_generation_performed'])
        self.assertFalse(manifest['pilot_modified'])
        self.assertFalse(manifest['challenge_modified'])
        self.assertFalse(manifest['coverage_saturation_claim'])
        self.assertEqual(manifest['source_sha256'],sha(ROOT/'stage4c0/scenario_catalog_v2.py'))
        self.assertEqual(set(manifest['parents_and_protected_inputs_sha256']),set(PARENTS)|{'pilot.jsonl','challenge.jsonl'})
        for filename,expected in manifest['parents_and_protected_inputs_sha256'].items():self.assertEqual(sha(ROOT/'scenarios'/filename),expected,filename)
        for filename,expected in manifest['sha256'].items():self.assertEqual(sha(CATALOG/filename),expected,filename)

    def test_every_record_has_valid_schema_and_explicit_ground_truth(self):
        self.assertEqual(check_catalog(self.rows)['status'],'PASS')
        for r in self.rows:
            with self.subTest(scenario=r['scenario_id']):
                self.assertEqual(contracts.validate_input(r['input']),[])
                self.assertEqual(validate_scenario(r),[])
                self.assertEqual(r['metadata']['ground_truth_sha256'],digest({'profile':r['input']['profile'],'rag':r['input']['rag'],'oracle':r['oracle']}))
                self.assertFalse(r['metadata']['full_teacher_target_consulted'])
                self.assertFalse(r['metadata']['target_exists_at_ground_truth_creation'])

    def test_original_technical_evidence_job_and_requirement_labels_are_unchanged(self):
        for old,new in zip(self.parents,self.rows[:143]):
            self.assertEqual(new['metadata']['parent_scenario_id'],old['scenario_id'])
            self.assertTrue(new['metadata']['parent_record_persisted'])
            self.assertEqual(new['metadata']['parent_input_sha256'],digest(old['input']))
            self.assertEqual(new['input']['job'],old['input']['job'])
            self.assertEqual(new['input']['rag'],old['input']['rag'])
            self.assertEqual(new['oracle']['requirements'],old['oracle']['requirements'])
            for container in ['input','oracle']:
                if container=='input':
                    a=[f for f in old['input']['profile']['facts'] if f['field']=='claim']
                    b=[f for f in new['input']['profile']['facts'] if f['field']=='claim']
                else:
                    a=[f for f in old['oracle']['facts'] if f['kind']=='claim']
                    b=[f for f in new['oracle']['facts'] if f['kind']=='claim']
                self.assertEqual(a,b)

    def test_education_is_diverse_and_degree_free_is_explicit_without_false_degree(self):
        candidates={r['input']['profile']['candidate_id']:r for r in self.rows if r['input']['profile']['facts']}
        paths={tuple(r['metadata']['education_path']) for r in candidates.values()}
        self.assertGreaterEqual(len(paths),30)
        text=' '.join(p for path in paths for p in path)
        for discipline in ['Statistics','Mathematics','Electrical Engineering','Physics','Ecology','Linguistics','History']:
            self.assertIn(discipline,text)
        degree_free=[]
        for r in candidates.values():
            facts=r['input']['profile']['facts']
            if any(f['field']=='education_status' and f['value']=='No college degree is held.' for f in facts):
                degree_free.append(r)
                self.assertFalse(any(f['field']=='degree' for f in facts))
                self.assertTrue(any(f['field']=='credential' and 'non-degree' in f['value'] for f in facts))
                self.assertNotIn('EDUCATION',r['input']['constraints']['required_sections'])
        self.assertGreaterEqual(len(degree_free),3)

    def test_project_title_origin_and_career_chronology_are_explicit(self):
        role_date_patterns=set()
        for r in self.rows:
            events=defaultdict(dict)
            for f in r['input']['profile']['facts']:events[f['event_id']][f['field']]=f['value']
            for event,fields in events.items():
                if event=='project' or event=='hobby_interface':
                    self.assertIn('name',fields)
                    self.assertIn(fields.get('origin'),{'PERSONAL','COURSE','RESEARCH'})
                if 'start_date' in fields:
                    self.assertIn('end_date',fields)
                    self.assertLessEqual(fields['start_date'],fields['end_date'])
                    self.assertLessEqual(fields['end_date'],'2026-09')
            if 'work' in events:
                f=events['work'];role_date_patterns.add((f.get('role'),f.get('start_date'),f.get('end_date')))
            if all(e in events for e in ['prior','work']):self.assertLess(events['prior']['end_date'],events['work']['start_date'])
        self.assertGreaterEqual(len(role_date_patterns),20)

    def test_fact_ids_are_candidate_owned_and_bounded_rag_is_same_event(self):
        ownership=defaultdict(set)
        for r in self.rows:
            facts={f['fact_id']:f for f in r['input']['profile']['facts']}
            evidence={e['evidence_id']:e for e in r['input']['rag']}
            self.assertLessEqual(len(evidence),5)
            for e in evidence.values():
                self.assertLessEqual(len(e['content']),640)
                self.assertEqual(e['trust'],'untrusted_data')
                self.assertEqual(e['citation_handle']['span'],[0,len(e['content'])])
            for f in r['oracle']['facts']:
                ownership[f['fact_id']].add(f['owner'])
                self.assertEqual(f['owner'],r['input']['profile']['candidate_id'])
                self.assertEqual(f['provenance'],facts[f['fact_id']]['provenance'])
                for e in f['evidence_ids']:self.assertEqual(evidence[e]['event_id'],f['event_id'])
        self.assertTrue(all(len(owners)==1 for owners in ownership.values()))

    def test_counterfactuals_and_substantive_families_cannot_cross_splits_or_challenge(self):
        groups=defaultdict(set)
        for r in self.rows:
            for field in ['scenario_family','template_family','candidate_archetype','job_archetype','split_group','counterfactual_group']:
                if r['metadata'].get(field):groups[(field,r['metadata'][field])].add(r['split'])
        self.assertTrue(all(len(v)==1 for v in groups.values()))
        challenge=read_rows(ROOT/'scenarios/challenge.jsonl')
        pilot=read_rows(ROOT/'scenarios/pilot.jsonl')
        for field in ['scenario_family','candidate_archetype','job_archetype','split_group']:
            self.assertFalse({r['metadata'][field] for r in self.rows}&{r['metadata'][field] for r in challenge+pilot})

    def test_explicit_denial_stays_unsupported_and_motivation_is_supplied(self):
        denials=[r for r in self.rows if r['metadata']['scenario_family']=='v2_explicit_denial']
        self.assertEqual(len(denials),3)
        for r in denials:
            mapping=r['oracle']['requirements'][0]
            self.assertEqual(mapping['label'],'UNSUPPORTED')
            self.assertTrue(mapping['evidence_ids'])
            negative=[f for f in r['oracle']['facts'] if f['polarity']=='negative']
            self.assertTrue(any('Kubernetes' in f['technologies'] for f in negative))
        motivations=[r for r in self.rows if r['input']['request']['question_type']=='MOTIVATION']
        self.assertTrue(motivations)
        for r in motivations:
            self.assertEqual(r['oracle']['expected_status'],'COMPLETE')
            self.assertTrue(any(f['field']=='motivation' and f['provenance']=='CANDIDATE_ASSERTED' for f in r['input']['profile']['facts']))

    def test_trusted_missing_personal_fields_are_controlled_worlds(self):
        rows=[r for r in self.rows if r['metadata']['scenario_family']=='v2_field_routing']
        self.assertEqual(len(rows),4)
        for r in rows:
            state=r['input']['profile']['candidate_id'].rsplit('_',1)[-1]
            fields={f['field']:f['value'] for f in r['input']['profile']['facts']}
            self.assertEqual(r['oracle']['expected_status'],'COMPLETE' if state=='stored' else 'USER_INPUT_REQUIRED')
            for field in ['work_authorization','availability','remote_preference']:
                self.assertEqual(field in fields,state=='stored')
            if state=='stored':
                self.assertEqual(fields['availability'],'2026-12-01')
                self.assertEqual(fields['remote_preference'],'Prefers remote work; open to discussing a hybrid arrangement.')

    def test_larger_history_has_real_selection_tradeoff_with_source_limits(self):
        rows=[r for r in self.rows if r['metadata']['scenario_family']=='v2_history_selection']
        self.assertEqual({r['input']['task'] for r in rows},{'SELECT_RESUME_CONTENT','GENERATE_RESUME'})
        for r in rows:
            self.assertEqual(len(r['input']['rag']),5)
            self.assertEqual(sum(f['field']=='claim' for f in r['input']['profile']['facts']),15)
            self.assertTrue(any(f['event_id']=='hobby_interface' for f in r['input']['profile']['facts']))
            self.assertFalse(any('React' in req['text'] for req in r['input']['job']['requirements']))
            events={f['event_id'] for f in r['input']['profile']['facts'] if f['field']=='claim'}
            self.assertEqual(events,{'work','prior','project','hobby_interface','prior_instrumentation'})

    def test_raw_job_analysis_and_teacher_projection_have_no_hidden_answers(self):
        for r in self.rows:
            self.assertEqual(set(r['input']),{'schema_version','task','job','profile','rag','request','constraints'})
            if r['input']['task']=='ANALYZE_JOB':
                self.assertEqual(r['input']['profile']['facts'],[])
                self.assertEqual(r['input']['rag'],[])
                self.assertEqual(r['input']['job']['requirements'],[])
        text=(CATALOG/'catalog_inputs.jsonl').read_text()
        for forbidden in ['"oracle":','"expected_status":','"ground_truth_sha256":','"parent_input_sha256":']:
            self.assertNotIn(forbidden,text)

    def test_mutated_owner_and_provenance_are_rejected(self):
        original=next(r for r in self.rows if r['oracle']['facts'])
        mutated=copy.deepcopy(original);mutated['oracle']['facts'][0]['owner']='SYN-C-ANOTHER'
        self.assertTrue(validate_scenario(mutated))
        mutated=copy.deepcopy(original);mutated['oracle']['facts'][0]['provenance']='NONEXISTENT'
        self.assertTrue(validate_scenario(mutated))


if __name__=='__main__':unittest.main()
