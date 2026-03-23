# Next Steps — Multi-Source Fusion Feature

> Design doc: `~/.gstack/projects/kipeum86-content-dashboard-agent/kpsfamily-main-design-20260323-182505.md`
> Status: APPROVED (2026-03-23)

## Context

/office-hours 완료. Approach B (Analysis-Aware Fusion) 선택.
여러 소스(PDF + YouTube + 웹페이지 등)를 합쳐서 하나의 대시보드로 만드는 기능.

## TODO

- [ ] `/plan-eng-review` 실행 — 아키텍처, 테스트, 엣지케이스 검토
- [ ] fusion JSON 스키마 확정 (`content_analysis.json` for `content_type: "fusion"`)
- [ ] CLAUDE.md 업데이트 — 멀티소스 감지, fusion 워크플로우, 폴더 구조 추가
- [ ] content-analyzer sub-agent에 fusion-aware 프롬프트 작성
- [ ] web-content-designer에 fusion 대시보드 템플릿 추가
- [ ] 실제 소스로 테스트 (예: 책 PDF + YouTube 강의)
- [ ] 첫 번째 fusion 예제 → `/library/example-fusion-01.html` 등록
