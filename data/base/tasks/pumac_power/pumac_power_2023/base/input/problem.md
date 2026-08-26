# PUMaC Power Round 2023

PUMaC 2022* Power Round:
The PID Structure Theorem
Frank Lu
Spring 2023
Rules and Reminders
1. Your solutions should be turned in by 12PM Thursday , March 30th, EDT. You
will submit the solutions through Gradescope. The instructions describing how to log
into Gradescope will be sent to the coaches. The deadline for submission is clearly
visible on the Gradescope site once you enroll in the course.
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
2. You are encouraged, but not required, to use L ATEX to write your solutions. If you
submit your power round electronically, you may submit several times, but only
your final submission will be graded (moreover, you may not submit any work
after the deadline). The last version of the power round solutions that we receive from
your team will be graded. Moreover, you must submit a PDF . No other file type
will be graded. For those new and interested in L ATEX, check out Overleaf as well as
its online guides. If you do not know the specific command for a math symbol, check
out Detexify or TeX.StackExchange.
3. Do not include identifying information aside from your team number in your solutions.
4. Please collate the solutions in order in your submission. Each problem should start
on a new page (there is a point deduction for not following this formatting).
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
In this power round, we state and prove the PID Structure Theorem , before de-
scribing a few applications of this theorem. This theorem states that certain examples of a
structure called a module satisfy nice properties. In order to state and prove the theorem,
we first need to introduce a few more structures from abstract algebra. We first study rings,
which are sets with addition and multiplication operations. This structure includes some
familiar sets, such as the set of integers and the set of rational numbers. As we introduce
new structures, we will slowly see, under certain conditions, that these structures satisfy
nice properties.
The material in this power round belongs to the field ofabstract algebra, which studies
sets equipped with operations that obey certain properties. A large part of the difficulty of
this subject arises from the abstraction and the amount of generality present (in contrast
with the computation-heavy and concrete world of high school algebra and geometry). Try
to keep in mind the examples introduced throughout the power round, and checking the
definitions and propositions against these examples. This will be useful in understanding
what each of these otherwise abstract statements are saying.
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
– Frank Lu
We would like to acknowledge and thank many individuals and organizations for their
support; without their help, this Power Round (and the entire competition) could not exist.
Please refer to the solutions of the power round for full acknowledgments and references.
Contents
1 Rings and Fields 6
1.1 Rings and Ideals . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
1.2 A Family of Rings . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
1.3 Product Rings, Quotient Rings and More Examples . . . . . . . . . . . . . 13
2 V ector Spaces 15
2.1 Definitions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
2.2 Coordinates and Bases . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
2.3 Linear Transforms . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
2.4 Matrices and Row Reduction . . . . . . . . . . . . . . . . . . . . . . . . . . 20
3 Modules 24
4 The PID Structure Theorem 27
4.1 Noetherian Rings and Modules . . . . . . . . . . . . . . . . . . . . . . . . . 27
4.2 Smith Normal Form . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 30
4.3 Proof of the PID Structure Theorem . . . . . . . . . . . . . . . . . . . . . . 32
5 Applications and Asides 32
5.1 A Counterexample . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 33
5.2 Abelian Groups . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 33
5.3 Jordan Canonical Form . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 35
Notation
• ∀: for all. Ex.: ∀x ∈ {1, 2, 3} means “for all x in the set {1, 2, 3}”
• A ⊂ B: proper subset. Ex.: {1, 2} ⊂ {1, 2, 3}, but {1, 2} ̸⊂ {1, 2}
• A ⊆ B: subset, possibly improper. ex.: {1}, {1, 2} ⊆ {1, 2}
• f : x 7→ y: f maps x to y. Ex.: if f (n) = n − 3 then f : 20 7→ 17 and f : n 7→ n − 3
are both true.
• f (C): for a function f : A → B and subset C ⊆ A, the set of elements of the form
f (c), for c ∈ C.
• {x ∈ S : C(x)}: the set of all x in the set S satisfying the condition C(x). Ex.:
{n ∈ N : √n ∈ N} is the set of perfect squares.
• N: the natural numbers, {1, 2, 3, . . .}.
• [n] = {1, 2, 3, ..., n}.
• Z: the integers.
• Q: the rational numbers.
• R: the real numbers.
• C: the complex numbers.
• |S|: the cardinality of set S.
1 Rings and Fields
In this section, our goal is to introduce some structures which generalize some of the key
features that we like from some familiar objects. The main example to motivate our dis-
cussion is the set of integers Z. In particular, we can add and subtract integers, as well as
multiply them together. It is these operations and certain nice properties that they satisfy
which we would like to capture.
1.1 Rings and Ideals
We begin with the concept of a ring, which generalizes the concept of the integers Z with
its addition and multiplication operations.
Definition 1.1.1. A ring is a set R equipped with two operations, + and ·, satisfying the
following conditions:
1. R is closed under + and · : that is, ∀r1, r2 ∈ R, r1 + r2, r1 · r2 ∈ R.
2. The operations + , · are associative: ∀r1, r2, r3 ∈ R, we have that ( r1 + r2) + r3 =
r1 + (r2 + r3), r1 · (r2 · r3) = (r1 · r2) · r3.
3. The operations + , · are commutative: ∀r1, r2 ∈ R, r1 + r2 = r2 + r1 and r1 · r2 = r2 · r1.
4. The operations + , · have identity elements: specifically, we have elements 0 , 1 ∈ R
such that 0 + r = r = 1 · r = ∀r ∈ R. We refer to 0 as the additive identity of R
and 1 as the multiplicative identity of R.
5. For each element r ∈ R, there is an element r′ ∈ R such that r +(r′) = 0. This element
r′ is the additive inverse of r; we will sometimes write r′ as −r.
6. We have the following distributive law: ∀r1, r2, r3 ∈ R, we have r1 · (r2 + r3) =
r1 · r2 + r1 · r3.
A subring of a ring R is a subset S of R that is a ring, using the same operations + , · as
R.
Remark. Sometimes we will have more than one ring that we will be concerned with. In
that case, for the sake of clarity, we will use + R and ·R to represent the addition and
multiplication operations for the ring R. In cases where which ring we are working with is
clear, for the sake of notational simplicity, we will write r1 · r2 as just r1r2.
Similarly, we will write 0 , 1 to denote the additive and multiplicative identities of our
ring, with subscripts to indicate which ring we are referring to when it isn’t clear from
context.
Example. We check that Z is a ring, using the standard addition and multiplication rules.
Note that the sum of two integers and the multiplication of two integers is also an integer.
Furthermore, we know that addition and multiplication are associative and commutative.
The additive identity is 0 and the multiplicative identity is 1 .
We observe as well that the additive inverse of an integer is its negative. Finally, we
know that addition and multiplication satisfy the distributive law.
Remark. With the above example, we can see how some of the key features of the addition
and multiplication operations in Z are captured in the above definition of a ring. It will
be useful throughout this section to think about Z when presented with a new example;
we will sometimes also explicitly relate the examples to the ring Z throughout the power
round.
In addition to the above example, Q, R, and C are all rings; you may assume that these
are rings without proof, with the standard addition and multiplication rules. When we write
one of the above symbols and refer to the corresponding ring, unless otherwise stated, the
addition and multiplication rules we are using are the standard addition and multiplication
rules.
We present an example of a ring that is not one of the above rings.
Example. We will show that Z[
√
2], the set of real numbers of the form a + b
√
2, where
a, b∈ Z, is a ring, under the normal addition and multiplication rules. We know from the
properties of addition and multiplication of real numbers that properties 2, 3, and 6 hold.
We just need to verify properties 1, 4, 5.
To show property 1, if we are given two elements r1, r2 ∈ Z[
√
2], we know by definition
that there exist integers a1, b1 and a2, b2 such that r1 = a1 + b1
√
2 and r2 = a2 + b2
√
2.
Then, we find that r1 + r2 = ( a1 + a2) + ( b1 + b2)
√
2 ∈ Z[
√
2]. Furthermore, r1r2 =
(a1 + b1
√
2)(a2 + b2
√
2) = (a1a2 + 2b1b2) + (a1b2 + a2b1)
√
2, which again lies in Z[
√
2]. This
shows the first property holds.
For property 4, note that the identity elements for addition and multiplication over R,
which are 0 and 1 , respectively, lie in Z[
√
2], and so Z[
√
2] also contains identity elements
for addition and multiplication.
Finally, for property 5, given any element r ∈ Z[
√
2], we know that it takes the form
a + b
√
2 for some integers a, b.But then the value r′ = (−a) + (−b)
√
2 also lies in Z[
√
2],
and the sum r′ + r yields 0. We have thus shown that Z[
√
2] is a ring.
Problem 1.1.1. Here are some more examples, and a non-example, of rings:
1. Show that 2 Z, the set of even integers, is not a ring. (Hint: which property does
it fail? In general, for questions of this nature, it is helpful to go through the
properties and figure out which ones are or are not satisfied).
2. Show that C[x], the set of polynomials in one variable x with complex coeffi-
cients, is a ring (under the standard addition and multiplication operations of
polynomials)
3. Show that the subset of polynomials in C[x] whose x coefficient is 0 forms a ring
(with the same addition and multiplication as for C[x]).
We also have the following example of a ring. Keep this example in mind as you go
through the rest of this section.
Problem 1.1.2. Let Z/nZ be the set of remainders of integers upon division by n,
where addition and multiplication are defined modulo n. For instance, when n = 6, we
have that 4 + 5 = 3, and 4 · 5 = 2. Prove that this is a ring.
Using the above definition of a ring, we can already prove some basic properties. For
instance, we have the following elementary proposition.
Proposition 1.1.2. Let R be a ring, with additive identity 0 and multiplicative identity 1.
1. There exists exactly one element e ∈ R so e + r = r ∀r ∈ R, namely e = 0, and there
is exactly one element i ∈ R so ir = r ∀r ∈ R, namely i = 1 . In other words, the
additive and multiplicative identity elements are unique.
2. For all r ∈ R, 0r = 0.
Proof. To prove the first property, suppose there were two elements e, e′ such that e + r =
r = e′ + r for all r ∈ R. Then, observe that e + e′ = e′, using the left equation, but
e + e′ = e′ + e = e, using the right equation. Therefore, e = e′, and there is only one
additive identity.
Similarly, suppose there were two elements i, i′ so that ir = r = i′r for all r ∈ R. Then,
we know that ii′ = i′, from the left equation, but ii′ = i′i = i from the right equation, so
again i = i′, and there is only one multiplicative identity.
To prove the second property, we observe that for each r ∈ R, 0r + 0r = (0 + 0)r = 0r.
Therefore, adding to both sides of the equation the additive inverse of 0 r yields us that
0r = 0, which is what we wanted to show.
Problem 1.1.3. Given a ring R, show that there exists an element x ∈ R such that
for all r ∈ R, r+ xr = 0. What element is this?
One of the first things we wish to generalize is the notion of divisibility inZ. In particular,
we can consider in Z subsets that are given as multiples of a given integer. We will begin
with something which captures some of the most basic properties about these sets; a more
precisely analogous concept will be introduced later.
Definition 1.1.3. An ideal of a ring R is a nonempty subset I ⊆ R such that the following
properties hold:
1. I is closed under addition. That is, for i, i′ ∈ I, we have i + i′ ∈ I.
2. For every i ∈ I and r ∈ R, we have that ri ∈ I.
A proper ideal of a ring R is an ideal I that is not equal to R itself.
Example. We show that the set of even integers is an ideal in the ring Z. To see this, recall
that the set of even integers are all the integers that can be written as 2 n, for some integer
n ∈ Z. Property 1 follows since for any r, r′ even integers, we know that there exist integers
n, n′ so r = 2n, r′ = 2n′, and so r + r′ = 2(n + n′), which is again even.
For the second property, given an even integer i, we can write it as i = 2 n for some
integer n. But then for any integer r, we have that ri = r2n = 2( nr), which is again an
even integer.
Problem 1.1.4. Show that the set of odd integers, as a subset of Z, is not an ideal.
(Hint: which property does this set not satisfy?)
Sometimes, we want to specify an ideal of R without having to explicitly list all of
the elements. In particular, we only need to specify a subset of the elements of the ideal,
knowing that our ideal satisfies the properties in the definition. For instance, note that any
ideal that contains 2 also must contain the even integers.
Indeed, note that if 2 lies in an ideal I, then so does every even integer, since each even
integer is equal to 2 times some other integer. As the even integers are an ideal, it thus
makes sense to describe the ideal of even integers as the smallest ideal that contains 2 :
that is, every other ideal containing 2 contains the even integers, and the even integers are
precisely the set of integers which are a multiple of 2 .
These notions, of each even integer being a multiple of 2 , and of the even integers being
the smallest such ideal containing 2 , motivates the notion of generators of an ideal.
Definition 1.1.4. We say that an ideal I is generated by a subset of elements S ⊂ I if
every element i ∈ I can be written in the form i =
nP
j=1
rjsj, for some positive integer n, and
elements s1, s2, . . . , sn ∈ S and r1, r2, . . . , rn ∈ R.
Similarly, given a ring R and elements s1, s2, . . . , sn, we let ⟨s1, s2, . . . , sn⟩ be the set of
elements of the form i =
nP
j=1
rjsj for elements r1, r2, . . . , rn ∈ R. We can also substitute a
set, letting ⟨S⟩ be the set of elements in R of the form i =
nP
j=1
rjsj for some positive integer
n, and elements s1, s2, . . . , sn ∈ S, r1, r2, . . . , rn ∈ R.
With the notation above, the set of even integers, 2 Z, can also be written as ⟨2⟩. Note
that the set of even integers is an ideal. This happens more generally, as follows.
Proposition 1.1.5. Given a subset S ⊂ R, the set ⟨S⟩ is an ideal.
Proof. For the first condition, suppose that we have two elements in ⟨S⟩, say i and i′.
Then, there are positive integers n, mand elements s1, s2, . . . , sn, s′
1, s′
2, . . . , s′
m ∈ S and
r1, r2, . . . , rn, r′
1, r′
2, . . . , r′
m ∈ S such that i =
nP
j=1
rjsj and i′ =
mP
j=1
r′
js′
j. Then, their sum
is equal to i + i′ =
nP
j=1
rjsj +
mP
j=1
r′
js′
j, which is of the given form. Notice that we can
further simplify this expression if we know that some of the sj and s′
j are equal, using the
distributive property.
For the second condition, given an element i in ⟨S⟩, we can write it as
nP
j=1
rjsj for some
positive integer n, s1, s2, . . . , sn ∈ S and r1, r2, . . . , rn ∈ R. But then, for each element
r ∈ R, observe that ri =
nP
j=1
rrjsj, which is also in ⟨S⟩. This finishes the proof of the
proposition.
Definition 1.1.6. We call the set ⟨S⟩ the ideal generated by S.
We now wish to generalize the notion of a prime from Z. Rather than thinking about
elements as being primes, we want to think about ideals. The main behavior we want to
capture is the fact that, given a prime number p, if ab lies in pZ, then either a or b lies in
it. Contrast this with 6 Z, for instance: 2 · 3 lies in 6 Z, but 2, 3 do not lie in 6 Z.
Definition 1.1.7. An ideal I of a ring R is said to be prime if it is a proper ideal, and
furthermore, for all a, b∈ R, ab∈ I implies that either a ∈ I or b ∈ I.
For instance, the ideal ⟨2⟩ ⊂Z is a prime ideal, since ab ∈ ⟨2⟩ if and only if ab is an
even integer; but notice that one of a, bmust be even as well.
Problem 1.1.5. Determine, with proof, all the prime ideals of C[x]. You may use,
without proof, the following theorem: any nonconstant polynomial in C[x] can be
written as a product of linear factors, and this product is unique up to the order of the
linear factors. This theorem is also known as the Fundamental Theorem of Algebra.
We finish by considering functions between rings. To do this, we have the following
definition relating functionss between sets.
Definition 1.1.8. Given a function f : S → S′, where S, S′ are sets, we say that f is
injective if f (s) = f (t) implies that s = t for any s, t∈ S.
We say that f is surjective if for all s′ ∈ S′, there exists an s ∈ S so f (s) = s′, and
bijective if it is both injective and surjective.
For instance, treating all the following as functions from R to R, the function f (x) = x3
is injective and surjective, the function g(x) = 2 x is injective but not surjective, and the
function f (x) = x3 − x is surjective but not injective. Note that the specification of the set
S′ is important: the function g(x) = 2 x is surjective when viewed as a function from R to
{x ∈ R|x >0}.
Problem 1.1.6. For each of the functions below, state whether they are injective,
surjective, both, or neither.
1. The function f (x) = |x| from the set of negative real numbers to the set of positive
real numbers.
2. The function f (x) = ex from R to R.
3. The function f (x) = sin x from [0, 2π] to [ −1, 1].
Definition 1.1.9. Given a function f : S → S′, an inverse of f is a function g : S′ → S
such that f (g(s′)) = s′ for all s′ ∈ S′, and g(f (s)) = s for all s ∈ S.
We have the following proposition, which you may assume to be true without proof.
Proposition 1.1.10. A function has an inverse if and only if it is injective and surjective.
If a function has an inverse, this inverse is unique.
We can now introduce our notion of maps (which is another word for “function”) between
rings.
Definition 1.1.11. A ring homomorphism between rings R and S is a map ϕ : R → S
such that the following holds:
1. For all r, r′ ∈ R, we have ϕ(r +R r′) = ϕ(r) +S ϕ(r′) and ϕ(r ·R r′) = ϕ(r) ·S ϕ(r′).
2. ϕ(1R) = 1S.
If this map is bijective, we say that it is a ring isomorphism, and then we say that R, S
are isomorphic.
The notion of two rings being isomorphic essentially means that two rings are the
“same;” that is, you can go from one to the other simply by relabelling the elements.
As a simple example, the function Z → Q sending n ∈ Z to itself, is a ring homomor-
phism. This is injective but not surjective. We also have a ring isomorphism ϕ from Z[
√
2]
to itself that sends a + b
√
2 to a − b
√
2. One can check that the properties of a ring homo-
morphism hold for this function: for instance, we notice that ϕ(a + b
√
2) + ϕ(c + d
√
2) =
(a + c) − (b + d)
√
2 = ϕ((a + c) + (b + d)
√
2).
1.2 A Family of Rings
We are now interested in a variety of different types of rings.
Definition 1.2.1. A field is a ring R such that every nonzero element r ∈ R has a
multiplicative inverse; that is, for each nonzero r ∈ R, there is an element s ∈ R such that
rs = 1.
For instance, Q, R, C are all fields; you may assume this fact without proof.
Problem 1.2.1. Show that the set of real numbers a + b
√
2, where a, b∈ Q, forms a
field, under the normal rules of addition and multiplication in R.
Problem 1.2.2. Show that a ring R is a field if and only if it has exactly two ideals.
Which two ideals are these? (Hint: think about the second question first. Consider the
field of rational numbers Q. What are its ideals?).
Of course, not all rings are fields, such as Z. However, Z still has some properties that
distinguish it from other rings. In particular, it is the following type of ring.
Definition 1.2.2. A integral domain is a ring R such that for any a, b∈ R, ab = 0 if
and only if one of a, bis zero.
Another example of such a ring is C[x]. One can check that the product of two polyno-
mials is zero if and only if one of the polynomials is zero.
However, not all rings are integral domains. For instance, considerZ/4Z, where addition
and multiplication are done modulo 4 . One can verify that this is a ring. Then, notice that
2 · 2 = 0, but 2 ̸= 0, so this ring is not an integral domain.
We are also interested in rings with particular finiteness properties, with regards to
ideals. This motivates the definitions below.
Definition 1.2.3. A principal ideal domain , or a PID, is an integral domain such that
every ideal can be generated by one element.
Problem 1.2.3. Show that Z is a PID. As a hint, given any ideal I of Z, consider the
smallest positive element in I, say i. Show that every element in the ideal has to be
divisible by i.
Remark. In particular, notice that this shows that the only ideals ofZ are the zero ideal (the
ideal consisting only of the element 0) and nZ, the set of elements divisible by a positive
integer n.
As another example, it turns out that for any field k, we have that k[x], the set of
polynomials with coefficients in k, is a PID. Here, we take our addition operation and
multiplication operations to be the typical addition and multiplication of two polynomials:
nX
i=1
aixi +
nX
i=1
bixi =
nX
i=1
(ai + bi)xi,
and
nX
i=1
aixi ·
nX
i=1
bixi =
2nX
j=1
nX
k=1
(akbj−k)xi,
where ai = bi = 0 for i not equal to 1 , 2, . . . , n.You may use the following theorem without
proof.
Theorem 1.2.4. Given a field k, the ring k[x] is a PID.
Besides ideals being prime, in Z we also have the notion of prime elements. There are
two properties of primes which seem familiar, but are slightly different. First, note that a
prime number cannot be decomposed into a product of two other numbers, where neither
is 1, −1. The second is that if p divides a product of positive integers, then p divides one of
the positive integers.
In Z, an element satisfies one property if and only if it satisfies the other. In general,
however, we cannot assume this. As such, we have the following definition.
Definition 1.2.5. Given a ring R, a unit is an element u ∈ R with a multiplicative inverse.
An element r ∈ R is irreducible if it cannot be written as the product of two elements
in the ring, neither of which are units, and furthermore is not a unit itself.
An element r ∈ R is prime if it is nonzero and the ideal generated by r is prime.
Example. For instance, the prime numbers in Z are prime in the sense of the above
definition. To prove this, given a prime number p, suppose that we have integers a, b∈ Z
such that ab ∈ ⟨p⟩. In other words, p divides ab. But we know by the Fundamental Theorem
of Arithmetic that this means that p appears in the prime factorization of ab, and thus of
either a or b.
The more traditional definition of a prime in Z, that a prime is divisible by only 1 or
itself, shows that all the prime numbers are irreducible as well.
However, we note that 4 is not prime: for instance, 2 · 2 lies in ⟨4⟩, but 2 does not.
Finally, we observe the only units in Z are 1, −1.
Problem 1.2.4. Show that for any integral domain R, every prime element is irre-
ducible.
Recall that we can uniquely factor integers into primes, up to ordering of the primes.
However, not all rings have this property. This suggests the following category of ring
which we’d like to consider.
Definition 1.2.6. A unique factorization domain, or UFD, is an integral domain where
every nonzero element can be uniquely written as a product of irreducible elements and a
unit, up to the order of irreducible elements and unit multiples.
For instance, Z is a UFD; this is the condition that lets us perform prime factorization,
and this factorization is unique up to ordering of the primes and choice of signs on the
primes. In fact, we can say something more general. We present the following theorem,
which you may use throughout this power round without proof.
Theorem 1.2.7. Every PID is a UFD, and in every UFD, every irreducible element is also
prime.
However, we have the following non-example of a UFD.
Problem 1.2.5. Show that the set of elements Z[√−13], of the form a + b√−13, for
a, b∈ Z, while an integral domain, is not a UFD, and therefore not a PID.
1.3 Product Rings, Quotient Rings and More Examples
In this subsection, we introduce two important constructions with regards to rings, before
proceeding with some explicit examples of rings.
Definition 1.3.1. Given two rings R and S, their product R × S is the set of pairs ( r, s),
where r ∈ R, s∈ S. We can then define the addition and multiplication operations by
(r, s) + (r′, s′) = ( r +R r′, s+S s′) and ( r, s) · (r′, s′) = ( r ·R r′, s·S s′). Recall here that
+R, ·R are the addition and multiplication operations on R, and +S, ·S are the addition and
multiplication operations on S.
Example. For instance, consider the product of the rings Z/2Z and Z/3Z. The addition
and multiplication tables for this ring are given below:
+ (0, 0) (0, 1) (0, 2) (1, 0) (1, 1) (1, 2)
(0, 0) (0, 0) (0, 1) (0, 2) (1, 0) (1, 1) (1, 2)
(0, 1) (0, 1) (0, 2) (0, 0) (1, 1) (1, 2) (1, 0)
(0, 2) (0, 2) (0, 0) (0, 1) (1, 2) (1, 0) (1, 1)
(1, 0) (1, 0) (1, 1) (1, 2) (0, 0) (0, 1) (0, 2)
(1, 1) (1, 1) (1, 2) (1, 0) (0, 1) (0, 2) (0, 0)
(1, 2) (1, 2) (1, 0) (1, 1) (0, 2) (0, 0) (0, 1)
· (0, 0) (0, 1) (0, 2) (1, 0) (1, 1) (1, 2)
(0, 0) (0, 0) (0, 0) (0, 0) (0, 0) (0, 0) (0, 0)
(0, 1) (0, 0) (0, 1) (0, 2) (0, 0) (0, 1) (0, 2)
(0, 2) (0, 0) (0, 2) (0, 1) (0, 0) (0, 2) (0, 1)
(1, 0) (0, 0) (0, 0) (0, 0) (1, 0) (1, 0) (1, 0)
(1, 1) (0, 0) (0, 1) (0, 2) (1, 0) (1, 1) (1, 2)
(1, 2) (0, 0) (0, 2) (0, 1) (1, 0) (1, 2) (1, 1)
One can show that this is a ring; for the purposes of this power round, you may assume
this to be true.
Definition 1.3.2. Given a ring R, let r ∈ R and I be an ideal of R. Let r + I be the
set of elements of the form r + i, for i ∈ I, and let R/I be the set {r + I|r ∈ R}. Then,
on this set, define the sum as ( r1 + I) + (r2 + I) = ( r1 + r2) + I and the product as
(r1 + I) · (r2 + I) = r1r2 + I.
Example. For instance, consider the ring Z. Note that 3 Z is an ideal. Then,
0 + 3Z = {0, 3, −3, 6, −6, . . .},
and similarly 1 + 3Z = {1, 4, −2, 7, −5, . . .} and 2 + 3Z = {2, 5, −1, 8, −4, . . .}.
First, we need to verify that these operations are well-defined: that is, if we pick a
different choice of r′ such that r′ + I = r + I, then the result of the operation should still
be the same. In particular, notice that for any i ∈ I, r+ I = (r + i) + I.
Problem 1.3.1. Prove that the operations are well-defined. That is, if r′
1 + I = r1 + I
and r′
2 + I = r2 + I, then
(r1 + I) + (r2 + I) = (r′
1 + I) + (r′
2 + I)
and
(r1 + I) · (r2 + I) = (r′
1 + I) · (r′
2 + I).
Remark. Note that it is important that we check that this operation is well-defined. Some-
times we want to define an operation that has certain nice properties. However, it is not
always clear that such an operation exists. In particular, we should expect to get the same
result if we apply the same input, regardless of how we describe that input.
As a non-example, note that the “numerator” of a rational number is not well-defined.
The number 0 .5 could have numerator 1 (from the fraction 1 /2), or numerator 8 (from
8/16). This is a problem, since then this function is not actually a function of the number
itself, but rather how we write it. Similarly, we need to check in the above problem that
our operations are actually operations that depend only on the sets r + I, not on which r
we used to represent it.
Now, we claim that this is a ring.
Problem 1.3.2. Prove that R/I is a ring, equipped with the operations we defined
above.
We call this ring a quotient ring of R. For instance, the set of residues (mod m), for any
positive integer m, is a quotient ring, given by Z/⟨m⟩. One can show that Z/mZ can be
thought of as the quotient of Z by the ideal mZ = ⟨m⟩, explaining the notation. You may
use this fact without proof throughout the rest of the power round.
We now aim to prove the following theorem.
Problem 1.3.3. Let R be a ring, and let I1, I2 be two ideals of R, such that I1 + I2 =
{i1 + i2|i1 ∈ I1, i2 ∈ I2} = R.
1. Show that I1 ∩ I2 is an ideal.
2. Consider the homomorphism from R/(I1 ∩ I2) to ( R/I1) × (R/I2) that sends
r + I1 ∩ I2 to ( r + I1, r+ I2). Show that this map is well-defined and indeed a
homomorphism.
3. Prove that the above map is injective.
4. Prove that the above map is surjective. As a suggestion on where to start, try
considering any pair ( r1 + I1, r2 + I2), and the fact that 1 ∈ R = I1 + I2.
This is known as the Chinese Remainder Theorem for rings. This is related to the case
of Chinese Remainder Theorem for the integers.
Problem 1.3.4. Using the previous problem, derive the Chinese Remainder Theorem
for integers. Namely, show that, given relatively prime integers m, n,show that given
residues r1 (mod m) and r2 (mod n), there exists a unique residue r (mod mn) so
r ≡ r1 (mod m) and r ≡ r2 (mod n).
2 Vector Spaces
We now foray into a brief introduction into the subject of linear algebra, and the study of
vector spaces. As we shall see, these structures are comparatively easy to classify.
2.1 Definitions
We begin by introducing our object of study.
Definition 2.1.1. Given a field k, a vector space V over the field k is a set of elements,
which we call vectors, equipped with two operations, addition + : V × V → V and scalar
multiplication · : k × V → V, satisfying the following properties:
1. V is closed under + and · : that is, ∀v1, v2 ∈ V, v1 + v2 ∈ V, and for all s ∈ k, v∈ V,
we have s · v ∈ V.
2. The operations + , · are associative: ∀v1, v2, v3 ∈ V, we have that ( v1 + v2) + v3 =
v1 + (v2 + v3), and for s1, s2 ∈ k and v ∈ V, we have s1 · (s2 · v) = (s1 ·k s2) · v.
3. The operation + is commutative.
4. The operation + has an identity element, which we denote as 0 .
5. Each element v ∈ V has an additive inverse.
6. For all v ∈ V, 1k · v = v.
7. We have the following distributive laws: ∀s ∈ k and v1, v2 ∈ V, we have s · (v1 + v2) =
s · v1 + s · v2, and for all s1, s2 ∈ k and v ∈ V, we have (s1 + s2) · v = s1 · v + s2 · v.
Again, we sometimes omit the multiplication dot, and add subscripts to the operations
as needed; the same convention will apply to other structures as well (when we introduce
modules in the next section).
We also say that V in this case is an k−vector space. A subspace of V is a subset U
that is also a vector space under the same operations as that of V.
Example. Consider the set of (x1, x2, . . . , xn) of real numbers. We equip it with coordinate-
wise addition and scalar multiplication, by (x1, x2, . . . , xn) + (y1, y2, . . . , yn) = (x1 + y1, x2 +
y2, . . . , xn + yn) and r · (x1, x2, . . . , xn) = ( rx1, rx2, . . . , rxn). We show that this forms a
vector space over R. We first observe that for tuples (x1, x2, . . . , xn) and (y1, y2, . . . , yn), we
have that their sum is (x1 +y1, x2 +y2, . . . , xn +yn) is also a tuple of real numbers (as the real
numbers are closed under addition). Similarly, given r ∈ R and a tuple ( x1, x2, . . . , xn), we
have that r · (x1, x2, . . . , xn) = (rx1, rx2, . . . , rxn) is a tuple of real numbers (real numbers
are closed under addition).
The commutativity, associativity, and distributivity properties are given from those of
addition and multiplication over R. Indeed, from the fact that these operations are defined
on each coordinate, properties 2, 3, 7 hold if they hold for each coordinate, which is the
case because these properties hold for R.
To show identity element, we note that (0, 0, . . . ,0) is the identity element (since adding
this to any tuple doesn’t change any of the coordinates), and we observe that negating
each of the entries of any tuple yields its additive inverse. Finally, property 6 follows since
1 · (x1, x2, . . . , xn) = (1 · x1, 1 · x2, . . . ,1 · xn) = (x1, x2, . . . , xn). This gives us that this is a
vector space.
We denote the vector space above as Rn. By the same reasoning, we have that Qn, Cn
(defined analogously) are vector spaces (and more generally kn for any field k) for n ∈ N.
Here are some other examples of vector spaces.
Problem 2.1.1. Prove the following spaces are vector spaces.
1. The set of polynomials with complex coefficients (with the standard addition and
multiplication operations), over the field C.
2. R, (with standard addition and multiplication operations), over the field Q.
Here’s an interesting non-example.
Problem 2.1.2. Determine all possible fields k such that Z can be made into a vector
space over k, using the standard addition operations. In particular, you’ll need to
consider all possible scalar multiplication operations.
2.2 Coordinates and Bases
Throughout this section, we will fix a vector space V over a field k.
Definition 2.2.1. A linear combination of v1, v2, . . . , vn ∈ V is an expression of the form
nP
i=1
sivi, where si ∈ k. By convention we say that we can take n = 0; in this case this is an
empty sum, which we set to equal zero.
A spanning set is a set S such that every element can be written as a linear combination
of some finite subset of S. We say that a module is finite dimensional if it has a finite
spanning set, and infinite dimensional otherwise.
A set of elements of M is linearly independent if, for every finite subset of M, the
only linear combination of these elements that equals zero is the linear combination where
all of the coefficients si are 0. Notice that if M is finite then it suffices to check the above
condition at the set M. By convention we say that the empty set is a linearly independent
set.
A set of elements of V is said to be a basis if it is linearly independent and a spanning
set.
Example. For instance, in the space of polynomials of degree at most 2 with coefficients
in C, the polynomials 1 , x, x2 are a basis. Indeed, they are linearly independent, since if
a + bx + cx2 = 0 as polynomials, where a, b, c∈ C, then a = b = c = 0. Furthermore, every
polynomial of degree at most 2 , by definition, can be written in the form a + bx + cx2, and
so these elements 1 , x, x2 are a basis.
As another example, note that 1 +x, x2, 2x2 + x + 1 is not a basis, since they are linearly
dependent. Indeed, 2 x2 + x + 1 + (−2)x2 + (−1)(x + 1) = 0.
Problem 2.2.1. Find two distinct bases (the plural of basis) for the vector space of
polynomials with real coefficients of degree at most 3 , and prove they are bases.
Our main goal for this subsection is to prove that every finite dimensional vector space
indeed has a basis, and in fact the length of this basis is the same, for a given vector space
V. From here on out, assume that we are working within a given finite dimensional vector
space V.
We begin by trying to compare the lengths of spanning sets and linearly independent
sets. To do this, consider the following properties of spanning sets.
Problem 2.2.2. Suppose that S is a spanning set, and v is a vector that doesn’t lie
in S.
1. Show that S ∪ {v} is linearly dependent.
2. Suppose furthermore that v is nonzero. Then, show there exists a vector w ∈ S
such that (S − {w}) ∪ {v} is a spanning set.
From here, we consider the following procedure. Start with a linearly independent set L
and a spanning set S; by assumption, we know that we can pick a spanning set S that is
finite. We now consider replacing vectors in S with those that are in L.
Problem 2.2.3. Show that if L ̸⊆ S, we can replace a vector in S with one in L so
that S remains a spanning set, and S ∩ L increases in size by one.
Problem 2.2.4. Using the above procedure, show that L must be finite, and that L
must have at most as many elements as S. Conclude that the size of every linearly
independent set is at most the size of every spanning set.
Using this size comparison, we are now ready to construct a basis for our vector space, and
show they have the same size. The first result allows us to state that every vector space
has a basis.
Problem 2.2.5. Prove the following.
1. Any spanning set with finitely many elements can be reduced to a basis. That
is, we may remove elements from our spanning set such that the resulting set is
a basis.
2. Any linearly independent set can be extended to a basis. That is, we may add
elements to our linearly independent set so that the resulting set is a basis.
We are now ready to state the main result.
Problem 2.2.6. Show that any two bases of our finite dimensional vector space have
the same size. This size is known as the dimension of the vector space, denoted as
dim V.
For instance, one can check that Rn, as a vector space over R, has dimension n (you may
assume this throughout the rest of the power round). Similarly, the space of polynomials,
with coefficients in C, with degree at most 2 , is a vector space with dimension 3 , as we saw
previously with this space having basis 1 , x, x2.
Problem 2.2.7. Show that if W is a subspace of V, then the dimension of W is at
most that of V.
2.3 Linear Transforms
Now that we’ve discussed vector spaces, we can consider maps between vector spaces. Just
like with rings, we consider a special type of map between vector spaces that are linear.
Definition 2.3.1. A linear transformation between two vector spaces V, Wover a com-
mon field k is a map T : V → W satisfying the following conditions:
1. For all vectors v1, v2 ∈ V, we have T (v1 + v2) = T (v1) + T (v2).
2. For all s ∈ k and v ∈ V, we have T (sv) = sT (v).
Such a linear transformation is an isomorphism if it is both injective and surjective.
As a first example, the maps of the form f (x) = kx, for k ∈ R, are all linear transfor-
mations from R to R. Notice, however, that f (x) = x + 1 is not a linear transformation,
since f (1) + f (1) = 2 + 2 = 4, but f (1 + 1) = f (2) = 3.
Notice that the second condition is sometimes unnecessary.
Problem 2.3.1. Suppose that k = Q, and V, Ware vector spaces over Q. Show that
if T : V → W satisfies T (v1 + v2) = T (v1) + T (v2) for all v1, v2 ∈ V, then T is actually
linear.
Now, given a linear transformationT : V → W, we consider the following two sets associated
with this linear transformation: the kernel and the image.
Definition 2.3.2. The kernel of a linear transformation, ker T, is the set of elements v ∈ V
such that T (v) = 0W . The image, im T, is the set of elements w ∈ W such that there exists
a v ∈ V so T (v) = w.
Example. Consider the map that sends a polynomial of degree at most 2 , with coefficients
in C, to its value at 0 (lying in C); we can easily check that this is a linear transformation.
The kernel of this map is then just the set of polynomials that vanish at 0 , namely those of
the form ax + bx2, for a, b∈ C, and the image is C.
Proposition 2.3.3. A linear transformation T is injective if and only if ker T = {0V }.
Proof. First, we note that T being injective means that ker T only has one element. Fur-
thermore, by linearity, T (0V ) + T (0V ) = T (0V ), meaning that T (0V ) = 0W , meaning that
ker T = {0V }. For the other direction, if ker T = {0v}, suppose that T (v1) = T (v2). By lin-
earity, we have that T (v1) − T (v2) = T (v1) + (−1)T (v2) = T (v1) +T (−v2) = T (v1 − v2) = 0.
But this means that v1 − v2 ∈ ker T, or that v1 − v2 = 0T , meaning that v1 = v2. This means
that T is injective, which is what we wanted to show.
Problem 2.3.2. Show that ker T is a subspace of V.
We now have the following result, which essentially states that finite-dimensional vector
spaces are essentially determined by their dimension. Indeed, just like with rings, we can
think of isomorphisms as simply being “relabellings” of the elements in our original space.
Problem 2.3.3. Suppose that V and W are finite dimensional vector spaces with the
same dimension d. Prove that V, Ware isomorphic; that is, there exists an isomor-
phism between them.
To show that this characterizes the space, we should also verify that two spaces that are
different dimensions cannot be isomorphic. First, we verify the following.
Problem 2.3.4. Prove that an infinite dimensional vector space cannot be isomorphic
to a finite dimensional vector space.
For a given linear transformation T, we can relate the dimension of its image and kernel in
the following way. The following theorem is also known as the rank-nullity theorem.
Theorem 2.3.4. Suppose that T is a linear transformation from V to W, where V is a
finite dimensional vector space. Then,
dim kerT + dim imT = dim V.
Often, dim kerT is referred to as the nullity of T, and dim imT the rank.
To do this, first consider a basis for ker T. Say these vectors are w1, w2, . . . , wn.
Problem 2.3.5. To prove the theorem, prove the following:
1. Show that this basis of ker T can be extended to a basis of V.
2. Suppose that this extension adds vectors wn+1, wn+2, . . . , wm. Show that
T (wn+1), T(wn+2), . . . , T(wm)
form a basis for im T, and from here prove the theorem.
Using the theorem, we also say the following.
Problem 2.3.6. Show that two finite dimensional vector spaces are isomorphic if and
only if they have the same dimension.
This says essentially that, for a given field k, the finite dimensional vector spaces over that
field are characterized exactly by the dimension of the space, up to isomorphism.
2.4 Matrices and Row Reduction
Sometimes it is useful to be able to talk explicitly about the vectors in a vector spaceV. This
can be done by fixing a basis of our vector space V, and then describing each vector as being
a linear combination of these basis vectors. In particular, given our basis w1, w2, . . . , wn,
we represent v =
nP
i=1
aiwi as the column vector


