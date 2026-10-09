"""Authored semantic families. No historical example strings or private profiles.
Each row: id, requested predicate, entailing paraphrase, related but insufficient
predicate, domain, requested action. Predicate identity is semantic, not lexical.
"""
ROWS = [
('container_orchestration','operated Kubernetes workloads','maintained live Kubernetes pods and handled their incidents','packaged an application as a Docker image','containers','operated'),
('container_helm','authored Helm deployment charts','created Helm chart templates and release values','edited Docker Compose services','containers','built'),
('container_swarm','operated Docker Swarm services','managed running Docker Swarm services and recovery','ran standalone Docker containers','containers','operated'),
('container_nomad','deployed services through Nomad','released service jobs using the Nomad scheduler','configured a Kubernetes namespace','containers','deployed'),
('container_podman','built images with Podman','created OCI images using Podman builds','created images using Docker builds','containers','built'),
('cloud_aws','deployed a worker on AWS','released the worker to Amazon Web Services','deployed a worker on Azure','cloud','deployed'),
('cloud_gcp','deployed an application on GCP','released the application on Google Cloud Platform','deployed an application on AWS','cloud','deployed'),
('cloud_azure','operated an Azure service','maintained the live service in Microsoft Azure','maintained a service in GCP','cloud','operated'),
('cloud_lambda','implemented an AWS Lambda function','wrote and tested the AWS Lambda handler','implemented an Azure Function','cloud','implemented'),
('cloud_cloudrun','deployed to Google Cloud Run','released the service to Google Cloud Run','deployed to Amazon ECS','cloud','deployed'),
('api_rest','built a REST endpoint','implemented request handlers for a REST endpoint','called a third-party REST endpoint','apis','built'),
('api_graphql','implemented a GraphQL server','wrote server-side GraphQL resolvers and schema','queried an external GraphQL endpoint','apis','implemented'),
('api_grpc','built a gRPC service','implemented the server handlers for a gRPC service','used a generated gRPC client','apis','built'),
('api_webhook','built a webhook receiver','implemented the HTTP handler accepting incoming webhooks','registered a webhook URL with a vendor','apis','built'),
('api_python','built Python web APIs','developed REST endpoints using Python and FastAPI','sent Python requests to external web APIs','apis','built'),
('framework_fastapi','implemented FastAPI routes','developed endpoint handlers with FastAPI','implemented Flask routes','frameworks','implemented'),
('framework_tensorflow','trained a TensorFlow model','optimized model parameters using TensorFlow training','trained a PyTorch model','frameworks','trained'),
('framework_pytorch','trained a PyTorch classifier','fit classifier parameters with PyTorch','trained a TensorFlow classifier','frameworks','trained'),
('framework_flask','built Flask endpoints','developed request handlers with Flask','built FastAPI endpoints','frameworks','built'),
('framework_jax','implemented a JAX training loop','wrote gradient updates and a training loop using JAX','implemented a PyTorch training loop','frameworks','implemented'),
('database_postgres','implemented PostgreSQL queries','wrote queries executed against PostgreSQL tables','studied generic SQL syntax','databases','implemented'),
('database_mysql','operated a MySQL database','managed backups and recovery for a running MySQL database','operated a PostgreSQL database','databases','operated'),
('database_redis','implemented Redis caching','wrote the application cache using Redis','implemented an in-process Python cache','databases','implemented'),
('database_mongo','built MongoDB aggregations','developed aggregation pipelines in MongoDB','queried JSON files with Python','databases','built'),
('database_pgvector','implemented pgvector similarity queries','created PostgreSQL vector searches with the pgvector extension','wrote ordinary PostgreSQL text queries','databases','implemented'),
('adaptation_qlora','fine-tuned model adapters with QLoRA','updated low-rank adapters through a frozen NF4 base model using QLoRA','updated LoRA adapters on a BF16 base model','adaptation','fine-tuned'),
('adaptation_nf4','performed QLoRA training','performed backward passes and optimizer updates on adapters over an NF4 base model','loaded a four-bit model for prediction','adaptation','trained'),
('adaptation_lora','trained LoRA adapters','optimized low-rank adapter weights during supervised training','loaded existing LoRA adapters for inference','adaptation','trained'),
('adaptation_full','fine-tuned base model weights','updated the base model parameters on supervised examples','retrieved context passages before inference','adaptation','fine-tuned'),
('adaptation_preference','trained with a preference objective','updated parameters using chosen and rejected response pairs','ranked outputs without any parameter updates','adaptation','trained'),
('rag_retrieval','implemented retrieval augmented generation','built passage retrieval and supplied those passages to the answer generator','completed a course about retrieval augmented generation','rag','implemented'),
('rag_finetuning','implemented task-specific fine-tuning','ran parameter updates on the task training corpus','implemented retrieval augmented generation over retrieved passages','rag','implemented'),
('rag_reranker','implemented a reranking service','built a service that reorders retrieved passages with a reranker','read an article about rerankers','rag','implemented'),
('rag_index','built a semantic retrieval index','implemented document embeddings and vector lookup for retrieval','searched documents with keyword matching','rag','built'),
('rag_evaluation','evaluated retrieval recall','measured retrieval recall against annotated relevant passages','reported language-model response latency','rag','evaluated'),
('lifecycle_production','operated the service in production','handled incidents and monitored the live production service','deployed the service once to a development host','mlops','operated'),
('lifecycle_deploy','deployed the inference service','released the inference server to a running remote environment','implemented an inference server locally','mlops','deployed'),
('lifecycle_train','trained a classifier','updated classifier weights over labeled training batches','ran predictions with a pretrained classifier','mlops','trained'),
('lifecycle_implement','implemented a model evaluator','wrote executable scoring code for model outputs','studied evaluation methods','mlops','implemented'),
('lifecycle_monitor','implemented model drift monitoring','built production alerts from measured feature drift','viewed a static model accuracy report','mlops','implemented'),
('numeric_latency','reduced p95 latency by exactly {n}%','achieved an exact {n}% reduction in p95 latency','reported a substantial latency improvement','metrics','reduced'),
('numeric_cost','saved exactly ${n} per month','recorded exactly ${n} in monthly cost savings','reported lower monthly costs','metrics','reduced'),
('numeric_throughput','achieved exactly {n} requests per second','measured throughput of exactly {n} requests per second','reported increased throughput','metrics','evaluated'),
('numeric_dataset','trained on exactly {n} records','used a training dataset containing exactly {n} records','described the training dataset as large','metrics','trained'),
('numeric_team','led exactly {n} contributors','coordinated a team containing exactly {n} contributors','mentioned coordinating a project team','metrics','led'),
('verified_aws','has independently verified AWS certification','holds AWS certification','claims AWS certification','credentials','verified'),
('verified_azure','has independently verified Azure certification','holds Azure certification','claims Azure certification','credentials','verified'),
('verified_ckad','has independently verified CKAD certification','holds CKAD certification','claims CKAD certification','credentials','verified'),
('verified_gcp','has independently verified GCP certification','holds GCP certification','claims GCP certification','credentials','verified'),
('verified_terraform','has independently verified Terraform certification','holds Terraform certification','claims Terraform certification','credentials','verified'),
('asserted_aws','reports holding an AWS certificate','states that they hold an AWS certificate','mentions studying AWS certification topics','assertions','reported'),
('asserted_azure','reports holding an Azure certificate','states that they hold an Azure certificate','mentions attending an Azure course','assertions','reported'),
('asserted_ckad','reports holding a CKAD certificate','states that they hold a CKAD certificate','mentions interest in CKAD certification','assertions','reported'),
('asserted_gcp','reports holding a GCP certificate','states that they hold a GCP certificate','mentions studying GCP exam material','assertions','reported'),
('asserted_terraform','reports holding a Terraform certificate','states that they hold a Terraform certificate','mentions reading Terraform certification guidance','assertions','reported'),
('operations_alerts','implemented Prometheus alerts','created Prometheus alerting rules and wired their evaluation','looked at an existing Prometheus dashboard','observability','implemented'),
('operations_otel','implemented OpenTelemetry tracing','instrumented service spans using OpenTelemetry','viewed trace screenshots in a design document','observability','implemented'),
('operations_ci','built a GitHub Actions workflow','authored CI job definitions in GitHub Actions','ran an existing GitHub Actions workflow','observability','built'),
('operations_terraform','built Terraform infrastructure modules','authored reusable Terraform resource modules','applied a Terraform module written by others','observability','built'),
('operations_grafana','built Grafana dashboards','authored Grafana panels and their data queries','viewed prebuilt Grafana dashboards','observability','built'),
]
CATALOG={r[0]:dict(id=r[0],claim=r[1],positive=r[2],adjacent=r[3],domain=r[4],action=r[5],category=r[0].split('_')[0]) for r in ROWS}
# Every substantive predicate family, all paraphrases and all counterfactuals stay together.
FAMILIES=list(CATALOG)
SPLITS={fid:('validation' if CATALOG[fid]['category']=='asserted' else 'test' if CATALOG[fid]['category']=='operations' else 'train') for fid in FAMILIES}
SECONDARY=[('implemented input validation','added executable validation checks for incoming requests','read about request validation'),('built automated service tests','wrote executable automated tests for the service','reviewed a testing guide'),('implemented structured logging','added structured event logging to the service','read example logging output')]
VERSION='stage4a-generator-v1'
SEED=410042
NOTICE='Retrieval membership does not prove support. No plausible candidate means retrieval absence, not contradiction or proof of corpus absence.'

