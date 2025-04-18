# Copyright 2024 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fastapi.testclient import TestClient

from sandbox.datasets.types import EvalResult, Prompt, TestConfig
from sandbox.server.online_judge_api import GetPromptByIdRequest, GetPromptsRequest, SubmitRequest
from sandbox.server.server import app

client = TestClient(app)


async def test_aider_benchmark_v1_get():
    request = GetPromptsRequest(dataset='aider_benchmark_v1', config=TestConfig())
    response = client.post('/get_prompts', json=request.model_dump())
    assert response.status_code == 200
    results = [Prompt(**sample) for sample in response.json()]
    assert len(results) == 5
    print(results)
    assert all('Please generate the code in the following format:' in r.prompt for r in results)
    assert all('Please answer in English with Markdown format.' not in r.prompt for r in results)


async def test_aider_benchmark_v1_get_wrap_prompt():
    request = GetPromptsRequest(dataset='aider_benchmark_v1', config=TestConfig(extra={'autoeval_wrap_prompt': True}))
    response = client.post('/get_prompts', json=request.model_dump())
    assert response.status_code == 200
    results = [Prompt(**sample) for sample in response.json()]
    assert len(results) == 5
    print(results)
    assert all('Please generate the code in the following format:' in r.prompt for r in results)
    assert all('Please answer in English with Markdown format.' in r.prompt for r in results)


async def test_aider_benchmark_v1_get_id():
    request = GetPromptByIdRequest(dataset='aider_benchmark_v1', id=1, config=TestConfig())
    response = client.post('/get_prompt_by_id', json=request.model_dump())
    assert response.status_code == 200
    result = Prompt(**response.json())
    assert 'Implement the `accumulate` operation' in result.prompt
    print(result.prompt)


async def test_aider_benchmark_v1_list_ids():
    request = GetPromptsRequest(dataset='aider_benchmark_v1', config=TestConfig())
    response = client.post('/list_ids', json=request.model_dump())
    assert response.status_code == 200
    result = response.json()
    assert result == list(range(1, 6))
    print(result)


async def test_aider_benchmark_submit_passed():
    request = SubmitRequest(
        dataset='aider_benchmark_v1',
        id=1,
        config=TestConfig(language='python'),
        completion='''
```python
def accumulate(collection, operation):
    response = []
    for ellement in collection:
        response.append(operation(ellement))
    return response
```
''',
    )
    response = client.post('/submit', json=request.model_dump())
    assert response.status_code == 200
    result = EvalResult(**response.json())
    print(result.full_code)
    print('=' * 60)
    print(result.test_code)
    print('=' * 60)
    print(result.tests[0].exec_info)
    assert result.accepted is True


async def test_aider_benchmark_submit_failed():
    request = SubmitRequest(
        dataset='aider_benchmark_v1',
        id=1,
        config=TestConfig(language='python'),
        completion='''
```python
def accumulate(collection, operation):
    pass
```
''',
    )
    response = client.post('/submit', json=request.model_dump())
    assert response.status_code == 200
    result = EvalResult(**response.json())
    assert result.accepted is False
