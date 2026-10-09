"""Prospective full-catalog v2, authored before any full-catalog teacher targets.
Original technical scenarios are retained; explicit family-level education/career
specifications replace the shared scaffolding. Original143, pilot and challenge
remain immutable. No teacher/critic artifacts are loaded by this module.
"""
import copy, hashlib, json, re
from collections import Counter
from pathlib import Path
from .scenarios import action, family, req, build_record, digest, SEED
ROOT=Path(__file__).resolve().parents[1]
VERSION='stage4c0-catalog-v2'
PARENTS=('pool.jsonl','pool-expansion-v1.jsonl','heldout-coverage-v1.2.jsonl')
RATIONALE='Prospective input audit found universal CS bachelor credentials, repeated career scaffolds, missing explicit project origins, and limited contradiction/motivation/personal-field/large-history coverage. No full teacher targets were consulted.'

# Explicit authored qualifications, never generated from teacher prose.
# degree-free paths use a non-degree completion credential and never a degree field.
def degree(title,start,end):return ('degree',title,start,end)
def certificate(title,start,end):return ('credential',title,start,end)
EDUCATION={
 'containers':[certificate('Certificate of Completion in Cloud Operations (non-degree)','2020-02','2021-05')],
 'clouds':[degree('Bachelor of Science in Electrical Engineering','2013-09','2017-05')],
 'adapters':[degree('Bachelor of Science in Applied Mathematics','2015-09','2019-05'),degree('Master of Science in Computational Mathematics','2019-09','2021-06')],
 'retrieval':[degree('Bachelor of Arts in Information Science','2021-09','2025-05')],
 'api_ownership':[degree('Associate of Applied Science in Software Development','2020-01','2022-05')],
 'metric_specificity':[degree('Bachelor of Science in Energy Engineering','2012-09','2016-06'),degree('Master of Science in Data Analytics','2017-01','2018-12')],
 'credential_trust':[degree('Bachelor of Science in Statistics','2017-09','2021-05')],
 'nlp_languages':[degree('Bachelor of Arts in Linguistics','2012-09','2016-05'),degree('Master of Science in Computational Linguistics','2017-09','2019-06')],
 'newgrad_cv':[degree('Bachelor of Engineering in Mechatronics','2020-08','2024-05'),degree('Master of Science in Robotics','2024-09','2026-06')],
 'scientist_causal':[degree('Bachelor of Science in Mathematics','2006-09','2010-05'),degree('Doctor of Philosophy in Statistics','2010-09','2016-05')],
 'data_quality':[degree('Bachelor of Science in Environmental Science','2020-09','2024-05')],
 'research_compute':[degree('Bachelor of Science in Physics','2008-09','2012-05'),degree('Doctor of Philosophy in Computational Biology','2012-09','2016-05')],
 'forward_deployed':[degree('Bachelor of Science in Industrial Engineering','2013-09','2017-06')],
 'genai_eval':[degree('Bachelor of Arts in Education Studies','2020-09','2024-05'),degree('Master of Science in Learning Analytics','2024-09','2026-05')],
 'backend_batch':[certificate('Certificate of Completion in Backend Systems (non-degree)','2017-03','2018-11')],
 'software_search':[degree('Bachelor of Arts in Digital Humanities','2017-09','2021-05')],
 'monitoring_holdout':[degree('Bachelor of Science in Computer Engineering','2012-09','2016-06')],
 'research_audio_holdout':[degree('Bachelor of Science in Acoustical Engineering','2017-09','2021-05'),degree('Master of Science in Signal Processing','2021-09','2023-06')],
 'datascience_holdout':[degree('Bachelor of Science in Agricultural Economics','2013-09','2017-06'),degree('Master of Science in Statistics','2017-09','2019-05')],
 'nlp_holdout':[degree('Bachelor of Arts in Linguistics','2021-09','2025-05')],
 'applied_holdout':[degree('Bachelor of Science in Ecology','2020-09','2024-05'),degree('Master of Science in Environmental Data Science','2024-09','2026-06')],
 'e_incident_dispute':[degree('Bachelor of Science in Information Technology','2012-09','2016-05')],
 'e_retrieval_corroboration':[degree('Bachelor of Engineering in Mechanical Engineering','2016-09','2020-05'),degree('Master of Science in Information Systems','2021-01','2022-12')],
 'e_saved_preferences':[degree('Associate of Applied Science in Network Systems','2016-08','2018-05')],
 'e_portfolio_fields':[degree('Bachelor of Arts in History','2015-09','2019-05'),certificate('Certificate of Completion in Web Application Development (non-degree)','2021-02','2022-04')],
 'e_credential_sections':[degree('Bachelor of Science in Statistics','2011-09','2015-05'),degree('Master of Public Policy','2016-09','2018-05')],
 'e_missing_preferences':[degree('Bachelor of Science in Geography','2020-09','2024-05')],
 'e_behavior_structure':[degree('Bachelor of Science in Agronomy','2011-09','2015-05'),degree('Master of Science in Biostatistics','2016-09','2018-06')],
 'h_geospatial_service':[degree('Bachelor of Science in Geospatial Engineering','2012-09','2016-05')],
 'h_embedded_project':[degree('Bachelor of Science in Electrical Engineering','2020-09','2024-05'),degree('Master of Science in Embedded Systems','2024-09','2026-06')],
 'h_validation_lab':[degree('Bachelor of Science in Physics','2008-09','2012-05'),degree('Master of Science in Instrumentation','2013-09','2015-06')],
 'h_trial_analytics':[degree('Bachelor of Science in Transportation Engineering','2016-09','2020-05')],
 'h_accessible_forms':[degree('Bachelor of Arts in Technical Communication','2021-09','2025-05')],
}
# Current-role identity/dates differ by substantive family. Paired worlds share these.
CAREERS={
 'containers':('Cloud Support Engineer','2022-07','2026-07'),
 'clouds':('Machine Learning Engineer','2020-04','2026-08'),
 'adapters':('Machine Learning Research Engineer','2022-02','2026-06'),
 'api_ownership':('Backend Software Developer','2022-08','2026-07'),
 'metric_specificity':('Inference Engineer','2019-03','2026-08'),
 'credential_trust':('Risk Data Analyst','2021-08','2026-06'),
 'nlp_languages':('Language Technology Engineer','2019-09','2026-07'),
 'scientist_causal':('Senior Applied Scientist','2020-09','2026-08'),
 'data_quality':('Junior Data Quality Analyst','2024-08','2026-06'),
 'research_compute':('Senior Research Software Engineer','2021-01','2026-08'),
 'forward_deployed':('Customer Solutions Engineer','2019-06','2026-07'),
 'backend_batch':('Backend Engineer','2019-02','2026-06'),
 'software_search':('Search Software Engineer','2022-04','2026-08'),
 'monitoring_holdout':('Senior ML Platform Engineer','2020-11','2026-08'),
 'research_audio_holdout':('Audio Research Engineer','2023-08','2026-06'),
 'datascience_holdout':('Forecasting Data Scientist','2019-09','2026-07'),
 'nlp_holdout':('Junior NLP Developer','2025-08','2026-08'),
 'e_incident_dispute':('Model Operations Engineer','2018-06','2026-08'),
 'e_retrieval_corroboration':('AI Application Engineer','2023-02','2026-07'),
 'e_saved_preferences':('ML Infrastructure Developer','2019-01','2026-08'),
 'e_credential_sections':('Statistical Data Scientist','2018-08','2026-07'),
 'e_missing_preferences':('Junior Data Analyst','2024-09','2026-08'),
 'e_behavior_structure':('Scientific Evaluation Analyst','2018-09','2026-08'),
 'h_geospatial_service':('Geospatial Platform Engineer','2019-05','2026-08'),
 'h_validation_lab':('Senior Scientific Software Engineer','2020-10','2026-07'),
 'h_trial_analytics':('Transportation Data Analyst','2021-07','2026-08'),
 'h_accessible_forms':('Junior Language Tools Developer','2025-09','2026-08'),
}
PROJECT_ORIGINS={'retrieval':'COURSE','newgrad_cv':'COURSE','genai_eval':'COURSE','nlp_holdout':'COURSE','applied_holdout':'RESEARCH','e_portfolio_fields':'PERSONAL','e_credential_sections':'COURSE','h_embedded_project':'COURSE','h_validation_lab':'PERSONAL','h_trial_analytics':'PERSONAL'}


