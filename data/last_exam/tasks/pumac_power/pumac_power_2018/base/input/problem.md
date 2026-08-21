# PUMaC 2018 Power Round

PUMaC 2018 Power Round Page 1
PUMaC 2018 Power Round:
“Life is a game I lost...”
November 17, 2018
“The Game gives you a Purpose. The Real Game is, to Find a Purpose.” — Vineet
Raj Kapoor
Rules and Reminders
1. Your solutions may be turned in in one of two ways:
• You may email them to us at pumac2018power@gmail.com by 8AM Eastern
Standard Time on the morning of PUMaC, November 17, 2018 with the subject
line “PUMaC 2018 Power Round.”
• You may hand them in to us when your team checks in on the morning of
PUMaC. Please staple your solutions together, including the cover sheet.
The cover sheet (the last page of this document) should be the ﬁrst page of your
submission. Each page should have on it the team number (not team name) and
problem number. This number can be found by logging in to the coach portal and
selecting the corresponding team. Solutions to problems may span multiple pages,
but include them in continuing order of proof.
2. You are encouraged, but not required, to use L ATEX to write your solutions. If you
submit your power round electronically, you may not submit multiple times .
The ﬁrst version of the power round solutions that we receive from your team will be
graded. If submitting electronically, you must submit a PDF . No other ﬁle type
will be graded.
3. Do not include identifying information aside from your team number in your solutions.
4. Please collate the solutions in order in your solution packet. Each problem should
start on a new page, and solutions should be written on one side of the paper only
(there is a point deduction for not following this formatting).
5. On any problem, you may use without proof any result that is stated earlier in the
test, as well as any problem from earlier in the test, even if it is a problem that your
team has not solved. These are the only results you may use. You may not cite parts
of your proof of other problems: if you wish to use a lemma in multiple problems,
please reproduce it in each one.
PUMaC 2018 Power Round Page 2
6. When a problem asks you to “ﬁnd with proof,” “show,” “prove,” “demonstrate,” or
“ascertain” a result, a formal proof is expected, in which you justify each step you
take, either by using a method from earlier or by proving that everything you do is
correct. When a problem instead uses the word “explain,” an informal explanation
suﬃces. When a problem asks you to “ﬁnd” or “list” something, no justiﬁcation is
required.
7. All problems are numbered as “Problem x.y.z” where x is the section number and y is
the subsection. Each problem’s point distribution can be found in parentheses before
the problem statement.
8. You may NOT use any references, such as books or electronic resources,
unless otherwise speciﬁed. You may NOT use computer programs, calcu-
lators, or any other computational aids.
9. Teams whose members use English as a foreign language may use dictionaries for
reference.
10. Communication with humans outside your team of 8 students about the
content of these problems is prohibited.
11. There are two places where you may ask questions about the test. The ﬁrst is Piazza.
Please ask your coach for instructions to access our Piazza forum. On Piazza, you may
ask any question so long as it does not give away any part of your solution to
any problem. If you ask a question on Piazza, all other teams will be able to see it.
If such a question reveals all or part of your solution to a power round question, your
team’s power round score will be penalized severely. For any questions you have that
might reveal part of your solution, or if you are not sure if your question is appropriate
for Piazza, please email us at pumac@math.princeton.edu. We will email coaches with
important clariﬁcations that are posted on Piazza.
PUMaC 2018 Power Round Page 3
Introduction and Advice
The topic of this power round is Combinatorial Game Theory . A combinatorial
game is a special type of game that is not commonly discussed in a typical Game Theory
setting. Despite this, combinatorial games show up quite often; examples of complex combi-
natorial games include chess, go, and even tic-tac-toe. There are lots of unsolved questions
in combinatorial game theory, and games such as chess still do not have a (discovered)
optimal strategy.
Section 1 introduces you to a seemingly separate topic: surreal numbers. Although
this is just Section 1, a lot of the deﬁnitions are diﬃcult to grasp at ﬁrst because of their
recursive or inductive nature; do not worry. We gave a fairly lengthy dedication to this
section, so you will be quite comfortable with surreal numbers by the end of the section.
Section 2 is an introduction to combinatorial games. Despite a few diﬀerences, you will
notice many similarities between combinatorial games and surreal numbers. This section is
fairly deﬁnition heavy, and we spend some time introducing games such as Toads and Frogs
and Hackenbush.
Section 3 begins with a useful combinatorial game known as Nim. Next, you will learn
about the Sprague-Grundy Theorem, a very important theorem in combinatorial game
theory that links many games to Nim.
Section 4 provides some challenge problems on several combinatorial games. These
problems will require you to use the material of previous sections in addition to lots of your
own creativity.
This is not intended to be a complete course in Combinatorial Game Theory; in any
event, a contest is far from the best way to provide a complete undertaking. After the
Power Round is over, we advise you to read about topics from the round that interested
you. We can give you recommended books to read as well (see the solutions)!
Here is some further advice with regard to the Power Round:
• Read the text of every problem! Many important ideas are included in problems
and may be referenced later on. In addition, some of the theorems you are asked to
prove are useful or even necessary for later problems.
• Make sure you understand the deﬁnitions . As we stated above, a lot of the
deﬁnitions are not easy to grasp (especially in the Surreal Numbers section); don’t
worry if it takes you a while to understand them. If you don’t, then you will not be
able to do the problems. Feel free to ask clarifying questions about the deﬁnitions on
Piazza (or email us).
• Don’t make stuﬀ up: on problems that ask for proofs, you will receive more points
if you demonstrate legitimate and correct intuition than if you fabricate something
that looks rigorous just for the sake of having “rigor.”
• Check Piazza often! Clariﬁcations will be posted there, and if you have a question
it is possible that it has already been asked and answered in a Piazza thread (and
if not, you can ask it, assuming it does not reveal any part of your solution to a
question). If in doubt about whether a question is appropriate for Piazza,
please email us at pumac@math.princeton.edu.
PUMaC 2018 Power Round Page 4
Good luck, and have fun!
– Nathan Bergman & Jackson Blitz
We’d like to acknowledge and thank many individuals and organizations for their sup-
port; without their help, this Power Round (and the entire competition) could not exist.
Please refer to the solutions of the power round for full acknowledgments.
PUMaC 2018 Power Round Page 5
Contents
1 Surreal Numbers (93 points) 7
1.1 Deﬁning the Surreal Numbers (41 points) . . . . . . . . . . . . . . . . . . . 7
1.2 General Statements about Surreal Numbers (52 points) . . . . . . . . . . . 12
2 Introduction to Combinatorial Game Theory (63 points) 15
2.1 Combinatorial Game Deﬁnitions (3 points) . . . . . . . . . . . . . . . . . . 15
2.2 ˜G (22 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
2.3 G (38 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
3 Nim and the Sprague-Grundy Theorem (92 points) 23
3.1 Nim (18 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
3.2 Nim Variants (41 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
3.3 Sprague-Grundy (33 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
4 Speciﬁc Games & Questions (390 points) 26
4.1 Toads and Frogs (75 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
4.2 Partizan Splittles (90 points) . . . . . . . . . . . . . . . . . . . . . . . . . . 26
4.3 Wythoﬀ (225 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
PUMaC 2018 Power Round Page 6
Notation
• ∀: for all. ex.:∀x∈{ 1, 2, 3} means “for all x in the set {1, 2, 3}”
• A⊂B: proper subset. ex.:{1, 2}⊂{ 1, 2, 3}, but{1, 2}̸⊂{ 1, 2}
• A⊆B: subset, possibly improper. ex.:{1},{1, 2}⊆{ 1, 2}
• f :x↦→y: f maps x to y. ex.: if f(n) = n− 3 then f : 20↦→ 17 and f :n↦→n− 3
are both true.
• {x∈ S : C(x)}: the set of all x in the set S satisfying the condition C(x). ex.:
{n∈ N :√n∈ N} is the set of perfect squares.
• N: the natural numbers, {1, 2, 3,... }.
• Z: the integers.
• R: the real numbers.
• D: the dyadic rationals, { m
2n :m∈ Z,n∈ N∪{ 0}}.
PUMaC 2018 Power Round Page 7
1 Surreal Numbers (93 points)
The surreal numbers provide a recursive way to construct a number system. They have
many properties that will be useful in analyzing combinatorial games, so we investigate
them below. Our goal is to model the surreal numbers to emulate properties of the real
numbers.
1.1 Deﬁning the Surreal Numbers (41 points)
We deﬁne the surreal numbers recursively in stages called days, together with a strict total
ordering < between them at each stage. The idea is that every surreal number x will take
the form x ={L| R}, where L and R are any subset of surreal numbers appearing on
previous days, with every element of L less than every element of R, with respect to the
order relation deﬁned below. We denote Lx andRx to be the sets L andR ofx ={L|R},
respectively. Note Lx and Rx depend on the form of x ={L|R}. We also denote xL and
xR to be an arbitrary element of Lx andRx respectively. We deﬁne an order relation using
recursive deﬁnitions below.
Deﬁnition 1.1.A. For two surreal numbers x and y we let x≥y if and only if there does
not exist an element a∈ Rx such that a≤ y and there does not exist an element b∈ Ly
such that b≥x. Let x≤y if and only if y≥x.
Deﬁnition 1.1.B. Letx =y if and only if x≥y andy≥x. Let x>y if and only if x≥y
and y̸≥x. Let x<y if and only if y >x.
Deﬁnition 1.1.C. (The critical condition) For all a∈Lx and for all b∈Rx, a<x<b .
We make two important notes about the deﬁnitions above. First, it is important to note
that some surreal numbers can have more than one form depending on which elements are
in L and R (more on this later). Second, the deﬁnitions above are inductive, because to
show something is true for x and y, we have to assume statements about xL,x R,y L, and
yR. Note here xL denotes any element in Lx, with analogous notation for the other three
terms. In the same way, surreal numbers are “invented” inductively.
Deﬁnition 1.1.D. We say a number is born on day n if its earliest construction occurs on
dayn.
On day 0, we start with the single surreal number {|}, which we denote by 0. Then,
on the nth day, we introduce surreal numbers of the form x ={L|R}, where L and R are
any subset of surreal numbers appearing on any previous day, and for all a∈Lx and for all
b∈Rx, we have a<b .
0 satisﬁes the conditions for surreal numbers written above. 0 = {|}, so L0 =R0 ={}.
Hence, every element in L0 is less than every element in R0, which means 0 is a surreal
number.
Let us demonstrate some of our deﬁnitions. For example, 0 ≥ 0 because there is no
a∈R0 such that a≤ 0 and no b∈L0 such that b≥ 0.
0 is the only number born on day 0. Now that we deﬁned 0, for any new surreal
number x ={L| R} born on day 1, we have L and R can be either the empty set or
PUMaC 2018 Power Round Page 8
the set just containing 0. This enables us to create four potential new surreal numbers:
{|},{0|},{| 0},{0| 0}. Note that {|} is not a new surreal number, because we already
deﬁned 0 ={|}. Deﬁne ∗ to be{0| 0}.∗ contradicts the deﬁnition of the surreal numbers,
as 0∈L∗ and 0∈R∗, yet 0̸< 0. Hence, ∗ is not a surreal number. So on day 1, we have
two new surreal numbers, which we denote 1 ={0|} and−1 ={| 0}. You will prove that 1
and−1 satisfy the properties of surreal numbers later. We will now show that these three
surreal numbers follow the desired order of the real numbers: −1< 0< 1. First, note that
0̸≥ 1, because there exists a∈ L1 such that a≥ 0, namely a = 0. By a similar method,
we can show that 1≥ 0, and putting these two together we get that 1 > 0. You will prove
that−1< 0 and−1< 1 below.
On day 2, we now have a total of 8 sets to use for L andR:{},{−1},{0},{1},{−1, 0},
{0, 1},{−1, 1}, and{−1, 0, 1}. However, not all combinations of these will yield new surreal
numbers. We cannot have an element in a∈Rx that is less than or equal to an element in
b∈Lx, and we have a few repeat surreal numbers that were born on days 0 and 1. We also
end up with a few equivalent forms for certain surreal numbers (more on this later). For
example, on day 2, the following forms are all representative of the surreal number 0:
0 ={|} ={−1|} ={| 1} ={−1| 1}
The following forms are all representative of the surreal number we denote as −2 born
on day 2:
−2 ={|− 1} ={|− 1, 0} ={|− 1, 1} ={|− 1, 0, 1}
There are three other surreal numbers born on day 2, which we denote as follows:
2 ={1|} ={0, 1|} ={−1, 1|} ={−1, 0, 1|}
1
2 ={0| 1} ={−1, 0| 1}
−1
2 ={−1| 0} ={−1| 0, 1}
These surreal numbers satisfy their respective inequalities in the real numbers. The
assignments of certain surreal numbers like 2 and 1
2 above may seem arbitrary at the mo-
ment. However, these assignments will make sense in conjunction with the deﬁnitions of
operations on surreal numbers such as addition and multiplication deﬁned later.
In general, surreal numbers born on day n are of the form {L|R}, where L and R are
any subset of surreal numbers formed on day n− 1 satisfying the critical condition (which
includes both those surreal numbers born on day n− 1 and all surreal numbers born before
dayn− 1).
PUMaC 2018 Power Round Page 9
Problem 1.1.1. (5 points)
a) Prove for all surreal numbers x that a∈Lx implies a /∈Rx.
b) Prove that 1 is a surreal number.
c) Prove that −1 is a surreal number.
d) Demonstrate −1< 0.
e) Demonstrate −1< 1.
Now we shall deﬁne binary operations on the surreal numbers.
Deﬁnition 1.1.E. Let a surreal number x be positive if x> 0. Let a surreal number y be
negative if y <0.
Deﬁnition 1.1.F. Let−x ={−xR|−xL}.
Note thatxL andxR iterate through all ofLx andRx. For example, 2 ={0, 1|} ={1|}.
Because 0 =−0 (you will show this below), −2 ={|− 1, 0} ={|− 1}, which is consistent
with our deﬁnition of −2 above.
Deﬁnition 1.1.G. Deﬁne addition on surreal numbers as follows
x +y ={xL +y,x +yL|xR +y,x +yR}
Deﬁnition 1.1.H. Deﬁne subtraction on surreal numbers as x−y =x + (−y).
Deﬁnition 1.1.I. Deﬁne multiplication on surreal numbers as follows
x·y ={xLy +xyL−xLyL,x Ry +xyR−xRyR|xLy +xyR−xLyR,x Ry +xyL−xRyL}
We include these deﬁnitions of operations here so that you can conﬁrm that the place-
ment of surreal numbers such as 2 and 1
2 as they are deﬁned above indeed preserve the
arithmetic operations of the real numbers. You may also assume that multiplying or adding
a number by the empty set gives the empty set. Conﬁrm a few properties of the surreal
numbers below.
Problem 1.1.2. (5 points)
a) Demonstrate 0 = −0.
b) Demonstrate −1 =−(1), proving notation is consistent for −1.
c) Demonstrate 0 + 0 = 0.
d) Demonstrate 0 · 0 = 0.
e) Demonstrate 1 + 1 = 2.
PUMaC 2018 Power Round Page 10
To recap, 0 is born on day zero.−1 and 1 are born on day one.−2, 2,− 1
2, and 1
2 are born
on day two. We now generalize the surreal numbers born on day n. On day n, the greatest
possible surreal number x would have all the previously born surreal numbers in Lx, so on
dayn, the greatest possible surreal number is x, deﬁned as x =n ={0, 1, 2, 3,...,n − 1|}.
Similarly, the least surreal number born on dayn is−x =−n ={| 0,−1,−2,−3,..., −(n−
1)}, and the smallest positive surreal number on day n is 1
2n ={0| 1, 1
2, 1
4, 1
8,..., 1
2n−1}.
Deﬁnition 1.1.J. Letω denote the ﬁrst day after all ﬁnite days, and also let ω denote the
surreal number ω ={1, 2, 3,···|} .
As it turns out, many surreal numbers are born on day ω. For example, it can be shown
that 1
3 ={ 1
4, 1
4 + 1
16, 1
4 + 1
16 + 1
64,... | 1
2, 1
2− 1
8, 1
2− 1
8− 1
32,... }, and that it is born on day
ω. We also denote ϵ as ϵ = 1
ω.
The surreal numbers turn out to be actually well-deﬁned. Further, every real number
x∈ R has a representationx ={L|R} as a surreal number, including all rational, algebraic,
and transcendental numbers. In fact, many more numbers than just real numbers can be
surreal numbers, such as ω,−ω2,ω ω and many more.
It can often be confusing to determine the exact value of a surreal numberx based solely
on the sets ofLx andRx. If neither set contains any use of ω, the following set of conditions
can help determine x givenLx and Rx.
1. If Lx and Rx are both empty, then x = 0.
2. If Rx is empty and there is some smallest integer n≥ 0 greater than every element of
Lx, x is this integer n.
3. If Rx is empty and there is no integern greater than every element ofLx, thenx =ω.
4. If Lx is empty and there is some greatest integer n≤ 0 less than every element of Rx,
x is this integer n.
5. If Lx is empty and there is no integer n less than every element of Rx, then x =−ω.
6. If Lx and Rx are both non-empty and there exists some dyadic rational greater than
every element of Lx and less than every element of Rx, x is the oldest (i.e. born
earliest) such dyadic rational.
7. If Lx andRx are both non-empty and there does not exist some dyadic rational greater
than every element of Lx and less than every element of Rx, but there exists some
dyadic fractiony inLx that is greater than or equal to every element of Lx,x =y +ϵ.
8. If Lx andRx are both non-empty and there does not exist some dyadic rational greater
than every element of Lx and less than every element of Rx, but there exists some
dyadic fraction y in Rx that is less than or equal to every element of Rx, x =y−ϵ.
9. If Lx and Rx are both non-empty and every dyadic rational is greater than some
element of Rx or less than some element of Lx, then x cannot be represented as a
dyadic fraction. In this case, Lx andRx must both converge to the same number. To
calculate x, ﬁnd what Lx and Rx converge to (as in the example with 1
3 above).
PUMaC 2018 Power Round Page 11
For example, let x ={−3,−2, 1|}. Then Rx is empty but Lx is not, and there is a
smallest integer greater than every element of Lx (this integer is 2), so x = 2. This is
condition 2 from the 9 conditions above.
For another example, let x ={ 1
2, 2| 5} Then both Lx andRx are non-empty, and there
is an oldest dyadic rational greater than every element of Lx and less than every element
ofRx; in particular, 3 is the oldest such dyadic rational, so x = 3. This is condition 6 from
the 9 conditions above.
If one of the two sets contains a use of ω, you can view ω as a constant and treat the
problem the same as the cases without ω above. For example, {0,ω |} can be viewed as ω
times the surreal number{0, 1|} = 2, so{0,ω|} = 2·ω = 2ω.
Using the conditions of how to denote a surreal number by its representation, each
representation is assigned to a unique surreal number. This surreal number may have
inﬁnite diﬀerent representations, but it shares no representation with a distinct surreal
number.
In particular, every question asking to “ﬁnd” a value actually has a unique answer. It
should be noted that if a surreal number has a reduced form in its real number interpretation,
it should be written in it reduced form. For example, it can be shown 1
2≤ 2
4 and 2
4≤ 1
2, so
we have 1
2 = 2
4.
Problem 1.1.3. (5 points)
a) Find the value of x if x ={2, 6|}.
b) Find the value of x if x ={−10,−4| 3, 8}.
c) Find the value of x if x ={−1, 1
2| 2}.
d) Find the value of x if x ={−1, 1
2| 1, 2}.
e) Find the value of x if x ={− 5
8,− 5
16| −1
4, 7
2, 729
64}.
Problem 1.1.4. (6 points) Prove that a surreal number is born on a ﬁnite day if and only
if it is a dyadic rational.
Problem 1.1.5. (2 points) Prove that if a surreal number x is born on day n, where n> 0
and n is ﬁnite, then Lx or Rx contains a surreal number born on day n− 1.
Problem 1.1.6. (4 points)
a) Find the day the surreal number 2018 is born on.
b) Find the day the surreal number − 7
2 is born on.
c) Find the day the surreal number 21
8 is born on.
d) Find the day the surreal number 3
5 is born on.
Problem 1.1.7. (4 points) Ascertain the number of distinct surreal numbers born on or
before day n.
Problem 1.1.8. (6 points) Prove that π and e are both born on day ω.
PUMaC 2018 Power Round Page 12
Problem 1.1.9. (4 points)
a) Ascertain the value of {0| 1
ω}.
b) Ascertain the value of {0| 1
ω, 1
2ω, 1
4ω,... }.
1.2 General Statements about Surreal Numbers (52 points)
As was stated earlier, the deﬁnitions and construction of the surreal numbers rely on previ-
ous surreal numbers, so the proofs largely rely on induction. The form of inductive proofs
we discuss all involve reducing the problem to an empty set of conditions, so it is not nec-
essary to address a base case. As an example proof, consider the following proof of the
transitive property:
Theorem 1.2.I. If x≥y and y≥z, then x≥z.
Proof 1.2.1. x≥y implies there does not exist a∈Rx such that a≤y. We assume the
theorem holds for xR (for all in Rx),y, and z, so by induction we cannot have a∈Rx such
that a≤z. By a similar argument, we cannot have b∈Lz such that x≤b, so x≥z.
There are lots of properties of the surreal numbers that we want to prove. They were
constructed to behave like the real numbers, so we want to prove many of the properties
the real numbers have. We will now prove that the surreal numbers form an abelian group.
Deﬁnition 1.2.A. A group G is a set equipped with an operation · and a ﬁxed “identity”
elemente such that for all a,b,c ∈G
• a·b∈G.
• (a·b)·c =a· (b·c).
• a·e =e·a =a.
• There exists an element a−1∈G such that a·a−1 =a−1·a =e.
Deﬁnition 1.2.B. A group G is abelian if for all a,b∈G we havea·b =b·a.
Theorem 1.2.II. Commutative Property of Addition: x +y =y +x.
Proof 1.2.2. x +y ={xL +y,x +yL|xR +y,x +yR}. By induction, we know that the
pairs (xL,y ), (x,y L), (xR,y ), (x,y R) all satisfy commutativity, so
{xL +y,x +yL|xR +y,x +yR} ={y +xL,y L +x|y +xR,y R +x} =y +x
Problem 1.2.1. (4 points)
a) Prove −(−x) =x.
b) Prove that −(x +y) =−x + (−y).
PUMaC 2018 Power Round Page 13
Problem 1.2.2. (8 points)
a) (Additive Identity) Prove that x + 0 = 0 +x =x.
b) (Associative Law of Addition) Prove that ( x +y) +z =x + (y +z).
c) (Additive Inverse) Prove that x + (−x) = 0.
Problem 1.2.3. (13 points)
a) Show that x−xL> 0 and xR−x> 0.
b) Prove that if x> 0 and y >0 then x·y >0.
c) Show that our deﬁnition of multiplication is consistent by showing that ( x·y)L <
(x·y)< (x·y)R.
d) Prove that x≤y if and only if x +z≤y +z.
With these properties, we conclude that the surreal numbers with the operation addition
form an abelian group. Next, we will prove some nice properties about multiplication of
the surreal numbers.
Theorem 1.2.III. (Zero Multiplication) For all x, x· 0 = 0.
Proof 1.2.3. Every 0, 0L, and 0R term are 0 or the empty set, so we get thatx·0 ={|} = 0.
Theorem 1.2.IV. (Distributive Property) (x +y)z =xz +yz
Proof 1.2.4.
(x +y)z ={(x +y)Lz + (x +y)zL− (x +y)LzL,... |...} =
={(xL +y)z + (x +y)zL− (xL +y)zL,
(x +yL)z + (x +y)zL− (x +yL)zL,... |...} =
={(xLz +xzL−xLzL) +yz,xz + (yLz +yz L−yLzL),... |...}
=xz +yz
Problem 1.2.4. (15 points)
a) (Multiplicative Identity) Prove that x· 1 =x.
b) (Commutative Property) Prove that x·y =y·x.
c) (Negative Multiplication) Prove that (−x)y =x(−y) =−(x·y).
d) (Associative Property) Prove that ( x·y)z =x(y·z).
e) (Zero Product Property) Prove that x·y = 0 if and only if x = 0 or y = 0.
PUMaC 2018 Power Round Page 14
With these properties completed, we can conclude that the surreal numbers form a ring.
Lastly, we will show they form a ﬁeld by ﬁnding the inverse for a number x. If you do not
know what a ring or ﬁeld is, no need to worry. We will not ask about it.
We will now deﬁne one more useful term for operating on surreal numbers.
Deﬁnition 1.2.C. Letx be a positive surreal number. Deﬁne the multiplicative inverse of
x, alternatively denoted by x−1, to be
y =
{
0, 1 + (xR−x)yL
xR , 1 + (xL−x)yR
xL
⏐⏐⏐⏐⏐
1 + (xL−x)yL
xL , 1 + (xR−x)yR
xR
}
In the deﬁnition above, we use the notation a
b to denotea(b−1). Note that the deﬁnition
of y (like the deﬁnitions earlier) is inductive, so to ﬁnd the inverse of x, it is necessary to
know the inverses of xL,x R. You will now show that y is the inverse of x.
Problem 1.2.5. (12 points) In this problem, let y =x−1.
a) Show for all yL∈Ly and yR∈Ry that x·yL< 1<x ·yR.
b) Show that y is a surreal number.
c) Show for all ( x·y)L∈Lxy and (x·y)R∈Rxy that (x·y)L< 1< (x·y)R.
d) Show that x·y = 1.
Hence, the surreal numbers create an inductive representation of the real numbers. This
notion will be very useful in the next section while examining combinatorial games.
PUMaC 2018 Power Round Page 15
2 Introduction to Combinatorial Game Theory (63 points)
Combinatorial game theory is the study of all turn-based games with perfect information,
meaning all players know every possible move by the opponent and every previous event at
any time. To best understand the terminology in this section, it will be beneﬁcial to look
for similarities between combinatorial games and surreal numbers.
2.1 Combinatorial Game Deﬁnitions (3 points)
Deﬁnition 2.1.A. A (two-player) combinatorial game consists of a space of possible posi-
tions, together with a speciﬁcation of which positions each player can move to on their own
turn. The game ends if a player has no legal moves at some position.
Deﬁnition 2.1.B. A game is an individual position in a combinatorial game.
Confusingly, the individual positions are also called games, so a game (i.e. position) can
be written as G ={LG|RG}, where LG is the set of games that the left player can move
to, and RG is the set of games that the right player can move to. See Deﬁnition 2.1.J for
clarity on this notation and the left and right player.
Deﬁnition 2.1.C. Normal play is when the player who makes the last move wins. Mis´ ere
play is when the player who makes the last move loses.
Unless otherwise stated, normal play will be assumed.
Deﬁnition 2.1.D. Combinatorial games where both players have identical move sets are
impartial.
Deﬁnition 2.1.E. N-positions are when the ﬁrst player can guarantee a win. P -positions
are when the second player can guarantee a win.
N-positions and P -positions get their name from being good for the next player and
previous player, respectively.
Deﬁnition 2.1.F. A subgame of a game G is a game which can occur after some set of
moves are performed from G.
Deﬁnition 2.1.G. A game G is ﬁnite if it only has ﬁnite subgames.
Deﬁnition 2.1.H. A game G is loopfree if there does not exist a sequence of moves from
G that repeats a game.
Deﬁnition 2.1.I. A game G is short if it is ﬁnite and loopfree.
We note combinatorial games have a left player and a right player, each with a possi-
bly distinct set of moves, which coincide with the ﬁrst and second player, not necessarily
respectively.
Deﬁnition 2.1.J. We may write the Left and Right Options of a game G as LG and RG,
denoting the list of possibilities to move for the left and right player, respectively. We may
write G ={LG| RG}. We also denote GL and GR to be an arbitrary element of LG and
RG respectively.
PUMaC 2018 Power Round Page 16
Note the left player and right player are arbitrarily assigned to the players. Typically,
the left player is the ﬁrst player and the right player is the second player, but this is not
necessarily the case.
Deﬁnition 2.1.K. L-positions are when the left player can guarantee a win, no matter
who moves ﬁrst. R-positions are when the right player can guarantee a win, no matter who
moves ﬁrst.
Deﬁnition 2.1.L. G> 0 (G is positive) if there is a winning strategy for the Left player.
Deﬁnition 2.1.M. G< 0 (G is negative) if there is a winning strategy for the Left player.
Deﬁnition 2.1.N. G = 0 (G is zero) if there is a winning strategy for the second player.
Deﬁnition 2.1.O. G|| 0 (G is fuzzy) if there is a winning strategy for the ﬁrst player.
We also have G≥ 0 if G = 0 or G> 0 and G≤ 0 if G = 0 or G< 0. Now, we deﬁne a
particularly special game.
Deﬁnition 2.1.P. Denote by 0 the empty game with no options, 0 = {|}.
For an example of this notation, we deﬁne our ﬁrst combinatorial game.
Game Deﬁnition 2.1.I. Toads and Frogs is played on a 1 ×n strip of squares. At all
times, each square is either empty or occupied by a single toad or frog. The left player may
move a toad one square to the right if it is empty. If a frog occupies the space immediately
to a toad’s right, and the space immediately right of the frog is empty, the left player may
move the toad into that empty space. This move is called a “hop.” Toads may not hop over
more than one frog or another toad. Similarly, the right player may move frogs left in the
same fashion. The ﬁrst player to be unable to move loses (normal play).
If we have a game of Toads and Frogs G without any moves played so far on a 1 × 6
strip with a toad in the 1 st square and frogs in the 4 th and 6th squares, we will denote this
game as T F F. We will use this notation throughout the rest of the power round for
Toads and Frogs, withX n denoting any position X repeated n times side by side. We may
writeG ={T2|F3,F 5} whereT2 = T F F,F3 =T F F, and F5 =T F F .
Note that G does not know whose move it is, so even if G is only possible on one player’s
move (for example, the start of the game) we still write both.
Problem 2.1.1. (3 points) Prove which player can guarantee a win in Toad and Frogs
played on a 1× 6 strip with a toad in the 1 st square and frogs in the 4 th and 6th squares.
2.2 ˜G (22 points)
We can formally build a group ˜G of short games with rich structure. We can deﬁne some
useful sets formally.
Deﬁnition 2.2.A. Deﬁne ˜G0 ={0}. For n≥ 0, deﬁne
˜Gn+1 ={{LG|RG} :LG,R G⊆ ˜Gn}
PUMaC 2018 Power Round Page 17
Deﬁnition 2.2.B. Deﬁne ˜G =
⋃
n≥0
˜Gn. A game G is short if G∈ ˜G.
Deﬁnition 2.2.B formalizes the deﬁnition of a short game.
Problem 2.2.1. (10 points) Prove Deﬁnition 2.1.I and Deﬁnition 2.2.B are both equivalent
deﬁnitions of short games.
Recall that∗ was deﬁned to be{0| 0} in Section 1. Although∗ is not a surreal number,
it does in fact represent a combinatorial game: the game where both players only have the
option of moving to the 0 game. ∗ is an unconditional ﬁrst-player win, so it is an example
of a fuzzy game. ∗ is just one example of a combinatorial game that cannot be expressed
as a surreal number.
Problem 2.2.2. (2 points)
a) Explain why the 0 game is a 2 nd player win.
b) Explain why the ∗ game is a 1 st player win.
Problem 2.2.3. (4 points) (Fundamental Theorem) Let G be short and assume normal
play. Prove that either the left player can force a win playing ﬁrst or else the right player
can force a win playing second, but not both.
Before we continue, we should go on a slight digression explaining why the surreal
numbers were introduced before any of the theme of the power round. The surreal numbers
have a very close connection to combinatorial game theory. Games are represented in the
same form{L|R} as surreal numbers. Every surreal number denoted by a real number is a
game. However, not every game is a surreal number, as games need not satisfy the critical
condition.
Nevertheless, the theory of surreal numbers prove to be helpful in examining games.
We shall deﬁne addition and negation of short games exactly as surreal numbers. All short
games turn out to be represented by a dyadic rational, which makes sense as short games
are ﬁnite and dyadic rationals are born on a ﬁnite day.
Hence, in proofs from now on, where appropriate, one may reference the theory of surreal
numbers.
We now introduce Hackenbush as an application of the concepts above.
Game Deﬁnition 2.2.I. The game of Hackenbush starts with a line on the ground and
a ﬁnite series of red and blue line segments (some connected to each other) all connected
either directly or indirectly to the ground line. Two players take turns removing segments
of their corresponding color (the Left player moves ﬁrst and can only remove blue segments,
the Right player can only remove red segments). At the end of a turn, any segments no
longer connected to the ground are also removed. The ﬁrst person who cannot delete a
segment on their turn loses. Note that some variants of Hackenbush include green line
segments both players can remove, and in some variants all line segments are removable by
both players, but we do not consider those forms here.
The simplest Hackenbush game is just the line on the ground. In this variant, neither
player has any moves to make, soLG =RG ={}. As was the case with the surreal numbers,
the empty game is the 0 game. A couple other examples of Hackenbush games are displayed
below.
PUMaC 2018 Power Round Page 18
Problem 2.2.4. (4 points)
a) Is Hackenbush a game of normal play or mis´ ere play?
b) Is Hackenbush an impartial game?
c) Prove that Hackenbush is a short game.
Deﬁnition 2.2.C. If G and H are short games, then we deﬁne the disjunctive sum as
G +H ={GL +H,G +H L|GR +H,G +H R}
The disjunctive sum is clearly commutative and associative. Note that the disjunctive
sum of short games is a short game.
Deﬁnition 2.2.D. LetG be short. Then deﬁne the negation of G by−G ={−GR|−GL}.
For example, in the game of Hackenbush, the game −G is obtained by turning all red
lines blue and all blue lines red. Note that G is a short game if and only if −G is a short
game.
Problem 2.2.5. (2 points)
a) Prove for any short game G we have−(−G) =G.
b) Evaluate ∗ +∗.
2.3 G (38 points)
Deﬁnition 2.3.A. Denote byo(G) the outcome of the game G, which by the fundamental
theorem exists as one of four options for short games: a ﬁrst player win, a second player win,
a left player win, or a right player win (meaning G is a N-position, P -position, L-position,
or R-position, respectively).
Deﬁnition 2.3.B. ForG,H ∈ ˜G, we say G =H if o(G +X) =o(H +X) for all X∈ ˜G.
Deﬁnition 2.3.C. An equivalence relation∼ satisﬁes for all a,b,c
• a∼a.
• a∼b if and only if b∼a.
• If a∼b and b∼c then a∼c.
Problem 2.3.1. (3 points) Prove that = (in the context of games) is an equivalence relation.
Deﬁnition 2.3.D. The game value ofG is its equivalence class modulo =. The set of game
values is G. For notational convenience, we will sometimes use G to denote both a game
and its corresponding game value when this introduces no ambiguity.
Problem 2.3.2. (6 points) Let G be an impartial game. Prove G is equivalent to 0 if and
only if G is a P -position.
PUMaC 2018 Power Round Page 19
Problem 2.3.3. (5 points) Prove G is an abelian group under addition.
We will now delve deeper into the notion of game value by using the combinatorial game
of Hackenbush. As the name suggests, the 0 game (discussed earlier) has value G = 0.
To construct more complicated games of Hackenbush, we use a similar approach to our
construction of the surreal numbers.
In Hackenbush Figure 1, Left player can delete the blue edge, creating the 0 game, while
Right player has no moves. So LG ={0},R G ={} and the game in Figure 1 corresponds to
valueG ={0|} = 1, because the surreal number {0|} = 1. In Hackenbush Figure 2, Left
player can delete the top blue edge, creating the game 1, or the bottom blue edge, creating
the 0 game. Right player still has no moves, so this game has value G ={0, 1|} = 2.
In Hackenbush Figure 3, Left player can delete the blue edge, creating the game −1,
and Right player can delete the red edge, creating the game 1. So this game has value
G ={−1| 1} = 0, which is another game of value 0. Note that this game is essentially two
diﬀerent games: the game of one red line (which has value −1) and the game of one blue
line (which has value 1); it is no coincidence that 1 + ( −1) = 0, the value of the combined
game. Generally speaking, if G1 and G2 are the values of two games, then the combined
game has value G1 +G2.
PUMaC 2018 Power Round Page 20
In general, the game value can say a lot about who is likely to win the game. If G> 0,
then there is a winning strategy for the Left player. If G < 0, then there is a winning
strategy for the Right player. If G = 0, then depending on the game either player could
win. Games can have fractional values as well. For example, consider the games below.
In Hackenbush Figure 4, Left player’s only move is to delete the blue edge, creating the
game 0, and Right player can delete the red edge, creating the game -1. So G ={0|1} = 1
2.
For our last example, we look at a game where the values must be found recursively, in the
same way that surreal numbers born on day n are formed from numbers born earlier. In
Hackenbush Figure 5, left player’s only move is to create game 0. Right player has three
possible lines to remove, but each leaves the same game G′: two red lines connected to the
blue line. The value of G′ is not immediately obvious: for this game, left player can create
game 0, while right player can create the game with one red line on top of one blue line
(which is Hackenbush Figure 4 and has value 1
2. So G′ ={0| 1
2} = 1
4, and G ={0| 1
4} = 1
8.
PUMaC 2018 Power Round Page 21
Problem 2.3.4. (2 points) Demonstrate the game value of Hackenbush Game 1 below.
Problem 2.3.5. (2 points) Demonstrate the game value of Hackenbush Game 2 below.
Problem 2.3.6. (4 points) Demonstrate the game value of Hackenbush Game 3 below.

PUMaC 2018 Power Round Page 22
Problem 2.3.7. (3 points) Demonstrate the game value of Hackenbush Game 4 below.
Problem 2.3.8. (5 points) Demonstrate the game value of Hackenbush Game 5 below.
Problem 2.3.9. (8 points) Demonstrate the game value of Hackenbush Game 6 below.

PUMaC 2018 Power Round Page 23
3 Nim and the Sprague-Grundy Theorem (92 points)
3.1 Nim (18 points)
Nim is quite possibly the canonical combinatorial game in the topic of combinatorial game
theory.
Game Deﬁnition 3.1.I. In Nim two players are presented with an arbitrary number of
piles of arbitrary numbers of tokens. On their turn, a player may take as many tokens as
they wish from any one pile. Whoever removes the last token wins.
Note that Nim is the disjunctive sum of its heaps. Now we present some deﬁnitions
about the classic game.
Deﬁnition 3.1.A. The nim-sum of two nonnegative integers a and b is denoted by a⊕b
and is obtained by “adding without carrying”/“exclusive or” in binary.
For example, 5⊕ 7 = 1012⊕ 1112 = 0102 = 2.
Deﬁnition 3.1.B. The nim-value of a game of NimG isa1⊕a2⊕...⊕an wherea1,a 2,...,a n
are the size of the token piles in G.
Problem 3.1.1. (4 points)
a) Find the nim-value of a game of Nim with piles of token size 5 , 6, 2, 9, and 2018.
b) Find the nim-value of a game of Nim with 2018 piles of token size 2018.
Deﬁnition 3.1.C. G is a zero position if its nim-value is 0.
These deﬁnitions allow for an easy formulation of the general winning strategy of the
game of Nim, with the help of a powerful theorem.
Problem 3.1.2. (6 points) (Bouton’s Theorem) Let G be a Nim position. Prove that if G
is a zero position, then every move from G leads to a nonzero position. Prove that if G is
a nonzero position, then there exists a move from G to a zero position.
Problem 3.1.3. (4 points) Find with proof the N-positions and P -positions of Nim.
Deﬁnition 3.1.D. A nimber is the game of Nim of a single heap of size n, and is denoted
by∗n. Note 0 = ∗0 and let∗ denote∗1.
Note∗n ={0,∗,∗2,..., ∗(n− 1)| 0,∗,∗2,..., ∗(n− 1)}.
Problem 3.1.4. (4 points) Prove for all a,b∈ N we have∗a +∗b =∗(a⊕b).
PUMaC 2018 Power Round Page 24
3.2 Nim Variants (41 points)
Problem 3.2.1. (5 points) In a game of mis´ ere nim, ﬁnd with proof the N-positions and
P -positions (recall the deﬁnition of mis´ ere from a previous section).
Game Deﬁnition 3.2.I. Triple Nim is played with the same rules as Nim, except a player
may take from up to three piles (and at least one pile), rather than just one. The player
may remove an arbitrary number from each pile.
Problem 3.2.2. (8 points) Find with proof theN-positions andP -positions of normal play
Triple Nim.
Problem 3.2.3. (4 points) Find with proof the N-positions and P -positions of mis´ ere play
Triple Nim.
Game Deﬁnition 3.2.II. In (n,r )-Nim there is only one pile of n coins. Each player can
take up to r coins from the pile.
Problem 3.2.4. (5 points) Find with proof theN-positions andP -positions of normal play
(n,r )-Nim.
Problem 3.2.5. (5 points) Find with proof the N-positions and P -positions of mis´ ere play
(n,r )-Nim.
Game Deﬁnition 3.2.III. In Tiger Nim there is only one pile of coins. The ﬁrst player
may take up to all but one of the coins on the ﬁrst turn. Every subsequent move can remove
up to twice the number of coins taken on the previous move.
Problem 3.2.6. (12 points) Find with proof the N-positions and P -positions of normal
play Tiger Nim.
Problem 3.2.7. (2 points) Find with proof the N-positions and P -positions of mis´ ere play
Tiger Nim.
3.3 Sprague-Grundy (33 points)
Before introducing the incredible Sprague-Grundy Theorem, we present a lemma to prove
the ubiquitous result.
Problem 3.3.1. (10 points) For every short impartial games G,G′, we haveG =G′ if and
only if G +G′ is a P -position.
We now provide a very useful operation to help prove a lemma of the Sprague-Grundy
Theorem and some later problems in the power round.
Deﬁnition 3.3.A. For a setS⊂ N∪{0}, we deﬁne the mex of S (minimal excluded value),
denoted mex(S), as the least integer m∈ N∪{ 0} such that m̸∈S.
Problem 3.3.2. (8 points) Leta1,a 2,...,a k∈ N∪{0}, and suppose thatG ={∗a1,∗a2,..., ∗ak|
∗a1,∗a2,..., ∗ak}. Prove that G =∗m, where m =mex{a1,a 2,...a k}.
PUMaC 2018 Power Round Page 25
And now the main theorem.
Problem 3.3.3. (6 points) (Sprague-Grundy Theorem) Every short impartial game under
the normal play convention is equivalent to a nimber.
The Sprague-Grundy Theorem is quite powerful in the analysis of short impartial games.
In general, we can compare short impartial games with a nimber to understand its proper-
ties.
Deﬁnition 3.3.B. For a short impartial game G equivalent to the nimber ∗n, let the
G-value of G be n.
Note the G-value is not equal to the game value.
Game Deﬁnition 3.3.I. Dawson’s Kayles consists of at least one row of connected boxes.
On a player’s turn, they remove two adjacent boxes from a single row, possibly disconnecting
it (and splitting it into two smaller rows), or remove one box of their choosing. The ﬁrst
person who cannot move loses.
Problem 3.3.4. (9 points) Find the G-values for a game of Dawson’s Kayles consisting of
one row of n boxes for each integer n from 0 to 17.
PUMaC 2018 Power Round Page 26
4 Speciﬁc Games & Questions (390 points)
4.1 Toads and Frogs (75 points)
Recall the game Toads and Frogs is presented as the ﬁrst combinatorial game in the power
round (Game 3.2.1).
Problem 4.1.1. (10 points) Find with proof the game value of
T F T F F F T T T F F T F F T T.
Problem 4.1.2. (20 points) Prove (T F) mT (T F) n has game value 2−n for all m,n∈
N∪{ 0}.
Problem 4.1.3. (20 points) Prove for every dyadic rational q, there exists a Toads and
Frogs game with game value q.
Problem 4.1.4. (25 points) Prove no matter whether the left or right player moves ﬁrst,
the game T n F F has game value 0 for all n≥ 2.
4.2 Partizan Splittles (90 points)
Game Deﬁnition 4.2.I. In Partizan Splittles, each position consists of a number of heaps
of tokens, and with each move, a player removess tokens from one heap and can optionally
split the remaining heap into two heaps. Additionally, two sets of positive integers SL and
SR are ﬁxed in advance, and the amount of tokens s the Left player can remove on a turn
must be in SL, and for Right the amount must be in SR.
Of course, depending on the sets SL and SR, this game can take on diﬀerent values.
We analyze a few of the scenarios below. In these scenarios, we use Gn to denote the game
value of a Partizan Splittles game played on n heaps.
Problem 4.2.1. (5 points) Prove that ifSL ={1,a 1,a 2,...,a j} andSR ={1,b 1,b 2,...,b k},
where each ai and each bi is a positive odd integer, then
Gn =
{
0 if n is even
∗ if n is odd
Problem 4.2.2. (15 points) Prove that if SL ={1} and SR ={k}, where k is a positive
odd integer, then
Gn =
{
n if n<k
{k− 1| 0} +Gn−k if n≥k
Problem 4.2.3. (50 points) Consider SL and SR with the properties that 1 ∈ SL and
SR ={1, 3, 5,..., 2k + 1} for some integer k or SR ={1, 3, 5,...} (i.e. all odd integers).
a) Prove that Gn≤Gn+2.
b) Prove that G2n+1 =G2n +∗.
c) Prove that if SR is ﬁnite and n−i−j≥ 2k is even then Gn≤Gi +Gj.
Problem 4.2.4. (20 points) Let n be odd and let Hn be the game where SL ={1} andSR
is the set of even integers. Prove that Hn+1−Hn< 1 and Hn−Hn−1 = 1.
PUMaC 2018 Power Round Page 27
4.3 Wythoﬀ (225 points)
Game Deﬁnition 4.3.I. In Wythoﬀ, there are two piles of coins. On a given turn, a player
may either remove as many tokens from one pile as they wish or they may remove the same
number of tokens from both piles. The winner is the one who removes the last coin.
For example, if we have a pile of 4 and 6 coins, then the ﬁrst player can take away 3
from both piles leaving 1 and 3. The second player can then take away 3 from the second
pile leaving just 1 coin. The ﬁrst player then removes the last coin and wins.
Before we continue, we introduce an important and relevant result from number theory.
Problem 4.3.1. (10 points) Let A ={⌊nr⌋ :n∈ N} andB ={⌊ns⌋ :n∈ N} for some real
numbers r and s. Prove A∪B = N and A∩B =∅ if r >0 and s >0 are two irrational
numbers such that 1
r + 1
s = 1.
Now, we have the main and intriguing result of the traditional Wythoﬀ Game.
Problem 4.3.2. (20 points) Let φ = 1+
√
5
2 . Prove that a P -position of Wythoﬀ is a pair
of piles with sizes given by the unordered pair (⌊nφ⌋,⌊nφ2⌋) for some n∈ N.
We present further results involving G-values and Wythoﬀ’s Game.
Problem 4.3.3. (20 points) Prove that every G-value n appears exactly once among all
ordered pairs of piles with the ﬁrst pile of any given, ﬁxed size.
Problem 4.3.4. (25 points) Let r > 0. r-Wythoﬀ is played with two piles of tokens.
On their turn, a player may either remove as many tokens from one pile as they wish, or
removea tokens from one pile and b from the other, where |a−b|<r . Prove that the nth
P -position of r-Wythoﬀ is given by (an,b n) = (⌊nα⌋,⌊nβ⌋) where α = 1
2(2−r +
√
r2 + 4)
and, β =α +r.
We give a nice theorem and useful deﬁnitions to solve the ﬁnal problem.
Deﬁnition 4.3.A. LetTj be the sequence of all pairs (a,b ),a≤b, of nonnegative integers
such that the Wythoﬀ game of those pile sizes has game value j. This sequence is of the
form{(a0,b 0), (a1,b 1),... } whereai is increasing (It actually can be proven (and used) that
it is strictly increasing). Let Aj ={a0,a 1,... } and similarly for Bj.
Deﬁnition 4.3.B. Let d1≥− 1 be an integer satisfying
{j : 0≤j≤d1} ={bj−aj : 0≤j≤d1}
The set of all pairs (ai,b i)∈T1 for which there is an integer d2>d 1 satisfying
{i :d1<i ≤d2} ={bi−ai :d1<i ≤d2}
{i :d1<i ≤d}̸ ={bi−ai :d1<i ≤d}
for everyd withd1<d<d 2, is called an integral. The size of the above integral isd2−d1+1.
PUMaC 2018 Power Round Page 28
Theorem 4.3.I. If
{i : 0≤i≤d} ={bi−ai : 0≤i≤d}
where ai∈ A1 and bi∈ B1, then the same holds for d replaced by d +j for some j ∈
{1, 2, 3, 4, 5, 6}.
You can take this theorem for granted.
Deﬁnition 4.3.C. B′
1 ={b′
0,b′
1,... } be the members of B1 in sorted order (least to great-
est).
Note: the last problem is very diﬃcult, and we do not expect many teams to solve it.
Grading will be similar to Olympiad grading, where scores will be clustered toward close to
0 points and close to full points.
Problem 4.3.5. (150 points) Let φ = 1+
√
5
2 . Prove that
8− 6φ<a n−φn< 6− 3φ
and
2− 3φ<b ′
n−φ2n< 6− 3φ
for an∈A1 and b′
n∈B′
1.
This problem implies the pairs of piles of G-value 1 are really close to those of G-value
0, a cool result.
Team Number:
PUMaC 2018 Power Round Cover Sheet
Remember that this sheet comes ﬁrst in your stapled solutions. You should submit
solutions for the problems in increasing order. Write on one side of the page only. The
start of a solution to a problem should start on a new page. Please mark which questions
for which you submitted a solution to help us keep track of your solutions.
Problem Number Points Attempted?
1.1.1 5
1.1.2 5
1.1.3 5
1.1.4 6
1.1.5 2
1.1.6 4
1.1.7 4
1.1.8 6
1.1.9 4
1.2.1 4
1.2.2 8
1.2.3 13
1.2.4 15
1.2.5 12
2.1.1 3
2.2.1 10
2.2.2 2
2.2.3 4
2.2.4 4
2.2.5 2
2.3.1 3
2.3.2 6
2.3.3 5
2.3.4 2
2.3.5 2
2.3.6 4
2.3.7 3
2.3.8 5
2.3.9 8
Problem Number Points Attempted?
3.1.1 4
3.1.2 6
3.1.3 4
3.1.4 4
3.2.1 5
3.2.2 8
3.2.3 4
3.2.4 5
3.2.5 5
3.2.6 12
3.2.7 2
3.3.1 10
3.3.2 8
3.3.3 6
3.3.4 9
4.1.1 10
4.1.2 20
4.1.3 20
4.1.4 25
4.2.1 5
4.2.2 15
4.2.3 50
4.2.4 20
4.3.1 10
4.3.2 20
4.3.3 20
4.3.4 25
4.3.5 150
Total 638
