#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BGE-M3 모델 다운로드 스크립트 (Windows용)
RAGTrace Lite 오프라인 배포를 위한 BGE-M3 임베딩 모델 다운로드

사용법: python download_bge_m3_windows.py
"""

import os
import sys
import time
from pathlib import Path

def print_banner():
    """배너 출력"""
    print("=" * 70)
    print("BGE-M3 임베딩 모델 다운로드")
    print("=" * 70)
    print()

def check_internet():
    """인터넷 연결 확인"""
    import urllib.request
    try:
        urllib.request.urlopen('https://huggingface.co', timeout=5)
        return True
    except:
        return False

def install_dependencies():
    """필요한 패키지 설치"""
    print("필요한 패키지 확인 중...")
    try:
        import huggingface_hub
        print("✓ huggingface_hub 패키지가 이미 설치되어 있습니다.")
    except ImportError:
        print("huggingface_hub 패키지 설치 중...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface-hub"])
        print("✓ huggingface_hub 패키지 설치 완료")

def download_bge_m3(target_dir="./models/bge-m3"):
    """BGE-M3 모델 다운로드"""
    from huggingface_hub import snapshot_download
    
    # 대상 디렉토리 생성
    model_path = Path(target_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n다운로드 위치: {model_path.absolute()}")
    print("\n다운로드 시작... (약 2.3GB, 시간이 걸릴 수 있습니다)")
    print("-" * 50)
    
    try:
        # 모델 다운로드
        snapshot_download(
            repo_id='BAAI/bge-m3',
            local_dir=str(model_path),
            local_dir_use_symlinks=False,
            resume_download=True,
            ignore_patterns=['*.h5', '*.ot', '*.msgpack', '*.safetensors.index.json']
        )
        
        print("\n✓ BGE-M3 모델 다운로드 완료!")
        
        # 다운로드된 파일 확인
        files = list(model_path.rglob("*"))
        file_count = len([f for f in files if f.is_file()])
        total_size = sum(f.stat().st_size for f in files if f.is_file()) / (1024**3)
        
        print(f"\n다운로드 정보:")
        print(f"  - 파일 개수: {file_count}개")
        print(f"  - 총 크기: {total_size:.2f}GB")
        
        # 주요 파일 확인
        important_files = ['config.json', 'pytorch_model.bin', 'tokenizer.json']
        print("\n주요 파일 확인:")
        for file in important_files:
            if (model_path / file).exists():
                print(f"  ✓ {file}")
            else:
                print(f"  ✗ {file} (누락)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 다운로드 실패: {str(e)}")
        return False

def create_env_file():
    """환경 설정 파일 생성"""
    env_content = """# RAGTrace Lite 환경 설정
# BGE-M3 모델 경로
BGE_M3_MODEL_PATH=./models/bge-m3

# 기본 임베딩 제공자
DEFAULT_EMBEDDING=bge_m3

# HCX API 키 (실제 키로 교체 필요)
CLOVA_STUDIO_API_KEY=your-hcx-api-key-here
"""
    
    env_path = Path(".env.example")
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"\n✓ 환경 설정 예제 파일 생성: {env_path}")

def main():
    """메인 함수"""
    print_banner()
    
    # 인터넷 연결 확인
    if not check_internet():
        print("❌ 인터넷 연결을 확인할 수 없습니다.")
        print("   인터넷 연결이 필요합니다.")
        sys.exit(1)
    
    print("✓ 인터넷 연결 확인됨")
    
    # 의존성 설치
    install_dependencies()
    
    # BGE-M3 다운로드
    start_time = time.time()
    success = download_bge_m3()
    elapsed_time = time.time() - start_time
    
    if success:
        print(f"\n총 소요 시간: {elapsed_time/60:.1f}분")
        
        # 환경 설정 파일 생성
        create_env_file()
        
        print("\n" + "=" * 70)
        print("✅ BGE-M3 모델 다운로드가 완료되었습니다!")
        print("=" * 70)
        print("\n다음 단계:")
        print("1. models/bge-m3 폴더를 오프라인 패키지에 포함시키세요.")
        print("2. .env.example 파일을 참고하여 .env 파일을 생성하세요.")
        print("3. 폐쇄망에서는 BGE_M3_MODEL_PATH 환경변수를 설정하세요.")
    else:
        print("\n" + "=" * 70)
        print("❌ BGE-M3 모델 다운로드에 실패했습니다.")
        print("=" * 70)
        print("\n문제 해결:")
        print("1. 인터넷 연결을 확인하세요.")
        print("2. 디스크 공간이 충분한지 확인하세요 (최소 3GB).")
        print("3. 다시 실행하면 이어받기가 됩니다.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        print("   다시 실행하면 이어받기가 됩니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 예기치 않은 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)