a1
a2
a3
...
an


∈ kn.
Problem 2.4.1. Show that this above map is well-defined and is an isomorphism
between V and kn.
If we now specify bases (v1, v2, . . . , vn) for V and (w1, w2, . . . , wm) for W, we can now describe
every linear transformation T : V → W as a matrix. Specifically, if T (vj) =
mP
i=1
ai,jwi, we
can represent T as the following m × n array of numbers:


a11 a12 · · ·a1n
a21 a22 · · ·a2n
... ... ...
am1 am2 · · ·amn

 .
We say that aij is the ( i, j)th entry of this matrix.
We can then view the operation of the linear transformation entirely using the coordi-
nates described by these bases, using the following multiplication rule:


a11 a12 · · ·a1n
a21 a22 · · ·a2n
... ... ...
am1 am2 · · ·amn




x1
x2
x3
...
xn


=


nP
i=1
a1ixi
nP
i=1
a2ixi
...
nP
i=1
amixi


.
For instance, given the vector space of polynomials of degree at most 2 , we can see that
this has a basis 1 , 1 + x, 1 + x + x2. Consider the map that sends each polynomial to the
vector
p(0)
p(1)

. Then, the matrix that we get for this linear transformation is
1 1 1
1 2 3

.
For instance, we note that T (1 + x + x2) =
1
3

