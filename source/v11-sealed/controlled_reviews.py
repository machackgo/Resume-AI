"""Novel semantic controls, independent of acceptance answers."""
import json
from resume_pipeline.licensing import REVIEW_SYSTEM,validate_review
from rag.reasoning.contract import strict_parse

def run(model):
 examples=[
  dict(id='nested_classifier_component',claim='Built a Python classification pipeline using a scikit-learn decision tree for the Atlas course project.',heading='Atlas — university course project',requirement='Implemented Python classification using scikit-learn Gradient Boosting.',sources=['The candidate built a Python classification pipeline using a scikit-learn decision tree for the Atlas university course project. Gradient Boosting was not implemented.'],expected_support='SUPPORTED',expected_accepted=True),
  dict(id='explicit_negative_constraint',claim='Implemented the Atlas API with Flask.',heading='Atlas project',requirement='Implemented an API without Flask.',sources=['The candidate implemented the Atlas API using Flask. No non-Flask implementation exists.'],expected_support='SUPPORTED',expected_accepted=False),
  dict(id='narrow_true_claim',claim='Implemented a Python API in the Atlas course project.',heading='Atlas — university course project',requirement='Implemented Python APIs and Kubernetes deployments.',sources=['The candidate implemented a Python API in the Atlas university course project. No Kubernetes deployment was performed.'],expected_support='SUPPORTED',expected_accepted=True),
  dict(id='different_measurement_populations',claim='Trained a classifier on 8,000 usable sensor rows.',heading='Atlas sensor project',requirement='Trained a classifier.',sources=['Atlas used 12,000 raw sensor rows. Filtering missing labels left 8,000 usable rows used to train the classifier. The deployment cache holds 13,500 rows including later arrivals.'],expected_support='SUPPORTED',expected_accepted=True),
  dict(id='explicit_same_event_correction',claim='Deployed the Atlas service to production.',heading='Atlas project',requirement='Deployed a service to production.',sources=['An early Atlas summary said it was deployed to production. Correction: Atlas ran only on a classroom laptop; no production deployment occurred.'],expected_support='CONTRADICTED',expected_accepted=False),
  dict(id='cross_project_metric',claim='Reduced latency by 30% in the Atlas service.',heading='Atlas project',requirement='Reduced latency in the Boreal service.',sources=['The candidate reduced Atlas service latency by 30%. Boreal is a separate project; no Boreal latency result was recorded.'],expected_support='SUPPORTED',expected_accepted=False),
  dict(id='academic_not_employment',claim='Implemented a Python API for a university course.',heading='University coursework',requirement='Professional employment implementing Python APIs.',sources=['The candidate implemented a Python API for a university course. No professional employment is documented.'],expected_support='SUPPORTED',expected_accepted=False),
  dict(id='policy_not_achievement',claim='Deployment must finish before evaluation begins.',heading='Project evaluation policy',requirement='Completed deployment work.',sources=['Project policy: Deployment must finish before evaluation begins. This is an instruction, not a record of completed work.'],expected_support=None,expected_accepted=False)
 ]
 results=[]
 for e in examples:
  task=dict(event_id='event-synthetic-'+e['id'],claim=e['claim'],source_context={'text':e['heading']},attribution='candidate-supplied statement',requirements=[dict(requirement_id='r1',text=e['requirement'])],sources=[dict(evidence_id='s'+str(i),content=s) for i,s in enumerate(e['sources'])])
  from resume_pipeline.component_review import review_task
  review=None;error=None;obj=None;accepted=False
  try:
   review=review_task(model,task)
   obj={k:review[k] for k in ('support','eligibility','event_id','links','evidence_ids','counterevidence_ids','reason')}
   accepted=review['accepted']
  except Exception as ex:error=str(ex);review=getattr(ex,'trace',None)
  passed=not error and accepted==e['expected_accepted'] and (e['expected_support'] is None or obj['support']==e['expected_support'])
  record=dict(control=e,task=task,review=review,decision=obj,error=error,accepted=accepted,passed=passed)
  results.append(record)
  import os
  from pathlib import Path
  directory=os.environ.get('RESUME_REPAIR_RUN_DIR')
  if directory:
   with (Path(directory)/('control-'+e['id']+'.json')).open('x') as stream:json.dump(record,stream,indent=2)
  print('CONTROL',e['id'],passed,error,flush=True)
 return results