def read_parents():
 return [json.loads(line) for name in PARENTS for line in (ROOT/'scenarios'/name).read_text().splitlines()]

def put(record,field,value,event,*,fid=None,provenance='AUTHENTICATED',polarity='positive',action_name=None,evidence_ids=()):
 cid=record['input']['profile']['candidate_id'];prefix=cid.removeprefix('SYN-C-')
 fid=fid or prefix+'-V2F'+str(len(record['input']['profile']['facts'])+1)
 record['input']['profile']['facts'].append(dict(fact_id=fid,event_id=event,field=field,value=value,provenance=provenance))
 record['oracle']['facts'].append(dict(fact_id=fid,event_id=event,owner=cid,kind=field,action=action_name,technologies=[],numbers=re.findall(r'(?<!\w)\d+(?:\.\d+)?%?(?!\w)',value),entities=[value] if field in {'name','role','organization','institution','degree','credential','title'} else [],evidence_ids=list(evidence_ids),polarity=polarity,provenance=provenance))
 return fid

def replace_value(record,fact,value):
 fact['value']=value
 oracle=next(f for f in record['oracle']['facts'] if f['fact_id']==fact['fact_id'])
 oracle['numbers']=re.findall(r'(?<!\w)\d+(?:\.\d+)?%?(?!\w)',value)
 if oracle['entities']:oracle['entities']=[value]


