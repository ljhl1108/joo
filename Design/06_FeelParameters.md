# 감각 조절 파라미터 목록

게임이 "어떻게 느껴지는지"를 결정하는 수치를 한곳에 모은 목록.
**완성 후에도 주기적으로 이 목록을 따라가며 한 번씩 점검**하는 용도.

> 밸런스 수치(체력·데미지 같은 "얼마나 센가")는 여기가 아니라 `TODO.md` M4 밸런스 항목에서 다룬다.
> 여기는 "얼마나 시원한가 / 잘 보이는가"를 다룬다.

---

## 점검 방법

1. 유니티 Play 실행 → 방 하나에서 적을 때리며 확인
2. **플레이 중에 Inspector 값을 바꾸면 바로 반영된다** (아래 ⚡ 표시 항목)
3. 마음에 드는 값을 찾으면 그대로 두고, 되돌리려면 `git diff`로 확인
4. ⚠️ 플레이 중 바꾼 **씬·컴포넌트** 값은 Play를 끄면 사라진다. ⚡(에셋)만 유지됨

---

## 1. 타격감 — ⚡ `Assets/Resources/HitFeelSettings.asset`

에셋 하나에 모여 있고 **플레이 중 수정이 그대로 저장**된다. 가장 먼저 만질 곳.

| 항목 | 기본값 | 범위 | 느낌 |
|---|---|---|---|
| Light / Medium / Heavy · Knockback Multiplier | 0.5 / 1.0 / 1.8 | 0~4 | 적이 밀려나는 거리 |
| Light / Medium / Heavy · Hit Stop Duration | 0.02 / 0.04 / 0.08초 | 0~0.3 | 맞은 적이 멈칫하는 시간. 길수록 묵직, 짧을수록 경쾌 |
| Light / Medium / Heavy · Shake Amplitude | 0 / 0.06 / 0.14 | 0~0.5 | 화면 흔들림 크기 |
| Shake Duration | 0.12초 | 0~0.5 | 흔들림이 잦아드는 시간 |
| Freeze Movement During Hit Stop | 꺼짐 | on/off | **켜면** 제자리에 멈췄다 밀려남(묵직) / **끄면** 즉시 밀려남(경쾌) |

강도 구분: Light = 양파 투사체 / Medium = 고양이 할퀴기 / Heavy = 약점 공격·마지막 일격

**점검 포인트**: 때린 즉시 밀려나는가, 여러 마리를 연속으로 때릴 때 답답하지 않은가,
양파 연사 중 화면이 계속 흔들려 어지럽지 않은가.

---

## 2. 적 반응 — 적 프리팹 (`Assets/Prefabs/Slime.prefab`, `RangeSlime.prefab`)

| 항목 | 위치 | 기본값 | 느낌 |
|---|---|---|---|
| Knockback Force | EnemyBase | 5 | 넉백 기준 세기 (위 배율이 여기에 곱해짐) |
| Knockback Resistance | EnemyBase | 0 | 1이면 안 밀림. 보스·방패병용 |
| Hit Stun Duration | EnemyBase | 0.3초 | 맞고 나서 다시 움직이기까지 |
| Death Duration | EnemyBase | 0.25초 | 죽을 때 작아지며 사라지는 시간 |

**점검 포인트**: 적이 밀려난 뒤 너무 빨리/늦게 달려드는가, 죽는 연출이 질질 끌지 않는가.

---

## 3. 데미지 숫자 — 씬의 `DamageNumbers` + `Assets/Prefabs/DamageNumber.prefab`

| 항목 | 위치 | 기본값 | 느낌 |
|---|---|---|---|
| Offset | DamageNumberSpawner | (0, 0.5) | 숫자가 뜨는 높이 |
| 색상 5종 | DamageNumberSpawner | 흰/주황/하늘/회색/빨강 | 보통·약점·저항·BLOCK·고양이 피격 |
| Weak Size / Resist Size | DamageNumberSpawner | 1.35 / 0.8 | 약점·저항 숫자 크기 |
| Lifetime | DamageNumber 프리팹 | 0.7초 | 숫자가 떠 있는 시간 |
| Rise Distance | DamageNumber 프리팹 | 0.8 | 떠오르는 높이 |
| Horizontal Jitter | DamageNumber 프리팹 | 0.25 | 연타 시 좌우로 흩어지는 정도 |
| Pop Scale / Pop Duration | DamageNumber 프리팹 | 1.5 / 0.08초 | 튀어나오는 연출 |
| Fade Start | DamageNumber 프리팹 | 0.6 | 언제부터 투명해지는지 |

**점검 포인트**: 연타할 때 숫자가 뭉쳐 안 읽히는가, 화면이 숫자로 지저분한가.

---

## 3.5 공격 예고 (텔레그래프) — 적 프리팹 `EnemyBase`

| 항목 | 기본값 | 느낌 |
|---|---|---|
| **Telegraph Duration** | 0.5초 | 예고 시간. 길수록 피하기 쉬움 → **난이도 조절 1순위 후보** |
| Blockable Color | 노랑 (1, 0.9, 0.2) | 막을 수 있는 공격 |
| Unblockable Color | 빨강 (1, 0.25, 0.2) | 피해야 하는 공격 |
| Telegraph Scale | 1.15 | 예고 중 부풀어 오르는 정도 |
| Lunge Speed / Duration / Cooldown | 9 / 0.25 / 1.4초 | 슬라임 돌진 (SlimeEnemy) |
| Fire Interval | 2초 | 원거리 슬라임 발사 간격 (RangedEnemy) |

