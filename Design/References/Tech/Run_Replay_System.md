# 런 리플레이 시스템 (Run Replay / Death Review)

리서치 날짜: 2026-08-21

## 개요

플레이어가 죽거나 런이 종료됐을 때 **마지막 N초의 플레이를 되돌아볼 수 있는 시스템**.
Hades의 "어떻게 죽었는지 확인" 화면, Spelunky의 리플레이, 격투게임의 리플레이에서 영감.
OnionCat에서는 협동 사망 장면을 두 플레이어가 같이 복기하며 웃고 배우는 경험 제공.
복잡한 전체 런 녹화 대신, **마지막 10~15초 스냅샷 기반** 간소화 구현을 권장.

---

## Unity 구현 방법

### 방법 1: 입력 로그 기반 리플레이 (Input Recording)

가장 정교하지만 구현 난이도 높음. 결정론적(deterministic) 게임에만 적합.

```csharp
[System.Serializable]
public struct InputFrame
{
    public float time;
    public Vector2 move;
    public bool slashPressed;
    public bool dashPressed;
    public Vector2 aimDir;
    public bool firePressed;
    public bool shieldPressed;
}

public class InputRecorder : MonoBehaviour
{
    private List<InputFrame> _frames = new();
    private bool _isRecording;
    private float _maxDuration = 15f;

    public void StartRecording() => _isRecording = true;

    private void Update()
    {
        if (!_isRecording) return;

        _frames.Add(new InputFrame
        {
            time = Time.time,
            // 실제 입력 값 읽기 (New Input System)
            move = _catInput.Move.ReadValue<Vector2>(),
            slashPressed = _catInput.Slash.IsPressed(),
            // ... 등
        });

        // 최대 보관 시간 초과 시 오래된 것 제거
        float cutoff = Time.time - _maxDuration;
        _frames.RemoveAll(f => f.time < cutoff);
    }

    public List<InputFrame> GetRecentFrames() => new List<InputFrame>(_frames);
}
```

**단점**: 물리/랜덤 함수가 끼어들면 재현 불일치 발생. 초보 개발자에게 비권장.

---

### 방법 2: 오브젝트 상태 스냅샷 (State Snapshot, 권장)

매 프레임(또는 N프레임마다) 씬의 주요 오브젝트 위치/상태를 찍어두고 재생.
구현이 단순하고, 결정론 없어도 동작. OnionCat 수준에 최적.

```csharp
[System.Serializable]
public struct SceneSnapshot
{
    public float timestamp;
    public Vector2 catPos;
    public Vector2 onionAimDir;
    public List<EnemySnapshot> enemies;
    public List<ProjectileSnapshot> projectiles;
}

[System.Serializable]
public struct EnemySnapshot
{
    public int id;
    public Vector2 pos;
    public float hp;
}

public class ReplayRecorder : MonoBehaviour
{
    [SerializeField] private float _recordInterval = 0.1f;  // 10fps로 기록
    [SerializeField] private float _maxDuration = 15f;
    
    private Queue<SceneSnapshot> _snapshots = new();
    private float _nextRecord;

    private void Update()
    {
        if (Time.time < _nextRecord) return;
        _nextRecord = Time.time + _recordInterval;

        var snap = CaptureSnapshot();
        _snapshots.Enqueue(snap);

        // 최대 보관량 초과 시 앞에서 제거
        while (_snapshots.Count > 0 &&
               Time.time - _snapshots.Peek().timestamp > _maxDuration)
        {
            _snapshots.Dequeue();
        }
    }

    private SceneSnapshot CaptureSnapshot()
    {
        return new SceneSnapshot
        {
            timestamp = Time.time,
            catPos = _cat.transform.position,
            onionAimDir = _onion.AimDirection,
            enemies = GetEnemySnapshots(),
            projectiles = GetProjectileSnapshots()
        };
    }

    public SceneSnapshot[] GetSnapshotsForReplay() => _snapshots.ToArray();
}
```

