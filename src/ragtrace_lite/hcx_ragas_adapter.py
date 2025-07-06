"""
HCX와 RAGAS 호환성을 위한 어댑터
"""
import json
import re
from typing import Dict, Any, List, Optional


class HCXRAGASAdapter:
    """HCX 응답을 RAGAS 형식으로 변환하는 어댑터"""
    
    # RAGAS 메트릭별 예상 응답 형식
    METRIC_SCHEMAS = {
        "faithfulness": {
            "prompt_keywords": ["statements", "문장", "extract", "추출"],
            "response_format": {"statements": List[str]},
            "field_mapping": {"text": "statements", "sentences": "statements", "문장들": "statements"}
        },
        "answer_relevancy": {
            "prompt_keywords": ["question", "질문", "generate"],
            "response_format": {"question": str, "noncommittal": int},
            "field_mapping": {"text": "question", "generated_question": "question", "질문": "question"}
        },
        "context_precision": {
            "prompt_keywords": ["relevant", "관련", "score", "점수"],
            "response_format": {"relevant": int},
            "field_mapping": {"text": "relevant", "is_relevant": "relevant", "관련성": "relevant"}
        },
        "context_recall": {
            "prompt_keywords": ["attributed", "귀속", "support"],
            "response_format": {"attributed": List[int]},
            "field_mapping": {"text": "attributed", "supported": "attributed"}
        }
    }
    
    @staticmethod
    def detect_metric_type(prompt: str) -> Optional[str]:
        """프롬프트에서 RAGAS 메트릭 타입 감지"""
        prompt_lower = prompt.lower()
        
        for metric, config in HCXRAGASAdapter.METRIC_SCHEMAS.items():
            keywords = config["prompt_keywords"]
            if any(keyword in prompt_lower for keyword in keywords):
                return metric
        
        return None
    
    @staticmethod
    def enhance_prompt_for_hcx(prompt: str, metric_type: Optional[str] = None) -> str:
        """HCX가 올바른 JSON을 생성하도록 프롬프트 강화"""
        
        # 메트릭 타입 자동 감지
        if not metric_type:
            metric_type = HCXRAGASAdapter.detect_metric_type(prompt)
        
        if not metric_type:
            return prompt
        
        # 메트릭별 JSON 예시 추가
        enhancements = {
            "faithfulness": """

다음 JSON 형식으로만 응답하세요. 절대 다른 설명이나 텍스트를 추가하지 마세요.
오직 JSON만 출력하세요:

{
  "statements": ["문장1", "문장2", "문장3"]
}

위 형식의 JSON만:""",
            
            "answer_relevancy": """

반드시 다음 JSON 형식으로만 응답하세요:
{
  "question": "생성된 질문",
  "noncommittal": 0
}
(noncommittal: 0=명확함, 1=모호함)

JSON만 출력:""",
            
            "context_precision": """

반드시 다음 JSON 형식으로만 응답하세요:
{
  "relevant": 1
}
(relevant: 1=관련있음, 0=관련없음)

JSON만 출력:""",
            
            "context_recall": """

반드시 다음 JSON 형식으로만 응답하세요:
{
  "attributed": [1, 0, 1]
}
(각 문장이 컨텍스트에서 지원되는지: 1=지원됨, 0=지원안됨)

JSON만 출력:"""
        }
        
        enhancement = enhancements.get(metric_type, "")
        return prompt + enhancement
    
    @staticmethod
    def parse_hcx_response(response: str, metric_type: Optional[str] = None) -> Dict[str, Any]:
        """HCX 응답을 RAGAS 형식으로 변환"""
        
        # 1. 먼저 순수 JSON 파싱 시도
        response = response.strip()
        
        # JSON 블록 추출 (```json ... ``` 형식 처리)
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        
        # 중괄호로 시작하는 JSON 찾기
        json_start = response.find('{')
        json_end = response.rfind('}')
        if json_start != -1 and json_end != -1:
            try:
                json_str = response[json_start:json_end+1]
                data = json.loads(json_str)
                
                # 이미 올바른 형식인 경우
                if metric_type and HCXRAGASAdapter._validate_response_format(data, metric_type):
                    return data
                
                # 필드 매핑 적용
                if metric_type:
                    return HCXRAGASAdapter._map_fields(data, metric_type)
                    
                return data
                
            except json.JSONDecodeError:
                pass
        
        # 2. JSON 파싱 실패 시 텍스트 응답 처리
        return HCXRAGASAdapter._parse_text_response(response, metric_type)
    
    @staticmethod
    def _validate_response_format(data: Dict, metric_type: str) -> bool:
        """응답이 올바른 RAGAS 형식인지 검증"""
        expected_format = HCXRAGASAdapter.METRIC_SCHEMAS.get(metric_type, {}).get("response_format", {})
        
        for field, field_type in expected_format.items():
            if field not in data:
                return False
            
            # 타입 검증
            if field_type == List[str] and not isinstance(data[field], list):
                return False
            elif field_type == str and not isinstance(data[field], str):
                return False
            elif field_type == int and not isinstance(data[field], (int, bool)):
                return False
                
        return True
    
    @staticmethod
    def _map_fields(data: Dict, metric_type: str) -> Dict[str, Any]:
        """HCX 응답 필드를 RAGAS 필드로 매핑"""
        field_mapping = HCXRAGASAdapter.METRIC_SCHEMAS.get(metric_type, {}).get("field_mapping", {})
        expected_format = HCXRAGASAdapter.METRIC_SCHEMAS.get(metric_type, {}).get("response_format", {})
        
        result = {}
        
        # 필드 매핑 적용
        for hcx_field, ragas_field in field_mapping.items():
            if hcx_field in data:
                value = data[hcx_field]
                
                # 타입 변환
                expected_type = expected_format.get(ragas_field)
                if expected_type == List[str]:
                    if isinstance(value, str):
                        # 문자열을 리스트로 변환
                        value = [s.strip() for s in value.split('.') if s.strip()]
                    elif not isinstance(value, list):
                        value = [str(value)]
                elif expected_type == int:
                    # 불린을 정수로 변환
                    if isinstance(value, bool):
                        value = 1 if value else 0
                    elif isinstance(value, str):
                        # "yes"/"no" 등을 정수로
                        value = 1 if value.lower() in ['yes', '예', 'true', '1'] else 0
                
                result[ragas_field] = value
        
        # 필수 필드가 없으면 기본값 추가
        for field, field_type in expected_format.items():
            if field not in result:
                if field_type == List[str]:
                    result[field] = []
                elif field_type == str:
                    result[field] = ""
                elif field_type == int:
                    result[field] = 0
                    
        return result
    
    @staticmethod
    def _parse_text_response(response: str, metric_type: Optional[str]) -> Dict[str, Any]:
        """텍스트 응답을 RAGAS 형식으로 변환"""
        
        if not metric_type:
            # 기본 처리
            return {"text": response}
        
        # 메트릭별 텍스트 파싱
        if metric_type == "faithfulness":
            # 번호가 있는 리스트 형식 처리 (1. xxx 2. xxx)
            numbered_pattern = r'\d+\.\s*([^.]+(?:\.[^.]+)*?)(?=\d+\.|$)'
            numbered_matches = re.findall(numbered_pattern, response, re.DOTALL)
            
            if numbered_matches:
                statements = [match.strip() for match in numbered_matches if match.strip()]
                return {"statements": statements}
            
            # 일반 문장 분리 (마침표, 줄바꿈 기준)
            sentences = re.split(r'[.。\n]+', response)
            statements = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
            return {"statements": statements}
            
        elif metric_type == "answer_relevancy":
            # 질문 추출 시도
            question_match = re.search(r'["""]([^"""]+\?)["""]', response)
            if question_match:
                return {"question": question_match.group(1), "noncommittal": 0}
            
            # 물음표로 끝나는 문장 찾기
            sentences = response.split('.')
            for sent in sentences:
                if '?' in sent:
                    return {"question": sent.strip(), "noncommittal": 0}
                    
            return {"question": response.strip(), "noncommittal": 0}
            
        elif metric_type == "context_precision":
            # 긍정/부정 판단
            positive_words = ['relevant', '관련', 'yes', '예', '맞', 'true']
            is_relevant = any(word in response.lower() for word in positive_words)
            return {"relevant": 1 if is_relevant else 0}
            
        elif metric_type == "context_recall":
            # 숫자 추출
            numbers = re.findall(r'\d+', response)
            if numbers:
                return {"attributed": [int(n) for n in numbers]}
            
            # 기본값
            return {"attributed": [1]}
        
        return {"text": response}


