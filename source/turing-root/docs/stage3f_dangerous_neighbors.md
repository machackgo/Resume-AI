# Stage 3F — dangerous neighbors and per-query review

All figures below are evaluation relevance, never support. Declared-pair inversion rates alone do not capture every error. These tables also show the actual top-one grade for every query and all direct-evidence survival failures. Full texts, scores, original ranks and provenance are in `results/stage3f/failure_analysis.json`; all metric regressions are in `regressions.json`.

## identity — candidate budget 5

| Need | Top 1 (grade) | Top 3 IDs | Direct evidence in top 3 | Declared pair inversions |
| --- | --- | --- | --- | --- |
| api_build | python_api_negative (1) | python_api_negative, fastapi_negative, python_api_positive | 1 | 2 |
| api_production | python_api_positive (2) | python_api_positive, fastapi_positive, api_production | 1 | 0 |
| docker | gcp (0) | gcp, azure, docker_positive | 1 | 0 |
| rag | built_negative (1) | built_negative, rag_positive, rag_negative | 1 | 0 |
| aws | aws_positive (3) | aws_positive, aws_negative, injection_negative | 1 | 0 |
| azure | aws_negative (3) | aws_negative, aws_positive, azure | 1 | 1 |
| gcp | aws_negative (1) | aws_negative, aws_positive, gcp | 1 | 2 |
| fastapi | fastapi_positive (3) | fastapi_positive, api_production, python_api_positive | 1 | 0 |
| pytorch | pytorch_positive (3) | pytorch_positive, pytorch_negative, inference_negative | 1 | 0 |
| qlora | lora_negative (3) | lora_negative, qlora_positive, quant_read | 1 | 0 |
| postgres | postgres_positive (3) | postgres_positive, postgres_negative, postgres_version | 1 | 2 |
| deep_learning | deep_learning_positive (3) | deep_learning_positive, pytorch_negative, pytorch_positive | 1 | 0 |
| inference | latency_generic (0) | latency_generic, inference_positive, model_qwen | 1 | 0 |
| built | built_positive (3) | built_positive, built_negative, rag_positive | 1 | 0 |
| deployed | deployed_positive (3) | deployed_positive, deployed_negative, aws_positive | 1 | 1 |
| designed | designed_positive (3) | designed_positive, designed_negative, implemented_arch | 1 | 0 |
| implemented | designed_positive (1) | designed_positive, designed_negative, implemented_arch | 1 | 1 |
| developed | observed_negative (3) | observed_negative, fastapi_positive, fastapi_negative | 1 | 0 |
| observed | observed_positive (3) | observed_positive, observed_negative, metadata_origin_positive | 1 | 0 |
| certificate | certificate_positive (3) | certificate_positive, injection_positive, certificate_negative | 1 | 2 |
| kubernetes | duplicate_3 (3) | duplicate_3, docker_negative, crowded_source | 1 | 0 |
| latency | latency_positive (3) | latency_positive, latency_increased, latency_inference40 | 1 | 1 |
| inference_latency | latency_inference30 (2) | latency_inference30, latency_inference40, latency_4 | 1 | 1 |
| lora | lora_positive (3) | lora_positive, qlora_negative, qlora_positive | 1 | 0 |
| training | inference_positive (1) | inference_positive, inference_negative, fourbit_inference | 1 | 5 |
| aws_verified | aws_verified (3) | aws_verified, injection_positive, aws_interest | 1 | 0 |
| aws_relevant | aws_interest (2) | aws_interest, aws_assertion, aws_verified | 1 | 0 |
| cpp | cpp (3) | cpp, cpp_negative, fourbit_inference | 1 | 0 |
| paraphrase | rag_positive (3) | rag_positive, built_negative, built_positive | 1 | 0 |
| current_version | current_v2 (3) | current_v2, metadata_origin_positive, production_docker | 1 | 0 |
| production_docker | production_docker (3) | production_docker, duplicate_3, metadata_origin_positive | 1 | 0 |
| model_name | model_qwen (3) | model_qwen, model_qwen_wrongversion, model_llama | 1 | 0 |
| postgres_version | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |


### api_build

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 3 | python_api_negative | 1 |
| api_production | 4 | python_api_negative | 1 |


### azure

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| azure | 3 | aws_positive | 2 |


### gcp

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| gcp | 3 | aws_negative | 1 |
| gcp | 3 | aws_positive | 2 |


### postgres

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| postgres_version | 3 | postgres_negative | 2 |
| postgres_other_version | 4 | postgres_negative | 2 |


### deployed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_positive | 3 | deployed_negative | 2 |


### implemented

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| implemented_arch | 3 | designed_positive | 1 |


### certificate

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_verified | 5 | certificate_negative | 3 |
| aws_wrongcert | 4 | certificate_negative | 3 |


### latency

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| latency_inference40 | 3 | latency_increased | 2 |


### inference_latency

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| latency_inference40 | 2 | latency_inference30 | 1 |


### training

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| training_positive | 5 | inference_positive | 1 |
| training_positive | 5 | fourbit_inference | 3 |
| inference_negative | 2 | inference_positive | 1 |
| deep_learning_negative | 4 | inference_positive | 1 |
| deep_learning_negative | 4 | fourbit_inference | 3 |


## identity — candidate budget 10

