# 패럴랙스 배경 시스템 (Parallax Background System)

리서치 날짜: 2026-07-30

## 개요
패럴랙스 스크롤링은 배경을 여러 레이어로 나누어 카메라 이동 속도에 비례하되 서로 다른 속도로 스크롤시키는 기법. 멀리 있는 레이어일수록 느리게 움직여 원근감과 깊이를 만들어냄.

OnionCat에서는 각 방(Room)이 독립된 프리팹 단위이지만, 방 배경에 2~3개의 레이어를 적용하면 픽셀아트 던전에 시각적 입체감을 쉽게 부여할 수 있음.

## Unity 구현 방법

### 방법 1: C# 스크립트로 레이어 오프셋 계산
```csharp
public class ParallaxLayer : MonoBehaviour
{
    [SerializeField] private float parallaxFactor; // 0 = 카메라 동기화, 1 = 완전 고정
    private Camera _cam;
    private Vector3 _lastCamPos;

    private void Awake()
    {
        _cam = Camera.main;
        _lastCamPos = _cam.transform.position;
    }

    public void ResetLastPosition()
    {
        _lastCamPos = _cam.transform.position;
    }

    private void LateUpdate()
    {
        Vector3 delta = _cam.transform.position - _lastCamPos;
        transform.position += new Vector3(delta.x * (1f - parallaxFactor),
                                          delta.y * (1f - parallaxFactor), 0f);
        _lastCamPos = _cam.transform.position;
    }
}
```

방 진입 시 반드시 `ResetLastPosition()`을 호출해야 카메라 점프 시 배경이 튀는 버그를 방지.

### 방법 2: 머티리얼 텍스처 오프셋 (무한 루프 배경)
카메라가 이동할 때 배경이 끊기지 않도록 텍스처를 반복:
```csharp
[SerializeField] private float parallaxFactor;
private Material _mat;
private Camera _cam;

private void Awake()
{
    _mat = GetComponent<SpriteRenderer>().material;
    _cam = Camera.main;
}

private void LateUpdate()
{
    Vector2 offset = new Vector2(_cam.transform.position.x, _cam.transform.position.y) * parallaxFactor;
    _mat.SetTextureOffset("_MainTex", offset);
}
```
SpriteRenderer의 Material이 Tiling을 지원해야 함 (Sprite/Default 쉐이더에서 Tiling 활성화).

### 레이어 구성 예시 (던전 방)
| 레이어 | 내용 | parallaxFactor |
|--------|------|----------------|
| 맨 뒤 | 어두운 동굴 벽, 안개 | 0.9 (거의 고정) |
| 중간 | 기둥, 횃불, 거미줄 | 0.5 |
| 앞 | 포그라운드 식물, 바위 | 0.2 (빠르게 이동) |
| 게임플레이 | 타일맵(바닥/벽) + 캐릭터 | 0 (카메라 동기화) |

### Sorting Layer 설정
Unity의 Sprite Renderer → Sorting Layer에서 깊이 순서 지정:
- **Background** → Sorting Order 낮음 (맨 뒤)
- **Midground** → Sorting Order 중간
- **Foreground** → Sorting Order 높음
- **Characters**, **UI** → 최상위

### Pixel Art 주의사항
parallaxFactor로 인해 소수점 이동이 발생 → 픽셀 흔들림(jitter) 발생 가능.
해결 방법:
1. `Pixel Perfect Camera` 컴포넌트 사용 → Unity 2D Pixel Perfect 패키지
2. 배경 스프라이트를 낮은 해상도(16px 타일)로 제작해 픽셀 단위 이동을 자연스럽게 처리
3. LateUpdate에서 transform.position을 픽셀 그리드로 스냅:
   ```csharp
   float ppu = 16f; // pixels per unit
   Vector3 snapped = new Vector3(
       Mathf.Round(transform.position.x * ppu) / ppu,
       Mathf.Round(transform.position.y * ppu) / ppu, 0f);
   transform.position = snapped;
   ```

## OnionCat 적용 포인트

### 방 배경에 ParallaxLayer 적용
각 방 프리팹에 자식 GameObject를 2~3개 추가하고 `ParallaxLayer` 컴포넌트 부착:
- **BackgroundLayer**: 동굴 암벽/원경 (parallaxFactor 0.85)
- **MidgroundLayer**: 기둥/횃불/장식 (parallaxFactor 0.5)
- **ForegroundLayer**: 전경 잡초/바위 (parallaxFactor 0.15)

### 방 전환 시 처리
방이 활성화될 때 모든 `ParallaxLayer.ResetLastPosition()` 호출 → 카메라 순간 이동으로 인한 배경 튐 방지.

```csharp
// Room.cs에서
private void OnEnable()
{
    foreach (var layer in GetComponentsInChildren<ParallaxLayer>())
        layer.ResetLastPosition();
}
```

### 던전 테마별 배경 세트
| 던전 테마 | 뒤 레이어 | 중간 레이어 | 앞 레이어 |
|-----------|-----------|-------------|-----------|
| 지하 동굴 | 어두운 암벽, 안개 | 종유석, 버섯 | 작은 돌, 잡초 |
| 식물 온실 | 밝은 유리창, 구름 | 덩굴, 큰 잎 | 꽃가루 파티클 |
| 유적 폐허 | 건물 실루엣, 먼지 | 무너진 기둥 | 낙엽 |

### 성능 고려
- 배경 레이어는 스프라이트 1장으로 충분 (타일맵 대신 단순 이미지)
- 방 비활성화 시 함께 비활성화되어 드로우콜 자동 제거
- 방 3개 이상 동시 활성화 금지 원칙 유지 (기존 Room System 참고)

## 참고 링크
- Unity Docs - Sprite Renderer: https://docs.unity3d.com/Manual/class-SpriteRenderer.html
- Unity 2D Pixel Perfect: https://docs.unity3d.com/Packages/com.unity.2d.pixel-perfect@5.0/manual/index.html
- Brackeys 패럴랙스 튜토리얼: 유튜브에서 "Brackeys parallax scrolling Unity" 검색
- Unity Sorting Layers: https://docs.unity3d.com/Manual/2DSorting.html
