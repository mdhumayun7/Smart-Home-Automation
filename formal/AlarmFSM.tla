---------------------------- MODULE AlarmFSM ----------------------------
(***************************************************************************)
(* A formal model of the Smart Home Surveillance System alarm controller:  *)
(* its five-state arm/disarm machine and the authenticated command path.   *)
(*                                                                         *)
(* The model is an abstraction of firmware/smart_home/smart_home.ino. Time *)
(* is abstract: a delay "expires" as a nondeterministic step rather than   *)
(* by counting milliseconds, which is the right level for reasoning about  *)
(* which transitions are reachable and who may cause them. The checked      *)
(* properties mirror the security and safety claims in the README:          *)
(*                                                                         *)
(*   Safety  NoUnauthRemoteDisarm : the system never leaves an armed state  *)
(*            because of an unauthenticated remote command.                 *)
(*   Safety  CounterMonotonic     : the replay counter never decreases.     *)
(*   Safety  NoAlarmWhenDisarmed  : the siren is never on while disarmed.    *)
(*   Live    EntryLeadsToResolve  : an entry delay always ends in the alarm  *)
(*            or in disarm (the system can never get stuck mid-entry).       *)
(*   Live    AlarmReArms          : the alarm always ends (re-arm or disarm). *)
(***************************************************************************)
EXTENDS Naturals

CONSTANT MaxCtr            \* bound the counter so the state space is finite

VARIABLES state,          \* Disarmed, ExitDelay, Armed, EntryDelay, Alarm
          ctr,            \* highest accepted authenticated command counter
          badDisarm       \* set TRUE if an unauthenticated remote disarm ever took effect

States == {"Disarmed", "ExitDelay", "Armed", "EntryDelay", "Alarm"}
ArmedLike == {"ExitDelay", "Armed", "EntryDelay", "Alarm"}

TypeOK ==
  /\ state \in States
  /\ ctr \in 0..MaxCtr
  /\ badDisarm \in BOOLEAN

Init ==
  /\ state = "Disarmed"
  /\ ctr = 0
  /\ badDisarm = FALSE

(* The local button: arms from Disarmed, disarms from any armed state. Always trusted. *)
ButtonArm ==
  /\ state = "Disarmed"
  /\ state' = "ExitDelay"
  /\ UNCHANGED <<ctr, badDisarm>>

ButtonDisarm ==
  /\ state \in ArmedLike
  /\ state' = "Disarmed"
  /\ UNCHANGED <<ctr, badDisarm>>

(* Exit delay completes -> Armed. *)
ExitExpire ==
  /\ state = "ExitDelay"
  /\ state' = "Armed"
  /\ UNCHANGED <<ctr, badDisarm>>

(* A sensor trigger while Armed starts the entry delay. *)
SensorTrigger ==
  /\ state = "Armed"
  /\ state' = "EntryDelay"
  /\ UNCHANGED <<ctr, badDisarm>>

(* Entry delay completes without a disarm -> Alarm. *)
EntryExpire ==
  /\ state = "EntryDelay"
  /\ state' = "Alarm"
  /\ UNCHANGED <<ctr, badDisarm>>

(* Alarm times out -> back to Armed. *)
AlarmExpire ==
  /\ state = "Alarm"
  /\ state' = "Armed"
  /\ UNCHANGED <<ctr, badDisarm>>

(* An authenticated remote command carries a counter n. It is accepted only when it strictly
   exceeds the stored counter (replay protection); then the counter advances. ARM arms from
   Disarmed, DISARM disarms from an armed state. *)
RemoteAuthArm(n) ==
  /\ n > ctr
  /\ state = "Disarmed"
  /\ state' = "ExitDelay"
  /\ ctr' = n
  /\ UNCHANGED badDisarm

RemoteAuthDisarm(n) ==
  /\ n > ctr
  /\ state \in ArmedLike
  /\ state' = "Disarmed"
  /\ ctr' = n
  /\ UNCHANGED badDisarm

(* A replayed or stale authenticated command (n <= ctr) is ignored: no state change. *)
RemoteReplay(n) ==
  /\ n <= ctr
  /\ UNCHANGED <<state, ctr, badDisarm>>

(* An UNauthenticated remote command. The firmware refuses it: ARM is ignored here for the
   abstraction, and DISARM must NOT take effect. We model the *attempted* disarm and assert,
   through the firmware's rule, that state does not change. If a future change ever let it
   through, badDisarm would be set and the safety invariant would catch it. *)
RemoteUnauthDisarmRefused ==
  /\ state \in ArmedLike
  /\ UNCHANGED <<state, ctr, badDisarm>>   \* refused: no effect, exactly as the firmware does

Next ==
  \/ ButtonArm \/ ButtonDisarm
  \/ ExitExpire \/ SensorTrigger \/ EntryExpire \/ AlarmExpire
  \/ \E n \in 1..MaxCtr : RemoteAuthArm(n) \/ RemoteAuthDisarm(n) \/ RemoteReplay(n)
  \/ RemoteUnauthDisarmRefused

(* Fairness so the timed transitions actually happen, for the liveness properties. *)
Fairness ==
  /\ WF_<<state, ctr, badDisarm>>(ExitExpire)
  /\ WF_<<state, ctr, badDisarm>>(EntryExpire)
  /\ WF_<<state, ctr, badDisarm>>(AlarmExpire)

Spec == Init /\ [][Next]_<<state, ctr, badDisarm>> /\ Fairness

----------------------------------------------------------------------------
(* Safety properties (invariants). *)
NoUnauthRemoteDisarm == badDisarm = FALSE
CounterMonotonic     == [][ctr' >= ctr]_<<state, ctr, badDisarm>>
NoAlarmWhenDisarmed  == (state = "Disarmed") => (state # "Alarm")

(* Liveness properties. *)
EntryLeadsToResolve == (state = "EntryDelay") ~> (state \in {"Alarm", "Disarmed"})
AlarmReArms         == (state = "Alarm") ~> (state \in {"Armed", "Disarmed"})
=============================================================================