| Need | Top 1 (grade) | Top 3 IDs | Direct evidence in top 3 | Declared pair inversions |
| --- | --- | --- | --- | --- |
| api_build | python_api_negative (1) | python_api_negative, fastapi_negative, python_api_positive | 1 | 2 |
| api_production | python_api_positive (2) | python_api_positive, fastapi_positive, api_production | 1 | 0 |
| docker | gcp (0) | gcp, azure, docker_positive | 1 | 0 |
| rag | built_negative (1) | built_negative, rag_positive, rag_negative | 1 | 0 |
| aws | aws_positive (3) | aws_positive, aws_negative, injection_negative | 1 | 0 |
| azure | aws_negative (3) | aws_negative, aws_positive, azure | 1 | 1 |
| gcp | aws_negative (1) | aws_negative, aws_positive, gcp | 1 | 2 |
| fastapi | fastapi_positive (3) | fastapi_positive, api_production, python_api_positive | 1 | 0 |
| pytorch | pytorch_positive (3) | pytorch_positive, pytorch_negative, inference_negative | 1 | 0 |
| qlora | lora_negative (3) | lora_negative, qlora_positive, quant_read | 1 | 0 |
| postgres | postgres_positive (3) | postgres_positive, postgres_negative, postgres_version | 1 | 2 |
| deep_learning | deep_learning_positive (3) | deep_learning_positive, pytorch_negative, pytorch_positive | 1 | 0 |
| inference | latency_generic (0) | latency_generic, inference_positive, model_qwen | 1 | 0 |
| built | built_positive (3) | built_positive, built_negative, rag_positive | 1 | 0 |
| deployed | deployed_positive (3) | deployed_positive, deployed_negative, aws_positive | 1 | 2 |
| designed | designed_positive (3) | designed_positive, designed_negative, implemented_arch | 1 | 0 |
| implemented | designed_positive (1) | designed_positive, designed_negative, implemented_arch | 1 | 1 |
| developed | observed_negative (3) | observed_negative, fastapi_positive, fastapi_negative | 1 | 4 |
| observed | observed_positive (3) | observed_positive, observed_negative, metadata_origin_positive | 1 | 0 |
| certificate | certificate_positive (3) | certificate_positive, injection_positive, certificate_negative | 1 | 2 |
| kubernetes | duplicate_3 (3) | duplicate_3, docker_negative, crowded_source | 1 | 0 |
| latency | latency_positive (3) | latency_positive, latency_increased, latency_inference40 | 1 | 1 |
| inference_latency | latency_inference30 (2) | latency_inference30, latency_inference40, latency_4 | 1 | 1 |
| lora | lora_positive (3) | lora_positive, qlora_negative, qlora_positive | 1 | 0 |
| training | inference_positive (1) | inference_positive, inference_negative, fourbit_inference | 1 | 8 |
| aws_verified | aws_verified (3) | aws_verified, injection_positive, aws_interest | 1 | 0 |
| aws_relevant | aws_interest (2) | aws_interest, aws_assertion, aws_verified | 1 | 0 |
| cpp | cpp (3) | cpp, cpp_negative, fourbit_inference | 1 | 0 |
| paraphrase | rag_positive (3) | rag_positive, built_negative, built_positive | 1 | 0 |
| current_version | current_v2 (3) | current_v2, metadata_origin_positive, production_docker | 1 | 0 |
| production_docker | production_docker (3) | production_docker, duplicate_3, metadata_origin_positive | 1 | 0 |
| model_name | model_qwen (3) | model_qwen, model_qwen_wrongversion, model_llama | 1 | 0 |
| postgres_version | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |


### api_build

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 3 | python_api_negative | 1 |
| api_production | 4 | python_api_negative | 1 |


### azure

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| azure | 3 | aws_positive | 2 |


### gcp

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| gcp | 3 | aws_negative | 1 |
| gcp | 3 | aws_positive | 2 |


### postgres

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| postgres_version | 3 | postgres_negative | 2 |
| postgres_other_version | 4 | postgres_negative | 2 |


### deployed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_negative | 7 | deployed_negative | 2 |
| aws_positive | 3 | deployed_negative | 2 |


### implemented

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| implemented_arch | 3 | designed_positive | 1 |


### developed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| api_production | 10 | api_integrated | 8 |
| api_production | 10 | api_docs | 6 |
| api_production | 10 | python_api_negative | 9 |
| api_developed | 7 | api_docs | 6 |


### certificate

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_verified | 5 | certificate_negative | 3 |
| aws_wrongcert | 4 | certificate_negative | 3 |


### latency

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| latency_inference40 | 3 | latency_increased | 2 |


### inference_latency

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| latency_inference40 | 2 | latency_inference30 | 1 |


### training

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| training_positive | 5 | inference_positive | 1 |
| training_positive | 5 | fourbit_inference | 3 |
| inference_negative | 2 | inference_positive | 1 |
| deep_learning_positive | 8 | inference_positive | 1 |
| deep_learning_positive | 8 | training_negative | 7 |
| deep_learning_positive | 8 | fourbit_inference | 3 |
| deep_learning_negative | 4 | inference_positive | 1 |
| deep_learning_negative | 4 | fourbit_inference | 3 |


## identity — candidate budget 20

