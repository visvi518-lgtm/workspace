모티AI (MotiAI)
프로젝트 소개

AI를 활용한 건강 관리 플랫폼으로, 운동과 식단 기록부터 건강 상담, 건강 콘텐츠 제공까지 하나의 서비스에서 이용할 수 있도록 개발한 풀스택 웹 애플리케이션입니다.

사용자의 건강 데이터를 기반으로 맞춤형 운동 및 식단을 추천하며, AI 건강 상담, 콘텐츠 자동 수집 및 요약, 관리자 시스템 등을 직접 구현했습니다. React와 FastAPI를 기반으로 개발했으며 Render 환경에 실제 배포까지 완료했습니다.

프로젝트 정보
프로젝트 유형 : 개인 프로젝트
개발 기간 : 2025 ~ 2026
배포 : 완료
구현 기능 : 22+
운동 칼로리 DB : 55종
외부 API 연동 : 5개
배포 서비스 : 3개
기술 스택
Frontend
React 18
TypeScript
Vite
Tailwind CSS
TanStack Query
Zustand
React Router v6
Backend
FastAPI
Python 3.11
SQLAlchemy 2.0
PostgreSQL
JWT Authentication
APScheduler
Alembic
AI 및 외부 API
Google Gemini 2.5 Flash
Google OAuth
Naver OAuth
Naver Search API
BeautifulSoup4
Infrastructure
Render Static Site
Render Web Service
Render PostgreSQL
GitHub
주요 기능
AI 건강 상담

Google Gemini를 활용하여 건강 상담 기능을 구현했습니다.

병력 및 복약 정보를 컨텍스트로 활용
건강 관련 질의응답
의학적 근거 기반 응답 제공
운동 및 식단 관리

사용자의 건강 데이터를 지속적으로 기록하고 관리할 수 있도록 구현했습니다.

운동일지
식단일지
체중 그래프
캘린더 기반 기록 조회
음식 사진 AI 칼로리 분석
맞춤 운동 및 식단 추천

사용자의 목적에 따라 개인화된 추천을 제공합니다.

운동

자세 교정
근력 향상
체중 관리

식단

감량
증량
유지
의료 목적

SQLAlchemy JSON 컬럼을 활용하여 유연한 추천 데이터를 관리하도록 설계했습니다.

건강 콘텐츠 자동 수집 시스템

건강 정보를 자동으로 수집하고 게시하는 파이프라인을 구축했습니다.

동작 과정

네이버 Search API
      ↓
뉴스/블로그 수집
      ↓
BeautifulSoup 원문 추출
      ↓
Gemini 6줄 요약
      ↓
중복 검사
      ↓
관리자 승인
      ↓
게시판 게시

특징

AI 자동 요약
관리자 승인 시스템
중복 게시물 제거
크롤링 중단 기능
Rollback 지원
게시판
건강정보
운동정보
자유게시판
댓글
태그 검색
페이지네이션
관리자 승인 게시물 관리
관리자 페이지

관리자가 서비스 전체를 관리할 수 있도록 구현했습니다.

사용자 관리
계정 정지
게시글 승인
크롤링 제어
통계 대시보드
운동 DB 관리
추천 데이터 관리
인증 시스템
Google OAuth
Naver OAuth
JWT 인증
SMTP 이메일 인증
비밀번호 재설정
휴면 계정 처리
운동 칼로리 계산

MET 공식을 이용하여 운동 칼로리를 계산하도록 구현했습니다.

Calories = MET × 체중 × 운동시간

기능

운동 검색
운동 DB 관리
카테고리 필터
관리자 CRUD
자동 계산
개발 과정
Phase 1

백엔드 설계

REST API 설계
JWT 인증
User 모델
PostgreSQL 구조 설계
Phase 2

프론트엔드 구축

React
TypeScript
Tailwind
Zustand
TanStack Query
Phase 3

AI 건강 기능

Gemini 연동
운동 CRUD
식단 CRUD
AI 칼로리 분석
캘린더
Phase 4

콘텐츠 자동화

크롤링
AI 요약
중복 제거
관리자 승인
Phase 5

인증 시스템

OAuth
계정 병합
SMTP
JWT Reset Token
Phase 6

배포

Render
PostgreSQL
GitHub
SPA Rewrite
Phase 7

추천 시스템

규칙 기반 추천 알고리즘
JSON 컬럼 설계
관리자 CRUD
Phase 8

칼로리 계산 시스템

MET 계산
운동 검색
카테고리 필터
운동일지 연동
주요 문제 해결 사례
1. 게시판 로딩 속도 개선

문제

게시글 조회 시마다 실시간 크롤링과 AI 요약이 실행되어 응답 속도가 느렸습니다.

해결

크롤링을 백그라운드 작업으로 분리
Draft 상태 저장
관리자 승인 후 Published 전환
캐시 데이터 제공
2. 크롤링 중단 시 데이터 손상

문제

중단된 크롤링 데이터가 DB에 남았습니다.

해결

Stop Flag 구현
db.rollback() 적용
미완성 데이터 제거
3. Render 배포 오류

문제

Python 3.14에서 라이브러리 빌드 오류 발생

해결

Python 3.11 고정
환경변수 수정
패키지 교체
4. OAuth 404 오류

문제

배포 환경에서 OAuth가 404 발생

해결

API URL 환경변수 적용
절대 경로 사용
SPA Rewrite 적용
5. PostgreSQL 마이그레이션 오류

문제

ALTER TABLE 실행 중 트랜잭션 전체 중단

해결

쿼리별 Connection 분리
트랜잭션 독립 실행
6. TypeScript 타입 충돌

문제

동일 타입명이 서로 다른 도메인에서 충돌

해결

타입 분리
명확한 도메인 타입 정의
7. Header 클릭 영역 오류

문제

로고 영역이 헤더 밖까지 클릭되는 문제

해결

CSS 높이 수정
Header 영역과 일치하도록 조정
프로젝트 핵심 성과
React + FastAPI 기반 풀스택 서비스 개발
AI(Gemini)를 활용한 건강 상담 및 콘텐츠 요약 기능 구현
OAuth, JWT, SMTP를 이용한 인증 시스템 구축
규칙 기반 운동·식단 추천 알고리즘 설계
관리자 시스템 및 콘텐츠 관리 기능 구현
Render 환경에 프론트엔드·백엔드·PostgreSQL을 분리 배포
다양한 실제 서비스 환경의 문제를 해결하며 운영 경험 확보
