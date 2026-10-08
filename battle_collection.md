# Pokémon Showdown Battle Collection

## Session

- Battle: `[Gen 9] Random Battle`
- Format ID: `gen9randombattle`
- Battle URL: `https://play.pokemonshowdown.com/battle-gen9randombattle-2695027145`
- Players: `zismanshd` vs. `kerbeus069`
- Teams: 6 vs. 6
- Battle status: one existing battle inspected; no second battle started
- Credentials: not stored in this report

## Timer

Yes. The battle timer was active.

Exact raw line:

```text
|inactive|Battle timer is ON: inactive players will automatically lose when time's up. (requested by zismanshd)
```

The browser also displayed the timer control with a countdown, including `2:24`, `2:20`, `2:16`, and `1:55` during inspection. The timer later displayed `-:--` after the battle state was reloaded, so the captured state should be treated as a historical snapshot rather than a live timer reading.

## My team

The team data came from the `|request|` JSON:

| Pokémon | Level/gender | Types | Item | Ability | Moves | Stats | HP | Tera |
|---|---|---|---|---|---|---|---|---|
| Sableye | 87, male | Dark/Ghost | Unknown after Knock Off | Prankster | Encore 7/8, Will-O-Wisp 23/24, Recover 8/8, Knock Off 31/32 | Atk 180, Def 180, SpA 163, SpD 163, Spe 137 | 124/229 | Available: Poison |
| Wo-Chien | 83, gender unknown | Dark/Grass | Leftovers | Tablets of Ruin | Protect, Leech Seed, Ruination, Knock Off; PP unknown | Atk 189, Def 214, SpA 205, SpD 272, Spe 164 | 277/277 | Poison |
| Toxtricity | 82, female | Electric/Poison | Throat Spray | Punk Rock | Shift Gear, Gunk Shot, Boomburst, Overdrive; PP unknown | Atk 208, Def 162, SpA 234, SpD 162, Spe 170 | 257/257 | Normal |
| Fezandipiti | 82, male | Poison/Fairy | Leftovers | Toxic Chain | Swords Dance, Tera Blast, Gunk Shot, Play Rough; PP unknown | Atk 196, Def 182, SpA 162, SpD 252, Spe 210 | 278/278 | Ground |
| Cramorant | 86, male | Water/Flying | Heavy-Duty Boots | Gulp Missile | Brave Bird, Surf, Defog, Roost; PP unknown | Atk 195, Def 144, SpA 195, SpD 213, Spe 195 | 261/261 | Ground |
| Medicham | 86, female | Fighting/Psychic | Choice Band | Pure Power | Ice Punch, Close Combat, Zen Headbutt, Bullet Punch; PP unknown | Atk 152, Def 178, SpA 152, SpD 178, Spe 187 | 243/243 | Fighting |

## Opponent

| Pokémon | Level/gender | HP | Revealed moves | Item | Ability | Tera | Unseen opponent Pokémon |
|---|---|---|---|---|---|---|---|
| Meowstic-M | 89, male | 100% | Reflect, Yawn | Unknown | Unknown | Unknown | 4 |
| Skuntank | 84, male | 92% | Knock Off | Life Orb, revealed when Knock Off removed it | Unknown | Unknown | 4 |

Opponent Terastallization was not observed: Unknown.

## Requested event coverage

These items were **not present in the saved capture** and were not generated deliberately:

| Event | Status | Evidence |
|---|---|---|
| Terastallization by either side | UNKNOWN | No `|terastallize|` line was captured. The request only showed that my side could Terastallize into Poison. |
| Pokémon fainting | UNKNOWN / NOT OBSERVED | No `|faint|` line was captured. |
| Forced-switch request | UNKNOWN / NOT OBSERVED | No forced-switch `|request|` was captured. The saved request was a normal move request. |
| Ability activating | UNKNOWN / NOT OBSERVED | No ability activation line such as `|-ability|` was captured. Abilities in the request describe team state, not an observed activation event. |
| Weather activating | UNKNOWN / NOT OBSERVED | No weather activation line such as `|-weather|` was captured. |
| Battle ending | UNKNOWN / NOT OBSERVED | No `|win|`, `|tie|`, or equivalent battle-end line was captured. |

