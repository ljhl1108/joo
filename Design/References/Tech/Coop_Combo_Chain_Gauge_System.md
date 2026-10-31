# 협동 콤보 체인 & 합동 게이지 시스템

리서치 날짜: 2026-10-31

## 개요

2인 비대칭 협력 게임에서 **두 플레이어가 번갈아 같은 적을 공격할 때 보너스를 주는 시스템**과, 이 시스템이 쌓아가는 **합동 궁극기 게이지**의 구현 방법.

OnionCat에서의 역할:
- "고양이↔양파가 1초 안에 번갈아 같은 적을 때리면 ×1.5, 금색 COMBO!" 표시
- 합동 게이지(콤보 +8 / 패링 +10 / 킥콤보 +15 / 2인 기믹 +20)
- 게이지가 차면 둘이 각자 버튼을 1.5초 안에 누르면 합동기 발동

---

## Unity 구현 방법

### 1. 데이터 구조

```csharp
// CombatEnums.cs (이미 존재)
public enum Attacker { Cat, Onion }

// CoopComboTracker.cs — 한 적당 마지막 공격 기록
[System.Serializable]
public class EnemyComboState {
    public Attacker lastAttacker;
    public float lastHitTime;
    public const float ComboWindow = 1f; // 1초 안에 교대

    public bool IsCombo(Attacker newAttacker) =>
        newAttacker != lastAttacker &&
        Time.time - lastHitTime <= ComboWindow;
}
```

### 2. 콤보 감지 (EnemyBase 통합)

```csharp
// EnemyBase.Status.cs의 TakeDamage 내부 (기존 코드에 통합)
// TakeDamage(..., Attacker attacker) 호출 시

void ProcessCoopCombo(int damage, Attacker attacker) {
    bool isCombo = _comboState.IsCombo(attacker);
    
    if (isCombo) {
        damage = Mathf.RoundToInt(damage * 1.5f);
        CoopComboManager.Instance.OnComboHit(this, attacker);
        // "COMBO!" 팝업 & 사운드
        FloatingText.Show(transform.position, "COMBO!", Color.yellow);
        Sfx.Play(SfxId.CoopCombo);
    }
    
    _comboState.lastAttacker = attacker;
    _comboState.lastHitTime = Time.time;
    
    return damage; // 수정된 피해량
}
```

### 3. 합동 게이지 시스템

```csharp
// JointGaugeManager.cs (싱글턴, 씬 유지)
public class JointGaugeManager : MonoBehaviour {
    public static JointGaugeManager Instance { get; private set; }
    
    [SerializeField] private float maxGauge = 100f;
    private float _gauge = 0f;
    
    // 게이지 기여량 상수
    private const float GaugePerCombo    = 8f;
    private const float GaugePerParry    = 10f;
    private const float GaugePerKickCombo = 15f;
    private const float GaugePerCoop2P   = 20f;
    
    // 게이지가 차면 발동 대기 상태
    private bool _awaitingCat  = false;
    private bool _awaitingOnion = false;
    private float _activationWindow = 1.5f;
    private float _activationTimer  = 0f;
    
    public void AddGauge(float amount) {
        _gauge = Mathf.Min(_gauge + amount, maxGauge);
        HUD.Instance.UpdateJointGauge(_gauge / maxGauge);
        
        if (_gauge >= maxGauge) {
            // 게이지 만땅 → 발동 대기 UI 켜기
            _awaitingCat = _awaitingOnion = false;
            HUD.Instance.ShowJointReady(true);
        }
    }
    
    // 각 플레이어가 합동기 버튼을 누를 때 호출
    public void RequestJoint(Attacker who) {
        if (_gauge < maxGauge) return;
        
        if (who == Attacker.Cat)   _awaitingCat   = true;
        if (who == Attacker.Onion) _awaitingOnion = true;
        
        if (!(_awaitingCat && _awaitingOnion)) {
            _activationTimer = _activationWindow; // 카운트다운 시작
            return;
        }
        
        // 둘 다 눌렀을 때
        TriggerJointUltimate();
    }
    
    private void Update() {
        if ((_awaitingCat || _awaitingOnion) && _gauge >= maxGauge) {
            _activationTimer -= Time.deltaTime;
            if (_activationTimer <= 0f) {
                // 타임아웃 — 입력 초기화 (게이지는 유지)
                _awaitingCat = _awaitingOnion = false;
                HUD.Instance.ShowJointActivationTimeout();
            }
        }
    }
    
    private void TriggerJointUltimate() {
        _gauge = 0f;
        _awaitingCat = _awaitingOnion = false;
        HUD.Instance.ShowJointReady(false);
        HUD.Instance.UpdateJointGauge(0f);
        
        // 실제 합동기 발동
        JointUltimateSkill.Instance.Execute();
        Sfx.Play(SfxId.JointUltimate);
    }
}
```

### 4. 게이지 기여 이벤트 연결