| Need | Top 1 (grade) | Top 3 IDs | Direct evidence in top 3 | Declared pair inversions |
| --- | --- | --- | --- | --- |
| api_build | python_api_negative (1) | python_api_negative, fastapi_negative, python_api_positive | 1 | 2 |
| api_production | python_api_positive (2) | python_api_positive, fastapi_positive, api_production | 1 | 0 |
| docker | gcp (0) | gcp, azure, docker_positive | 1 | 0 |
| rag | built_negative (1) | built_negative, rag_positive, rag_negative | 1 | 0 |
| aws | aws_positive (3) | aws_positive, aws_negative, injection_negative | 1 | 0 |
| azure | aws_negative (3) | aws_negative, aws_positive, azure | 1 | 1 |
| gcp | aws_negative (1) | aws_negative, aws_positive, gcp | 1 | 2 |
| fastapi | fastapi_positive (3) | fastapi_positive, api_production, python_api_positive | 1 | 0 |
| pytorch | pytorch_positive (3) | pytorch_positive, pytorch_negative, inference_negative | 1 | 0 |
| qlora | lora_negative (3) | lora_negative, qlora_positive, quant_read | 1 | 0 |
| postgres | postgres_positive (3) | postgres_positive, postgres_negative, postgres_version | 1 | 2 |
| deep_learning | deep_learning_positive (3) | deep_learning_positive, pytorch_negative, pytorch_positive | 1 | 0 |
| inference | latency_generic (0) | latency_generic, inference_positive, model_qwen | 1 | 0 |
| built | built_positive (3) | built_positive, built_negative, rag_positive | 1 | 0 |
| deployed | deployed_positive (3) | deployed_positive, deployed_negative, aws_positive | 1 | 2 |
| designed | designed_positive (3) | designed_positive, designed_negative, implemented_arch | 1 | 0 |
| implemented | designed_positive (1) | designed_positive, designed_negative, implemented_arch | 1 | 1 |
| developed | observed_negative (3) | observed_negative, fastapi_positive, fastapi_negative | 1 | 4 |
| observed | observed_positive (3) | observed_positive, observed_negative, metadata_origin_positive | 1 | 0 |
| certificate | certificate_positive (3) | certificate_positive, injection_positive, certificate_negative | 1 | 2 |
| kubernetes | duplicate_3 (3) | duplicate_3, docker_negative, crowded_source | 1 | 0 |
| latency | latency_positive (3) | latency_positive, latency_increased, latency_inference40 | 1 | 1 |
| inference_latency | latency_inference30 (2) | latency_inference30, latency_inference40, latency_4 | 1 | 1 |
| lora | lora_positive (3) | lora_positive, qlora_negative, qlora_positive | 1 | 0 |
| training | inference_positive (1) | inference_positive, inference_negative, fourbit_inference | 1 | 17 |
| aws_verified | aws_verified (3) | aws_verified, injection_positive, aws_interest | 1 | 0 |
| aws_relevant | aws_interest (2) | aws_interest, aws_assertion, aws_verified | 1 | 0 |
| cpp | cpp (3) | cpp, cpp_negative, fourbit_inference | 1 | 0 |
| paraphrase | rag_positive (3) | rag_positive, built_negative, built_positive | 1 | 0 |
| current_version | current_v2 (3) | current_v2, metadata_origin_positive, production_docker | 1 | 0 |
| production_docker | production_docker (3) | production_docker, duplicate_3, metadata_origin_positive | 1 | 0 |
| model_name | model_qwen (3) | model_qwen, model_qwen_wrongversion, model_llama | 1 | 0 |
| postgres_version | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |


### api_build

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 3 | python_api_negative | 1 |
| api_production | 4 | python_api_negative | 1 |


### azure

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| azure | 3 | aws_positive | 2 |


### gcp

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| gcp | 3 | aws_negative | 1 |
| gcp | 3 | aws_positive | 2 |


### postgres

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| postgres_version | 3 | postgres_negative | 2 |
| postgres_other_version | 4 | postgres_negative | 2 |


### deployed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_negative | 7 | deployed_negative | 2 |
| aws_positive | 3 | deployed_negative | 2 |


### implemented

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| implemented_arch | 3 | designed_positive | 1 |


### developed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| api_production | 10 | api_integrated | 8 |
| api_production | 10 | api_docs | 6 |
| api_production | 10 | python_api_negative | 9 |
| api_developed | 7 | api_docs | 6 |


### certificate

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_verified | 5 | certificate_negative | 3 |
| aws_wrongcert | 4 | certificate_negative | 3 |


### latency

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| latency_inference40 | 3 | latency_increased | 2 |


### inference_latency

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| latency_inference40 | 2 | latency_inference30 | 1 |


### training

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| training_positive | 5 | inference_positive | 1 |
| training_positive | 5 | fourbit_inference | 3 |
| lora_positive | 11 | inference_positive | 1 |
| lora_positive | 11 | training_negative | 7 |
| lora_positive | 11 | fourbit_inference | 3 |
| qlora_negative | 14 | inference_positive | 1 |
| qlora_negative | 14 | training_negative | 7 |
| qlora_negative | 14 | fourbit_inference | 3 |
| inference_negative | 2 | inference_positive | 1 |
| deep_learning_positive | 8 | inference_positive | 1 |
| deep_learning_positive | 8 | training_negative | 7 |
| deep_learning_positive | 8 | fourbit_inference | 3 |
| deep_learning_negative | 4 | inference_positive | 1 |
| deep_learning_negative | 4 | fourbit_inference | 3 |
| pytorch_negative | 18 | inference_positive | 1 |
| pytorch_negative | 18 | training_negative | 7 |
| pytorch_negative | 18 | fourbit_inference | 3 |


## minilm — candidate budget 5

