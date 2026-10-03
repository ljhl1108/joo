# 사운드 확인 가이드

> 2026-10-04 1차 적용 (유니티 `d6b193a`). 전부 **CC0 무료 에셋** — 상업 이용 가능, 출처 표기 의무 없음.
> 출처 기록: `Assets/Audio/LICENSE_AUDIO.txt`
> Claude는 소리를 들을 수 없어서 **파일 이름만 보고 골랐다** → 어색한 소리는 직접 듣고 골라내야 한다.

---

## 1. 확인 방법

- [ ] 플레이해서 아래 표를 보며 "이상한 소리" 체크 → Claude에게 **용도 이름**으로 알려주기
  (예: "Kick이 너무 둔탁해", "SeedShoot 시끄러워")
- [ ] 음량만 문제면 직접 고쳐도 된다: `Assets/Resources/Audio/SoundBank.asset` 선택 →
  Inspector의 해당 항목 `volume` (플레이 중 바꾸면 바로 반영, 단 플레이 중 값은 에셋에 남음)
- [ ] 소리 자체를 바꾸려면: `Assets/Audio/SFX/<용도>_0.ogg`, `_1.ogg`… 파일을 교체 →
  메뉴 **OnionCat > Audio > Rebuild Sound Bank**
- [ ] 전체·음악·효과음 음량은 게임 안 ESC → SETTINGS에서도 조절

## 2. 소리 목록 (용도 → 원본)

| 용도 | 언제 | 원본 (Kenney 팩) |
|---|---|---|
| ClawSwing | 할퀴기 휘두를 때 | RPG Audio — knifeSlice |
| Hit / HitHeavy | 적이 맞을 때 / 약점·마지막 일격 | Impact — punch medium / heavy |
| SeedHit | 씨앗이 적에 맞을 때 | Impact — generic light |
| SeedShoot | 양파 발사 | Interface — pluck |
| EnemyDeath | 적 사망 | Sci-Fi — slime |
| Blocked | 방패에 막힘 (BLOCK) | Impact — metal light |
| PlayerHurt | 고양이 피격 | Impact — plate medium |
| ShieldBlock / Parry | 실드로 막음 / 패링 | Impact — metal medium / bell heavy |
| Dash | 대쉬 | Digital — phaseJump |
| Kick / Crash | 걷어차기 / 날아간 적 충돌 | Impact — wood heavy / plank medium |
| Explosion / BigExplosion | 박·화상 폭발 / 합동기 | Sci-Fi — explosionCrunch / lowFrequency_explosion |
| TelegraphRed / TelegraphYellow | 적 공격 예고 (피해라 / 막을 수 있음) | Interface — error / question |
| EnemyShoot | 원거리 적 발사 | Sci-Fi — laserRetro |
| BossSlam / ShieldBreak | 보스 내려찍기 / 보스 방패 파괴 | Impact — plate heavy / glass heavy |
| Plant / SkillCast / Heal / Spore | 심기 / 산탄 / 회복 / 포자 | Interface drop / Digital phaserUp / powerUp / Sci-Fi forceField |
| HairballThrow / HairballReturn | 털뭉치 던지기 / 회수 | RPG cloth / Interface tick |
| Pickup / ItemUse | 아이템 줍기 / 사용 | Interface confirmation / Digital threeTone |
| Combo | 협동 콤보 | Interface — glass |
| JointReady / JointUltimate | 합동 게이지 가득 / 발동 | Digital — zapThreeToneUp / zapTwoTone |
| DoorOpen / RoomClear | 방 이동 / 방 클리어 | RPG doorOpen / Jingles NES00 |
| GameOver | 게임오버 | Digital — zapThreeToneDown |
| PuzzleSolved / PlatePress / CrystalLit | 쌍둥이 스위치 | Jingles PIZZI00 / RPG metalClick / Interface glass |
| UiMove / UiConfirm / UiBack | 메뉴 이동 / 확인 / 뒤로 | Interface — select / click / back |
| MenuOpen / MenuClose / RewardOpen | 일시정지 열기·닫기 / 보상 화면 | Interface — open / close / maximize |

**배경음악** (Juhani Junkala "5 Action Chiptunes", CC0)

| 곡 | 언제 |
|---|---|
| Music_Title | 메인 메뉴 |
| Music_Stage1 | 스테이지 (전투방) |
| Music_Boss | 보스방 |
| Music_Ending | 스테이지 완료 (1회) |
| Music_Stage1_B | 아직 안 씀 (스테이지 2 후보) |

## 3. 더 좋은 소리가 필요하면

- 무료(CC0): Kenney 다른 팩, OpenGameArt, freesound.org (라이선스 개별 확인)
- 유료: 에셋스토어 효과음 팩 — 사면 `Assets/Audio/SFX/` 규칙대로 파일만 넣고 Rebuild