, giving us the third column.
We wish to relate the two operations of matrix multiplication and of applying our linear
transformation in general.
Problem 2.4.2. Show that if we multiply the matrix of T with the coordinate rep-
resentation of v ∈ V, we get the coordinate representation of T (v). In this sense, our
notion of matrix multiplication is consistent with the way our linear transformation
acts on vectors.
Often, we want to represent T using a choice of bases that are as simple as possible. If
we are allowed to change the bases of both V and W, this can take a particularly simple
form.
Problem 2.4.3. Show that there exists bases for V, W such that the only nonzero
entries of T are along the diagonal; that is, only the ( i, i)th entries are nonzero for
i = 1, 2, . . . , rfor some nonnegative integer r. What is the value of r?
Although this is a nice result, often we run into situations where we cannot freely choose
bases in the way the above result requires. First, if T is a map from a vector space to
itself, we often only want to use one basis for both the input and output. This gives us
significantly less flexibility; see section 5 for more details.
In other situations, we have a nice basis for V which we would like to preserve. As
such, we are only allowed to choose a basis for W. In this latter situation, we can achieve a
comparatively simple form using a method called row reduction.
The main algorithm for row reduction utilizes three operations, acting on rows of our
matrix.
1. We can take a row and multiply every entry in the row by some nonzero scalar c ∈ k.
2. We can swap two rows (that is, if we are swapping rows i, j,then the old (i, k)th entry
is the new ( j, k)th entry for k = 1, 2, . . . , n,and vice versa).
3. We can add a multiple of one row to another row.
For instance, we can apply some row operations to the matrix