| Need | Top 1 (grade) | Top 3 IDs | Direct evidence in top 3 | Declared pair inversions |
| --- | --- | --- | --- | --- |
| api_build | python_api_negative (1) | python_api_negative, api_production, python_api_positive | 1 | 2 |
| api_production | api_production (3) | api_production, api_docs, python_api_positive | 1 | 0 |
| docker | gcp (0) | gcp, azure, docker_positive | 1 | 0 |
| rag | built_negative (1) | built_negative, rag_positive, rag_negative | 1 | 0 |
| aws | metadata_verification_positive (0) | metadata_verification_positive, injection_negative, injection_positive | 0 | 1 |
| azure | azure (3) | azure, aws_negative, kube_interest | 1 | 0 |
| gcp | gcp (3) | gcp, kube_interest, aws_negative | 1 | 0 |
| fastapi | api_production (3) | api_production, python_api_positive, fastapi_positive | 1 | 0 |
| pytorch | pytorch_positive (3) | pytorch_positive, deep_learning_positive, pytorch_negative | 1 | 0 |
| qlora | qlora_positive (3) | qlora_positive, lora_negative, quant_read | 1 | 0 |
| postgres | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |
| deep_learning | pytorch_positive (3) | pytorch_positive, pytorch_negative, fourbit_inference | 1 | 0 |
| inference | fourbit_inference (1) | fourbit_inference, latency_generic, model_qwen | 0 | 0 |
| built | built_positive (3) | built_positive, built_negative, rag_positive | 1 | 0 |
| deployed | deployed_negative (1) | deployed_negative, deployed_positive, designed_negative | 1 | 2 |
| designed | designed_positive (3) | designed_positive, implemented_arch, designed_negative | 1 | 0 |
| implemented | implemented_arch (3) | implemented_arch, designed_negative, designed_positive | 1 | 0 |
| developed | observed_negative (3) | observed_negative, observed_positive, fastapi_positive | 1 | 0 |
| observed | observed_positive (3) | observed_positive, observed_negative, metadata_origin_positive | 1 | 0 |
| certificate | injection_positive (3) | injection_positive, certificate_positive, aws_wrongcert | 1 | 0 |
| kubernetes | duplicate_3 (3) | duplicate_3, crowded_source, crowded_source | 1 | 0 |
| latency | latency_inference40 (3) | latency_inference40, latency_positive, latency_inference30 | 1 | 0 |
| inference_latency | latency_inference40 (3) | latency_inference40, latency_inference30, latency_increased | 1 | 0 |
| lora | lora_positive (3) | lora_positive, qlora_negative, qlora_positive | 1 | 0 |
| training | deep_learning_negative (3) | deep_learning_negative, inference_negative, inference_positive | 1 | 2 |
| aws_verified | aws_verified (3) | aws_verified, aws_interest, aws_wrongcert | 1 | 0 |
| aws_relevant | aws_assertion (3) | aws_assertion, aws_verified, aws_interest | 1 | 0 |
| cpp | cpp (3) | cpp, cpp_negative, fourbit_inference | 1 | 0 |
| paraphrase | rag_positive (3) | rag_positive, built_positive, rag_negative | 1 | 0 |
| current_version | current_v2 (3) | current_v2, metadata_origin_positive, production_docker | 1 | 0 |
| production_docker | production_docker (3) | production_docker, metadata_origin_positive, duplicate_3 | 1 | 0 |
| model_name | model_qwen (3) | model_qwen, model_qwen_wrongversion, model_llama | 1 | 0 |
| postgres_version | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |


### api_build

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 3 | python_api_negative | 1 |
| api_production | 2 | python_api_negative | 1 |


### aws

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_positive | 5 | aws_negative | 4 |


### deployed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| deployed_positive | 2 | deployed_negative | 1 |
| aws_positive | 4 | deployed_negative | 1 |


### training

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| training_positive | 5 | inference_positive | 3 |
| training_positive | 5 | fourbit_inference | 4 |


## minilm — candidate budget 10

| Need | Top 1 (grade) | Top 3 IDs | Direct evidence in top 3 | Declared pair inversions |
| --- | --- | --- | --- | --- |
| api_build | python_api_negative (1) | python_api_negative, api_production, api_integrated | 1 | 3 |
| api_production | api_production (3) | api_production, api_docs, python_api_positive | 1 | 0 |
| docker | gcp (0) | gcp, azure, production_docker | 0 | 0 |
| rag | built_negative (1) | built_negative, built_positive, rag_positive | 1 | 0 |
| aws | metadata_verification_positive (0) | metadata_verification_positive, injection_negative, aws_verified | 0 | 1 |
| azure | azure (3) | azure, aws_negative, designed_negative | 1 | 0 |
| gcp | designed_negative (0) | designed_negative, gcp, kube_interest | 1 | 0 |
| fastapi | api_production (3) | api_production, python_api_positive, fastapi_positive | 1 | 0 |
| pytorch | pytorch_positive (3) | pytorch_positive, deep_learning_positive, pytorch_negative | 1 | 0 |
| qlora | qlora_positive (3) | qlora_positive, lora_negative, quant_read | 1 | 0 |
| postgres | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |
| deep_learning | kube_malicious (0) | kube_malicious, latency_4, latency_inference30 | 0 | 0 |
| inference | gcp (2) | gcp, azure, fourbit_inference | 0 | 0 |
| built | built_positive (3) | built_positive, built_negative, rag_positive | 1 | 0 |
| deployed | frontend (1) | frontend, deployed_negative, deployed_positive | 1 | 3 |
| designed | designed_positive (3) | designed_positive, implemented_arch, designed_negative | 1 | 0 |
| implemented | implemented_arch (3) | implemented_arch, designed_negative, designed_positive | 1 | 0 |
| developed | api_developed (3) | api_developed, observed_negative, api_integrated | 1 | 9 |
| observed | observed_positive (3) | observed_positive, observed_negative, implemented_arch | 1 | 0 |
| certificate | injection_positive (3) | injection_positive, certificate_positive, aws_wrongcert | 1 | 0 |
| kubernetes | duplicate_3 (3) | duplicate_3, crowded_source, crowded_source | 1 | 0 |
| latency | latency_inference40 (3) | latency_inference40, latency_positive, latency_inference30 | 1 | 0 |
| inference_latency | latency_inference40 (3) | latency_inference40, latency_inference30, latency_increased | 1 | 0 |
| lora | lora_positive (3) | lora_positive, qlora_negative, qlora_positive | 1 | 0 |
| training | deep_learning_negative (3) | deep_learning_negative, inference_negative, inference_positive | 1 | 6 |
| aws_verified | aws_verified (3) | aws_verified, aws_interest, aws_wrongcert | 1 | 0 |
| aws_relevant | aws_assertion (3) | aws_assertion, aws_verified, aws_interest | 1 | 0 |
| cpp | cpp (3) | cpp, cpp_negative, fourbit_inference | 1 | 0 |
| paraphrase | rag_positive (3) | rag_positive, built_positive, rag_negative | 1 | 0 |
| current_version | current_v2 (3) | current_v2, metadata_origin_positive, production_docker | 1 | 0 |
| production_docker | production_docker (3) | production_docker, metadata_origin_positive, duplicate_3 | 1 | 0 |
| model_name | model_qwen (3) | model_qwen, model_qwen_wrongversion, model_llama | 1 | 0 |
| postgres_version | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |


