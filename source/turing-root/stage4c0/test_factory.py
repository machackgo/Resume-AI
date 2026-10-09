"""Input/research/contract audits only. Never opens teacher or critic targets.
Run: PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest stage4c0.test_factory
"""
import copy
import hashlib
import json
import re
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from . import contracts
from .grounding import validate_scenario
from .scenarios import generate_pilot, generate_pool, generate_challenge
from .scenario_expansion import generate_expansion
from .scenario_heldout import generate_heldout

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'research'/'stage4c0'
SCENARIOS=ROOT/'scenarios'
ACTIVE=('pool.jsonl','pool-expansion-v1.jsonl','heldout-coverage-v1.2.jsonl')

def read(path):return json.loads(Path(path).read_text())
def rows(name):return [json.loads(line) for line in (SCENARIOS/name).read_text().splitlines()]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def property_keys(schema):
    if isinstance(schema,dict):
        yield from schema.get('properties',{})
        for v in schema.values():yield from property_keys(v)
    elif isinstance(schema,list):
        for v in schema:yield from property_keys(v)

class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=[json.loads(line) for line in (RESEARCH/'sources.jsonl').read_text().splitlines()]
        cls.manifest=read(RESEARCH/'research_manifest.json')
        cls.principles=[p for f in RESEARCH.glob('*_principles.json') for p in read(f)['principles']]

    def test_manifest_counts_and_all_requested_domains(self):
        self.assertEqual(self.manifest['source_count'],len(self.sources))
        self.assertEqual(self.manifest['principle_count'],len(self.principles))
        self.assertEqual(set(self.manifest['coverage']),set('ABCDEFGHIJ'))
        for domain,ids in self.manifest['coverage'].items():
            self.assertTrue(ids,domain)
            self.assertTrue(all(domain in next(s['domains'] for s in self.sources if s['source_id']==i) for i in ids))

    def test_sources_have_traceable_verified_and_scoped_provenance(self):
        self.assertEqual(len({s['source_id'] for s in self.sources}),len(self.sources))
        self.assertEqual(len({s['url'] for s in self.sources}),len(self.sources))
        for s in self.sources:
            with self.subTest(source=s['source_id']):
                self.assertRegex(s['verified_on'],r'^\d{4}-\d{2}-\d{2}$')
                self.assertTrue(s['url'].startswith('https://'))
                self.assertIn(s['access_method'],{'web_open_page_text','web_search_page_text'})
                self.assertTrue(s['publisher'] and s['scope'] and s['limitations'] and s['confidence'])
                self.assertFalse(s['full_source_text_stored'])
                self.assertTrue(s['license']['restriction'])
                body=dict(s);expected=body.pop('snapshot_note_sha256')
                actual=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                self.assertEqual(expected,actual)

    def test_principles_link_to_sources_and_distinguish_normative_rules(self):
        sources={s['source_id']:s for s in self.sources}
        self.assertEqual(len({p['principle_id'] for p in self.principles}),len(self.principles))
        kinds=set()
        for p in self.principles:
            self.assertEqual(p['version'],'1.0.0')
            self.assertTrue(p['principle'] and p['provenance'])
            kinds.add(p['evidence_kind'])
            self.assertIn(p['scope'],{'universal_product_rule','context_dependent'})
            for ref in p['provenance']:
                self.assertEqual(ref['source_url'],sources[ref['source_id']]['url'])
                self.assertIn(p['principle_id'],sources[ref['source_id']]['principle_ids'])
        self.assertTrue({'source_supported','conservative_inference','research_informed_product_rule','user_requirement_research_context'}<=kinds)

    def test_research_snapshot_hashes_and_no_corpus_ingestion(self):
        manifest=read(RESEARCH/'snapshot_checksums.json')
        for name,expected in manifest['sha256'].items():self.assertEqual(sha(RESEARCH/name),expected,name)
        for name in ['external_training_corpora_included','public_job_postings_copied','private_candidate_records_used']:
            self.assertEqual(self.manifest[name],0)
        config=self.manifest['teacher_configuration']
        self.assertEqual(config['requested_model'],'gpt-6-astra')
        self.assertEqual(config['requested_reasoning'],'ultra')
        self.assertIsNone(config['observed_runtime_model'])