2 6 3
1 0 4
0 −1 1

 . If we
subtract half the first row from the second, we get the matrix


2 6 3
0 −3 2 .5
0 −1 1

 . If we then
divide the first row by 2 , we get the matrix


1 3 1 .5
0 −3 2 .5
0 −1 1

 .
Problem 2.4.4. Show that if we apply one of our row reduction operations to a matrix
for T, we get another matrix for T, using a different basis for W (but the same basis
for V ). How do you relate the old basis to the new basis?
From here, we claim that we can reach the following form, known asreduced row echelon
form. This form satisfies the following properties.
1. Every row with at least one nonzero entry has their leftmost nonzero entry as a 1 .
These 1s are known as pivots.
2. Each pivot is the only nonzero entry in its column.
3. The pivot of the ith row is left of the pivot of the jth row if i < j.
4. The rows with all zeros are on the bottom of the matrix.
For instance, with the same matrix as the above, we can continue our procedure: swapping
rows two and three yields


1 3 1 .5
0 −1 1
0 −3 2 .5

 , then subtracting three times the second row
from the third yields


1 3 1 .5
0 −1 1
0 0 −0.5

 . Adding three times the second row to the first
yields


1 0 4 .5
0 −1 1
0 0 −0.5

 . Adding two times the third row to the second, and nine times the