### api_build

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 4 | api_integrated | 3 |
| python_api_positive | 4 | python_api_negative | 1 |
| api_production | 2 | python_api_negative | 1 |


### aws

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_positive | 9 | aws_negative | 8 |


### deployed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_negative | 10 | deployed_negative | 2 |
| deployed_positive | 3 | deployed_negative | 2 |
| aws_positive | 6 | deployed_negative | 2 |


### developed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 8 | api_integrated | 3 |
| python_api_positive | 8 | api_docs | 5 |
| observed_positive | 4 | api_integrated | 3 |
| api_production | 9 | api_integrated | 3 |
| api_production | 9 | api_docs | 5 |
| fastapi_negative | 7 | api_integrated | 3 |
| fastapi_negative | 7 | api_docs | 5 |
| fastapi_positive | 6 | api_integrated | 3 |
| fastapi_positive | 6 | api_docs | 5 |


### training

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| training_positive | 8 | inference_positive | 3 |
| training_positive | 8 | training_negative | 5 |
| training_positive | 8 | fourbit_inference | 4 |
| deep_learning_positive | 6 | inference_positive | 3 |
| deep_learning_positive | 6 | training_negative | 5 |
| deep_learning_positive | 6 | fourbit_inference | 4 |


## minilm — candidate budget 20

| Need | Top 1 (grade) | Top 3 IDs | Direct evidence in top 3 | Declared pair inversions |
| --- | --- | --- | --- | --- |
| api_build | python_api_negative (1) | python_api_negative, api_production, api_integrated | 1 | 3 |
| api_production | api_production (3) | api_production, api_docs, python_api_positive | 1 | 0 |
| docker | gcp (0) | gcp, azure, model_qwen | 0 | 0 |
| rag | built_negative (1) | built_negative, built_positive, rag_positive | 1 | 0 |
| aws | metadata_verification_positive (0) | metadata_verification_positive, injection_negative, aws_verified | 0 | 1 |
| azure | azure (3) | azure, aws_negative, designed_negative | 1 | 0 |
| gcp | designed_negative (0) | designed_negative, gcp, kube_interest | 1 | 0 |
| fastapi | api_production (3) | api_production, python_api_positive, fastapi_positive | 1 | 0 |
| pytorch | pytorch_positive (3) | pytorch_positive, deep_learning_positive, pytorch_negative | 1 | 0 |
| qlora | qlora_positive (3) | qlora_positive, lora_negative, quant_read | 1 | 0 |
| postgres | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |
| deep_learning | kube_interest (0) | kube_interest, kube_malicious, latency_4 | 0 | 0 |
| inference | gcp (2) | gcp, azure, fourbit_inference | 0 | 0 |
| built | built_positive (3) | built_positive, built_negative, rag_positive | 1 | 0 |
| deployed | frontend (1) | frontend, deployed_negative, deployed_positive | 1 | 3 |
| designed | designed_positive (3) | designed_positive, implemented_arch, designed_negative | 1 | 0 |
| implemented | implemented_arch (3) | implemented_arch, designed_negative, designed_positive | 1 | 0 |
| developed | api_developed (3) | api_developed, observed_negative, api_integrated | 1 | 9 |
| observed | observed_positive (3) | observed_positive, observed_negative, implemented_arch | 1 | 0 |
| certificate | injection_positive (3) | injection_positive, certificate_positive, aws_wrongcert | 1 | 0 |
| kubernetes | kube_manifest (3) | kube_manifest, duplicate_3, crowded_source | 1 | 0 |
| latency | latency_inference40 (3) | latency_inference40, latency_positive, latency_inference30 | 1 | 0 |
| inference_latency | latency_inference40 (3) | latency_inference40, latency_inference30, latency_increased | 1 | 0 |
| lora | lora_positive (3) | lora_positive, qlora_negative, qlora_positive | 1 | 0 |
| training | qlora_negative (3) | qlora_negative, lora_positive, deep_learning_negative | 1 | 9 |
| aws_verified | aws_verified (3) | aws_verified, aws_interest, aws_wrongcert | 1 | 0 |
| aws_relevant | aws_assertion (3) | aws_assertion, aws_verified, aws_interest | 1 | 0 |
| cpp | cpp (3) | cpp, cpp_negative, model_qwen | 1 | 0 |
| paraphrase | rag_positive (3) | rag_positive, built_positive, rag_negative | 1 | 0 |
| current_version | current_v2 (3) | current_v2, metadata_origin_positive, production_docker | 1 | 0 |
| production_docker | production_docker (3) | production_docker, metadata_origin_positive, duplicate_3 | 1 | 0 |
| model_name | model_qwen (3) | model_qwen, model_qwen_wrongversion, model_llama | 1 | 0 |
| postgres_version | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |


