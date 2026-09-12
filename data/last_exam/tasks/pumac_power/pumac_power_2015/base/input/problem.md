# PUMaC Power Round 2015

PUMaC 2015 Power Round
“We have a new theorem—that mathematicians can prove only trivial theorems,
because every theorem that’s proved is trivial.” —Richard Feynman
Rules and Reminders
These rules supersede any rules appearing elsewhere about the Power Round:
1. Your solutions are to be turned in when your team checks in on the morning of PUMaC or emailed to us
at pumac@math.princeton.edu by 8AM Eastern Standard Time on the morning of PUMaC, November
21, 2015 with the subject line “PUMaC 2015 Power Round.” Please staple your solutions together,
including the Power Round cover sheet (the last page of this document) as the ﬁrst page. Each page
should also have on it the team number (not team name) and problem number . Solutions to
problems may span multiple pages, but staple them in continuing order of proof.
2. It is not necessary to do the problems in order, although it is a good idea to read all the problems, so
that you know what is permissible to assume when doing each problem. However, please collate the
solutions in order in your solution packet. Each problem should start on a new page, and solutions
should be written on one side of the paper only (there is a point deduction for not following this
formatting).
3. On any Problem, you may use without proof any Problem, Lemma, or Proposition from earlier
in the test, even if it’s a problem your team has not solved. You may cite results from conjectures or
subsequent problems only if your team solved them independently of the problem in which you wish
to cite them. You may not cite parts of your proof of other problems: if you wish to use a lemma in
multiple problems, please reproduce it in each one.
4. All problems are numbered as “Problem x.y” where x is the section number. A list of problems follows
the table of contents to help you keep track of the problems you have done. Each problem’s title and
point distribution can be found in parentheses between the problem number and problem statement.
The point distribution is bolded.
5. Using computer programs, calculators, and Mathematica (or similar programs) is allowed. However,
print and online references are not allowed . If you attempt to use a program, please attach any
relevant code that is used in the solution.
6. Teams whose members use English as a foreign language may use dictionaries for reference.
7. No communication with humans outside your team of 8 students about the content of these problems is
allowed. If you have any questions regarding the test, please contact us at once at pumac@math.princeton.edu.
Figure 1: Graphical View of kP.
Updated 11/18/15.
PUMaC 2015 Power Round Section 1 page 2
1 Introduction
Elliptic curves appear often in mathematics because they possess remarkably nice properties. For example,
elliptic curves relate elegantly to ideas from Galois theory. This Power Round will demonstrate the utility
of elliptic curves and Galois theory by using them to prove an interesting fact about the Tiger sequence. We
deﬁne the Tiger sequence {an} for non-negative n recursively by a0 =a1 =a2 =a3 = 1 and for n≥ 4, the
relation
anan−4 =an−1an−3 +a2
n−2.
We ultimately seek to prove the following theorem.
Theorem 1. Let π(x) be the number of primes less than or equal to x. Then
lim
x→∞
|{p≤x :p prime and p|an for some n}|
π(x) = 11
21.
This 11
21 fraction is called the density of primes that divides a term of the Tiger sequence.
While much mathematical machinery is needed to prove this, we have broken down the task into a series
of sections that culminate in a ﬁnal proof in section 9. Please note that while the ultimate goal of this
Power Round is to prove the given theorem, the sections may include problems that are not essential to the
ﬁnal proof, but are relevant and good problems to try. We have sorted the problems in as straightforward
a manner as possible with regards to the ﬁnal proof, but as the various topics are very interconnected you
may ﬁnd it useful to refer back to previous sections for ideas on how to proceed. As always, refer to the
rules at the start of the document for how to reference other problems.
In a similar vein, we have a couple housekeeping remarks:
• All deﬁnitions, propositions, lemmas, and theorems are labeled in increasing order using the same
index. For example, this document began by introducing a theorem labeled Theorem 1 and will soon
introduce its ﬁrst lemma labeled Lemma 2 followed by its ﬁrst oﬃcial deﬁnition labeled Deﬁnition 3.
• While this document guides you through the ﬁnal proof, it will not babysit your progress. In any given
part of the document, we may make assertions that will be necessary when solving a later problem. It
is your responsibility as the reader to keep track of such material. Details that are absolutely essential
will often be written in bold, but this is not an if and only if criterion for discerning important facts.
Lastly, you may be asking yourself: “Why is this interesting?” Well, we could name-drop famous math-
ematicians who have answered similar questions, or lie and say this is a large area of mathematics (this
speciﬁc ﬂavor of math isn’t). But that would only tell you why this topic is interesting to others. Why
will it be interesting to you? Well, if we take a slightly more general view, the question becomes: Why
is math interesting to you? You have probably heard people say that math is necessary for science or as
a life skill. But, if you have voluntarily decided to take this contest, you might have a diﬀerent opinion.
Sure, the science/life skills part might be true, but that’s not why you are here and that’s not why we have
organized this tournament for you. PUMaC is a competition for many diﬀerent types of people created by
many diﬀerent types of people, but we all share an interest in and appreciation for math for its own sake.
Math is pretty. Back to the original question, we hope that this Power Round will expose you to an area
of math you haven’t seen before and that is remarkably pretty (but we’ll leave that aesthetic judgment to
you). Now, please don’t get too carried away by the scoring and the fact that this is a competition. It may
be clich´ e, but please have fun as well.
-Heesu Hwang.
We’d like to acknowledge and thank many individuals and organizations for their support; without their
help, this Power Round (and the entire competition) could not exist. Please refer to the solution of the
Power Round for full acknowledgments.
2
PUMaC 2015 Power Round Section 1 page 3
Contents
1 Introduction 2
2 Let’s Get Started 4
3 Group Theory 5
4 Elliptic Curves 9
5 Sequences 13
6 Interlude 14
7 Galois Theory 16
8 Elliptic Curves and Galois Theory 18
9 Final Fraction 21
List of Problems
3.1 Problem (Basic Group Theory; 2, 2, 2, 2 ) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
3.2 Problem (Finite Field; 5) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
3.3 Problem (Finite Group; 5) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
3.4 Problem (Subgroup Test; 5) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
3.5 Problem (Lagrange’s Theorem; 10) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
3.6 Problem (Odd Order; 5) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
4.1 Problem (Transformation of EC; 2, 8) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
4.2 Problem (Addition Computation; 2, 2) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
4.3 Problem (Addition Theory; 2, 8) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
4.4 Problem (Reduced Rational Point; 5) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
4.5 Problem (E Symmetry; 2, 2) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
4.6 Problem (Sequence and Curve; 10) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
5.1 Problem (Secondary Sequence; 5, 2) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
5.2 Problem (Is Integral; 10) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
5.3 Problem (Sequence Divisibility; 5) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
5.4 Problem (Integrality, Integrality!; 8, 12) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
6.1 Problem (EC over Finite Field; 5) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
6.2 Problem (An Odd Divisor; 5) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
7.1 Problem (0 Ring; 5) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
7.2 Problem (Fields; 4, 2, 2, 4 ) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
7.3 Problem (Galois Automorphisms; 2, 8) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
9.1 Problem (Final Fraction; 10, 10, 10, 10 ) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 21
3
PUMaC 2015 Power Round Section 2 page 4
2 Let’s Get Started
Firstly, if you haven’t read the introduction, then go back and read the introduction! It really does add big-
picture context to the problems you’re doing. Now as a preliminary and as an example of the standards of
justiﬁcation we expect throughout this power round, here is a classical number theory result called B´ ezout’s
Lemma, with proof. Very quickly, here is a spot of terminology:
Deﬁnition 2. Z represents the set of integers. Q represents the set of rational numbers. R represents the
set of real numbers. C represents the set of complex numbers. Finally, N represents the set of positive
integers. (A point of interest, Europeans include 0 in this set while Americans do not. Do you agree? Is 0 a
natural number?)
Deﬁnition 3. Sets. A set is a collection of objects. We write that set A ={ai} for integers 1≤ i≤ n if
A contains exactly elements ai and nothing else. We may similarly have inﬁnite sets. Here is some speciﬁc
notation with sets:
• a∈A: Let A be a set such that A contains the element A; then we write a∈A.
• A\B: Let A and B both be sets. Then A\B denotes the set of elements that are inside A but not in
B.
• A⊂B: Let A and B both be sets. If every element of A lies inside B, we write A⊂B.
• ∀a∈A: The notation ∀a∈A is read in English as “for all elements a in A”, and means we consider
all elements of set A.
• ∃a(∈A): This notation is read as “there exists an element a (in set A).” It is usually followed up by
the phrase “such that.” For example, ∃x∈ R such that x> 0.
Lemma 4 (B´ ezout’s Lemma). Prove that if x and y are coprime integers, then there exist integers a and b
such that ax +by = 1.
Proof. We prove the more general case of integers x and y with a general gcd.
Examine the set S :={c∈ N : c = ax +by where a,b ∈ Z}. Since gcd( x,y ) divides x and y, gcd(x,y )
divides any element of S.
Suppose thatl is the least element ofS by the well-ordering principle (which states that every non-empty
set of positive integers has a least element); thus let a0 andb0 be integers such that l =a0x +b0y. Take any
other arbitrary element of S; for example k =a1x +b1y. Then by integer division, suppose that k =l·q +r
where 0≤r<l . Thus
l =a0x +b0y =⇒ lq =a0qx +b1qy =⇒ r =k−lq = (a1−a0q)x + (b1−x0q)y.
Sincel by assumption was the least positive integer that was a linear combination of x andy, we must have
r = 0. Thus k =l·q, and every element of S is divisible by l.
Note that|x|,|y|∈ S; thusl| gcd(x,y ). But clearly gcd(x,y )|l, and so they are equal. Thus there is some
integer solution to l =ax +by.
4
PUMaC 2015 Power Round Section 3 page 5
3 Group Theory
Groups are fundamental to mathematics. They form the basis (pun!) of algebra, one of the two overarching
subjects of math. It is important that anyone who wishes to explore math further understands groups well.
A group is deﬁned as follows.
Deﬁnition 5. A group is a set of elements G with a closed binary operation∗. Binary means∗ operates on
two elements. Closed means that for any a,b∈G,a∗b is contained inside G. These elements and operation
obey the following three rules.
• There exists an unique element e∈G such that for all elements g∈G,e∗g =g∗e =g. This is called
the identity element. (In cases of ambiguity, we will denote this as eG.)
• For any elementg∈G, there exists a unique element h∈G such that g∗h =h∗g =e. This element
h is usually denoted g−1 (in additive groups (to be explained), it is denoted −g).
• For alla,b,c ∈G, the associative property holds:
a∗ (b∗c) = (a∗b)∗c.
Deﬁnition 6. Suppose{G,∗} is a group. Suppose ∗ is commutative. That is, for all a and b in the group,
a∗b =b∗a. Then G is called commutative or abelian.
To demonstrate all this, Z is a group with addition as the operation. This is a group because we may
always add two integers and get another integer, 0 is the additive identity, and similarly the other group
properties are satisﬁed. In fact, {Z, +} is an abelian group. Now here are some warm-up problems.
Problem 3.1 (Basic Group Theory; 2, 2, 2, 2 ). Give justiﬁcation for each of the following.
a) Is {Z,−}, the set of integers under subtraction, a group?
b) Is {N, +}, the set of positive integers under addition, a group?
c) Is {Q,·}, the set of rationals under multiplication, a group?
d) Is {Q\{0},·}, the set of rationals without zero under multiplication, a group?
We turn now brieﬂy to the topic of modular numbers where we ﬁnd groups arising naturally. We denote
Z/nZ as the integers mod n. Elements of this set are integers m where 0≤m <n. Note that by division,
for any integer z∈ Z, we may write z = n·q +r where 0≤ r < nand q and r are both integers. Thus
in this set of integers mod n, z≡ r (mod n). For examples, in the set of integers mod 7 ( Z/7Z), 10 ≡ 3
mod 7,−5≡ 4 mod 9, and 1063 ≡ 3 mod 10. A nice property of mods is that we may substitute equivalent
quantities at any time. For example,
6546· 773− 1650· 945 + 8654651 = (935· 7 + 1)· (110· 7 + 3)− (235· 7 + 5)· (135· 7) + (7 + 1)654651
≡ 1· 3− 5· 0 + 1654651 (mod 7)
≡ 4 (mod 7) .
We mention mods because they are very fundamental to number theory and algebra. For one, note that
Z/nZ is a group with respect to addition (morally, you should really prove this to yourself, but there is no
5
PUMaC 2015 Power Round Section 3 page 6
problem to write up). If n =p is prime, we equivalently write Fp = Z/pZ. Primes are really nice numbers,
and in general “things” like Fp that are associated with primes are also often very nice, as we shall see in
depth later (ﬁelds!). For now, here’s just a small problem about mods.
Problem 3.2 (Finite Field; 5). Let p∈ Z be a prime. Setwise, the unit group of Fp is Z/pZ\{0}. Prove
that the unit group of Z/pZ, denoted as Z/pZ×, is a group under multiplication.
Turning back now to group theory, if the operation of a group is called “addition,” we call it an additive
group. Notationally, for any g∈ G and n a non-negative integer, ng :=
n∑
i=1
g denotes g added to itself n
times and for n< 0,ng =−((−n)g). Also, 0 denotes the group identity. Similarly, if the operation is called
multiplication, then for any g∈G and n a non-negative number, gn =
n∏
i=1
g denotes g multiplied by itself n
times, and for n< 0, ng = (|n|g)−1. Also, 1 is the group identity. When notation is written with powers, it
is implicitly implied that the operation is multiplication, and similarly notation that uses scalar multiples of
group elements implies the operation is addition. With that, here are a bunch of problems and deﬁnitions!
Deﬁnition 7. The order of any element g∈G is the least positive integer l such that gl =e. If no such l
exists, then the order is called inﬁnite.
Secondly, the order of a group G is the number of elements of G. Note if G has inﬁnitely many elements,
the order of G is inﬁnity.
For example, 2015 has inﬁnite order in the group of integers under addition. However, 2015 has order 2
in Z/4030Z.
Problem 3.3 (Finite Group; 5). LetG be a ﬁnite group. Prove that every element of G has a ﬁnite order.
We only consider ﬁnite groups in depth during this power round. However, we have seen examples
of inﬁnite groups (such as the integers under addition). In general, there aren’t really large philosophical
diﬀerences between the two categories. However, we primarily present ﬁnite groups here because it’s easier
to work with them when ﬁrst starting out.
Deﬁnition 8. Suppose that G is a ﬁnite group and H⊂G is a non-empty subset of the elements of G that
is itself a group. Then H is called a subgroup of G where H inherits the operation of G.
The motivation behind such a construction of a subgroup is simple enough; it is a group in its own right
that just happens to be contained inside another! You know what, here’s a fun trick that you may ﬁnd useful
sometime (you likely won’t use it in this power round, unfortunately).
Problem 3.4 (Subgroup Test; 5). Let G be a group and H⊂G a non-empty subset of G. Suppose H is a
set that has the property that for all a,b∈H, ab−1∈H. Prove that H is a subgroup of G.
Subgroups in fact are very nice, natural constructions from groups. Think back to the group of integers
and the group of integers mod n; for example let’s take n = 7. Another way to think about mods is
to imagine that the numbers 0 ≤ k < 7 simply represent the classes of numbers {c· 7 + k : c ∈ Z}.
6
PUMaC 2015 Power Round Section 3 page 7
For example, 0 represents the class of numbers [0] := {··· ,−14,−7, 0, 7, 14,···} , 1 represents the class
[1] := {··· ,−13,−6, 1, 8, 15,···} , and so forth. In this manner, note that [0] is a subgroup of Z under
addition. However, [1] is unfortunately not a subgroup. For example, 1 + 1 = 2 is not in the set [1].
However, [1] is still a pretty natural construction; maybe there is a name for it? Yes, there is!
Deﬁnition 9. Let H be a subgroup of G. For all g∈G, we call gH :={g·h :h∈H} a left coset. For all
g∈G, we call Hg :={h·g :h∈H} a right coset.
For example, letH = 7Z, the set of numbers that is 7 times an integer, and let G = Z the integers. Note
thatH is [0] as mentioned above. Then 1 + H is a coset of G (note in this case, this is both a left and right
coset) that in this case is the class [1] mentioned directly above.
Cosets are very valuable tools in the proofs of group theory problems. Why? Because they are very
symmetric in a sense, and this leads to neat properties. For example, if aH andbH are two cosets of a group
G, do you think they have to intersect non-trivially? Well no; [0] and [1] as we saw above do not intersect
([0] is the coset 0 +H in our example). Well if aH andbH do intersect, do you think they can intersect only
a little bit? That is, can aH∩bH be non-empty, butaH∩bH is strictly smaller than both aH andbH? Or
ifG is a ﬁnite group, do you think that aH andbH have to have the same size? Or do you think that every
element of G has to be contained inside some coset? These are all questions that you should think about.
Finally, this leads us to a what we call Lagrange’s Theorem.
Problem 3.5 (Lagrange’s Theorem; 10). Suppose G is a ﬁnite group of order n. Then prove for all g∈G,
gn = 1.
And now, before we proceed to other sections, here is a ﬁnal group theory problem.
Problem 3.6 (Odd Order; 5). Let G be a ﬁnite group. Prove that an element g has odd order in G if and
only if for every positive integer k, there exists some element hk∈ G such that (hk)2k
= g. (Note that we
do not specify G as abelian; it is suﬃcient to take G a ﬁnite group.)
Hopefully you have found these problems illuminating (hint: you may see these things again). However,
to end this section, we would just like to present some standard material that we think is enriching to
experience.
Suppose we have two groups G and H, and we create a function f between them f : G→ H. But
we don’t want any old functions; we want functions that somehow show that the structure of G and H
have similarities. For example, examine Z and 2Z as additive groups (2 Z is notation for the set of all even
numbers). Any addition done with the even numbers is linked to addition done with regular numbers. For
example,
2 + 46 = 48⇔ 2(1) + 2(23) = 2(24).
We want functions between groups to somehow reﬂect the similarities between them. Thus we impose more
conditions on f.
Deﬁnition 10. Let G and H be groups with a function f :G→H. This function f is called a homomor-
phism if:
• For alla,b∈G,f(a∗Gb) =f(a)∗Hf(b) (∗G and∗H represent the operations ofG andH respectively).
For example, let G = Z, H = 2 Z, and let f(a) = 2a. We encourage you to check that this is indeed
a homomorphism, and that it has the property we wanted: that it represents the relationship between the
structure of G and H.
7
PUMaC 2015 Power Round Section 3 page 8
Deﬁnition 11. Letf :G→H be a homomorphism. If every element of H is the image of some element of
G, then f is surjective and is a surjection.
Deﬁnition 12. Let f : G→ H be a homomorphism. If the only element of G that is mapped to eH, the
identity element of H, is eG, then f is injective and is an injection.
Deﬁnition 13. If a group homomorphism is both injective and surjective (if it satisﬁes both, then it is also
called bijective), then it is called an isomorphism.
You may want to convince yourself that in the example above, the homomorphism is indeed bijective. In
general, the same terminology applies to general functions. If a function f : A→ B has the property that
∀b∈ B,∃a∈ A such that f(a) = b (surjective) and that ∀a,a′∈ A, f(a) = f(a′) =⇒ a = a′ (injective),
then f is bijective (this is an adjective) and is a bijection (this is a noun).
Next, we introduce the idea of mashing groups together. Recall that a number line can be represented as
R. A coordinate plane is similarly represented by the notationR2 or R×R. This is called a direct product, and
elements of R2 are coordinate pairs (a,b ) wherea andb both come from R. Well, this is something we can do
with groups as well. For example, taking two groups G andH, we denote G×H :={(g,h ) :g∈G,h∈H}.
The group operation on this new set is the combination of the operations of G and H component-wise
respectively. One fact that we ask the reader to convince themself (this is clearly grammatically not “correct,”
but the author strongly believes this should be an oﬃcial singular, gender-neutral pronoun) is that G×H
is itself a group. While this isn’t an oﬃcial problem, you should convince yourself that this works because
it’s necessary to understand for the next part.
We ﬁrst introduce a deﬁnition. We will explore this topic more thoroughly in section 7, but the deﬁnition
is suﬃcient here for now.
Deﬁnition 14. LetR be a set of elements with a closed binary operation we call addition such that {R, +}
is an additive, commutative group. Furthermore, suppose R admits another closed binary operation · that
we can call multiplication; it is commutative, and ∀a,b,c ∈R, a· (b·c) = (a·b)·c; a· (b +c) =a·b +a·c;
and (b +c)·a =b·a +c·a. Finally, there exists a multiplicative identity we call 1 such that for all a∈R,
a· 1 = 1·a =a. Then R is called a ring.
Deﬁnition 15. LetR be a ring. Then GLn(R) is called the general linear group, and denotes the group of
n×n invertible matrices with elements in R as a group under multiplication.
There is yet another way to make a group from two smaller groups. As a generalization of the direct
product, we introduce the semidirect product. We start with a group G and a group H, where H is a group
of functions that act on elements of G. For example, let G be the set of vectors Z× Z, and let H be the set
of matrices GL 2(Z).
In other words, G is a set of vectors of the form ( a,b ) where a and b are both integers, and H is the
set of invertible 2× 2 matrices with integer coeﬃcients (invertible under multiplication). Elements of H are
indeed functions that act on elements of G; for example if h∈ H and g∈ G, then h·g is another vector.
Thus we can deﬁne a semidirect product as follows.
8
PUMaC 2015 Power Round Section 4 page 9
Proposition 16. Let the semidirect product setwise be deﬁned asG⋊H :={(g,h ) :g∈G,h∈H} whereH
is a group of functions that acts onG (yes, groups may have functions as elements). Let∗g and∗h denote the
group operations of G andH respectively. Then the group operation on this set for (g1,h 1), (g2,h 2)∈G ⋊H
is deﬁned by
(g1,h 1)∗ (g2,h 2) := (g1∗gh1(g2),h 1∗hh2).
G ⋊H is a group.
Thus in our example here, we can deﬁne a group (Z× Z) ⋊GL2(Z) (this is an example of an aﬃne general
linear group as we shall see later). Here is an example operation:
([2
0
]
,
[−5 2
2 −1
])
∗
([1
5
]
,
[1 0
0 1
])
=
([2
0
]
+
[−5 2
2 −1
]
·
[1
5
]
,
[−5 2
2 −1
]
·
[1 0
0 1
])
=
([
2
0
]
+
[
5
−3
]
,
[
−5 2
2 −1
]
·
[
1 0
0 1
])
=
([ 7
−3
]
,
[−5 2
2 −1
])
.
Later on when we revisit this aﬃne general linear group, we use this notation AGL2(R) to denote (R)2 ⋊
GL2(R) where R is a general ring. We will go in depth about this later. With this, we turn now to the topic
of elliptic curves.
4 Elliptic Curves
Elliptic curves are integral (hah! it’s a pun!) to mathematics, and in fact have even higher generalizations
called varieties. For the purposes of this power round, we deﬁne an elliptic curve as follows.
Deﬁnition 17. An elliptic curve E is the curve satisfying an equation of the form
E :y2 +a1xy +a3y =x3 +a2x2 +a4x +a6,
where the coeﬃcients ai are INTEGERS (can’t stress this enough :p).
The strange coeﬃcient numberings are of historical signiﬁcance. The reason that elliptic curves are
interesting is that there is a natural group on the set of points on them.
Very important remarks: for the entirety of this power round, we take coeﬃcients of elliptic curves
to be integers. However, we may allow points on the curve to be rational or something else. Unless oth-
erwise speciﬁed, any elliptic curve has integer coeﬃcients and any points we consider on it are rational points.
Now, if you’re the average person looking at this equation, you may be slightly disgusted by how unwieldy
it looks; come on, that xy term looks atrocious. So let’s get rid of it.
Problem 4.1 (Transformation of EC; 2, 8).
a) Let f(x) = x3 +a2x2 +a1x +a0 be a polynomial with rational coeﬃcients. Find some linear change of
variablesx =mx′ +n such that f(x) =x′3 +b1x′ +b0 is another polynomial with rational coeﬃcients.
b) Let E :y2 +a1xy +a3y =x3 +a2x2 +a4x+a6 be an elliptic curve. Find a change of variables y↦→y′ and
x↦→x′ such that y′2 =x′3 +Ax′ +B. This gives us another elliptic curve E′; note that E′ is an elliptic
curve, and so A,B ∈ Z. (Hint: you may have to use a change of variables that involves two variables at
once. Also keep in mind that the starting and ﬁnal coeﬃcients have to be integral.)
9
PUMaC 2015 Power Round Section 4 page 10
This latter form is what is called the short Weierstrass form. This form can be much easier to work with
at times. Substitution for y2 is a lot easier for example. Let’s try to work with this form.
Let E : y2 = x3− 20x− 15 be an elliptic curve. Note the points P = (−4, 1) and Q = (−1,−2) lie on
E. The picture below shows the graph of the elliptic curve in blue with two points on it P and Q. In the
picture, notice the black line through points P andQ. It intersects the elliptic curve again at another point
we callP∗Q at coordinates (6,−9). Finally, the reﬂection of point P∗Q vertically over thex-axis is shown
by the red line. This gives us a point we call P +Q at (6, 9). Thus we write (−1,−2) + (−4, 1) = (6, 9).
Figure 2: Addition of Two Rational Points.
This method in general gives us a way to deﬁne the “addition” of two points that will lead us to a group.
Let’s do a few more examples ﬁrst, though. We stress that getting P +Q from P∗Q by reﬂecting over the
x-axis only works for elliptic curves in short Weierstrass form.
Problem 4.2 (Addition Computation; 2, 2). Let E : y2 = x3− 20x− 15 be an elliptic curve. Note that
(6,−9), (−4, 1), (6, 9), and (204, 2913) all lie on the curve.
a) What is (6,−9) + (−4, 1)?
b) What is (6, 9) + (204, 2913)?
We are ready to present the group on an elliptic curve. Again, we reiterate that we have only seen
addition for elliptic curves in short Weierstrass form.
Deﬁnition 18. LetE be a general elliptic curve. Then E(Q) denotes the set of rational points on E. That
is, those points (α,β ) with α,β ∈ Q such that (α,β ) lies on the curve E.
10
PUMaC 2015 Power Round Section 4 page 11
Deﬁnition 19. Let E be a general elliptic curve with points P and Q on E. Note that line PQ intersects
E at a third point. This point is called P∗Q. (The cautious reader might see some problems with this
deﬁnition. For example, what if P = Q? This statement will be fully justiﬁed later, although you may be
able to prove it yourself.)
Proposition 20. Let E be an elliptic curve in short Weierstrass form. Then {E(Q), +} is a group where
the binary operation on two points P andQ is called addition. Namely, P +Q is the reﬂection of P∗Q over
the x-axis.
Proving that this group (incredibly) exists can be unnecessarily complicated in general. For example, the
existence of the identity element requires machinery that is a little too complicated to build here (we will
build it later though!). Also, digest for a moment the almost magical nature of what this says. Given a line
through two rational points on an elliptic curve, you get another rational point! With this in mind, it is a
good exercise to prove some of the basic facts of this group law, after which you may assume this proposition
is true.
Problem 4.3 (Addition Theory; 2, 8). Let E :y2 =x3 +Ax +B be an elliptic curve with A,B ∈ Z and
P = (a,b ), Q = (c,d ), and H = (e,f ) be rational points on E. For simplicity, we assume the x-coordinates
of P , Q, and H are distinct.
a) Prove that P +Q is a rational point.
b) Prove that the associative property holds. Namely, show that (P +Q) +H = P + (Q +H). You may
furthermore assume thex coordinates ofP +Q andH are diﬀerent, and that ofP andQ+H are diﬀerent
as well.
Problem 4.4 (Reduced Rational Point; 5). Let E :y2 +e1xy +e3y =x3 +e2x2 +e4x +e6 be an elliptic
curve with integer coeﬃcients. Suppose that P =
(a
b, c
d
)
onE is a rational point in reduced form (i.e. both
the coordinates are reduced fractions). We may assume b and d are positive (since a or c can be negative).
Give an equality relating b and d by writing one as a positive power of the other.
So if you are morally convinced by now that E(Q) should be a group (as you should be), then you might
also morally accept that Proposition 20 is also true for any elliptic curve, not just those written in short
Weierstrass form. And it is! However, the deﬁnition of addition is slightly diﬀerent in the general case. The
reason we tookP +Q as the reﬂection ofP∗Q in the short Weierstrass case is that for elliptic curves written
in short Weierstrass form, there is a natural horizontal line of symmetry at the x-axis. In the general case,
we can ﬁnd another natural horizontal line of symmetry; and so in the general case, while P∗Q is always
the same, P +Q will be diﬀerent.
For example, consider the curvey2−2015y =x3−36x2 +x. Notice that for all points (a,b ) on the curve,
by how left hand side is written, the point ( a, 2015−b) is also on the curve. Thus the horizontal line of
symmetry in this case is 2015
2 . For this curve then, P∗Q is deﬁned as the third point of intersection of the
linePQ and the curve, andP +Q is deﬁned as the reﬂection of P∗Q over the liney = 2015
2 . More generally
for all the curves we consider in this power round, this process of reﬂecting over the line of symmetry applies.
11
PUMaC 2015 Power Round Section 4 page 12
Figure 3: Horizontal Line of Symmetry.
Deﬁnition 21. LetE be an elliptic curve. Then P +Q is the reﬂection of P∗Q over the horizontal line of
symmetry of E.
Consider now the elliptic curve E : y2 +y = x3−x and the point P = (0, 0) on this curve. From this
point on, we mostly refer to this curve and point P . It is the most important curve that we examine in order
answer our question about prime density.
Problem 4.5 (E Symmetry; 2, 2). Let E be the elliptic curve y2 +y =x3−x.
a) For every point (a,b ) on E, there is another point (a,c ) on E as well. What is c?
b) There is the horizontal line of symmetry y =α for this curve E. What is α?
Now, remember that sequence we mentioned in the introduction? Recall that the Tiger sequence {an} is
deﬁned by a0 =a1 =a2 =a3 = 1 and recursively by anan−4 =an−1an−3 +a2
n−2. You’ll get to prove some
facts about this sequence later. This following problem should keep you occupied with it until then. Keep
in mind that we ﬁxed a curve E and point P above. One fact about E andP is that P +P = (1, 0) (for the
interested, adding a point to itself requires the use of a tangent line; learn calculus!).
Problem 4.6 (Sequence and Curve; 10). Prove for n > 1 that (2n− 3)P =
(
f (n)
a2n
, g(n)
a3n
)
where f(n) =
a2
n−an−1an+1 andg(n) =a2
n−1an+2− 2an−1anan+1. (Recall from section 3, the group theory section, that
kP =∑k
i=1P .)
12
PUMaC 2015 Power Round Section 5 page 13
5 Sequences
So we turn now to the Tiger sequence again. A priori, we know nothing about this sequence. From the
deﬁnition, it’s not even clear that it’s integral! (Hint: it is). As reference, here are some of the ﬁrst few
values starting with a0: 1, 1, 1, 1, 2, 3, 7, 23, 59, 314, ··· . Well, that is royally unhelpful. Let’s try to get
our hands dirty working with these types of non-linear recurrences. Note by the recursive deﬁnition of the
Tiger sequence that we may deﬁne terms of the sequence for negative n. For example, a−1a3 = a0a2 +a2
1
gives a way to deﬁne a−1. This may be necessary for you to establish base cases.
Deﬁnition 22. Forn∈ N, deﬁne sn :=an−3an+3−an−2an+2.
As it turns out, this new sequence of numbers is intimately related to the Tiger sequence, which may
help us prove integrality.
Problem 5.1 (Secondary Sequence; 5, 2).
a) Prove that a2
nsn−1 =a2
n−1sn for n∈ N.
b) Prove that sn = 4a2
n for n∈ N.
Problem 5.2 (Is Integral; 10). Prove that an is integral for n ∈ N and that the following are true,
gcd(an,an−1) = gcd(an,an−2) = 1.
Because there are so many ways to create a recursive sequence, there aren’t really centralized strategies
for dealing with them in much generality. But maybe this set of problems was interesting. As a parting
shot, here are few more problems.
Problem 5.3 (Sequence Divisibility; 5). We deﬁne a recursive sequence {bn} by b0 =b1 =b2 = 1 and for
n≥ 3, bn =bn−1bn−2 +bn−3. Prove that for all integers n> 1, there exists a k≥ 0 such that n|bk.
Problem 5.4 (Integrality, Integrality!; 8, 12).
a) We deﬁne a recursive sequence {cn} byc0 =c1 =c2 =c3 =c4 = 1 and for n≥ 5, cncn−5 =cn−4cn−1 +
cn−2cn−3. Prove that this sequence is integral for n≥ 0.
b) We deﬁne a recursive sequence {dn} byd0 = 1, d1 = 2, d2 = 1, and d3 =−3 and for n≥ 4,
dn =