third row to the first, yields


1 0 0
0 −1 0
0 0 −0.5

 . Multiplying the third row by −2 and the
first by −1 yields the final matrix


1 0 0
0 1 0
0 0 1

 , which is in reduced row echelon form.
Problem 2.4.5. Reduce the following matrices to reduced row echelon form.
1.
1 2 3
6 5 4

2.


4 2 −1 −3
1 0 −5 2
0 1 0 2


Problem 2.4.6. Show that for any i, using the row operations on the matrix for T,
if column i had at least one nonzero entry initially, then there is a sequence of row
operations such that the resulting matrix only has one nonzero entry in column i, and
it is a 1 .
Problem 2.4.7. Using the above procedure, show that any matrix can be reduced to
reduced row echelon form.
With the reduced row echelon form, we can more easily read off useful information about
our linear transformation T.
Problem 2.4.8. Show that the number of pivots ofT is equal to the rank of T, and the
number of columns without pivots is equal to the nullity of T, without using the rank-
nullity theorem. (One can prove the rank-nullity theorem by analyzing the reduced row
echelon form of a matrix).
With the above method, we can everywhere replace the word “row” with “column” to
get column reduction. This corresponds to changing the basis for the input space, which
you may assume without proof.
3 Modules
We can generalize the definition of a vector space above to that of a module, as below.
Definition 3.0.1. Given a ring R, a module M is a set of elements equipped with two
operations, addition + : M × M → M and scalar multiplication · : R × M → M, satisfying
the following properties:
1. M is closed under addition and scalar multiplication: that is, ∀m1, m2 ∈ M, m1+m2 ∈
M, and for all r ∈ R, m∈ M, we have r · m ∈ M.
2. The operations + , · are associative: ∀m1, m2, m3 ∈ M, we have that (m1 +m2)+ m3 =
m1 + (m2 + m3), and for r1, r2 ∈ R and m ∈ M, we have r1 · (r2 · m) = (r1 ·R r2) · m.
3. The operation + is commutative.
4. The operation + has an identity element, which we denote as 0 .
5. Each element m ∈ M has an additive inverse.
6. For all m ∈ M, 1R · m = m.
7. We have the following distributive laws: ∀r ∈ R and m1, m2 ∈ M, we have r1 · (m1 +
m2) = r1 · m1 + r1 · m2, and for all r1, r2 ∈ R and m ∈ M, we have ( r1 + r2) · m =
r1 · m + r2 · m.
We also say that M in this case is an R−module. A submodule of M is a subset N
that is also a module under the same operations as that of M.
Notice in particular that a vector space over a field is also module over that field, and
any ring is a module over itself. Here is another example.
Example. The set of even integers is a module over Z, using the standard addition on even
integers and scalar multiplication being just multiplication in Z. Properties 2, 3, 7 follow
simply because we know that Z is a ring, and property 1 follows since we’ve previously
argued that the sum of even integers is even, and the product of an even integer with
another integer is even.
For property 4, we note that the identity for addition, 0, lies in Z, and property 5 follows
since we know that for each even integer, its negation is also even. Finally, for property 6,
by the standard multiplication rule in Z, multiplying any even integer by 1 yields the even
integer again.
This example can be generalized.
Problem 3.0.1. Show that for any ring R and ideal I of R, Iis an R−module under
the addition and multiplication operations of the ring R.
Definition 3.0.2. Given an R−module M, a linear combination of m1, m2, . . . , mn ∈ M
is an expression of the form
nP
i=1
rimi, where ri ∈ R.
A generating set of a module M is a set S such that every element can be written as a
linear combination of some finite subset of S. We say that a module is finitely generated
if it has a finite generating set.
A set of elements of M is linearly independent if the only linear combination of these
elements that equals zero is the linear combination where all of the coefficients ri are 0.
A set of elements of M is said to be a free basis of M if it is linearly independent and
a generating set. In this case, if such a free basis exists, we say that M is a free module .
Its rank is then the length of this free basis.
These definitions should be reminiscent of definitions of linear independence and span from
our discussions of linear algebra. We need to explicitly point out when our modules are free
for the following reason.
Example. Consider the ideal I = ⟨2, 1 + √−5⟩ inside the ring R = Z[√−5], the set of
integers of the form a + b√−5 for some integers a, b.Notice that this ideal is an R−module
by Problem 3.0.1. We show that this is not a free module.
To see this, suppose for the sake of contradiction that {r1, r2, . . . , rk} was a free basis for
I. If k ≥ 2, then note that by linear independence that none of the elements can be zero. But
then (−r2)r1 + r1r2 = 0, meaning that this set is not linearly independent, contradiction.
Therefore, I would have to have a free basis with one element, say r1. But then there
exist elements s1, s2 ∈ R such that s1r1 = 2 and s2r1 = 1 + √−5. But suppose that
s1 = a1 + a2
√−5 and r1 = b1 + b2
√−5, then s1r1 = (a1b1 − 5a2b2) + (a1b2 + a2b1)√−5.
For this to equal 2 , we need a1b2 = −a2b1. Note however that multiplying this by ( a1 −
a2
√−5)(b1 − b2
√−5), which equals ( a1b1 − 5a2b2) − (a1b2 + a2b1)√−5 = 2 , yields that
(a2
1 + 5a2
2)(b2
1 + 5b2
2) = 4. For this to hold, as the ai are integers, we need one pair of ( a1, a2)
to be ( ±1, 0) and the other to be ( ±2, 0). However, note that r1 cannot be ±2, since that
implies that s2 = ± 1+√−5
2 /∈ Z[√−5], contradiction.
But if r1 = ±1, this means that 1 ∈ ⟨2, 1 + √−5⟩, meaning that there exist a + b√−5
and c + d√−5 in Z[√−5] so 2(a + b√−5) + (1 +√−5)(c + d√−5) = 1, or that (2a + c − 5d) +
(2b + c + d)√−5 = 1. But c − 5d would have to be odd and c + d even, which is impossible.
Hence, no r1 can exist, and therefore I must not be a free module, which is what we
wanted to show.
Observe that if we are given a free module, the following property from linear algebra
does carry over to the module case. You may assume that this proposition holds without
proof.
Proposition 3.0.3. Suppose that F is a free module over a nonzero ring R that is finitely
generated. Then, any two free bases of F have the same length.
Similarly to the vector space case, we can also consider maps between modules, in the
following way.
Definition 3.0.4. A module homomorphism between R−modules M and N is a map ϕ :
M → N such that for all m, m′ ∈ M and r ∈ R, we have that ϕ(m+M m′) = ϕ(m)+N ϕ(m′),
and ϕ(r ·M m) = r ·N ϕ(m).
Definition 3.0.5. A module homomorphism is said to be an isomorphism if it is injective
and surjective. Two modules are then isomorphic if there exists an isomorphism between
them.
We also have the kernel and the image, defined similarly to the vector space case.
Definition 3.0.6. Let ker ϕ = {m ∈ M |ϕ(m) = 0}, and imϕ = {ϕ(m)|m ∈ M }.
Just like before, we will omit which objects are being mapped if it is clear from context
what objects we are mapping. Similarly to the vector space case, we can verify that the ker-
nel and image of a module homomorphism are both modules; you may use this throughout
the rest of the power round without proof.
Problem 3.0.2. Show that any finitely generated free module is isomorphic to Rn for
some n ∈ N.
We finally have the notion of a quotient module and the direct sum of modules.
Definition 3.0.7. Given R−modules M1, M2, . . . , Mk, the module M1 ⊕ M2 ⊕ . . .⊕ Mk,
sometimes written as Lk
i=1 Mi, is the set of elements {(m1, m2, . . . , mk)|mi ∈ Mi for i =
1, 2, . . . , k}, equipped with addition and scalar multiplication coordinate-wise. That is,
(m1, m2, . . . , mk) + (m′
1, m′
2, . . . , m′
k) = (m1 +M1 m′
1, m2 +M2 +m′
2, . . . , mk +Mk m′
k)
and
r · (m1, m2, . . . , mk) = (r ·M1 m1, r·M2 m2, . . . , r·Mk mk).
For instance, to get the module Rn, the set of tuples of length n (whose entries are
elements of R), we can do Rn = R ⊕ R ⊕ . . .⊕ R; the addition and scalar multiplication
operations of Rn are precisely those that are obtained by using this direct sum procedure.
Definition 3.0.8. Given two R−modules M, N, define for m ∈ M the set m + N as
{m+n|n ∈ N }. Then, M/N is the module defined to be the set of elements{m+N |m ∈ M },
equipped with addition (m1 +N )+( m2 +N ) = (m1 +m2)+ N and r·(m1 +N ) = (r·m1)+ N,
for all m1, m2 ∈ M and r ∈ R.
One can verify that the two above definitions are well-defined and actually give modules.
For the purposes of this power round, however, you may assume these to be true.
We now begin to discuss some important properties of homomorphisms.
Problem 3.0.3. Given a submodule N of an R−module M, consider the map κM,N :
M → M/N that sends m to m + N. Show that this map is a surjective homomorphism.
What is the kernel of κM,N ?
Problem 3.0.4. Given a homomorphism between R−modules M, N:
1. Show that there exists a homomorphism ¯ϕ : M/ ker ϕ → N such that
¯ϕ(κM,ker ϕ(m)) = ϕ(m)
for all
...[truncated]
