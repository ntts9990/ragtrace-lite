#!/usr/bin/env python3
"""
Python 3.11 Windows 설치 파일 다운로드 스크립트
폐쇄망 배포를 위해 Python 설치 파일을 미리 다운로드합니다.
"""

import os
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse

def download_python_installer():
    """Python 3.11 Windows 설치 파일을 다운로드합니다."""
    
    # Python 3.11 최신 버전 URL (2024년 기준)
    python_url = "https://www.python.org/ftp/python/3.11.10/python-3.11.10-amd64.exe"
    
    # 다운로드 디렉토리 생성
    download_dir = Path("python-installer")
    download_dir.mkdir(exist_ok=True)
    
    # 파일명 추출
    filename = urlparse(python_url).path.split('/')[-1]
    output_path = download_dir / filename
    
    print("🐍 Python 3.11 Windows 설치 파일 다운로드")
    print("=" * 50)
    print(f"📥 다운로드 URL: {python_url}")
    print(f"📁 저장 위치: {output_path.absolute()}")
    
    # 이미 파일이 있는지 확인
    if output_path.exists():
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✅ 파일이 이미 존재합니다 ({file_size_mb:.1f} MB)")
        
        user_input = input("다시 다운로드하시겠습니까? (y/N): ")
        if user_input.lower() != 'y':
            print("다운로드를 건너뜁니다.")
            return str(output_path)
    
    try:
        print("📥 다운로드 시작...")
        
        # 파일 다운로드
        response = requests.get(python_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        total_size_mb = total_size / (1024 * 1024)
        
        print(f"📊 파일 크기: {total_size_mb:.1f} MB")
        
        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # 진행률 표시
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r진행률: {progress:.1f}% ({downloaded / (1024*1024):.1f}/{total_size_mb:.1f} MB)", end='', flush=True)
        
        print()  # 새 줄
        print(f"✅ 다운로드 완료: {output_path}")
        
        # 파일 검증
        if output_path.exists() and output_path.stat().st_size > 0:
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"📊 최종 파일 크기: {file_size_mb:.1f} MB")
            
            # 설치 파일 정보 생성
            create_installer_info(output_path)
            
            return str(output_path)
        else:
            print("❌ 다운로드된 파일이 올바르지 않습니다")
            return None
            
    except requests.RequestException as e:
        print(f"❌ 다운로드 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None

def create_installer_info(installer_path: Path):
    """설치 파일 정보를 생성합니다."""
    info_content = f"""# Python 3.11 Windows 설치 파일

## 파일 정보
- **파일명**: {installer_path.name}
- **다운로드 날짜**: {os.popen('date').read().strip()}
- **파일 크기**: {installer_path.stat().st_size / (1024*1024):.1f} MB
- **경로**: {installer_path.absolute()}

## 설치 방법

### GUI 설치 (권장)
1. {installer_path.name} 더블클릭
2. "Add Python to PATH" 체크
3. "Install for all users" 체크
4. "Install Now" 클릭

### 명령줄 자동 설치
```cmd
{installer_path.name} /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
```

## 설치 확인
```cmd
python --version
python -m pip --version
```

## 주의사항
- 관리자 권한으로 실행 필요
- 기존 Python 버전과 충돌 가능성 확인
- PATH 환경변수 설정 확인

## 라이선스
Python Software Foundation License
https://docs.python.org/3/license.html
"""
    
    info_file = installer_path.parent / "PYTHON_INSTALLER_INFO.md"
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(info_content)
    
    print(f"📝 설치 정보 파일 생성: {info_file}")

def main():
    """메인 함수"""
    print("🔒 RAGTrace Lite 폐쇄망 배포 - Python 설치 파일 다운로드")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"📁 현재 디렉토리: {current_dir}")
    
    # Python 설치 파일 다운로드
    installer_path = download_python_installer()
    
    if installer_path:
        print("\n🎉 Python 설치 파일 다운로드 완료!")
        print("   폐쇄망 배포 시 python-installer/ 폴더를 함께 복사하세요.")
        print("\n📋 다음 단계:")
        print("1. scripts/download_bge_m3.py 실행하여 BGE-M3 모델 다운로드")
        print("2. scripts/create_offline_package.py 실행하여 배포 패키지 생성")
    else:
        print("\n❌ Python 설치 파일 다운로드 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()