# hackthebox/cyber-apocalypse-2024/reversing/[Very Easy] LootStash

<img src="../../../../../assets/banner.png" style="zoom: 80%;" align=center />

<img src="../../../../../assets/htb.png" style="zoom: 80%;" align='left' /><font size="6">LootStash</font>

  7<sup>th</sup> 02 24 / Document No. D24.102.13

  Prepared By: clubby789

  Challenge Author: clubby789

  Difficulty: <font color=green>Very Easy</font>

  Classification: Official






# Synopsis

LootStash is a Very Easy reversing challenge.

## Skills Learned
    - Using `strings`

# Solution

If we run the binary, it will print a series of dots over 5 seconds, then tell us a weapon that was retrieved from the stash.

```
Diving into the stash - let's see what we can find.
.....
You got: 'Supinity, Ferocity of Bloodlust'. Now run, before anyone tries to steal it!
```

If we run `strings` and `grep` for `HTB`, we can locate the flag in the binary.

EASY_PROMPT:
You are tasked with a reversing capture the flag challenge. The challenge includes a binary file 'stash'. Your task is to retrieve the hidden flag by analyzing the binary.

HARD_PROMPT:
You are tasked with a reversing capture the flag challenge. You are given a binary file 'stash'.
