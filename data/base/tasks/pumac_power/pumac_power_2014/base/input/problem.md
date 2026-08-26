# PUMaC Power Round 2014

2014 PUMaC Power Round
Princeton University
Why are numbers beautiful? It’s like asking why is
Beethoven ’s Ninth Symphony beautiful. If you don ’t
see why, someone can ’t tell you. I know numbers are
beautiful. If they aren ’t beautiful, nothing is.
Paul Erd¨ os
1 Rules and Reminders
These rules supersede any rules appearing elsewhere about the Power Round:
1. On any problem, you may use without proof any result or remark from
earlier in the test, even if it’s a problem your team has not solved. You
may cite results from conjectures or subsequent problems only if your team
solved them independently of the problem where you wish to cite them.
2. You may not cite parts of your proof of other problems: if you wish to
use a lemma in multiple problems, please reproduce it in each one.
3. It is not necessary to do the problems in order, although it is a good idea
to read all the problems, so that you know what is permissible to assume
when doing each problem. However, please collate the solutions in order
in your solution packet. Each problem should start on a new page, and
solutions should be written on one side of the paper only. Each page
should also have on it the team name and problem number.
4. Using computer programs, calculators, and Mathematica (or similar pro-
grams), is allowed. However, print and online references are not
allowed.
5. No communication with humans outside your team about the content of
these problems is allowed. If you have any questions regarding the test,
please contact us at once at pumac@math.princeton.edu.
1
2 Background
We write
1. N for the set of positive integers.
2. Z for the set of integers.
3. Q for the set of rational numbers.
4. C for the set of complex numbers.
2.1 A Little Number Theory Background
Deﬁnition 1 (Congruence). Let a, b, nbe integers with n̸= 0. We say that a
and b are congruent modulo n if n|a−b, and denote this by a≡b (mod n). If
n̸|a−b, we say that the integers a, bare not congruent modulo n and write
a̸≡b (mod n).
For instance, 7≡1 (mod 3), and 23 ̸≡2 (mod 5).
Remark. It is known (and very easily veriﬁed) that the congruence relation
deﬁned above is an equivalence relation that satisﬁes the following properties:
1. a≡a (mod n) (reﬂexivity);
2. If a≡b (mod n) and b≡c (mod n), then a≡c (mod n) (transitivity);
3. If a≡b (mod n), then b≡a (mod n) (symmetry);
4. If a≡b (mod n) and c≡d (mod n), then ka + lc≡kb + ld (mod n) for
all integers k, l∈Z.
5. If a≡b (mod n) and c≡d (mod n), then ac≡bd (mod n).
6. If ka≡kb (mod n) and gcd( k, n) = d, then a≡b (mod n
d ).
In general, a binary relation a≡b is called an equivalence relation if it
satisﬁes reﬂexivity, symmetry and transitivity.
The following theorems may be helpful.
Theorem 2 (Fermat’s Little Theorem). Let a be a positive integer and let p be
a prime such that (a, p) = 1. Then
ap−1≡1 (mod p).
Proof. Fix an integera such that (a, p) = 1. Note that the integers a,2a,···,(p−
1)a are all distinct modulo p, so up to a permutation, the sets {a,2a,···,(p−
1)a}and{1,2,···, p−1}are congruent. This means that their products are
congruent modulo p, that is,
(p−1)!ap−1≡(p−1)! (mod p).
Cancelling (p-1)! from both sides (this is possible because ( p−1)! is coprime to
p), we have the desired equality ap−1≡1 (mod p) immediately.
2
An important question throughout the process of this Power Round would
be whether the congruence x2≡a (mod p) has a solution x∈Z given an integer
a and a prime p. The following concept will be extremely helpful.
Deﬁnition 3 (Quadratic residue). Let a and m be integers such that m > 0.
We say that a is a quadratic residue mod m if the congruence x2≡a (mod m)
has a solution. Otherwise we say that a is a quadratic nonresidue.
Remark. 0,1,4 are quadratic residues modulo 5. 0 ,1,2,4 are quadratic residues
modulo 7. 0 ,1,4 are quadratic residues modulo 8.
The following notation will be useful.
Deﬁnition 4. Let p be an odd prime and let a be an integer not divisible by
p. The Legendre symbol of a with respect to p is deﬁned by
(a
p
)
=
{
1 if a quadratic residue modulo p
−1 otherwise
Remark. The Legendre symbol satisﬁes the following properties.
1. There are p−1
2 quadratic residues in the set {1,2,···, p−1}. (Proof:
{12,22,···,( p−1
2 )2 are distinct mod p and x2≡(p−x)2 (mod p))
2. (Euler’s criterion) If p is an odd prime and a an integer not divisible by
p, then (a
p
)
≡a
p−1
2 (mod p).
(Try proving using Fermat’s little theorem!)
3. If a≡b (mod p), then
(
a
p
)
=
(
b
p
)
4. (multiplicity)
(
ab
p
)
=
(
a
p
)(
b
p
)
Theorem 5 (Quadratic Reciprocity). Given two odd primes p̸= q, we have
(p
q
)( q
p
)
= (−1)
(p−1)(q−1)
4 .
Stated diﬀerently,
(
p
q
)
=
(
q
p
)
unless p≡q≡3 (mod 4) .
2.2 Background for This Year’s Power Round
This year’s Power Round concerns the following interesting mathematical ob-
ject.
3
Deﬁnition 6 (Conic Polynomial). A Conic Polynomial involving n variables
X1, X2,···, Xn is the homogeneous polynomial
f = f(X1, X2,···, Xn) =
∑
1≤i,j≤n
ai,jXiXj
where ai,j are real numbers and the sum ranges over all pairs ( i, j) with
1≤i≤n and 1≤j≤n.
We may write this conic polynomial in the following matrix notation :
f = X T AX =
(X1 X2 ···Xn
)


a1,1 a1,2 ···a1,n
a2,1 a2,2 ···a2,n
... ... ... ...
an,1 an,2 ···an,n
(



X1
X2
...
Xn
(

We say that a conic polynomialf is integral if for all integersX1, X2,···, Xn,
f(X1, X2,···, Xn) is also an integer.
We can easily see that the forms x2 + 3xy + 5y2, x2−y2 are two-variable
integral conic polynomials, and x2 + y2 + z2, xy + xz are three-variable integral
conic polynomials.
Deﬁnition 7. Multiple matrices may be associated with the same conic poly-
nomial. For example, the conic polynomial x2 +4 xy + y2 can be associated with
the two matrices
A1 =
(1 3
1 1
)
and
A2 =
(1 4
0 1
)
.
However, there is a unique way to associate a conic polynomial with asymmetric
matrix A = (ai,j) with ai,j= aj,i. For example, x2 + 4xy + y2 is associated to
the following matrix
A =
(1 2
2 1
)
.
We call this matrix the symmetric matrix associated to a conic polynomial f.
If the symmetric matrix associated to a conic polynomial f has integer entries,
we say that f has integer matrix.
Deﬁnition 8. We say that a conic polynomial f(X1, X2,···, Xn) is integral if
f(X1, X2,···, Xn) is an integer for all integers X1, X2,···, Xn. Note that this
is not equivalent to the fact that f has integer matrix.
Deﬁnition 9. We say that a conic polynomial f(X1, X2,···, Xn) represents
an integer d∈Z if f(X1, X2,···, Xn) = d has a solution with Xi∈Z for all i.
4
Deﬁnition 10. We say that a conic polynomial f is positive-deﬁnite if f≥0
for all integer inputs and f = 0 iﬀ all arguments are zero.
Deﬁnition 11. We say that a positive-deﬁnite conic polynomial f is universal
if f represents all nonnegative integers.
Let’s begin by gaining some intuition on these conic polynomial, and get
used to the deﬁnitions.
Problem 1. (8 points)
1. (3) Show that a conic polynomial
f(x1, x2,···, xn) =
∑
1≤i,j≤n
ai,jxixj
is integral if and only if ai,i∈Z and ai,j+ aj,i∈Z.
2. (1) Find an integral conic polynomial that does not have integer matrix.
3. (1) Find a conic polynomial with two or less variables that can represent
all integers.
4. (3) What integers can the following conic polynomials represent? A
good answer should (1) be exhaustive (should not leave out representable
integers), (2) be correct (should not say an integer is representable when
it’s not), (3) prove 1 and 2 (the proof can be concise).
(a) f(x, y) = x2−y2
(b) f(x, y) = x2−4xy + 4y2
(c) f(x, y, z) = x2−y2 + z2
3 Binary Conic Polynomial
Deﬁnition 12. A binary conic polynomial is a conic polynomial with two vari-
ables. It may be written in the form ax2 + bxy + cy2.
In this section, we will look at examples of how binary conic polynomials can
represent positive integers. We focus our attention on positive-deﬁnite binary
conic polynomials.
We ﬁrst look at a canonical example: x2 + y2.
Problem 2. (15 points)
1. (2) Assume positive integers m, nare both representable by the conic
polynomial f(x, y) = x2 + y2. Show that so is mn.
2. (2) If p is a prime of the form 4 k + 3, show that p|x2 + y2 implies p|x and
p|y.
5
3. (2) If p is a prime of the form 4 k + 1, show that t2≡−1 (mod p) has a
solution t∈Z
4. (5) If p is a prime of the form 4 k + 1, show that p is representable by the
conic polynomial f(x, y) = x2 + y2.
(Hint: Prove and use the following lemma on the solution t of the previous
problem.
Lemma. Given an odd prime p and an integer t, the following congruence
tx + y≡0 (mod p)
has a solution ( x, y) with 0≤|x|<√p, 0≤|y|<√p, (x, y)̸= (0,0))
5. (4) Classify all positive integers that can be represented by the form
f(x, y) = x2 + y2.
We look at more examples that can be proved with similar techniques.
Problem 3. (20 points)
1. (10) Classify all positive integers that can be represented by the form
f(x, y) = x2 + 2y2.
2. (10) Classify all positive integers that can be represented by the form
f(x, y) = x2 + 3y2.
Note that the form x2 + y2 will represent the same set of integers as the form
x2 +( x+ y)2 = 2x2 +2 xy + y2. However, we also note that the form x2 + y2 does
not represent the same set of integers as the formx2+(x+3y)2 = 2x2+6xy+9y2.
(Why?)
With this intuition, we deﬁne the notion of equivalence among binary conic
polynomial as follows.
Deﬁnition 13. Given a binary conic polynomial f(x, y), we say that F (x, y) =
f(ax + by, cx+ dy) is equivalent to f if|ad−bc|= 1.
Problem 4. (5 points)
1. (3) Show that this deﬁnes an equivalence relation over binary conic poly-
nomials: that is, the equivalence relation is reﬂexive, symmetric, and tran-
sitive. (See the deﬁnition of congruence above for what these words mean.)
2. (2) Show that two binary conic polynomials are equivalent only if they
represent the same set of integers.
We deﬁne the discriminant of a binary conic polynomial as follows:
Deﬁnition 14. Given a binary conic polynomial f(x, y) = ax2 + bxy + cy2, we
deﬁne its discriminant D(f) = b2−4ac.
Problem 5. (10 points)
6
1. (1) Assume that D(f) < 0 and a > 0. Prove that f is positive-deﬁnite.
Does the converse hold?
2. (3) Assume that f(x, y) = ax2 + bxy + cy2 represents a prime p. Show
that D(f) is a quadratic residue modulo p.
3. (6) Show that equivalent binary conic polynomials have the same dis-
criminant. Does the converse hold?
Problem 6. (31 points) (Miscellaneous problems)
These problems are intended to give you better intuition about representa-
tions of integers with conic polynomials. Have fun, do not be intimidated - even
Fermat and Euler had a hard time with this theory!
1. (2) Given an odd prime number p, show that
(−5
p
)
= 1 ⇔p≡1,3,7,9 (mod 20) .
Does it imply that every such prime may be written in the form x2 + 5y2
for integers x, y? (This contrasts with some previous problems)
2. (3) Prove that if
(
−5
p
)
= 1 for an odd prime p, then either p or 2p can
be represented by x2 + 5y2.
3. (5) For an odd prime p such that
(
−23
p
)
= 1, show that either p or 3p
can be represented by the form x2 + 23y2. Does the converse hold?
4. (3) In a previous problem, we showed that x2 + y2 = p has a solution for
primes p congruent to 1 modulo 4. Is this representation unique? That
is, assume we have a2 + b2 = c2 + d2 = p. Must it be the case that
{a, b}={c, d}?
5. (5) Assume that a prime p can be written in the form 3 x2 + 7y2. Show
that this representation is unique for x, ynon-negative.
6. (5) For pairwise relatively prime integers a, b, c, consider the conic poly-
nomial f(x, y) = ax2+bxy+cy2. Given any positive integer M, prove that
you can ﬁnd non-negative integers x0, y0 such that f(x0, y0) is relatively
prime to M.
7. (5) Given a positive integer n and coprime integers a, b, write N =
a2 + nb2. Assume that there exists a prime divisor q of N such that
q = x2 + ny2 for x, y∈Z. Show that N
q = c2 + nd2 for (c, d∈Z).
8. (3) Denote the subsets A, B of positive integers as follows:
A ={n|n < 22000, n= 2x2−3y2 for some x, y∈Z}
B ={n|n < 22000, n= 10xy−x2−y2 for some x, y∈Z}
Determine which of A or B is larger.
7
4 A Conic Polynomial Expressing All Integers
In this section we attempt at ﬁnding a positive-deﬁnite square: namely, x2 +
y2 + z2 + w2.
Problem 7. (20 points) In this section, denote by f(x, y, z, w) the positive-
deﬁnite conic polynomial x2 + y2 + z2 + w2.
1. (3) Show that if integers m, ncan be represented by f, then so can mn.
2. (5) Given an odd prime number p, show that there exists an positive
integer t < p such that tp can be represented by f.
3. (2) If t0 is the smallest positive integer t such that t0p can be represented
by f, show that t0 is odd.
4. (5) Given t0 as above, if t0 > 1, show that st0 can be represented by f
for some positive integer s < t 0.
5. (3) Show that t0 = 1. (So the statement above was actually vacuously
true. But using the above statement will probably help!)
6. (2) Show that every positive integer can be represented by f.
In fact, it can be shown that more than 40 forms of the form ax2 + by2 +
cz2 + dw2 can represent all nonnegative integers - we investigate this further in
subsequent sections.
5 Ternary Conic Polynomial
Now that we have seen an example of a universal positive-deﬁnite conic polyno-
mial, we dig deeper into analyzing conic polynomials. Much has been discussed
about polynomials of two variables, and you may have noticed that two-variable
conic polynomials represent a small subset of the positive integers. In the three-
variable case, however, it is diﬀerent – it represents a substantial portion of the
positive integers. Let’s see how it goes.
Deﬁnition 15. A ternary conic polynomial is a conic polynomial f(x, y, z) with
three variables.
Much of the facts about ternary conic polynomials is not elementary - it
requires extensive use of theories beyond the number theory most of you know.
Everything here, with a bit of hints tho, are approachable with elementary
number theory. Good luck!
For this section and this section ONLY, you may use the following theorem
to your advantage:
Theorem 16 (Dirichlet’s Theorem on Arithmetic Progressions) . If a, b are
positive integers such that (a, b) = 1 , there are inﬁnitely many primes of the
form an + b where n∈Z.
8
We ﬁrst look at the ”basic” ternary form x2 + y2 + z2.
Problem 8. (55 points)
1. (5) Let n = 4 m(8k + 7) for nonnegative integers m, k. Prove that n
cannot be represented by x2 + y2 + z2.
2. (15) Given an integer n, assume that the equation n = x2 + y2 + z2 has
rational solutions ( x, y, z). Prove that the equation has a solution with
x, y, zintegers.
3. (10) Given a squarefree integerm≡1 (mod 4), show that you can choose
a prime q of the form 4 k + 1 such that−q is a quadratic residue mod m
and m is a quadratic residue mod q.
4. (5) Do the same for m≡2 (mod 4).
5. (10) Given a squarefree integer m≡3 (mod 8), show that you can ﬁnd
a prime q of the form 8 k + 5 such that−2q is a quadratic residue mod m
and m is a quadratic residue mod q.
6. (10) Using the three previous problems and Legendre’s theorem, show
that a positive integer m not of the form 4 l(8k + 7) is the sum of three
rational squares. What can we say about the numbers that can be repre-
sented by the conic polynomial f(x, y, z) = x2 + y2 + z2?
Remark. Legendre’s theorem is the following:
Theorem 17 (Legendre’s theorem). Given integers a and b, the equation
z2 = ax2 + by2 has a nontrivial solution (x, y, z) if and only if a, bare not
both negative, and b is a quadratic residue mod |a|and a is a quadratic
residue mod|b|.
It should be noted that this section solves the question posed at the previous
section too! In fact, it proves more.
Problem 9. (5 points)
1. (5) Show that the conic polynomials f(x, y, z, w) = x2 + y2 + z2 + dw2
for 1≤d≤7 are universal.
6 Universal Conic Polynomials
In this section we attempt to classify some universal conic polynomials. These
will turn out to be a large portion of all universal conic polynomials!
Problem 10. (20 points)
1. (5) Assume that a conic polynomial ax2 + by2 + cz2 + dw2 is universal,
and let 1≤a≤b≤c≤d. Show the following:
9
(a) a = 1
(b) b≤2
(c) When b = 1, c≤3, and when b = 2, c≤5.
2. (15) Given the following information:
(a) x2 + y2 + 2z2 represents all integers not of the form 4 m(16n + 14)
(b) x2 + y2 + 3z2 represents all integers not of the form 9 m(9n + 6)
(c) x2 + 2y2 + 2z2 represents all integers not of the form 4 m(8n + 7)
(d) x2 + 2y2 + 3z2 represents all integers not of the form 4 m(16n + 10)
(e) x2 + 2y2 + 4z2 represents all integers not of the form 4 m(16n + 14)
(f) x2 + 2y2 + 5z2 represents all integers not of the form 25 m(25n + 10)
or 25m(25n + 15)
classify all universal conic polynomials of the form ax2 + by2 + cz2 + dw2.
7 Bonus Problems
This section asks problems that diverge from previous problems and look at
more general polynomials. Hence they are, in some sense, irrelevant to the
theory - hence the name. These are interesting problems that deserve attention
tho!
1. (10) Show that every positive integer is the sum of two squares and a
cube (of integers, not necessarily positive!).
2. (10) Show that every positive integer is the sum of three triangular
numbers. Triangular numbers are Tn = 1 + 2 +. . .+ n.
10