### 리플레이 재생기

```csharp
public class ReplayPlayer : MonoBehaviour
{
    [SerializeField] private Transform _catGhost;     // 반투명 고양이 스프라이트
    [SerializeField] private Transform _onionGhost;

    public IEnumerator PlayReplay(SceneSnapshot[] snapshots, float speedMultiplier = 1f)
    {
        // 일반 게임플레이 일시정지
        Time.timeScale = 0f;

        for (int i = 0; i < snapshots.Length - 1; i++)
        {
            var current = snapshots[i];
            var next = snapshots[i + 1];
            float duration = (next.timestamp - current.timestamp) / speedMultiplier;

            float elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.unscaledDeltaTime;
                float t = elapsed / duration;

                // 위치 보간으로 부드러운 재생
                _catGhost.position = Vector2.Lerp(current.catPos, next.catPos, t);
                // 적, 투사체도 마찬가지로 보간

                yield return null;
            }
        }

        Time.timeScale = 1f;
        // 리플레이 종료 → 게임오버 UI 표시
    }
}
```

### 게임오버 화면 연동

```csharp
public class DeathReviewController : MonoBehaviour
{
    private ReplayRecorder _recorder;
    private ReplayPlayer _player;

    public void OnPlayerDeath()
    {
        var snapshots = _recorder.GetSnapshotsForReplay();
        
        // "마지막 10초 다시보기" 버튼을 게임오버 UI에 추가
        _gameOverUI.ShowWithReplayButton(
            onReplayPressed: () => StartCoroutine(_player.PlayReplay(snapshots, 0.5f))
        );
    }
}
```

---

## OnionCat 적용 포인트

### 협동 사망 리뷰
- 게임오버 화면에 "마지막 10초 다시보기" 버튼 추가
- 반투명(ghost) 스프라이트로 Cat과 Onion의 마지막 움직임 재현
- 두 플레이어가 "내가 이렇게 했었구나!" 복기 → 웃음 유발 및 학습

### 구현 우선순위 (초보 개발자 로드맵)
1. **Step 1**: ReplayRecorder 추가 → 스냅샷만 쌓기 (메모리 확인)
2. **Step 2**: 게임오버 시 스냅샷 배열 저장
3. **Step 3**: 반투명 고양이/어니언 ghost 오브젝트 생성
4. **Step 4**: ReplayPlayer로 위치 보간 재생
5. **Step 5**: 재생 속도 조절(0.5x, 1x, 2x) UI 버튼 추가

### 주의할 점
- 스냅샷 간격 0.1초(10fps) × 15초 = 150 개 구조체 → 메모리 부담 낮음
- 파티클 이펙트, 사운드는 리플레이에서 생략해도 됨 (시각적 위치만 재현)
- 물리 충돌 재현은 필요 없음 → ghost는 그냥 위치 이동만
- 온라인 공유 기능은 2차 목표 (로컬 관람만으로도 충분)

### 확장 아이디어
- "사망 하이라이트" 자동 감지: 마지막 3초에 가장 데미지 많이 받은 순간 강조
- 쿨러 연출: 사망 순간 slow-motion 재생 (Time.timeScale = 0.3f)
- 런 통계와 연동: 몇 번째 루프에서 죽었는지, 처치한 적 수 등 함께 표시

---

## 참고 링크

- Unity 공식 Time.timeScale: https://docs.unity3d.com/ScriptReference/Time-timeScale.html
- 상태 기반 리플레이 구현 패턴: https://gamedevelopment.tutsplus.com/tutorials/how-to-build-a-replay-system-in-unity--cms-29661
- 격투게임 리플레이 시스템 설계 (GDC): GGPO Rollback Networking (참고 개념)
- Hades 사망 리뷰 UX 분석: 사망 화면에서 "어떻게 죽었는지" 텍스트로만 보여주는 간소화 버전도 유효
