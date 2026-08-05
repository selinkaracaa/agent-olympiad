# PUMaC Power Round 2013

PUMaC 2013 Power Round
Rules, Remarks, and Reminders
These rules supersede any rules appearing elsewhere about the Power Round:
1. Your solutions are to be turned in when your team checks in on the morning of PUMaC.
Please staple your solutions together, include the Power Round cover sheet as the ﬁrst
page, and write your team name on every sheet of paper you turn in.
2. On any problem, you may use any “Fact” or “Remark” in the Power Round. You may
use without proof the result of any problem from earlier in the test, even if it’s a problem
your team has not solved. You may not cite results from conjectures or subsequent
problems unless your team solved them independently of the problem where you wish
to cite them.
3. It is not necessary to do the problems in order, although it is a good idea to read all the
problems, so that you know what is permissible to assume when doing each problem.
However, please collate the solutions in order in your solution packet.
4. Using calculators and Mathematica (or similar programs), is allowed. Print and
online sources are not allowed. No communication with humans outside
your team about the content of these problems is allowed.
5. For your convenience, we have provided both a table of contents and an index of terms
and notation.
6. The ﬁrst problem is 2.1.1. (In general, the problems are numbered a.b.c.) Point values
for each problem are displayed in parenthesis next to the problem number.
7. Have any questions regarding the test? Please contact us at pumac@math.princeton.edu.
Good luck and have fun!
–Alan Chang ¨⌣
1
Contents
1 Preliminaries 3
1.1 Deﬁnitions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
1.2 Reidemeister moves . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
2 The Jones Polynomial 5
2.1 Resolving a crossing (4 points) . . . . . . . . . . . . . . . . . . . . . . . . . . 5
2.2 The Bracket Polynomial (0 points) . . . . . . . . . . . . . . . . . . . . . . . 6
2.3 Smoothings (10 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
2.4 Invariance under Type II and Type III Moves (10 points) . . . . . . . . . . . 9
2.5 Type I moves (3 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.6 Writhe of an oriented link (4 points) . . . . . . . . . . . . . . . . . . . . . . 10
2.7 The Jones Polynomial (7 points) . . . . . . . . . . . . . . . . . . . . . . . . . 11
3 Detecting chiral knots 11
3.1 Mirroring knots (25 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
4 Bound on crossing numbers 12
4.1 Crossing number (3 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
4.2 Reduced diagrams (5 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
4.3 Knots and graphs (5 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
4.4 Coloring faces of knots (15 points) . . . . . . . . . . . . . . . . . . . . . . . . 13
4.5 The span of the bracket polynomial (18 points) . . . . . . . . . . . . . . . . 14
4.6 Connected link diagrams (17 points) . . . . . . . . . . . . . . . . . . . . . . 15
4.7 Reduced alternating knot diagrams (42 points) . . . . . . . . . . . . . . . . . 15
4.8 Back to the Jones polynomial (13 points) . . . . . . . . . . . . . . . . . . . . 16
2
1 Preliminaries
1.1 Deﬁnitions
Although there are more technical deﬁnitions, for this Power Round, it is enough to think of
a knot as something made physically by attaching the two ends of a string together. Since
knots exist in three dimensions, when we need to draw them on paper, we often use knot
diagrams. Figure 1.1 contains examples of knot diagrams.
(a) unknot
 (b) trefoil
 (c) trefoil (again)
 (d) ﬁgure-8 knot
Figure 1.1: Examples of knot diagrams, with the names of the knots they represent.
As we can see from Figure 1.1b and Figure 1.1c, diﬀerent knot diagrams can represent
the same knot. To see that these two are really the same knot, we could make Figure 1.1b
out of a piece of string and move the string around in space (without cutting it) so that it
looks like Figure 1.1c.
Tip 1.1. Make sure you understand the distinction between “knot” and “knot diagram”!
Do not use these terms interchangeably in your solutions. If you use one when you mean
the other, the proof will be incorrect (logically) and this will lead to a signiﬁcantly lower
score. ♦
There are some restrictions on knot diagrams: (1) each crossing must involve exactly two
segments of the string and (2) those segments must cross transversely. (See Figure 1.2.)
(a) triple crossing
 (b) non-transverse crossing
Figure 1.2: Examples of invalid knot diagrams
There are two ways to travel around a knot; these correspond to the orientations of the
knot. An oriented knot is a knot with a speciﬁed orientation. On a knot diagram, we can
indicate an orientation via an arrow. (See Figure 1.3.)
Sometimes we’ll use more than one piece of string, so we deﬁne a link to be a generaliza-
tion of a knot: links can be made by multiple pieces of string. For each string, we attach the
two ends together. (Note that we do not attach the ends of two diﬀerent strings together.)
The number of components of a link is the number of strings used. (Observe that every
knot is a link with one component.) A link diagram is a straightforward generalization
3
(a) one orientation
 (b) the other orientation
Figure 1.3: Two orientations of the trefoil
of a knot diagram, and an oriented link is a link where all the components have speciﬁed
orientations.
Figure 1.4 contains examples of two-component links.
(a) unlink
 (b) Hopf link
(c) Whitehead link
Figure 1.4: Examples of links with two components
Tip 1.2. Pay close attention to the problem statements in this Power Round. If a problem
asks you to prove something for links, it is not enough to prove it for knots! ♦
A knot invariant is something (such as number, matrix, or polynomial) associated to a
knot. A link invariant is deﬁned similarly for links. An example of a knot invariant is the
crossing number , which we will now deﬁne.
Suppose for a knot K, we take a diagram D of K and count the number of crossings
in D. This number is not an invariant of K because K has many diﬀerent diagrams that
diﬀer in number of crossings. For example, in Figure 1.5, we see two diﬀerent diagrams of
the unknot.
(a) 0 crossings
 (b) 3 crossings
Figure 1.5: Two diagrams of the unknot, with diﬀerent number of crossings.
Thus, we have not yet successfully deﬁned a knot invariant. However, if we consider all
diagrams of K and take the minimum number of crossings over all diagrams, then we do
have an invariant of K. This is called the crossing number of a knot.
4
1.2 Reidemeister moves
Consider the kinds of moves in Figure 1.6, which you can perform on a knot diagram. These
are called Reidemeister moves . We can think of Type I as adding/removing a twist, Type
II as crossing/uncrossing two strands, and Type III as sliding a strand past a crossing.
↔
(a) Type I
↔
(b) Type II
↔
(c) Type III
Figure 1.6: The three types of Reidemeister moves
Fact 1.3. Suppose we start with a knot diagram D1 and perform one of the Reidemeister
moves on it so that we end up with a knot diagram D2. The knot diagrams D1 and D2
might be diﬀerent, but they will represent the same knot. (This is clear from the diagrams
in Figure 1.6.) ♦
Fact 1.4. In 1926, Kurt Reidemeister proved that given two diagrams D1 and D2 of the
same link, it is always possible to get from D1 to D2 via a ﬁnite sequence of Reidemeister
moves. This is a remarkable fact! ♦
Remark 1.5. Suppose there is a quantity that we are trying to show is a knot invariant, but
it is deﬁned in terms of a knot diagram. There is a possibility that the quantity is diﬀerent
for diﬀerent diagrams of the same knot, in which case our quantity would not be a knot
invariant. However, if we can show the quantity is unchanged when we alter the diagram
via any Reidemeister move, then we know it is an invariant, because of Fact 1.4. ♦
2 The Jones Polynomial
2.1 Resolving a crossing (4 points)
Deﬁnition 2.1. Suppose we start with a crossing of the form
 . The 0-resolution of this
crossing is
 and the 1-resolution is
 . (For example, see Figure 2.1.) ♦
(a) trefoil
 (b) 0-resolution
 (c) 1-resolution
Figure 2.1: Resolving a crossing
5
Remark 2.2. A diagram may need to be rotated so that the crossing in concern appears as
. For example, after a 90 ◦ rotation, we see that the 0- and 1-resolutions of
 are
 and
, respectively. ♦
Remark 2.3. Here is one way to think of a 0-resolution: if we are traveling along a knot
and reach a crossing in which we are on the upper strand, then we turn left onto the lower
strand. (For a 1-resolution, we would turn right instead.) ♦
2.1.1. (2) Start with the diagram of the ﬁgure 8 knot given in Figure 2.2. Observe that the
crossings are labeled A, B, C, D. Draw the diagram in which crossing B has been
resolved with a 0-resolution and identify the resulting knot/link.
BA
D
C
Figure 2.2
2.1.2. (2) Once again, start with the diagram of the ﬁgure 8 knot given in Figure 2.2. It is
possible to resolve one of the crossings so that the resulting diagram is a trefoil. Which
crossing can we resolve ( A, B, C, D) and how do we resolve it (0- or 1-resolution)?
Simply state an answer.
2.2 The Bracket Polynomial (0 points)
Deﬁnition 2.4. As you all know, a polynomial in x is something of the form
anxn +an−1xn−1 +··· +a1x +a0.
A Laurent polynomial inx is like a polynomial except you can use negative powers. In other
words a Laurent polynomial is something of the form
anxn +an−1xn−1 +··· +amxm,
wherem andn are integers withm≤n. (For example, x3 + 2x + 4 +x−1− 5x−4 is a Laurent
polynomial.) Quite confusingly, a Laurent polynomial is not necessarily a polynomial. ♦
Deﬁnition 2.5. The bracket polynomial of a link diagram D is a Laurent polynomial in the
variableA and is denoted⟨D⟩. It is completely determined by three rules:
⟨
 ⟩
= 1 (BP1)⟨
D⊔
⟩
= (−A2−A−2)⟨D⟩ (BP2)⟨
 ⟩
=A
⟨
 ⟩
+A−1⟨
 ⟩
(BP3)
(The BP stands for “bracket polynomial.”) ♦
6
Let’s go through what these rules mean, one by one.
1. The ﬁrst relation (BP1) states that the bracket polynomial of the knot diagram
 is
the constant polynomial 1. (Note, however, that this does not mean that the bracket
polynomial of any diagram depicting the unknot is 1. For example,
 is also
a diagram of the unknot, but this diagram turns out not to have bracket polynomial
1.)
2. For the second relation, the expression D⊔
 denotes a diagram D with an extra
circle added. Furthermore, the circle does not cross the rest of the diagram. If we do
have a diagram of this form, then BP2 means that we can ﬁnd its bracket polynomial
by starting with the bracket polynomial of the diagram with the circle removed and
multiplying it by−A2−A−2. For example, using BP2 (along with BP1), we have
⟨
 ⟩
= (−A2−A−2)
⟨
 ⟩
=−A2−A−2.
3. In order to apply the third relation, we need to resolve crossings. Start with a diagram
D and ﬁx a crossing. If D0 and D1 are the 0- and 1-resolutions of this crossing, then
BP3 states that⟨D⟩ =A⟨D0⟩ +A−1⟨D1⟩. For example,
⟨
 ⟩
=A
⟨
 ⟩
+A−1
⟨
 ⟩
Example 2.6. Let’s compute the bracket polynomial of the diagram
 . (It is a diagram
of the Hopf link.) Applying BP3 gives us
⟨
 ⟩
=A
⟨
 ⟩
+A−1
⟨
 ⟩
. (2.1)
Using BP3 again,
⟨
 ⟩
=A
⟨
 ⟩
+A−1
⟨
 ⟩
⟨
 ⟩
=A
⟨
 ⟩
+A−1
⟨
 ⟩
.
(2.2)
Combining (2.1) and (2.2), we see that
⣨
 ⟩
=A2
⣨
 ⟩
+
⣨
 ⟩
+
⣨
 ⟩
+A−2
⣨
 ⟩
.
Invoking BP1 and BP2 gives us
⣨
 ⟩
=
⣨
 ⟩
= 1 and
⣨
 ⟩
=
⣨
 ⟩
=−A2−A−2.
Putting everything together gives us ⟨
 ⟩ =−A4−A−4. ♦
7
Fact 2.7. For the trefoil, we have
⟨
 ⟩
=A7−A3−A−5.
You might want to verify this yourself, to make sure you understand how to compute bracket
polynomials of knot diagrams. ♦
2.3 Smoothings (10 points)
In Example 2.6, we decomposed the Hopf link into four diagrams. The four diagrams corre-
spond to the four ways of resolving the two crossings of
 . Each of these diagrams is called
a smoothing.
Deﬁnition 2.8. Given a link diagram D, a smoothing of D is a diagram in which every
crossing of D has been resolved (either by a 0-resolution or a 1-resolution). Note that a
smoothing has no crossings. ♦
Deﬁnition 2.9. Let{0, 1}n denote the set of n-tuples, where each component is either 0 or
1. ♦
Deﬁnition 2.10. LetD be a link diagram with n crossings. Number the crossings 1,...,n .
Let ϵ = (ϵ1,...,ϵ n)∈{ 0, 1}n. Then Dϵ denotes the smoothing of D where crossing i is
resolved via a ϵi-resolution for i = 1,...,n . (Note that Dϵ is also a knot diagram.) ♦
Deﬁnition 2.11. Let D be a link diagram, and let ϵ = (ϵ1,ϵ 2,...,ϵ n) ∈ {0, 1}n be a
smoothing of D. Deﬁne
s0(ϵ) = the number of 0-resolutions in Dϵ
s1(ϵ) = the number of 1-resolutions in Dϵ
o(ϵ) = the number of circles in Dϵ.
(We use the letter o because it looks like a circle!) Also, deﬁne
⟨D,ϵ⟩ =As0(ϵ)−s1(ϵ)⟨Dϵ⟩. ♦
Remark 2.12. We will omit the commas in the ( ϵ1,...,ϵ n) notation to avoid clutter. For
example, ϵ = 10011 is short for ϵ = (1, 0, 0, 1, 1). ♦
Example 2.13. If D =
 , and the top crossing is labeled 1 (so the bottom crossing is
labeled 2), then
D00 =
 , D 01 =
 , D 10 =
 , D 11 =
 . (2.3)
Also, s0(00) = 2, s0(01) = s0(10) = 1, s0(11) = 0, s1(00) = 0, s1(01) = s1(10) = 1,
s1(11) = 2, o(00) =o(11) = 2, o(01) =o(10) = 1. ♦
8
2.3.1. (5) Let D be a link diagram with n crossings. Show that
⟨D⟩ =
∑
ϵ∈{0,1}n
⟨D,ϵ⟩,
where the sum is over all smoothings ϵ of D.
2.3.2. (3) Let D be a link diagram and let ϵ be a smoothing of D. Show that
⟨Dϵ⟩ = (−A2−A−2)o(ϵ)−1.
2.3.3. (2) Show that if ϵ and ϵ′ diﬀer by one resolution, then
o(ϵ′) =o(ϵ)± 1.
2.4 Invariance under Type II and Type III Moves (10 points)
Because of our discussion of invariants and Reidemeister moves at the end of Section 1.2, we
should study how the bracket polynomial behaves under Reidemeister moves.
2.4.1. (5) Show that if link diagrams D and D′ are related by one application of a Type II
Reidemeister move, then⟨D⟩ =⟨D′⟩. That is, show that
⟨
 ⟩
=
⟨
 ⟩
.
2.4.2. (5) Show that if link diagrams D andD′ are related by one application of a Type III
Reidemeister move, then⟨D⟩ =⟨D′⟩. That is, show
⟨
 ⟩
=
⟨
 ⟩
.
2.5 Type I moves (3 points)
In the previous section, you showed that the bracket polynomial is invariant under Type II
and Type III Reidemeister moves. If it is also invariant under Type I moves, the the bracket
polynomial would be a genuine link invariant. However, this is not the case.
2.5.1. (3) Show that ⣨
 ⟩
=−A−3⟨
 ⟩
.
9
(a) positive crossing
 (b) negative crossing
Figure 2.3: Two types of crossings for an oriented diagram
2.6 Writhe of an oriented link (4 points)
Deﬁnition 2.14. Given an oriented link diagram we can deﬁne positive crossings and neg-
ative crossings by Figure 2.3. ♦
Deﬁnition 2.15. Let n+(D) and n−(D) be the number of positive and negative crossings,
respectively, of an oriented link diagram D. ♦
Deﬁnition 2.16. For an oriented link diagram D, the writhe of D is w(D) = n+(D)−
n−(D). ♦
Fact 2.17. As the following diagrams show, if we reverse the direction of all components of
a link, the crossing types (positive/negative) do not change.
↔
 ↔
 ♦
Remark 2.18. Since a knot is a link with one component, we can deﬁne positive and
negative crossings for knot diagrams without specifying an orientation on the knot. Note
that this is not true for links in general. If we reverse the orientations of some (but not all)
of the components of a link, then some crossing types will change. ♦
2.6.1. (2) Show
w
(
 )
=w
(
 )
− 1
w
(
 )
=w
(
 )
− 1.
2.6.2. (2) Show
w
(
 )
=w
(
 )
w
(
 )
=w
(
 )
w
(
 )
=w
(
 )
w
(
 )
=w
(
 )
.
Fact 2.19. The writhe is also unchanged under type III moves. ♦
10
2.7 The Jones Polynomial (7 points)
Because of Problem 2.6.1, the writhe is not invariant under Type I moves.
2.7.1. (7) For an oriented linkL with diagramD, show that the polynomial (−A)−3w(D)⟨D⟩
is an invariant of the link L.
Deﬁnition 2.20. Let L be an oriented link, and let D be a diagram of L. The Jones
polynomial of L, denoted VL(t), is obtained by taking the expression ( −A)−3w(D)⟨D⟩ and
setting A =t−1/4. ♦
Fact 2.21. Because of Problem 2.7.1, the Jones polynomial is an invariant of oriented links.
For knots, recall that the writhe does not depend on the orientation. If we retrace our
arguments above, we see that the Jones polynomial is also an invariant of (unoriented)
knots. ♦
Fact 2.22. For the trefoil (see Figure 1.1b), we have
VK(t) =−t−4 +t−3 +t−1.
You might want to verify this yourself. ♦
Remark 2.23. Vaughan Jones received the Fields Medal for his discovery of the Jones
polynomial. It is a pretty big deal! ♦
3 Detecting chiral knots
3.1 Mirroring knots (25 points)
Deﬁnition 3.1. For a knot K, let Kﬂip denote the mirrored knot. (In other words, make
K out of a piece of string, and hold it in front of a mirror! The knot you see in the mirror
is Kﬂip.) ♦
Deﬁnition 3.2. A knot K is amphichiral if it is equivalent to Kﬂip. Otherwise, it is chiral.
♦
Consider, for example the two diagrams in Figure 3.1. We may ask if they are the same
knot.
3.1.1. (20) Show that for any knot K,
VKﬂip(t) =VK(t−1).
3.1.2. (5) Is the trefoil amphichiral or chiral? Justify your answer.
Remark 3.3. Recall that the Jones polynomial is not just a knot invariant but also an
oriented link invariant. Thus, Problem 3.1.1 still holds if we replace “knot” with “oriented
link.” ♦
11
(a) diagram of K
 (b) diagram of Kﬂip
Figure 3.1: Mirror images of a trefoil
4 Bound on crossing numbers
4.1 Crossing number (3 points)
Deﬁnition 4.1. The crossing number of a knot K is the minimum number of crossings
needed to draw the knot in a plane. It is denoted c(K). ♦
4.1.1. (3) While the diagram given in Figure 4.1 has seven crossings, show that the crossing
number of that knot is not 7.
Figure 4.1
4.2 Reduced diagrams (5 points)
Deﬁnition 4.2. A knot diagram D is un-reduced is it has the form of Figure 4.2. (That
is, there are exactly two strands in the region between X and Y that go from X to Y .
Furthermore, these two strands cross each other exactly once.) A knot diagram D is reduced
if it is not un-reduced.
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1
/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0
/0/0/0/0/0/0/0/0/0
/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1
/1/1/1/1/1/1/1/1/1
Y
X
Figure 4.2
♦
4.2.1. (5) Show, by drawing an example, that it is possible to have two diagrams D andD′
of the same knot K, such that
• D is reduced and
• D′ has fewer crossings than D.
12
4.3 Knots and graphs (5 points)
Every knot diagram corresponds to a planar graph. (See, for example, Figure 4.3.)
(a) trefoil
 (b) corresponding graph
Figure 4.3
Deﬁnition 4.3. A graph is a set of vertices (e.g., the black dots in Figure 4.3b) that are
joined together by edges (e.g., the lines between the dots in Figure 4.3b). A graph isplanar if
it can be drawn on the plane in such a way that its edges intersect only at their endpoints. ♦
Fact 4.4. A planar graph divides the plane into regions, called faces. (The exterior of a graph
is considered a face too.) If V , E, F are the number of vertices, edges, faces (respectively)
of a planar graph, then Euler’s formula says that V−E +F = 2. ♦
Example 4.5. The planar graph Figure 4.3b has V = 3, E = 6, F = 5 (don’t forget to
count the exterior face!). Thus, V−E +F = 2, as expected. ♦
4.3.1. (5) Show that for a knot diagram with n crossings, the corresponding graph has n + 2
faces.
4.4 Coloring faces of knots (15 points)
It is always possible to color the faces of a link in an alternating black-white pattern, as
shown in Figure 4.4. (Recall that we are considering the exterior of the knot diagram to be
a face as well, which explains why Figure 4.4b is a valid checkerboard coloring of the trefoil.)
(a) trefoil
 (b) trefoil
Figure 4.4: Examples of checkerboard colorings
Fact 4.6. By resolving a crossing, we still get a checkerboard coloring. (See, for example
Figure 4.5.) ♦
Given a checkerboard coloring of a knot diagram, we can divide the crossings into two
types. (See Figure 4.6.)
13
(a) checkerboard
 (b) 0-resolution
 (c) 1-resolution
Figure 4.5: Resolving a crossing still gives us a checkerboard coloring.
(a) 0-separating
 (b) 1-separating
Figure 4.6: Two coloring types at a crossing
Deﬁnition 4.7. The coloring in Figure 4.6a is called “0-separating” (because a 0-resolution
separates the two black regions). The coloring in Figure 4.6b is called “1-separating.” ♦
Deﬁnition 4.8. A knot diagram is alternating if the strand alternates between going over
and going under at crossings. A knot is alternating if there is a alternating diagram of the
knot. ♦
4.4.1. (15) Show that a knot diagram is alternating if and only if the diagram admits a
checkerboard coloring consisting of only 0-separating crossings.
4.5 The span of the bracket polynomial (18 points)
Recall the deﬁnitions of⟨D,ϵ⟩ and o(ϵ) given in section Section 2.3.
Deﬁnition 4.9. For a Laurent polynomial f(x), we deﬁne hp(f) to be the highest power
of x that appears in f, and we deﬁne lp( f) similarly to be the lowest power. We deﬁne
span(f) = hp(f)− lp(f). ♦
Deﬁnition 4.10. Let D be a link diagram. We let 0 = (0, 0,..., 0) denote the smoothing
with all 0-resolutions and 1 = (1, 1,..., 1) denote the smoothing with all 1-resolutions. ♦
4.5.1. (5) Let D1 and D2 be knot diagrams of the same knot. Show that span ⟨D1⟩ =
span⟨D2⟩.
4.5.2. (3) Let D be a knot diagram and let ϵ be a smoothing of D. Show that
hp⟨D,ϵ⟩ =s0(ϵ)−s1(ϵ) + 2o(ϵ)− 2.
4.5.3. (5) Let D be a knot diagram. Show that
hp⟨D, 0⟩≥ hp⟨D,ϵ⟩
for all smoothings ϵ.
14
4.5.4. (2) Let D be a knot diagram with n crossings. Show that
hp⟨D⟩≤ n + 2o(0)− 2.
4.5.5. (3) Let D be a knot diagram with n crossings. Show that
span⟨D⟩≤ 2n + 2(o(0) +o(1))− 4.
4.6 Connected link diagrams (17 points)
Deﬁnition 4.11. We say that a link diagram is connected if its corresponding graph is
connected. For example, the usual diagram for the unlink
 is not connected. However,
if the two components overlap in the diagram (as in
 ), then the diagram is connected.
(Note that knot diagrams are always connected.) ♦
4.6.1. (15) Let D be a connected link diagram. Show that if D has n crossings, then
o(0) +o(1)≤n + 2.
4.6.2. (2) Let D be a knot diagram with n crossings. Show that
span⟨D⟩≤ 4n.
4.7 Reduced alternating knot diagrams (42 points)
The goal of this section is to show that alternating knots are nice.
Deﬁnition 4.12. A knot diagram D is reduced alternating if it is both reduced and alter-
nating. ♦
Fact 4.13. Given an alternating knot K, there is a diagram D of K that is reduced alter-
nating. (This is not hard to show.) ♦
4.7.1. (7) Show that ifD is a reduced alternating diagram andϵ is a smoothing with exactly
one 1-resolution, then
o(0) =o(ϵ) + 1.
4.7.2. (5) Show that the assumption that the diagram D is reduced is necessary for Prob-
lem 4.7.1. Give an example where D is alternating but o(0)̸=o(ϵ) + 1.
4.7.3. (30) Let D be a reduced alternating knot diagram with n crossings. Show that
span⟨D⟩ = 4n.
15
4.8 Back to the Jones polynomial (13 points)
We are almost there!
4.8.1. (3) Let K be a knot. Show that
c(K)≥ spanVK.
4.8.2. (5) Let K be an alternating knot. Show that
c(K) = spanVK.
4.8.3. (5) Determine the crossing number c(K) of the knot K depicted by the diagram D
in Figure 4.7. Justify your answer.
Figure 4.7: D, crazy knot diagram
16
Index
0-resolution, 5
0-separating, 14
1-resolution, 5
1-separating, 14
Dϵ, 8
Kﬂip, 11
VL(t), 11
⟨D,ϵ⟩, 8
⟨D⟩, 6
hp(f), 14
lp(f), 14
span(f), 14
0, 14
1, 14
{0, 1}n, 8
n+(D), 10
n−(D), 10
o(ϵ), 8
s0(ϵ), 8
s1(ϵ), 8
alternating knot, 14
alternating knot diagram, 14
amphichiral, 11
bracket polynomial, 6
chiral, 11
component of a link, 3
connected link diagram, 15
crossing number, 4, 12
graph, 13
Jones polynomial, 11
knot, 3
knot diagram, 3
knot invariant, 4
Laurent polynomial, 6
link, 3
link diagram, 3
link invariant, 4
negative crossing, 10
oriented knot, 3
oriented link, 4
planar graph, 13
positive crossing, 10
reduced, 12
reduced alternating, 15
Reidemeister moves, 5
smoothing, 8
writhe, 10
17
