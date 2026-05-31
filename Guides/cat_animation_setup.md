# 고양이 캐릭터 스프라이트 & 애니메이션 적용 가이드

> 진행 상태: `[ ]` 미완료 · `[x]` 완료
> 완료 후 이 파일을 `Guides/Done/` 폴더로 이동

---

## [ ] 1단계 — Aseprite에서 스프라이트 시트 내보내기

각 방향 파일마다 반복 수행합니다.

1. 메뉴 **파일 → 내보내기 → 스프라이트 시트**
2. **레이아웃** 탭
   - 시트 유형: `수평 배치` (프레임을 한 줄로 나란히 배치 — 방향별 파일이 따로 있을 때 적합)
3. **출력** 탭
   - `출력 파일` 체크 → PNG 저장 경로 지정
   - `JSON 데이터` 체크 → 같은 이름의 `.json`도 함께 저장됨
4. **내보내기** 클릭

결과물 예시:
```
walk_down.png  +  walk_down.json
walk_up.png    +  walk_up.json
walk_left.png  +  walk_left.json
... (8방향 모두)
```

---

## [ ] 2단계 — Unity로 가져오기

1. PNG + JSON을 `Assets/Sprites/Character/` 에 드래그 앤 드롭
2. PNG 선택 후 Inspector 설정:
   - `Texture Type` → **Sprite (2D and UI)**
   - `Sprite Mode` → **Multiple**
   - `Pixels Per Unit` → **16** 또는 **32** (Aseprite 캔버스 크기 맞춤)
   - `Filter Mode` → **Point (no filter)**
   - `Compression` → **None**
3. **Apply** 클릭

---

## [ ] 3단계 — Sprite Editor에서 슬라이싱

1. PNG 선택 → Inspector에서 **Sprite Editor** 버튼 클릭
2. 상단 `Slice` 드롭다운 → `Type: Grid By Cell Size`
3. 프레임 크기 입력 (Aseprite 캔버스 가로/세로 픽셀)
4. **Slice** → **Apply**

---

## [ ] 4단계 — Animation Clip 만들기

1. `Project` 창에서 슬라이싱된 PNG를 펼치면 프레임들이 하위에 나타남
2. 해당 방향의 프레임 전체 선택 (Shift+클릭)
3. `Hierarchy`의 **CatBody**에 드래그 앤 드롭
4. "애니메이션 클립 저장" 팝업 → 저장 위치 지정 (`Assets/Animations/` 권장)

8방향 각각 Clip 생성:
- `cat_walk_down`, `cat_walk_up`, `cat_walk_left`, `cat_walk_right`
- `cat_walk_downleft`, `cat_walk_downright`, `cat_walk_upleft`, `cat_walk_upright`
- `cat_idle` (정지 프레임)

---

## [ ] 5단계 — Animator Controller & Blend Tree

1. `Assets` 우클릭 → Create → Animator Controller → `CatAnimator` 저장
2. Animator 창 열기 → 파라미터 추가:
   - `MoveX` (Float)
   - `MoveY` (Float)
   - `IsMoving` (Bool)
3. 우클릭 → `Create State → From New Blend Tree`
4. Blend Tree 더블클릭 → Inspector 설정:
   - `Blend Type`: **2D Simple Directional**
   - Parameters: `MoveX`, `MoveY`
5. `+` 버튼으로 8방향 + Idle 클립 추가, 방향 벡터 입력:

| 클립 | X | Y |
|------|---|---|
| cat_walk_up | 0 | 1 |
| cat_walk_down | 0 | -1 |
| cat_walk_left | -1 | 0 |
| cat_walk_right | 1 | 0 |
| cat_walk_upleft | -0.7 | 0.7 |
| cat_walk_upright | 0.7 | 0.7 |
| cat_walk_downleft | -0.7 | -0.7 |
| cat_walk_downright | 0.7 | -0.7 |
| cat_idle | 0 | 0 |

---

## [ ] 6단계 — CatController.cs 수정

`Awake()`에 추가:
```csharp
private Animator animator;
animator = GetComponentInChildren<Animator>();
```

이동 입력 처리 부분에 추가:
```csharp
Vector2 moveDir = /* 현재 입력 방향 */;
animator.SetFloat("MoveX", moveDir.x);
animator.SetFloat("MoveY", moveDir.y);
animator.SetBool("IsMoving", moveDir.magnitude > 0.1f);
```

> CatController.cs 코드 확인 후 정확한 삽입 위치를 안내받을 것

---

## [ ] 7단계 — Unity 에디터 마무리

- `CatBody` 오브젝트에 `Animator` 컴포넌트 추가
- `Controller` 필드에 `CatAnimator` 드래그 연결
- 게임 실행 후 8방향 이동 시 애니메이션 전환 확인