# HcxAdapter 클래스 수정을 위한 패치
def patch_hcx_adapter():
    """기존 HcxAdapter에 RAGAS 호환성 개선 적용"""
    from ragtrace_lite.llm_factory import HcxAdapter
    
    # 원래 메서드 저장
    original_agenerate = HcxAdapter.agenerate_answer
    original_clean = HcxAdapter._clean_response_for_ragas
    
    async def enhanced_agenerate_answer(self, prompt: str, max_retries: int = 3, **kwargs):
        """향상된 비동기 응답 생성"""
        # 메트릭 타입 감지
        metric_type = HCXRAGASAdapter.detect_metric_type(prompt)
        
        # 프롬프트 강화
        enhanced_prompt = HCXRAGASAdapter.enhance_prompt_for_hcx(prompt, metric_type)
        
        # 원래 메서드 호출
        response = await original_agenerate(self, enhanced_prompt, max_retries, **kwargs)
        
        # 메트릭 타입 정보를 응답에 추가 (임시 저장)
        if hasattr(self, '_last_metric_type'):
            self._last_metric_type = metric_type
            
        return response
    
    def enhanced_clean_response(self, content: str) -> str:
        """향상된 응답 정리"""
        # 저장된 메트릭 타입 가져오기
        metric_type = getattr(self, '_last_metric_type', None)
        
        # RAGAS 어댑터로 파싱
        parsed = HCXRAGASAdapter.parse_hcx_response(content, metric_type)
        
        # JSON 문자열로 반환
        return json.dumps(parsed, ensure_ascii=False)
    
    # 메서드 교체
    HcxAdapter.agenerate_answer = enhanced_agenerate_answer
    HcxAdapter._clean_response_for_ragas = enhanced_clean_response
    
    return HcxAdapter


if __name__ == "__main__":
    # 테스트
    test_cases = [
        ("faithfulness", '{"text": "라면은 물을 끓여서 만듭니다"}'),
        ("faithfulness", "라면은 물을 끓입니다. 면을 넣습니다. 3분 기다립니다."),
        ("answer_relevancy", '{"text": "라면을 어떻게 만드나요?"}'),
        ("answer_relevancy", '"라면 조리법이 무엇인가요?"라는 질문이 적절합니다.'),
        ("context_precision", '{"relevant": true}'),
        ("context_precision", "네, 이 문맥은 관련이 있습니다."),
    ]
    
    for metric, response in test_cases:
        print(f"\n=== {metric} ===")
        print(f"입력: {response}")
        result = HCXRAGASAdapter.parse_hcx_response(response, metric)
        print(f"출력: {json.dumps(result, ensure_ascii=False)}")