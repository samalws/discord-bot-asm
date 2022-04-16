import asyncio
import discord
import random
import json
import requests
import os
import time

STRING_MAXSIZE = 4000
TIME_KILL = 60*60*24
MAX_NVARS = 500
FULL_GAS = 10000

LIT  = 0
MOV  = 1
ADD  = 2
MUL  = 3
SBST = 4
JMP  = 5
JE   = 6
JG   = 7
STR  = 8
GAS  = 9
UPR  = 10
LWR  = 11
SEND = 12
READ = 13
CHN  = 14
USR  = 15
AT   = 16
SLP  = 17
EXIT = 18
DUMP = 19
RNG  = 20
PID  = 21
ALLW = 22
INT  = 23
EMJI = 24
LEN  = 25
NVAR = 26
ARBW = 27
ARBR = 28
NWLN = 29
HTTP = 30

cmdStrs = {
  "MOV": MOV,
  "ADD": ADD,
  "MUL": MUL,
  "SBST": SBST,
  "JMP": JMP,
  "JE": JE,
  "JG": JG,
  "STR": STR,
  "GAS": GAS,
  "UPR": UPR,
  "LWR": LWR,
  "SEND": SEND,
  "READ": READ,
  "CHN": CHN,
  "USR": USR,
  "AT": AT,
  "SLP": SLP,
  "EXIT": EXIT,
  "DUMP": DUMP,
  "RNG": RNG,
  "PID": PID,
  "ALLW": ALLW,
  "INT": INT,
  "EMJI": EMJI,
  "LEN": LEN,
  "NVAR": NVAR,
  "ARBW": ARBW,
  "ARBR": ARBR,
  "NWLN": NWLN,
  "HTTP": HTTP,
}

cmdGases = {
  LIT:  1,
  MOV:  1,
  ADD:  1,
  MUL:  1,
  SBST: 1,
  JMP:  1,
  JE:   1,
  JG:   1,
  STR:  1,
  GAS:  1,
  UPR:  1,
  LWR:  1,
  SEND: 100,
  READ: 1,
  CHN:  1,
  USR:  1,
  AT:   1,
  SLP:  5,
  EXIT: 0,
  DUMP: 5,
  RNG:  5,
  PID:  1,
  ALLW: 1,
  INT:  1,
  EMJI: 5,
  LEN:  1,
  NVAR: 1,
  ARBW: 1,
  ARBR: 1,
  NWLN: 1,
  HTTP: 20,
}

cmdStrGas = {}
cmdStrGas["LIT"] = cmdGases[LIT]
for k,v in cmdStrs.items():
  cmdStrGas[k] = cmdGases[v]

def parseCode(codeStr):
  code = []
  lbls = {}
  pc = 0
  for l in codeStr.split("\n")[1:]:
    if l == "" or l[0] == "#" or l[0] == "`":
      continue

    if l[-1] == ":" and l.find(" ") == -1:
      lbls[l[:-1]] = pc
      continue

    words = l.split(" ")
    thisProc = []
    if words[0].upper() == "LITINT":
      thisProc = [LIT, words[1], int(words[2])]
    elif words[0].upper() == "LITSTR":
      strStarts = 0
      for i in range(2):
        strStarts = l.find(" ",strStarts)+1
      thisProc = [LIT, words[1], l[strStarts:]]
    else:
      thisProc = [cmdStrs[words[0].upper()]] + words[1:]
    code += [thisProc]
    pc += 1

  return (code, lbls)

