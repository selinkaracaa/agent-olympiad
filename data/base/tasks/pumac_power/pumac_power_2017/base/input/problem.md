# PUMaC Power Round 2017

PUMaC 2017 Power Round Page 1
PUMaC 2017 Power Round:
“I ain’t even Lie-in’...”
November 17, 2017
“Out of nothing I have created a strange new universe.” —J´ anos Bolyai
Rules and Reminders
1. Your solutions may be turned in in one of two ways:
• You may email them to us at pumac2017power@gmail.com by 8AM Eastern
Standard Time on the morning of PUMaC, November 18, 2017 with the subject
line “PUMaC 2017 Power Round.”
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
team has not solved. You may not cite parts of your proof of other problems: if you
wish to use a lemma in multiple problems, please reproduce it in each one.
PUMaC 2017 Power Round Page 2
6. When a problem asks you to “show,” “prove” or “demonstrate” a result, a formal
proof is expected, in which you justify each step you take, either by using a method
from earlier or by proving that everything you do is correct. When a problem instead
uses the word “explain,” an informal explanation suﬃces. When a problem asks you
to “ﬁnd” or “list” something, no justiﬁcation is required.
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
PUMaC 2017 Power Round Page 3
Introduction and Advice
The topic of this power round is Lie algebras (“Lie” pronounced as “Lee”). Lie al-
gebras are mathematical objects with a simple set of operations that leads to a powerful
classiﬁcation. Rather than being a trivial matter untouched by modern mathematicians, Lie
algebras are integral to a great deal of cutting-edge research; just last year, mathematicians
fully cracked the structure of the algebra corresponding to the E8 Dynkin diagram (shown
on page 20).
Sections 1 and 2 introduce fundamental ideas of linear algebra. Sections 3 and 4 provide
some theory of Lie algebras through a problem-solving approach. Section 5 it discusses
graphs known as Dynkin diagrams and works through elegant cases of Serre’s Theorem.
This is not intended to be a complete course in Lie algebras; in any event, a contest
is far from the best way to provide a complete undertaking. Rather, think of this as a
groundwork for Section 5, which contains some truly beautiful results, in a sort of “greatest
hits” of linear algebra.
Instead of having very few problems with many steps apiece, the guiding philosophy
behind Sections 3-5 is that the majority of the problems are intended to be solved using
only a handful of leaps. This is meant to reward understanding, as the progression in these
sections is meant to be incremental.
Here is some further advice with regard to the Power Round:
• Read the text of every problem! Many important ideas are included in problems
and may be referenced later on. In addition, some of the theorems you are asked to
prove are useful or even necessary for later problems.
• Make sure you understand the deﬁnitions , especially in the last few sections.
If you don’t, then you will not be able to do the problems. Feel free to ask clarifying
questions about the deﬁnitions on Piazza (or email us).
• Don’t make stuﬀ up : on problems that ask for proofs, but you will receive more
points if you demonstrate legitimate and correct intuition than if you fabricate some-
thing that looks rigorous just for the sake of having “rigor.”
• Check Piazza often! Clariﬁcations will be posted there, and if you have a question
it is possible that it has already been asked and answered in a Piazza thread (and
if not, you can ask it, assuming it does not reveal any part of your solution to a
question). If in doubt about whether a question is appropriate for Piazza,
please email us at pumac@math.princeton.edu.
Good luck, and have fun!
– Zachary Stier
We’d like to acknowledge and thank many individuals and organizations for their sup-
port; without their help, this Power Round (and the entire competition) could not exist.
Please refer to the solution of the power round for full acknowledgments.
PUMaC 2017 Power Round Page 4
Contents
0 Whitelist 5
1 Linear Algebra I (20 points) 6
1.1 Vector Spaces (5 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
1.2 Linear Mappings, Inner Products (11 points) . . . . . . . . . . . . . . . . . 7
1.3 Matrices (4 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
2 Linear Algebra II (22 points) 10
2.1 Eigen- (7 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
2.2 Trace (12 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
2.3 Semisimplicity & nilpotency (3 points) . . . . . . . . . . . . . . . . . . . . . 11
3 Lie Algebras I (77 points) 11
3.1 What is a Lie algebra? (26 points) . . . . . . . . . . . . . . . . . . . . . . . 11
3.2 Ideals and Subalgebras (16 points) . . . . . . . . . . . . . . . . . . . . . . . 13
3.3 Ado’s Theorem (9 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
3.4 The adjoint representation (26 points) . . . . . . . . . . . . . . . . . . . . . 14
4 Lie Algebras II (55 points) 15
4.1 The Killing form and semisimple Lie algebras (24 points) . . . . . . . . . . 15
4.2 Root space decomposition (31 points) . . . . . . . . . . . . . . . . . . . . . 15
5 Root systems (125 points) 16
5.1 What is a root system? (37 points) . . . . . . . . . . . . . . . . . . . . . . . 16
5.2 Dynkin diagrams (48 points) . . . . . . . . . . . . . . . . . . . . . . . . . . 18
5.3 Dynkin diagrams of Lie algebras (40 points) . . . . . . . . . . . . . . . . . . 21
PUMaC 2017 Power Round Page 5
Notation
•∀: for all. ex.:∀x∈{ 1, 2, 3} means “for all x in the set {1, 2, 3}”
• f◦g: function composition. ex.: (f◦g)(x) =f(g(x)).
• A⊂B: proper subset. ex.:{1, 2}⊂{ 1, 2, 3}, but{1, 2}̸⊂{ 1, 2}
• A⊆B: subset, possibly improper. ex.:{1},{1, 2}⊆{ 1, 2}
• f :x↦→y: f maps x to y. ex.: if f(n) = n− 3 then f : 20↦→ 17 and f :n↦→n− 3
are both true.
•{x∈ S | C(x)}: the set of all x in the set S satisfying the condition C(x). ex.:
{n∈ N|√n∈ N} is the set of perfect squares.
• N: the natural numbers {1, 2, 3,... }.
• R: the real numbers.
• C: the complex numbers, {x +iy|x,y∈ R and i =√−1}.
0 Whitelist
Linear algebra can be tough to grasp in its ﬁrst go. For teams that might like a more
in-depth look at certain aspects, only the following resources may be referenced to enhance
understanding:
• Robert Beezer, A First Course in Linear Algebra, http://linear.ups.edu/fcla/index.html
– I would recommend this link ﬁrst, as it appears to be an intermediate stage between
the exposition of this Power Round and the following two texts.
• Jim Heﬀeron, Linear Algebra, 3 ed., http://joshua.smcvt.edu/linearalgebra/book.pdf
• David Cherney et al., Linear Algebra, https://www.math.ucdavis.edu//tildelowlinear/linear-
guest.pdf
These are the only resources you may access while working on the Power
Round. Using any other resource constitutes cheating.
In addition, you may only cite the texts when those results are consistent with
only what has been featured prior to that point in the Power Round . This is to
ensure that the texts are purely supplemental to the Round.
What follows is a brief crash course in linear algebra, which will begin to lay down the
foundations for the crux of this Power Round. If it appears that the coming sections are
rather disjointed, understand that a great deal of content has been omitted as to only
include the topics essential for our course of study.
PUMaC 2017 Power Round Page 6
1 Linear Algebra I (20 points)
1.1 Vector Spaces (5 points)
Deﬁnition 1.1.A. A vector space is a set V of elements (known as vectors) that is
associated with a ﬁeld F . In what follows, F will be either R or C (though these are not
the only ﬁelds).
• A vector space is closed under two operations:
– addition (v + w is an element of V for any v, w∈V )
– scalar multiplication (av is an element of V for any a∈F and v∈V )
• There is a zero element 0∈V that functions as an additive identity.
• Scalar multiplication distributes over vector addition (a(v +w) =av +aw) and vice-
versa ((a +b)v =av +bv), plus we have the following associativity: a(bv) = (ab)v.
Note that this implies the existence of additive inverses in V , i.e. for any v∈ V there is
another element, w, for which v + w = 0.
Two illustrative initial examples are R and C, which are each vector spaces over them-
selves. We see that each is closed under addition and scalar multiplication (which is actu-
ally just multiplication distributing over addition), and multiplying by −1 gives additive
inverses. Rn and Cn, the ordered n-tuples (a1,a 2,...,a n) of real or complex numbers, are
for the same reasons vector spaces.
Deﬁnition 1.1.B. W⊆V is a subspace if W is itself a vector space.
For instance,{(z, 0)|z∈ C}⊂ C2 is a subspace relation.
If two vector spaces are “independent from each other,” in that their only common
element is 0, then we write V1⊕V2 ={v1 + v2 | v1 ∈ V1, v2 ∈ V2}. For instance, if
V1 ={(r, 0)| r∈ R} and V2 ={(0,r )| r∈ R} then V1⊕V2 = R2. This lends itself to a
notion of “adding” disjoint vector spaces.
Deﬁnition 1.1.C. A set of vectors{v1, v2,..., vn} is linearly independent if there are no
c1,c 2,...,c n∈F such that not all of them are 0 and c1v1 +c2v2 +··· +cnvn = 0.
For instance, (2, 0), (1, 7)∈ R2 are linearly independent because they cannot be com-
bined to 0. However, no two nonzero real numbers are linearly independent.
Deﬁnition 1.1.D. A subsetV′⊂V spansV if, given v∈V , there is a collection of values
c1,...,c |V ′| for which if V′ ={v′
1,..., v′
|V ′|}, then v =c1v′
1 +··· +c|V ′|v′
|V ′|.
Deﬁnition 1.1.E. The dimension of V is the smallest integer n such that there exists
a spanning set {v1, v2,..., vn}⊂ V , and such a set is called a basis. If there is no such
integern thenV is inﬁnite-dimensional; otherwise V is ﬁnite-dimensional. We denote this
byn = dimV .
For instance, R3 ={(a,b,c )|a,b,c ∈ R} has dimension 3; one basis is{(1, 0, 0), (0, 1, 0), (0, 0, 1)}.
PUMaC 2017 Power Round Page 7
Problem 1.1.1. (2 points) Show that any linearly independent set of size dim V <∞ in
the vector space V over the ﬁeld F is a basis of V .
Problem 1.1.2. (3 points) Show that R[x] is a real vector space, and that C[x] is a complex
vector space (where F [x] is the set of ﬁnite-degree polynomials with coeﬃcients in F ). Is
R[x] a complex vector space? Is C[x] a real vector space?
1.2 Linear Mappings, Inner Products (11 points)
Deﬁnition 1.2.A. A linear mapping or homomorphism is a function f :V →W subject
to f(v + w) = f(v) +f(w) and f(cv) = cf(v) for any c∈F and v, w∈V , where V and
W are vector spaces associated to the same ﬁeld F .
Deﬁnition 1.2.B. In the linear mapping above, V is sometimes called the domain of f
and W is sometimes called the range.
Deﬁnition 1.2.C. We deﬁne the image of f to be im f ={f(v)| v∈ V}⊆ W and the
kernel of f to be set ker f ={v∈V |f(v) = 0}⊆ V .
Consider as an example the linear mapping f : R → R2 sending f : x ↦→ (x, 2x).
f(cx) = (cx, 2cx) = c(x, 2x) = cf(x). This has domain R, range R2, image {(r, 2r)| r∈
R} = R(1, 2), and kernel{0}.
Deﬁnition 1.2.D. A homomorphism ϕ : V → W is said to be an isomorphism if it has
an inverse function ϕ−1 :W→V . V and W are then said to be isomorphic.
Deﬁnition 1.2.E. A bilinear mapping f :V1×V2→S (whereV1,V 2 are vector spaces over
F ) satisﬁes f(c1v1,c 2v2) = c1c2f(v1, v2) as well as linearity in both the ﬁrst and second
components.
Deﬁnition 1.2.F. An inner product is a special type of mapping, which is linear in the
ﬁrst argument (and is “almost linear” in the second); it is denoted ⟨x, y⟩. ⟨·,·⟩ : V 2→ F
and satisﬁes:
•⟨x, y⟩ =⟨y, x⟩ (if F = R then r =r for each r∈ R)
•⟨cx, y⟩ =c⟨x, y⟩ for all c∈F
•⟨x, z⟩ +⟨y, z⟩ =⟨x + y, z⟩
•⟨x, x⟩> 0 if x̸= 0.
One important inner product is the standard inner product , sometimes known as the
dot product. If a = (a1,a 2,...,a n)∈ Rn and b = (b1,b 2,...,b n)∈ Rn, then ⟨a, b⟩ =
a1b1 +a2b2 +··· +anbn. You may want to take a minute to verify that this satisﬁes
bilinearity and the inner product conditions.
Problem 1.2.1. (2 points each) Fix N∈ N. Let a(x) take the form a(x) =
N∑
n=0
anxn and
let FN be the set of degree- N polynomials in F [x]. For each of the following functions
fi :FN→F [x], determine with proof whether or not it is a linear map.
PUMaC 2017 Power Round Page 8
(i) f1 :a(x)↦→a(x) +a(1)
(ii) f2 :a(x)↦→a(x) +a(1)xN +1
(iii) f3 :a(x)↦→
N∑
n=0
(an−aN−n)xn
Problem 1.2.2. (3 points) Describe as precisely as possible all possible inner products on
C2.
Problem 1.2.3. (2 points) If φ is an isomorphism, show that φ−1 is also an isomorphism.
1.3 Matrices (4 points)
Suppose we have the linear map
f : v1 = (1, 0, 0)↦→ (2, 0)
: v2 = (0, 1, 0)↦→ (1, 7)
: v3 = (0, 0, 1)↦→ (1, 1).
We can use a shorthand this function:
[2 1 1
0 7 1
]
. The ﬁrst column represents the image of
the ﬁrst basis vector under the map f; the same holds for the second and third columns. In
general, this format of storing the data of a linear mapping may be used interchangeably
with the function itself, since it conveys precisely the same information. This will be
important and convenient when it becomes cumbersome to work with the function as a list
of operations and instead more useful to use a grid. In general, if f :V →W and we ﬁx a
basis for each of V and W , then we can represent the map f as a m×n array of numbers
in the following way:
Deﬁnition 1.3.A. Anm×n matrix is a grid of values inF havingm rows andn columns,
where the ith column represents f(vi), the image of V ’s ith basis vector.
For another example, R2 has the bases {(0, 1), (1, 0)} and{(1, 1), (1,−1)}. The map
f : (0, 1)↦→ 4, f : (1, 0)↦→ 2 has matrix
[
4 2
]
with the ﬁrst basis and
[
6 −2
]
with the
second.
We will denote byAT the transpose of matrix A, having at the jth column and ith row
the entry inA’sith column andjth row. AT is ann×m matrix ifA ism×n. For instance,
[1 2 3
4 5 6
]T
=


1 4
2 5
3 6

.
We will not treat matrices independently of the context of the functions that they
represent.
Matrix addition is rather intuitive; simply add corresponding elements. For example,[2 0 1 7
1 7 4 6
]
+
[1 7 3 8
1 1 2 2
]
=
[3 7 4 15
2 8 6 8
]
.
Multiplication is less obvious, however. When multiplying, we think of the left mul-
tiplicand as a column vector of row vectors; for example,
[2 0 1
1 7 4
]
=
[v1
v2
]
where v1 =
PUMaC 2017 Power Round Page 9
[
2 0 1
]
, etc., and the right multiplicand is a row vector of column vectors; for example,

1 1
1 0
2 7

 =
[
w1 w2
]
where w1 =


1
1
2

, etc. We simply deﬁne the product, then, to be the
matrix{ai,j} wherei ranges along the height of the left multiplicand andj ranges along the
width of the right multiplicand, and ai,j = vi· wj. So,
[2 0 1
1 7 4
]
·


1 1
1 0
2 7

 =
[ 4 9
16 29
]
. In
general, note the rule that a m×n matrix multiplied by a n×p matrix is a m×p matrix.
Deﬁnition 1.3.B. Then×n matrixIn =


1 ··· 0
... ... 0
0 0 1

 having 1’s along its main diagonal
and 0’s elsewhere is the identity matrix, because InM =MIn for all n×n matrices M.
Deﬁnition 1.3.C. The set of linear mappings between Fn =F×F×···× F and itself
is denoted gln.
The elements of gln can (and often will) be thought of as n×n matrices. (F is assumed
to be C unless otherwise speciﬁed.)
Sometimes for notational convenience we use block matrices. For instance, we could
write


1 0 0 0
0 1 0 0
0 0 1 0
0 0 0 1

 as
[I2 0
0 I2
]
, where the 0’s actually represent
[0 0
0 0
]
; or we may say
[I3 0
0 1
]
, where one 0 represents
[
0 0 0
]
and the other


0
0
0

, as to make the size of the
matrix’s elements make sense.
Problem 1.3.1. (1 point) Does matrix multiplication associate? Why or why not? Answer
the same question about commutativity.
The following two problems give that matrix operations and function operations corre-
spond as we expect.
Problem 1.3.2. (1 point) Show that, for linear mappings T1,T 2 : Rm→ Rn represented
by then×m matrices{ai,j} and{bi,j}, respectively, the linear mappingT1 +T2 : Rm→ Rn
can be represented by the n×m matrix{ai,j +bi,j} (where in each instance i ranges along
1 to m and j from 1 to n).
Problem 1.3.3. (2 points) Show that, for matrices T1 : Rn→ Rp and T2 : Rm→ Rn and
vector v∈ Rm, T1(T2v) = (T1×T2)v.
Note that all these results also hold for Cm and Cn, as well as matrices represented as
block matrices (though when working with block matrices, it’s important to keep careful
track of the dimensions of the blocks).
PUMaC 2017 Power Round Page 10
2 Linear Algebra II (22 points)
2.1 Eigen- (7 points)
Suppose we have a linear transformation M of a vector space V and we wish to know M’s
ﬁxed points – i.e., the vectors for which Mv = v. Unfortunately, it is not always the case
that there exist such vectors, but we can study vectors v such that Mv = λv for some
λ∈F .
Deﬁnition 2.1.A. If there exists a pair consisting of the ﬁeld element λ and nonzero
vector v satisfying that relation, then v is an eigenvector and λ is v’s eigenvalue.
Deﬁnition 2.1.B. Aλ-eigenspace is the set of elements of V that satisfy Mv =λv. It is
often denoted by Vλ (with the linear transformation implied to be already speciﬁed).
For instance,
[2 0
0 1
]
has eigenvectors, for any t∈ R,
[t
0
]
and
[0
t
]
with eigenvealues 2
and 1, respectively, and which give V2 = R×{ 0} and V1 ={0}× R.
Problem 2.1.1. (1 point) Show that each eigenspace Vλ is a subspace of V .
Problem 2.1.2. (1 point) Why does any mapping of a ﬁnite-dimensional space have a
ﬁnite number of distinct eigenvalues?
Problem 2.1.3. (2 points) Suppose M : R2→ R2 is a linear map with matrix
[2 0
1 7
]
.
Find each eigenvector and the corresponding eigenvalue of M. (Hint: which linear map
sends the vector v to cv (c∈ R)?)
Problem 2.1.4. (3 points) For each function in Problem 1.2.1, if it is a linear map,
determine its eigenvalues and classify as best you can the associated eigenvectors.
2.2 Trace (12 points)
Deﬁnition 2.2.A. The trace of A, an n×n square matrix having value ai,j at column i
and row j, is equal to
n∑
k=1
ak,k, that is, the sum of its diagonal entries.
For instance, tr
[2 0
1 7
]
= 2 + 7 = 9.
Lemma 2.2.1. tr(XY ) = tr(YX ) for X,Y n×n matrices.
This result is very useful; for practice, you may try to prove it.
Deﬁnition 2.2.B. sln is the set of n×n complex matrices with trace 0.
While we’re on the topic of deﬁning subspaces of gln, let’s introduce two more classes
of matrices. Denote by R2n =
[ 0 In
In 0
]
, by R2n+1 =


1 0 0
0 0 In
0 In 0

 =
[1 0
0 R2n
]
, and by
˜R2n =
[ 0 In
−In 0
]
.
PUMaC 2017 Power Round Page 11
Deﬁnition 2.2.C. son is the set ofn×n complex matricesM that satisfyMTRn+RnM =
0.
Deﬁnition 2.2.D. sp2n is the set of 2n× 2n complex matrices M that satisfy MT ˜R2n +
˜R2nM = 0. (We do not deﬁne sp2n+1.)
While these deﬁnitions may come across as unmotivated, we will eventually discover
some of their remarkable properties.
Problem 2.2.1. (2 points) What is dim sln? Find a basis.
Problem 2.2.2. (10 points) Classify as best you can the elements of son and spn; ﬁnd
dim son and dim spn.
2.3 Semisimplicity & nilpotency (3 points)
Deﬁnition 2.3.A. A diagonal matrix is one where each of its entries not on the main
diagonal are zero.


1 0 0
0 2 0
0 0 3

 and
[0 0
0 0
]
are both examples of diagonal matrices.
Suppose, for the rest of this section, that all matrices considered lie in gln for a ﬁxed n.
Deﬁnition 2.3.B. The matrix A is semisimple if there is diagonal matrix D and another
matrix P having a multiplicative inverse such that PA =DP .
Clearly, all diagonal matrices are semisimple, by choosing P = I. Additionally, it is
important to note that the invertibility of P is essential, since otherwise any matrix would
be semisimple, by choosing P = 0.
Deﬁnition 2.3.C. The matrix N is nilpotent if there is a positive integer k for which
Nk = 0.
The matrix 0 is trivially nilpotent. A less obvious example is
[0 1
0 0
]
(it becomes 0 after
squaring).
It turns out that semisimple and nilpotent matrices have a very deep relationship.
Problem 2.3.1. (3 points) Show that if X and Y are matrices that commute and X is
nilpotent then tr(XY ) = 0.
We are now ready to begin investigating Lie algebras. Despite their simple deﬁnition, we
will soon see a host of powerful results that aid in their classiﬁcation.
3 Lie Algebras I (77 points)
3.1 What is a Lie algebra? (26 points)
Deﬁnition 3.1.A. A Lie algebra is a vector space L with, besides addition, the bilinear
operation [·,·] : L×L→ L. This bracket (sometimes the Lie bracket ) is subject to the
following properties:
PUMaC 2017 Power Round Page 12
• [x,x ] = 0 for x∈L
• [x, [y,z ]] + [y, [z,x ]] + [z, [x,y ]] = 0 for any x,y,z ∈L (the Jacobi identity )
Linear maps from Fn→ Fn are actually a very good way to think about many Lie
algebras. (You’ll show in Problem 3.1.1 that these functions do indeed form a Lie algebra.)
Lemma 3.1.1 (anticommutativity of the bracket ). [x,y ] =−[y,x ] for x,y elements of a
Lie algebra L.
Proof. Letz =x+y. 0 = [z,z ] = [x+y,x +y] = [x,x ]+[x,y ]+[y,x ]+[y,y ] = [x,y ]+[y,x ].
Deﬁnition 3.1.B. A Lie algebra for which the bracket is degenerate, i.e. [ x,y ] = 0 for all
x,y∈L, is termed an abelian Lie algebra.
Note that the dimension of a Lie algebra is its dimension as a vector space under
addition. In general, we do not have a meaningful way to treat the bracket operation as an
operation giving rise to a vector space.
We also have a natural extension to the concept of vector space homomorphism and
isomorphism:
Deﬁnition 3.1.C. A homomorphism of Lie algebras is a function ϕ :L1→L2 where L1
and L2 are lie algebras over the same ﬁeld, and for which ϕ([x,y ]) = [ϕ(x),ϕ (y)] for any
x,y∈L1.
Deﬁnition 3.1.D. An isomorphism of Lie algebras is a bijective homomorphism of Lie
algebras.
The following problems will serve to hone your intuition.
Problem 3.1.1. (1 point) Let [f,g ] = f◦g−g◦f for f,g ∈ gln. Show that the Jacobi
identity holds for f,g,h ∈ gln, and therefore that gln is a Lie algebra.
Problem 3.1.2. (1 point) Explain why two Lie algebras of diﬀerent dimension cannot be
isomorphic.
Problem 3.1.3. (4 points) Show that if L1 and L2 are abelian Lie algebras, they are
isomorphic if and only if they are of the same dimension.
Problem 3.1.4. (4 points) Assume that for all x,y,z ∈L, [x, [y,z ]] = [[x,y ],z ]. What is
the most general statement you can make about elements of L?
Problem 3.1.5. Fixn. Suppose there is some subalgebra S⊆ gln for whichφ : sl2→S is
a bijective Lie algebra homomorphism (where gln has the bracket as in Problem 3.1.1). If
v1 =
[0 1
0 0
]
,v2 =
[0 0
1 0
]
, and v3 =
[1 0
0 −1
]
, let Vi =φ(vi). Let λ3 andλ′
3 be the greatest
and least eigenvalue, respectively, of V3 and let v,v′∈ Cn be vectors such that V3v = λ3v
and V3v′ =λ′
3v′.
(i) (5 points) Find, with proof, V1v and V2v′.
(ii) (7 points) Find, with proof, λ3 and λ′
3.
Problem 3.1.6. (4 points) Up to isomorphism, how many Lie algebras have dimension 1?
dimension 2? List them all.
PUMaC 2017 Power Round Page 13
3.2 Ideals and Subalgebras (16 points)
Deﬁnition 3.2.A. A subalgebraS of the Lie algebra L is a subspace for which if x andy
are any elements of S then [x,y ]∈S.
Deﬁnition 3.2.B. An ideal I is a subalgebra for which if x is any element of I and y is
any element of L then [x,y ]∈I.
One example is the x-axis in R2 (i.e.{(x, 0)|x∈ R} under the bracket [P,Q ] = 0. The
axis is a vector space, and thus both a subalgebra and an ideal.
Deﬁnition 3.2.C. A Lie algebra L is simple if its only ideals are {0} and itself.
One example of a simple Lie algebra issl2. (To prove this, you can show that no subspace
of dimension 1 or 2 may be an ideal, by forcing contradictions by bracketing with the right
choices of v1,v 2,v 3.)
Problem 3.2.1.
(i) (1 point) If L is an abelian Lie algebra, show that any subspace of L is a subalgebra
and an ideal.
(ii) (4 points) Find a nonabelian Lie algebra on a space of n×n matrices for some n> 2
that has a subalgebra that is not an ideal. Specify that subalgebra and brieﬂy justify
why it is not an ideal.
Problem 3.2.2. (5 points) Take I ={x∈L|x nilpotent} where L is a subspace of gln.
Is I a subalgebra? an ideal? Fully justify your responses.
Problem 3.2.3. (3 points) Let [L1,L 2] ={[v1,v 2]|vi∈Li} for Lie algebras L1 and L2.
Is [I,J ] an ideal for ideals I and J of the same Lie algebra?
Problem 3.2.4. (3 points) Show that ker φ is an ideal and im φ is a subalgebra of the
domain and image space, respectively, for φ a Lie algebra homomorphism.
3.3 Ado’s Theorem (9 points)
Theorem 3.3.1 (Ado’s theorem). For any ﬁnite-dimensional Lie algebra L, there exists a
positive integer n such that there is a subalgebra of gln that is isomorphic to L.
Its proof is well beyond the scope of this Power Round, so we will assume it to hold
true. We will also assume that any Lie algebra henceforth is a matrix subalgebra,
i.e. a subalgebra of gln for some n. For any matrix space, we deﬁne the bracket to take
[X,Y ] =XY−YX ; since the matrices are linear mappings, note that this is the deﬁnition
we have used earlier, such as in Problem 3.1.1.
In general it is not strictly important what the isomorphism is between a non-matrix
Lie algebra and the corresponding matrix subalgebra, but to further your comfort with
isomorphisms and the Lie bracket, this section’s exercises will be concerned with that task.
Problem 3.3.1. Consider the additive vector space Vd of degree-d polynomials with real
coeﬃcients.1
1Note that x3 + x + 1 is a polynomial of degree 3, 4, 5, etc. but not 2, 1 or 0.
PUMaC 2017 Power Round Page 14
(i) (1 point) Find the dimension of V3, and ﬁnd a basis.
(ii) (5 points) Say V2 is given a bracket operation, for p(x) = α0 +α1x +α2x2 and
q(x) =β0 +β1x +β2x2 elements of V2,
[p,q ] = (α1β2−α2β1) + (α2β0−α0β2)x + (α0β1−α1β0)x2.
Find a subspace S of gln for some n such that there is an isomorphism between V2
and S; explicitly describe such an isomorphism that preserves the bracket.
Problem 3.3.2. (3 points) Suppose R2 is given a Lie bracket that makes it abelian. Find a
subspaceS of gln for somen such that there is an isomorphism between R2 andS; explicitly
describe the isomorphism.
3.4 The adjoint representation (26 points)
Deﬁnition 3.4.A. The adjoint representation of x∈L is a function taking L to itself in
the following manner: ad x :y↦→ [x,y ].
In practice, we write the action of x’s adjoint representation on y as (adx)(y) = [x,y ].
Problem 3.4.1. (1 point) Verify that adx is a linear map.
Problem 3.4.2.
(i) (2 points) Explain how ad x can be thought of as an element of gl3 if x∈ sl2.
(ii) (5 points) Find an explicit, nontrivial 2 isomorphism from the Lie algebra sl2 to a
subalgebra of gl3.
Problem 3.4.3. (5 points) Show that the set of 3 × 3 complex upper-triangular matrices
is a Lie algebra, ﬁnd a basis, and write ad ei explicitly for each basis vector ei. Find ad ei’s
eigenvalues for each basis vector ei.
Hint for 3.4.2(ii) and 3.4.3: Remember that ad x is a linear map from L to itself, or equiv-
alently, fromS to itself, where S⊆ gln is isomorphic to L. Also, make sure you specify the
order of the elements of your basis when writing your matrices.
Problem 3.4.4. (5 points) Show that [x,y ] = 0 implies (adx)◦ (ady) = (ady)◦ (adx).
Problem 3.4.5. (6 points) If x is nilpotent, is ad x nilpotent? If ad x is nilpotent, is x
nilpotent? Justify your response.
Problem 3.4.6. (2 points) Show that adx satisﬁes the relation (adx)([y,z ]) = [(adx)(y),z ]+
[y, (adx)(z)] for any x,y,z ∈L. (Such functions are called derivations.)
2e.x., M ↦→
[M 0
0 0
]
is such a trivial mapping. The problem isn’t very much fun if read to allow trivial
solutions, is it?
PUMaC 2017 Power Round Page 15
4 Lie Algebras II (55 points)
4.1 The Killing form and semisimple Lie algebras (24 points)
Deﬁnition 4.1.A. The Killing form is an operation deﬁned as
κ(x,y ) = tr(adx· ady).
(Don’t be intimidated by the name!)
Deﬁnition 4.1.B. We callκ non-degenerate and we say thatL is a semisimple Lie algebra
if the only element x∈L for which κ(x,y ) = tr(adx· ady) = 0 for all y is x = 0.
As it turns out, all the Lie algebras that we have considered thus far have been semisim-
ple. We now restrict our attention to such algebras, and with this deﬁnition to guide us,
we are about to see a number of remarkable results.
Problem 4.1.1. (1 point) Verify that the Killing form is symmetric and bilinear.
Problem 4.1.2. (5 points) Show that κ([x,y ],z ) =κ(x, [y,z ]).
Problem 4.1.3. (10 points) Show thatx∈L is semisimple if and only if adx is semisimple.
Problem 4.1.4.
(i) (3 points) Let I′ ={x∈ L| κ(x,y ) = 0∀y∈ I} for I⊆ L an ideal. Show that I′ is
also an ideal.
(ii) (5 points) If L is semisimple, show that there are n simple subalgebras Li
(1≤n≤ dimL) such that
L =
n⨁
i=1
Li.
4.2 Root space decomposition (31 points)
Deﬁnition 4.2.A. The center of a subalgebra S⊆L is{x∈L| [x,y ] = 0∀y∈S}.
Theorem 4.2.1. Any Lie algebraL has a nontrivial subalgebra H of semisimple elements
that is equal to its center in L;H is known as the maximal toral subalgebra. There exists a
basis of L such that each basis element is an eigenvector to each element of H.
In particular [ h,vi] = λi(h)vi for some function λi : H → C. For example, for the
sub-basis spanning H consisting of {v1,...,v dimH} (renumbered as necessary), λi(h) = 0
identically for 1≤i≤ dimH, since H is equal to the center, where the bracket is abelian
(but this would not necessarily hold for an element not in H).
Deﬁnition 4.2.B. λi is called a root of L, and H∗ is the vector space with spanned by
{λi| 1≤i≤ dimL}.
Deﬁnition 4.2.C. The root spaceLλ corresponding to the root λ consists of the elements
of L that are λ-eigenvectors of H – i.e.,
Lλ ={v∈L| [h,v ] =λ(h)v∀h∈H}.
PUMaC 2017 Power Round Page 16
This yields the root space decomposition of L.
From each root λ we then are able to derive a convenient isomorphism: there are three
elementseλ∈Lλ,fλ∈L−λ andhλ∈H for which sl2 is isomorphic to span{eλ,fλ,hλ} via
ϕ :v1↦→eλ
v2↦→fλ
v3↦→hλ
and the additional condition that λ(hλ) = 2.
We are now also ready to talk about H∗ as a vector space having an inner product.
Deﬁnition 4.2.D. tλ∈ H corresponds to λ∈ H∗ such that κ (tλ,h ) = λ(h) for each
h∈H.
Then, we get a convenient inner product for our space space of functions! We let the
inner product on H∗ be⟨λ1,λ 2⟩ =κ (tλ1,tλ2).
Problem 4.2.1. (5 points) Show that each λi is linear.
Problem 4.2.2. (3 points) Show that L is isomorphic to the vector space
⨁
λ:H→C
Lλ.
Problem 4.2.3. (6 points) Supposeα andβ are roots ofL having maximal toral subalgebra
H. Under what condition on α andβ is it true thatκ(v1,v 2)̸= 0 for somev1∈Lα,v 2∈Lβ?
Hint: you may not be able to prove the result stated in this exact manner.
Hint 2: try multiplying by a nice factor.
Problem 4.2.4. (6 points) Show that ⟨·,·⟩ : H∗×H∗→ C as deﬁned above is an inner
product.
Problem 4.2.5. (6 points) Show that [x,y ] =κ(x,y )tλ for x∈Lλ,y∈L−λ.
Problem 4.2.6. (5 points) Show that for roots λ∈H∗, κ(tλ,tλ)κ(hλ,hλ) = 4 and show
that hλ = 2tλ
κ(tλ,tλ).
5 Root systems (125 points)
5.1 What is a root system? (37 points)
We will brieﬂy step back to consider any vector space, which might not have a Lie bracket.
Deﬁnition 5.1.A. A subset ( note: not a subspace) S of a real vector space V with the
inner product⟨·,·⟩ is a root system of V if spanS =V and, for any v,w ∈S,
1. the only other scalar multiple of v in S is−v
PUMaC 2017 Power Round Page 17
2. w− 2⟨v,w⟩
⟨v,v⟩v∈S3
3. 2⟨v,w⟩
⟨v,v⟩∈ Z
Elements of the root system are known as roots. (This is related to the deﬁnition in Section
4.3.)
Note that a root system is not guaranteed to exist.
Deﬁnition 5.1.B. A reducible root system may be decomposed into into nonempty subsets
R1∪R2 for which⟨v1,v 2⟩ = 0 for v1∈R1,v 2∈R2, where R1 andR2 are also root systems.
An irreducible root system is one that is not reducible.
Figure 1: Two root systems of R2, (a) A1×A1 and (b) A2.
Figure 1(a) depicts the root system of R2
R1a =
{[
2 0
]
,
[
−2 0
]
,
[
0 1
]
,
[
0 −1
]}
.
Note that R1a =
{[
2 0
]
,
[
−2 0
]}
∪
{[
0 1
]
,
[
0 −1
]}
and that
spanR1a = R2 = span
{[
2 0
]
,
[
−2 0
]}
⊕ span
{[
0 1
]
,
[
0 −1
]}
.
We see that A1×A1 is a reducible root system. Meanwhile, Figure 1(b) depicts the irre-
ducible root system of R2
R1b =
{[
1 0
]
,
[
−1 0
]
,
[
1
2
√
3
2
]
,
[
− 1
2
√
3
2
]
,
[
− 1
2 −
√
3
2
]
,
[
1
2 −
√
3
2
]}
;
note that only trivially can R1b be broken up into smaller root spaces (i.e. via {0} andR1b
itself).
Deﬁnition 5.1.C. R has baseB⊂R ifB is a basis of V and, for eachw∈R, there exists
c :B→ N∪{ 0} such that w =± ∑
v∈B
c(v)v.
3This represents reﬂecting w across the plane in V perpendicular to v and passing through 0.
PUMaC 2017 Power Round Page 18
Going back to our examples, A1×A1 can have the base
{[
2 0
]
,
[
0, 1
]}
and A2 can
have the base
{[
1 0
]
,
[
− 1
2
√
3
2
]}
.
Problem 5.1.1. (1 point) Find all root systems in R.
Problem 5.1.2. (3 points) In condition 3, note that v and w are interchangeable. Use
this and the identity that⟨v,w⟩ =∥v∥·∥w∥ cosφ (whereφ is the angle between the vectors)
to show that 4 cos2φ∈{ 0, 1, 2, 3} wheneverv̸=±w.
Problem 5.1.3. (8 points) Think about the construction of the root systems in the text,
as well as Problem 5.1.2, use these to understand why the subsets of R2 shown in Figure 1
are root systems. Draw (on separate coordinate axes) all possible root systems R.4
Problem 5.1.4. (10 points) Show that any root system can be written as the union of
irreducible root systems. (Use the fact that a root system R is irreducible if there is no
subset R′ such that for α∈R′ and β∈R\R′,⟨α,β⟩ = 0.)
Problem 5.1.5. (15 points) Show that any root system has a base.
5.2 Dynkin diagrams (48 points)
Let B be a base of a root system and let B′ =
{
v√
⟨v,v⟩,|v∈B
}
(we normalize the base).
We now assume that B′ satisﬁes⟨vi,vj⟩≤ 0 when i̸=j, and 4⟨vi,vj⟩2∈{ 0, 1, 2, 3}.
We will represent the normalized base as a graph withmulti-edges, i.e. a number of edges,
possibly greater than one (and in that case directed), and possibly zero, connecting two given
vertices. We will think of these as “total edges,” so that there cannot simultaneously be
edges going in both directions. We deﬁne this as
e(v,w ) = 4 ⟨v,w⟩2
∥v∥2∥w∥2.
(Note that this is equal to
(
2⟨v,w⟩
⟨v,v⟩
)
·
(
2⟨v,w⟩
⟨w,w⟩
)
.)
Since we have an explicit characterization of the nature of edges connecting any two
simple roots, we simply draw a node for each of those roots and the appropriate edge to
each other simple root. Frequently an edge will be zero, so we simply will not draw an edge
at all; otherwise, we draw a straight, undirected edge between v andw ife(v,w ) = 1 and a
directed n-fold edge if e(v,w ) = n. The quesiton, then, is how to determine the direction
of the edge, since e is symmetric in its inputs v and w (e(v,w ) = e(w,v )). Our resolution
is simply to point from the longer root of the shorter one, where the length of v is deﬁned
as ℓ =
√
⟨v,v⟩.5
As an example, let’s ﬁnd the diagrams for A1×A1 and A2. We will use B′
1 ={w1 =
(1, 0),w 2 = (0, 1)} and B′
2 ={v1 = (1, 0),v 2 =
(
− 1
2,
√
3
2
)
}. We are using the dot product
for⟨·,·⟩. e(w1,w 2) = 0 and e(v1,v 2) = 1, so we have the following Dynkin diagrams:
4Up to rotation and dilation; that is, if R1 and R2 are two root systems that you submit, there should
not exist a nonidentity matrix M for which R1 = M R2.
5One can check that for the standard inner product on Rn this is equivalent to the regular conception of
length using the distance formula.
PUMaC 2017 Power Round Page 19
Figure 2: Dynkin diagram for A1×A1 on the left (the two disconnected points) and A2 on the
right.
Before continuing onto the Problems, let’s look at a sample proof to gain a sense for
Dynkin diagram arguments. Consider a line which may be part of a larger Dynkin diagram.
Figure 3: A line (sub)diagram.
Now consider “combining” these into a “super-vertex” by “folding along” – i.e., let
v =v1; then let v =v +v2; then let v =v +v3; etc., until we get a single vector v =
k∑
i=1
ivi.
We will show that⟨v,v⟩ = k(k+1)
2 .
Proof. We know that⟨vi,vj⟩̸ = 0 iﬀ|i−j|≤ 1.⟨vi,vi⟩ = 1 since they are unit vectors, and
2⟨vi,vi+1⟩ =−1 since the edge length is 1, and the inner product here cannot be positive. 6
Thus⟨v,v⟩ =
k∑
i=1
i2 + 2
k−1∑
i=1
⟨vi,vi+1⟩i(i + 1) = k(k+1)
2 by computation.
This should serve as a viable model for the coming problems that ask about the im-
possibility of certain Dynkin diagrams – look to use the fact that the number of edges is
necessarily a nonnegative integer.
Problem 5.2.1. (10 points) Show that a root system is irreducible if and only if it has a
connected Dynkin diagram.
Problem 5.2.2. (7 points) Show that no Dynkin diagram may have a cycle.
Problem 5.2.3. (8 points) Show that no node in a Dynkin diagram may have more than
three total edges connected to it.
We’ll now restrict our consideration to only connected Dynkin diagrams.
Problem 5.2.4. (4 points) The Shrinking Lemma states that if a Dynkin diagram on
the base B has n vertices v1,v 2,...,v n that are in a line and v =
n∑
i=1
vi, then the base
B\{v1,v 2,...,v n}∪{v} corresponds to the root system with the intermediate vertices “com-
bined” into a single vertex (as before). (See Figure 4.) Use the Shrinking Lemma 7 to show
6Think about why; this will be useful in the coming problems. Hint: what would be wrong with these
vectors having an acute angle? What would that imply?
7The Shrinking Lemma is not exceptionally diﬃcult to prove, but it is something of a digression. You
may want to try proving it to test your command of the material, but henceforth you may assume it is true.
PUMaC 2017 Power Round Page 20
that no Dynkin diagram may have more than one branch, more than one double-edge, or
both a branch and a double edge.
Figure 4: An impossible Dynkin diagram. The Shrinking Lemma gives that if there is a root
system corresponding a variant of this diagram (with n nodes amongst the ··· ) then there is one
corresponding to the one with n− 1,n− 2,..., 1, 0 vertices.
Problem 5.2.5. (4 points) Prove that if a Dynkin Diagram has a double edge with both
ends connected to other nodes then it must be F4.
Figure 5: F4, the Dynkin diagram discussed in Problem 5.3.6.
Problem 5.2.6. (15 points) Imagine a Dynkin diagram with a “branching point” – there
is some vector with three lines coming oﬀ of it. Show that one of those lines must have
length one (i.e. only one edge), and show that of the other two, either
• if one has length 1 then the third may have any length
• if one has length 2 then the other’s length may not be more than 4.
Theorem 5.2.1 (Classiﬁcation of Dynkin diagrams ). The following are the only possible
irreducible Dynkin diagrams:
Proof. Problems 5.2.1 and 5.2.3-7.
This is an amazing result! We gave only a handful of restrictions on our deﬁnition of
these diagrams – and yet we get such a restricted and asymmetrical list of options. Let’s now
look into how this relates to the Lie algebra content that we spent so much time building
up.
PUMaC 2017 Power Round Page 21
5.3 Dynkin diagrams of Lie algebras (40 points)
We are now prepared to look at root systems and bases of our simple Lie algebras! In doing
so, with a little help from Jean-Pierre Serre, we will be able to see, pictorially, precisely
every isomorphism between the classical Lie algebras. 8
Deﬁnition 5.3.A. The Dynkin diagram of a Lie algebra is the Dynkin diagram corre-
sponding to the vector space of its roots.
Deﬁnition 5.3.B. ei,j denotes the N×N matrix having the entry 1 at row i and column
j, and zeros elsewhere (where the value of N will be clear from context).
For a worked example, take L = so2n. As L’s elements satisfy xTR2n +R2nx = 0, we
know that x can be written in the form
[M P
Q −MT
]
for any n×n matrix M and n×n
matrices P and Q both equal to their negative transpose.
H is the set of diagonal matrices in L, so H =
{ n∑
i=1
ci(ei,i−ei+n,i+n)|ci∈ C
}
. We can
give L the additional basis elements mi,j = ei,j−ej+n,i+n (i̸= j), pi,j = ei,j+n−ej,i+n
(i < j), and pT
i,j to go along with those of H. (It is straightforward to check that this is
indeed a basis of L – try writing down the matrices mi,j and pi,j to verify this.) We ﬁnd,
for an arbitrary element h∈H of the form speciﬁed in H’s speciﬁcation,
[h,mi,j] = (ci−cj)mi,j
[h,pi,j] = (ci +cj)pi,j
[h,pT
i,j] =−(ci +cj)pT
i,j
so our roots are particularly convenient:
root eigenspace
λi−λj span{mi,j,mj,i}
λi +λj span{pi,j,pj,i}
ForH∗, a vector space having the basis {λi}, we see that{λ1−λ2,λ 2−λ3,...,λ n−1−
λn,λn−1 +λn} is a base; this base will be what we use to build our Dynkin diagram.
Computation gives that
⟨λi−λi+1,λj−λj+1⟩ =



−2 i =j
−1 |i−j| = 1
−0 otherwise
⟨λi−λi+1,λn−1 +λn⟩ =
{
−1 i =n− 2
−0 otherwise
⟨λn−1 +λn,λi−λi+1⟩ =
{
−1 i =n− 2
−0 otherwise
Since e(v,w ) =⟨v,w⟩·⟨ w,v⟩, our Dynkin diagram is shown in Figure 6.
8The classical Lie algebras are the four spaces deﬁned in Section 2.2: sln, son, sp2n.
PUMaC 2017 Power Round Page 22
Figure 6: In this diagram, we use the shorthands αi =λi−λi+1 and βn =λn−1 +λn.
Theorem 5.3.1 (Serre’s theorem). Two Lie algebras with the same Dynkin diagram are
isomorphic.
Serre’s theorem is the ﬁnal piece of the puzzle; now, you will put to the test what we
have learned to ﬁnd the bases of the other classical Lie algebras.
Problem 5.3.1. (10 points each) For n≥ 1 in all cases...
(i) draw the Dynkin diagram for so2n+1
(ii) draw the Dynkin diagram for sln
(iii) draw the Dynkin diagram for sp2n
and show your reasoning. In particular, many details of the computations were omitted
above, but you will be expected to (brieﬂy) justify the numbers you ﬁnd.
What you should get from this is that we have discussed exactly four inﬁnite classes of
classical Lie algebras, and there are exactly four inﬁnite classes of Dynkin diagrams. This,
combined with Serre’s theorem, takes us to our last result.
Problem 5.3.2. (10 points) State all isomorphims between the classical Lie algebras,
and the Dynkin diagrams that you used to reach those conclusions. (Do not provide the
isomorphisms explicitly – just brieﬂy state your reasoning.)
That’s it! We’ve managed to ﬁnd all the equivalencies between the classical Lie algebras,
admittedly in a rather roundabout manner – but I hope you’ve enjoyed the scenery along
the way!
Team Number:
PUMaC 2017 Power Round Cover Sheet
Remember that this sheet comes ﬁrst in your stapled solutions. You should submit
solutions for the problems in increasing order. Write on one side of the page only. The
start of a solution to a problem should start on a new page. Please mark which questions
for which you submitted a solution to help us keep track of your solutions.
Problem Number Points Attempted?
1.1.1 2
1.1.2 3
1.2.1 6
1.2.2 3
1.2.3 2
1.3.1 1
1.3.2 1
1.3.3 2
2.1.1 1
2.1.2 1
2.1.3 2
2.1.4 3
2.2.1 2
2.2.2 10
2.3.1 3
3.1.1 1
3.1.2 1
3.1.3 4
3.1.4 4
3.1.5 12
3.1.6 4
3.2.1 5
3.2.2 5
3.2.3 3
3.2.4 3
3.3.1 6
3.3.2 3
3.4.1 1
3.4.2 7
Problem Number Points Attempted?
3.4.3 5
3.4.4 5
3.4.5 6
3.4.6 2
4.1.1 1
4.1.2 5
4.1.3 10
4.1.4 8
4.2.1 5
4.2.2 3
4.2.3 6
4.2.4 6
4.2.5 6
4.2.6 5
5.1.1 1
5.1.2 3
5.1.3 8
5.1.4 10
5.1.5 15
5.2.1 10
5.2.2 7
5.2.3 8
5.2.4 4
5.2.5 4
5.2.6 15
5.3.1 30
5.3.2 10
Total 299
