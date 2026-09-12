# PUMaC Power Round 2021

PUMaC 2021 Power Round:
Mixed Volumes and Convex Bodies
Alan Yan
Spring 2022
Rules and Reminders
1. Your solutions should be turned in by 12PM Thursday , March 24th, EDT. You
will submit the solutions through Gradescope. The instructions describing how to log
into Gradescope will be sent to the coaches. The deadline for submission is clearly
visible on the Gradescope site once you enroll in the course.
Please make sure you submit you work on time. No late submissions will be
accepted. Please do not submit your work using email or in any other way. If you
have questions about Gradescope, please post them on Piazza.
You may either typeset the solutions in L ATEX or write them by hand. We strongly
encourage you to typeset the solutions. This way, the proofs end up being clearer.
Moreover, you might want to use some of the LATEX resources listed in point 2.
In case your solutions are handwritten, the cover sheet (the last page of this document)
should be the first page of your submission. In case you typeset your solutions, please
take a look at the Solutions Template we posted and make sure the cover sheet is the
first page of your submission.
Each page should contain the team number (not team name) and problem num-
ber. This number can be found by logging in to the coach portal and selecting the
corresponding team. Solutions to problems may span multiple pages. If so, make sure
to collate them in the proper order.
2. You are encouraged, but not required, to use L ATEX to write your solutions. If you
submit your power round electronically, may submit several times, but only
your final submission will be graded (moreover, you may not submit any work
after the deadline). The last version of the power round solutions that we receive
from your team will be graded. Moreover, you must submit a PDF . No other file
type will be graded. For those new and interested to L ATEX, checkout Overleaf and
its online guides. If you do not know the specific command for a math symbol, check
out Detexify or TeX.StackExchange.
3. Do not include identifying information aside from your team number in your solutions.
4. Please collate the solutions in order in your submission. Each problem should start
on a new page. Points may be deducted if this format is not followed.
1
5. On any problem, you may use without proof any result that is stated earlier in the
test, as well as any problem from earlier in the test, even if it is a problem that your
team has not solved. These are the only results you may use. In particular, to solve
a problem, you may not cite the subsequent ones. The only exceptions to this rule are
common facts in the “constest math toolbox”, e.g., the Cauchy-Schwartz inequality,
the AM-GM inequality, Vieta’s relations, etc. If you are unsure whether or not you
can cite a certain result, you can also write us a private post on piazza or email. Check
point 11 for more details. You may not cite parts of your proof of other problems: if
you wish to use a lemma in multiple problems, please reproduce it in each one.
6. When a problem asks you to “find”, “find with proof,” “show,” “prove,” “demon-
strate,” or “ascertain” a result, a formal proof is expected, in which you justify each
step you take, either by using a method from earlier or by proving that everything
you do is correct. When a problem instead uses the word “explain,” an informal
explanation suffices. When a problem instead uses the word “sketch” or “draw”, a
clearly marked diagram is expected.
7. All problems are numbered as “Problem x.y” where x is the section number and y is
the the number of the problem within this section. Each problem’s point distribution
can be found in the cover sheet.
8. Y ou may NOT use any references, such as books or electronic resources,
unless otherwise specified. Y ou may NOT use computer programs, calcu-
lators, or any other computational aids.
9. Teams whose members use English as a foreign language may use dictionaries for
reference.
10. Communication with humans outside your team of 8 students about the
content of these problems is prohibited.
11. There are two places where you may ask questions about the test. The first is Piazza.
Please ask your coach for instructions to access our Piazza forum. On Piazza, you
may ask any question. However, you must mark your posts as only visible to
instructors. If these instructions are not followed, your team’s power round score
may be penalized severely. Any questions that are deemed to be useful in general will
be made public by the instructors. Secondly, you can always email questions to us at
pumacpowerround2021@gmail.com.
2
Introduction and Advice
The topic of this power round will be convex bodies and mixed volumes . We
begin with a review of some basic facts in linear algebra, topology, and analysis. Then, we
study the structure of convex bodies, which are compact and convex subsets of Rn. This
includes the facial structure, volume, and metric properties of convex bodies. The power
round culminates in the proof of a powerful inequality involving quantities associated to
collections of convex bodies called mixed volumes. At the end, there are some applications
of this inequality to combinatorics.
The power round provides the necessary machinery to solve all the problems. The key
ideas for some of the proofs of the problems can sometimes be found in previous problems.
In this way, the power round is completely self-contained.
Here is some further advice with regard to the power round:
 Read the text of every problem! Many important ideas are included in problems
and may be referenced later on. In addition, some of the theorems you are asked to
prove are useful or even necessary for later problems.
 Make sure you understand the definitions . A lot of the definitions are not easy
to grasp; don’t worry if it takes you a while to fully understand them. If you don’t,
then you will not be able to do the problems. Feel free to ask clarifying questions
about the definitions on Piazza (or email us).
 Don’t make stuff up. on problems that ask for proofs, you will receive more points
if you demonstrate legitimate and correct intuition than if you fabricate something
that looks rigorous just for the sake of having “rigor.”
 Check Piazza often! Clarifications will be posted there, and if you have a question
it is possible that it has already been asked and answered in a Piazza thread. If
not, you can ask it, as long as you post it as only visible to the instructors .
If in doubt about whether a question is appropriate for Piazza, please email us at
pumacpowerround2021@gmail.com.
 Don’t cheat. as stated in Rules and Reminders, you may NOT use any references
such as books or electronic resources. If you do cheat, you will be disqualified and
banned from PUMaC, your school may be disqualified, and relevant external institu-
tions may be notified of any misconduct.
Good luck, and have fun!
– Daniel Carter, Igor Medvedev, Aleksa Milojevic, Alan Yan
We would like to thank many individuals and organizations for their support; without
their help, this Power Round (and the entire competition) could not exist. Please refer to
the solutions of the power round for full acknowledgments and references.
3
Contents
1 Some Linear Algebra and T opology 6
1.1 Vector Spaces and Affine Spaces . . . . . . . . . . . . . . . . . . . . . . . . 6
1.2 Geometry . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
1.3 Linear Transformations . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
1.4 Spectral Theory . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
1.5 Determinants . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
1.6 Metric Spaces . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
1.7 A Brief Detour: Supremum and Infimum . . . . . . . . . . . . . . . . . . . . 16
1.8 Topology of Metric Spaces . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
2 Convex Bodies 22
2.1 Properties of Convex Sets . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
2.2 Facial Structure of Convex Bodies . . . . . . . . . . . . . . . . . . . . . . . 25
2.3 Polytopes and Polyhedra . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
2.4 More on the Facial Structure of Convex Bodies . . . . . . . . . . . . . . . . 27
2.5 Volume of Convex Bodies . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
2.6 Hausdorff Distance . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 30
3 Introduction to Mixed V olumes 32
3.1 Mixed Volume Formula for Polytopes . . . . . . . . . . . . . . . . . . . . . . 33
3.2 Extending the Mixed Volume to Arbitrary Convex Bodies . . . . . . . . . . 33
3.3 Properties of Mixed Volumes . . . . . . . . . . . . . . . . . . . . . . . . . . 34
4 An Inequality about Mixed V olumes 36
4.1 Isoperimetric Inequalities . . . . . . . . . . . . . . . . . . . . . . . . . . . . 36
4.2 Simple Consonant Polytopes . . . . . . . . . . . . . . . . . . . . . . . . . . . 36
4.3 Extending the Mixed Volume to a Bilinear Form . . . . . . . . . . . . . . . 39
4.4 Proof of Theorem 4.1.1 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 39
5 Combinatorial Applications of Mixed V olumes 41
5.1 Applications to Partially Ordered Sets . . . . . . . . . . . . . . . . . . . . . 41
5.2 Applications to Matroids . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42
4
Notation
 ∀: for all. Ex.: ∀x ∈ {1, 2, 3} means “for allx in the set{1, 2, 3}”
 A ⊂ B: subset. Ex.: {1, 2} ⊂ {1, 2, 3}
 f : A → B means that f is a map defined on the set A with values on the set B.
 f (U ), f−1(V ): If f : X → Y is a map andU ⊂ X, V⊂ Y , then f (U ) := {f (u) : u ∈ U }
