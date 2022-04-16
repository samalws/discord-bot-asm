# Assembly Discord Bot

This bot allows you to write your own programs in an assembly-like language.
These programs can read and send messages, as well as choosing random numbers, making HTTP requests, and performing computations.
The language is Turing complete, but there are gas limits (as in Ethereum) preventing you from running too many commands and taking up all the bot's compute time.
The bot has a permission system allowing you to choose which programs can access which channels.

## Commands:

- $addProc \`\`\` \[code\] \`\`\` - Spawn a new process with specified assembly code (see below for description of the assembly language). The process is given a process ID (PID) which can be used to identify it.
- $allow \[pid\] - Allow a process in the current channel. This allows the process to read new (but not old) messages, and send messages. (By default, processess are allowed in the channel they're created in. This can be undone using $ban).
- $ban \[pid\] - Ban a process from the current channel. This can be undone by using $allow again.
- $allowedList - View a list of all processes (listed by pid) allowed in the current channel.
- $gas \[pid\] - Check how much gas a process has left.
- $refuel \[pid\] - Refuel a process back to full gas.

Note that it is impossible to modify a program once it is made, or to view a program's source code or internal variables unless it chooses to send them.

## "Assembly" code:

Like assembly, code can have labels, instructions, and comments.
Unlike assembly, you are allowed to name your own variables, and assign variables to be strings, ints, users, or channels.
Here is an example program:

```
# Asks to be refueled whenever its gas total drops below 1000

# When created, programs first run the start: label. It's like the "main" function in C.
start:
# Assign some integer literals.
LITINT gasCutoff 1000
LITINT sleepAmt 10
# Assign variables to be string literals. Note the lack of quotes around the strings; the string lasts until the end of the line.
LITSTR gasReqMsg HELP I NEED MORE FUEL
LITSTR thanksMsg thanks :)

# After assigning these variables, we continue on to our main loop.
loop:
# wait a bit first
SLP sleepAmt
# get the current gas level
GAS g
# conditional jump
JG gasCutoff g requestGas
# normal jump, back up to loop:
JMP loop

requestGas:
# get the channel the process was created in
CHN channel
# send a message in the channel: "HELP I NEED MORE FUEL"
SEND channel gasReqMsg
JMP loop

# Whenever a bot is refueled, its refuel: label is called.
# Whenever a bot added to a channel, its added: label is called.
# You can also add "banned:" and "msg:" labels for when the bot is banned, or when it sees a new message in a channel it's allowed in.
# All these labels are optional; if they aren't there, no code gets executed when the action happens.

refueled:
added:
CHN channel
SEND channel thanksMsg
# We didn't need to exit out of the program in start:, since we infinite loop.
# Here, we need to exit using the EXIT tag
EXIT

# Note that multiple threads can run at once, but everything should be atomic
```

More examples are available in the `examples` folder.

## Instruction List:

Here is a full list of instructions in our assembly language:

| Instruction | Description | Gas Cost |
| --- | --- | --- |
| `LITSTR s asdfasdf asdf` | Assign `s` to be the string "asdfasdf asdf" | 1   |
| `LITINT n 10` | Assigns `n` to be 10 | 1   |
| `NWLN s` | Assigns `s` to be the newline character | 1   |
| `MOV x y` | Assigns `x` to be the value of `y` | 1   |
| `ADD x y` | Adds `x` and `y` (either ints or strings), and puts the result into `x` | 1   |
| `MUL x y` | Multiplies `x` and `y` (either two ints, two strings, or a string and an int), and puts the result into `x` | 1   |
| `SBST s x y` | Takes `s[x:y]` and puts the result into `s` | 1   |
| `JMP l` | Jumps to label `l` | 1   |
| `JE x y l` | Jumps to label `l` if `x == y` (Can be strings, ints, channels, or users) | 1   |
| `JG x y l ` | Jumps to label `l` if `x > y` (Must be ints) | 1   |
| `STR x` | Converts x into a string | 1   |
| `INT x` | Converts x into an int | 1   |
| `UPR s` | Converts string `s` to uppercase | 1   |
| `LWR s` | Converts string `s` to lowercase | 1   |
| `GAS x` | Gets the amount of gas left, storing the result in `x` | 1   |
| `SEND c m` | Sends message `m` (a string) on channel `c` | 100 |
| `READ s` | Reads the message that initiated program execution into variable `s` | 1   |
| `CHN c` | Gets the channel that initiated program execution, putting it into variable `c` | 1   |
| `USR u` | Gets the user that initiated program execution, putting it into variable `u` | 1   |
| `AT u` | Creates an `@` message to ping user `u`, overwriting variable `u` | 1   |
| `SLP t` | Sleeps for `t` seconds | 5   |
| `DUMP v` | Dumps a JSON representation of all program variables into variable `v` (for debugging). Note that this can get cut off if it exceeds the maximum variable size. | 5   |
| `RNG r a b` | Generates a random integer between `a` and `b` (inclusive), and stores the result in `r` | 5   |
| `PID v` | Stores the program's pid in `v` | 1   |
| `ALLW v c` | Checks if the proram is allowed in channel `c`. If it is, `v` is set to `1`; otherwise it is set to `0`. | 1   |
| `EMJI s v` | Turns `s` into an emoji, checking for emojis in channel `c`. For example, `smile` would become `:smile:`, although custom emojis create more complicated strings. | 5   |
| `LEN s` | Gets the length of string `v`, overwriting `v` with the value. Useful for avoiding rate limits. | 1   |
| `NVAR v` | Puts the current number of variables used into `v`. This is important for avoiding rate limits. | 1   |
| `ARBW x v` | Writes value `v` to an arbitrary "memory location", identified by `x`. This location can be a string or an int. | 1   |
| `ARBR v x` | Reads the value at "memory location" `x` into `v`. | 1   |
| `HTTP s v` | Sends an HTTP GET request to address `s`. The response is put into `s`, and the response code into `v`. If the response is too long (exceeds maximum string size), `s` is set to an error message and `v` is set to -1. | 20  |
| `EXIT` | Terminates program execution (just this thread, not all of them) | 0   |

Note that, except in `LITINT` and `LITSTR`, all values must be variables, not literals.
To get a literal, create a dummy variable with the value you want using `LITINT` or `LITSTR`.

Also note that instructions are not case sensitive, so `aDd a b` is a valid instruction.

## Special Labels:

The following special labels are called at different times:
- `start:` - Called when a program is first created.
- `msg:` - Called when a message is sent in a channel the program is allowed in. The message can be retreived with `READ`.
- `allowed:` - Called when a program is allowed in a channel.
- `banned:` - Called when a program is banned from a channel.
- `refueled:` - Called when a program is refueled.

## Rate Limits:

The following limits are added to your program by default. If you self-host the bot, you can easily change around these limits to allow your program to have more resources.

- Maximum string size: 4000 characters
- Maximum number of variRate limits: max string size 4000, max number of vars 500, gas per refuel 10000, dead process kill time 86400 seconds
128
ables (including "memory locations" written to by ARBW): 500 variables
- Full gas level: 10000 gas
- Dead process kill time (if a process stays out of gas for too long, or is not allowed in any channels): 1 day
