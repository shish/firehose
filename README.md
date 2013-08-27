firehose
========

GPG-based chat client

Protocol:
```
 * connect to firehose.shishnet.org:9988
 * send packets, receive packets

 * packet =
   * unsigned short: length of data
   * byte[$length]: GPG-encrypted message

 * message =
   * cmd data

 * cmds:
   * MSG <text>
   * ACT <text>
   * PING
   * PONG <status>
```

If the GPG message is signed, and the recipient has your public key, you'll
show up in a window of your own at their end; if not, you'll show up as
"Unknown". This is pretty much using your GPG keyring as an IM buddy list.


Notes
-----
I am not a cryptographer, this is an experiment, don't bet your life on it.

Why?
----
Because the people on Hacker News keep pointing out the same flaws in all
sorts of supposedly secure systems; I want to fix those, so that they can
have a different set of flaws to complain about :P

Firstly, I haven't rolled my own encryption, I'm using GPG and leaving the
settings at what I presume are sane defaults.

Encrypted email still has "To:" and "From:" in clear text, which is enough
to get you in trouble. The firehose is broadcast, so everyone gets all
messages, you can't tell who's talking to who from the headers.

Traffic analysis (A sends a message, then B sends a message, then A sends a
message) would allow an attacker to infer that those two people are chatting.
To combat this, clients send a constant ~1kbps stream of data 24/7 - small /
empty messages are padded with random[1] data, large messages are buffered
and dripped out slowly. (Not implemented yet.)

[1] does encrypted random data look like encrypted real data? If the data
is compressed before encryption, then real data would be shorter than random.