class ContractTests(unittest.TestCase):
    def test_frozen_contract_file_hashes(self):
        manifest=read(ROOT/'contracts/manifest.v1.json')
        self.assertEqual(manifest['version'],'stage4c0-v1')
        for name,expected in manifest['files'].items():self.assertEqual(sha(ROOT/name),expected,name)
        self.assertEqual(sha(RESEARCH/'research_manifest.json'),manifest['research_manifest_sha256'])

    def test_ten_task_schemas_have_discriminators_and_no_private_reasoning_fields(self):
        self.assertEqual(len(set(contracts.TASKS)),10)
        forbidden={'chain_of_thought','scratchpad','private_reasoning','hidden_reasoning','analysis_transcript'}
        for task in contracts.TASKS:
            schema=read(ROOT/'contracts'/f'{task.lower()}.schema.json')
            self.assertEqual(schema,contracts.output_schema(task))
            self.assertFalse(forbidden.intersection(property_keys(schema)))
            for alternative in schema['oneOf']:
                self.assertEqual(alternative['properties']['task']['const'],task)
                self.assertEqual(alternative['properties']['schema_version']['const'],'stage4c0-v1')
                self.assertFalse(alternative['additionalProperties'])

    def test_task_rubrics_preserve_grounding_hard_gate_and_source_links(self):
        supplement=read(ROOT/'contracts/task_rubric_supplement.v1.json')
        found=set();source_ids={s['source_id'] for s in ResearchTests.sources} if hasattr(ResearchTests,'sources') else {s['source_id'] for s in [json.loads(x) for x in (RESEARCH/'sources.jsonl').read_text().splitlines()]}
        for filename,expected in supplement['files'].items():
            self.assertEqual(sha(ROOT/filename),expected)
            rubric=read(ROOT/filename);found.add(rubric['task'])
            self.assertEqual(rubric['version'],'stage4c0-task-rubric-v1')
            grounding=rubric['dimensions']['grounding']
            self.assertTrue(grounding['hard_gate']);self.assertEqual(grounding['minimum'],4)
            self.assertEqual(grounding['weight'],0)
            self.assertFalse(rubric['thresholds_changed'])
            self.assertFalse(rubric['pilot_requests_retroactively_modified'])
            self.assertTrue(rubric['task_specific_anchor_4'])
            for p in rubric['principles']:self.assertTrue(set(p['source_ids'])<=source_ids)
        self.assertEqual(found,set(contracts.TASKS))

    def test_bounded_revision_and_truth_gate_cannot_be_averaged_away(self):
        gates=read(ROOT/'contracts/acceptance_gates.v1.json')
        self.assertEqual(gates['max_revisions'],2)
        self.assertEqual(gates['per_record']['grounding_score'],4)
        self.assertFalse(gates['per_record']['unknown_partial_unsupported_candidate_claims_accepted'])
        self.assertEqual(gates['release']['catastrophic_truth_failures_allowed'],0)
        self.assertTrue(gates['per_record']['no_oracle_or_test_target_in_model_messages'])
        self.assertTrue(gates['per_record']['no_truncation'])
        self.assertFalse(gates['release']['training_started'])
        trace=contracts.TRACE['properties']
        self.assertLessEqual(trace['decisions']['maxItems'],12)
        self.assertEqual(set(trace),{'selected_requirement_ids','selected_evidence_ids','excluded_evidence_ids','principle_ids','decisions'})

    def test_teacher_critic_revision_contracts_are_distinct_and_no_cot(self):
        teacher=(ROOT/'contracts/prompts/teacher.v1.txt').read_text()
        critic=(ROOT/'contracts/prompts/critic.v1.txt').read_text()
        revision=(ROOT/'contracts/prompts/revision.v1.txt').read_text()
        self.assertIn('Do not emit private chain-of-thought',teacher)
        self.assertIn('fresh context',critic)
        self.assertIn('never private chain-of-thought',critic)
        self.assertIn('at most two',revision)
        self.assertIn('Never invent evidence',revision)
        self.assertNotEqual(teacher,critic)
        self.assertIn('same-event',teacher)
        self.assertIn('SHA256',critic)

class ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.active=sum((rows(name) for name in ACTIVE),[])
        cls.pilot=rows('pilot.jsonl');cls.challenge=rows('challenge.jsonl')
        cls.all=cls.pilot+cls.active+cls.challenge

    def test_active_counts_and_heldout_task_coverage(self):
        self.assertEqual(len(self.active),143)
        self.assertEqual(Counter(r['split'] for r in self.active),{'train':113,'validation':14,'test':16})
        self.assertEqual(len(self.pilot),18);self.assertEqual(len(self.challenge),10)
        for split in ['train','validation','test']:
            self.assertEqual({r['input']['task'] for r in self.active if r['split']==split},set(contracts.TASKS))
        heldout=read(SCENARIOS/'heldout-manifest.v1.2.json')
        self.assertEqual(heldout['records'],10)
        self.assertFalse(heldout['teacher_outputs_accessed'])
        self.assertFalse(heldout['pilot_outputs_accessed'])

    def test_deterministic_factories_reproduce_existing_snapshots(self):
        cases=[(generate_pilot,'pilot.jsonl'),(generate_pool,'pool.jsonl'),(generate_challenge,'challenge.jsonl'),(generate_expansion,'pool-expansion-v1.jsonl'),(generate_heldout,'heldout-coverage-v1.2.jsonl')]
        for factory,name in cases:
            with self.subTest(file=name):
                self.assertEqual(factory(),rows(name))
                self.assertEqual(factory(),factory())
        self.assertNotEqual(generate_pool(seed=1),generate_pool(seed=2))

    def test_all_inputs_and_ground_truth_validate(self):
        for r in self.all:
            with self.subTest(scenario=r['scenario_id']):
                self.assertEqual(contracts.validate_input(r['input']),[])
                self.assertEqual(validate_scenario(r),[])
                self.assertEqual(r['metadata']['ground_truth_sha256'],digest({'profile':r['input']['profile'],'rag':r['input']['rag'],'oracle':r['oracle']}))
                self.assertFalse(r['metadata']['target_exists_at_ground_truth_creation'])

    def test_every_source_fact_has_matching_owner_scope_and_provenance(self):
        for r in self.all:
            facts={f['fact_id']:f for f in r['input']['profile']['facts']}
            evidence={e['evidence_id']:e for e in r['input']['rag']}
            self.assertEqual({f['fact_id'] for f in r['oracle']['facts']},set(facts))
            for f in r['oracle']['facts']:
                self.assertEqual(f['owner'],r['input']['profile']['candidate_id'])
                self.assertEqual(f['event_id'],facts[f['fact_id']]['event_id'])
                self.assertEqual(f['provenance'],facts[f['fact_id']]['provenance'])
                self.assertTrue(set(f['evidence_ids'])<=set(evidence))
                self.assertTrue(all(evidence[e]['event_id']==f['event_id'] for e in f['evidence_ids']))

    def test_raw_job_analysis_has_no_preextracted_answers_or_candidate_leakage(self):
        for r in self.all:
            if r['input']['task']=='ANALYZE_JOB':
                self.assertEqual(r['input']['job']['requirements'],[])
                self.assertEqual(r['input']['profile']['facts'],[])
                self.assertEqual(r['input']['rag'],[])
            for req in r['oracle']['expected_job_requirements']:
                self.assertIn(req['source_quote'],r['input']['job']['text'])

    def test_input_only_projections_do_not_include_oracles_or_split_hints(self):
        names=[('pilot.jsonl','pilot_inputs.jsonl'),('pool.jsonl','pool_inputs.jsonl'),('challenge.jsonl','challenge_inputs.jsonl'),('pool-expansion-v1.jsonl','pool-expansion-v1-inputs.jsonl'),('heldout-coverage-v1.2.jsonl','heldout-coverage-v1.2-inputs.jsonl')]
        for full,projected in names:
            expected=[{'scenario_id':r['scenario_id'],'input':r['input']} for r in rows(full)]
            self.assertEqual(rows(projected),expected)
            for item in rows(projected):
                self.assertEqual(set(item),{'scenario_id','input'})
                self.assertFalse({'oracle','expected_status','split','scenario_family'}&set(item['input']))

    def test_unique_ids_and_candidate_job_task_combinations(self):
        self.assertEqual(len({r['scenario_id'] for r in self.all}),len(self.all))
        pairs={(r['input']['profile']['candidate_id'],r['input']['job']['job_id'],r['input']['task']) for r in self.all}
        self.assertEqual(len(pairs),len(self.all))

    def test_connected_family_identifiers_never_cross_split(self):
        for field in ['scenario_family','template_family','candidate_archetype','job_archetype','split_group']:
            groups=defaultdict(set)
            for r in self.all:groups[r['metadata'][field]].add(r['split'])
            self.assertFalse({k:v for k,v in groups.items() if len(v)>1},field)
        challenge={r['metadata']['scenario_family'] for r in self.challenge}
        self.assertFalse(challenge&{r['metadata']['scenario_family'] for r in self.pilot+self.active})

    def test_counterfactual_variants_are_grouped_and_materially_different(self):
        groups=defaultdict(list)
        for r in self.active:
            if r['metadata']['counterfactual_group'] and r['input']['task']=='GENERATE_RESUME':groups[r['metadata']['counterfactual_group']].append(r)
        self.assertEqual(set(groups),{'containers','clouds','adapters','retrieval','api_ownership','metric_specificity','credential_trust'})
        for group,records in groups.items():
            self.assertEqual(len(records),2,group)
            self.assertEqual(len({r['split'] for r in records}),1)
            a,b=records
            self.assertEqual(a['input']['job'],b['input']['job'])
            left=[(f['field'],f['value'],f['provenance']) for f in a['input']['profile']['facts']]
            right=[(f['field'],f['value'],f['provenance']) for f in b['input']['profile']['facts']]
            self.assertNotEqual(left,right,group)
            self.assertEqual(len(left),len(right),group)

    def test_role_seniority_fit_section_and_action_coverage(self):
        self.assertEqual(len({r['metadata']['role_family'] for r in self.active}),10)
        self.assertEqual({r['metadata']['seniority'] for r in self.active},{'student_new_graduate','entry_level','early_career','mid_level','senior'})
        self.assertEqual({r['metadata']['fit_level'] for r in self.active},{'strong','moderate','weak','mixed'})
        self.assertEqual({r['input']['request']['section'] for r in self.active if r['input']['task']=='GENERATE_RESUME_SECTION'},set(contracts.SECTIONS))
        actions={a for r in self.active for a in r['metadata']['action_tags']}
        self.assertTrue({'studied','used','consumed','built','implemented','designed','trained','fine-tuned','evaluated','optimized','deployed','operated','led','collaborated'}<=actions)

    def test_representative_technology_and_trust_diversity(self):
        tech={t for r in self.active for t in r['metadata']['technology_tags']}
        self.assertTrue({'Python','PyTorch','TensorFlow','LLMs','RAG','LoRA','QLoRA','FastAPI','Flask','REST APIs','Docker','Kubernetes','AWS','Azure','GCP','SQL','PostgreSQL','vector databases','CI/CD'}<=tech)
        actual={f['provenance'] for r in self.active for f in r['input']['profile']['facts']}
        self.assertEqual(actual,set(contracts.PROVENANCE))
        polarities={f['polarity'] for r in self.active for f in r['oracle']['facts']}
        self.assertTrue({'positive','conflict','instruction'}<=polarities)
        self.assertTrue(any(len(f['evidence_ids'])>1 for r in self.active for f in r['oracle']['facts']))

    def test_rag_bounds_exact_spans_and_attestations(self):
        for r in self.all:
            self.assertLessEqual(len({e['content'] for e in r['input']['rag']}),5)
            fids={f['fact_id'] for f in r['input']['profile']['facts']}
            for e in r['input']['rag']:
                self.assertLessEqual(len(e['content']),640)
                self.assertEqual(e['trust'],'untrusted_data')
                self.assertEqual(e['citation_handle'],{'source_version':1,'span':[0,len(e['content'])]})
                self.assertEqual(e['verification']['reference_policy'],'resolve_supports')
                for attestation in e['authenticated_attestations']:
                    self.assertEqual(attestation['source_id'],e['source_id'])
                    self.assertTrue(set(attestation['fact_ids'])<=fids)
                    self.assertEqual(attestation['policy'],'exact_fact_ids_only')

    def test_personal_missing_data_and_trusted_answers_are_both_present(self):
        application=[r for r in self.active if r['input']['task'] in {'ANSWER_APPLICATION_QUESTION','IDENTIFY_MISSING_INFORMATION'}]
        self.assertTrue(any(r['oracle']['expected_status']=='USER_INPUT_REQUIRED' and not r['oracle']['personal_fields'] for r in application))
        trusted=[r for r in application if r['oracle']['expected_status']=='COMPLETE' and r['oracle']['personal_fields']]
        self.assertTrue(trusted)
        self.assertTrue(any('portfolio_url' in r['oracle']['personal_fields'] for r in trusted))
        self.assertTrue(any('salary_expectation' in r['oracle']['personal_fields'] for r in trusted))
        self.assertTrue(any(r['input']['request']['max_characters'] is not None for r in application))
        self.assertTrue({50,100,200}<={r['input']['request']['max_words'] for r in application})

    def test_employment_education_dates_are_ordered_per_event(self):
        for r in self.all:
            events=defaultdict(dict)
            for f in r['input']['profile']['facts']:
                if f['field'] in {'start_date','end_date'}:events[f['event_id']][f['field']]=f['value']
            for event,dates in events.items():
                self.assertTrue({'start_date','end_date'}<=dates.keys(),(r['scenario_id'],event))
                self.assertLessEqual(dates['start_date'],dates['end_date'],(r['scenario_id'],event))
                self.assertLessEqual(dates['end_date'],r['input']['constraints']['as_of_date'])

    def test_no_real_contact_data_or_user_private_identifiers(self):
        for r in self.all:
            self.assertTrue(r['metadata']['synthetic']);self.assertFalse(r['metadata']['private_data_used'])
            text=json.dumps(r['input'],ensure_ascii=False)
            self.assertNotRegex(text,r'(?i)mohammedmubashir|turing\.wpi\.edu|@(?:gmail|outlook|wpi)\.')
            self.assertNotRegex(text,r'\b\d{3}-\d{2}-\d{4}\b')
            self.assertNotRegex(text,r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
            for f in r['input']['profile']['facts']:
                if f['field']=='url':self.assertIn('.example/',f['value'])
                if f['field']=='name' and f['event_id']=='identity':self.assertTrue(f['value'].startswith('Synthetic Candidate '))

    def test_original_and_quarantined_input_snapshots_are_preserved(self):
        manifests=['manifest.json','expansion-manifest.v1.json','heldout-manifest.v1.json','heldout-manifest.v1.1.json','heldout-manifest.v1.2.json']
        for name in manifests:
            manifest=read(SCENARIOS/name)
            for filename,expected in manifest['sha256'].items():self.assertEqual(sha(SCENARIOS/filename),expected,(name,filename))
        for version in ['v1','v1.1']:
            quarantine=read(SCENARIOS/f'heldout-{version}-quarantine.json')
            self.assertEqual(quarantine['acceptance_status'],'QUARANTINED_INPUT_SNAPSHOT')
            self.assertFalse(quarantine['teacher_targets_generated'])
            source=SCENARIOS/quarantine['source_archive']
            manifest=read(SCENARIOS/f'heldout-manifest.{version}.json')
            self.assertEqual(sha(source),manifest['source_sha256'])
        self.assertNotIn('heldout-coverage-v1.jsonl',ACTIVE)
        self.assertNotIn('heldout-coverage-v1.1.jsonl',ACTIVE)

    def test_cross_candidate_mutation_is_rejected(self):
        specimen=copy.deepcopy(next(r for r in self.active if r['oracle']['facts']))
        specimen['oracle']['facts'][0]['owner']='SYN-C-foreign'
        self.assertIn('CROSS_CANDIDATE_FACT',validate_scenario(specimen))

    def test_provenance_or_citation_span_mutation_is_rejected(self):
        specimen=copy.deepcopy(next(r for r in self.active if r['input']['rag']))
        specimen['input']['rag'][0]['citation_handle']['span'][1]-=1
        self.assertTrue(contracts.validate_input(specimen['input']))
        specimen=copy.deepcopy(next(r for r in self.active if r['oracle']['facts']))
        specimen['oracle']['facts'][0]['provenance']='CANDIDATE_ASSERTED'
        self.assertIn('FACT_PROVENANCE_MISMATCH',validate_scenario(specimen))

if __name__=='__main__':unittest.main()
