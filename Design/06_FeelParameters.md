# 조절 수치 목록

게임에서 **사람이 만져 볼 만한 수치를 전부 한곳에** 모은 목록 — "어디서(어느 asset·컴포넌트·코드) 고치는지 + 지금 값 + 의미".
1~9장 = 감각(얼마나 시원한가·잘 보이는가), 10장~ = 시스템·밸런스(얼마나 센가·얼마나 자주 나오나).
**완성 후에도 주기적으로 이 목록을 따라가며 한 번씩 점검**하는 용도. 새 조절 수치가 생기면 Claude가 여기에 한 줄 추가한다.

### 위치 표시

| 표시 | 뜻 | 고치는 법 |
|---|---|---|
| ⚡ | 에셋 (`.asset`) | 유니티 Project 창에서 에셋 선택 → Inspector. **플레이 중에 바꿔도 유지됨** |
| 🧩 | 씬·프리팹 컴포넌트 | Hierarchy·프리팹 선택 → Inspector. 플레이 중에 바꾼 값은 Play를 끄면 사라짐 |
| 🛠 | 코드·표 | Claude에게 요청 (코드 표를 고치고 빌드 메뉴를 다시 돌려야 함) |
| 📊 | 공용 CSV (`Design/Data`) | 엑셀에서 고치면 Claude가 코드·에셋에 반영 |

> 값은 2026-10-23 기준 **실제 저장된 값** (코드 기본값이 아니라 에셋·씬에 들어 있는 값). 밸런스는 아직 임시.

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
| Combo Window / Multiplier | 1초 / 1.5 | 협동 콤보 제한 시간·배율 |
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
| Lunge Speed / Duration | 14 / 0.4초 | 슬라임 돌진. **걸어올 때(2)와 확실히 차이 나야 '온다'가 읽힘** |
| Lunge Cooldown | 1.2초 | 다음 돌진까지 |
| Min Lunge Distance | 2.5 | 이보다 가까우면 물러나서 거리부터 만듦 (코앞 돌진 방지) |
| Windup Pullback | 1.5 | 예고 중 뒤로 빼는 속도 (활시위 효과) |
| Attack Range (Slime) | 4.5 | 돌진을 시작하는 거리 |
| Fire Interval | 1.4초 | 원거리 슬라임 발사 간격 (RangedEnemy) |
| Turn Speed | 110°/s | 방패 근위병 회전 속도. **느릴수록 뒤를 잡기 쉬움 → 난이도 조절 후보** |
| Bash Speed / Duration / Cooldown | 10 / 0.35 / 2초 | 방패 근위병 밀치기 |
| Front / Back Multiplier | 0 / 2 | 방패 근위병 정면 차단·등 약점 배율 |
| Split Count / Child Health / Child Scale | 2 / 3 / 0.65 | 분열 슬라임 |
| **보스** Charge Telegraph / Speed / Duration | 0.7초 / 16 / 0.55초 | 돌진 |
| **보스** Exhausted Time | 1.3초 | 돌진 후 무방비 — **이 값이 보스 난이도의 핵심** |
| **보스** Slam Telegraph / Radius / Damage | 0.6초 / 2.8 / 20 | 내려찍기 |
| **보스** Pattern Interval | 1.2초 (2페이즈 0.6) | 패턴 사이 간격 |
| **보스** Phase 2 Threshold | 0.5 | 방패가 부서지는 체력 비율 |

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
| Dash Force / Duration | Dash_Default | 20 / 0.2초 | 대쉬 거리·시간 |
| Max Charges / Recharge Time / Min Interval | Dash_Default | 2 / 0.9초 / 0.12초 | 충전식 대쉬 칸 수·1칸 충전 시간·연속 대쉬 최소 간격 |
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
| Reward Delay | DungeonManager | 0.6초 | 방 클리어 후 보상 카드가 뜨기까지 |
| Victory Delay | DungeonManager | 1.0초 | 마지막 방 클리어 후 Stage Clear까지 |
| Fade Delay / Fade Duration | GameOverManager | 0.8 / 0.6초 | 사망 후 게임오버 화면 |
| Hover Scale | UpgradeCardView | 1.06 | 카드 위에 커서가 있을 때 커지는 정도 |

