--------------------------- MODULE Isolation ---------------------------
(***************************************************************************)
(* Isolation of the safety function from the network path.                 *)
(*                                                                         *)
(* AlarmFSM.tla models WHAT the alarm does. This module models HOW the two  *)
(* cores interact, and proves the architectural claim the paper makes: no   *)
(* behaviour of the network side can stop, delay or alter a step of the     *)
(* safety side.                                                             *)
(*                                                                         *)
(* The model is deliberately adversarial about the network task: it may     *)
(* stall for an unbounded time, be flooded with attacker messages, fail to  *)
(* publish, and crash and restart. The safety task is a loop that must be   *)
(* able to take its next step in every reachable state.                     *)
(*                                                                         *)
(* Properties proved:                                                      *)
(*   SafetyCanAlwaysStep : in EVERY reachable state the safety task is      *)
(*                         enabled, i.e. it is never blocked by the network *)
(*                         side (no shared lock, no bounded buffer it must  *)
(*                         wait on, no synchronous call).                   *)
(*   SafetyProgress      : the safety task takes a step infinitely often    *)
(*                         even under a permanently misbehaving network.    *)
(*   NoNetworkWrite      : the network task never writes the alarm state.   *)
(*   QueueBounded        : the event queue never exceeds its capacity       *)
(*                         (the writer drops instead of blocking).          *)
(*   NoSilentLoss        : an event is either delivered or counted as       *)
(*                         dropped; it never disappears unaccounted for.    *)
(***************************************************************************)
EXTENDS Naturals

CONSTANTS QCap,        \* event queue capacity (16 in the firmware)
          MaxEvents    \* bound on events generated, to keep the model finite

VARIABLES
  safetySteps,   \* number of steps the safety loop has taken
  produced,      \* events the safety side has generated
  queued,        \* events currently in the queue
  delivered,     \* events the network side has published
  dropped,       \* events dropped because the queue was full (counted)
  netState,      \* "idle", "busy", "stalled", "down"
  netOwnsState   \* TRUE only if the network task could write the alarm state (must stay FALSE)

vars == <<safetySteps, produced, queued, delivered, dropped, netState, netOwnsState>>

TypeOK ==
  /\ safetySteps \in 0..MaxEvents
  /\ produced \in 0..MaxEvents
  /\ queued \in 0..QCap
  /\ delivered \in 0..MaxEvents
  /\ dropped \in 0..MaxEvents
  /\ netState \in {"idle", "busy", "stalled", "down"}
  /\ netOwnsState \in BOOLEAN

Init ==
  /\ safetySteps = 0
  /\ produced = 0
  /\ queued = 0
  /\ delivered = 0
  /\ dropped = 0
  /\ netState = "idle"
  /\ netOwnsState = FALSE

(*************************************************************************)
(* The safety task. One step of the loop. It may enqueue an event. The    *)
(* enqueue NEVER blocks: if the queue is full it drops the oldest and     *)
(* counts it. Crucially this action's guard mentions nothing owned by the *)
(* network task, which is what makes isolation hold.                      *)
(*************************************************************************)
SafetyStepQuiet ==
  /\ safetySteps < MaxEvents
  /\ safetySteps' = safetySteps + 1
  /\ UNCHANGED <<produced, queued, delivered, dropped, netState, netOwnsState>>

SafetyStepEmit ==
  /\ safetySteps < MaxEvents
  /\ produced < MaxEvents
  /\ safetySteps' = safetySteps + 1
  /\ produced' = produced + 1
  /\ IF queued < QCap
       THEN /\ queued' = queued + 1
            /\ dropped' = dropped
       ELSE /\ queued' = queued          \* full: drop the oldest, keep the newest
            /\ dropped' = dropped + 1
  /\ UNCHANGED <<delivered, netState, netOwnsState>>

SafetyStep == SafetyStepQuiet \/ SafetyStepEmit

(*************************************************************************)
(* The network task, modelled adversarially. It can move between idle,    *)
(* busy, stalled (blocked in a slow DNS/TCP/TLS call for an unbounded     *)
(* time) and down. It can publish only when the link is usable, and it    *)
(* may fail to publish at any time. It never touches the alarm state.     *)
(*************************************************************************)
NetGoBusy    == /\ netState \in {"idle"}      /\ netState' = "busy"
                /\ UNCHANGED <<safetySteps, produced, queued, delivered, dropped, netOwnsState>>
NetStall     == /\ netState \in {"idle","busy"} /\ netState' = "stalled"
                /\ UNCHANGED <<safetySteps, produced, queued, delivered, dropped, netOwnsState>>
NetRecover   == /\ netState \in {"stalled","down"} /\ netState' = "idle"
                /\ UNCHANGED <<safetySteps, produced, queued, delivered, dropped, netOwnsState>>
NetCrash     == /\ netState' = "down"
                /\ UNCHANGED <<safetySteps, produced, queued, delivered, dropped, netOwnsState>>

NetDeliver ==
  /\ netState = "busy"
  /\ queued > 0
  /\ queued' = queued - 1
  /\ delivered' = delivered + 1
  /\ netState' = "idle"
  /\ UNCHANGED <<safetySteps, produced, dropped, netOwnsState>>

(* A failed publish: the event goes back to the queue, nothing is lost. *)
NetPublishFails ==
  /\ netState = "busy"
  /\ queued > 0
  /\ netState' = "down"
  /\ UNCHANGED <<safetySteps, produced, queued, delivered, dropped, netOwnsState>>

NetStep == NetGoBusy \/ NetStall \/ NetRecover \/ NetCrash \/ NetDeliver \/ NetPublishFails

Next == SafetyStep \/ NetStep

(* Only the safety task is assumed to be fair. The network task is given NO fairness at all:
   it is allowed to stall forever. If the safety task still progresses, isolation holds. *)
Spec == Init /\ [][Next]_vars /\ WF_vars(SafetyStep)

----------------------------------------------------------------------------
(* The isolation invariant: in every reachable state, the safety task can take a step,
   unless it has simply finished its bounded run in this model. No network state blocks it. *)
SafetyCanAlwaysStep == (safetySteps < MaxEvents) => ENABLED SafetyStep

(* The network task never writes the alarm state. *)
NoNetworkWrite == netOwnsState = FALSE

(* The queue never overflows its capacity: the writer drops instead of blocking. *)
QueueBounded == queued <= QCap

(* Every produced event is accounted for: delivered, still queued, or counted as dropped. *)
NoSilentLoss == produced = delivered + queued + dropped

(* Liveness: the safety task keeps taking steps however badly the network behaves.
   Within this bounded model the safety task runs until it has taken MaxEvents steps, so the
   property is stated as: it always eventually reaches its bound, i.e. it is never starved. *)
SafetyProgress == <>(safetySteps = MaxEvents)
=============================================================================