async def interpretCode(thisProc,startLbl,id,chn,msg,usr):
  code = thisProc["code"]
  lbls = thisProc["lbls"]
  vars = thisProc["vars"]
  if not startLbl in lbls: return
  pc = lbls[startLbl]
  consecOutOfGas = 0

  try:
    while True:
      cmd = code[pc]
      thisProc["gas"] -= cmdGases[cmd[0]]
      if thisProc["gas"] <= 0:
        thisProc["gas"] = 0
        await asyncio.sleep(10)
        consecOutOfGas += 10
        if consecOutOfGas >= TIME_KILL:
          del allProcs[id]
          break
        else:
          continue
      consecOutOfGas = 0

      if cmd[0] == LIT:
          vars[cmd[1]] = cmd[2]
      elif cmd[0] == MOV:
          vars[cmd[1]] = vars[cmd[2]]
      elif cmd[0] == ADD:
          if type(vars[cmd[1]]) == type("") and type(vars[cmd[2]]) == type("") and len(vars[cmd[1]]) + len(vars[cmd[2]]) > STRING_MAXSIZE:
            raise Exception("add operation exceeded max size")
            continue
          vars[cmd[1]] += vars[cmd[2]]
      elif cmd[0] == MUL:
          if type(vars[cmd[1]]) == type("") and type(vars[cmd[2]]) == type(0) and len(vars[cmd[1]]) * vars[cmd[2]] > STRING_MAXSIZE:
            raise Exception("add operation exceeded max size")
            continue
          vars[cmd[1]] *= vars[cmd[2]]
      elif cmd[0] == SBST:
          vars[cmd[1]] = vars[cmd[1]][vars[cmd[2]]:vars[cmd[3]]]
      elif cmd[0] == JMP:
          pc = lbls[cmd[1]]-1
      elif cmd[0] == JE:
          if vars[cmd[1]] == vars[cmd[2]]:
            pc = lbls[cmd[3]]-1
      elif cmd[0] == JG:
          if vars[cmd[1]] > vars[cmd[2]]:
            pc = lbls[cmd[3]]-1
      elif cmd[0] == STR:
          vars[cmd[1]] = str(vars[cmd[1]])
      elif cmd[0] == GAS:
          vars[cmd[1]] = thisProc["gas"]
      elif cmd[0] == UPR:
          vars[cmd[1]] = vars[cmd[1]].upper()
      elif cmd[0] == LWR:
          vars[cmd[1]] = vars[cmd[1]].lower()
      elif cmd[0] == SEND:
        if chn.id in thisProc["channels"]:
          await vars[cmd[1]].send("[" + str(id) + "] " + vars[cmd[2]])
          await asyncio.sleep(1)
      elif cmd[0] == READ:
          vars[cmd[1]] = msg
      elif cmd[0] == CHN:
          vars[cmd[1]] = chn
      elif cmd[0] == USR:
          vars[cmd[1]] = usr
      elif cmd[0] == AT:
          vars[cmd[1]] = vars[cmd[1]].mention
      elif cmd[0] == SLP:
          await asyncio.sleep(vars[cmd[1]])
      elif cmd[0] == EXIT:
          break
      elif cmd[0] == DUMP:
          vars[cmd[1]] = json.dumps(vars)[:STRING_MAXSIZE]
      elif cmd[0] == RNG:
          vars[cmd[1]] = random.randint(vars[cmd[2]],vars[cmd[3]])
      elif cmd[0] == PID:
          vars[cmd[1]] = id
      elif cmd[0] == ALLW:
          vars[cmd[1]] = 1 if (vars[cmd[2]].id in thisProc["channels"]) else 0
      elif cmd[0] == INT:
          vars[cmd[1]] = int(vars[cmd[1]])
      elif cmd[0] == EMJI:
          try:
            found = False
            for e in vars[cmd[2]].guild.emojis:
              if e.name == vars[cmd[1]]:
                found = True
                vars[cmd[1]] = str(e)
                break
            if not found:
              vars[cmd[1]] = ":"+vars[cmd[1]]+":"
          except Exception as e:
            vars[cmd[1]] = ":"+vars[cmd[1]]+":"
          vars[cmd[1]] = vars[cmd[1]][:STRING_MAXSIZE]
      elif cmd[0] == LEN:
          vars[cmd[1]] = len(vars[cmd[1]])
      elif cmd[0] == NVAR:
          vars[cmd[1]] = len(vars)
      elif cmd[0] == ARBW:
          if len(vars) < MAX_NVARS:
            vars[vars[cmd[1]]] = vars[cmd[2]]
      elif cmd[0] == ARBR:
          vars[cmd[1]] = vars[vars[cmd[2]]]
      elif cmd[0] == NWLN:
          vars[cmd[1]] = "\n"
      elif cmd[0] == HTTP:
          try:
            resp = requests.get(vars[cmd[1]], stream=True, timeout=30)
            vars[cmd[2]] = resp.status_code
            totalSize = 0
            vars[cmd[1]] = b''
            for chunk in resp.iter_content(1024):
              vars[cmd[1]] += chunk
              totalSize += 1024
              if totalSize > STRING_MAXSIZE:
                raise Exception("content is too long")
            vars[cmd[1]] = vars[cmd[1]].decode(resp.encoding)
          except Exception as e:
            vars[cmd[1]] = str(e)
            vars[cmd[2]] = -1

      pc += 1
  except Exception as e:
    await chn.send("Program {0} errored: {1}".format(id,str(e)))




client = discord.Client(activity = discord.Game("$help for more info"))

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