### api_build

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 4 | api_integrated | 3 |
| python_api_positive | 4 | python_api_negative | 1 |
| api_production | 2 | python_api_negative | 1 |


### aws

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_positive | 10 | aws_negative | 9 |


### deployed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_negative | 12 | deployed_negative | 2 |
| deployed_positive | 3 | deployed_negative | 2 |
| aws_positive | 7 | deployed_negative | 2 |


### developed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 10 | api_integrated | 3 |
| python_api_positive | 10 | api_docs | 5 |
| observed_positive | 4 | api_integrated | 3 |
| api_production | 12 | api_integrated | 3 |
| api_production | 12 | api_docs | 5 |
| fastapi_negative | 7 | api_integrated | 3 |
| fastapi_negative | 7 | api_docs | 5 |
| fastapi_positive | 6 | api_integrated | 3 |
| fastapi_positive | 6 | api_docs | 5 |


### training

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| training_positive | 11 | inference_positive | 5 |
| training_positive | 11 | training_negative | 7 |
| training_positive | 11 | fourbit_inference | 6 |
| deep_learning_positive | 9 | inference_positive | 5 |
| deep_learning_positive | 9 | training_negative | 7 |
| deep_learning_positive | 9 | fourbit_inference | 6 |
| pytorch_negative | 14 | inference_positive | 5 |
| pytorch_negative | 14 | training_negative | 7 |
| pytorch_negative | 14 | fourbit_inference | 6 |


## tinybert — candidate budget 5

| Need | Top 1 (grade) | Top 3 IDs | Direct evidence in top 3 | Declared pair inversions |
| --- | --- | --- | --- | --- |
| api_build | api_production (3) | api_production, python_api_negative, python_api_positive | 1 | 1 |
| api_production | api_production (3) | api_production, api_docs, python_api_positive | 1 | 0 |
| docker | azure (0) | azure, gcp, docker_positive | 1 | 0 |
| rag | built_negative (1) | built_negative, model_qwen, model_qwen_wrongversion | 0 | 1 |
| aws | injection_negative (0) | injection_negative, injection_positive, metadata_verification_positive | 0 | 0 |
| azure | azure (3) | azure, aws_negative, kube_interest | 1 | 0 |
| gcp | gcp (3) | gcp, kube_interest, aws_positive | 1 | 0 |
| fastapi | api_production (3) | api_production, python_api_positive, fastapi_positive | 1 | 0 |
| pytorch | pytorch_positive (3) | pytorch_positive, deep_learning_positive, pytorch_negative | 1 | 0 |
| qlora | qlora_positive (3) | qlora_positive, lora_negative, quant_read | 1 | 0 |
| postgres | postgres_other_version (3) | postgres_other_version, postgres_version, postgres_positive | 1 | 0 |
| deep_learning | pytorch_negative (3) | pytorch_negative, pytorch_positive, fourbit_inference | 1 | 0 |
| inference | latency_generic (0) | latency_generic, fourbit_inference, model_qwen | 0 | 0 |
| built | built_negative (1) | built_negative, built_positive, rag_positive | 1 | 1 |
| deployed | designed_negative (0) | designed_negative, deployed_positive, deployed_negative | 1 | 1 |
| designed | implemented_arch (1) | implemented_arch, designed_positive, designed_negative | 1 | 1 |
| implemented | implemented_arch (3) | implemented_arch, designed_negative, designed_positive | 1 | 0 |
| developed | observed_negative (3) | observed_negative, observed_positive, fastapi_negative | 1 | 0 |
| observed | observed_positive (3) | observed_positive, observed_negative, metadata_origin_positive | 1 | 0 |
| certificate | injection_positive (3) | injection_positive, aws_wrongcert, aws_verified | 1 | 0 |
| kubernetes | duplicate_3 (3) | duplicate_3, crowded_source, crowded_source | 1 | 0 |
| latency | latency_inference40 (3) | latency_inference40, latency_inference30, latency_positive | 1 | 1 |
| inference_latency | latency_inference40 (3) | latency_inference40, latency_inference30, latency_4 | 1 | 0 |
| lora | qlora_negative (3) | qlora_negative, lora_positive, qlora_positive | 1 | 0 |
| training | deep_learning_negative (3) | deep_learning_negative, inference_negative, fourbit_inference | 1 | 2 |
| aws_verified | aws_verified (3) | aws_verified, aws_assertion, aws_interest | 1 | 0 |
| aws_relevant | aws_assertion (3) | aws_assertion, aws_interest, aws_verified | 1 | 0 |
| cpp | cpp (3) | cpp, cpp_negative, fourbit_inference | 1 | 0 |
| paraphrase | rag_positive (3) | rag_positive, observed_positive, built_positive | 1 | 0 |
| current_version | current_v2 (3) | current_v2, metadata_origin_positive, docker_positive | 1 | 0 |
| production_docker | production_docker (3) | production_docker, metadata_origin_positive, duplicate_3 | 1 | 0 |
| model_name | model_qwen (3) | model_qwen, model_qwen_wrongversion, model_llama | 1 | 0 |
| postgres_version | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |


