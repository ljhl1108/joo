# 에셋 직접 사용하기 — SPUM · Honeti GUI · AetherForge

> 2026-09-24 작성. 사람이 직접 해야 하는 작업의 순서만 적는다.
> 만든 결과물을 어디에 저장했는지만 알려주면, 유니티 연결(프리팹 교체·애니메이션·임포트 설정)은 Claude가 처리한다.

---

## A. SPUM — 인간형 캐릭터 만들기

### A-1. 최초 1회: 설치

1. 유니티에서 `Assets/SPUM/Scene/SPUM_Scene.unity` 열기
2. Hierarchy에서 **`SPUM_Manager`** 오브젝트 선택
3. Inspector 맨 위의 **`Install`** 버튼 클릭
4. `Assets/Resources/SPUM/SPUM_Sprites` 폴더가 생겼는지 확인 (안 생겼으면 맨 아래 **`Reset Resources Data`**)

### A-2. 캐릭터 만들기

1. `SPUM_Scene`에서 **Play** 실행 (에디터 위쪽 ▶)
2. 화면에서 파츠를 고른다
   - 왼쪽/오른쪽 패널: 몸(Human·Orc·Elf·Skeleton·Devil) / 머리카락 / 눈 / 옷 / 바지 / 갑옷 / 투구 / 망토 / 무기 / 방패
   - **Random** 버튼으로 굴려보다가 마음에 드는 걸 다듬는 방식이 빠르다
   - 색은 각 파츠의 컬러 피커로 바꿀 수 있다 → **팔레트를 맞추는 게 이질감 줄이는 핵심**
3. 애니메이션 버튼(IDLE / MOVE / ATTACK 등)으로 움직임을 미리 본다
4. **Save** 버튼 → 유닛이 `Assets/Resources/SPUM/SPUM_Units/`에 코드 이름으로 저장된다
5. Play 종료

### A-3. 만든 유닛을 게임에 넣기

Claude에게 **저장된 유닛 이름(또는 경로)과 어떤 적에 쓸지**만 알려주면 된다.
예: "SPUM_20260924… 유닛을 방패 근위병에 써줘"

Claude가 하는 일: 적 프리팹의 자식으로 교체 → `SpumEnemyVisual` 연결 → 크기·위치 보정 → 플레이 검증

### A-4. 수정하고 싶을 때

`SPUM_Scene` Play → **Load** 버튼 → 저장된 유닛 선택 → 고친 뒤 **Edit** 버튼으로 덮어쓰기

---

## B. Honeti GUI 킷 — UI 부품 찾기

- **데모 보기**: `Assets/Honeti/PixelArtGUI/Scenes/` 의 씬을 열면 모든 부품이 배치된 화면을 볼 수 있다
- **프리팹**: `Assets/Honeti/PixelArtGUI/Prefabs/` — Bars(체력바) / Buttons / Panels / Texts
- **이미지**: `Assets/Honeti/PixelArtGUI/Textures/` — Bars / Buttons / Icons(8·16·32px, 246종) / Panels / Misc

원하는 부품 이름만 알려주면 Claude가 해당 UI에 적용한다.
예: "업그레이드 카드 테두리를 CornersGold로 바꿔줘"

---

## C. AetherForge AI — 고양이 32px 다시 만들기

> 공식 튜토리얼: https://www.aetherforgeai.com/ko/tutorial
> ⚠️ **상업적 사용 라이선스는 이용약관에서 먼저 확인할 것** (페이지에 명시돼 있지 않음)

### C-1. 캐릭터 이미지 만들기

- 입력: **텍스트 프롬프트** 또는 **참고 이미지**
- 튜토리얼 권장사항
  - 프롬프트는 **영어로** 쓰는 편이 결과가 안정적
  - 한 번에 끝내려 하지 말고 **여러 번 생성**해서 고르기
  - 얼굴·의상을 유지하고 싶으면 `keep the same face`, `keep the costume design` 같은 문구를 덧붙인다

우리 고양이용 프롬프트 예시 (영어):

```
top-down 2D game sprite, small orange and white cat character,
standing upright, facing camera, simple pixel art, thick dark outline,
flat colors, limited palette, solid white background, centered, full body
```

### C-2. 애니메이션 만들기 (선택)

- **V1**: 이미지 1장 → 25~169 프레임 생성 (픽셀화 옵션 있음)
- **V2**: 시작 프레임 + 끝 프레임 → 49~121 프레임, 더 부드러움
- 준비 조건: 캐릭터가 **오른쪽을 보게**, **단색(흰색) 배경**, 캐릭터 주변에 여백
- 결과물: **GIF + 스프라이트 시트** 다운로드

> 프레임이 수십~백 장 나오는데 우리는 한 동작에 2~4장이면 충분하다.
> 다운로드 후 Aseprite에서 **필요한 프레임만 고르는 작업**이 반드시 필요하다.

### C-3. 우리 프로젝트에 맞게 다듬기 (Aseprite)

1. 받은 이미지를 Aseprite로 열기
2. `Sprite → Sprite Size`로 **32×32 또는 40×40**으로 축소 (Resize method: **Nearest Neighbor**)
3. 축소하면 뭉개지는 부분(눈·외곽선)을 손으로 정리 — 이 단계가 품질을 좌우한다
4. 팔레트 정리: 색 수를 16~24색 정도로 줄이면 타일셋과 잘 섞인다
5. 프레임에 **태그**를 단다: `idle`, `walk`, `attack`, `dash`
6. **`.aseprite`로 `Assets/Sprite/` 안에 저장** → 유니티가 자동으로 스프라이트와 애니메이션 클립을 만든다

그다음 Claude에게 알려주면 고양이 프리팹 교체·애니메이터 연결·화분 위치 보정까지 처리한다.

---

## D. 이질감을 줄이는 체크리스트

지금 SPUM 캐릭터가 겉도는 이유는 그림 실력 문제가 아니라 **규격이 안 맞아서**다. 순서대로 맞추면 크게 줄어든다.

| 항목 | 기준 | 현재 상태 |
|---|---|---|
| **키(높이)** | 캐릭터 = 타일 1칸(32px) 전후로 통일 | ❌ 고양이 64px(2칸) vs SPUM 기사 35px |
| **외곽선** | 있음/없음, 굵기 1px로 통일 | ⚠️ 고양이는 굵은 외곽선, SPUM은 얇음 |
| **팔레트** | 채도·명도를 타일셋(잔디·돌)에 맞춤 | ⚠️ SPUM 기본색이 더 선명함 → SPUM 편집기에서 색 조정 가능 |
| **시점** | 위에서 약간 기울여 보는 각도 | ✅ 모두 탑다운 |
| **그림자** | 캐릭터 발밑에 타원 그림자 | ❌ 아직 없음 (넣으면 바닥에 붙어 보인다) |

**가장 먼저 할 것은 키 통일.** 고양이를 32~40px로 다시 만들면 나머지는 색 조정으로 대부분 해결된다.
