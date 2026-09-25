# Sprite Normal Map — URP 2D Lit Sprite

리서치 날짜: 2026-09-25

## 개요

URP 2D에서 스프라이트에 노말 맵을 적용하면 2D 라이트(Point Light, Spot Light)가 스프라이트 표면을 3D처럼 조명한다.
평면 픽셀아트에 입체감·깊이감을 더하는 기법으로, 보스 스프라이트나 주요 오브젝트의 시각적 완성도를 크게 높인다.

**OnionCat 관련성**: 고양이 캐릭터, 보스, 주요 소품(화분 등)에 적용하면 2D 라이트로 드라마틱한 조명 효과 가능.
완전 적용보다는 **보스 등 하이라이트 에셋에만 선택적 적용** 권장 (성능·아트 스타일 고려).

## Unity 구현 방법

### 1. URP 2D Renderer 준비

Project Settings → Graphics → Scriptable Render Pipeline Asset이 **URP**이고,
Renderer가 **2D Renderer**여야 한다 (Forward Renderer에서는 2D Lit 미지원).

```
URP Asset → Renderer List → 2D Renderer Data
```

### 2. Lit 머티리얼 사용

Sprite Renderer의 Material을 **Sprite-Lit-Default**로 설정:
```
Project → Create → 2D → Sprite-Lit-Default Material
```
또는 Sprite Renderer의 Material 슬롯에서 직접 선택.

### 3. 노말 맵 텍스처 생성

#### 방법 A: NormalMap Online (무료 웹 도구)
1. https://cpetry.github.io/NormalMap-Online/ 접속
2. 스프라이트 PNG 업로드
3. Strength, Level 조절 후 다운로드
4. 픽셀아트: **Blur = 0, Strength = 낮게(0.5~1)** — 과도한 블러 방지

#### 방법 B: GIMP (무료)
1. Filter → Map → Normal Map (GIMP NormalMap 플러그인 필요)
2. Depth 조절, Wrap 체크 해제

#### 방법 C: Aseprite + 외부 도구 조합
```bash
# Aseprite로 스프라이트 내보내기
"$A" --batch sprite.aseprite --save-as sprite_base.png
# 이후 방법 A 또는 B로 노말 맵 생성
```

#### 픽셀아트 노말 맵 특이사항
- **Point Filtering 유지**: 노말 맵 텍스처도 Filter Mode = Point, 압축 = None (DXT5nm 권장)
- 스프라이트와 동일한 PPU(32) 설정
- 아웃라인이 있는 스프라이트: 아웃라인 부분은 배경과 같은 노말 값으로 처리

### 4. Unity에서 노말 맵 텍스처 임포트

```
텍스처 선택 → Inspector
Texture Type: Normal map ← 반드시 이 타입으로
Filter Mode: Point (픽셀아트)
Compression: None 또는 Normal Quality
Apply
```

### 5. 스프라이트에 노말 맵 연결

**방법 A: Sprite Renderer + Lit Material의 Normal Map 슬롯**
```
Sprite Renderer의 Material (Sprite-Lit-Default) 에서
Normal Map 텍스처 슬롯에 생성한 노말맵 드래그
```

**방법 B: 커스텀 Shader Graph (URP 2D Lit)**
1. Create → Shader Graph → URP → Sprite Lit Shader Graph
2. Sprite Normal Map 노드 사용
3. 디테일 노말, 동적 노말 합성 가능

### 6. 씬에 2D Light 배치

노말 맵은 **2D 라이트가 있어야** 효과가 보인다:
```
Create → Light → 2D → Point Light 2D
또는 Global Light 2D (전체 조명)
```

```csharp
// 런타임 조명 조절 예시 (히트 시 플래시)
[SerializeField] Light2D hitLight;

IEnumerator HitLightFlash() {
    hitLight.intensity = 3f;
    yield return new WaitForSeconds(0.08f);
    hitLight.intensity = 1f;
}
```

### 7. 검증

Game View에서 라이트를 좌우로 움직이면 스프라이트 표면에 그림자가 생기면 정상 동작.

## OnionCat 적용 포인트

### 적용 우선순위 (ROI 높은 순서)

1. **보스 스프라이트** — 보스 방 진입 시 드라마틱한 백라이트 + Point Light로 등장 연출
2. **고양이 캐릭터** — 이동 방향에 따라 조명 방향이 달라지는 느낌
3. **화분(Flowerpot)** — 공유 바디의 특징적 오브젝트, 도자기 질감 강조
4. **적 엘리트 변종** — 일반 적과 시각적으로 구별

### 구현 팁

```csharp
// 보스 입장 시 드라마틱 조명 전환
public class BossLightController : MonoBehaviour {
    [SerializeField] Light2D[] bossLights;
    [SerializeField] Light2D globalLight;

    public void OnBossEnter() {
        globalLight.intensity = 0.2f; // 전체 어둡게
        foreach (var l in bossLights) l.enabled = true;
    }
}
```

### 성능 고려

- URP 2D Light는 기본적으로 라이트 수가 많을수록 Draw Call 증가
- `Light2D.blendStyleIndex`를 같은 스타일끼리 묶으면 배칭 유지
- 노말 맵 자체는 텍스처 샘플링 추가 비용 (모바일 타겟이면 신중히)
- OnionCat이 640×360 저해상도이므로 성능 여유 있음

### 픽셀아트에서의 한계

노말 맵이 너무 강하면 "픽셀아트 느낌"을 해칠 수 있다.
→ 라이트 Intensity를 낮게(0.3~0.7) 유지, 보조적 효과로만 사용 권장.
→ 아트 디렉터(사용자)가 먼저 소수 에셋으로 테스트 후 결정할 것.

## 참고 링크

- Unity 공식 URP 2D Lights: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@14.0/manual/2DLighting-concept.html
- NormalMap Online (무료): https://cpetry.github.io/NormalMap-Online/
- Unity 2D 노말맵 튜토리얼 (YouTube): "Unity 2D normal map sprites URP" 검색
- Brackeys — URP 2D Lighting: https://www.youtube.com/watch?v=nkgaMkhQknA
- Pixel art normal map tips: https://0x72.itch.io/pixeldudesmaker (normal map section)