def diversify(record):
 r=copy.deepcopy(record);m=r['metadata'];g=m['scenario_family'];original_hash=digest(record['input'])
 r['scenario_id']=r['scenario_id'].replace('S4C0-','S4C0V2-',1)
 # Raw analysis stays candidate-free. Its source lineage still records the family plan.
 if r['input']['task']!='ANALYZE_JOB':
  remove={f['fact_id'] for f in r['input']['profile']['facts'] if f['event_id'] in {'education','graduate_education'}}
  r['input']['profile']['facts']=[f for f in r['input']['profile']['facts'] if f['fact_id'] not in remove]
  r['oracle']['facts']=[f for f in r['oracle']['facts'] if f['fact_id'] not in remove]
  for i,(kind,title,start,end) in enumerate(EDUCATION[g]):
   event='education_'+str(i+1) if kind=='degree' else 'nondegree_training_'+str(i+1)
   prefix=r['input']['profile']['candidate_id'].removeprefix('SYN-C-')+'-V2ED'+str(i+1)
   school='Synthetic '+g.replace('_',' ').title()+(' Academy' if kind=='credential' else ' Institute')
   for field,value in [(kind,title),('institution',school),('start_date',start),('end_date',end)]:put(r,field,value,event,fid=prefix+'-'+field)
  if not any(x[0]=='degree' for x in EDUCATION[g]):put(r,'education_status','No college degree is held.','education_status',polarity='negative')
  if g in CAREERS:
   title,start,end=CAREERS[g]
   for f in r['input']['profile']['facts']:
    if f['event_id']=='work' and f['field'] in {'role','start_date','end_date'}:replace_value(r,f,{'role':title,'start_date':start,'end_date':end}[f['field']])
  if any(f['event_id']=='project' for f in r['input']['profile']['facts']):
   if g not in PROJECT_ORIGINS:raise ValueError('Missing authored project origin '+g)
   put(r,'origin',PROJECT_ORIGINS[g],'project',fid=r['input']['profile']['candidate_id'].removeprefix('SYN-C-')+'-V2-project-origin')
  # Externally observed evidence sentences and their provenance remain unchanged.
 m.update(generator_version=VERSION,parent_scenario_id=record['scenario_id'],parent_record_persisted=True,parent_input_sha256=original_hash,parent_ground_truth_sha256=record['metadata']['ground_truth_sha256'],education_path=[x[1] for x in EDUCATION[g]],education_plan_family=g,prospective_change_reason=RATIONALE,full_teacher_target_consulted=False)
 r['metadata']['ground_truth_sha256']=digest({'profile':r['input']['profile'],'rag':r['input']['rag'],'oracle':r['oracle']})
 return r