### api_build

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 3 | python_api_negative | 2 |


### rag

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| rag_positive | 5 | rag_negative | 4 |


### built

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| built_positive | 2 | built_negative | 1 |


### deployed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_positive | 4 | deployed_negative | 3 |


### designed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| designed_positive | 2 | implemented_arch | 1 |


### latency

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| latency_positive | 3 | latency_inference30 | 2 |


### training

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| training_positive | 5 | inference_positive | 4 |
| training_positive | 5 | fourbit_inference | 3 |


## tinybert — candidate budget 10

| Need | Top 1 (grade) | Top 3 IDs | Direct evidence in top 3 | Declared pair inversions |
| --- | --- | --- | --- | --- |
| api_build | api_production (3) | api_production, python_api_negative, cpp_negative | 1 | 2 |
| api_production | api_production (3) | api_production, api_docs, api_developed | 1 | 0 |
| docker | azure (0) | azure, gcp, production_docker | 0 | 0 |
| rag | built_negative (1) | built_negative, built_positive, api_integrated | 0 | 1 |
| aws | aws_assertion (0) | aws_assertion, injection_negative, aws_interest | 0 | 0 |
| azure | azure (3) | azure, aws_negative, designed_negative | 1 | 0 |
| gcp | designed_negative (0) | designed_negative, gcp, kube_interest | 1 | 0 |
| fastapi | api_production (3) | api_production, python_api_positive, fastapi_positive | 1 | 0 |
| pytorch | pytorch_positive (3) | pytorch_positive, deep_learning_positive, pytorch_negative | 1 | 0 |
| qlora | qlora_positive (3) | qlora_positive, lora_negative, quant_read | 1 | 0 |
| postgres | postgres_other_version (3) | postgres_other_version, postgres_version, postgres_positive | 1 | 0 |
| deep_learning | kube_malicious (0) | kube_malicious, latency_inference40, quant_read | 0 | 0 |
| inference | gcp (2) | gcp, azure, latency_generic | 0 | 0 |
| built | built_negative (1) | built_negative, built_positive, rag_positive | 1 | 1 |
| deployed | frontend (1) | frontend, designed_negative, deployed_positive | 1 | 2 |
| designed | implemented_arch (1) | implemented_arch, designed_positive, designed_negative | 1 | 1 |
| implemented | implemented_arch (3) | implemented_arch, designed_negative, designed_positive | 1 | 0 |
| developed | api_developed (3) | api_developed, api_integrated, observed_negative | 1 | 11 |
| observed | observed_positive (3) | observed_positive, observed_negative, implemented_arch | 1 | 0 |
| certificate | injection_positive (3) | injection_positive, aws_wrongcert, aws_verified | 1 | 0 |
| kubernetes | duplicate_3 (3) | duplicate_3, crowded_source, crowded_source | 1 | 0 |
| latency | latency_inference40 (3) | latency_inference40, latency_inference30, latency_positive | 1 | 1 |
| inference_latency | latency_inference40 (3) | latency_inference40, latency_inference30, latency_4 | 1 | 0 |
| lora | qlora_negative (3) | qlora_negative, lora_positive, qlora_positive | 1 | 0 |
| training | deep_learning_negative (3) | deep_learning_negative, inference_negative, fourbit_inference | 1 | 6 |
| aws_verified | aws_verified (3) | aws_verified, aws_assertion, aws_interest | 1 | 0 |
| aws_relevant | aws_assertion (3) | aws_assertion, aws_interest, aws_verified | 1 | 0 |
| cpp | cpp (3) | cpp, cpp_negative, latency_inference40 | 1 | 0 |
| paraphrase | rag_positive (3) | rag_positive, observed_positive, built_positive | 1 | 0 |
| current_version | current_v2 (3) | current_v2, metadata_origin_positive, docker_positive | 1 | 0 |
| production_docker | production_docker (3) | production_docker, metadata_origin_positive, duplicate_3 | 1 | 0 |
| model_name | model_qwen (3) | model_qwen, model_qwen_wrongversion, model_llama | 1 | 0 |
| postgres_version | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |


### api_build

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 5 | api_integrated | 4 |
| python_api_positive | 5 | python_api_negative | 2 |


### rag

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| rag_positive | 9 | rag_negative | 8 |


### built

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| built_positive | 2 | built_negative | 1 |


### deployed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_negative | 10 | deployed_negative | 4 |
| aws_positive | 5 | deployed_negative | 4 |


### designed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| designed_positive | 2 | implemented_arch | 1 |


### developed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 10 | api_integrated | 2 |
| python_api_positive | 10 | api_docs | 5 |
| python_api_positive | 10 | python_api_negative | 9 |
| observed_positive | 4 | api_integrated | 2 |
| api_production | 8 | api_integrated | 2 |
| api_production | 8 | api_docs | 5 |
| observed_negative | 3 | api_integrated | 2 |
| fastapi_negative | 6 | api_integrated | 2 |
| fastapi_negative | 6 | api_docs | 5 |
| fastapi_positive | 7 | api_integrated | 2 |
| fastapi_positive | 7 | api_docs | 5 |


### latency

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| latency_positive | 3 | latency_inference30 | 2 |


### training

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| training_positive | 8 | inference_positive | 4 |
| training_positive | 8 | training_negative | 6 |
| training_positive | 8 | fourbit_inference | 3 |
| deep_learning_positive | 7 | inference_positive | 4 |
| deep_learning_positive | 7 | training_negative | 6 |
| deep_learning_positive | 7 | fourbit_inference | 3 |


## tinybert — candidate budget 20