---

## 앞으로 이 목록에 추가될 것

- 파티클 양 (히트 이펙트, 사망 이펙트)
- 역할별 난이도 옵션에서 조절할 항목 (위 표의 **굵은 항목**들이 후보)
- 사운드 음량·음높이·연타 간격은 `Assets/Resources/Audio/SoundBank.asset` (확인 가이드 `Guides/sound_check.md`)

---

## 10. 코어 시스템 — 테스트하며 조절할 값

| 항목 | 위치 | 기본값 | 의미 |
|---|---|---|---|
| ⏸ Cooldown / Range / Arc Angle | `Player_Cat` → CatKick | 4초 / 1.7 / 120° | 걷어차기 재사용·범위 — **걷어차기는 꺼 둠** (`GameFeatures.Kick`) |
| ⏸ Launch Speed / Duration | CatKick | 16 / 0.4초 | 걷어찬 적이 날아가는 세기 (넉백 저항만큼 감소) |
| ⏸ Impact Damage | CatKick | 3 | 날아간 적이 벽·적에 부딪힐 때 (CRASH) |
| Base Charges / Auto Aim Range | `Player_Cat` → CatThrow | 1 / 9 | 털뭉치 개수·자동 조준 거리 |
| Auto Return Time / Slow | `Prefabs/Core/Hairball` | 4초 / 0.6배 2초 | 털뭉치 자동 회수·둔화 |
| Combo / KickCombo / Parry / Teamwork Gain | `Player_Cat` → JointUltimate | 8 / 15 / 10 / 20 | 합동 게이지 충전량 (100이 가득) |
| **Press Window** | JointUltimate | 1.5초 | 두 사람이 합동기를 눌러야 하는 허용 시간 — 난이도 후보 |
| Duration / Pulse Damage | JointUltimate | 2초 / 3 | ONION STORM 위력 |
| Base Damage / Radius | `Prefabs/Plants/Plant_Bomb` | 4 / 1.6 | 박 폭발 (레벨당 +1 / +0.2) |
| Kick Combo Multiplier | Plant_Bomb | 1.5 | 걷어찬 적으로 터뜨렸을 때 보너스 |
| Radius / Slow Multiplier | `Prefabs/Plants/Plant_Spicy` | 1.8 / 0.5 | 매운 양파 범위·둔화 |
| Cooldown | `Data/Skills/*.asset` | 4~12초 | 스킬별 쿨다운 (레벨당 10% 감소) |
| Item Drop Chance | `Data/RewardTable.asset` | 0.6 | 방 클리어 시 아이템 드롭 확률 |
| Lit Duration | Room_02 → TwinSwitch → Crystal | 2.5초 | 쌍둥이 스위치 타이밍 여유 — 난이도 후보 |

---

## 11. 장비 (v4) — 테스트하며 조절할 값

| 항목 | 위치 | 기본값 | 의미 |
|---|---|---|---|
| Rarity Weights | `Data/RewardTable.asset` | 60 / 28 / 10 / 2 | 보상 카드에 일반·희귀·에픽·전설이 뽑힐 비중 |
| Stats (Per Level) / Max Level | `Data/Gear/Gear_*.asset` | 장비마다 (할퀴기 +1, 이동 +3% 등) / 5 (마법서 3) | 레벨마다 붙는 기본 능력치 |
| 분해 씨앗 | `GearItem.SeedValue` (코드) | 일반 5 · 희귀 10 · 에픽 20 · 전설 40 × 레벨 | 분해했을 때 받는 씨앗 |
| Passive Limit / Spellbook Slots | `Loadout` (코드) | 6 / 3 | 패시브 최대 개수·마법서 칸 |
| ⚡ Gear Drop Chance | `Data/RewardTable.asset` | 0.5 | 방 클리어 시 장비가 바닥에 떨어질 확률 |
| ⚡ Cards Per Role | RewardTable | 3 | 보상 화면에서 고양이·양파가 각자 보는 카드 수 |
| ⚡ Combat / Elite Clear Seeds | RewardTable | 5 / 15 | 전투방·엘리트방 클리어 씨앗 (보스 = 엘리트 ×2) |
| ⚡ Shop Prices | RewardTable | 15 / 30 / 60 / 120 | 상점 가격 (일반·희귀·에픽·전설) |
| ⚡ Reroll Base Cost / Step | RewardTable | 10 / +5 | 상점 새로고침 가격 (누를 때마다 오름) |
| ⚡ Shop Items Per Role | RewardTable | 3 | 상점 가판대 개수 (역할마다) |
| ⚡ Rest Heal | RewardTable | 40 | 휴식 정원 샘물 회복량 |
| 🛠 Max Loot Per Room | `DungeonManager` (코드) | 3 | 한 방에 떨어지는 장비 최대 개수 |