allProcs = {}
usedIds = {}
allowedProcs = {}

@client.event
async def on_message(message):
  if message.author == client.user:
    return
  elif message.content[:len("$addProc")] == "$addProc":
    thisProc = {}
    try:
      (thisProc["code"],thisProc["lbls"]) = parseCode(message.content)
    except Exception as e:
      await message.channel.send("Error parsing your code: " + str(e))
      return
    thisProc["vars"] = {}
    thisProc["gas"] = FULL_GAS
    thisProc["channels"] = { message.channel.id: True }
    thisProc["lastBan"] = -1
    id = str(len(usedIds))
    usedIds[id] = id
    allProcs[id] = thisProc
    if message.channel.id not in allowedProcs: allowedProcs[message.channel.id] = {}
    allowedProcs[message.channel.id][id] = True
    await message.channel.send("Started process id {0} with gas {1}".format(id,thisProc["gas"]))
    await interpretCode(thisProc,"start",id,message.channel,message.content[1:],message.author)
    while True:
      try:
        await asyncio.sleep(TIME_KILL)
        if len(thisProc["channels"]) == 0 and time.time() - thisProc["lastBan"] > TIME_KILL:
          del allProcs[id]
          break
      except:
        break
  elif message.content[:len("$refuel ")] == "$refuel ":
    id = message.content[len("$refuel "):]
    try:
      thisProc = allProcs[id]
    except KeyError as e:
      await message.channel.send("Invalid process number")
      return
    thisProc["gas"] = FULL_GAS
    await message.channel.send("Refueled process {0}'s gas to {1}".format(id,allProcs[id]["gas"]))
    await interpretCode(thisProc,"refueled",id,message.channel,message.content[1:],message.author)
  elif message.content == "$allowedList":
    if message.channel.id in allowedProcs:
      await message.channel.send("Processes allowed in this channel: {0}".format(str(list(allowedProcs[message.channel.id].keys()))))
    else:
      await message.channel.send("No processes allowed in this channel")
  elif message.content[:len("$allow ")] == "$allow ":
    id = message.content[len("$allow "):]
    try:
      thisProc = allProcs[id]
    except KeyError as e:
      await message.channel.send("Invalid process number")
      return
    thisProc["channels"][message.channel.id] = True
    if message.channel.id not in allowedProcs: allowedProcs[message.channel.id] = {}
    allowedProcs[message.channel.id][id] = True
    await message.channel.send("Allowed process {0} in this channel".format(id))
    await interpretCode(thisProc,"allowed",id,message.channel,message.content[1:],message.author)
  elif message.content[:len("$ban ")] == "$ban ":
    id = message.content[len("$ban "):]
    try:
      thisProc = allProcs[id]
    except KeyError as e:
      await message.channel.send("Invalid process number")
      return
    try:
      del thisProc["channels"][message.channel.id]
      del allowedProcs[message.channel.id][id]
      if len(allowedProcs[message.channel.id]) == 0:
        del allowedProcs[message.channel.id]
    except KeyError as e:
      await message.channel.send("Bot was already banned in this channel")
      return
    thisProc["lastBan"] = time.time()
    await message.channel.send("Banned process {0} in this channel".format(id))
    await interpretCode(thisProc,"banned",id,message.channel,message.content[1:],message.author)
  elif message.content[:len("$gas ")] == "$gas ":
    id = message.content[len("$gas "):]
    try:
      thisProc = allProcs[id]
    except KeyError as e:
      await message.channel.send("Invalid process number")
      return
    await message.channel.send("Process {0} has {1} gas".format(id,thisProc["gas"]))
  elif message.content == "$help":
    await message.channel.send("All commands and their gas prices: ```" + json.dumps(cmdStrGas) + "```")
    await message.channel.send("Rate limits: max string size **{0}**, max number of vars **{1}**, gas per refuel **{2}**, dead process kill time **{3}** seconds".format(STRING_MAXSIZE,MAX_NVARS,FULL_GAS,TIME_KILL))
    await message.channel.send("To start a process: $addProc \`\`\` (newline) code (newline) \`\`\`")
    await message.channel.send("Other commands: $allow [pid], $ban [pid], $allowedList, $gas [pid], $refuel [pid]")
    await message.channel.send("See https://github.com/samalws/discord-bot-asm/blob/main/README.md for more info")
  elif message.channel.id in allowedProcs:
    await asyncio.gather(*[interpretCode(allProcs[id],"msg",id,message.channel,message.content,message.author) for id in allowedProcs[message.channel.id].keys()])

client.run(os.environ["token"])