| Need | Top 1 (grade) | Top 3 IDs | Direct evidence in top 3 | Declared pair inversions |
| --- | --- | --- | --- | --- |
| api_build | api_production (3) | api_production, python_api_negative, cpp_negative | 1 | 2 |
| api_production | api_production (3) | api_production, api_docs, api_developed | 1 | 0 |
| docker | azure (0) | azure, gcp, production_docker | 0 | 0 |
| rag | built_negative (1) | built_negative, built_positive, latency_generic | 0 | 1 |
| aws | aws_assertion (0) | aws_assertion, injection_negative, aws_interest | 0 | 0 |
| azure | azure (3) | azure, aws_negative, designed_negative | 1 | 0 |
| gcp | designed_negative (0) | designed_negative, gcp, kube_interest | 1 | 0 |
| fastapi | api_production (3) | api_production, python_api_positive, fastapi_positive | 1 | 0 |
| pytorch | pytorch_positive (3) | pytorch_positive, deep_learning_positive, pytorch_negative | 1 | 0 |
| qlora | qlora_positive (3) | qlora_positive, lora_negative, quant_read | 1 | 0 |
| postgres | postgres_other_version (3) | postgres_other_version, postgres_version, postgres_positive | 1 | 0 |
| deep_learning | kube_interest (0) | kube_interest, kube_malicious, lora_positive | 0 | 0 |
| inference | gcp (2) | gcp, azure, latency_generic | 0 | 0 |
| built | built_negative (1) | built_negative, built_positive, rag_positive | 1 | 1 |
| deployed | frontend (1) | frontend, designed_negative, production_docker | 0 | 2 |
| designed | implemented_arch (1) | implemented_arch, designed_positive, designed_negative | 1 | 1 |
| implemented | implemented_arch (3) | implemented_arch, designed_negative, designed_positive | 1 | 0 |
| developed | api_developed (3) | api_developed, api_integrated, observed_negative | 1 | 11 |
| observed | observed_positive (3) | observed_positive, observed_negative, implemented_arch | 1 | 0 |
| certificate | injection_positive (3) | injection_positive, aws_wrongcert, aws_verified | 1 | 0 |
| kubernetes | kube_manifest (3) | kube_manifest, duplicate_3, crowded_source | 1 | 0 |
| latency | latency_inference40 (3) | latency_inference40, latency_inference30, latency_positive | 1 | 1 |
| inference_latency | latency_inference40 (3) | latency_inference40, latency_inference30, latency_4 | 1 | 0 |
| lora | qlora_negative (3) | qlora_negative, lora_positive, qlora_positive | 1 | 0 |
| training | deep_learning_negative (3) | deep_learning_negative, inference_negative, fourbit_inference | 1 | 12 |
| aws_verified | aws_verified (3) | aws_verified, aws_assertion, aws_interest | 1 | 0 |
| aws_relevant | aws_assertion (3) | aws_assertion, aws_interest, aws_verified | 1 | 0 |
| cpp | cpp (3) | cpp, cpp_negative, latency_increased | 1 | 0 |
| paraphrase | rag_positive (3) | rag_positive, observed_positive, built_positive | 1 | 0 |
| current_version | current_v2 (3) | current_v2, metadata_origin_positive, docker_positive | 1 | 0 |
| production_docker | production_docker (3) | production_docker, metadata_origin_positive, duplicate_3 | 1 | 0 |
| model_name | model_qwen (3) | model_qwen, model_qwen_wrongversion, model_llama | 1 | 0 |
| postgres_version | postgres_version (3) | postgres_version, postgres_other_version, postgres_positive | 1 | 0 |


### api_build

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 6 | api_integrated | 4 |
| python_api_positive | 6 | python_api_negative | 2 |


### rag

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| rag_positive | 17 | rag_negative | 15 |


### built

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| built_positive | 2 | built_negative | 1 |


### deployed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| aws_negative | 17 | deployed_negative | 5 |
| aws_positive | 6 | deployed_negative | 5 |


### designed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| designed_positive | 2 | implemented_arch | 1 |


### developed

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| python_api_positive | 13 | api_integrated | 2 |
| python_api_positive | 13 | api_docs | 5 |
| python_api_positive | 13 | python_api_negative | 12 |
| observed_positive | 4 | api_integrated | 2 |
| api_production | 8 | api_integrated | 2 |
| api_production | 8 | api_docs | 5 |
| observed_negative | 3 | api_integrated | 2 |
| fastapi_negative | 6 | api_integrated | 2 |
| fastapi_negative | 6 | api_docs | 5 |
| fastapi_positive | 7 | api_integrated | 2 |
| fastapi_positive | 7 | api_docs | 5 |


### latency

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| latency_positive | 3 | latency_inference30 | 2 |


### training

| Stronger evidence | Rank | Weaker evidence ranked above it | Rank |
| --- | --- | --- | --- |
| training_positive | 11 | inference_positive | 5 |
| training_positive | 11 | training_negative | 9 |
| training_positive | 11 | fourbit_inference | 3 |
| lora_positive | 4 | fourbit_inference | 3 |
| qlora_negative | 6 | inference_positive | 5 |
| qlora_negative | 6 | fourbit_inference | 3 |
| deep_learning_positive | 10 | inference_positive | 5 |
| deep_learning_positive | 10 | training_negative | 9 |
| deep_learning_positive | 10 | fourbit_inference | 3 |
| pytorch_negative | 15 | inference_positive | 5 |
| pytorch_negative | 15 | training_negative | 9 |
| pytorch_negative | 15 | fourbit_inference | 3 |


