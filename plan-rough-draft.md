# 치지직 플레이즈 게임개발 — 기획안

> 시청자 후원 기반 AI 라이브 게임 개발 방송 시스템
>
> Version 1.0 | 2026.03.31 | Author: Kay (박근우)
>
> Stack: FastAPI + Claude Agent SDK + Unity + React + chzzkpy
>
> 환경: 현재 개발 환경은 windows에 설치된 WSL 환경에서 개발 중이지만 실제 작동은 windows 환경에서 할 예정임.

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [비용 모델 및 후원 가격표](#3-비용-모델-및-후원-가격표)
4. [보안 아키텍처](#4-보안-아키텍처)
5. [큐 시스템 설계](#5-큐-시스템-설계)
6. [방송 화면 구성](#6-방송-화면-구성)
7. [컴포넌트별 상세 사양](#7-컴포넌트별-상세-사양)
8. [에셋 전략](#8-에셋-전략)
9. [구현 로드맵](#9-구현-로드맵)
10. [리스크 분석](#10-리스크-분석)
11. [성공 지표](#11-성공-지표)

---

## 1. 프로젝트 개요

### 1.1 컨셉

치지직에서 장시간(6시간~24시간) 방송을 켜놓고, 시청자가 후원을 통해 Claude Code에 프롬프트를 전송하면 AI가 실시간으로 Unity 게임을 개발하는 참여형 콘텐츠. 트위치 플레이즈 포켓몬의 게임 개발 버전.
첫 프롬프트는 내가 줄 것이고, 해당 프롬프트로 게임의 장르가 정해짐. 항상 main genre는 여기서 설정된 장르로 설정하되, 후원자들의 프롬프트를 최대한 수용해서 적절히 구현할 것. 장르가 뒤죽박죽이 되는 것 또한 컨텐츠의 일환.

### 1.2 핵심 가치

- **콘텐츠성**: AI가 코드 짜는 걸 실시간으로 보는 것 자체가 콘텐츠
- **수익화**: 후원 = 프롬프트 권한으로 자연스러운 모네타이제이션
- **바이럴**: 모순되는 요청이 쌓이며 괴작이 탄생하는 과정 자체가 바이럴 요소
- **포트폴리오**: AI 엔지니어링 실력을 실시간으로 보여주는 살아있는 포트폴리오

### 1.3 운영 모델

- 방송 시간: 하루 약 12시간 (24시간 자동 운영 목표)
- 리뷰 사이클: 6시간마다 1시간 직접 검수 (보안, 버그 수정, Git 커밋)
- 게임 배포: 무료 배포 (GitHub 공개 리포)
- 수익원: 후원금 (치즈) - API 비용 = 순익

---

## 2. 시스템 아키텍처

### 2.1 전체 파이프라인

시스템은 5개의 핵심 컴포넌트로 구성되며, 단방향 데이터 플로우를 따른다.

| 단계 | 컴포넌트 | 역할 | 기술 | 통신 |
|------|----------|------|------|------|
| 1 | chzzkpy 클라이언트 | 후원 이벤트 수신 | Python | WebSocket |
| 2 | 오케스트레이터 | 큐 관리, 필터링, 티어 분류 | FastAPI | REST + WS |
| 3 | Claude Agent SDK | 프롬프트 실행, 코드 생성 | Python SDK | Async Stream |
| 4 | Unity 프로젝트 | 게임 빌드 + 실행 | Unity Editor | File Watch |
| 5 | 큐 UI (OBS 오버레이) | 후원 대기열 표시 | React | WebSocket |

### 2.2 데이터 플로우

```
치지직 후원 → chzzkpy (후원 이벤트 수신) → 오케스트레이터 (필터링 + 큐 삽입)
→ Claude Agent SDK (query() 실행) → Unity 프로젝트 (코드 변경) → OBS 방송 화면
```

### 2.3 테크 스택

| 영역 | 기술 | 선택 이유 |
|------|------|-----------|
| Backend | FastAPI (Python 3.12+) | async 네이티브, chzzkpy와 같은 Python 생태계 |
| 후원 수신 | chzzkpy v2 (공식 API) | 공식 API 기반, donation 이벤트 구독 지원 |
| AI Agent | claude-agent-sdk (Python) | Hook 시스템, 세션 관리, 샌드박스 내장 |
| AI Model | Claude Sonnet 4.6 | $3/$15 per MTok, 코딩 성능 우수, 비용 효율적 |
| Game Engine | Unity 6+ (LTS) | C# 스크립트 핫 리로드, 방송에 적합한 UI |
| 큐 UI | React + WebSocket | OBS 브라우저 소스로 오버레이 가능 |
| 버전 관리 | Git + GitHub | 자동 커밋으로 롤백 가능, 공개 배포 |
| 인증 | Anthropic API Key | 레이트 리밋 널널, 종량제로 후원 마진 확보 |

---

## 3. 비용 모델 및 후원 가격표

### 3.1 API 비용 구조

Anthropic API Key 종량제 사용. Sonnet 4.6 기준: input $3/MTok, output $15/MTok.

Prompt caching 적용 시 input 비용 90% 절감 (Unity 프로젝트 컨텍스트가 매번 반복되므로 캐시 효율 높음). 환율 1,450원/$로 계산.

### 3.2 후원 티어별 원가 분석

아래 표는 Sonnet 4.6 + Prompt caching 적용 기준 예상 비용이며, 실제 비용은 프롬프트 복잡도에 따라 변동될 수 있다.

| 티어 | 후원금 | Input (K) | Output (K) | API 원가 | 순익 | 마진 |
|------|--------|-----------|------------|----------|------|------|
| 한 줄 수정 | 1,000원 | 15K | 4K | ~95원 | ~905원 | ~90% |
| 기능 추가 | 5,000원 | 50K | 18K | ~415원 | ~4,585원 | ~92% |
| 대규모 변경 | 10,000원 | 160K | 60K | ~1,380원 | ~8,620원 | ~86% |
| 카오스 모드 | 30,000원 | 300K | 120K | ~2,660원 | ~17,340원 | ~87% |

### 3.3 티어 기술적 제어

각 티어의 객관적 기준은 `max_turns`와 `allowed_tools` 조합으로 강제한다.

| 티어 | max_turns | allowed_tools | 예시 프롬프트 | 타임아웃 |
|------|-----------|---------------|---------------|----------|
| 한 줄 수정 | 1 | Read, Edit | `"점프 높이 2배로"` | 60초 |
| 기능 추가 | 3 | Read, Edit, Write, Bash | `"체력바 UI 추가"` | 120초 |
| 대규모 변경 | 8 | Read, Edit, Write, Bash, Glob | `"인벤토리 시스템"` | 180초 |
| 카오스 모드 | 15 | Read, Edit, Write, Bash, Glob, Grep | `"멀티플레이어 추가"` | 300초 |

### 3.4 예상 수익 시뮬레이션

보수적 가정: 하루 후원 50건 (한 줄 30, 기능 15, 대규모 4, 카오스 1)

- 일일 후원 수입: 30×1,000 + 15×5,000 + 4×10,000 + 1×20,000 = 165,000원
- 일일 API 비용: 30×95 + 15×415 + 4×1,380 + 1×2,660 = ~17,500원
- **일일 순익: ~147,500원 (마진 ~89%)**
- **월간 예상 순익 (30일): ~4,425,000원**

---

## 4. 보안 아키텍처

### 4.1 3계층 보안 모델

외부 프롬프트를 받는 시스템이므로, 3계층 보안을 적용한다.

#### Layer 1: 프롬프트 사전 필터링 (오케스트레이터)

Claude에 넘기기 전에 오케스트레이터에서 정규식 + 키워드 기반 1차 스크리닝.

- **차단 키워드**: `cd ..`, `/etc/`, `env`, `API_KEY`, `passwd`, `curl`, `wget`, `ssh`, `nc`, `ncat`, `eval`, `exec`, `import os`, `subprocess`
- **차단 패턴**: 상위 디렉토리 접근 (`../`), 절대경로 (`/home`, `/root`, `/var`), 네트워크 명령어
- **처리**: 차단된 프롬프트는 실행하지 않고 "클로드가 윤리적 기준에 의해 거부했습니다" 메시지 표시

#### Layer 2: Agent SDK Hook (런타임 차단)

Claude가 실제로 실행하려는 명령어를 `PreToolUse` hook에서 검사하여 차단.

- Bash 명령어 중 위험 패턴 감지 시 `permissionDecision: "deny"` 반환
- 프로젝트 디렉토리 외부 파일 접근 시도 차단
- 네트워크 요청 (curl, wget, fetch) 차단

```python
async def security_hook(input_data, tool_use_id, context):
    if input_data["tool_name"] == "Bash":
        command = input_data["tool_input"].get("command", "")
        dangerous = ["rm -rf", "curl", "wget", "../", "/etc/", "env"]
        for pattern in dangerous:
            if pattern in command:
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"Blocked: {pattern}"
                    }
                }
    return {}
```

#### Layer 3: OS 레벨 샌드박스

Agent SDK의 sandbox 모드를 활성화하여 파일 시스템과 네트워크 접근을 OS 레벨에서 격리.

- `cwd`를 Unity 프로젝트 루트로 제한
- 네트워크: 모든 도메인 차단 (Unity 패키지 매니저 예외 가능)
- 파일 시스템: Unity 프로젝트 폴더 외 쓰기 금지

### 4.2 Ban 시스템

- 보안 필터에 걸린 후원자의 치지직 ID를 블랙리스트 DB에 저장
- 이후 해당 ID의 후원은 자동 무시 (후원금은 수령되지만 프롬프트 미실행)
- 방송 화면에 Ban 알림 표시

### 4.3 Git 안전망

- 매 후원 프롬프트 처리 후 자동 WIP 커밋
- 커밋 메시지 포맷: `[auto] {donor_name}: {prompt_summary}`
- 빌드 실패 시 자동 `git revert HEAD`
- 6시간마다 운영자가 직접 리뷰 → squash merge → main 브랜치

---

## 5. 큐 시스템 설계

### 5.1 큐 우선순위

후원 금액이 높을수록 높은 우선순위를 부여하되, 같은 티어 내에서는 FIFO(선입선출) 순서를 따른다. 단, 우선순위가 높은 후원이 들어와도 현재 실행 중인 프롬프트는 중단하지 않는다 (non-preemptive).

### 5.2 쿨다운 정책

같은 유저가 연속 후원으로 큐를 독점하는 것 방지:

- 유저당 최소 간격: 한 줄 수정 1분, 기능 추가 3분, 대규모 5분, 카오스 10분
- 쿨다운 중에도 후원은 받되, 큐에 대기 상태로 등록

### 5.3 큐 UI 사양

OBS 브라우저 소스로 표시되는 React 웹 앱.

- **현재 실행 중**: 상단에 강조 표시 (후원자명, 프롬프트 요약, 티어 배지, 경과 시간)
- **대기열**: 아래에 리스트로 표시 (최대 8건)
- **티어별 시각적 구분**: 한 줄(회색), 기능(파란), 대규모(보라), 카오스(금색)
- **통신**: FastAPI 서버와 WebSocket 연결, 실시간 업데이트

---

## 6. 방송 화면 구성

### 6.1 레이아웃

```
┌──────────────────────────┬──────────────────────────┐
│                          │    후원 큐 UI (상단 50%)   │
│                          │  현재 실행 중 + 대기열      │
│   Claude Code Terminal   │  React 앱 (OBS 브라우저)   │
│                          ├─────────────┬────────────┤
│   전체 높이 차지           │ Metadata    │ 채팅 +     │
│   후원 프롬프트 실행 화면   │ (하단좌)    │ 카메라/    │
│                          │ 게임 제목,   │ 아바타     │
│                          │ GitHub 링크  │ (하단우)   │
└──────────────────────────┴─────────────┴────────────┘
```

- **좌측 50%**: Claude Code 터미널 (전체 높이). 후원 프롬프트가 실행되는 터미널 화면 실시간 표시.
- **우측 상단 50%**: 후원 큐 UI. 현재 실행 중 프롬프트 + 대기열. React 앱 (OBS 브라우저 소스).
- **우측 하단 좌측**: Metadata 패널. 게임 제목/주제, GitHub 다운로드 링크, 현재 게임 상태.
- **우측 하단 우측**: 채팅 + 카메라/아바타. OBS에서 직접 배치.

---

## 7. 컴포넌트별 상세 사양

### 7.1 후원 수신 모듈 (chzzkpy)

치지직 공식 API를 chzzkpy v2로 연동. `UserPermission(donation=True)`로 후원 이벤트만 구독.

- **수신 데이터**: 후원자 닉네임, 후원 금액, 후원 메시지 (프롬프트로 사용), 유저 ID
- **인증**: 치지직 개발자센터에서 `client_id` + `client_secret` 발급
- **에러 처리**: 연결 끊김 시 자동 재연결 (exponential backoff)

### 7.2 오케스트레이터 (FastAPI)

전체 시스템의 중앙 제어 서버.

**API 엔드포인트:**
- `POST /donation` — 후원 이벤트 수신 (내부)
- `GET /queue` — 현재 큐 상태 조회
- `WS /ws/queue` — 큐 실시간 업데이트 (React UI용)
- `POST /ban/{user_id}` — 수동 Ban
- `GET /stats` — 통계 (총 후원, API 비용, 마진)

**큐 관리**: `asyncio.PriorityQueue` 사용, 티어별 우선순위 + FIFO

**상태 관리**: `IDLE → FILTERING → QUEUED → RUNNING → BUILDING → DONE/FAILED`

### 7.3 Claude Agent SDK 연동 모듈

Python Agent SDK의 `ClaudeSDKClient`를 사용하여 세션을 유지하며 프롬프트를 실행.

- **세션 관리**: 방송 시작 시 세션 생성, Unity 프로젝트 컨텍스트 유지
- **system_prompt**: "너는 Unity C# 게임 개발자이다. 현재 프로젝트의 Assets/Scripts/ 폴더에서 작업한다..."
- **Hook 구성**:
  - `PreToolUse` — 보안 검사 (Layer 2)
  - `PostToolUse` — 변경사항 로깅, Git 커밋 트리거
- **비용 추적**: 각 세션의 token usage를 기록하여 실제 마진 모니터링

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher

options = ClaudeAgentOptions(
    model="claude-sonnet-4-6-20250514",
    cwd="/path/to/unity-project",
    system_prompt="너는 Unity C# 게임 개발자이다...",
    allowed_tools=["Read", "Edit", "Write", "Bash"],
    max_turns=3,  # 티어별 동적 설정
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[security_hook])
        ],
        "PostToolUse": [
            HookMatcher(matcher=".*", hooks=[git_commit_hook])
        ]
    }
)
```

### 7.4 큐 UI (React)

OBS 브라우저 소스로 표시되는 단일 페이지 React 앱.

- **기술**: React 18+ / Vite / TailwindCSS
- **통신**: WebSocket으로 FastAPI 서버와 연결
- **표시 요소**:
  - 현재 실행 중 프롬프트 (후원자명 + 티어 배지 + 프롬프트 + 타이머)
  - 대기열 리스트 (최대 8건, 스크롤)
  - Ban 알림 애니메이션
  - 처리 완료 알림 (성공/실패)
- **배경**: 투명 (크로마키 사용) — OBS에서 합성

---

## 8. 에셋 전략

### 8.1 Phase별 에셋 접근

게임은 코드만으로 완성되지 않는다. 캐릭터, 환경, UI, 사운드 등 에셋이 필요하며, 이를 Phase별로 확장한다.

| Phase | 에셋 전략 | 설명 |
|-------|-----------|------|
| Phase 1 (MVP) | 기본 도형 Only | Unity 내장 프리미티브 (Cube, Sphere, Capsule) + 색상만으로 게임 구성. 코드 생성 파이프라인 검증에 집중. |
| Phase 2 | 프로시저럴 생성 | Claude가 코드로 만드는 에셋 활용. 프로시저럴 메시, 파티클 이펙트, Unity UI 시스템으로 자체 제작. |
| Phase 3 | 무료 에셋팩 도입 | Unity Asset Store 무료 에셋 10~20개 프로젝트에 임포트. system_prompt에 에셋 목록 명시. |
| Phase 4 | 에셋 후원 티어 | "에셋 업그레이드" 후원 — 기본 도형 캐릭터를 에셋팩 캐릭터로 교체하는 특별 커맨드. |

### 8.2 Phase 1: 기본 도형 가이드

MVP에서는 에셋 없이 게임이 동작해야 한다. system_prompt에 아래 제약 명시:

- 모든 시각적 오브젝트는 Unity 기본 프리미티브 (Cube, Sphere, Capsule, Cylinder, Plane)로 구성
- 색 구분은 Material의 color 속성으로 처리
- UI는 Unity 내장 Canvas + TextMeshPro 사용
- 사운드는 코드로 생성 가능한 AudioClip (사인파, 비프음) 또는 무음

콘텐츠적으로 오히려 이게 더 재밌을 수 있다 — 네모가 동그라미를 쏘는 슈팅게임, 캡슐이 점프하는 플랫포머 등. 기본 도형이 점점 진화하는 과정 자체가 바이럴 요소.

### 8.3 Phase 3: 무료 에셋팩 추천 카테고리

Asset Store에서 미리 받아둘 무료 에셋 카테고리:

- 캐릭터: Low-poly 캐릭터 팩 (로우폴리가 Claude 코드 연동에 가장 쉬움)
- 환경: 간단한 지형, 나무, 건물 프리팹
- UI: 무료 UI 킷 (버튼, 패널, 아이콘)
- 이펙트: 파티클 이펙트 팩 (폭발, 총알, 마법)
- 사운드: 무료 SFX 팩 (효과음, BGM)

에셋 임포트 후 `Assets/ThirdParty/` 하위에 정리하고, system_prompt에 에셋 경로와 프리팹 목록을 명시하여 Claude가 활용 가능하게 한다.

### 8.4 에셋 관련 system_prompt 예시

```
Phase 1:
"시각적 오브젝트는 반드시 Unity 기본 프리미티브만 사용한다.
 색상은 new Material()로 구분한다. 외부 에셋은 없다."

Phase 3:
"Assets/ThirdParty/ 폴더에 아래 에셋이 있다:
 - Characters/LowPoly/: LowPolyWarrior.prefab, LowPolyArcher.prefab ...
 - Environment/: Tree_01.prefab, Rock_03.prefab, Ground_Tile.prefab ...
 - VFX/: Explosion.prefab, MuzzleFlash.prefab ...
 - Audio/SFX/: jump.wav, hit.wav, coin.wav ...
 기존 기본 도형을 이 에셋으로 교체하는 것도 가능하다."
```

---

## 9. 구현 로드맵

### Phase 1: MVP (1주차)

최소 기능으로 방송 가능한 상태를 만든다.

- [ ] FastAPI 오케스트레이터 기본 구조 (큐, WebSocket)
- [ ] chzzkpy v2 후원 이벤트 수신 연동
- [ ] Claude Agent SDK `query()` 기본 연동
- [ ] React 큐 UI MVP (OBS 브라우저 소스)
- [ ] Unity 빈 프로젝트 세팅
- [ ] Git 자동 커밋 스크립트

### Phase 2: 보안 + 안정성 (2주차)

- [ ] 3계층 보안 필터 구현 (사전 필터 + Hook + Sandbox)
- [ ] Ban 시스템 구현
- [ ] Build 실패 시 자동 롤백
- [ ] 프롬프트 실행 타임아웃
- [ ] 유저별 쿨다운 정책
- [ ] 에러 핸들링 + 재연결 로직

### Phase 3: 폴리싱 (3주차)

- [ ] 큐 UI 디자인 마무리 (티어별 색상/장식, 애니메이션)
- [ ] Metadata 패널 (GitHub 링크, 게임 정보)
- [ ] 비용 모니터링 대시보드
- [ ] Watchdog (시스템 장애 감지 + 알림)

### Phase 4: 확장 (4주차+)

- [ ] 투표 시스템 (채팅 투표로 우선순위 결정)
- [ ] "되돌리기" 후원 (git revert 특별 커맨드)
- [ ] 모델 라우팅 (Haiku로 간단한 작업 처리)
- [ ] 다중 게임 프로젝트 지원
- [ ] 24시간 완전 자동 운영

### Phase 5: 필수는 아니지만 있으면 좋을 수도 있는 기능들

- [ ] 하이라이트 클립 자동 생성 (방송 클립 → 유튜브 콘텐츠)

---

## 10. 리스크 분석

| 리스크 | 심각도 | 영향 | 대응책 |
|--------|--------|------|--------|
| 큐 처리 실패 | 상 | 시청자 이탈 | 큐로 등록된 모든 프롬프트와 후원자 명과 ID, 프롬프트 적용이 되었는지 안되었는지에 대한 여부, 날짜, Commit ID 등 추적할 수 있는 내용 기록 및 디스코드 알림 |
| API 비용 폭주 | 중 | 예상치 못한 고액 청구 | max_turns로 제한 + 일일 예산 상한 설정 |
| 악성 프롬프트 | 높음 | 개인정보 탈취, 시스템 파괴 | 3계층 보안 + Ban 시스템 |
| Unity 빌드 실패 | 중 | 게임 먹통, 방송 중단 | 자동 git revert + 전 상태 복원 |
| 치지직 API 변경 | 낮음 | 후원 수신 불가 | SSAPI 대체 API 준비 |
| 큐 독점 | 중 | 한 유저가 연속 후원으로 큐 점유 | 유저별 쿨다운 정책 |
| 컨텍스트 붕괴 | 중 | 모순되는 요청으로 코드 수습불가 | 6시간마다 리뷰 사이클 |
| Anthropic 요금 변경 | 낮음 | 마진율 변동 | 후원 가격표 조정 + 모델 라우팅 |

---

## 11. 성공 지표

### 11.1 방송 지표

- 일 평균 동시 시청자 수 50명 이상 (1개월 목표)
- 일 평균 후원 건수 30건 이상
- 큐 처리 성공률 95% 이상

### 11.2 수익 지표

- 월 순익 300만원 이상 (3개월 목표)
- API 비용 대비 마진 85% 이상 유지

### 11.3 브랜딩 지표

- 유튜브 구독자 1,000명 도달 (3개월 목표)
- 치지직 팔로워 100명 도달 (3개월 목표)
- (나중에) 방송 클립 → 유튜브 콘텐츠 전환율 추적

---

## Appendix: 참고 링크

- **chzzkpy v2**: https://github.com/gunyu1019/chzzkpy
- **치지직 공식 API**: https://chzzk.gitbook.io/chzzk
- **Claude Agent SDK (Python)**: https://platform.claude.com/docs/en/agent-sdk/python
- **Agent SDK Hooks**: https://platform.claude.com/docs/en/agent-sdk/hooks
- **Agent SDK Permissions**: https://platform.claude.com/docs/en/agent-sdk/permissions
- **Anthropic API Pricing**: https://platform.claude.com/docs/en/about-claude/pricing
- **SSAPI (대체 후원 API)**: https://ssapi.kr/
- **awesome-chzzk**: https://github.com/dokdo2013/awesome-chzzk