dn−1dn−3−d2
n−2
dn−4
if n≡ 0, 1 (mod 3)
dn−1dn−3− 3d2
n−2
dn−4
if n≡ 2 (mod 3) .
Prove that the sequence{dn} is an integral sequence for n≥ 0.
13
PUMaC 2015 Power Round Section 6 page 14
6 Interlude
As the reader may have noticed by now, this Power Round is a rather eclectic collection of math topics. The
following rephrases our previous work into a form we may use later.
We introduce projective space, speciﬁcally projective 2-space, denoted P2(R) (this means that coordinates
are elements of R; we can also work instead in P 2(Q), but that is not necessary). The motivation of such
a system of numbers is hard to ﬂesh out fully here. (For the interested reader, consider this system as an
attempt to ﬁx the “problem” that two parallel lines do not intersect by adding points at inﬁnity. For the
artists out there, this is a formalization of the concept of perspective drawings in which parallel lines do in
fact converge. Unfortunately, the implementation we present here may not make it clear why these things
are true.)
Elements of P2(R) represent the lines in R3, real 3-space, that pass through the origin. Examine such a
line ℓ that passes through the origin (0 , 0, 0). We represent ℓ by a triplet of coordinates ( a : b : c) where ℓ
passes through points (0, 0, 0) and (a,b,c ). This clearly doesn’t give a unique representation of ℓ. Under this
representation, for all real numbers s, (sa : sb : sc) and (a : b : c) will always represent the same line. For
example, ifℓ is a line that passes through (0, 0, 0) and (2, 4, 3), then we can denote this line inP 2(R) in many
ways: (2 : 4 : 3)∼= (4 : 8 : 6)∼= (π : 2π : 3π
2 ), and so forth. When possible, it is convention to standardize the
way we represent these vectors by making the last coordinate 1; thus if c̸= 0, then (a :b :c) = (a
c : b
c : 1),
and the latter is the preferred form.
Deﬁnition 23. Let P2(R) represent projective 2-space. Then elements α∈ P2(R) are represented as α =
(a :b :c) where if c̸= 0, we may assume c = 1.
The reason we introduce this space is because it is in some sense the “correct” medium in which to
examine elliptic curves.
Deﬁnition 24. Let E :y2 +a1xy +a3y =x3 +a2x2 +a4x +a6 be an elliptic curve. Denote another curve
in three variables (adding z) as F :y2z +a1xyz +a3yz 2 =x3 +a2x2z +a4xz2 +a6z3. We say that F has
been homogenized because each term has the same degree (degree is the sum of the powers of all variables).
F is an elliptic curve in P2(R).
By the three variables given by homogenization, we can start to look at F as a curve lying in projective
2-space. It’s clear that if ( a,b ) is a solution to E, then (a :b : 1) is a solution to F . We may say more.
Proposition 25. There is a bijective correspondence between an elliptic curve E and a homogenized F
with a further bijective correspondence between points on E and F .
We check this by proof by example! (Note this is not actually a proof. Never actually do this, but
this example should illustrate clearly why this proposition is true.) Examine the elliptic curve E : y2 =
x3− 20x− 15 again. Then the homogenization is F :y2z =x3− 20xz2− 15z3. Since (−4, 1) is a solution to
E, we see (−4 : 1 : 1) is clearly a solution to F . Conversely note (1284 : −5601 : 64) is a solution to F (you
may way want to check this). Then it is clear
( 321
16 : −5601
64 : 1
)
is also a solution to F , and so
( 321
16,−5601
64
)
is
a solution to E. Note the importance of homogenization in this work. For example, what would have failed
if F were made by simply multiplying every term by exactly one factor z?
And ﬁnally, here is why we needed projective space: how do we look at elliptic curves over a ﬁnite ﬁeld?
An example of a ﬁnite ﬁeld is Fp (you know enough to verify that is indeed a ﬁeld). Fields are explored more
thoroughly in section 7.
14
PUMaC 2015 Power Round Section 6 page 15
Deﬁnition 26. LetK be a ring. Furthermore let K also have the additional property that for all non-zero
elementsa,∃a−1∈K such that a·a−1 =a−1·a = 1. Then K is called a ﬁeld.
Perhaps it is unclear here why we would want to look at elliptic curves over Fp, but you‘ll see why soon
enough. So, is there a notion of an elliptic curve over Fp wherep is a prime? In case you haven’t noticed by
now how these rhetorical questions go... Yes! There is. Suppose E :y2 +a1xy +a3y =x3 +a2x2 +a4x +a6
is an elliptic curve with integer coeﬃcients. We can look at points in E/Fp (readE over Fp meaning that we
takeE as an equation and points on E all inside Fp) in two ways: by solving E in Fp from the start, or by
reducing points from E/Q. The ﬁrst is easy to do: simply solve E :y2 +a1xy +a3y≡x3 +a2x2 +a4x +a6
(mod p).
Problem 6.1 (EC over Finite Field; 5). LetE :y2 =x3 + 3x + 9 be an elliptic curve over F13. Find all the
elements of E(F13). (Hint: there are 14 total elements. You may have to read on ﬁrst to ﬁnd the identity
element.)
Otherwise, we can ﬁnd points on E over ﬁnite ﬁelds by mapping rational points of E over Q by the
“obvious” mapping to try. Suppose that ( a
b, c
d)∈E(Q) is a rational point on E. We look at the reduction
of E onto Fp by ﬁrst translating to projective space; this point naturally maps to ( ad : bc : bd). Here
in projective space, we divide by any powers of p necessary such that gcd( ad/pk,bc/pk,bd/pk) = 1 (else
the point would vanish trivially over Fp). Finally we translate into Fp by taking these coordinates modulo
p. Thus in summary,
(a
b, c
d
)
↦→ (ad (mod p),bc (mod p),bd (mod p)), modulo some conditions on clearing
denominators with powers of p.
As promised before, we can now present the identity of the group E(Q): it’s (0 : 1 : 0). This furthermore
shows that the identity of E(Fp) is also (0 : 1 : 0). This gives us the following corollary (corollary of what I
wonder...)
Problem 6.2 (An Odd Divisor; 5). Let p be a prime. Prove p divides some term of the Tiger sequence
{an} if and only if P = (0, 0) has odd order in the group E(Fp) where E :y2 +y =x3−x.
This is a rather magical connection between divisibility of a sequence and elliptic curves, don’t you think?
However, strangely enough, we will soon be able to make even weirder equivalent statements.
15
PUMaC 2015 Power Round Section 7 page 16
7 Galois Theory
Unfortunately, for the sake of time (we can’t build up all of Galois theory from scratch for this Power
Round!), we won’t be able to give more than a heuristic of some of the methods we use here. (Un)Luckily
for you, the reader, this also means there aren’t many problems directly on Galois theory :(. We hope that
regardless of your mathematical background, this section is still interesting enough to try to understand. We
describe ﬁrst some of the necessary groundwork.
We previously introduced a fundamental object of algebra: groups. This was essentially the most basic
“thing” we could do math on. We have only one operation on a group at all times. Anything simpler would
have very little to it. Since then, we further saw a taste of more complicated algebraic objects, which as
promised, we explore here. One step up from the group is another essential object of mathematics: a ring.
Rings in some sense can be thought of as an extension of (additive) groups.
Deﬁnition 27. Let R be a set of elements that has a closed, binary operation we call addition such that
{R, +} is an additive, commutative group and a second closed, binary, commutative operation· that we can
call multiplication. Suppose R has these properties:
• The operation· is associative.
• For alla,b,c ∈R,
a· (b +c) =a·b +a·c,
and
(b +c)·a =b·a +c·a.
• Finally, there exists a multiplicative identity we call 1 such that for all a∈R, a· 1 = 1·a =a.
Then R is called a ring.
The consequences of such a deﬁnition is thatR contains 0 (necessary by the addition law), and 1 (necessary
by the multiplication law). Many deﬁnitions also add that 1 ̸= 0, but this is not strictly necessary.
Problem 7.1 (0 Ring; 5). Let A :={0} be the set of just the element 0. Let + and· be operations on A
such that 0 + 0 = 0· 0 = 0. Prove or disprove that A is a ring.
If you ﬁnd the deﬁnition of rings a little scary looking, all it really says is that a ring is something like
the integers Z. (Mathematicians have this tendency of taking familiar objects like the integers and building
abstractions of them. If you see one of these abstractions ﬁrst, they can seem intimidating. But, if you know
where the abstraction came from, you might see that it is quite natural. Rings are one example of this.)
However, if you recall from the exercises in section 3, the integers are missing something. This leads us to
something else called a ﬁeld.
Deﬁnition 28. LetK be a ring where 1̸= 0. Furthermore let K also have the additional property that for
all non-zero elements a,∃a−1∈K such that a·a−1 =a−1·a = 1. Then K is called a ﬁeld.
Again, this is an example of an abstraction of a natural object. A ﬁeld really emulates the properties
of the rational numbers Q. In the same way Q is built from Z, ﬁelds are built from rings. Also, note the
relationship between rings and ﬁelds. A ﬁeld is always a ring, but not the other way around.
There are many examples of ﬁelds. While Q may have been a motivating example for the abstraction
for a ﬁeld (history fun fact: I have no idea if this is true. I made it up because this might be true...), ﬁelds
are so common that you probably already know many other examples. A few more examples of ﬁelds are
the real numbers R; the complex numbers C; and ﬁnite ﬁelds Z/pZ = Fp. Something of interest is that the
16
PUMaC 2015 Power Round Section 7 page 17
rational numbers are a subset of the real numbers; we write this Q⊂ R and say that Q is a sub-ﬁeld of R;
equivalently, we also say that R is a ﬁeld extension of Q. Another example is R⊂ C. We can say much more
about the relationships between ﬁelds than characterizing them as subsets of each other.
The only thing that R really lacks compared to C is the number i. Every complex number is the
combination of a real part and an imaginary part. This gives us another way to construct C. We may write
C∼= R[i]. This notation R[i] means we take the set of real numbers R, and also add in the element i. We
can then take any ﬁnite sum of scalar multiples of powers of i. More formally,
R[i] :={c0 +c1·i +c2·i2 +c3·i3 +c4·i4 +··· +cn·in :n∈ N,ci∈ R}.
Notice that since i2 =−1·i0, any power of i greater than 1 may be re-written as a power less than 2.
Thus in practice, we may also write R[i] ={c0 +c1·i :ci∈ R}. This shows us why we call R a ﬁeld extension
of Q—we build the former by literally adding things to the latter.
In general, if R is a ring, R[α] is deﬁned similarly.
Deﬁnition 29. LetR be an arbitrary ring. Ifα is algebraic overR, thenR[α] :={∑n
i=0ciαi :n∈ N,ci∈R}.
There are some conditions necessary on the value of α—namely that α be algebraic. However, algebraic
numbers are something we do not address here (for interested readers, this is what transcendental numbers
pertain to). Now to make sure things make sense so far, here is a problem.
Problem 7.2 (Fields; 4, 2, 2, 4 ).
a) Examine Q[
√
2]. Setwise, are Q[
√
2] and{a +b
√
2 : a,b ∈ Q} equivalent? Why or why not? (Keep in
mind the justiﬁcation of R[i] ={c0 +c1·i : ci∈ R} was not fully ﬂeshed out. You must start with an
arbitrary maximum degree n and reduce it to 1.)
b) Is 1
8 inside Z[ 1
2]? Why or why not?
c) Is 1
3 inside of Z[ 1
6]? Why or why not?
d) Are Q[
√
2] and Q[
√
3] equivalent? (Two ﬁelds are equivalent if they are setwise equivalent; i.e. K andF
are equivalent ﬁelds if K⊂F and F⊂K.) Why or why not?
Finally, a more “professional” way to think about R[i]∼= C comes from realizing that i is a root of the
polynomial x2 + 1. Notice that the two roots of x2 + 1 are ±i. This leads to the construction denoted
R[x]/(x2 + 1), which we take to mean that we adjoin to R a root of the polynomial x2 + 1 (it doesn’t
matter if we take i or−i since they give equivalent ﬁelds). In this case, adjoining to R a root of x2 + 1
is exactly the same as adjoining i. Thus we now have three ways of representing the complex numbers:
C∼= R[i]∼= R[x]/(x2 + 1). This latter notation is most important for us. It demonstrates a way of thinking
about ﬁeld extensions: adjoining roots of polynomials. This leads naturally to the concept of Galois groups.
Deﬁnition 30. For certain rational polynomials f(x), the details of which we omit for the sake of time,
Q[x]/(f(x)) is called a Galois extension.
(The speciﬁcs of what polynomials are necessary is omitted. They involve deﬁnitions which are unnec-
essary in the scheme of this Power Round, but speciﬁc polynomials make their ﬁeld extensions Galois.)
Examine all the roots of f(x) that exist in this new ﬁeld K but don’t exist in Q. We can form a group
(of functions) that acts on these roots by sending them to each other. For example, for the construction
Q[x]/(x2 + 1), we can imagine a function that sends i to−i and vice versa (this is conjugation). The impor-
tant thing about conjugation is that it sends rational numbers to rational numbers: it ﬁxes elements that
17
PUMaC 2015 Power Round Section 8 page 18
were in the base ﬁeld. We assert that conjugation and the “do nothing” function (the identity function) are
the only such functions that exist. They act on Q[x]/(x2 + 1) but are the identity function when restricted
to Q. Thus our group of functions has two elements: the conjugation function, and the identity function.
We encourage the reader to convince themself that this small thing is indeed a group. In general, this group
that we construct of functions is known as the Galois group of the ﬁeld extension.
Deﬁnition 31. SupposeK = Q[x]/(f(x)) is a Galois extension. Then σ :K→K is a Galois automorphism
if the following hold:
• If a∈ Q, σ(a) =a (this is called “ﬁxing a”).
• Let A ={r∈K,r /∈ Q :f(r) = 0}. Then σ :A→A is a bijection.
• If α,β are two elements of K, then σ(α +β) =σ(α) +σ(β) and σ(α·β) =σ(α)·σ(β).
Deﬁnition 32. LetG be the set of all Galois automorphisms of a ﬁeld extension K of Q. Then G is a group
that is denoted Gal(K/Q) and called the Galois group of K.
In practice, to form a Galois automorphism, focus ﬁrst on the second condition. If you impose conditions
on where the roots are sent and let rational numbers remain unchanged, the other properties tend to work
out as well.
Problem 7.3 (Galois Automorphisms; 2, 8). Let f(x) =x4− 70x2 + 25.
a) What are the roots of f(x)?
b) You are given that f(x) is a nice enough polynomial that Q[x]/(f(x)) is a Galois. Give four examples of
Galois automorphisms—an isomorphism from one set to itself. (You may just tell us where each root is
sent for each automorphism).
Before moving on though, we can go even further than what we have done here; we can adjoin multiple
roots of many diﬀerent polynomials at once to Q. For example, a classic example you may see if you study
mathematics more is adjoining to Q the roots of bothx2 +x+1 and x3−2 at the same time to yield Q[ω,
3√
2]
for ω a primitive 3rd root of unity.
8 Elliptic Curves and Galois Theory
Galois theory is incredibly rich, but unfortunately there are details we must omit about the subject for the
sake of time, and this is suﬃcient background; we can now relate Galois theory and elliptic curves. Suppose
you have a general elliptic curve E and a general point P on it. We deﬁne a k-division point of P as some
point Q on E such that kQ =P . A fact of elliptic curves is that there are exactly k2 suchk-division points
in C (the coordinates of Q may be complex numbers), but likely many of them won’t be rational points.
But examine for a moment such a non-rational point βk such that kβk =P . Suppose we take the x and y
coordinates of βk and adjoined them to Q. What would we get? Going further, suppose we took all such
βki such that kβki = P and adjoined to Q all of the x and y coordinates of these division points. We get
some large ﬁeld extension we label Kk. This directly gives us a way to use Galois theory in a way that gives
us information about our initial E and P .
Take on faith thatKk/Q is indeed a Galois extension, and examine some Galois automorphism σ of this
extension; it acts on all these coordinates we just adjoined. Let ( a,b ) be one of the k-division points; then
18
PUMaC 2015 Power Round Section 8 page 19
σ((a,b )) = (σ(a),σ (b)). Now we have a curious situation: we have found a Galois automorphism that acts
on points on an elliptic curve! Weee.
That these Galois automorphisms act on the set of k-division points is important. Can you visualize
how they are acting? These functions send coordinate pairs, essentially vectors, to other vectors. This is
quite similar to how matrices act on vectors! In fact, this leads to what is called a Galois representation: a
homomorphism from the Galois group to a linear algebra construct. Here we become guilty of omitting some
details, but it would take too much work to present in full rigor. But please take these two propositions to
be true.
Proposition 33. Let E :y2 +y =x3−x, P = (0, 0), and let Kk be the ﬁeld described above, namely the
ﬁeld extension of Q by adjoining all the coordinates of the k-division points of P . Then there is a surjective
homomorphism from the Galois group Gal(Kk/Q) to AGL2(Z/2kZ) = ( Z/2kZ)2 ⋊GL2(Z/2kZ). Denote
this by ϕ : Gal(Kk/Q)→AGL2(Z/2kZ).
A quick word on notation here. We deﬁned the semidirect product in Proposition 16, and here we see an
example of one. For an element of such a groupAGL2(Z/2kZ), we will write it as (⃗ v,M) where⃗ v∈ (Z/2kZ)2
and M∈GL2(Z/2kZ).
Proposition 34. Let E :y2 +y =x3−x and P = (0, 0) be a point on E. Let ℓ be a prime larger than 37.
Then P has odd order in E(Fℓ), the reduction of the curve to this ﬁnite ﬁeld, if and only if for all k∈ N,
∃(⃗ v,M)∈AGL2(Z/2kZ) such that ⃗ vlies in the column space of M−I (the column space of a matrix such
as (M−I) is the set{(M−I)·⃗ v,⃗ v∈ (Z/2kZ)2}).
Let’s parse this last proposition; recall from the interlude that prime ℓ divides some term of the sequence
if and only if P has ﬁnite order in E(Fℓ). We saw earlier as well in problem 3.6 that this happens if and
only if for all integers i, there exists some element βi∈E(Fℓ) such that 2i·βi =P . Finally, this condition
is equivalent to the latter part of the above proposition. If you are familiar with Galois theory, as a hint of
why this might be true, the fact that such a βi exists implies that it is ﬁxed by the Fr¨ obenius automorphism.
This leads to the fact that AGL2(Z/2kZ) acting on ( Z/2kZ)2 ﬁxes some element ⃗ x. Thus ( ⃗ v,M)(⃗ x) :=
M·⃗ x+⃗ v=⃗ x=⇒ (M−I)⃗ x=−⃗ v. From here it’s easy to see that ⃗ v∈ im(M−I)⇔−⃗ v∈ im(M−I).
Deﬁnition 35. Let (⃗ v,M)∈AGL2(Z/2kZ) be an element of the aﬃne general linear group. We call (⃗ v,M)
a ruminative element if ⃗ vis in the column space of M−I.
For the observant reader, another way to describe this element ( ⃗ v,M) is to say that M ﬁxes a vector
⃗ x∈ (Z/2kZ)2 where the action of AGL2(Z/2kZ) on ( Z/2kZ)2 is as described above.
Thus we have come from an original question about primes dividing terms of a sequence to a question
about the column space of matrices. This latter is something that we can much more likely solve directly.
(In general, this is a useful strategy. Linear algebra is a subject that is very well understood compared to
other mathematical subjects. This is the motivation behind group representations, for example. In fact,
that linear algebra is so well understood has given rise to the half-serious joke of dismissing a problem by
saying, “it’s just linear algebra!”) For one ﬁnal step before we try to use linear algebra to ﬁnd a fraction, we
present the Chebotarev Density Theorem.
Theorem 36. Suppose K/Q is a Galois extension with G := Gal(K/Q) where C⊂G is a conjugacy class
of G. Deﬁne πC(x) := #{p≤x :p is a prime that is unramiﬁed in K and
[K/Q
p
]
=C}. Then
lim
x→∞
πC(x)
π(x) =|C|
|G|.
19
PUMaC 2015 Power Round Section 8 page 20
(The deﬁnition of unramiﬁed is unimportant for us. In our speciﬁc case, this equivalently means primes
that are greater than 37.) As written, this doesn’t seem to necessarily apply to anything we’ve written so
far. However, one of the facts that we obscured in our presentation of the two propositions above is that the
images of the Galois groups above are in fact images of conjugacy classes. The ultimate result of all of this
is the following.
Proposition 37. Let π(x) denote the number of primes less than x, and let π′(x) denote the number of
primes less than x that divide some term of the Tiger sequence. Let S represent the conjugacy class of
Gal(Kk/Q) of theβk such that 2k·βk =P . Let S′ := im(S) andAGL2(Z/2kZ) = im(Gal(Kk/Q)) represent
the images under the homomorphism ϕ : Gal(Kk/Q)→AGL2(Z/2kZ) from above. Then
lim
x→∞
π′(x)
π(x) = lim
k→∞
lim
x→∞
|S|
| Gal(Kk/Q)|
= lim
k→∞
|S′|
|AGL2(Z/2kZ)|.
In other words, the ﬁnal fraction we have to compute is the last expression in the proposition above. The
best way to interpretS′ in the above is thatS′ is the subset ofAGL2(Z/2kZ) that consists of the ruminative
elements.
20
PUMaC 2015 Power Round Section 9 page 21
9 Final Fraction
Thus we are only left with calculating the density! Here are the ﬁnal steps.
Deﬁnition 38. Let vp : Z→ Z be a function such that vp(n) = m, where m is the exponent of p in the
prime factorization of n. For example, v2(24) = 3, v3(8) = 0, and v5(−25) = 2.
Proposition 39. Let M∈ GL2(Z/2kZ) be a matrix such that v2(det(M−I)) = r. Then the number of
elements in the column space ofM−I is 22k−r. (Two notes: we do not regard the cases where det(M−I) = 0,
and by deﬁnition, det(M−I) is reduced to be the integer n such that 0≤ n <2k and n≡ det(M−I)
(mod 2k) where det(M−I) is evaluated in Z.)
Problem 9.1 (Final Fraction; 10, 10, 10, 10 ). In all but the last sub-problem here, assume that k is a
ﬁxed positive integer and we examine elements of AGL2(Z/2kZ) or GL2(Z/2kZ) as the problem dictates.
Vectors are arbitrary element (⃗ v,M)∈AGL2(Z/2kZ).
a) Error notice: The problem originally stated here was incorrectly phrased. Due to the fact that we are
sending out a revision so late, we are awarding everyone the full 10 points for this problem. The problem
should have been Proposition 39, which you may assume is true.
b) Suppose that a,b ∈ Z/2Z, c∈ Z/2nZ, and n≥ 2. Prove the number of pairs (α,β )∈ (Z/2nZ)2 with
αβ≡c (mod 2n) with α≡a (mod 2) and β≡b (mod 2) is



