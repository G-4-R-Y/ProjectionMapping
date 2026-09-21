# Performance Director live controls

The Performance Director can be played from the projector window, MIDI hardware, or OSC while the
same musical conductor continues to react to the song. External controls do not create a second
sequencer: they feed the same `PerformanceDirector` state machine.

## Install controls

```bash
python -m pip install -e '.[ui,vision,audio,graphics,controls]'
```

The desktop bundles already include the control dependencies.

## Keyboard

With the projector window focused:

| Key | Action |
| --- | --- |
| `1` .. `8` | Trigger the eight hot cues in catalog order |
| `N` | Advance to the next cue in the active journey |
| `[` / `]` | Decrease / increase base MADNESS by 0.05 |
| `a` / `A` | Save / load snapshot A |
| `b` / `B` | Save / load snapshot B |
| `F11` | Toggle fullscreen |
| `Esc` | Exit the visual |

Hot-cue order:

1. `liquid_intro`
2. `membrane_drift`
3. `data_build`
4. `mercury_rise`
5. `cathedral_release`
6. `reactor_release`
7. `singularity_drop`
8. `afterglow`

## MIDI

Enable MIDI in `projection-ui` or launch with `--midi`.

Defaults:

- CC 1 -> continuous MADNESS 0..1
- notes 36..43 -> hot cues 1..8
- note 44 -> next journey cue
- note 45 -> save snapshot A
- note 46 -> load snapshot A
- note 47 -> save snapshot B
- note 48 -> load snapshot B
- MIDI Program Change -> select a journey by index

The CC and note base are configurable with `--midi-madness-cc` and `--midi-note-base`.
Use `--midi-device "substring"` to select a controller, or:

```bash
python experiments/33_performance_director.py --list-midi
```

## OSC

OSC is enabled by default on `127.0.0.1:9000`. Use `--osc-port 0` to disable it.

Addresses:

```text
/pm/madness <float 0..1>
/pm/cue <cue-name>
/pm/next
/pm/mode <hybrid|musical|timed>
/pm/journey <journey-name>
/pm/journey/save <name> <cue1> <cue2> ...
/pm/snapshot/save <name>
/pm/snapshot/load <name>
```

Binding to localhost is deliberate. Set `--osc-host 0.0.0.0` only when a trusted LAN controller
needs to reach the machine.

## Persistent state vault

By default snapshots and custom journeys are stored at:

```text
~/.projection_mapping/performance_states.json
```

A different path can be supplied with `--state-file`.

Snapshots preserve:

- current cue
- active journey
- sequencing mode
- base MADNESS

Custom journeys are ordered lists of existing cue names. Save one over OSC with
`/pm/journey/save`, then select it with `/pm/journey`. To start directly in a saved journey from
the UI or CLI, set `--user-journey <name>`.

## Control philosophy

Audio remains responsible for continuous musical evidence and sparse drop/beat events. Manual
control is an override layer for intentional performance decisions. Triggering a cue does not reset
the persistent particle simulation; it starts the same smooth cue morph used by automatic journeys.