---

## 12. 한 판 흐름 · 지도 (`Design/08_RunFlow.md`)

| 항목 | 위치 | 지금 값 | 의미 |
|---|---|---|---|
| 🧩 Health Per Stage | GameScene → `DungeonManager` | 1.35 | 스테이지마다 적 체력 배율 (2스테이지 ×1.35, 3스테이지 ×1.82). 보스는 제외 |
| 🛠 스테이지마다 위험도 + | `DungeonManager.BeginStage` (코드) | +1 / 스테이지 | 뒤 스테이지일수록 위험한 적·조합이 나옴 |
| 🛠 스테이지 수 | `MetaProgress.StageCount` (코드) | 3 (해금마다 +1, 최대 5) | 한 판 길이 |
| 🛠 층 수 / 길 수 / 칸 수 | `RunMap.cs` 상수 | 갈림길 5층 + 휴식 + 보스 / 3갈래 / 4칸 | 지도 모양 |
| ⚡ 방 종류 확률 | `Resources/RunTuning.asset` → 지도 | 물음표 0.14 · 보물 0.13 · 상점 0.13 · 엘리트 0.12 (3층~) · 휴식 0.10 (3~4층) · 나머지 전투 | 2~5층 칸이 무엇이 될지 (1층은 전투만). 다음 스테이지 지도부터 반영 |
| 🛠 층별 난이도 | `RunMap.TierFor` | 1~2층 = 1 · 3~4층 = 2 · 5층~ = 3 | 방 난이도 → 나오는 적 위험도 상한 |
| ⚡ Vote Wait | RunTuning → 고르기 | 5초 | 한 명만 골랐을 때 기다리는 시간 (둘이 같으면 바로) |
| 🧩 Fade / Reward / Victory Delay | GameScene → `DungeonManager` | 0.4 / 0.6 / 1.0초 | 9장과 같음 |

## 13. 적 구성 · 체력 (`Design/02_Enemies.md` 1-1)

| 항목 | 위치 | 지금 값 | 의미 |
|---|---|---|---|
| ⚡ Squad Chance | `Resources/EnemyRoster.asset` → 조합 | 0.7 | 전투방이 **조합**(서로 돕는 묶음)으로 나올 확률. 아니면 자리마다 무작위 |
| ⚡ Stage Weight | EnemyRoster | 2 | 지금 스테이지 전용 적·조합의 뽑힘 비중 (공통 = 1) |
| ⚡ Replace Chance | EnemyRoster | 0.6 | 무작위일 때 방의 적 자리 하나를 스테이지 적·공통 적으로 바꿀 확률 |
| 🛠 조합 목록 | `Editor/EnemyBuilder.cs` `BuildSquads` → 메뉴 **OnionCat > Enemies > Build Enemies** | 14개 | 구성 적·힌트·스테이지·위험도. Inspector에서 고치면 다음 빌드에 덮어써짐 |
| 🛠 체력 배율 | `EnemyBuilder.HpScale` / `HpScaleHelper` / `HpScaleBoss` | ×5 / ×3 / ×3 | 표의 hp(예전 눈금)에 곱해서 프리팹에 넣음 — 처치 시간 기준선 |
| 📊 적마다 체력·속도 | `Design/Data/enemies.csv` | 슬라임 30 · 방패병 60 · 보스 360~600 | 게임 안 최종값. 고치면 Claude가 표에 반영 |
| ⚡ Elite Health / Scale | RunTuning → 엘리트 | ×2 / ×1.2 (금빛) | 엘리트방·매복 적 |
| 🛠 적 크기 등급 | `EnemyBuilder.SizeOf` | 작음 0.5 · 보통 0.6 · 큼 0.75 · 보스 1.1 | 4등급만 |

