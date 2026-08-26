# PUMaC Power Round 2012

2012 PUMaC Power Round
Princeton University
Why are numbers beautiful? It’s like asking why is
Beethoven ’s Ninth Symphony beautiful. If you don ’t
see why, someone can ’t tell you. I know numbers are
beautiful. If they aren ’t beautiful, nothing is.
Paul Erdös
1 Rules and Reminders
These rules supersede any rules appearing elsewhere about the Power Round:
1. On any problem, you may use without proof anyresult or remark from
earlier in the test, even if it’s a problem your team has not solved. You
may cite results from conjectures or subsequent problems only if your team
solved them independently of the problem where you wish to cite them.
You may not cite parts of your proof of other problems: if you wish to use
a lemma in multiple problems, please reproduce it in each one.
2. It is not necessary to do the problems in order, although it is a good idea
to read all the problems, so that you know what is permissible to assume
when doing each problem. However, please collate the solutions in order
in your solution packet. Each problem should start on a new page, and
solutions should be written on one side of the paper only. Each page
should also have on it the team name and problem number.
3. Using computer programs, calculators, and Mathematica (or similar pro-
grams), is allowed. This year, however,print and online references
are not allowed.
4. No communication with humans outside your team about the content of
these problems is allowed. If you have any questions regarding the test,
please contact us at once at pumac@math.princeton.edu.
1
2 Background
We write
1. Z for the set of integers.
2. Q for the set of rational numbers.
3. C for the set of complex numbers.
For convenience, letZ+ be the set of positive integers. We writeZ[X] for the set
of polynomials inX with coeﬃcients inZ, and more generally,Z[X1,...,Xn] for
the set of polynomials inX1,...,Xn with integer coeﬃcients. Similar notation
is used forQ and C. We writen∈Z+ to denote thatn is a member ofZ+.
Recall that, like real numbers, complex numbers have a notion of absolute
value: by deﬁnition,|a +bi|=
√
a2 +b2. For allz1,z 2∈C, we have|z1z2|=
|z1||z2|and|z1 +z2|≤|z1|+|z2|, just like for real numbers.
2.1 Deﬁnition.Let f be a polynomial inX1,...,Xn whose coeﬃcients are
not all zero. If f consists of one term, then thedegree of f, written degf, is
the sum of the exponents of theXj’s. In general,degf is the maximum degree
among all terms off.
For instance, iff (X) = a0 +a1X +...+adXd and ad̸= 0, then degf =d
as usual. Henceforth, we always assumead̸= 0 when writing a polynomial in
this form. We say thatadXd is the leading term of f, and ad is the leading
coeﬃcient. Note that the degree of the0 polynomial isundeﬁned.
2.2 Deﬁnition.A polynomialf (x1,x 2,...,xn) is homogeneousif (and only if)
each of its terms, individually, has the same degree as the others. Equivalently,
f is homogeneous if
f (λx1,λx2,...,λxn) = λdegff (x1,x 2,...,xn)
for anyλ̸= 0.
2.3 Deﬁnition.A number isalgebraic if it is the root of a nonzero polynomial
in Q[X]. All numbers that are not algebraic aretranscendental. We writeQ for
the set of algebraic numbers.
2.1 Remark. Important! Q is a subset ofC. More precisely, every polynomial
in Q[X] splits completely into linear factors inC[X]. The multiplicity of αas
a root of a polynomial is the exponent to which(X−α) appears in the linear
factorization of that polynomial inC[X].
2.4 Deﬁnition.Let α∈Q. The degree of α, written degα, is the minimum
degree among degrees of all nonzero polynomials inQ[X] that haveαas a root.
2.5 Deﬁnition.A polynomial in one variable ismonic if its leading coeﬃcient
is 1. A number is analgebraic integerif it is the root of a monic polynomial in
Z[X].
2
Here’s an example. Letα=
√
3. Note that αis a root of the polynomial
f (X) = X 2−3. Since αis not the root of a linear polynomial with rational
coeﬃcients,αis an algebraic number of degree 2. Since f is monic and has
integer coeﬃcients,αis actually analgebraic integer.
2.6 Deﬁnition.Let f =a0 +a1X +...+adXd∈C[X]. Deﬁne
∥f∥= max{|a0|,...,|ad|}
2.2 Remark. If S is a set, thenmaxS is the maximum among the elements of
S.
The following problems will not only develop our intuition for∥f∥, but will
also be useful later in the test.
2.1 (4 points)
Let f,g ∈C[X] such thatf̸= 0, and letα,β∈C.
1. (1) Show that
|f (α)|≤(1 + degf )∥f∥·max(1,|α|)degf
2. (1) Show that∥αf+βg∥≤|α|∥f∥+|β|∥g∥. where the notationf +g is
the sum of the polynomialsf and g.
3. (2) Prove∥fg∥≤(1 + degf )∥f∥∥g∥, wherefg is the product of polyno-
mials f and g.
2.2 (3 points)
Suppose f (X) = (X−α)rg(X), whereα∈C is nonzero,r∈Z+, andg∈C[X]
is nonzero. Prove that
∥g∥< (1 + degg)(2 max(1,|α|−1))degf∥f∥
2.3 (5 points)
1. (3) Let f,g ∈Q[X] such thatg̸= 0. Prove that there existq,r ∈Q[X]
such that
f (X) = q(X)g(X) +r(X)
and eitherr = 0 or degr< degg. Ifr = 0, then we sayg divides f.
2. (2) Why does the same statement hold withf,g,q,r ∈C[X]? Deduce
that αis a root off∈C[X] if and only iff (X) = (X−α)q(X) for some
q∈C[X].
3
2.4 (6 points)
Let f (X) = a0 +a1X +...+adXd. For all0≤k≤d, let
Dkf =
d∑
j=0
(j
k
)
ajXj−k
where (j
k
)
= j!
k!(j−k)!
for 0≤k≤j, and equals0 otherwise.
We abbreviate by writingDf =D1f.
1. (2) Show that∥Dkf∥≤2d∥f∥for all 0≤k≤degf.
2. (1) Show thatk!Dk(f ) = D(k)
1 (f ), whereD(k)
1 denotes the composition
of D1 with itselfk times.
3. (3) Show that ifD0(f )(α) = D1(f )(α) = ...= Dk−1(f )(α) = 0 , thenf
has a root of multiplicity at leastk at α.
2.3 Remark.You should verify the factD(fg ) = fDg +gDf and use it for part
3, though it carries no individual point value.
2.5 (4 points)
Suppose f,g ∈C[X] are nonzero such that
fDg =gDf
1. (1) Show that degf = degg.
2. (3) Show thatf,g diﬀer by a constant multiple.
3 Algebraic Numbers
3.1 (7 points)
Let α∈Q.
1. (1) Show that ifa,b ∈Q with a̸= 0, thenβ= aα+b is algebraic and
degβ= degα.
2. (1) Show there existsa∈Z+ such thataαis an algebraic integer.
3. (1) Suppose αis an algebraic integer. Show that ifb∈Z, thenα+b is
an algebraic integer.
4
4. (4) Suppose αis an algebraic integer, such thatf (α) = 0 for some monic
polynomial f∈Z[X] of degreed. Let r∈Z be nonnegative. Prove that
we can write
αr =
d−1∑
j=0
ar,jαj
for somear,j∈Z with|ar,j|≤(1 +∥f∥)r.
3.1 Deﬁnition.A polynomialf∈Z[X]issimple if there do not exist an integer
a> 1 and a polynomialg∈Z[X] such thatf (X) = ag(X). For example, the0
polynomial is not simple.
3.2 (7 points)
Let f∈Z[X].
1. (3) Suppose g∈Z[X]. Show that if the productfg is not simple, then
at least one off or g is not simple.
2. (2) Suppose insteadg∈Q[X]. Show that iff is simple andfg∈Z[X],
then g∈Z[X].
3. (2) Conclude that if a polynomial inZ[X] does not factor into two non-
constant polyomials in Z[X], then it cannot factor into two nonconstant
polynomials in Q[X].
3.2 Deﬁnition.For allα∈Q, letmα∈Q[X] be a monic polynomial of lowest
degree among all polynomials that haveαas a root.
3.1 Remark. Verify thatmαdivides any polynomial in Q[X] that hasαas a
root. (This will not be graded.)
3.3 (12 points)
Let α∈Q, and letf∈Q[X] be nonzero.
1. (2) Show that the roots ofmαall have multiplicity1, or in other words,
that they are pairwise distinct.
2. (2) Supposef does not factor into two nonconstant polynomials inQ[X].
Show the roots off are pairwise distinct algebraic numbers, each of degree
degf.
3. (2) Suppose αis a root of multiplicitym of f. Prove degf≥m degα.
4. (3) Suppose p/q∈Q is in lowest terms, and is a root of multiplicitym of
f. Also, supposef∈Z[X] and has leading coeﬃcienta. Proveqm≤|a|.
5. (3) Show that ifαis an algebraic integer, thenmα∈Z[X].
Hint: See Problem 2.3! Also, on parts 4 and 5, use Problem 3.2.
5
3.4 (6 points)
For all1≤i≤m, let
fi(X1,...,Xn) = ai,1X1 +...+ai,nXn∈Z[X1,...,Xn]
where n > mand|ai,j|≤A for alli,j for some ﬁxedA >0. Prove that there
exist x1,...,xn∈Z, satisfying
f1(x1,...,xn) = ...=fm(x1,...,xn) = 0
such that|xj|≤⌊(nA)m/(n−m)⌋for allj and xj̸= 0 for somej. We use the
notation⌊s⌋to denote the greatest integer not greater thans.
Hint: Use the Pigeonhole Principle. That is, if there areN pigeonholes and
M pigeons, whereM >N, then at least one pigeonhole must get> 1 pigeon.
4 Main Results
The problems in this section are very hard, so do not be discouraged if you get
stuck on some—or all!—of them. In what follows, letI = [−1/2, +1/2], the set
of realnumbers with absolute values of at most1/2.
4.1 (4 points)
Let 0 < ϵ <1/2. Show that if, for allαwhich are algebraic integers inI of
degree d≥3, ⏐⏐⏐⏐α−p
q
⏐⏐⏐⏐< 1
q1+ϵ+d/2
has only ﬁnitely many solutions for the rationalp/q in lowest terms, then, for
all αwhich are algebraic integers (not necessarily inI) of degreed≥1, it also
has only ﬁnitely many solutions for the rationalp/q in lowest terms.
4.2 (8 points)
Let d,m,n ∈Z+ such thatd≥3 and 1< md
n+1 < 2, and let
λ= 1−md
2n + 2
Letαbeanalgebraicintegerin I ofdegree d. Showthatthereexist P (X),Q (X)∈
Z[X] such that:
1. degP, degQ≤n.
2. ∥P∥,∥Q∥≤cn/λ
1 , for somec1 > 1 depending only onα.
3. Dj(P +αQ)(α) = 0 for all 0≤j <m.
4. P (X)/Q(X) is not constant inX.
Hint: Write down some linear equations and solve for the coeﬃcients ofP,Q
using Problem 3.4!
6
4.3 (10 points)
Letd,n,λ,m,α,P,Q,c1 be as in the previous problem. Letu =p/q andv =r/s
be rational numbers in lowest terms such thatq,s≥2 and
|α−u|< 1
qµand|α−v|< 1
sµ
for someµ>1. Prove that for all0≤j <m,
|Dj(P +vQ)(u)|≤cn/λ
2
( 1
qµ(m−j) + 1
sµ
)
for somec2 > 1 depending only onα.
Hint: Use the various facts aboutDk and∥·∥from section 2.
4.4 (12 points)
Let d,n,λ,m,α,P,Q,u = p/q,v = r/s be as in the previous problem. Prove
that
Dh(P +vQ)(u)̸= 0
for someh∈Z+ such thath≤1 + (c3/λ)n/ logq, wherec3 > 0 depends only
on α. Note that logq = logeq.
Hint: Recall part 4 of Problem 3.3.
4.5 (22 points)
Let 0<ϵ<1/2. Prove that for allα∈Q of degreed≥1,
⏐⏐⏐⏐α−p
q
⏐⏐⏐⏐< 1
q1+ϵ+d/2
has only ﬁnitely many solutions for the rationalp/q in lowest terms.
Hint: Assume that there are inﬁnitely many solutions. Lett be a an even
integer such thatt > 4d/ϵ−2 and let µ= 1 + ϵ+d/2. Given t, carefully
select n,λ,m,P,Q,u =p/q,v =r/s as in the above problems (u,v exist by the
assumption of inﬁnitely many solutions) and produce a contradiction between
the results of Problems 4.3 and 4.4.
7