and f −1(V ) := {x ∈ X : f (x) ∈ V }.
 {x ∈ S : C(x)}: the set of all x in the set S satisfying the condition C(x). Ex.:
{n ∈ N : √n ∈ N} is the set of perfect squares.
 N: the natural numbers (excluding 0)
 Z: the integers
 R: the real numbers
 [n] := {k ∈ N : 1 ≤ k ≤ n} for n ∈ N.
 |S|: the cardinality of the set S.
 [a, b] := {λa + (1 − λ)b : 0 ≤ λ ≤ 1}.
 (a, b] := {λa + (1 − λ)b : 0 < λ≤ 1}.
 [a, b) := {λa + (1 − λ)b : 0 ≤ λ <1}.
 (a, b) := {λa + (1 − λ)b : 0 < λ <1}.
All other notations used should be defined within in the power round.
5
1 Some Linear Algebra and Topology
This first section will be an introduction to linear algebra, (metric space) topology, and
(metric space) analysis. Although we approach these topics from an abstract point of
view, the main space that we will be using throughout this power round will be Rn. Set-
theoretically, this space consists of all n-tuples of real numbers. This space is nice because
not only does it have a linear structure (as you will see in the sequel), but it also admits a
natural topology and geometry. This gives us a plethora of tools to work with in this space.
1.1 Vector Spaces and Affine Spaces
We begin the power round with an abstract definition of a vector space. Although vector
spaces can be defined over any field, we will only be working with real vector spaces.
Definition 1.1.1. A (real) vector space is a set V of elements, which we callvectors, that
is equipped with (vector) addition + : V × V → V and (scalar) multiplication · : R × V → V
which satisfy the following properties:
1. (Commutativity) v1 + v2 = v2 + v1 for any v1, v2 ∈ V
2. (Associativity) ( v1 + v2) +v3 = v1 + (v2 + v3) and a · (b · v1) = (ab) · v1 for all a, b∈ R
and v1, v2, v3 ∈ V .
3. (Zero Element) There is a vector 0 := 0 V ∈ V such that v + 0 = v and λ · 0 = 0 for
all v ∈ V and λ ∈ R.
4. (Multiplicative Identity) 1 · v = v for all v ∈ V .
5. (Distributive Properties) λ · (v1 + v2) = λ · v1 + λ · v2 for all λ ∈ R and v1, v2 ∈ V .
Moreover (λ1 + λ2) · v = λ1 · v + λ2 · v for all λ1, λ2 ∈ R and v ∈ V .
When vectors and scalars are clear from the context, scalar multiplication may be written
as λv (without the ·) to mean λ · v.
Not only will we mostly restrict ourselves to real vector spaces, but we will also be
working almost exclusively with the vector space Rn and its subspaces. Explicitly, the
vector space Rn is defined as the set of n-tuples of real numbers:
Rn = {(x1, ..., xn) : x1, ..., xn ∈ R}
with the vector space operations
(x1, ..., xn) + (y1, ..., yn) = (x1 + y1, ..., xn + yn)
λ · (x1, ..., xn) = (λx1, ..., λxn).
Often, we will refer to a vector x ∈ Rn and we will implicitly let the coordinates of x
be x1, . . . , xn. The same convention will hold for any other variable. The definition of a
subspace of a vector space is probably what you would expect.
Definition 1.1.2. A subset W of a vector space V is called a subspace of V if W is also
a vector space equipped with the same vector addition and scalar multiplication as V .
6
Every vector space contains the trivial subspace {0}, which is also clearly the smallest
subspace since every vector space contains an additive identity.
Problem 1.1 (5 points). Find a non-trivial subspace of the vector space R2.
Not every subset S ⊂ V of a vector space V is a vector subspace. However, given any
subset S ⊂ V , there exists a vector subspace W ⊂ V with S ⊂ W ⊂ V . This statement
alone is not very interesting since we can simply take W = V . What is more interesting is
that there always exists a “smallest” vector subspace W ⊂ V that contains S.
Problem 1.2 (10 points) . For a subset of vectors S ⊂ V , prove that there is a vector
subspace W ⊂ V containing S which satisfies the following property: If W0 ⊂ V is a
subspace containing S, then W ⊂ W0.
From Problem 1.2, we can make the following definition.
Definition 1.1.3. For a subset of vectors S ⊂ V , let lin S be the smallest vector subspace
of V containing S. We call lin S the linear hull of S or the (linear) span of S.
Explicitly, the linear hull of S ⊂ V is the collection of vectors in V which can be written
in the form λ1s1 +. . .+λmsm where m ≥ 1 is a positive integer, the si’s are vectors in S, and
the λi’s are real number. We call such an expression a linear combination of the vectors
s1, . . . , sm. Thus, the linear hull of S ⊂ V consists of all finite linear combinations of vectors
in S. From here on out, you may use this fact without proof. This characterization may
also provide a hint for Problem 1.2. This notion of the linear span suggests a set operation
on the subsets of Rn which takes advantage of the linear structure.
Definition 1.1.4. For any non-empty subsets A, B⊂ Rn and λ ∈ R, define the following
sets
A + B := {a + b ∈ Rn : a ∈ A, b∈ B}
λ · A := {λ · a ∈ Rn : a ∈ A}.
Geometrically, λA is the image of the set A under a dilation by a factor of λ and A + B is
the subset obtained by placing a copy of A at every point in B or vice-versa.
Figure 1: Examples of P , Q, and P + Q
As an abuse of notation, when we add a subset X ⊂ Rn to a singleton {v} ⊂Rn
where v ∈ Rn, we will sometimes denote their sum by X + v without the curly braces.
Geometrically, we are translating the subset X by the vector v. The next definition will be
about affine spaces. In Problem 1.3, you will prove that affine spaces are simply translated
vector subspaces.
7
Definition 1.1.5. We call a space A ⊂ Rn an affine space if the line through any pair
of points x, y∈ A is contained in A. That is, for all x, y∈ A and λ ∈ R, we have
λx + (1 − λ)y ∈ A.
Problem 1.3 (10 points) . If A ⊂ Rn is an affine space, prove that there exists a (non-
necessarily unique) vector v ∈ Rn and a unique vector subspaceV ⊂ Rn such that A = v+V .
Similar to vector subspaces, for every subset S ⊂ Rn there exists a “smallest” affine
space which contains S. You may take this result for granted.
Definition 1.1.6. For a non-empty subset of vectors S ⊂ Rn, there exists an affine space
aff S containing S such that if W0 is an affine space containing S, then aff S ⊂ W0. We call
aff S the affine span or affine hull of S.
Remark 1.1.1. To be consistent with our naming, we call a linear combination of the form
λ1x1 +. . .+λmxm where λ1 +. . .+λm = 1 an affine combination of the vectors x1, . . . , xm.
Then, it is not hard to show that aff S contains all affine combinations of elements in S.
Since R is an infinite set, all non-trivial vector spaces will consist of an infinite number of
vectors. Hence, we cannot compare the relative sizes of vector vectors based on the number
of vectors in the space. However, when we consider the vector subspaces of for example
R3, we find subspaces that look like lines and planes through the origin. Intuitively, there
should be a notion of dimension that allows us to say that the line will be “smaller” than
the plane. Now, we will develop our definition of the dimension of a vector space.
Definition 1.1.7. The vectors v1, . . . , vm ∈ V are said to be linearly independent if the
only choice of constants λ1, . . . , λm ∈ R satisfying Pm
i=1 λivi = 0 is λ1 = . . .= λm = 0.
Conversely, if there exist constants λ1, . . . , λm ∈ R not all zero with Pm
i=1 λivi = 0, then
we say that the vectors v1, . . . , vm are linearly dependent.
Problem 1.4 (5 points). Suppose that the vectors v1, . . . , vm ∈ V are linearly independent.
Prove that every vector in lin {v1, . . . , vm} can be written uniquely as a linear combination
of v1, . . . , vm.
One interpretation of the dimension of a vector space is the number of vectors needed
to specify all the data in the space. For example, one vector is needed to specify a line and
two vectors are needed to specify a plane. The uniqueness of representation in terms of
linearly independent vectors given in Problem 1.4 then motivates a definition of dimension
in terms of the size of a set of linearly independent vectors.
Definition 1.1.8. A set of linearly independent vectors is maximal if there is no larger
set of linearly independent vectors which contain this set. Any such maximal set is called
a basis of the vector space.
We would like to define the dimension of a vector space as the size of a basis. However,
in order for this definition to be well-defined, we need that the number of elements in each
basis is the same, which is not immediately obvious. Luckily this is the case. You may
black-box the following result.
Theorem 1.1.1. Let V be a vector space. If there exists a basis with a finite number of
elements, then all bases of V have the same number of elements.
8
This allows us to define the dimension of not only vector spaces, but also affine spaces.
Definition 1.1.9 (Dimension of Vector Spaces and Affine Spaces). Let V be a vector space.
We define dim V to be the number of elements in a basis of V whenever the basis is finite
and ∞ otherwise. Let A be an affine space. From Problem 1.3, there exists a unique vector
space V that is a translate of A. We define dim A := dim V . We call dim V and dim A to
be the dimension of V and A, respectively.
Problem 1.5 (5 points). Prove that dim Rn = n.
Example 1.1.1. In R3, the subspaces of dimension 2 are the planes passing through the
origin and the subspaces of dimension 1 are the lines passing through the origin. The only
subspace of dimension 3 is R3. These are all the non-trivial subspaces of R3.
Figure 2: Example of a two-dimensional subspace (plane) of R3
Definition 1.1.10. Let e1, . . . , en ∈ Rn be the vectors where ei is 1 in the ith coordinate
and 0 everywhere else. Then e1, . . . , en is a basis called the standard basis of Rn.
1.2 Geometry
We now explore the geometry of Rn through the lens of an inner product. The inner
product will allow us to compute lengths, angles, and projections. We first give the abstract
definition of an inner product.
Definition 1.2.1. An inner product on V is a function that takes each ordered pair (u, v)
of elements in V to a number ⟨u, v⟩ ∈R with the following properties:
(i) (Positive-Definiteness) ⟨v, v⟩ ≥0 for all v ∈ V and ⟨v, v⟩ = 0 if and only if v = 0.
(ii) (Linearity in the First Variable) ⟨λu + v, w⟩ = λ⟨u, w⟩ + ⟨v, w⟩ for all u, v, w∈ V .
(iii) (Symmetry) ⟨u, v⟩ = ⟨v, u⟩ for all u, v∈ V .
Problem 1.6 (10 points) . On the vector space Rn, prove that the function ⟨·, ·⟩2 : Rn ×
Rn → R defined as
⟨x, y⟩2 :=
nX
i=1
xiyi.
is an inner product.
9
From now on, when we write an inner product ⟨·, ·⟩ on Rn without specifying the inner
product, we will default to the standard inner product ⟨·, ·⟩2. With respect to this inner
product, we can also define the Euclidean norm
∥x∥ := ∥x∥2 =
p
⟨x, x⟩ =
vuut
nX
i=1
x2
i .
Geometrically, ⟨x, y⟩ is the (scaled) length of the projection of y onto x and ∥x∥ is the
length of the vector x. Hence, the geometric meaning of ⟨x, y⟩ = 0 is that the vectors x and
y are orthogonal. In many situations, we want to work with a basis in which any two basis
vectors are orthogonal and every basis vector has unit length.
Definition 1.2.2. We say v1, . . . , vn ∈ V is an orthonormal basis of the vector space V
with respect to an inner product ⟨·, ·⟩ if it is a basis, ⟨vi, vj⟩ = 0 for i ̸= j, and ⟨vi, vi⟩ = 1.
An orthonormal basis allows us to represent every vector as a linear combination of the
basis vectors in terms of the inner product.
Problem 1.7 (5 points). Let V be a vector space and u1, . . . , un be an orthonormal basis
with respect to an inner product ⟨·, ·⟩. Then, for every v ∈ V , prove that
v =
nX
k=1
⟨v, uk⟩uk.
Example 1.2.1 (The Gram-Schmidt Process) . An inner product gives us an easy way
to construct an orthonormal basis starting from any basis. Indeed, begin with a nonzero
v1 ∈ V . Suppose we have constructed linearly independent vectors v1, ..., vm which are
mutually orthogonal. If lin {v1, ..., vm} is the whole vector space, then this set is already a
basis. Otherwise, there exists some vector w ∈ V which is not in the linear span. Consider
the vector
vm+1 = w −
mX
k=1
⟨w, vk⟩vk.
You can check that this is non-zero and orthogonal to the previous vectors. Continue this
process until our vectors span the whole vector spaces. After normalizing our vectors,
we have an orthonormal basis. This process is called the Gram-Schmidt process. Thus,
when working with a vector space with an inner product, we can always pick an orthonormal
basis.
Problem 1.8 (10 points). Consider the inner product on R3 defined by
⟨x, y⟩ := x1y1 + 2x2y2 + 3x3y3.
Find an orthonormal basis of R3 with respect to this inner product.
1.3 Linear Transformations
Now that we have developed vector spaces, we should also be interested in the structure-
preserving maps (morphisms) between them. These maps are called linear transformations
or linear maps.
10
Definition 1.3.1. For two vector spaces V, W we call T : V → W a linear map if
T (λv + µw) = λT (v) + µT (w) for all λ, µ∈ R and v, w∈ V .
Example 1.3.1 (Constructing Linear Maps). Once you have a basis, linear maps are easy
to construct. Suppose we were trying to create a linear map T : V → W . Let v1, . . . , vn be
a basis of V . Then, for any arbitrary vectors w1, . . . , wn, there exists a unique linear map
T : V → W satisfying T (vi) = wi for all 1 ≤ i ≤ n. Hence, the image of the basis vectors
are sufficient to describe the whole map.
Suppose we have a map T : V → W and fix bases v1, . . . , vn ∈ V and w1, . . . , wm ∈ W .
Then there are constants aji ∈ R such that
T (vi) =
mX
j=1
aji · wj.
From Example 1.3.1, the entire data of T is described by the images the vi. Hence, the
constants aji are sufficient to describe the map T completely. A compact way to store this
data is in a m × n matrix:
[aij] =