## 14. 물음표 방 — ⚡ `Assets/Resources/RunTuning.asset` (`Design/08_RunFlow.md` 2장)

숫자를 바꾸면 **선택지 설명 문구도 같이 바뀐다** (다음 물음표 방부터). 이벤트의 동작 자체(무엇을 하는지)는 코드 `RunEvents.cs`.

| 항목 (Inspector 머리글) | 지금 값 | 의미 |
|---|---|---|
| 방 N개 동안 효과 — 세기 | 최대 체력 ×0.7 · 받는 피해 ×2 · 주는 피해 ×2 · 적 체력 ×0.5 · 방마다 체력 -8 · 보스 체력 ×1.5 | 효과의 강도 (모든 이벤트 공통) |
| 매복 | 3마리 · 위험도 = 스테이지 + 2 | 도박꾼의 상자·영웅의 짐에서 지면 |
| 악마의 계약 | 전설 / 3방 | 보상 등급 / 최대 체력 감소가 이어지는 방 수 |
| 저주받은 왕관 | 4방 | 주는·받는 피해 증가가 이어지는 방 수 |
| 도박꾼의 상자 | 0.5 / 전설 / 매복 이기면 에픽 | 성공 확률 / 성공 보상 / 매복 보상 |
| 피의 제단 | 지금 체력 0.5 / 씨앗 60 / 에픽 | 체력 대가(비율) / 씨앗 대가 / 보상 |
| 시간의 모래시계 | 3방 | 적 체력 감소·대쉬 봉인이 이어지는 방 수 |
| 영웅의 유물 | 파편 3 | 기억 파편 (대신 이번 스테이지 보스 체력 증가) |
| 금지된 씨앗 | 전설 / 4방 | 보상 / 방마다 체력 감소가 이어지는 방 수 |
| 영웅의 짐 꾸러미 | 0.5 / 씨앗 80 / 매복 이기면 희귀 | 성공 확률 / 씨앗 / 매복 보상 |
| 도박하는 거북 | 최소 20 / 0.34 / ×3 | 걸 수 있는 최소 씨앗 / 이길 확률 / 배수 |
| 기억의 꽃 | 파편 2 / 2방 | 기억 파편 / 받는 피해 증가가 이어지는 방 수 |

## 14.5 온실 (`Design/07_StoryMeta.md` 2장)

| 항목 | 위치 | 지금 값 | 의미 |
|---|---|---|---|
| 📊 해금 가격 | `Design/Data/items.csv` `해금` 열 = 🛠 `Editor/GreenhouseBuilder.cs` → 메뉴 **OnionCat > Content > Apply Greenhouse Unlock Costs** | 에픽 12개 × 파편 2 · 전설 2개 × 파편 4 | 빈칸 = 처음부터 보상에 나옴. 장비 에셋의 Unlock Cost 칸에 들어감 (Inspector에서 고쳐도 되지만 다음 빌드 때 표 값으로 돌아감) |
| 🛠 기억 파편 얻는 양 | `MetaProgress.OnBossDefeated` · RunTuning(유물 3 · 꽃 2) | 보스 +1 | 한 판에 3~6개 |

## 15. 고양이 특수 공격 · 야성 게이지 (`Design/01_Characters.md` 0-1)

| 항목 | 위치 | 지금 값 | 의미 |
|---|---|---|---|
| 🧩 Wild Per Hit | GameScene → `Player_Cat` → MeleeAttack_Slash | 8 | 할퀴기가 맞을 때 게이지 (가득 = 100) |
| 🧩 Back Hit Wild Multiplier | MeleeAttack_Slash | 2 | 등을 쳤을 때 배율 (발톱 고양이 "사냥 본능") |
| 🧩 Cost | `Player_Cat` → CatSpecial | 100 | 특수 공격에 드는 게이지 |
| 🛠 무기별 특수 공격 | `CatSpecial.cs` | 난무 8연타 · 회오리 3초 · 덮치기 · 찢어발기기 X자 2번 · 광란 6초 (공속 ×2, 이동 ×1.3) | 무기마다 다른 특수 공격 |
