@echo off
call venv\Scripts\activate.bat

echo RAGTrace Lite 평가 실행...
ragtrace-lite evaluate data\input\evaluation_data.json --llm hcx

echo 평가 완료!
echo 결과: reports\web\dashboard.html 확인

echo.
echo 웹 대시보드 생성...
ragtrace-lite dashboard --open

pause