```csharp
// CoopComboManager.cs (이미 있거나 새로 추가)
public class CoopComboManager : MonoBehaviour {
    public static CoopComboManager Instance { get; private set; }
    
    public void OnComboHit(EnemyBase enemy, Attacker attacker) {
        JointGaugeManager.Instance.AddGauge(
            JointGaugeManager.GaugePerCombo);
    }
    
    public void OnParry() {
        JointGaugeManager.Instance.AddGauge(
            JointGaugeManager.GaugePerParry);
    }
    
    public void OnKickCombo() { // 킥 봉인 중 사용 안 함 (GameFeatures.Kick)
        JointGaugeManager.Instance.AddGauge(
            JointGaugeManager.GaugePerKickCombo);
    }
    
    public void OnTwoPlayerMechanic() {
        JointGaugeManager.Instance.AddGauge(
            JointGaugeManager.GaugePerCoop2P);
    }
}
```

### 5. 콤보 HUD 요소

```csharp
// JointGaugeHUD.cs — HUD의 합동 게이지 바 담당
public class JointGaugeHUD : MonoBehaviour {
    [SerializeField] private Image gaugeFill;
    [SerializeField] private Image gaugeBackground;
    [SerializeField] private GameObject readyFlash;  // "합동기 준비!" 반짝임
    [SerializeField] private Animator pulseAnim;
    
    public void UpdateGauge(float normalized) {
        gaugeFill.fillAmount = normalized;
        // 80% 이상이면 게이지 색 변경 (흰 → 황금)
        gaugeFill.color = normalized >= 0.8f ? Color.yellow : Color.white;
    }
    
    public void ShowReady(bool ready) {
        readyFlash.SetActive(ready);
        if (ready) pulseAnim.SetTrigger("Pulse");
    }
}
```

### 6. COMBO! 팝업 텍스트

```csharp
// FloatingComboBanner.cs — 콤보 발생 시 화면 상단에 배너
public class FloatingComboBanner : MonoBehaviour {
    [SerializeField] private TMP_Text label;  // Galmuri11
    [SerializeField] private float displayTime = 0.8f;
    
    private Coroutine _show;
    
    public void Show(string text) {
        if (_show != null) StopCoroutine(_show);
        _show = StartCoroutine(ShowRoutine(text));
    }
    
    private IEnumerator ShowRoutine(string text) {
        label.text = text;
        label.gameObject.SetActive(true);
        yield return new WaitForSecondsRealtime(displayTime);
        label.gameObject.SetActive(false);
    }
}
```

---

## OnionCat 적용 포인트

### 현재 구현 상태 (00_Implemented.md 기준)
```
✅ 콤보 판정: Attacker.Cat / Onion → TakeDamage(..., Attacker)
✅ ×1.5 피해: 이미 적용됨
✅ 합동 게이지: 콤보·패링·킥콤보·2인기믹이 기여
✅ 합동기: ONION STORM 1종
```

### 주의할 설계 함정

**1. 시간 창 (ComboWindow)**
```
1초가 맞는지 플레이테스트 필요.
  - 너무 짧으면 (0.5초): 의도치 않게 콤보가 안 됨 → 실망감
  - 너무 길면 (3초): 번갈아 치기가 당연해져 전략성 없음
  - Hades 수준 (0.8~1.0초): "집중하면 맞출 수 있다" 밸런스
```

**2. 게이지 한쪽만 채우는 문제 방지**
```
// 한 플레이어가 혼자 때리면 게이지가 거의 안 참
// → 협력 유도 설계
if (lastAttacker == newAttacker) {
    gauge += GaugePerCombo * 0.1f;  // 10%만 채움
} else {
    gauge += GaugePerCombo;          // 100% 채움
}
```

**3. 합동기 발동 타이밍 표시**
```
한 명이 눌렀을 때:
  - 누른 쪽의 버튼 UI를 깜빡임
  - 상대방 UI에 "누르세요!" 표시
  - 1.5초 카운트다운 바를 좁혀가며 압박감 연출
```

**4. GameManager.IsGameplayActive 체크**
```csharp
// 업그레이드 선택·일시정지 중에는 합동기 버튼을 받지 않음
public void RequestJoint(Attacker who) {
    if (!GameManager.Instance.IsGameplayActive) return;
    // ...
}
```

**5. 방 전환 시 콤보 상태 초기화**
```csharp
// Room.ResetForReuse() 에서 호출
void OnRoomEnter() {
    // 모든 적의 _comboState 초기화됨 (새 방 = 새 적)
    // 합동 게이지는 유지 (RunData에 저장)
}
```

---

## 참고 링크

- Unity Coroutine Pattern: https://docs.unity3d.com/Manual/Coroutines.html
- TMP Color Tags: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.2/manual/RichText.html
- Hades Co-op (디스코드 인터뷰): https://www.gamedeveloper.com/design/hades-postmortem-supergiant
- Children of Morta 협동 시스템 설계: `Design/References/Game/Children_of_Morta.md`
