#!/usr/bin/env python
"""Create test Excel data for RAG evaluation with HCX-005 and BGE-M3"""

import pandas as pd
from datetime import datetime
import json

def create_test_data():
    """Create comprehensive test data for RAG evaluation"""
    
    # RAG 평가를 위한 실제적인 QA 데이터
    test_data = [
        {
            "question": "Python에서 리스트와 튜플의 차이점은 무엇인가요?",
            "answer": "리스트는 가변(mutable) 자료형으로 요소를 추가, 삭제, 수정할 수 있습니다. 반면 튜플은 불변(immutable) 자료형으로 한 번 생성되면 요소를 변경할 수 없습니다. 리스트는 대괄호 []를 사용하고, 튜플은 소괄호 ()를 사용합니다.",
            "contexts": [
                "Python에는 여러 종류의 자료형이 있습니다. 리스트(list)는 순서가 있는 가변 자료형으로 요소의 추가, 삭제, 수정이 가능합니다.",
                "튜플(tuple)은 순서가 있는 불변 자료형입니다. 한 번 생성되면 요소를 변경할 수 없어 데이터의 무결성을 보장합니다.",
                "리스트는 [1, 2, 3]과 같이 대괄호로 표현하고, 튜플은 (1, 2, 3)과 같이 소괄호로 표현합니다."
            ],
            "ground_truth": "리스트는 가변 자료형이고 튜플은 불변 자료형입니다. 리스트는 []로, 튜플은 ()로 표현합니다.",
            "env_model_version": "v2.1",
            "env_temperature": "0.1",
            "env_context_window": "large"
        },
        {
            "question": "딥러닝에서 과적합(overfitting)을 방지하는 방법은?",
            "answer": "과적합을 방지하는 주요 방법으로는 1) 드롭아웃(Dropout) 적용, 2) 조기 종료(Early Stopping), 3) 정규화(Regularization) 기법 사용, 4) 더 많은 훈련 데이터 확보, 5) 데이터 증강(Data Augmentation) 등이 있습니다.",
            "contexts": [
                "과적합은 모델이 훈련 데이터에만 특화되어 새로운 데이터에 대한 성능이 떨어지는 현상입니다.",
                "드롭아웃은 훈련 과정에서 임의의 뉴런을 비활성화하여 모델의 복잡도를 줄이는 기법입니다.",
                "조기 종료는 검증 손실이 더 이상 개선되지 않을 때 훈련을 중단하는 방법입니다.",
                "L1, L2 정규화는 가중치에 페널티를 부여하여 모델의 복잡도를 제어합니다."
            ],
            "ground_truth": "드롭아웃, 조기 종료, 정규화, 데이터 증강 등의 방법으로 과적합을 방지할 수 있습니다.",
            "env_model_version": "v2.1",
            "env_temperature": "0.1",
            "env_context_window": "large"
        },
        {
            "question": "REST API의 HTTP 메서드별 용도는?",
            "answer": "GET은 데이터 조회, POST는 새 리소스 생성, PUT은 리소스 전체 수정, PATCH는 리소스 일부 수정, DELETE는 리소스 삭제에 사용됩니다. 각 메서드는 멱등성과 안전성 특성이 다릅니다.",
            "contexts": [
                "REST API는 HTTP 프로토콜의 메서드를 활용하여 리소스에 대한 CRUD 작업을 수행합니다.",
                "GET 메서드는 안전하고 멱등한 특성을 가지며 서버 상태를 변경하지 않습니다.",
                "POST는 새로운 리소스를 생성할 때 사용하며 멱등하지 않습니다.",
                "PUT은 리소스 전체를 교체하며 멱등한 특성을 가집니다."
            ],
            "ground_truth": "GET(조회), POST(생성), PUT(전체수정), PATCH(부분수정), DELETE(삭제)로 각각 다른 용도를 가집니다.",
            "env_model_version": "v2.0",
            "env_temperature": "0.2",
            "env_context_window": "medium"
        },
        {
            "question": "Docker 컨테이너와 가상머신의 차이는?",
            "answer": "Docker 컨테이너는 OS 커널을 공유하여 더 가볍고 빠른 실행이 가능합니다. 가상머신은 하드웨어를 가상화하여 완전히 격리된 환경을 제공하지만 더 많은 리소스를 사용합니다.",
            "contexts": [
                "컨테이너는 운영체제 수준의 가상화 기술입니다.",
                "Docker 컨테이너는 호스트 OS의 커널을 공유하므로 오버헤드가 적습니다.",
                "가상머신은 하이퍼바이저를 통해 하드웨어를 가상화합니다."
            ],
            "ground_truth": "컨테이너는 OS 커널을 공유하여 가볍고, 가상머신은 하드웨어를 가상화하여 완전히 격리됩니다.",
            "env_model_version": "v2.0",
            "env_temperature": "0.2",
            "env_context_window": "medium"
        },
        {
            "question": "JWT 토큰의 구조와 장점은?",
            "answer": "JWT는 Header, Payload, Signature 세 부분으로 구성됩니다. 장점으로는 stateless 특성, 확장성, 다양한 플랫폼 호환성, 자체 포함된 정보 등이 있습니다.",
            "contexts": [
                "JWT(JSON Web Token)는 웹 표준으로 두 당사자 간에 정보를 안전하게 전송하기 위한 토큰입니다.",
                "JWT는 점(.)으로 구분된 세 부분: Header, Payload, Signature로 구성됩니다.",
                "Header에는 토큰 타입과 해싱 알고리즘 정보가 포함됩니다."
            ],
            "ground_truth": "JWT는 Header.Payload.Signature 구조로 되어있으며 stateless하고 확장성이 좋습니다.",
            "env_model_version": "v1.5",
            "env_temperature": "0.3",
            "env_context_window": "small"
        }
    ]
    
    # DataFrame 생성
    df_data = []
    for item in test_data:
        df_data.append({
            'question': item['question'],
            'answer': item['answer'],
            'contexts': json.dumps(item['contexts'], ensure_ascii=False),
            'ground_truth': item['ground_truth'],
            'env_model_version': item['env_model_version'],
            'env_temperature': item['env_temperature'],
            'env_context_window': item['env_context_window']
        })
    
    df = pd.DataFrame(df_data)
    
    # Excel 파일로 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'test_rag_data_{timestamp}.xlsx'
    
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"✅ Test data created: {filename}")
    print(f"📊 Dataset info:")
    print(f"   - Items: {len(df)}")
    print(f"   - Columns: {list(df.columns)}")
    print(f"   - Environment conditions: {df[['env_model_version', 'env_temperature', 'env_context_window']].drop_duplicates().shape[0]} unique combinations")
    
    return filename

if __name__ == "__main__":
    create_test_data()