0 ab̸≡c (mod 2),
2n−1 ab≡ 0 (mod 2) and one of a or b is nonzero,
(2− 1)(v2(c)− 1)2n−1 a≡b≡c≡ 0 (mod 2) ,c̸≡ 0 (mod 2 n),
n2n−1 a≡b≡c≡ 0 (mod 2) ,c≡ 0 (mod 2 n).
(As a note, the factor (2− 1) is correctly present, and it is not a typo.)
c) For n≥ 1, prove the number of matrices M∈ GL2(Z/2kZ) with det(M−I)≡ 0 (mod 2k−1) but with
det(M−I)̸≡ 0 (mod 2k) is {
2 k = 1,
3· 23k−2− 3· 22k−1 k≥ 2.
d) Prove that the density of primes dividing a term of the Tiger sequence is 11
21.
That’s it! We hope you’ve had a fun ride.
21
Team Number:
PUMaC 2015 Power Round Cover Sheet
Remember that this sheet comes ﬁrst in your stapled solutions. You should submit solutions for the problems
in increasing order. Write on one side of the page only. The start of a solution to a problem should start on
a new page. Please mark which questions have been attempted and for which you have submitted solutions
to help us keep track of your solutions.
Problem Number Points Attempted?
3.1 a) 2
3.1 b) 2
3.1 c) 2
3.1 d) 2
3.2 5
3.3 5
3.4 5
3.5 10
3.6 5
4.1 a) 2
4.1 b) 8
4.2 a) 2
4.2 b) 2
4.3 a) 2
4.3 b) 8
4.4 5
4.5 a) 2
4.5 b) 2
4.6 10
Problem Number Points Attempted?
5.1 a) 5
5.1 b) 2
5.2 10
5.3 5
5.4 a) 8
5.4 b) 12
6.1 5
6.2 5
7.1 5
7.2 a) 4
7.2 b) 2
7.2 c) 2
7.2 d) 4
7.3 a) 2
7.3 b) 8
9.1 a) 10
9.1 b) 10
9.1 c) 10
9.1 d) 10
Total: 200 ≥ 10
Figure 4: Graphical View of kP.