def new_families():
 return [
 family('v2_explicit_denial','MLOps Engineer','mid_level','mixed','cold-chain monitoring','model alerting',[
 action('Operated Azure model-monitoring jobs for cold-chain forecast alerts.','operated',['Azure','monitoring']),
 action('The candidate has never operated a Kubernetes cluster.','operated',['Kubernetes'],polarity='negative',trust='CANDIDATE_ASSERTED'),
 action('Implemented CI/CD checks for the alert-service configuration.','implemented',['CI/CD'])],
 [req('Required: operate Kubernetes clusters.',1,label='UNSUPPORTED'),req('Preferred: ML alerting experience.',0,'preferred')],style='v2_direct_requirement_note',notes=['explicit_negative'],question='Have you operated Kubernetes clusters?'),
 family('v2_supplied_motivation','AI Engineer','mid_level','moderate','accessible navigation','route explanation tools',[
 action('Built a Python prototype that exposed route explanations for accessibility reviewer feedback.','built',['Python']),
 action('Collaborated with accessibility reviewers to identify confusing route explanations.','collaborated',[]),
 action('Evaluated whether revised wording resolved the reviewers’ documented concerns.','evaluated',['evaluation'])],
 [req('Required: build reviewable AI application prototypes.',0),req('Preferred: accessibility collaboration.',1,'preferred')],style='v2_contribution_invitation',notes=['supplied_motivation'],question='Why does this role interest you?'),
 family('v2_field_routing','Data Scientist','early_career','strong','building operations','energy analysis',[
 action('Used SQL to reconcile building-energy readings with inspection dates.','used',['SQL']),
 action('Built a Python report comparing energy use before and after a documented equipment change.','built',['Python']),
 action('Collaborated with facility analysts to explain missing-meter intervals.','collaborated',[])],
 [req('Required: analyze operational records with Python and SQL.',[0,1])],style='v2_administration_card',notes=['trusted_missing_personal_pair']),
 family('v2_history_selection','Machine Learning Engineer','senior','strong','industrial diagnostics','grounded diagnostic services',[
 action('Built FastAPI REST API endpoints in Python to serve diagnostic-model predictions.','built',['FastAPI','REST APIs','Python']),
 action('Designed SQL reconciliation checks for an earlier warehouse migration.','designed',['SQL'],event='prior'),
 action('Implemented a RAG prototype that retrieved diagnostic manuals for engineer review.','implemented',['RAG'],event='project')],
 [req('Required: build reviewable diagnostic inference APIs.',0),req('Required: implement retrieval over technical manuals.',2),req('Preferred: operational data-quality work.',1,'preferred')],style='v2_priority_brief',notes=['large_history_selection'])]

NEW_EDUCATION={
 'v2_explicit_denial':[degree('Bachelor of Science in Information Systems','2011-09','2015-05')],
 'v2_supplied_motivation':[degree('Bachelor of Arts in Cognitive Science','2010-09','2014-05'),degree('Master of Science in Human-Computer Interaction','2016-09','2018-05')],
 'v2_field_routing':[degree('Bachelor of Science in Building Services Engineering','2016-09','2020-05')],
 'v2_history_selection':[degree('Bachelor of Science in Mechanical Engineering','2008-09','2012-05'),degree('Master of Science in Computer Science','2013-09','2015-05')],
}
EDUCATION.update(NEW_EDUCATION)
CAREERS.update({'v2_explicit_denial':('Model Operations Engineer','2018-05','2026-08'),'v2_supplied_motivation':('Human-Centered AI Engineer','2019-02','2026-08'),'v2_field_routing':('Building Analytics Engineer','2021-03','2026-08'),'v2_history_selection':('Senior Machine Learning Engineer','2022-01','2026-08')})
PROJECT_ORIGINS['v2_history_selection']='PERSONAL'