a11 a12 . . . a1n
a21 a22 . . . a2n
... ... . . . ...
am1 am2 . . . amn

 .
Visually, a matrix is simply a rectangular table of numbers. However, it hides two additional
pieces of data: a basis of V and a basis of W . A matrix represents a linear map from V to W
with respect to this chosen basis for V and for W . Hence, the construction in Example 1.3.1
represents the linear map T with respect to the basis {vi}1≤i≤n and the basis {wi}1≤i≤m.
For a fixed map T : V → W , the corresponding matrix will change based on which basis
we choose for V and W .
Remark 1.3.1. In the correspondence between matrices and linear maps, whenever we write
down a m × n matrix, we will implicitly assume that it is representing a map T : Rn → Rm
with respect to the standard bases.
Example 1.3.2. The matrix
1 2
3 4

represents the map T : R2 → R2 defined by T (e1) =
e1 + 3e2 and T (e2) = 2e1 + 4e2.
Given a map T : V → W , there are two associated vector subspaces.
Definition 1.3.2. Let T : V → W be a linear map. Define the subspaces
ker T := T −1(0) = {v ∈ V : T (v) = 0}
im T := T (V ) = {w ∈ W : ∃v ∈ V such that T (v) = w}.
We call ker T the kernel of T and im T the image of T .
The kernel and image satisfy the following theorem, which you may take as a black box.
Theorem 1.3.1. Let T : V → W be a linear map where V is finite-dimensional. Then
dim V = dim kerT + dim imT .
11
Problem 1.9 (10 points) . Let v1, ..., vn ∈ Rn be a basis and let α1, ..., αn ∈ R be real
numbers. Prove that there is exactly one vector w ∈ Rn that satisfies
⟨vi, w⟩ = αi
for all 1 ≤ i ≤ n.
1.4 Spectral Theory
Definition 1.4.1. Let T : V → V be a linear map. Suppose there exists a non-zero v and
constant λ ∈ R such that T v= λv. Then we call λ an eigenvalue and v an eigenvector
with eigenvalue λ.
As an example, consider the linear map T : R2 → R2 defined by T (e1) = e1 + 2e2
and T (e2) = 2 e1 + e2. This has eigenvector e1 + e2 because T (e1 + e2) = 3( e1 + e2).
The corresponding eigenvalue is 3. Note that linear maps do not necessarily have (real)
eigenvalues / eigenvectors. For example, consider the map T : R2 → R2 defined by T (e1) =
e2 and T (e2) = −e1. Geometrically, it is easy to see why this map has no real eigenvectors
since it is a rotation.
Definition 1.4.2. We call a linear map T : V → V self-adjoint with respect to an inner
product ⟨·, ·⟩ if for all x, y∈ V we have
⟨x, T y⟩ = ⟨T x, y⟩.
One easy example of a subset of the self-adjoint operators with respect to the standard
inner product are the diagonal matrices, which are maps of the form T (ei) = λiei for λi ∈ R.
Self-adjoint operators are nice because they are guarenteed to have many eigenvectors.
Indeed, you may take the following result as a black box.
Theorem 1.4.1. Suppose T : Rn → Rn is self-adjoint with respect to some inner product
on Rn. Then there exists an orthonormal basis of eigenvectors with real eigenvalues.
Let A : Rn → Rn be a linear map with inner product ⟨·, ·⟩. We say A is positive
semi-definite if A is self-adjoint with respect to the inner product and ⟨x, Ax⟩ ≥0 for
all x ∈ Rn. In the following problem, you will prove some properties of self-adjoint linear
maps.
Problem 1.10 (25 points). Let A : Rn → Rn be a self-adjoint linear map with respect to
some inner product ⟨·, ·⟩.
(a) (15 points) Let λ be the largest eigenvalue of A. Prove that
λ = sup
x̸=0
⟨x, Ax⟩
⟨x, x⟩ .
For a definition of sup, look at Definition 1.7.1.
(b) (10 points) If A is positive semi-definite, prove that
⟨x, Ay⟩2 ≤ ⟨x, Ax⟩ · ⟨y, Ay⟩
for all x, y∈ Rn.
12
When you drop the positive semi-definiteness condition, the inequality does not neces-
sarily hold, and can even reverse!
Problem 1.11 (50 points). Suppose that A : Rn → Rn is self-adjoint with respect to some
inner product ⟨·, ·⟩. Prove that the following two conditions are equivalent:
(i) The space spanned by the eigenvectors with positive eigenvalues has dimension at
most 1.
(ii) Whenever ⟨y, Ay⟩ ≥0, we have ⟨x, Ay⟩2 ≥ ⟨x, Ax⟩⟨y, Ay⟩ for all x.
The eigenvalues of matrices obtained from graphs also satisfy nice properties. We call
a matrix M a graphic matrix if there is a connected graph G with vertices {1, . . . , n}
such that M = [ Mij] where Mij = 0 whenever {i, j} /∈ E(G) and Mij > 0 otherwise.
We summarize the needed results of these matrices in Theorem 1.4.2. In this theorem, we
introduce the notion of the transpose of a matrix. If M is a n × n matrix [ Mij]1≤i,j≤n,
we define the transpose of M to be M T = [ Mji]1≤i,j≤n. Visually, M T is M with the
entries reflected across the main diagonal. In the vector space world, M T has a natural
interpretation as the matrix of the dual of the represented linear map, but this knowledge
is not required for the power round.
Theorem 1.4.2. Let M : Rn → Rn be a graphic matrix. Then, the following results are
true.
(a) M has a positive eigenvalue λ >0 that is greater than any other (real) eigenvalue.
(b) The subspace of eigenvectors of eigenvalue λ is one-dimensional and contains the
unique eigenvector (up to scalar factor) with strictly positive entries.
(c) M T also has an eigenvector with strictly positive entries with respect to the eigenvalue
λ.
The next problem is an application of Theorem 1.4.2. In the language of Markov chains,
it states that every nice Markov chain has a unique stationary distribution.
Problem 1.12 (15 points). Suppose that there are n lily pads numbered 1, . . . , non a pond
and numbers 0 < pij < 1 for 1 ≤ i, j≤ n such that P
j pij = 1 for all 1 ≤ i ≤ n. Aleksa,
being an enjoyer of aquatic plants, asks you to come up with an n-tuple (π1, . . . , πn) where
π1, . . . , πn ≥ 0 and π1 + . . .+ πn = 1. With probability πi, Aleksa will initially step onto lily
pad i. From then on, if Aleksa is on lily pad j for some 1 ≤ j ≤ n, he will move to lily pad
k with probability pjk and rest there for a second. Prove that there exists a unique n-tuple
(π1, . . . , πn) that you can give to Aleksa such that at any time, the probability that he will
be at lily pad k is πk for all 1 ≤ k ≤ n.
1.5 Determinants
Now, suppose we want to know how a linear map T : Rn → Rn would change the volume of
a object in Rn. To answer this question, we first consider a multi-linear map D : (Rn)n → R
satisfying the following three properties:
(i) (Multilinearity) For any 1 ≤ i ≤ n, vi, v′
i ∈ Rn and λ ∈ R, we have
D(. . . , vi−1, λvi + v′
i, vi+1, . . .) = λD(. . . , vi−1, vi, vi+1, . . .) + D(. . . , vi−1, v′
i, vi+1, . . .).
13
(ii) (Antisymmetry) For 1 ≤ i < j≤ n, let swapij : ( Rn)n → (Rn)n be the map that
swaps the i and j vectors. Then D(swapij(v1, . . . , vn)) = −D(v1, . . . , vn) for all 1 ≤
i < j≤ n.
(iii) (Normality) D(e1, . . . , en) = 1 where e1, . . . , en is the standard basis for Rn.
Intuitively, D is the (signed) volume for the parallelotope spanned by the vectors in its
argument. In particular, condition (iii) says that the volume of a unit cube (oriented in the
correct way) is 1. You may use the following result without proof.
Theorem 1.5.1. There exists a unique multilinear, antisymmetric, normal functional D :
(Rn)n → R.
Using this functional D, we can define the determinant of a linear operator T : Rn → Rn
as follows.
Definition 1.5.1. Let T : Rn → Rn be a linear map. We define the determinant of T to
be
det T := D(T e1, . . . , T en)
where e1, . . . , en is the standard basis of Rn.
The determinant enjoys many nice properties. Below, we have listed some of these
properties which you may assume without proof.
Proposition 1.5.1. The determinant satisfies the following properties.
(i) If S, T: Rn → Rn are two linear operators, then det( S ◦ T ) = (det S)(det T ).
(ii) If λ ∈ R and T : Rn → Rn, then det( λT ) = λn det(T ).
(iii) det( I) = 1 where I : Rn → Rn is the identity map.
Closely related to the determinant is the group of permutations Sn that consist of
all bijective maps π : [n] → [n]. In the following problem, you will consider special maps
χ : Sn → {−1, 1}.
Problem 1.13 (30 points) . We call a map χ : Sn → {−1, 1} a character (of Sn) if
χ(π1 ◦ π2) = χ(π1) · χ(π2) for all π1, π2 ∈ Sn. Prove that there are exactly two characters
of Sn when n ≥ 2.
From the previous problem, we know that Sn, when n ≥ 2, has two characters which we
denote by 1Sn and sgn. The former is simply the map which sends every permutation to 1
and the latter is the sign representation of Sn which sends transpositions (permutations
which simply swap two elements) to −1. When n = 1, it is easy to see that there is only one
character 1Sn. In that case, we will let sgn = 1Sn. The sgn character gives us the following
explicit formula for the determinant of a linear map.
Proposition 1.5.2. If [aij] is the matrix for a linear map T : Rn → Rn, then
det T :=
X
π∈Sn
sgn(π)
nY
i=1
aiπ(i).
14
In the right hand side, we are picking n terms entries in the matrix which are all in
distinct rows and columns and multiplying them together. Then we are adding all of these
products while weighting them based on the sign of our permutation.
Problem 1.14 (Computing Determinants, 30 points). In this exercise, you will compute a
few determinants.
(a) (5 points) Compute the determinant of