## Control-action test status

The following actions were **not tested** in the last inspection. No live move, switch, Tera action, or chat command was intentionally submitted:

| Action | Result |
|---|---|
| Clicking a move button | UNKNOWN / NOT TESTED |
| Clicking a switch button | UNKNOWN / NOT TESTED |
| Ticking Terastallize and clicking a move | UNKNOWN / NOT TESTED |
| Typing `/choose move 1` in chat | UNKNOWN / NOT TESTED |

The previous inspection only read the rendered controls, inspected the in-page battle state, and captured WebSocket frames. Testing these actions would submit choices to a live battle and therefore requires a separately authorized controlled test.

## Second battle observation

The second battle was observed passively after play was already underway. No controls were clicked by the observer. Exact observed events are saved in [current_battle_observation.txt](./current_battle_observation.txt).

Confirmed from the rendered log:

```text
(Hypno has Terastallized into the Fairy-type!)
The opposing Piloswine fainted!
Drednaw fainted!
(The opposing Landorus has Terastallized into the Ground-type!)
```

At the latest observation, it was Turn 10, the timer showed about `2:04`, Gurdurr was at 79%, Landorus-Therian was at 64% and Tera Ground, Drednaw had fainted, and Piloswine had fainted. This second observation is rendered-log text, not a raw WebSocket capture, because the connection was already open before passive observation began.

## Raw protocol highlights

```text
|teamsize|p1|6
|teamsize|p2|6
|switch|p1a: Meowstic|Meowstic, L89, M|100/100
|switch|p2a: Fezandipiti|Fezandipiti, L82, M|100/100
|switch|p2a: Sableye|Sableye, L87, M|100/100
|move|p1a: Meowstic|Reflect|p1a: Meowstic
|move|p1a: Meowstic|Yawn|p2a: Sableye
|move|p2a: Sableye|Encore|p1a: Meowstic
|switch|p1a: Skuntank|Skuntank, L84, M|100/100
|move|p2a: Sableye|Knock Off|p1a: Skuntank
|-damage|p1a: Skuntank|92/100
|-enditem|p1a: Skuntank|Life Orb|[from] move: Knock Off|[of] p2a: Sableye
|move|p2a: Sableye|Will-O-Wisp|p1a: Skuntank
|move|p1a: Skuntank|Knock Off|p2a: Sableye
|-damage|p2a: Sableye|55/100
|-enditem|p2a: Sableye|Leftovers|[from] move: Knock Off|[of] p1a: Skuntank
```

The complete raw capture, including the full `|request|` JSON, is in [battle_log.txt](./battle_log.txt).

## UI and automation selectors

The complete selector map is in [selectors.json](./selectors.json). The most stable observed selectors were:

```text
button[name="login"]
input[name="username"]
input[type="password"]
button[name="search"]
button[name="chooseMove"]
button[name="chooseSwitch"]
input[name="terastallize"]
textarea[name="chat"]
button[name="closeRoom"]
```

Text and CSS backups are preserved in `selectors.json`.

## Log viewing and export

1. Click **Chat** in the battle room to display the in-room battle log and chat input.
2. Open developer tools with **F12**.
3. In **Network**, filter by **WS**, select the Showdown WebSocket, and inspect **Messages/Frames**.
4. Look for `|request|`, `|switch|`, `|move|`, `|-damage|`, `|-item|`, and `|-ability|`.
5. Open **Battle Options** and choose **Save replay**, **Upload replay**, or **Share replay** when available.
6. Replays preserve the rendered battle log; raw WebSocket frames must be captured separately.

## Limitations

- No second battle was started.
- No move was intentionally submitted during inspection.
- The integrated browser did not expose a separate F12 developer-tools window, so WebSocket frames were captured with an in-page listener during reload.
- Reserve Pokémon PP was not available in the captured request.
- Hidden opponent Pokémon, items, abilities, and Tera types remain unknown unless revealed.
- `/choose move 1` was not tested because testing it could submit a battle choice.