def add_history(record):
 # Four additional true facts per history event are unnecessary. Three compact
 # propositions per source expose content-selection tradeoffs without bloating context.
 inp=record['input'];oracle=record['oracle'];g=record['metadata']['scenario_family']
 groups=[
 ('work','EMPLOYMENT',['Built FastAPI REST API endpoints in Python to serve diagnostic-model predictions.','Deployed the diagnostic service to Azure using Docker.','Operated service alerts and documented recovery steps for failed inference requests.']),
 ('prior','EMPLOYMENT',['Designed SQL reconciliation checks for an earlier warehouse migration.','Implemented PostgreSQL records linking source batches to validation results.','Collaborated with warehouse analysts to resolve inconsistent part identifiers.']),
 ('project','PERSONAL',['Implemented a RAG prototype that retrieved diagnostic manuals for engineer review.','Evaluated unanswered questions against a manually reviewed diagnostic-question set.','Built a Python comparison view showing source passages beside proposed answers.']),
 ('hobby_interface','PERSONAL',['Built a React interface for a personal hiking-log project.','Used a local JSON file to store trail notes.','Designed a map legend for the hiking-log interface.']),
 ('prior_instrumentation','EMPLOYMENT',['Used Python to inspect laboratory sensor exports.','Implemented checks that flagged incomplete calibration fields.','Collaborated with technicians to document corrected export procedures.'])]
 # Replace source groups as a unit before targets; retain each factual proposition.
 old={f['fact_id'] for f in inp['profile']['facts'] if f['field']=='claim'}
 inp['profile']['facts']=[f for f in inp['profile']['facts'] if f['fact_id'] not in old]
 oracle['facts']=[f for f in oracle['facts'] if f['fact_id'] not in old]
 inp['rag']=[];links={}
 verbs=['built','deployed','operated','designed','implemented','collaborated','implemented','evaluated','built','built','used','designed','used','implemented','collaborated']
 for i,(event,origin,texts) in enumerate(groups):
  eid=g+'-V2H'+str(i+1);source=g+'-history-source-'+str(i+1);content='\n'.join(texts)
  if len(content)>640:raise ValueError('history source exceeds frozen bound')
  fids=[]
  for j,text in enumerate(texts):
   fid=put(record,'claim',text,event,fid=g+'-V2H'+str(i+1)+'-F'+str(j+1),provenance='EXTERNAL_OBSERVED',action_name=verbs[3*i+j],evidence_ids=[eid])
   fids.append(fid)
   tech=[t for t in ['FastAPI','Python','Azure','Docker','SQL','PostgreSQL','RAG','React','JSON'] if re.search(r'(?<!\w)'+re.escape(t)+r'(?!\w)',text)]
   if 'REST API' in text:tech.append('REST APIs')
   next(f for f in oracle['facts'] if f['fact_id']==fid)['technologies']=tech
  inp['rag'].append(dict(evidence_id=eid,event_id=event,content=content,source_id=source,source_type='external_observation',origin='synthetic_authored_history_record',trust='untrusted_data',verification={'reference_policy':'resolve_supports','meaning':'Each excerpt groups facts from one event; the source label is not an authenticated attestation.'},authenticated_attestations=[],citation_handle={'source_version':1,'span':[0,len(content)]}))
  links[event]=(eid,fids)
  if event not in {'work','prior','project'}:
   values=[('name','Hiking Log Interface')] if event=='hobby_interface' else [('organization','Synthetic Sensor Instrumentation Works'),('role','Instrumentation Software Developer'),('start_date','2015-08'),('end_date','2018-12')]
   for field,value in values:put(record,field,value,event)
   put(record,'origin',origin,event)
 for m,event in zip(oracle['requirements'],['work','project','prior']):m['evidence_ids']=[links[event][0]];m['fact_ids']=[links[event][1][0]]
 oracle['source_lineage']={e['evidence_id']:e['source_id'] for e in inp['rag']}
 # Current/previous chronology is coherent; older employment precedes prior work.
 for f in inp['profile']['facts']:
  if f['event_id']=='prior' and f['field'] in {'start_date','end_date'}:replace_value(record,f,{'start_date':'2019-02','end_date':'2021-11'}[f['field']])
 inp['request']['instruction']+=' Select only the strongest relevant events; do not repeat the same achievement across sections. A personal hiking interface is available but the job does not request frontend work.'
 record['metadata']['technology_tags']=sorted(set(record['metadata']['technology_tags'])|{'React','PostgreSQL','Azure','Docker','SQL','RAG','Python','FastAPI','REST APIs','evaluation','inference','monitoring'})
 record['metadata']['action_tags']=sorted(set(verbs))