1 2 3
4 5 6
7 8 9

.
(b) (10 points) Let v1, . . . , vn be a collection of linearly dependent vectors. Compute
D(v1, . . . , vn).
(c) (15 points) Let v1, . . . , vn be an orthonormal basis of Rn. Compute |D(v1, . . . , vn)|.
In Problem 2.13(c), you will prove that the determinant is indeed the volume of the
parallelotope spanned by the n column vectors. For the final concept in this subsection, we
define a minor of a matrix.
Definition 1.5.2. Let M be a matrix, not necessarily square. We define a minor of the
matrix M to be the determinant of some smaller square matrix which we obtain by deleting
rows and columns.
To give an example, consider the matrix
A =
1 2 3
4 5 6

.
The minors of A will be the determinants of the following matrices
1 2
4 5

,
1 3
4 6

,
2 3
5 6

and each individual entry in A.
Definition 1.5.3. Let M be a matrix. We say M is unimodular if all of its minors are
in {−1, 0, 1}.
The next time Definition 1.5.3 will reppear is at Section 5.2. Thus, you do not need to
concern yourself with the definition at the moment.
1.6 Metric Spaces
In this section, we introduce the notion of a topology. A topology is gives us a way to
characterize sets of points which are close together. We will only be interested in topologies
which can be induced by a metric. With a metric, we can begin talking about continuity
and convergence.
Definition 1.6.1. A metric space is an ordered pair ( X, d) of a set X and a metric
d : X × X → R which satisfies
(i) d(x, y) ≥ 0 for all x, y∈ X and d(x, y) = 0 if and only if x = y.
15
(ii) d(x, y) = d(y, x) for all x, y,∈ X.
(iii) d(x, y) + d(y, z) ≥ d(x, z) for all x, y, z∈ X.
From the definition, we can see that a metric space includes two components: a set
of points X and a function d called the metric. The metric d should be thought of a
measurement of distance between points. Definition 1.6.1(iii) then asserts that the triangle
inequality holds.
Example 1.6.1. On any set X, we can equip it with the discrete metric 1 : X ×X → {0, 1}
defined by 1(x, y) = 1 if x ̸= y and 1(x, y) = 0 otherwise.
Example 1.6.2. The pair ( Rn, d2) where d2(x, y) = ∥x − y∥ is the Euclidean norm is a
metric space. More generally, ( Rn, dp) where
dp(x, y) =
( nX
k=1
|xi − yi|p
)1/p
and p ≥ 1 is a metric space. When p = 1 and n = 1, we get the common metric space
(R, | · |). This formalizes the notion of the absolute value being a measure of distance in the
real numbers.
1.7 A Brief Detour: Supremum and Infimum
Before introducing more topological notions, we first introduce a property of many ordered
sets which generalizes the idea of a maximum and minimum. This concept will be used
regularly in later sections of the power round.
Definition 1.7.1. Suppose E ⊂ R is bounded above. If a real number α ∈ R satisfies the
properties that
(i) α is an upper bound of E
(ii) if α0 is an upper bound of E, then α0 ≥ α
then, we call α a supremum of A. Similarly, we call β an infimum of E if E is bounded
below and −β is a supremum of −E. Let sup E denote the set of suprema and inf E denote
the set of infima.
Problem 1.15 (5 points) . Prove that for any subset E ⊂ R, if suprema or infima exist
they must be unique.
It turns out that any subset of real numbers with an upper bound also has a well-
defined supremum and any subset of real numbers with a lower bound also has a well-
defined infimum. You may take this fact for granted. This allows us to make the following
definition.
Definition 1.7.2. Let A ⊂ R be a subset of the reals. We define the sup A to be the
supremum of A if A is bounded above and inf A to be the infimum of A if A is bounded
below. If A is not bounded above we let sup A = +∞. Similarly, if A is not bounded below,
we let inf A = −∞.
16
The supremum and infimum are generalizations of maximum and minimum to infinite
sets. For example, the open interval (1, 2) contains no element which is larger than all of the
other elements or smaller than all of the other elements. This implies that the maximum
and minimum are undefined for this set. However, we would like to say that the “minimum”
is 1 and the “maximum” is 2. The supremum and infimum allow us to express this idea with
sup(1, 2) = 2 and inf(1, 2) = 1. For another example, consider the set of increasingly precise
decimal approximations of
√
2: {1, 1.4, 1.41, 1.414, 1.4142, ...}. This set has no maximum
but it has supremum
√
2. In the following problem, you will prove an important analytic
property of the supremum and infimum. We only state the result for supremum, but the
corresponding result for infimum can be easily deduced.
Problem 1.16 (5 points) . Let A ⊂ R be a subset with α = sup A <∞. Prove that for
every ε >0, there exists an element β ∈ A such that β > α− ε.
However, in most applications, the supremum fulfills a similar role to the maximum. The
following problem uses both, but the you may find that there is little difference between
the supremum and the maximum in this example.
Problem 1.17 (15 points). In probability theory, there is a useful metric on the distribu-
tions of a fixed sample space called the total variation distance . In this problem, we
explore a simple case of this distance. Consider the simplex
∆d := {(x1, ..., xd) ∈ Rd : x1 + ... + xd = 1 and x1, ..., xd ≥ 0}.
We define the total variation distance between two vectors x, y∈ ∆d to be
dTV(x, y) = 1
2
dX
k=1
|xk − yk|.
(a) (5 points) Prove that dTV is a metric.
(b) (10 points) Prove that
dTV(x, y) = max
A⊂[d]

