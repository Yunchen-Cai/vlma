"""
fsm_state_machine.py — Python implementation of the SOP-guided FSM described in
§3.5 of the paper.

The FSM consumes a stream of (timestamp, vlm_output, confidence) tuples and
maintains per-node completion mass C_i(t), readiness F_i(t), error mass E_i(t),
and timeout mass D_i(t). It raises three classes of alarms:

  - ordering-violation : E_i > eps_ordering
  - timing-violation   : D_i > eps_timing
  - unfinished         : V-gated node has C_i > thresh_C_complete but no
                          Verification-mode Finish confirmation yet

SOP graph format (sop_graph_gearpump.json):
{
  "default_eps_ordering": 0.05,
  "default_eps_timing": 0.05,
  "default_complete_threshold": 0.7,
  "nodes": [
    {
      "id": "place_mounting_flange",
      "actions_whitelist": ["place-mountingFlange", "place-mounting_flange"],
      "parents": [],
      "tau_lower_sec": 2.0,
      "tau_upper_sec": 8.0,
      "v_gated": true,
      "part": "Mounting Flange"
    },
    ...
  ]
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class NodeState:
    id: str
    actions_whitelist: List[str]
    parents: List[str]
    tau_lower_sec: float
    tau_upper_sec: float
    v_gated: bool
    part: Optional[str] = None

    # Dynamic state
    C: float = 0.0           # completion mass (cumulative, [0, 1])
    F: float = 0.0           # readiness (product of parents' C)
    E: float = 0.0           # error mass = C * (1 - F)
    D: float = 0.0           # timing-overshoot mass
    first_active_time: Optional[float] = None  # when its C first crossed eps
    verified: bool = False   # whether Verification mode has confirmed Finish for this node
    visit_prob_history: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class Alarm:
    alarm_type: str  # 'ordering' | 'timing' | 'unfinished'
    node_id: str
    frame_idx: int
    timestamp_sec: float
    score: float     # E_i or D_i or C_i at trigger


class SOPGuidedFSM:
    """Probabilistic SOP-guided state machine.

    Notes on semantics matching §3.5:
      - Eq. (4): F_i(t) = prod_{j in pi_i} C_j(t). Empty parents -> F_i = 1.
      - Confidence-weighted observation update: when VLM emits action-object string s,
        the matching nodes share `confidence` mass; we further weight by parent
        readiness F_i (so a node with unfulfilled parents accumulates LESS
        directly, which produces the error mass E_i = C_i * (1 - F_i) for
        wrong-order activations).
      - Timing overshoot D_i: accumulated whenever the node is "active"
        (C_i > eps_active) AND its dwell time has exceeded tau_upper_sec.
    """

    def __init__(self, sop_graph_json_path: str,
                 eps_ordering: Optional[float] = None,
                 eps_timing: Optional[float] = None,
                 complete_threshold: Optional[float] = None,
                 eps_active: float = 0.05,
                 alarm_dedupe: bool = True):
        path = Path(sop_graph_json_path)
        graph = json.loads(path.read_text(encoding='utf-8'))
        self.eps_ordering = eps_ordering if eps_ordering is not None else graph.get('default_eps_ordering', 0.05)
        self.eps_timing = eps_timing if eps_timing is not None else graph.get('default_eps_timing', 0.05)
        self.complete_threshold = complete_threshold if complete_threshold is not None else graph.get('default_complete_threshold', 0.7)
        self.eps_active = eps_active
        self.alarm_dedupe = alarm_dedupe

        self.nodes: Dict[str, NodeState] = {}
        for n in graph['nodes']:
            self.nodes[n['id']] = NodeState(
                id=n['id'],
                actions_whitelist=n['actions_whitelist'],
                parents=n.get('parents', []),
                tau_lower_sec=float(n.get('tau_lower_sec', 0.0)),
                tau_upper_sec=float(n.get('tau_upper_sec', 1e9)),
                v_gated=bool(n.get('v_gated', False)),
                part=n.get('part'),
            )
        self.node_order = [n['id'] for n in graph['nodes']]
        self.last_time: Optional[float] = None
        self.alarms_raised: Dict[Tuple[str, str], Alarm] = {}  # (alarm_type, node_id) -> earliest Alarm

    # ---- core update ----

    def _match_nodes(self, action_object_string: str) -> List[NodeState]:
        if not action_object_string:
            return []
        s_norm = action_object_string.strip().lower().replace(' ', '').replace('_', '')
        out = []
        for node in self.nodes.values():
            for w in node.actions_whitelist:
                w_norm = w.strip().lower().replace(' ', '').replace('_', '')
                if w_norm == s_norm:
                    out.append(node)
                    break
        return out

    def _readiness(self, node: NodeState) -> float:
        if not node.parents:
            return 1.0
        prod = 1.0
        for pid in node.parents:
            prod *= self.nodes[pid].C
        return prod

    def consume(self, frame_idx: int, timestamp_sec: float,
                vlm_mode: str, vlm_output: dict, confidence: float) -> List[Alarm]:
        """Consume one observation. Returns list of newly-raised alarms in this frame."""
        if confidence is None:
            confidence = 0.0
        confidence = max(0.0, min(1.0, float(confidence)))

        new_alarms: List[Alarm] = []

        if vlm_mode == 'general':
            action = (vlm_output or {}).get('action', '') or ''
            part = (vlm_output or {}).get('part', '') or ''
            s = self._action_object_string(action, part)
            matches = self._match_nodes(s)
            if matches:
                share = confidence / len(matches)
                for node in matches:
                    F = self._readiness(node)
                    delta = share * F
                    # Even if F is low (ordering violation), still credit a base share
                    # so the error mass C*(1-F) registers; this matches the §3.5 description
                    # "confidence-weighted probability is distributed ... in proportion to
                    # each parent's readiness ... and remaining budget".
                    # We allow a small "leak" so wrong-order activations also accumulate.
                    leak = share * (1.0 - F) * 0.5
                    node.C = min(1.0, node.C + delta + leak)
                    if node.first_active_time is None and node.C > self.eps_active:
                        node.first_active_time = timestamp_sec
        elif vlm_mode == 'verification':
            part = (vlm_output or {}).get('part', '') or ''
            verdict = (vlm_output or {}).get('verification', '') or ''
            # Match V-gated nodes whose `part` matches
            for node in self.nodes.values():
                if not node.v_gated:
                    continue
                if node.part and node.part.strip().lower() == part.strip().lower():
                    if verdict.lower().startswith('finish'):
                        # Soft additive contribution
                        node.C = min(1.0, node.C + 0.5 * confidence)
                        if confidence > 0.5:
                            node.verified = True

        # Update F, E, D for every node
        dt = 0.0
        if self.last_time is not None:
            dt = max(0.0, timestamp_sec - self.last_time)
        self.last_time = timestamp_sec

        for node in self.nodes.values():
            node.F = self._readiness(node)
            node.E = node.C * (1.0 - node.F)
            # Timing overshoot accumulation: if node is "active" (C > eps_active) and
            # the time since it first became active exceeds tau_upper_sec, accumulate D.
            if node.first_active_time is not None:
                dwell = timestamp_sec - node.first_active_time
                if dwell > node.tau_upper_sec and not node.verified:
                    node.D = min(1.0, node.D + dt * 0.1)  # 10s overshoot -> D=1
                else:
                    pass  # keep D
            node.visit_prob_history.append((timestamp_sec, node.C))

        # Check alarm conditions
        for node in self.nodes.values():
            # Ordering violation
            if node.E > self.eps_ordering:
                key = ('ordering', node.id)
                if not self.alarm_dedupe or key not in self.alarms_raised:
                    a = Alarm('ordering', node.id, frame_idx, timestamp_sec, node.E)
                    new_alarms.append(a)
                    self.alarms_raised[key] = a
            # Timing violation
            if node.D > self.eps_timing:
                key = ('timing', node.id)
                if not self.alarm_dedupe or key not in self.alarms_raised:
                    a = Alarm('timing', node.id, frame_idx, timestamp_sec, node.D)
                    new_alarms.append(a)
                    self.alarms_raised[key] = a
            # Unfinished completion
            if (node.v_gated and node.C > self.complete_threshold
                    and not node.verified):
                # Only alert after the node should have been verified — i.e. dwell exceeds tau_lower
                if node.first_active_time is not None:
                    dwell = timestamp_sec - node.first_active_time
                    if dwell > node.tau_lower_sec * 1.5:
                        key = ('unfinished', node.id)
                        if not self.alarm_dedupe or key not in self.alarms_raised:
                            a = Alarm('unfinished', node.id, frame_idx, timestamp_sec, node.C)
                            new_alarms.append(a)
                            self.alarms_raised[key] = a
        return new_alarms

    @staticmethod
    def _action_object_string(action: str, part: str) -> str:
        a = (action or '').strip().lower()
        p = (part or '').strip()
        if not a or not p:
            return ''
        # Convert 'Place' + 'Port End Cover' -> 'place-portEndCover'
        camel = ''.join(w.capitalize() if i > 0 else w.lower()
                        for i, w in enumerate(p.split()))
        return f'{a}-{camel}'

    # ---- snapshot for logging ----
    def snapshot(self) -> Dict:
        return {
            'nodes': {
                nid: {'C': n.C, 'F': n.F, 'E': n.E, 'D': n.D,
                      'verified': n.verified, 'first_active_time': n.first_active_time}
                for nid, n in self.nodes.items()
            },
            'n_alarms_raised': len(self.alarms_raised),
        }


if __name__ == '__main__':
    # Tiny smoke test
    import tempfile
    sop_graph = {
        'default_eps_ordering': 0.05,
        'default_eps_timing': 0.05,
        'default_complete_threshold': 0.7,
        'nodes': [
            {'id': 'A', 'actions_whitelist': ['place-A'], 'parents': [],
             'tau_lower_sec': 1.0, 'tau_upper_sec': 5.0, 'v_gated': True, 'part': 'A'},
            {'id': 'B', 'actions_whitelist': ['place-B'], 'parents': ['A'],
             'tau_lower_sec': 1.0, 'tau_upper_sec': 5.0, 'v_gated': True, 'part': 'B'},
        ],
    }
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(sop_graph, f)
        path = f.name

    fsm = SOPGuidedFSM(path)

    print("# Test 1: in-order -> no alarms")
    for i, t in enumerate([0.0, 0.5, 1.0]):
        a = fsm.consume(i, t, 'general', {'action': 'place', 'part': 'A'}, 0.9)
        print(f"  t={t}: A.C={fsm.nodes['A'].C:.3f}, alarms={len(a)}")
    # Verify A
    a = fsm.consume(3, 1.5, 'verification', {'part': 'A', 'verification': 'Finish'}, 0.95)
    for i, t in enumerate([2.0, 2.5, 3.0]):
        a = fsm.consume(4 + i, t, 'general', {'action': 'place', 'part': 'B'}, 0.9)
        print(f"  t={t}: B.C={fsm.nodes['B'].C:.3f}, B.F={fsm.nodes['B'].F:.3f}, B.E={fsm.nodes['B'].E:.3f}, alarms={len(a)}")
    print(f"  Total alarms raised: {len(fsm.alarms_raised)}")

    print()
    print("# Test 2: out-of-order -> ordering alarm")
    fsm2 = SOPGuidedFSM(path)
    for i, t in enumerate([0.0, 0.5]):
        a = fsm2.consume(i, t, 'general', {'action': 'place', 'part': 'B'}, 0.9)
        print(f"  t={t}: B.C={fsm2.nodes['B'].C:.3f}, B.E={fsm2.nodes['B'].E:.3f}, alarms_this_frame={[al.alarm_type for al in a]}")

    print()
    print("# Test 3: timing overshoot -> timing alarm")
    fsm3 = SOPGuidedFSM(path)
    # Activate A then let dwell time exceed tau_upper
    fsm3.consume(0, 0.0, 'general', {'action': 'place', 'part': 'A'}, 0.9)
    fsm3.consume(1, 0.5, 'general', {'action': 'place', 'part': 'A'}, 0.9)
    # No verification, no further activation
    a = []
    for i, t in enumerate([6.0, 8.0, 10.0]):
        new = fsm3.consume(2 + i, t, 'general', {'action': '', 'part': ''}, 0.0)
        a.extend(new)
        print(f"  t={t}: A.D={fsm3.nodes['A'].D:.3f}, alarms_this_frame={[al.alarm_type for al in new]}")

    print()
    print("# Test 4: unfinished completion -> unfinished alarm")
    fsm4 = SOPGuidedFSM(path)
    for i, t in enumerate([0.0, 0.5, 1.0, 1.5, 2.0, 2.5]):
        new = fsm4.consume(i, t, 'general', {'action': 'place', 'part': 'A'}, 0.9)
        if new:
            print(f"  t={t}: alarms={[al.alarm_type for al in new]}")
    print(f"  Total alarms: {len(fsm4.alarms_raised)}")
    print(f"  A.C={fsm4.nodes['A'].C:.3f}, A.verified={fsm4.nodes['A'].verified}")
    print(f"  Alarms raised: {[(k, a.frame_idx, a.score) for k, a in fsm4.alarms_raised.items()]}")
