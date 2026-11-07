---- MODULE AlarmFSM_TTrace_1794034091 ----
EXTENDS Sequences, TLCExt, AlarmFSM, Toolbox, Naturals, TLC

_expression ==
    LET AlarmFSM_TEExpression == INSTANCE AlarmFSM_TEExpression
    IN AlarmFSM_TEExpression!expression
----

_trace ==
    LET AlarmFSM_TETrace == INSTANCE AlarmFSM_TETrace
    IN AlarmFSM_TETrace!trace
----

_inv ==
    ~(
        TLCGet("level") = Len(_TETrace)
        /\
        ctr = (0)
        /\
        badDisarm = (TRUE)
        /\
        state = ("Disarmed")
    )
----

_init ==
    /\ state = _TETrace[1].state
    /\ ctr = _TETrace[1].ctr
    /\ badDisarm = _TETrace[1].badDisarm
----

_next ==
    /\ \E i,j \in DOMAIN _TETrace:
        /\ \/ /\ j = i + 1
              /\ i = TLCGet("level")
        /\ state  = _TETrace[i].state
        /\ state' = _TETrace[j].state
        /\ ctr  = _TETrace[i].ctr
        /\ ctr' = _TETrace[j].ctr
        /\ badDisarm  = _TETrace[i].badDisarm
        /\ badDisarm' = _TETrace[j].badDisarm

\* Uncomment the ASSUME below to write the states of the error trace
\* to the given file in Json format. Note that you can pass any tuple
\* to `JsonSerialize`. For example, a sub-sequence of _TETrace.
    \* ASSUME
    \*     LET J == INSTANCE Json
    \*         IN J!JsonSerialize("AlarmFSM_TTrace_1794034091.json", _TETrace)

=============================================================================

 Note that you can extract this module `AlarmFSM_TEExpression`
  to a dedicated file to reuse `expression` (the module in the 
  dedicated `AlarmFSM_TEExpression.tla` file takes precedence 
  over the module `AlarmFSM_TEExpression` below).

---- MODULE AlarmFSM_TEExpression ----
EXTENDS Sequences, TLCExt, AlarmFSM, Toolbox, Naturals, TLC

expression == 
    [
        \* To hide variables of the `AlarmFSM` spec from the error trace,
        \* remove the variables below.  The trace will be written in the order
        \* of the fields of this record.
        state |-> state
        ,ctr |-> ctr
        ,badDisarm |-> badDisarm
        
        \* Put additional constant-, state-, and action-level expressions here:
        \* ,_stateNumber |-> _TEPosition
        \* ,_stateUnchanged |-> state = state'
        
        \* Format the `state` variable as Json value.
        \* ,_stateJson |->
        \*     LET J == INSTANCE Json
        \*     IN J!ToJson(state)
        
        \* Lastly, you may build expressions over arbitrary sets of states by
        \* leveraging the _TETrace operator.  For example, this is how to
        \* count the number of times a spec variable changed up to the current
        \* state in the trace.
        \* ,_stateModCount |->
        \*     LET F[s \in DOMAIN _TETrace] ==
        \*         IF s = 1 THEN 0
        \*         ELSE IF _TETrace[s].state # _TETrace[s-1].state
        \*             THEN 1 + F[s-1] ELSE F[s-1]
        \*     IN F[_TEPosition - 1]
    ]

=============================================================================



Parsing and semantic processing can take forever if the trace below is long.
 In this case, it is advised to uncomment the module below to deserialize the
 trace from a generated binary file.

\*
\*---- MODULE AlarmFSM_TETrace ----
\*EXTENDS IOUtils, AlarmFSM, TLC
\*
\*trace == IODeserialize("AlarmFSM_TTrace_1794034091.bin", TRUE)
\*
\*=============================================================================
\*

---- MODULE AlarmFSM_TETrace ----
EXTENDS AlarmFSM, TLC

trace == 
    <<
    ([ctr |-> 0,badDisarm |-> FALSE,state |-> "Disarmed"]),
    ([ctr |-> 0,badDisarm |-> FALSE,state |-> "ExitDelay"]),
    ([ctr |-> 0,badDisarm |-> TRUE,state |-> "Disarmed"])
    >>
----


=============================================================================

---- CONFIG AlarmFSM_TTrace_1794034091 ----
CONSTANTS
    MaxCtr = 4
    AllowUnauthDisarm = TRUE

INVARIANT
    _inv

CHECK_DEADLOCK
    \* CHECK_DEADLOCK off because of PROPERTY or INVARIANT above.
    FALSE

INIT
    _init

NEXT
    _next

CONSTANT
    _TETrace <- _trace

ALIAS
    _expression
=============================================================================
\* Generated on Sat Nov 07 12:18:11 IST 2026