X
n∈A
(xn − yn)
 = 1
2 sup
( dX
k=1
fk(xk − yk) : max
i∈[d]
|fi| ≤1
)
Now back to the regularly scheduled programming.
1.8 Topology of Metric Spaces
Definition 1.8.1. Let ( X, d) be a metric space. For r > 0, we can define the following
subsets of X:
B0(x, r) = {y ∈ X : d(x, y) < r}
B(x, r) = {y ∈ X : d(x, y) ≤ r}
S(x, r) = {y ∈ X : d(x, y) = r}.
When the underlying metric space is understood to be ( Rn, ∥·∥), we let Bn := B(0, 1) and
Sn−1 := S(0, 1).
17
Geometrically, B0(x, r) is the open ball of radius r and S(x, r) is the sphere of radius
r. The difference between B(x, r) and B0(x, r) is that the former includes points which are
exactly a distance of r away while the latter does not. If we consider R2 equipped with the
standard Euclidean metric, the open ball centered around 0 with radius 1 would be a unit
disk without boundary. However, if we change the metric, to say for example the taxicab
metric, open balls would be a different shape.
Problem 1.18 (5 points). On R2, define the taxicab distance as dT (x, y) = |x1 − y1| +
|x2 −y2|. Describe or draw the shape of open balls of the taxicab distance. A picture suffices
for this problem.
In a metric space, the open balls generate a topology. It is not necessary for the power
round for you to understand what this means, but morally it means that we have a means
to understand continuity and convergence. In the following definitions, all terms apply to
some metric space ( X, d).
Definition 1.8.2. We call a subset S ⊂ X an open set if and only if for each s ∈ S, there
is a positive radius r >0 such that B0(s, r) ⊂ S. Trivially, the empty set and the whole set
are always open. We call a subset S ⊂ X a closed set if the complement Sc is open.
Definition 1.8.3. Let S ⊂ X be a subset of our metric space.
(i) The interior of S, denoted by int(S), is the set of points p ∈ S such that there exists
an open ball containing p and contained in S.
(ii) The boundary of S, denoted by ∂S , is the set of points p ∈ X such that any open
ball centered around p contains at least one point of S\{p} and at least one point in
Sc.
(iii) The closure of S, denoted by clo(S), is defined as the union of S and boundary of S.
Remark 1.8.1. Suppose ( X, d) is a metric space. Then, any subset S ⊂ X when equipped
with the metric d also becomes a metric space. Hence, for subsets E ⊂ S, we can consider
the interior, boundary, and closure of E relative to S. This means that instead of viewing
E as a subset of the metric space ( X, d), we are viewing E as a subset of the metric space
(S, d). This will give drastically different sets for the interior, boundary, and closure. Thus,
we will denote by intS(E), ∂SE, and cloS(E) as the interior, boundary, and closure relative
to S.
Figure 3: x is an interior point while y is a boundary point.
18
Problem 1.19 (10 points) . Let X = R3 and consider the subset K = {(x, y, z) ∈ R3 :
0 ≤ x, y≤ 1, z= 0 }. Let P = {(x, y, z) ∈ R3 : z = 0 }. Please answer the following two
questions. No proof of your answers are required.
(a) (5 points) What are int K, ∂K , and clo K?
(b) (5 points) What are int P K, ∂P K, and clo P K?
For nice shapes in Euclidean space, the interior, boundary, and closure are exactly what
you would imagine them to be. For example, the interior of an open disk would be itself.
The boundary would be the circle bounding the disk. The closure would be the closed
disk. However, for more irregular shapes it might be wise to rely less on your intuition.
The following is an alternative characterization of the closure and interior which you do not
need to prove.
Proposition 1.8.1 (Alternative Characterization of Interior and Closure) . Let E ⊂ X be
a subset. Prove that int E is the largest open set contained in E and clo E is the smallest
closed set containing E. In other words, prove that int E is open, clo E is closed, and
whenever O ⊂ E is open and C ⊃ E is closed, then
O ⊂ int E ⊂ E ⊂ clo E ⊂ C.
One way to construct metric spaces is to build them up from smaller ones. In particular,
if (X, dX ) and (Y, dY ) are metric spaces, we can construct a metric space ( X × Y, d) where
the metric is defined by
d(x1 × y1, x2 × y2) =
p
dX (x1, x2)2 + dY (y1, y2)2.
We leave it as an exercise to prove that this is indeed a metric. Note that the metric space
(Rn, ∥·∥) is constructed exactly in this way.
Definition 1.8.4. We say a sequence of points {an}n≥1 ⊂ X converges to a point a ∈ X
if for every ε > 0, there exists a positive constant N such that for all n > N, we have
d(an, a) < ε. We write this as an → a as n → ∞or lim n→∞ an = a. We say the sequence
{an}n≥1 is Cauchy if for every ε >0, there exists a positive constant N such that for all
m, n > N, we have d(an, am) < ε.
Definition 1.8.4 is a formalization of the idea a sequence of points getting “close” to
a limit. Not only do our points need to get arbitrarily close to the limit, but they have
to eventually stay arbitrarily close as well. A Cauchy sequence is similar to a convergent
sequence, except we are only guarenteed that our sequence gets (and eventually stays)
arbitrarily close to itself. Convergent sequences are always Cauchy sequences, but the
converse is not necessarily true. Indeed, see if you can find a sequence in the rationals Q
that is Cauchy but not convergent. However, in many spaces that we work with, the two
notions are the same. The name of such spaces is given in Definition 1.8.5.
Definition 1.8.5. We call a metric space ( X, d) complete if all Cauchy sequences in X
converge.
Problem 1.20 (30 points) . The following two problems involve the convergence of se-
quences.
19
(a) (10 points) Prove that every convergent sequence has a unique point of convergence.
That is, if an → x1 and an → x2 are two convergent sequences in a metric space
(X, d), then x1 = x2.
(b) (20 points) Let ( X, d) be a complete metric space. Let f : X → X be a map satisfying
d(f (x), f(y)) ≤ c · d(x, y) where c ∈ (0, 1). Prove that there exists exactly one xfix ∈ X
with f (xfix) = xfix.
The next definition is a topological generalization of finiteness and will be particularly
important for the remainder of the power round.
Definition 1.8.6. A subset K ⊂ X is compact if for any collection of open sets {Uα}α∈I
satisfying
K ⊂
[
α∈I
Uα
there exists a finite subset S ⊂ I with
K ⊂
[
α∈S
Uα.
Written succinctly, every open cover of K has a finite subcover.
Whenever we are in Rn, the open covers in Definition 1.8.6 can be avoided with the
following characterization of compact sets. You may assume the result without proof.
Theorem 1.8.1. A subset K ⊂ Rn is compact if and only if K is closed and bounded.
In a metric space (X, d), we say that a subset K ⊂ Rn is bounded if there exists r ∈ R>0
and x ∈ X such that K ⊂ B(x, r). In other words, there exists a ball of finite radius which
covers the set. Another result about compact sets is that given any open cover, any small
enough subset will be contained in a single open set in the open cover. We summarize this
result in the following theorem.
Theorem 1.8.2. Let A be an open covering of the metric space ( X, d). If X is compact,
there is a δ >0 such that for every subset of X having diameter less than δ, there exists an
element of A containing it. Recall that the diameter of the subset E is defined as
diam E := sup
x,y∈E
d(x, y).
We now consider the maps between metric spaces which preserve their topology.
Definition 1.8.7. Given metric spaces ( X, dX ) and ( Y, dY ), we call a map f : X → Y
continuous if f −1(U ) is open as a subset of X whenever U ⊂ Y is open as a subset of Y .
A continuous function is then a map f : X → R where R is equipped with the Euclidean
metric.
When given an explicit formula for a map, Definition 1.8.7 may be a bit cumbersome to
use. Luckily, we have the following ε-δ definition of continuity which in some situations is
more suited to computation. You may take this result for granted.
20
Proposition 1.8.2. A map f : (X, dX ) → (Y, dY ) between metric spaces is continuous if
and only if for any x ∈ X and ε >0, there exists a δ := δ(x, ε) > 0 dependent on both x
and ε such that for all u ∈ X, we have
dX (x, u) < δ =⇒ dY (f (x), f(u)) < ε.
In other words, we can make the value f (u) get arbitrarily close to f (x) as long as u is
sufficiently close to x.
Problem 1.21 (Exercises in Continuity and Compactness, 40 points) . Let ( X, d) be a
metric space.
(a) (10 points) Let K ⊂ X be compact and f : (X, d) → (M, dM ) be a continuous map.
Prove that f (K) is a compact subset of M .
(b) (10 points) Suppose we have a sequence of non-empty compact subsets Kn ⊂ X
satisfying Kn ⊃ Kn+1 for all n ≥ 1. Prove that T
n≥1 Kn is non-empty and compact.
(c) (10 points) Let {xn} ⊂Rn be a bounded sequence. Prove that there is a convergent
subsequence.
(d) (10 points) Let K ⊂ X be compact and f : K → R a continuous function. Prove that
there exists xmin, xmax ∈ K that satisfy
f (xmin) = inf
x∈K
f (x), f (xmax) = sup
x∈K
f (x).
21
2 Convex Bodies
2.1 Properties of Convex Sets
Definition 2.1.1. A set C ⊂ Rn is convex if for any two elements x, y∈ C, the set C
contains the segment [ x, y]. That is, for all α ∈ [0, 1], we have αx + (1 − α)y ∈ C.
A familiar class of convex sets are the affine spaces. Since an affine space A is defined
to be a space for which for any two x, y∈ A and λ ∈ R satisfies λx + (1 − λ)y ∈ A, it
is clear that affine spaces are convex. Convex sets have a construction similar to that of
Definition 1.1.3.
Definition 2.1.2. For a non-empty subset of vectors S ⊂ Rn, there exists a convex set
conv S containing S such that if C0 is a convex set containing S then conv S ⊂ C0. We call
conv S the convex hull of S.
Remark 2.1.1. By generalizing the linear combination in Definition 2.1.1, we say a vector
x ∈ Rn is a convex combination of vectors x1, ..., xm ∈ Rn if there are non-negative
constants λ1, ..., λm ∈ R≥0 satisfying
x =
mX
i=1
λixi and
mX
k=1
λk = 1.
It is not difficult to prove that conv S can be explicitly described as the set of points which
can be represented as the convex combination of a finite set of points in S. From here on
out, you may use this result as a black box.
We have finally come to the main objects that we will be working with in the power
round. We will not be working with sets that are only convex. Instead, we will be working
with sets that are convex and compact.
Definition 2.1.3. A convex body is a non-empty convex and compact subset of Rn for
some n ≥ 1. We let Kn denote the family of convex bodies in Rn. For K ∈ Kn we can define
the dimension of K as dim K := dim aff K.
Problem 2.1 (10 points). If K ∈ Kn, prove that dim K < nif and only if int K = ∅.
Problem 2.1 shows that there are a large class of non-trivial convex bodies in Rn with
empty interior. This makes topologically distinguishing convex objects tricky. For example,
consider a closed square. In R2 it has non-empty interior but in R3 it has empty interior.
Thus, to study the structure of convex bodies, we need the following refined notion of
interior and boundary.
Definition 2.1.4. Let K ⊂ Rn be a convex body. Define
relint K = intaff K K
relbd K = ∂aff KK
where we take the interior and boundary while taking aff K to be the ambient space.
Problem 2.2 (15 points). Let K ⊂ Rn be a convex body. Let x ∈ relint K and y ∈ K be
arbitrary points. Prove that (1 − λ)x + λy ∈ relint K for all λ ∈ [0, 1).
22
A related concept to convex sets is cones. Formally, we define aconvex cone (or simply
cone) to be a subset A ⊂ Rn such that for all a ∈ A and λ ≥ 0, we have λa ∈ A. In other
words, by taking any point in the set, the positive scalar multiples of this point will lie in
our cone. For any subset S ⊂ Rn, we can then define
pos S =
( mX
i=1
λixi : λi ≥ 0, xi ∈ S
)
to be the conic hull or positive hull of the set S. In the next problem, you prove that
the space of convex bodies when equipped with set addition and scalar multiplication form
a vector space.
Problem 2.3 (15 points). Let K, L∈ Kn and let a ∈ R be a real number. Prove that a · K
and K + L are both in Kn.
By requiring our convex sets to compact, we give ourselves powerful tools to analyze the
geometry of convex bodies. These tools are projection and separation. Projection allows
us to find the (unique) shortest point from a given point to the convex body. Separation in
general is a useful property.
Problem 2.4 (15 points). For x ∈ Rn and a closed convex subset K ⊂ Rn, let
dist(x, K) := inf
y∈K
∥x − y∥
be the distance of x from K. Prove that there exists a unique x∗ ∈ K with ∥x − x∗∥ =
dist(x, K).
The previous problem allows us to make the following definition.
Definition 2.1.5. For a convex body K ⊂ Rn and x ∈ Rn, define π(K, x) or πK(x) to be
the unique element of K satisfying
∥x − πK(x)∥ = dist(x, K).
We call πK(x) the projection of x onto to K.
Problem 2.5 (Exercises on the Projection Operator, 30 points) . Let K ⊂ Rn be a closed
convex subset and x, y∈ Rn be arbitrary points.
(a) (5 points) Prove that πK(x) = x if and only if x ∈ K.
(b) (10 points) Prove that y = πK(x) if and only if ⟨x − y, z− y⟩ ≤0 for all z ∈ K.
Geometrically, the condition on the right says that the angle between the segment xy
and yz is obtuse for all z ∈ K.
(c) (15 points) Prove that πK(·) is 1-Lipschitz. That is, prove that for any x, y∈ Rn, the
following inequality holds:
∥πK(x) − πK(y)∥ ≤ ∥x − y∥ .
23
A hyperplane through the origin H ⊂ Rn is defined to be the set of vectors which
are perpendicular to a fixed vector. A general hyperplane H ⊂ Rn is a translation of
a hyperplane through the origin and can be specified by two parameters: a vector and a
scalar. Specifically, suppose we specify α ∈ R and v ∈ Rn\{0}. Then we can define the
hyperplane
Hv,α = {x ∈ Rn : ⟨x, v⟩ = α}.
In R3, Hv,α would be the plane which passes through αv
⟨v,v⟩ and perpendicular to v. The
hyperplane Hv,α also has a nice interpretation in terms of linear functionals. Define the
linear functional φv : Rn → R by
φv(u) = ⟨u, v⟩.
Then Hv,u is simply the dimension n − 1 affine space
Hv,u := αv
⟨v, v⟩ + kerφv.
Every hyperplane Hv,α partitions Rn into two closed half-spaces given by:
H +
v,α = {x ∈ Rn : ⟨x, v⟩ ≥α}
H −
v,α = {x ∈ Rn : ⟨x, v⟩ ≤α}.
Definition 2.1.6. Let A, B⊂ Rn be two subsets. We say H = Hv,α separates A and B if
⟨a, v⟩ ≥α ≥ ⟨b, v⟩ or ⟨a, v⟩ ≤α ≤ ⟨b, v⟩
for all a ∈ A, b∈ B. We say H strongly separates A and B if there exists ε >0 such
that
⟨a, v⟩ + ε < α <⟨b, v⟩ −ε or ⟨a, v⟩ −ε > α >⟨b, v⟩ + ε
for all a ∈ A, b∈ B.
Geometrically, a hyperplane separates two subsets of Rn if the two subsets are on dif-
ferent sides of the hyperplane. Strong separation is the stronger notion that we are able to
“thicken” our hyperplane by ε while still separating both of the subsets.
Figure 4: Separating hyperplane between C and x
Definition 2.1.7. Let K ⊂ Rn be a convex body and H a hyperplane. If H ∩ K ̸= ∅ and
K ⊂ H + or K ⊂ H −, we call H a supporting hyperplane of K and the corresponding
half-space containing K a supporting half-space .
In the following problem, you will prove that you can always (strongly) separate a point
outside of closed convex subset from the closed convex subset.
24
Problem 2.6 (30 points). In this problem, you will prove two separation results.
(a) (10 points) Let K ⊂ Rn be closed and convex. Let x ∈ Rn be an arbitrary point not
contained in K. Prove that there is a hyperplane H which strongly separates x and
K.
(b) (20 points) Let C ⊂ Rn be a non-empty closed convex set. For each x ∈ ∂C , there is
a hyperplane H such that C ⊂ H − and x ∈ C ∩ H.
If we are only intersected in separation, then we have the following result which you
may assume without proof.
Theorem 2.1.1. Let K, L⊂ Rd be non-empty convex sets satisfying relintK ∩relint L = ∅.
Then we can separate K and L.
2.2 Facial Structure of Convex Bodies
In Definition 2.2.1, we define an important function that allows us to describe the geometry
of a convex body.
Definition 2.2.1. For any subset K ⊂ Rn, define the height function hK : Sn−1 → R
defined by
hK(u) = sup
x∈K
⟨x, u⟩.
Geometrically, the value hK(u) is the distance of the furthest point on K in the direction
of u.
Problem 2.7 (20 points). Let K ∈ Kn body and u ∈ Sn−1.
(a) (5 points) Show that there exists x ∈ K such that ⟨x, u⟩ = hK(u).
(b) (5 points) Prove that H = {x ∈ Rn : ⟨x, u⟩ = hK(u)} is a supporting hyperplane of
K.
(c) (10 points) If K, Lare convex bodies and a >0, then haL+K(u) = ahL(u) + hK(u)
for all u ∈ Sn−1.
We now want to formalize the notion of a “face” of a convex body. Consider the case of
a solid cube [0, 1]3 ⊂ R3. The common knowledge about the cube is that there are six faces:
the six squares. These faces can be viewed as the points which are the furthest in one of the
following six directions: ( ±1, 0, 0), (0, ±1, 0), and (0, 0, ±1). This motivates Definition 2.2.2.
Definition 2.2.2. For any subset K ⊂ Rn, we define a face of K to be the intersection of
K with any supporting hyperplane. For 0 ≤ k ≤ dim K, a k-face is a face of dimension k.
We call a face of K a facet if it has dimension dim K − 1. By convention, we let K be a
dim K face of K even if there is not necessarily a supporting hyperplane which makes it so.
Define the face of K in the direction of u ∈ Sn−1 as
F (K, u) := FK(u) := {x ∈ K : ⟨x, u⟩ = hK(u)}.
Note that from Definition 2.2.2 the cube has more than the six faces described. The
faces described consist of all the facets, but all of the “edges” and “vertices” will also be
faces as well. From Problem 2.7, it is not difficult to prove Proposition 2.2.1. You may take
this result for granted.
25
Proposition 2.2.1. Let K1, . . . , Km ⊂ Rn be convex bodies and α1, . . . , αm > 0. Let
K = α1K1 + . . .+ αmKm. Then
F (K, u) =
nX
k=1
αiF (Ki, u).
Definition 2.2.3. For a convex body K ⊂ Rn, a point v ∈ K is called a vertex of K if
1
2 (y + z) = v for y, z∈ K implies that y = z = v. We denote the set of vertices of K as
v(K).
The set of vertices v(K) contains all the information we need to determine K. This is
summarized by Theorem 2.2.1 which you may take for granted.
Theorem 2.2.1. Let K ∈ Kn. Then K = conv v(K).
Problem 2.8 will imply that you do not need too many of the vertices to specify an
arbitrary point in your convex body.
Problem 2.8 (15 points). Let S ⊂ Rn be an arbitrary subset of vectors. Let x ∈ conv S.
Prove that x can be written as a convex combination of at most n + 1 elements in S.
2.3 Polytopes and Polyhedra
In this section, we consider two special classes of convex sets: polytopes and polyhedra.
These are higher-dimensional generalizations of polygons.
Definition 2.3.1. A polytope is a convex hull of a finite number of points. A polyhedra
is the intersection of a finite number of closed half-spaces. Let Pn denote the family of
polytopes in Rn.
In general, the set of polytopes and polyhedra are not equivalent. Indeed, polytopes are
necessarily bounded while polyhedra may not be. However, in Problem 2.10 you will show
that the two concepts are equivalent if we assume boundedness. To aid you in the proof,
we introduce a useful duality tool to go from polytopes to polyhedra and vice versa.
Definition 2.3.2. If K is a convex body, define the dual of K as
K◦ := {x ∈ Rn : ⟨x, p⟩ ≤1 for all p ∈ K}.
Problem 2.9 (20 points). Let K be a convex body with 0 ∈ int K.
(a) (10 points) Prove that K◦ is a convex body with 0 ∈ int K◦.
(b) (10 points) Prove that K = K◦◦.
In other words, ·◦ is a notion of duality on the convex bodies containing 0 in their interior.
Problem 2.10 (40 points). Let K ⊂ Rn be bounded. In this problem you will prove that
K is a polyhedron if and only if it is a polytope.
(a) (15 points) Suppose that K = Tm
i=1 H −
ni,αi is a polyhedron where H −
ni,αi = {x ∈ Rn :
⟨x, ni⟩ ≤αi}. For x ∈ K, define ind(x) = {i ∈ [m] : ⟨x, ni⟩ = αi} to be the indices of
the hyperplanes that contain x. Prove that if x ∈ v(K) then lin i∈ind(x){ni} = Rn.
26
(b) (10 points) Prove that the number of vertices is finite and conclude that bounded
polyhedra are polytopes.
(c) (15 points) Suppose that K = conv{x1, ..., xm} ⊂Rn is a polytope. Prove that
K◦ = {x ∈ Rn : ⟨x, xj⟩ ≤1 for 1 ≤ j ≤ m}.
Conclude that polytopes are polyhedra.
2.4 More on the Facial Structure of Convex Bodies
You may have noticed that there is a discrepancy between the notion of a face and a vertex.
We defined a face as the intersection of our convex body with a supporting hyperplane.
Thus, faces are defined from the “outside” of the convex body. On the other hand, we
defined vertices from the “inside” by letting them be the points which cannot be written as
a non-trivial convex combination of points in our convex body. If we were to try to define
faces more intrinsically, we would make the following formal definition.
Definition 2.4.1. Let K ∈ Kn. A closed, convex set F ⊂ K is called a feature of K
if whenever y, z∈ K and 1
2 (y + z) ∈ F then y, z∈ F . When k = dim F , we call F a
k-feature. In particular, vertices are 0-features. We let Fi := Fi(K) for 0 ≤ i ≤ dim K be
the collection of i-features of K.
Faces are clearly features, but features are not necessarily faces. Figure 5 demonstrates
why this is the case. The labelled point is a vertex (0-feature) but not a 0-face. Thus
the result Problem 2.8 would not hold if we replaced v(K) with the set of 0-faces. Hence,
features are better than faces at representing information about our convex bodies. Indeed,
in the following problem, you will prove that our convex bodies can be partitioned into the
relative interiors of our faces.
Figure 5: The top two dotted points are 0-features but not 0 faces
Problem 2.11 (15 points). Let F be the collection of all of the features of K. Prove that
K =
G
F ∈F
relint(F ).
where the union is disjoint.
In the case of polytopes, it turns out that features and faces are the exact same concept!
This result, along with many other useful properties of features and facets of polytopes, is
summarized in Proposition 2.4.1. You may take these results for granted.
27
Proposition 2.4.1. Let P = conv{x1, ..., xm} be a polytope in Rn.
(a) If F is a face of P , 
...[truncated]
