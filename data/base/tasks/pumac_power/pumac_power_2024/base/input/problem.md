# PUMaC Power Round 2024

PUMaC 2024 Power Round:
Measures and Fractals
Colby Riley
Fall 2024
Rules and Reminders
Read ALL of the following rules. Failure to follow proper rules may result in point deduc-
tions.
1. Your solutions should be turned in by 5pm Thursday the 21st of November,
EST. You will submit the solutions through Gradescope. The instructions describing
how to log into Gradescope will be sent to the coaches. The deadline for submission
is clearly visible on the Gradescope site once you enroll in the course.
Please make sure you submit your work in time. No late submissions will be
accepted. Please do not submit your work using email or in any other way. If you
have questions about Gradescope, please post them on Piazza.
You may either typeset the solutions in L ATEX or write them by hand. We strongly
encourage you to typeset the solutions. This way, the proofs end up being more clear
and the chances are you will not lose points there. Moreover, you might want to use
some of the LATEX resources listed in point 2.
In case your solutions are handwritten, the cover sheet (the last page of this document)
should be the first page of your submission. In case you typeset your solutions, please
take a look at the Solutions Template we posted and make sure to make the cover
sheet the first page of your submission.
Each page should have on it the team number (not team name) and problem
number. This number can be found by logging in to the coach portal and selecting
the corresponding team. Solutions to problems may span multiple pages. Please put
them in order when submitting your solutions.
2. you may resubmit several times before the due date, but only your final submission
will be graded (moreover, you may not submit any work after the deadline). The
last version of the power round solutions that we receive from your team will be
graded. Moreover, you must submit a PDF . No other file type will be graded.
For those new and interested in LATEX, check out Overleaf as well as its online guides.
If you do not know the specific command for a math symbol, check out Detexify or
TeX.StackExchange.
3. Do not include identifying information aside from your team number in your solutions.
4. When submitting to Gradescope, assign the solutions to the correct problems on the
Gradescope submission outline. Failure to do this WILL result in a point deduction,
as it creates a ton of extra work for us on the back-end.
5. On any problem, you may use without proof any result that is stated earlier in the
test, as well as any problem from earlier in the test, even if it is a problem that your
team has not solved. These are the only results you may use. In particular, to solve a
problem, you may not cite the subsequent ones. You may not cite parts of your proof
of other problems: if you wish to use a lemma in multiple problems, please reproduce
it in each one.
6. When a problem asks you to “find”, “find with proof,” “show,” “prove,” “demon-
strate,” or “ascertain” a result, a formal proof is expected, in which you justify each
step you take, either by using a method from earlier or by proving that everything you
do is correct. When a problem instead uses the word “explain,” an informal expla-
nation suffices. When a problem instead uses the word “sketch” or “draw” a clearly
marked diagram is expected.
7. All problems are numbered as “Problem x.y.z” where x.y is the subsection number
and z is the the number of the problem within the subsection. Each problem’s point
distribution can be found in the cover sheet.
8. Y ou may NOT use any references, such as books or electronic resources,
unless otherwise specified. Y ou may NOT use computer programs, calcu-
lators, or any other computational aids.
9. Teams whose members use English as a foreign language may use dictionaries for
reference.
10. Communication with humans outside your team of 8 students about the
content of these problems is prohibited.
11. There are two places where you may ask questions about the test. The first is Piazza.
Please ask your coach for instructions to access our Piazza forum. On Piazza, you may
ask any question so long as it does not give away any part of your solution to
any problem. If you ask a question on Piazza, all other teams will be able to see it.
If such a question reveals all or part of your solution to a power round question, your
team’s power round score will be penalized severely. For any questions you have that
might reveal part of your solution, or if you are not sure if your question is appropriate
for Piazza, please email us at pumac@math.princeton.edu. We will email coaches with
important clarifications that are posted on Piazza.
Introduction and Advice
In this power round, we formally investigate fractals, exploring how to make the idea
of self-similarity and non-integer dimensions rigorous. We hope that this introduction pro-
vides not only an interesting perspective on something often seen as pop-math, but also an
introduction to measure theory, a fascinating branch of mathematics.
A large part of the difficulty in this power round will arise from the many different
perspectives that one needs to understand the material and tackle the problems. For ex-
ample, understanding the geometry of fractals is essential to proving facts about them, but
grasping set theory and topology is essential to making many of these intuitions formal.
Here is some further advice with regard to the Power Round:
• Read the text of every problem! Many important ideas are included in problems
and may be referenced later on. In addition, some of the theorems you are asked to
prove are useful or even necessary for later problems.
• Make sure you understand the definitions . A lot of the definitions are not easy
to grasp; don’t worry if it takes you a while to fully understand them. If you don’t,
then you will not be able to do the problems. Feel free to ask clarifying questions
about the definitions on Piazza (or email us).
• Don’t make stuff up: on problems that ask for proofs, you will receive more points
if you demonstrate legitimate and correct intuition than if you fabricate something
that looks rigorous just for the sake of having “rigor.”
• Check Piazza often! Clarifications will be posted there, and if you have a question
it is possible that it has already been asked and answered in a Piazza thread (and
if not, you can ask it, assuming it does not reveal any part of your solution to a
question). If in doubt about whether a question is appropriate for Piazza,
please email us at pumac@math.princeton.edu.
• Don’t cheat: as stated in Rules and Reminders, you may NOT use any references
such as books or electronic resources. If you do cheat, you will be disqualified and
banned from PUMaC, your school may be disqualified, and relevant external institu-
tions may be notified of any misconduct.
Good luck, and have fun!
– Colby Riley
We would like to acknowledge and thank many individuals and organizations for their
support; without their help, this Power Round (and the entire competition) could not exist.
Please refer to the solutions of the power round for full acknowledgments and references.
Contents
1 T opology in Rn 6
2 Measures 8
2.1 Hausdorff measure . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
3 Interlude: some fractal constructions 12
3.1 Cantor Set . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
3.2 Sierpinski Carpet . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
3.3 Minkowski Sausage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
3.4 Koch Curve . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
4 Iterated F unction Systems 14
4.1 Dimension of IFS’s . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
4.2 Mass Distribution Principle . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
5 Sierpinski T riangle 21
Notation and Basic Concepts
• {x ∈ S : C(x)}: the set of all x in the set S satisfying the condition C(x). Ex.:
{n ∈ N : √n ∈ N} is the set of perfect squares.
• A × B: cartesian product. It is the set consisting of ordered pairs {(a, b) : a ∈ A, b∈
B}. Ex.: Rn = R × ... × R
• A ⊂ B: subset. Ex.: {1, 2} ⊂ {1, 2, 3}, and {1, 2} ⊂ {1, 2}
• f (C): for a function f : A → B and subset C ⊆ A, the set of elements of the form
f (c), for c ∈ C.
• N: the natural numbers, {1, 2, 3, . . .}.
• Z: the integers.
• Q: the rational numbers.
• R: the real numbers.
• for a < b, [a, b] = {x : a ≤ x ≤ b}, (a, b) = {x : a < x < b}, and (a, b], [a, b) are defined
similarly.
• sup X: the supremum. For X ⊂ R, The supremum is the smallest values such that for
all x ∈ X, x ≤ s. Always exists, but may be ±∞. Ex.: sup{1, 2, 3} = 3. sup N = ∞.
• supx∈X f (x): the supremum applied to the set f (X).
• inf X: the infimum, the largest value s such that for all x ∈ X, x ≥ s. Always exists,
but may be ±∞.
• for a decreasing sequence an, limn→∞ an is defined to be inf n∈N an.
• for an increasing function f : (0, a) → R defined near 0, lim δ→0 f (δ) is defined to be
inf δ>0 f (δ). Ex.: limδ→0(δ2 + 5) = 5 . For a decreasing function, use sup.
• log with no base refers to the natural logarithm.
• a function f : A → B is injective if for all x, y∈ A, f (x) = f (y) = ⇒ x = y. It is
surjective if for all b ∈ B, there is some a ∈ A such that f (a) = b. It is bijective if
it is injective and surjective.
• a set is countable if there exists a bijection from it to N or a finite set.
Notes on the use of calculus in the Power Round: we here at PuMaC do not expect
anyone in this competition to necessarily know calculus. Thus, we have tried to minimize
the use of calc in this power round. Accordingly, for proofs which involve limits, infimums,
and supremums, we do not expect formal, ϵ − δ type proofs, nor do we want you to be
citing continuity results willy nilly. Thus, the limit parts of your proofs will be graded to a
lesser standard than other parts of your proofs, as a little treat. Still try to be as rigorous
as possible, and we will keep it in mind during grading. Thank you!
1 Topology in Rn
This section is a crash course in the parts of topology relevant for this power round. There
are no problems, but the concepts introduced here are important technical details that we
need for fractals. Without them, fractals would be too hard to study and understand.
Rn is the set of n-tuples (x1, ..., xn) with that every xi ∈ R.1 Two points of Rn can be
added term-wise and multiplied by a scalar c ∈ R:
(x1, ..., xn) + (y1, ..., yn) = (x1 + y1, ..., xn + yn)
cx = c(x1, ..., xn) = (cx1, ...cxn)
Denote the special element (0 , ...,0) as simply 0. Given an element x = (x1, ..., xn) ∈ Rn,
we define the Euclidean norm to be
|x| =
vuut
nX
i=0
x2
i
For example, in R2, this is the distance formula
|x| =
q
x2
1 + x2
2
The Euclidean metric is how we measure distance. We define dist( x, y) = |x − y|.
This function satisfies 3 very important properties:
1. dist( x, y) ≥ 0 for all x, yand equality is achieved if and only if x = y.
2. dist( x, y) = dist(y, x).
3. (triangle inequality) dist( x, t) ≤ dist(x, z) + dist(z, y).
We will usually avoid the notation ”dist( x, y)” and just use |x − y|.
For a point x0 ∈ Rn, we define an open ball at x0 with radius r ≥ 0 as
Bx0(r) = {x : |x − x0| < r}
That is, it is the set of all points less than r away from x0. Notice the ” <” - it is a strict
inequality.
Similarly, the closed ball is the set of points
Bx0(r) = {x : |x − x0| ≤r}
An open set is a subset of Rn which is a(n arbitrarily large, even infinite) union of
open balls. Clearly, any open ball in Rn is also an open set.
Here are three crucial properties of open sets:
1for n = 2, n-tuple notation conflicts with the open interval notation ( a, b). Context should make the
notation clear.
1. ∅, Rn are both open sets.
2. If {Uα}α is an arbitrary collection of open sets (indexed by α), then S
α Uα is an open
set. This is immediate from the definition.
3. (Nontrivial) If {Ui}i is a finite collection of open sets, then T
i Ui is an open set. This
is not true for arbitrary intersections.
Example. The unit open cube, consisting of the points [0 , 1]n = (x1, ..., xn) ∈ Rn such that
0 < xi < 1 for all xi, is an open set.
Proof. For any pointx ∈ [0, 1]n, there exists somer0(x) depending on x such that Bx(r0(x)) ⊂
[0, 1]n (convince yourself that this is true!). Then
[0, 1]n =
[
x∈[0,1]n
Bx(r0(x))
Notice that this union is over an uncountably infinite number of elements, one ball for each
x in the cube.
A set is a closed set if it is a complement of an open set. For example, given an r and
an x0, the set of points {x : |x − x0| ≥r} is a closed set. The closed ball,
Bx0(r) = {x : |x − x0| ≤r}
is a closed set. Again, convince yourself this is true. Here are the properties of closed sets:
1. ∅, Rn are both closed sets.
2. If {Cα}α is an arbitrary collection of closed sets, then T
α Cα is a closed set.
3. If {Ci}i is a finite collection of closed sets, then S
i Ui is a closed set. This is not true
for arbitrary intersections.
The last important property is that of compactness: a set K ⊂ Rn is compact if and
only if it is both closed and bounded; that is, its complement is open, and there exists some
B(0,...,0)(r) such that K ⊂ B(0,...,0)(r).
Theorem 1.0.1. Let
K0 ⊃ K1 ⊃ K2 ⊃ ...
be a countably infinite sequence of compact sets in Rn, each one of which containing the
rest of them. Suppose that they are all non-empty. Then T
i Ki is also non-empty.
Note that ∩iKi is also compact since it is bounded and closed, being an intersection of
closed sets.
2 Measures
A measure is any way which we use to describe ”size” to sets, especially when seen as subsets
of a larger space. They are designed to generalize and formalize the intuitive notions of
length, area, volume, and probability that we know and love.
Let X be a set, and Σ ⊂ P(X) a subset of the power set of X.
Definition 2.0.1. Σ is called a σ-algebra on X if it is closed under complements, countable
unions, and countable intersections. That is, if {Ei}∞
i=1 ⊂ Σ ⊂ P(X), then
1. ∅ ∈Σ
2. X \ Ei ∈ Σ
3. S∞
i=1 Ei ∈ Σ
4. T∞
i=1 Ei ∈ Σ
These include finite intersections and unions.
In short, a σ-algebra is a set of subsets which play very nicely with set-theoretic opera-
tions. Also notice that first two conditions immediately imply that X ∈ Σ.
Problem 2.0.1. Which of the following sets are σ-algebras over X = {0, 1, 2, 3, 4}?
1. Σ = {∅, X}
2. Σ = {∅, 0, 1, 2, 3, 4, X}
3. Σ = {∅, {0, 1}, {2, 3, 4}, {0, 1, 2, 3, 4}}
4. Σ = {∅, {0}, {1}, {0, 1}, {1, 2}, {1, 2, 3, 4}, {0, 2, 3, 4}, X}
It turns out that when doing work with fractals, it is imposible to attempt to deal with
arbitrary subsets of Rn, which is why we will restrict ourselves to the following σ-algebra:
The Borel algebra over Rn is defined to be the smallest σ-algebra on Rn which contains
all open sets. By the definition of σ-algebras, this means that it also contains all countable
unions, intersections, and complements of open sets in Rn. Elements of the the borel sigma
algebra are called Borel sets.
Now, let µ : Σ → R ∪ {∞}be a function to the extended real line . Here we take the
extra element infinity to be such that if a ∈ R, then a <∞. We may sometimes denote it
as R.
Definition 2.0.2. µ is a measure if:
1. µ(∅) = 0
2. µ(E) ≥ 0 for all E ∈ Σ.
3. Let {Ei}∞
i=1 ⊂ Σ be a collection of elements of Σ which are pairwise disjoint: that is,
for i ̸= j, Ei ∩ Ej = ∅. Then 2
µ
 ∞[
i=1
Ei
!
=
∞X
i=1
µ(Ei)
Condition 1 is mostly a technicality, whereas conditions 2 and 3 are important to what
it means to be a measure. Condition 2 represents the idea that something may not have
a ”negative area.” Condition 3 tells us that for a measure, ant set is the sum of its parts.
This should be familiar with one’s intuition for the regular area or volume of a shape.
We call the triplet ( X, Σ, µ) a measure space if Σ is a σ-algebra on X and µ is a
measure for Σ.
Problem 2.0.2. Let X be any set and Σ = P(X). Let µ : Σ → R be defined as
µ(A) = #A, the cardinality of A, if A ⊂ X is finite, and µ(A) = ∞ if A is infinite.
1. Verify that Σ forms a σ-algebra over X.
2. Verify that µ forms a measure over ( X, Σ).
This measure is called the counting measure. It is the simplest non-trivial measure.
Problem 2.0.3. Verify that in a measure space ( X, Σ, µ) with A, B∈ Σ, if A ⊂ B
then µ(A) ≤ µ(B).
Problem 2.0.4 (Countable Subadditivity ). Let ( X, Σ, µ) a measure space; show
that for any countable collection {Ei}∞
i=1 ⊂ Σ,
µ
 ∞[
i=1
Ei
!
≤
∞X
i=1
µ(Ei)
[Hint: think about what you would do for the finite case first.]
Problem 2.0.5. Let X be any set and Σ = P(X). Let x0 ∈ X be a designated point
in X. Now, define µ : Σ → R so that µ(A) = 1 if x0 ∈ A, and µ(A) = 0 otherwise. Is
(X, Σ, µ) a measure space?
2Since we are working with non-negative numbers, the infinite sum, if it converges, is well-defined and
absolute. If it diverges or has an ∞ term, then the sum is defined to equal ∞. When working with
infinite sums of positive numbers, you may assume standard facts that are true for finite sums, such as the
distributive law, commutativity, associativity, etc. Also, this definition includes the case of a finite sum /
union
2.1 Hausdorff measure
The Hausdorff measure is the measure we actually care about in this Power Round. Actually,
there is no one Hausdorff measure; there is a Hausdorff measure for every non-negative real
number s. If s is an integer, then the Hausdorff meaure is just the regular length, area,
volume, etc that we are accustomed to! Thus, it is a generalization of the regular concept
of area.
Let S ⊂ Rn. Define the diameter of S as
|S| = sup
x,y∈S
|x − y|
Notice that S is a set but x − y is a point, so the notation does not clash.
Problem 2.1.1. For any set E and any ϵ >0, show that there exists a convex, open
set U ⊃ E such that |U | ≤ |E| + ϵ. (for U to be convex means that if x, y∈ U , then
for any t ∈ [0, 1], tx + (1 − t)y ∈ U ). [hint: first find a set satisfying just convexity]
Now, let F ⊂ Rn. Then, fixing some δ >0, let {Ui}i be any finite or countably infinite
number of sets, such that two properties are satisfied:
1. F ⊂ S
i Ui
2. |Ui| < δ
Then {Ui}i is called a δ-cover of F .
Problem 2.1.2. let [0, 1] ⊂ R. Which of the following are δ-covers of [0, 1], for δ = 1
2 ?
1. {(− 1
3 , 1
3 ), ( 1
3 , 2
3 ), ( 2
3 , 4
3 )}
2. {[0, 1
n ] : n ∈ N}
3. {[0, 1
2 ], [ 1
2 , 1]}
We define the outer s-dimensional Hausdorff measure as follows:
Hs
δ(F ) = inf
( ∞X
i=1
|Ui|s : {Ui} is a δ-cover of F
)
Where the infimum is taken over all possible δ-coverings of F . By problem 2.1.1, it suffices
to consider δ-coverings where every element of the covering is open and convex.
Problem 2.1.3. Let 0 < δ1 < δ2; show that
Hs
δ1(F ) ≥ Hs
δ2(F )
Because of the previous exercise, there is a well defined limit
Hs(F ) = lim
δ→0
Hs
δ(F )
(where Hs(F ) could be infinity). This is the s-dimensional Hausdorff measure of F .
We need to justify that it actually is a measure:
Problem 2.1.4. Prove the following:
1. Hs(E) ≥ 0 for all E ⊂ Rn.
2. Hs(∅) = 0
3. Prove countable subadditivity for the s-dimensional Hausdorff measure (see prob-
lem 2.0.4).
Full additivity for the measure is true over Borel sets (but harder to prove), and thus
Theorem 2.1.1. For each s ≥ 0, the s-dimensional Hausdorff measure is a measure on Rn
over the Borel σ-algebra.
From here on, we may assume that every set mentioned is a Borel set and thus has a
Hausdorff measure (this includes when you are solving problems).
Problem 2.1.5. (homogeneity) Let E ⊂ Rn and 0 < c∈ R Then let E′ be E scaled
up by c, that is, E′ = {cx : x ∈ E}. Show that for all s,
Hs(E′) = csH s(E)
[Hint: cover E using covers of E′ and vice-versa]
Problem 2.1.6. (translation invariance) Let E ⊂ Rn and x ∈ Rn. Let E′ = E+x =
{e + x : e ∈ E}. Show that for all s, Hs(E) = Hs(E′).
Problem 2.1.7. For 0 < r < sand E ⊂ Rn, prove the following:
1. Hr(E) ≥ Hs(E).
2. If Hr(E) < ∞, then Hs(E) = 0.
[Hint: for both of these, fix 0 < δ <1 and use coverings where |Ui| < δ]
This problem demonstrates that for any E, there is a critical value s where the Hausdorff
measure jumps from 0 to ∞, and this value s is the only possible value where the Hausdorff
measure might be both non-zero and non-infinite.
Definition 2.1.2. This critical value of s is the Hausdorff dimension of E.
Note: just because the dimension of a set E is s does not mean that Hs(E) > 0. It
could very well be that the measure drops from infinity directly to zero. That said, the
dimension is still be defined.
Problem 2.1.8. Prove that if E ⊂ Rn, then the Hausdorff dimension of E is ≤ n.
Problem 2.1.9. Prove that H0 is simply the counting measure.
Because of this, we will freely assume s >0.
3 Interlude: some fractal constructions
There are no problems in this section: instead, we will provide several constructions of
fractals which we will base problems off of in later sections.
3.1 Cantor Set
Let C0 be the closed unit interval C0 = [0 , 1] ⊂ R. Then let C1 = C0 \ ( 1
3 , 2
3 ) =
[0, 1
3 ] ∪ [ 2
3 , 1]. Notice that C1 is the disjoint union of two closed intervals. We will construct
Cn+1 from Cn as follows: by induction, each Cn is a finite disjoint union of closed intervals
Cn = S
j[aj, bj], and each interval is length 3 −n. Thus, let
Cn+1 =
[
j
 
[aj, bj] \ (aj + 3−n−1, bj − 3−n−1)

This process removes the middle third of each interval. Since Cn+1 is clearly also the
finite union of disjoint closed intervals, it follows by induction that Ci exists for every i,
and that Ci+1 ⊂ Ci.
Then, define the Cantor Set C as
C = ∩∞
i=0Ci
This intersection is non-empty and compact since it is the intersection of a decreasing
sequence of compact sets.
3.2 Sierpinski Carpet
Figure 1: The construction of the Sierpinski Carpet.
Start with the closed unit square □0 = [0 , 1] × [0, 1]. To go from □i to □i+1, divide
each component square into 9 equal new squares, and remove the central open square, as
in figure 1. At stage □k there will be 8 k squares, each with sidelength 3 −k.
Note that when we remove the center square, we are deleting the open component.
For example, □1 = □0 \
 
( 1
3 , 2
3 ) × ( 1
3 , 2
3 )

. Thus, each □i is closed and so compact, and
□i+1 ⊂ □i. Thus,
□ =
\
i
□i
Is non-empty by compactness. □ is the Sierpinski Carpet.
3.3 Minkowski Sausage
Let M0 = [0, 1] the interval. At each stage, replace every interval in Mi with the interval
pattern as in figure 2 on the left to createMi+1. Each interval in Mk is length 4−k, and there
are 8 k such intervals. Notice that in M1, for example, we consider there to be 8 intervals
each with length 1
4 , even though two of the intervals are colinear. There is a well-defined
limit of this process which results in a compact fractal denoted as M , called the Minkowski
Sausage.
3.4 Koch Curve
Let K0 = [0, 1] the interval. At each stage, replace every interval in Ki with the interval
pattern as in figure 2 on the right to create Ki+1. Each interval in Kk is length 3 −k, and
there are 4 k such intervals. Notice that in K1, for example, we consider there to be 4
intervals each with length 1
3 . There is a well-defined limit of this process which results in a
compact fractal denoted as K, called the Koch Curve.
Figure 2: (Left) the construction of the Minkowski Sausage. (Right) the Koch Curve
4 Iterated Function Systems
An iterated function system is a method of generating self-similar fractals. All the fractals
in the interlude, as well as many more, may be created using this method.
Definition 4.0.1. A function f : Rn → Rn is called a contraction if there exists some
constant 0 < c <1 such that for every x, y∈ Rn, |f (x) − f (y)| = c|x − y|. The value c is
called the contraction ratio for f .
Reworded, a contraction is a function that sends points closer to each-other by some
common factor.
An iterated function system (IFS), then, is just a finite set of contractions (f1, ..., fm),
m ≥ 2 (they are assumed to all have the same domain and codomain, but not necessarily
the same contraction ratios).
Problem 4.0.1. Let f be a contraction in Rn. Denote f (k) to be f composed with
itself k times (e.g., f (2)(x) = f (f (x))).
1. Show that for any x, y∈ Rn and any ϵ > 0, there exists some k such that
|f (k)(x) − f (k)(y)| < ϵ.
2. Show that if one replaces the contraction assumption with the weaker |f (x) −
f (y)| < |x − y| (for x ̸= y), then there exist such functions with no fixed points;
that is, no x such that f (x) = x.
Problem 4.0.2. If f is a contraction and K is compact, show that f (K) is compact.
A subset D ⊂ Rn is said to be self-similar if it is the union of contractions of itself;
that is, if there exists an IFS ( f1, ..., fm) such that
D =
m[
i=1
fi(D)
The union is allowed to intersect itself, so that for instance f1(D) ∩ f2(D) ̸= ∅. In this case,
the D is called and attractor of the IFS ( f1, ..., fm).
Theorem 4.0.2. Every IFS (f1, ..., fm) is the attractor of a unique, non-empty, compact
set F .
Proof. Let the IFS be ( f1, ..., fn): there exists a compact set C such that fi(C) ⊂ C for all
i: in fact, the closed ball B(0,...,0)(r) suffices for r sufficiently large. C exists by the following
argument:
Let ci be the contraction ratio for each fi; let ri = |fi(0)|
1−ci
and |x| ≤ri. Then
|fi(x)| ≤ |fi(x) − fi(0)| + |fi(0)| = ci|x| + |fi(0)|
≤ ciri + |fi(0)| =
 ci
1 − ci
+ 1

|fi(0)|
= ci + 1 − ci
1 − ci
|fi(0)| = |fi(0)|
1 − ci
= ri
By setting r = maxi(ri), we get our desired ball B0(r).
Next, for X a set, define f (X) = S
i fi(X), and define f (k)(X) to be f composed with
itself k times as in problem 4.0.1.
Then for each k, f (k)(C) is a compact set (cf. problem 4.0.2). Since f (C) ⊂ C, by
repeated application of f to both sides, f (k)(C) ⊂ f (k−1)(C). Thus,
C ⊃ f (C) ⊃ f (2)(C) ⊃ ...
Forms a decreasing sequence of compact sets, so
F =
\
k
f (k)(C)
is non-empty and compact, and it is clear that
f (F ) = f
 \
k
f (k)(C)
!
=
\
k
f (k+1)(C) =
\
k
f (k)(C) = F
Showing existence.
Problem 4.0.3. Prove uniqueness of the above theorem. That is, prove that if
(f1, ..., fm) is the attractor of two non-empty, compact sets F1, F2, then F1 = F2.
[Hint: at some point, it may be useful to prove the following alternative description
of closed sets: a set C is closed if and only if C contains all points x such that for all
r >0, Bx(r) ∩ C ̸= ∅]
The set D is called the attractor of the IFS. Sometimes we will abuse notation and
refer to something as an IFS when really we mean the attractor of it. No confusion should
arise since attractors are unique.
Example. Let
f1(x) = 1
3 x
f2(x) = 1
3 x + 2
3
be functions R → R. Then the Cantor set is the attractor of the IFS ( f1, f2).
Problem 4.0.4. For each of the following fractals, find an IFS whose attractor is that
fractal and explain why it is the attractor.
1. the Sierpinski carpet
2. the Koch Curve
3. the Minkowski Sausage
4.1 Dimension of IFS’s
Clearly, the Hausdorff dimension of an attractor of an IFS whose domain and codomain is
Rn is at most n. Unfortunately, it is not always true that there is a nice way to glean the
exact Hausdorff dimension from the functions which make up an IFS. However, in practice,
most IFSs we care about satisfy the following condition:
Definition 4.1.1. An IFS ( f1, ..., fm) satisfies the Open Set Condition (OSC) if there
exists a bounded, non-empty open set U ⊂ Rn such that for each i ̸= j,
fi(U ) ∩ fj(U ) = ∅
and
U ⊃
[
i
fi(U )
Given this condition, there is the following remarkable result:
Theorem 4.1.2. Let (f1, ..., fm) be an IFS, with ci the contraction ratio for fi. Then the
unique real number s such that
mX
i=1
cs
i = 1
is the Hausdorff dimension of the attractor for the IFS.
Proof. Elementary but long and technical, so ommitted.
Problem 4.1.1. Let f1, f2, f3 : R2 → R2 be defined as
f1(x) = 1
2 x
f2(x) = 1
2 x + (1
2 , 0)
f3(x) = 1
2 x +
 
1
4 ,
√
3
4
!
Show that this IFS satisfies the open set condition, and calculate its attractor’s Haus-
dorff dimension with proof.
Problem 4.1.2. Verify that the Hausdorff dimension of the Cantor Set is log 2
log 3, and
find the Hausdorff dimension of the Koch Curve.
Problem 4.1.3. Use 4.1.2 to give a proof that the Cantor set is uncountable.
Example. Here is a method to show that the Hausdorff-measure Hs(C) of the Cantor
set is less than or equal to 1 (with s = log 2
log 3, as shown in problem 4.1.2). Since, in the
definition of Hausdorff measure, we use an infimum of δ-coverings, as δ → 0, all we have to
do is demonstrate that for any δ, we can provide a δ-covering with the sum of the scaled
diameters arbitrarily close to 1.
In fact, our covers are going to be exactly the disjoint intervals we used in the construc-
tion of C! In the construction, Cn is a finite, disjoint union of 2 n closed intervals, each of
length 3 −n. Thus, each Cn comes from a 3 −n-cover; so let that cover be indexed as {Ei}.
Then X
i
|Ei|log 2/ log 3 = 2n(3−n)log 2/ log 3 = 2n2−n = 1
Since for every δ >0, there exists some k such that 3 −k < δ, we have a δ-cover of size
1 for every δ. Thus, Hs(C) ≤ 1. In fact, Hs(E) = 1, but that is harder to show.
Problem 4.1.4. Let n, m∈ N. Show that there is a k and a set E ⊂ Rk such that the
Hausdorff dimension of E is n
m . Conclude that for any 0 ≤ r ∈ R, there exist sets with
Hausdorff dimensions arbitrarily close to r.
It is important to note, however, that many self-similar fractals do not satisfy the open
set condition.
Problem 4.1.5. Construct an example of an IFS which does not satisfy the OSC, and
where no two functions in the IFS are equal.
4.2 Mass Distribution Principle
Definition 4.2.1. A Mass Distribution on a compact set F ⊂ Rn is a measure µ on F
such that 0 < µ(F ) < ∞.
Theorem 4.2.2 (Mass Distribution Principle). Let µ be a mass distribution on F , and let
s be the Hausdorff dimension of F . Suppose there exist c, ϵ >0 such that for all U ⊂ F
with |U | ≤ϵ,
µ(U ) ≤ c|U |s
Then
Hs(F ) ≥ µ(F )
c
Proof. Let {Ui} be an ϵ-covering of F . By countable subadditivity and the assumptions of
the theorem,
0 < µ(F ) ≤ µ
 [
i
Ui
!
≤
X
i
µ(Ui) ≤ c
X
i
|Ui|s
For δ < ϵ, we take infima over all δ-coverings {Ui}i,
0 < µ(F )
c ≤ Hs
δ(F )
As we draw δ → 0, we get
0 < µ(F )
c ≤ Hs(F )
Problem 4.2.1. Prove that the real line has Hausdorff dimension 1, but H1(R) = ∞.
[Hint: work over [0 , 1]].
The Mass Distribution principle is one of the few systematic ways to provide non-trivial
lower bounds on the Hausdorff measure of a set.
Example. Let’s describe a mass-distribution µ on the cantor set C. Remember that the
Cantor set is constructed in steps, with the kth step consisting of 2 k disjoint intervals, each
of length 3 −k. Define
µ(Ik ∩ C) = 2−k
For Ik one of those kth level intervals; take a second to make sure that this is well-defined.
for U ⊂ C, we define µ(U ) to be the value obtained by approximating U it with smaller
and smaller Ik ∩ C: that is,
µ(U ) = inf
(X
i
µ(Ei) : U ⊂
[
i
Ei, Ei is an interval in the construction
)
Let |U | < 1; there exists some k such that 3−(k+1) ≤ |U | < 3−k. Then U ⊂ Ik ∩ C for Ik
one of the intervals generated in the kth step (as discussed above). Then by problem 2.0.3,
µ(U ) ≤ 2−k = (3log 2/ log 3)−k
= (3−k)log 2/ log 3 = (3 · 3−(k+1))log 2/ log 3
≤ (3|U |)log 2/ log 3
From problem 4.1.2, the dimension of C is precisely log 2 / log 3, so from the Mass-
Distribution principle,
Hs(F ) ≥ 3− log 2/ log 3 = 1
2
Theorem 4.2.3. Let s = log 2
log 3. Let C be the Cantor Set. Then
1
2 ≤ Hs(C) ≤ 1
Proof. examples 4.1 and 4.2.
It turns out that in fact Hs(C) = 1 using a slightly more involved technique, but our
bounds here are nothing to shake a stick at.
Problem 4.2.2. Find a mass distribution on the Cantor set such that the hypothesis
of the Mass Distribution Principle is not met. More specifically, that for all c, ϵ >0,
there is some U ⊂ C where |U | ≤ϵ, but
µ(U ) > c|U |s
The example for the Cantor set provides a way to come up with a natural measure
on any attractor of an IFS that satisfies OSC. Let our IFS be ( f1, ..., fm) with contraction
ratios c1, ..., cm, and attractor E. Then let s be the dimension of E, as determined via the
OSC. Lastly, denote fi1,i2,...,im(X) to be fi1(fi2(...(fim(X)))). Then we can define
µ(fi1,i2,...im(E)) = cs
i1cs
i2...cs
im
Notice that µ(E) = 1. The crucial fact to verify is that
mX
k=1
µ(fk(E)) = µ
 m[
k=1
fk(E)
!
= µ(E)
And indeed this follows from the definition of the attractor and of µ.
Lastly, we extend this to Borel subsets of E. The easiest way is indeed the right way to
do it: if A ⊂ E, then let Jk = {fi1,i2,...ik (E) : fi1,i2,...ik (E) ⊂ A}. That is, Jk is all the level
k copies of E that fit inside of A.
µ(A) = lim
k→∞
X
E∈Jk
µ(E)
This is fancy notation for saying in order to get µ(A), we simply add the measure of all the
sets which we can pack into A that we’ve already defined the measure for.
Theorem 4.2.4. For E the attractor of the IFS (f1, ...fm) satisfying the OSC, the natural
measure described above is a mass distribution.
Even though extension to Borel sets makes the natural measure an actual measure,
notice that in example 4.2, we avoided having to use that part of the definition by passing
immediately to the intervals using sub-additivity. It would be wise for you to do the same.
Theorem 4.2.5. If an attractor E satisfies the OSC, with dimension s, then Hs(E) > 0.
Proof. Too long.
Problem 4.2.3. Give an explicit, non-trivial (greater than 0) lower bound on the
Hausdorff measure of the Cantor dust C × C ⊂ R2, the product of the Cantor set with
itself, in the appropriate dimension.
[Hint: first find an IFS whose attractor is the Cantor Dust to compute the Hausdorff
dimension, then proceed as in example 4.2]
Problem 4.2.4. Show that the open set V which satisfies OSC for the Cantor set C
can be made to have intersection C ∩ V ̸= ∅ (this is called the Strong Open Set
Condition). In fact, show that V can even be made to contain C entirely. How much
of this is true for the Sierpinski Carpet as well?
Problem 4.2.5. Construct an example of a set with Hausdorff dimension 1 but with
0 measure. [Hint: can you construct a cantor-like set for each dimension s <1?]
Problem 4.2.6. Describe a mass distribution for the Sierpinski carpet inspired by its
construction in the interlude. Use it (again mimicking the example for the cantor set)
to give a lower bound on the Hausdorff measure in the appropriate dimension.
5 Sierpinski Triangle
The Attractor of the IFS described in problem 4.1.1 is called the Sierpinski T riangle
(sometimes the Sierpsinki Gasket) and will be denoted as
 . It looks like this:
For clarity, we restate here the IFS for
 :
S1(x) = 1
2 x
S2(x) = 1
2 x +
 1
2 , 0

S3(x) = 1
2 x +
 
1
4 ,
√
3
4
!
This quickly gives us that the Hausdorff dimension of
 is s = log 3
log 2.
Since
 satisfies the OSC, we can provide the natural measure on it: we will again
describe it here for clarity. let ∆ be the equilateral triangle with vertices (0 , 0), (1, 0) and
( 1
2 ,
√
3
2 ). It is clear that
 ⊂ ∆. Thus also S1(
 ) ⊂ S1(∆) and so on. Let In = (i1, i2, ..., in)
be a list with each ik ∈ {1, 2, 3}, and set SIn(∆) = Si1(Si2(...(Sin(∆)))). Then for any such
In, we define µ(SIn(∆) ∩
 ) = 3−n.
Problem 5.0.1. Show that 1
6 ≤ Hs(
 ) ≤ 1.
Now we will describe a refinement on the Mass-Distribution principle that allows us, in
theory, to get arbitrarily close upper and lower bounds on Hs(
 ).
Definition 5.0.1. Let µ be the natural measure on
 . Define Tn = {SIn(
 ) : In =
(i1, ..., in), ik ∈ {1, 2, 3}} be the collection of all 3 n self-similar scalings of size 2 −n of the
Sierpinski triangle. Now let {∆i}i ⊂ Tn be a non-empty collection of those scalings.
So lastly, define
an = min
{∆i}i⊂Tn
 | S
i ∆i|s
µ(S
i ∆i)

The intuition behind this idea is that we are finding a ”densest” subset possible at any
given level.
Problem 5.0.2. Find a1 and a2. (Take your time with this and draw some pictures!
Doing this problem slowly will help a lot with the other problems in this section)
Theorem 5.0.2. Hs(
 ) ≤ an.
Proof. The original proof for this is easy, but a tiny-bit more than elementary, so we provide
a more elementary proof sketch instead.
For each δ, we will provde a covering based on an such that Hs
δ(
 ) ≤ an. We will start
with showing it for Hs
1(
 ).
Since an is the finite minimum over non-empty subsets of Tn, there is some collection
{∆i}i, i≥ 1, which minimizes an. Call this collection U , with # U = k. Lastly, let U =S
∆i∈U ∆i.
If U =
 , we are done; it is already a cover for
 , and a calculation shows the theorem
is satisfied.
Otherwise, let V = Tn \ U ; # V = 3 n − k. Each element of V will be covered in a
scaled down way like we covered
 itself: if SIn(
 ) = ∆ ′
m ∈ V , then scale down each
element of U and place it in V at the 2 n-level of the construction of
 . That is, if we
denote our scaled-down U as U ′ and notating U′ similarly, then |U′| = 2−n|U|. There will
be #V = 3n − k of these U ′s, one for each missed element of Tn that U does not hit. Our
covering so far consists of U, and the 3 n − k sets congruent to U′. Now, since U ̸=
 , our
new covering also doesn’t cover
 , so we create a U ′′ by scaling down U again, this time
so that |U′′| = 2−n|U′′| = 2−2n|U|, and there will be (# V )2 of these, and so on.
Letting this process run to infinity, we get a cover of
 consisting of 1 copy of U, 3n − k
copies of U′, (3n − k)2 copies of U′′, and so on; thus,
Hs
1(
 ) ≤
∞X
i=0
(3n − k)i|U(i)|s
=
∞X
i=0
(3n − k)i(2−in|U|)s
= |U|s
∞X
i=0
 3n − k
3n
i
= |U|s
1 − 3n−k
3n
= |U|s
k
3n
= |U|
µ(U) = an
Where we use the definition ofHs
δ and s = log 3/ log 2, the definition ofan, and the geometric
series formula.
Now, for δ <1, there exists some m ∈ N such that 2 −m < δ. This part is fairly easy.
Instead of starting with the cover U , simply start with 3 m copies of U scaled down by 2−m,
one at each level m tile of
 . Then perform the process as stated above for each of the
scaled down copies of U . At each stage we will simply get 3 n extra copies of U (n), and each
of them will have a diameter scaled by 2 −n. So we get
Hs
δ(
 ) ≤ 3m
" ∞X
i=0
(3n − k)i(2−n|U(n)|)s
#
= 3m2−n log 3/ log 2
" ∞X
i=0
(3n − k)i(|U(n)|)s
#
=
∞X
i=0
(3n − k)i(|U(n)|)s = an
Using the definition of s and the earlier calculation. Since the largest cover we used this
time was size 2 −n < δ, this is a valid covering for Hs
δ, and taking the limit gives
Hs(
 ) ≤ an
Problem 5.0.3. Show that an decreases as n increases.
Since an > 0 is clear, it immediately follows that L = lim n→∞ an exists and L ≥ 0.
Combining it with the previous theorem, we get that Hs(
 ) ≤ L (and therefore also that
L >0).
Theorem 5.0.3. Hs(
 ) = limn→∞ an.
Proof. This follows from the remark above by showing thatL ≤ H s(
 ). We first remember
that the only good way we have of creating lower bounds is the mass distribution principle,
we thus want to show that for any set U ⊂
 , µ(U ) ≤ 1
L |U |s. This will imply that
Hs(
 ) ≥ L by mass distribution.
µ(U ) = lim
n→∞
µ


[
SIn (
 )⊂U
SIn(
 )


≤ lim
n→∞
1
an

[
SIn (
 )⊂U
SIn(
 )

s
≤ lim
n→∞
1
an
|U |s = 1
L |U |s
The questionable implications here are the first equality and the first inequality. The
first comes from our definition of the natural measure, and the inequality comes from our
definition of an.
Problem 5.0.4. Find some A <0.9 such that Hs(
 ) ≤ A and prove it.
[Hint: find a covering that shows that ak < 0.9 for some k]
The best known current bounds on Hs(
 ) are proven using a continuation of the meth-
ods developed during this Power Round:
Theorem 5.0.4. 0.77 ≤ Hs(
 ) ≤ 0.82
The area is an active field of research.
Problem 5.0.5. Generalize the construction in this section to the Minkowski Sausage
M (with dimension m), and use it to prove that Hm(M ) ≤ 0.8.
Problem 5.0.6. Find a3 (use of a computer program is allowed for the computation
itself, although the code must be provided and justified).
Problem 5.0.7. Use the following fact about
 to show that Hs(
 ) ≥ 0.3: for all n,
H s(
 ) ≥ ane− 16
√
3
3 s( 1
2 )
n
[Hint: find a4 (use of a computer program is allowed for the computation itself,
although the code must be provided and justified)]
This concludes the Power Round. Congratulations!
Team Number:
PUMaC 2023 Power Round Cover Sheet
In years past, this page was for hand-turned in submissions. Now it is for reference for
you guys! So that you know how many points each problem is worth.
Problem Number Points Attempted?
2.0.1 5
2.0.2 5
2.0.3 5
2.0.4 10
2.0.5 5
2.1.1 15
2.1.2 5
2.1.3 10
2.1.4 15
2.1.5 10
2.1.6 5
2.1.7 10
2.1.8 10
2.1.9 5
4.0.1 15
4.0.2 10
4.0.3 15
4.0.4 10
4.1.1 5
4.1.2 5
4.1.3 5
4.1.4 15
4.1.5 10
Problem Number Points Attempted?
4.2.1 10
4.2.2 10
4.2.3 5
4.2.4 5
4.2.5 20
4.2.6 15
5.0.1 10
5.0.2 5
5.0.3 5
5.0.4 10
5.0.5 25
5.0.6 40
5.0.7 50