DOMAIN_SECONDARY={
 'container': [('built a Docker image','created an application image with Docker','read a Docker tutorial'),('deployed the packaged service','released the packaged service to a running host','built the packaged service locally'),('operated the service in production','monitored the live production service and resolved incidents','tested the service on a laptop')],
 'cloud': [('built a Python service','implemented the service handlers in Python','used an existing Python service'),('containerized the service with Docker','packaged the service as a Docker image','studied containerization'),('implemented deployment health checks','wrote executable health checks for deployed instances','read a health-check specification')],
 'api': [('containerized the API with Docker','created a Docker image containing the API','read about Docker packaging'),('deployed the API service','released the API server to a running remote environment','ran API tests locally'),('deployed the API on AWS','released the API service to Amazon Web Services','deployed the API on Azure')],
 'framework': [('evaluated held-out model accuracy','measured model accuracy on held-out labeled examples','reported training loss only'),('deployed a model inference endpoint','released a running endpoint that serves model predictions','loaded a model in a notebook'),('implemented model monitoring','built alerts for production prediction drift','read a monitoring guide')],
 'database': [('implemented database backup automation','wrote scheduled executable database backup jobs','read a backup runbook'),('tested database restoration','executed a database restore and checked recovered records','configured backup storage only'),('operated the database in production','managed the live production database and handled incidents','ran a local development database')],
 'adaptation': [('evaluated the adapted model','measured the adapted model on a held-out test collection','reported training loss only'),('deployed an inference service','released a running service for model predictions','loaded a model locally'),('built a versioned dataset','created and versioned the training examples','read a dataset description')],
 'rag': [('implemented evidence citations','wrote code linking generated claims to retrieved evidence IDs','mentioned citation support in a plan'),('evaluated retrieval precision','measured retrieval precision against relevance annotations','reported generation speed only'),('deployed a retrieval service','released a running retrieval server','built a local retrieval prototype')],
 'lifecycle': SECONDARY,
 'numeric': [('implemented a performance benchmark','wrote an executable benchmark for the measured system','read a benchmark report'),('deployed the measured service','released the measured service to a running environment','built the measured service locally'),('documented the measurement procedure','wrote a reproducible procedure for the reported measurement','mentioned future measurement plans')],
 'verified': [('implemented a cloud deployment','built and executed a cloud deployment process','studied cloud deployment diagrams'),('operated a production cloud service','maintained a live production cloud service','ran a local service prototype'),('implemented cloud monitoring','built alerts from cloud service telemetry','read a cloud monitoring article')],
 'asserted': [('reports completing a cloud project','states that they completed a cloud project','mentions interest in a cloud project'),('reports deploying a service','states that they deployed a running service','mentions a future deployment plan'),('reports implementing service tests','states that they wrote executable service tests','mentions reading a testing guide')],
 'operations': SECONDARY,
}