def generate_new(seed=SEED):
 fs=new_families();rows=[]
 specs=[(0,['MAP_JOB_TO_CANDIDATE','GENERATE_RESUME','ANSWER_APPLICATION_QUESTION']),(1,['ANSWER_APPLICATION_QUESTION','GENERATE_RESUME','GENERATE_COVER_LETTER']),(3,['SELECT_RESUME_CONTENT','GENERATE_RESUME'])]
 for which,tasks in specs:
  for task in tasks:
   f=fs[which];r=diversify(build_record(f,task,600+len(rows),seed));request=r['input']['request'];o=r['oracle']
   if which==0 and task=='ANSWER_APPLICATION_QUESTION':request.update(question_type='FACTUAL',max_words=50);o.update(expected_status='COMPLETE',desired_field=None)
   if which==1:
    put(r,'motivation','I want to build AI tools that help accessibility reviewers understand and challenge route explanations.','preferences',provenance='CANDIDATE_ASSERTED')
    if task=='ANSWER_APPLICATION_QUESTION':request.update(question_type='MOTIVATION',max_words=100);o.update(expected_status='COMPLETE',desired_field=None)
   if which==3:add_history(r)
   r['metadata']['new_coverage_family']=True
   r['metadata']['parent_record_persisted']=False
   r['metadata']['ground_truth_sha256']=digest({'profile':r['input']['profile'],'rag':r['input']['rag'],'oracle':o})
   rows.append(r)
 # Trusted/missing field worlds share candidate/job background and remain together.
 for state in ['stored','missing']:
  f=copy.deepcopy(fs[2]);f['key']+='_'+state;f['group']='v2_field_routing';f['notes']+=['counterfactual']
  for task in ['ANSWER_APPLICATION_QUESTION','IDENTIFY_MISSING_INFORMATION']:
   r=diversify(build_record(f,task,600+len(rows),seed));request=r['input']['request'];o=r['oracle']
   request.update(question='Are you authorized to work in the United States, when can you start, and which work arrangement do you prefer?',question_type='ELIGIBILITY',max_words=100 if task=='ANSWER_APPLICATION_QUESTION' else None)
   o.update(expected_status='COMPLETE' if state=='stored' else 'USER_INPUT_REQUIRED',desired_field='work_authorization_availability_remote_preference')
   if state=='stored':
    facts={'work_authorization':'Authorized to work in the United States.','availability':'2026-12-01','remote_preference':'Prefers remote work; open to discussing a hybrid arrangement.'}
    for field,value in facts.items():put(r,field,value,'preferences')
    o['personal_fields']=facts
   r['metadata'].update(new_coverage_family=True,parent_record_persisted=False,counterfactual_group='v2_field_routing',ground_truth_sha256=digest({'profile':r['input']['profile'],'rag':r['input']['rag'],'oracle':o}))
   rows.append(r)
 return rows


