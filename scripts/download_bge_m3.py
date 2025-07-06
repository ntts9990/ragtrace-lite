#!/usr/bin/env python3
"""
BGE-M3 모델 사전 다운로드 스크립트
폐쇄망 배포를 위해 BGE-M3 모델을 미리 다운로드합니다.
"""

import os
import sys
from pathlib import Path

def download_bge_m3_model():
    """BGE-M3 모델을 다운로드합니다."""
    try:
        from huggingface_hub import snapshot_download
        
        # 모델 저장 경로
        model_path = Path("models/bge-m3")
        model_path.mkdir(parents=True, exist_ok=True)
        
        print("🚀 BGE-M3 모델 다운로드 시작...")
        print(f"📁 저장 위치: {model_path.absolute()}")
        print("⚠️  이 작업은 약 2.3GB의 데이터를 다운로드하며, 시간이 걸릴 수 있습니다.")
        
        # BGE-M3 모델 다운로드
        snapshot_download(
            repo_id="BAAI/bge-m3",
            local_dir=str(model_path),
            local_dir_use_symlinks=False,  # 심볼릭 링크 대신 실제 파일
            resume_download=True  # 중단된 다운로드 재개
        )
        
        print("✅ BGE-M3 모델 다운로드 완료!")
        print(f"📊 모델 크기: {get_folder_size(model_path):.1f} MB")
        
        # 모델 파일 목록 확인
        print("\n📋 다운로드된 파일:")
        for file_path in sorted(model_path.rglob("*")):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  - {file_path.name}: {size_mb:.1f} MB")
        
        # 모델 로딩 테스트
        print("\n🧪 모델 로딩 테스트...")
        test_model_loading(model_path)
        
        return True
        
    except ImportError as e:
        print(f"❌ huggingface_hub가 설치되지 않았습니다: {e}")
        print("💡 해결방법: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"❌ BGE-M3 모델 다운로드 실패: {e}")
        return False

def get_folder_size(folder_path: Path) -> float:
    """폴더 크기를 MB 단위로 반환합니다."""
    total_size = 0
    for file_path in folder_path.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    return total_size / (1024 * 1024)

def test_model_loading(model_path: Path) -> bool:
    """모델 로딩을 테스트합니다."""
    try:
        from sentence_transformers import SentenceTransformer
        
        # 모델 로딩 테스트
        model = SentenceTransformer(str(model_path))
        
        # 간단한 임베딩 테스트
        test_text = "This is a test sentence."
        embedding = model.encode(test_text)
        
        print(f"✅ 모델 로딩 테스트 성공!")
        print(f"   - 임베딩 차원: {len(embedding)}")
        print(f"   - 모델 디바이스: {model.device}")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  sentence-transformers가 설치되지 않아 모델 테스트를 건너뜁니다: {e}")
        return True  # 다운로드는 성공했으므로 True 반환
    except Exception as e:
        print(f"❌ 모델 로딩 테스트 실패: {e}")
        return False

def create_model_info_file(model_path: Path):
    """모델 정보 파일을 생성합니다."""
    info_content = f"""# BGE-M3 Model Information

## Model Details
- **Model ID**: BAAI/bge-m3
- **Download Date**: {os.popen('date').read().strip()}
- **Model Size**: {get_folder_size(model_path):.1f} MB
- **Local Path**: {model_path.absolute()}

## Usage
```python
from sentence_transformers import SentenceTransformer

# 모델 로딩
model = SentenceTransformer('{model_path}')

# 임베딩 생성
embeddings = model.encode(['문장1', '문장2'])
```

## Requirements
- sentence-transformers >= 2.2.0
- torch >= 1.11.0
- transformers >= 4.21.0

## License
MIT License - https://huggingface.co/BAAI/bge-m3
"""
    
    info_file = model_path / "MODEL_INFO.md"
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(info_content)
    
    print(f"📝 모델 정보 파일 생성: {info_file}")

def main():
    """메인 함수"""
    print("🔒 RAGTrace Lite 폐쇄망 배포 - BGE-M3 모델 다운로드")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"📁 현재 디렉토리: {current_dir}")
    
    # BGE-M3 모델 다운로드
    if download_bge_m3_model():
        model_path = Path("models/bge-m3")
        create_model_info_file(model_path)
        print("\n🎉 BGE-M3 모델 다운로드 및 설정 완료!")
        print("   폐쇄망 배포 시 models/ 폴더를 함께 복사하세요.")
    else:
        print("\n❌ BGE-M3 모델 다운로드 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()