#!/usr/bin/env python3
"""
폐쇄망 배포 완전 준비 스크립트
Python 설치 파일, BGE-M3 모델, 의존성 패키지를 모두 다운로드하고 배포 패키지를 생성합니다.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_script(script_path: str, description: str) -> bool:
    """스크립트를 실행하고 결과를 반환합니다."""
    print(f"\n🚀 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, script_path], check=True, capture_output=False)
        print(f"✅ {description} 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ {description} 중 오류 발생: {e}")
        return False

def check_internet_connection() -> bool:
    """인터넷 연결을 확인합니다."""
    print("🌐 인터넷 연결 확인 중...")
    
    try:
        import requests
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code == 200:
            print("✅ 인터넷 연결 확인됨")
            return True
        else:
            print(f"❌ 인터넷 연결 문제: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 인터넷 연결 실패: {e}")
        return False

def check_disk_space() -> bool:
    """디스크 공간을 확인합니다."""
    print("💾 디스크 공간 확인 중...")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free / (1024**3)
        
        print(f"📊 사용 가능한 공간: {free_gb:.1f} GB")
        
        # 최소 5GB 필요 (Python 설치파일 30MB + BGE-M3 2.3GB + wheels 1GB + 여유공간 2GB)
        if free_gb < 5.0:
            print("❌ 디스크 공간 부족! 최소 5GB 필요")
            return False
        else:
            print("✅ 충분한 디스크 공간 확인됨")
            return True
            
    except Exception as e:
        print(f"⚠️  디스크 공간 확인 실패: {e}")
        print("계속 진행합니다...")
        return True

def main():
    """메인 함수"""
    print("🔒 RAGTrace Lite 폐쇄망 배포 완전 준비")
    print("=" * 60)
    print("이 스크립트는 다음 작업을 수행합니다:")
    print("1. 인터넷 연결 및 디스크 공간 확인")
    print("2. Python 3.11 Windows 설치 파일 다운로드")
    print("3. BGE-M3 모델 다운로드")
    print("4. 모든 의존성 패키지 수집")
    print("5. 폐쇄망 배포 패키지 생성")
    print("=" * 60)
    
    # 사용자 확인
    user_input = input("계속 진행하시겠습니까? (Y/n): ")
    if user_input.lower() in ['n', 'no']:
        print("작업이 취소되었습니다.")
        sys.exit(0)
    
    start_time = time.time()
    
    # 1. 사전 확인
    print("\n📋 [1/5] 사전 확인")
    
    if not check_internet_connection():
        print("❌ 인터넷 연결이 필요합니다!")
        sys.exit(1)
    
    if not check_disk_space():
        print("❌ 디스크 공간이 부족합니다!")
        sys.exit(1)
    
    # 2. Python 설치 파일 다운로드
    print("\n📥 [2/5] Python 설치 파일 다운로드")
    
    python_script = Path("scripts/download_python_installer.py")
    if not python_script.exists():
        print(f"❌ 스크립트를 찾을 수 없습니다: {python_script}")
        sys.exit(1)
    
    if not run_script(str(python_script), "Python 설치 파일 다운로드"):
        print("❌ Python 설치 파일 다운로드 실패!")
        user_input = input("계속 진행하시겠습니까? (y/N): ")
        if user_input.lower() != 'y':
            sys.exit(1)
    
    # 3. BGE-M3 모델 다운로드
    print("\n🤖 [3/5] BGE-M3 모델 다운로드")
    
    bge_script = Path("scripts/download_bge_m3.py")
    if not bge_script.exists():
        print(f"❌ 스크립트를 찾을 수 없습니다: {bge_script}")
        sys.exit(1)
    
    if not run_script(str(bge_script), "BGE-M3 모델 다운로드"):
        print("❌ BGE-M3 모델 다운로드 실패!")
        user_input = input("계속 진행하시겠습니까? (y/N): ")
        if user_input.lower() != 'y':
            sys.exit(1)
    
    # 4. 의존성 패키지 수집
    print("\n📦 [4/5] 의존성 패키지 수집")
    
    try:
        # requirements-offline.txt가 있는지 확인
        req_file = Path("requirements-offline.txt")
        if not req_file.exists():
            print("⚠️  requirements-offline.txt가 없습니다. 현재 환경에서 생성합니다...")
            # 현재 환경의 패키지 목록 생성
            subprocess.run([sys.executable, "-m", "pip", "freeze"], 
                         stdout=open("requirements-full.txt", "w"), check=True)
        
        print("✅ 의존성 패키지 목록 준비 완료")
        
    except Exception as e:
        print(f"⚠️  의존성 패키지 목록 생성 실패: {e}")
        print("패키지 생성 단계에서 처리됩니다...")
    
    # 5. 배포 패키지 생성
    print("\n📦 [5/5] 폐쇄망 배포 패키지 생성")
    
    package_script = Path("scripts/create_offline_package.py")
    if not package_script.exists():
        print(f"❌ 스크립트를 찾을 수 없습니다: {package_script}")
        sys.exit(1)
    
    if not run_script(str(package_script), "배포 패키지 생성"):
        print("❌ 배포 패키지 생성 실패!")
        sys.exit(1)
    
    # 완료 메시지
    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_minutes = elapsed_time / 60
    
    print("\n" + "=" * 60)
    print("🎉 폐쇄망 배포 준비 완료!")
    print("=" * 60)
    print(f"⏱️  총 소요 시간: {elapsed_minutes:.1f}분")
    print()
    
    # 생성된 파일들 확인
    print("📋 생성된 파일들:")
    
    # Python 설치 파일
    python_installer = Path("python-installer")
    if python_installer.exists():
        installer_files = list(python_installer.glob("*.exe"))
        if installer_files:
            file_size = installer_files[0].stat().st_size / (1024*1024)
            print(f"✅ Python 설치 파일: {installer_files[0].name} ({file_size:.1f} MB)")
    
    # BGE-M3 모델
    bge_model = Path("models/bge-m3")
    if bge_model.exists():
        model_size = sum(f.stat().st_size for f in bge_model.rglob('*') if f.is_file()) / (1024*1024)
        print(f"✅ BGE-M3 모델: models/bge-m3/ ({model_size:.1f} MB)")
    
    # 배포 패키지
    dist_dir = Path("dist")
    if dist_dir.exists():
        package_files = list(dist_dir.glob("ragtrace-lite-offline-*.zip"))
        if package_files:
            package_size = package_files[0].stat().st_size / (1024*1024)
            print(f"✅ 배포 패키지: {package_files[0].name} ({package_size:.1f} MB)")
    
    print()
    print("🎯 다음 단계:")
    print("1. dist/ 폴더의 ZIP 파일을 폐쇄망 윈도우 PC로 복사")
    print("2. ZIP 파일 압축 해제")
    print("3. scripts/install.bat 실행")
    print("4. .env 파일에 HCX API 키 설정")
    print("5. scripts/run_evaluation.bat으로 평가 실행")
    print()
    print("📚 자세한 설치 방법은 OFFLINE_DEPLOYMENT.md와 MANUAL_INSTALLATION_GUIDE.md를 참조하세요.")

if __name__ == "__main__":
    main()