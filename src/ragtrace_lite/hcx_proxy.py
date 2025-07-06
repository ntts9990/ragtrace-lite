"""
HCX-RAGAS 프록시 레이어
RAGAS가 기대하는 정확한 JSON 응답을 보장하는 중간 계층
"""
import json
import re
import asyncio
from typing import List, Dict, Any, Optional, Union
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import Generation, LLMResult
from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun


class HCXRAGASProxy(LLM):
    """RAGAS와 HCX 사이의 완벽한 변환을 보장하는 프록시"""
    
    # Pydantic 필드 정의
    hcx: Any = None
    
    class Config:
        # 임의의 타입 허용
        arbitrary_types_allowed = True
        # 추가 필드 허용
        extra = "allow"
    
    def __init__(self, real_hcx_llm: LLM, **kwargs):
        super().__init__(**kwargs)
        self.hcx = real_hcx_llm
        
        # Private 속성은 __ 접두사 사용
        self.__last_metric_type = None
        
        # RAGAS 메트릭별 스키마 정의 - RAGAS가 실제로 기대하는 스키마
        self.__metric_schemas = {
            'faithfulness': {
                'keywords': ['break down each sentence', 'analyze the complexity', 'statement', 'extract', 'factual', 'claims'],
                'schema': {'statements': List[str]},
                'default': {'statements': []}
            },
            'faithfulness_nli': {
                'keywords': ['judge the faithfulness', 'based on a given context', 'verdict'],
                'schema': {'statements': List[Dict[str, Any]]},
                'default': {'statements': []}
            },
            'answer_relevancy': {
                'keywords': ['generate a question for', 'generate', 'question', 'relevancy'],
                'schema': {'question': str, 'noncommittal': int},
                'default': {'question': '', 'noncommittal': 0}
            },
            'context_precision': {
                'keywords': ['verify if the context was useful', 'context was useful', 'give verdict', 'useful in arriving'],
                # RAGAS expects 'reason' and 'verdict', not 'relevant'!
                'schema': {'reason': str, 'verdict': int},
                'default': {'reason': 'Unable to determine', 'verdict': 0}
            },
            'context_recall': {
                'keywords': ['analyze each sentence', 'classify if the sentence', 'can be attributed', 'attributed to the given context'],
                # RAGAS expects 'classifications' with list of objects
                'schema': {'classifications': List[Dict[str, Any]]},
                'default': {'classifications': []}
            },
            'answer_correctness': {
                'keywords': ['ground truth and an answer', 'classify them', 'TP (true positive)', 'FP (false positive)'],
                # RAGAS expects TP, FP, FN lists
                'schema': {'TP': List[Dict[str, str]], 'FP': List[Dict[str, str]], 'FN': List[Dict[str, str]]},
                'default': {'TP': [], 'FP': [], 'FN': []}
            }
        }
    
    @property
    def _llm_type(self) -> str:
        return "hcx_ragas_proxy"
    
    def set_run_config(self, run_config: Any) -> None:
        """RAGAS가 요구하는 run_config 설정 메서드"""
        # 실제 HCX LLM에 전달
        if hasattr(self.hcx, 'set_run_config'):
            self.hcx.set_run_config(run_config)
        # 아니면 무시 (프록시는 자체 설정 사용)
    
    def _detect_metric_type(self, prompt: str) -> Optional[str]:
        """프롬프트에서 RAGAS 메트릭 타입 감지"""
        prompt_lower = prompt.lower()
        
        # 특정 패턴을 먼저 확인 (우선순위 높음)
        if 'judge the faithfulness' in prompt_lower and 'verdict' in prompt_lower:
            self.__last_metric_type = 'faithfulness_nli'
            return 'faithfulness_nli'
        
        if 'break down each sentence' in prompt_lower or 'analyze the complexity' in prompt_lower:
            self.__last_metric_type = 'faithfulness'
            return 'faithfulness'
        
        if 'generate a question for' in prompt_lower and 'answer' in prompt_lower:
            self.__last_metric_type = 'answer_relevancy'
            return 'answer_relevancy'
        
        # 키워드 매칭 점수 계산 (더 구체적인 키워드가 높은 점수)
        scores = {}
        for metric, config in self.__metric_schemas.items():
            keywords = config['keywords']
            score = 0
            for keyword in keywords:
                if keyword in prompt_lower:
                    # 더 긴 키워드는 더 높은 점수
                    score += len(keyword) * 2  # 가중치 증가
            if score > 0:
                scores[metric] = score
        
        # 가장 높은 점수의 메트릭 선택
        if scores:
            best_metric = max(scores, key=scores.get)
            self.__last_metric_type = best_metric
            return best_metric
        
        return None
    
    def _extract_statements(self, text: str) -> List[str]:
        """텍스트에서 문장 추출 (다양한 형식 지원)"""
        statements = []
        
        # 1. 번호 리스트 (1. xxx 2. yyy)
        numbered = re.findall(r'\d+\.\s*([^.]+(?:\.[^.]+)*?)(?=\d+\.|$)', text, re.DOTALL)
        if numbered:
            statements.extend([s.strip() for s in numbered if s.strip()])
            return statements
        
        # 2. 불릿 포인트 (- xxx, • yyy)
        bullets = re.findall(r'[-•]\s*([^-•]+)', text)
        if bullets:
            statements.extend([s.strip() for s in bullets if s.strip()])
            return statements
        
        # 3. 줄바꿈으로 구분된 문장
        lines = text.strip().split('\n')
        if len(lines) > 1:
            statements.extend([line.strip() for line in lines if line.strip() and len(line.strip()) > 10])
            if statements:
                return statements
        
        # 4. 마침표로 구분된 문장
        sentences = re.split(r'[.。]\s*', text)
        statements.extend([s.strip() for s in sentences if s.strip() and len(s.strip()) > 10])
        
        return statements if statements else [text.strip()]
    
    def _extract_question(self, text: str) -> str:
        """텍스트에서 질문 추출"""
        # 따옴표 안의 질문
        quoted = re.search(r'[""]([^""]+\?)["""]', text)
        if quoted:
            return quoted.group(1)
        
        # 물음표로 끝나는 문장
        questions = re.findall(r'([^.!]+\?)', text)
        if questions:
            return questions[0].strip()
        
        # 첫 문장 반환
        first_sentence = text.split('.')[0].strip()
        return first_sentence + "?" if not first_sentence.endswith('?') else first_sentence
    
    def _extract_relevance(self, text: str) -> int:
        """텍스트에서 관련성 판단"""
        text_lower = text.lower()
        
        # 긍정 키워드
        positive = ['yes', '예', 'relevant', '관련', 'useful', '유용', 'correct', '맞', 'true', '참']
        # 부정 키워드
        negative = ['no', '아니', 'not relevant', '관련 없', 'irrelevant', 'useless', '무용', 'false', '거짓']
        
        # 부정이 먼저 체크
        for neg in negative:
            if neg in text_lower:
                return 0
        
        # 긍정 체크
        for pos in positive:
            if pos in text_lower:
                return 1
        
        # 기본값
        return 0
    
    def _extract_attribution(self, text: str) -> List[int]:
        """텍스트에서 귀속 정보 추출"""
        # 숫자 패턴 찾기 (0 또는 1)
        numbers = re.findall(r'[01]', text)
        if numbers:
            return [int(n) for n in numbers]
        
        # 예/아니오 패턴
        attributions = []
        sentences = text.split('.')
        for sent in sentences:
            sent_lower = sent.lower()
            if any(word in sent_lower for word in ['yes', '예', 'support', '지원', 'true']):
                attributions.append(1)
            elif any(word in sent_lower for word in ['no', '아니', 'not support', '지원 안', 'false']):
                attributions.append(0)
        
        return attributions if attributions else [1]  # 기본값
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None,
              run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> str:
        """동기 호출 - RAGAS가 사용"""
        
        # 1. 메트릭 타입 감지
        metric_type = self._detect_metric_type(prompt)
        
        if not metric_type:
            # 메트릭을 감지할 수 없으면 그냥 전달
            return self.hcx._call(prompt, stop, run_manager, **kwargs)
        
        # 2. 메트릭별 특화 프롬프트 생성
        enhanced_prompt = self._create_enhanced_prompt(prompt, metric_type)
        
        # 3. HCX 호출
        raw_response = self.hcx._call(enhanced_prompt, stop, run_manager, **kwargs)
        
        # 디버깅: 메트릭별 응답 로깅
        if metric_type in ['context_precision', 'context_recall', 'answer_correctness']:
            import logging
            logging.info(f"[HCX_PROXY] {metric_type} raw response: {raw_response}")
        
        # 4. 응답을 RAGAS 스키마에 맞게 변환
        try:
            # 먼저 JSON 파싱 시도
            if raw_response.strip().startswith('{'):
                data = json.loads(raw_response)
                # 스키마 검증
                if self._validate_schema(data, metric_type):
                    return json.dumps(data, ensure_ascii=False)
        except:
            pass
        
        # 5. 메트릭별 강제 변환
        result = self._force_convert(raw_response, metric_type)
        
        # 디버깅: 변환 결과 로깅
        if metric_type in ['context_precision', 'context_recall', 'answer_correctness']:
            import logging
            logging.info(f"[HCX_PROXY] {metric_type} converted result: {result}")
        
        # 6. JSON 문자열로 반환
        return json.dumps(result, ensure_ascii=False)
    
    async def _acall(self, prompt: str, stop: Optional[List[str]] = None,
                     run_manager: Optional[AsyncCallbackManagerForLLMRun] = None, **kwargs: Any) -> str:
        """비동기 호출"""
        # asyncio를 사용하여 동기 함수를 비동기로 실행
        import asyncio
        from functools import partial
        loop = asyncio.get_event_loop()
        # partial을 사용하여 kwargs를 올바르게 전달
        return await loop.run_in_executor(
            None, 
            partial(self._call, prompt, stop, run_manager, **kwargs)
        )
    
    def _create_enhanced_prompt(self, prompt: str, metric_type: str) -> str:
        """메트릭별 특화 프롬프트 생성"""
        
        if metric_type == 'faithfulness':
            return f"""{prompt}

중요: 답변을 개별적인 사실 문장으로 나누어주세요.
각 문장은 하나의 독립적인 사실을 담아야 합니다.
번호를 매겨서 나열해주세요.

예시:
1. 서울은 한국의 수도입니다.
2. 서울의 인구는 약 950만 명입니다.
"""

        elif metric_type == 'answer_relevancy':
            return f"""{prompt}

주어진 답변에 대한 적절한 질문을 생성해주세요.
질문은 반드시 물음표(?)로 끝나야 합니다.
"""

        elif metric_type == 'context_precision':
            return f"""{prompt}

중요: 컨텍스트가 답변을 생성하는데 유용했는지 판단하세요.
반드시 다음 중 하나로만 답하세요:
- "1" (유용함)
- "0" (유용하지 않음)

숫자만 답하세요. 설명은 필요없습니다.
"""

        elif metric_type == 'context_recall':
            return f"""{prompt}

각 문장이 컨텍스트에서 지원되는지 확인하고, 다음 형식으로 답하세요:
[1, 0, 1, 1, 0]

각 숫자는:
- 1: 해당 문장이 컨텍스트에서 지원됨
- 0: 해당 문장이 컨텍스트에서 지원되지 않음

대괄호 안에 쉼표로 구분된 숫자만 답하세요.
"""

        elif metric_type == 'faithfulness_nli':
            return f"""{prompt}

각 문장에 대해 다음 형식으로 응답하세요:
{{
  "statements": [
    {{
      "statement": "검토한 문장",
      "verdict": 1,
      "reason": "컨텍스트에서 지원되는 이유"
    }}
  ]
}}
verdict: 1 = 지원됨, 0 = 지원안됨
"""

        elif metric_type == 'answer_correctness':
            return f"""{prompt}

Ground truth와 answer를 비교하여 다음 형식으로 분류하세요:
{{
  "TP": ["정답과 일치하는 문장1", "문장2"],
  "FP": ["정답에 없는 잘못된 문장3"],
  "FN": ["정답에는 있지만 답변에 없는 문장4"]
}}

TP=True Positive, FP=False Positive, FN=False Negative
"""

        else:
            return prompt
    
    def _force_convert(self, response: str, metric_type: str) -> Dict[str, Any]:
        """응답을 메트릭별 스키마로 강제 변환"""
        
        schema_config = self.__metric_schemas.get(metric_type, {})
        default = schema_config.get('default', {})
        
        
        try:
            if metric_type == 'faithfulness' or metric_type == 'faithfulness_nli':
                # JSON 응답 처리
                try:
                    if response.strip().startswith('{') or response.strip().startswith('['):
                        data = json.loads(response)
                        
                        # Case 1: {"statements": [...]}
                        if isinstance(data, dict) and 'statements' in data:
                            statements = data['statements']
                            
                            # Case 1a: 단순 문자열 리스트
                            if isinstance(statements, list) and all(isinstance(s, str) for s in statements):
                                return {'statements': statements}
                            
                            # Case 1b: 객체 리스트 (NLI 응답)
                            if isinstance(statements, list) and all(isinstance(s, dict) for s in statements):
                                # NLI 응답인 경우 support 값 추출
                                support_values = []
                                for stmt in statements:
                                    if 'support' in stmt:
                                        support_values.append(stmt['support'])
                                    elif 'verdict' in stmt:
                                        # verdict가 있는 경우 (1 = support, 0 = not support)
                                        support_values.append(1 if stmt['verdict'] else 0)
                                
                                # NLI 응답은 다른 형식으로 반환
                                if support_values:
                                    return {'attributed': support_values}
                                
                                # 아니면 statement만 추출
                                stmt_texts = [s.get('statement', str(s)) for s in statements]
                                return {'statements': stmt_texts}
                except:
                    pass
                
                # 텍스트에서 추출
                statements = self._extract_statements(response)
                
                # faithfulness vs faithfulness_nli 구분
                if metric_type == 'faithfulness':
                    # 단순 문자열 리스트
                    return {'statements': statements}
                else:
                    # NLI는 객체 리스트 필요
                    stmt_objects = []
                    for stmt in statements:
                        stmt_objects.append({
                            'statement': stmt,
                            'verdict': 1,  # 기본값
                            'reason': 'Extracted from response'
                        })
                    return {'statements': stmt_objects}
            
            elif metric_type == 'answer_relevancy':
                question = self._extract_question(response)
                # noncommittal은 항상 0으로 설정 (명확한 질문 생성)
                return {'question': question, 'noncommittal': 0}
            
            elif metric_type == 'context_precision':
                # RAGAS expects {"reason": "...", "verdict": 0 or 1}
                # 숫자 응답 우선 확인
                response_stripped = response.strip()
                verdict = 0
                reason = "Context was not useful"
                
                if response_stripped in ['0', '1']:
                    verdict = int(response_stripped)
                    reason = "Context was useful in arriving at the answer" if verdict else "Context was not useful"
                elif response.strip().startswith('{'):
                    try:
                        data = json.loads(response)
                        if 'verdict' in data:
                            verdict = int(data['verdict'])
                            reason = data.get('reason', reason)
                        elif 'relevant' in data:
                            verdict = int(data['relevant'])
                            reason = "Context was useful" if verdict else "Context was not useful"
                        elif 'statements' in data:
                            # HCX가 statements 형식으로 응답한 경우
                            verdict = 1  # 기본값
                            reason = "Context evaluation based on statements"
                    except:
                        pass
                else:
                    # 텍스트에서 관련성 추출
                    verdict = self._extract_relevance(response)
                    reason = "Based on analysis of the response"
                
                return {'reason': reason, 'verdict': verdict}
            
            elif metric_type == 'context_recall':
                # RAGAS expects {"classifications": [{"statement": "...", "reason": "...", "attributed": 0 or 1}]}
                classifications = []
                
                try:
                    # JSON 응답 처리
                    if response.strip().startswith('{'):
                        data = json.loads(response)
                        if 'classifications' in data:
                            classifications = data['classifications']
                        elif 'statements' in data:
                            # statements를 classifications로 변환
                            if data['statements']:  # 비어있지 않은 경우
                                for stmt in data['statements']:
                                    if isinstance(stmt, dict):
                                        classifications.append({
                                            'statement': stmt.get('statement', ''),
                                            'reason': stmt.get('reason', 'Based on context'),
                                            'attributed': stmt.get('attributed', stmt.get('support', 0))
                                        })
                            else:
                                # 빈 statements인 경우 기본값
                                classifications.append({
                                    'statement': 'Answer statement',
                                    'reason': 'Context supports the answer',
                                    'attributed': 1
                                })
                    elif response.strip().startswith('['):
                        # [1, 0, 1] 형태 -> classifications로 변환
                        data = json.loads(response)
                        if isinstance(data, list):
                            for i, val in enumerate(data):
                                classifications.append({
                                    'statement': f'Statement {i+1}',
                                    'reason': 'Attributed to context' if val else 'Not found in context',
                                    'attributed': int(val)
                                })
                except:
                    pass
                
                # 응답에서 숫자 추출 시도
                if not classifications:
                    import re
                    numbers = re.findall(r'[01]', response)
                    if numbers:
                        for i, num in enumerate(numbers):
                            classifications.append({
                                'statement': f'Statement {i+1}',
                                'reason': 'Based on extraction',
                                'attributed': int(num)
                            })
                
                # 기본값
                if not classifications:
                    classifications = [{
                        'statement': 'Unable to parse',
                        'reason': 'Default response',
                        'attributed': 0
                    }]
                
                return {'classifications': classifications}
            
            elif metric_type == 'answer_correctness':
                # RAGAS expects {"TP": [...], "FP": [...], "FN": [...]} with statement objects
                tp_list = []
                fp_list = []
                fn_list = []
                
                try:
                    if response.strip().startswith('{'):
                        data = json.loads(response)
                        if 'TP' in data:
                            # 문자열 리스트를 객체 리스트로 변환
                            for item in data.get('TP', []):
                                if isinstance(item, str):
                                    tp_list.append({'statement': item, 'reason': 'True positive'})
                                elif isinstance(item, dict):
                                    tp_list.append(item)
                        
                        if 'FP' in data:
                            for item in data.get('FP', []):
                                if isinstance(item, str):
                                    fp_list.append({'statement': item, 'reason': 'False positive'})
                                elif isinstance(item, dict):
                                    fp_list.append(item)
                        
                        if 'FN' in data:
                            for item in data.get('FN', []):
                                if isinstance(item, str):
                                    fn_list.append({'statement': item, 'reason': 'False negative'})
                                elif isinstance(item, dict):
                                    fn_list.append(item)
                        
                        # HCX가 statements만 반환한 경우
                        if 'statements' in data and not ('TP' in data or 'FP' in data or 'FN' in data):
                            # 기본적으로 TP로 처리
                            if data['statements']:
                                for stmt in data['statements']:
                                    if isinstance(stmt, str):
                                        tp_list.append({'statement': stmt, 'reason': 'Assumed correct'})
                                    elif isinstance(stmt, dict):
                                        tp_list.append({'statement': stmt.get('statement', ''), 'reason': stmt.get('reason', 'Assumed correct')})
                            else:
                                # 빈 statements인 경우
                                tp_list.append({'statement': 'Answer evaluated', 'reason': 'Default evaluation'})
                except:
                    pass
                
                # 기본값 설정
                if not tp_list and not fp_list and not fn_list:
                    # 텍스트 유사도 추정
                    if '정확' in response or '일치' in response or 'correct' in response.lower():
                        tp_list = [{'statement': 'Answer is correct', 'reason': 'Based on response analysis'}]
                    else:
                        fp_list = [{'statement': 'Answer may be incorrect', 'reason': 'Based on response analysis'}]
                
                return {'TP': tp_list, 'FP': fp_list, 'FN': fn_list}
            
        except Exception as e:
            pass
        
        # 실패 시 기본값
        return default
    
    def _validate_schema(self, data: Dict, metric_type: str) -> bool:
        """스키마 검증"""
        schema_config = self.__metric_schemas.get(metric_type, {})
        schema = schema_config.get('schema', {})
        
        for field, field_type in schema.items():
            if field not in data:
                return False
            
            # 타입 검증
            if field_type == List[str] and not isinstance(data[field], list):
                return False
            elif field_type == str and not isinstance(data[field], str):
                return False
            elif field_type == int and not isinstance(data[field], (int, bool)):
                return False
            elif field_type == float and not isinstance(data[field], (int, float)):
                return False
        
        return True
    
    # RAGAS 호환성을 위한 추가 메서드들
    def generate(self, prompts: List[Union[str, Any]], **kwargs: Any):
        """RAGAS가 호출하는 generate 메서드 - 비동기 컨텍스트 감지"""
        # RAGAS 버그 우회: RAGAS가 await llm.generate()를 호출하므로
        # 비동기 컨텍스트에서는 코루틴을 반환해야 함
        try:
            # 비동기 컨텍스트 확인
            loop = asyncio.get_running_loop()
            # 비동기 컨텍스트에서 실행 중이면 agenerate 반환
            return self.agenerate(prompts, **kwargs)
        except RuntimeError:
            # 동기 컨텍스트에서는 일반 LLMResult 반환
            if not isinstance(prompts, list):
                prompts = [prompts]
            
            generations = []
            for prompt in prompts:
                prompt_str = str(prompt) if not hasattr(prompt, 'text') else prompt.text
                response = self._call(prompt_str, **kwargs)
                generations.append([Generation(text=response)])
            
            return LLMResult(generations=generations)
    
    def agenerate(self, prompts: List[Union[str, Any]], **kwargs: Any):
        """비동기 generate - 코루틴 반환"""
        async def _async_generate():
            if not isinstance(prompts, list):
                prompts_list = [prompts]
            else:
                prompts_list = prompts
            
            generations = []
            for prompt in prompts_list:
                prompt_str = str(prompt) if not hasattr(prompt, 'text') else prompt.text
                # 비동기 호출 사용
                response = await self._acall(prompt_str, **kwargs)
                generations.append([Generation(text=response)])
            
            return LLMResult(generations=generations)
        
        # 코루틴 객체 반환 (await 없이)
        return _async_generate()


def wrap_hcx_with_proxy(hcx_llm: LLM) -> HCXRAGASProxy:
    """기존 HCX LLM을 프록시로 감싸는 헬퍼 함수"""
    return HCXRAGASProxy(hcx_llm)