def generate_catalog(seed=SEED):
 return [diversify(r) for r in read_parents()]+generate_new(seed)


def check_catalog(rows):
 from .contracts import validate_input
 from .grounding import validate_scenario
 from collections import defaultdict
 problems=[]
 for r in rows:
  problems.extend((r['scenario_id'],e) for e in validate_input(r['input'])+validate_scenario(r))
  if r['metadata']['ground_truth_sha256']!=digest({'profile':r['input']['profile'],'rag':r['input']['rag'],'oracle':r['oracle']}):problems.append((r['scenario_id'],'GROUND_TRUTH_HASH'))
  for e in r['input']['rag']:
   if len(e['content'])>640:problems.append((r['scenario_id'],'RAG_LENGTH'))
  for event in {f['event_id'] for f in r['input']['profile']['facts']}:
   fields={f['field']:f['value'] for f in r['input']['profile']['facts'] if f['event_id']==event}
   if 'start_date' in fields and ('end_date' not in fields or fields['start_date']>fields['end_date']):problems.append((r['scenario_id'],'CHRONOLOGY'))
 groups=defaultdict(set)
 for r in rows:
  for key in ['scenario_family','template_family','candidate_archetype','job_archetype','split_group']:groups[(key,r['metadata'][key])].add(r['split'])
 if any(len(v)>1 for v in groups.values()):problems.append(('catalog','SPLIT_OVERLAP'))
 ids=[r['scenario_id'] for r in rows]
 if len(ids)!=len(set(ids)):problems.append(('catalog','DUPLICATE_ID'))
 keys=[(r['input']['profile']['candidate_id'],r['input']['job']['job_id'],r['input']['task']) for r in rows]
 if len(keys)!=len(set(keys)):problems.append(('catalog','DUPLICATE_CANDIDATE_JOB_TASK'))
 if problems:raise ValueError(problems[:20])
 return {'status':'PASS','records':len(rows),'splits':dict(Counter(r['split'] for r in rows)),'maximum_rag_characters':max(len(e['content']) for r in rows for e in r['input']['rag'])}


def write_catalog(root=None):
 root=Path(root or ROOT/'scenarios'/'catalog-v2');rows=generate_catalog();audit=check_catalog(rows)
 root.mkdir(parents=True,exist_ok=True)
 payloads={'catalog.jsonl':rows,'catalog_inputs.jsonl':[{'scenario_id':r['scenario_id'],'input':r['input']} for r in rows]}
 for name,payload in payloads.items():
  text=''.join(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n' for x in payload);path=root/name
  if path.exists() and path.read_text()!=text:raise ValueError('refusing to overwrite '+str(path))
  if not path.exists():path.write_text(text)
 parent_hashes={name:hashlib.sha256((ROOT/'scenarios'/name).read_bytes()).hexdigest() for name in PARENTS+('pilot.jsonl','challenge.jsonl')}
 manifest={'version':VERSION,'status':'frozen_prospective_inputs_before_full_teacher_generation','authored_on':'2026-09-29','rationale':RATIONALE,'records':len(rows),'retained_technical_scenarios':143,'new_records':len(generate_new()),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parents_and_protected_inputs_sha256':parent_hashes,'sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in payloads},'full_teacher_outputs_consulted':False,'pilot_modified':False,'challenge_modified':False,'teacher_target_generation_performed':False,'selection_policy':'Use catalog v2 instead of the original full143+additions; never concatenate v1 and v2 as independent evidence.','coverage_saturation_claim':False,'audit':audit}
 text=json.dumps(manifest,indent=2)+'\n';path=root/'manifest.json'
 if path.exists() and path.read_text()!=text:raise ValueError('refusing to mutate manifest')
 if not path.exists():path.write_text(text)
 return manifest

if __name__=='__main__':
 print(json.dumps(write_catalog(),indent=2))