**점검 포인트**: 예고를 보고 피할 시간이 실제로 있는가, 적이 여럿일 때 누가 공격하는지 구분되는가,
적 기본색과 경고색이 헷갈리지 않는가.

## 4. 화면 — Main Camera (`CameraController`)

| 항목 | 기본값 | 느낌 |
|---|---|---|
| Smooth Time | 0.15 | 카메라가 고양이를 따라가는 부드러움. 낮을수록 딱 붙음 |
| Max Speed | 50 | 따라가는 최대 속도 |
| **Shake Multiplier** | 1 | 전체 흔들림 배율. **멀미 옵션으로 연결 예정 (0 = 완전히 끔)** |

**점검 포인트**: 빠르게 움직일 때 화면이 멀미 나게 흔들리는가, 카메라가 늦게 따라와 답답한가.

---

## 5. 고양이 조작감 — `Player_Cat`

| 항목 | 위치 | 기본값 | 느낌 |
|---|---|---|---|
| Move Speed | CatController | 5 | 이동 속도 |
| Dash Force / Duration / Cooldown | Dash_Default | 20 / 0.2 / 0.5초 | 대쉬 거리·시간·재사용 |
| Cooldown / Attack Duration | MeleeAttack_Slash | 0.2 / 0.1초 | 할퀴기 연타 속도 |
| Range / Angle | MeleeAttack_Slash | 1.5 / 150° | 할퀴기 범위 (넉넉할수록 캐주얼) |
| Attack Slow Multiplier | MeleeAttack_Slash | 0.7 | 공격 중 이동 속도 |
| **Aim Assist Angle** | MeleeAttack_Slash | 90° | 가까운 적 쪽으로 방향 보정. 0이면 꺼짐 → **고양이 난이도 조절 후보** |
| Full Circle When Idle | MeleeAttack_Slash | 켜짐 | 멈춰 있을 때는 360° 전체에서 가장 가까운 적을 노림 |

**점검 포인트**: 적 옆에서 휘둘렀는데 빗나가는 일이 있는가, 보정이 과해서 엉뚱한 적을 때리는가.

---

## 6. 양파 조작감 — `CropHolder`

| 항목 | 위치 | 기본값 | 느낌 |
|---|---|---|---|
| Shoot Cooldown | OnionController | 0.1초 | 최소 발사 간격 |
| Prewarm Count | OnionController | 20 | 미리 만들어 둘 씨앗 수 (많을수록 첫 연사가 매끄러움) |
| Speed / Lifetime | Projectile 프리팹 | 10 / 3초 | 씨앗 속도·사거리 |
| Shield Duration / Parry Window / Cooldown | OnionShield | 0.5 / 0.25 / 3초 | 실드 지속·패링 판정·재사용 → **양파 난이도 조절 후보** |

---

## 7. 피격·생존감 — `PlayerHealth`

| 항목 | 기본값 | 느낌 |
|---|---|---|
| Hit Invincibility Duration | 1초 | 연속으로 맞지 않게 해주는 시간. 캐주얼 방향이면 넉넉하게 |
| Hit Shake Amplitude / Duration | 0.15 / 0.15초 | 맞았을 때 화면 흔들림 |
| Shield Recharge Delay / Time Per Point | 4 / 2초 | 실드가 다시 차기까지 |

---

## 8. HUD — 씬의 `HUD`

| 항목 | 위치 | 기본값 | 느낌 |
|---|---|---|---|
| Trail Delay / Trail Speed | HUDController | 0.4초 / 1.2 | 깎인 체력이 남아 있다 줄어드는 연출 |
| High / Mid / Low Color | HUDController | 초록/노랑/빨강 | 체력 구간별 색 |

---

## 9. 화면 전환 · 흐름

| 항목 | 위치 | 기본값 | 느낌 |
|---|---|---|---|
| Fade Duration | DungeonManager | 0.4초 | 방 이동 암전 |
| Reward Delay | DungeonManager | 0.6초 | 방 클리어 후 카드가 뜨기까지 |
| Victory Delay | DungeonManager | 1.0초 | 마지막 방 클리어 후 Stage Clear까지 |
| Fade Delay / Fade Duration | GameOverManager | 0.8 / 0.6초 | 사망 후 게임오버 화면 |
| Time Limit | UpgradeSelectUI | 30초 | 카드 선택 제한 시간 |
| Hover Scale | UpgradeCardView | 1.06 | 카드 위에 커서가 있을 때 커지는 정도 |

---

## 앞으로 이 목록에 추가될 것

- 사운드 볼륨·타격음 (M3)
- 파티클 양 (히트 이펙트, 사망 이펙트)
- 적 텔레그래프 표시 시간 (공격 예고를 얼마나 일찍 보여줄지)
- 역할별 난이도 옵션에서 조절할 항목 (위 표의 **굵은 항목**들이 후보)
